"""任务 4 · 拼接结果的隐藏代价：两个版本放在两种形状上量

参考解。与任务目录里的同名文件只差标着 TODO 的五段。

课件「拼接结果的隐藏代价」那一节：拼接写法读起来最贴近定义，但**每一层都要
复制一遍子树的结果**，而子树的大小取决于树的形状。

    拼接版   return [t[0]] + preorder_concat(t[1]) + preorder_concat(t[2])
    累加器版 out.append(t[0]); 递归两个孩子; return out

同一个 n 上，链状树的代价是平方级（每层都要复制一遍剩下那半条链），
平衡树上小得多（每个结点的子树本来就不大）。本机实测（Python 3.14.7t）：

    链状 200  拼接 0.000054 秒   累加器 0.000012 秒   4.4 倍
    链状 400  拼接 0.000187 秒   累加器 0.000034 秒   5.5 倍
    链状 800  拼接 0.000704 秒   累加器 0.000079 秒   8.9 倍
    平衡 500 / 1000 / 2000 上两版的倍数只有 1.6-1.7 倍

链长从 200 涨到 800（四倍），拼接涨约 13 倍（每翻一倍 3.5 倍上下，平方级），
累加器只涨约 6.6 倍（每翻一倍 2.3 倍，接近线性）。同一对函数放到平衡树上
差距小得多——**代价与形状有关，不只是与 n 有关**。

链状树取 200 / 400 / 800（再大就撞递归上限），平衡树取 500 / 1000 / 2000。
每一行都是「跑 K 次取最快的一次」，秒数取六位小数：即使这样，末几位仍会浮动，
所以判分看的是**趋势**（翻倍涨多少倍、两列差多少倍），不核对具体秒数。

最后一段要量的那条链有 2000 层，比默认的递归上限（1000）还深，所以那一段外面
临时把上限调高、量完还原——**这一段要看的代价是拼接的复制量，不是撞递归上限**。
（默认上限下的那条线是任务 3 量的东西。）

接口：文件名、函数名、造树那几行、带 print 的行都是判分接口，别改。

跑： py task4_concat_cost.py
判： py run_tests.py
"""

import sys

from tools import node, show_count, show_label, show_time, timed

CHAIN_SIZES = (200, 400, 800)                  # 别改：与课件量过的那三档一样
BALANCED_SIZES = (500, 1000, 2000)             # 别改
REPEATS = 50                                   # 别改：每个规模跑这么多次，取最快的一次
BIG = 2000                                     # 别改：最后比较「两个形状的倍数」用的规模
DEEP_LIMIT = 3000                              # 别改：量 BIG 那条链时用的递归上限


# ══ TODO 1 ═════════════════════════════════════════════════
def preorder_concat(t):
    """拼接版前序——课件「三种遍历」那一节的原样写法。"""
    if t is None:
        return []
    return [t[0]] + preorder_concat(t[1]) + preorder_concat(t[2])


# ══ TODO 2 ═════════════════════════════════════════════════
def preorder_acc(t, out=None):
    """累加器版前序：结果 append 进传进来的 out。"""
    if out is None:
        out = []
    if t is None:
        return out
    out.append(t[0])
    preorder_acc(t[1], out)
    preorder_acc(t[2], out)
    return out


# ══ TODO 3 ═════════════════════════════════════════════════
def build_chain(n):
    """链状树：每个结点只有左孩子。"""
    t = None
    for i in range(n):
        t = node(i, t, None)
    return t


# ══ TODO 4 ═════════════════════════════════════════════════
def build_balanced(n):
    """平衡树：根是 k，左子树 k // 2 个结点，其余给右子树（与任务 3 同一版）。"""
    def rec(k):
        if k == 0:
            return None
        left = k // 2
        return node(k, rec(left), rec(k - 1 - left))

    return rec(n)


# ══ TODO 5 ═════════════════════════════════════════════════
def best_of(func, t, repeats):
    """把 func(t) 跑 repeats 次，交回**最快**那一次的秒数。"""
    best = 1e9
    for _ in range(repeats):
        _, seconds = timed(func, t)
        if seconds < best:
            best = seconds
    return best


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声

    # ── 一、两个版本答案必须一样（别改）──────────────────────────
    chain200 = build_chain(200)                # 别改
    # tools.timed 就是这套计时：交回 (函数的值, 秒数)。先拿它量一次看看量到的是什么。
    first_value, first_seconds = timed(preorder_concat, chain200)      # 别改
    show_time(0, '链状树 拼接  ', 'n=200 第一次', first_seconds)         # 别改
    print('链状 200 两版答案一致', preorder_concat(chain200) == preorder_acc(chain200),
          first_value[:5])                                            # 别改：期望 True
    print('空树 两版答案一致', preorder_concat(None) == preorder_acc(None))   # 别改：期望 True
    print('单点 两版答案一致', preorder_concat(node(7)) == preorder_acc(node(7)))   # 别改：期望 True
    show_label('两版答案一致', preorder_concat(chain200) == preorder_acc(chain200))   # 别改

    # ── 下面三段的打印都是判分接口，别改 ─────────────────────────
    # 第四段要量的那条链有 2000 层，比默认的那条递归上限还深（这是第 13 课的
    # 那条判断：递归深度取决于形状），所以量它之前把上限临时调高，
    # 量完在 finally 里还原——**要看的代价是拼接的复制量，不是撞递归上限**。
    original_limit = sys.getrecursionlimit()   # 别改
    sys.setrecursionlimit(DEEP_LIMIT)          # 别改
    try:                                       # 别改
        # ── 二、链状树上量三档 ──────────────────────────────────
        chain_concat = []                      # 别改
        chain_acc = []                         # 别改
        for n in CHAIN_SIZES:                  # 别改
            t = build_chain(n)                 # 别改
            c = best_of(preorder_concat, t, REPEATS)      # 别改
            a = best_of(preorder_acc, t, REPEATS)         # 别改
            chain_concat.append(c)             # 别改
            chain_acc.append(a)                # 别改
            show_time(1, '链状树 拼接  ', 'n=' + str(n), c)               # 别改
            show_time(2, '链状树 累加器', 'n=' + str(n), a)               # 别改
        for i in range(1, len(CHAIN_SIZES)):   # 别改
            show_label('倍数 链状 拼接 n=' + str(CHAIN_SIZES[i]),
                       round(chain_concat[i] / max(chain_concat[i - 1], 1e-9), 2))    # 别改
            show_label('倍数 链状 累加器 n=' + str(CHAIN_SIZES[i]),
                       round(chain_acc[i] / max(chain_acc[i - 1], 1e-9), 2))          # 别改

        # ── 三、平衡树上量三档 ──────────────────────────────────
        bal_concat = []                        # 别改
        bal_acc = []                           # 别改
        for n in BALANCED_SIZES:               # 别改
            t = build_balanced(n)              # 别改
            c = best_of(preorder_concat, t, REPEATS)      # 别改
            a = best_of(preorder_acc, t, REPEATS)         # 别改
            bal_concat.append(c)               # 别改
            bal_acc.append(a)                  # 别改
            show_time(3, '平衡树 拼接  ', 'n=' + str(n), c)               # 别改
            show_time(4, '平衡树 累加器', 'n=' + str(n), a)               # 别改

        # ── 四、两个形状上的「拼接比累加器慢几倍」──────────────────
        chain_t = build_chain(BIG)             # 别改
        bal_t = build_balanced(BIG)            # 别改
        chain_ratio = best_of(preorder_concat, chain_t, REPEATS) / max(
            best_of(preorder_acc, chain_t, REPEATS), 1e-9)                # 别改
        bal_ratio = best_of(preorder_concat, bal_t, REPEATS) / max(
            best_of(preorder_acc, bal_t, REPEATS), 1e-9)                  # 别改
        print('链状 n=' + str(BIG), '拼接比累加器慢', round(chain_ratio, 2), '倍')   # 别改
        print('平衡 n=' + str(BIG), '拼接比累加器慢', round(bal_ratio, 2), '倍')     # 别改
        print('链状上的倍数更大', chain_ratio > bal_ratio)                    # 别改：期望 True
        show_label('形状对照 链状倍数', round(chain_ratio, 2))                 # 别改
        show_label('形状对照 平衡倍数', round(bal_ratio, 2))                   # 别改

        show_count(1, '两版答案一致', preorder_concat(chain_t) == preorder_acc(chain_t))   # 别改
        show_count(2, '链状 800 拼接倍率',
                   round(chain_concat[-1] / max(chain_concat[0], 1e-9), 2))      # 别改
        show_count(3, '链状 800 累加器倍率',
                   round(chain_acc[-1] / max(chain_acc[0], 1e-9), 2))            # 别改
    finally:                                   # 别改
        sys.setrecursionlimit(original_limit)  # 别改：量完把上限还原
