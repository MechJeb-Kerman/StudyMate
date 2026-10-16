"""任务 3 · 形状与递归深度：树高是一回事，递归能走多深是另一回事

参考解。与任务目录里的同名文件只差标着 TODO 的四段。

课件「树高与递归深度」那一节：**递归深度等于树高，所以它取决于形状、不取决于规模**。

  · 平衡树：$n$ 个结点的树高约 $\\log_2 n$——一万个结点只走 14 层；
  · 链状树：树高就是 $n$——不到一千层就爆栈。

这一份量出来的三个数（本机 Python 3.14.7t、递归上限 1000）：

  01 平衡树 树高 10000 → 14        （1 万个结点，dfs 只走 14 层）
  02 链状 爆栈长度 → 999           （998 层还跑得动、999 层撞上递归上限）
  03 递归再深一层 → 997            （树高等于它时还跑得动，再深一层就报错）

第 03 行说明「爆栈的长度减一」差不多就是递归能走的层数；它与 sys.getrecursionlimit()
差着几层固定开销（进入 height、递归里调用 max、以及解释器自己占的那几层，本机 2-3 层）。
这一行贴着上限，注定差得动一两层：这一份是在**函数里**试的，比主块顶层少一层
（函数自己那一帧），所以报出来的是 997；在主块顶层直接试能走到 998。
判分接受的是一小段（995-998），判据是「它贴着上限、而且那个深度上 height 交回的
树高等于深度本身」。这一行是在**默认**上限下试出来的：不在这里改 setrecursionlimit，
否则量到的就不是默认的那条线了。

接口：文件名、函数名、带 print 的行都是判分接口，别改。

跑： py task3_depth_shape.py
判： py run_tests.py
"""

import sys

from tools import node, show_count, show_label, show_pair, show_recursion_error

SIZES = (100, 1000, 10000)                     # 别改：三种规模


# ══ TODO 1 ═════════════════════════════════════════════════
def build_balanced(n):
    """n 个结点的平衡树：根是 k，左子树 k // 2 个结点，其余给右子树。"""
    def rec(k):
        if k == 0:
            return None
        left = k // 2
        return node(k, rec(left), rec(k - 1 - left))

    return rec(n)


# ══ TODO 2 ═════════════════════════════════════════════════
def build_chain(n):
    """链状树：每个结点只有左孩子，树高就是 n。"""
    t = None
    for i in range(n):
        t = node(i, t, None)
    return t


# ══ TODO 3 ═════════════════════════════════════════════════
def height(t):
    """树高 = 层数。这一份里它就是递归深度，所以**不许**改成迭代版。

    链状树上它会一直递归到树底，撞上递归上限时抛出 RecursionError——
    不在这里接住，交给调用处接。
    """
    if t is None:
        return 0
    return 1 + max(height(t[1]), height(t[2]))


# ══ TODO 4 ═════════════════════════════════════════════════
def max_safe_depth():
    """树高等于它时 height 还跑得动、再深一层就报 RecursionError 的最大值。

    在**默认**的递归上限下往上试：这一份量的是默认上限下的那条线，
    所以不在这里改 setrecursionlimit。跑得动就记下来，报错就停。
    """
    limit = sys.getrecursionlimit()
    deep = 0
    for depth in range(limit - 10, limit + 5):
        try:
            height(build_chain(depth))
        except RecursionError:
            break
        deep = depth
    return deep


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声
    LIMIT = sys.getrecursionlimit()            # 别改：本机的递归上限

    # ── 一、两种形状在三种规模上的树高（这几行别改）──────────────
    print('形状 规模 树高 这一层的递归')                                   # 别改
    for n in SIZES:                            # 别改
        safe = build_balanced(n)               # 别改
        try:                                   # 别改
            h = height(safe)                   # 别改
            print('平衡 n=' + str(n).rjust(5), '树高', str(h).rjust(6), '跑得动')   # 别改
            show_pair('树高行 平衡 n=' + str(n), h, '跑得动')                   # 别改
        except RecursionError:                 # 别改
            print('平衡 n=' + str(n).rjust(5), '树高 爆栈')                     # 别改
            show_pair('树高行 平衡 n=' + str(n), '爆栈', '爆栈')                # 别改
    for n in SIZES:                            # 别改
        chain = build_chain(n)                 # 别改
        try:                                   # 别改
            h = height(chain)                  # 别改
            print('链状 n=' + str(n).rjust(5), '树高', str(h).rjust(6), '跑得动')   # 别改
            show_pair('树高行 链状 n=' + str(n), h, '跑得动')                   # 别改
        except RecursionError:                 # 别改
            print('链状 n=' + str(n).rjust(5), '树高 爆栈')                     # 别改
            show_pair('树高行 链状 n=' + str(n), '爆栈', '爆栈')                # 别改

    show_label('计数 01 平衡 n=10000 树高', height(build_balanced(10000)))    # 别改

    # ── 二、链状树加到多长会爆栈（这一段别改）──────────────────
    crash_at = 0                               # 别改
    for n in range(990, 1006):                 # 别改
        try:                                   # 别改
            height(build_chain(n))             # 别改
        except RecursionError:                 # 别改
            crash_at = n                       # 别改
            break                              # 别改
    show_recursion_error(2, '链状 爆栈长度', crash_at)      # 别改：留白版这一行是 0
    show_label('链状 爆栈长度', crash_at)          # 别改：期望 999

    # ── 三、递归再深一层：树高等于它时还跑得动（这一段别改）────────
    deep = max_safe_depth()                    # 别改
    show_label('递归再深一层', deep)              # 别改：期望 995-998 之间
    show_label('注释 递归上限', LIMIT)             # 别改
    print('递归深度比上限小几层', deep < LIMIT)                              # 别改：期望 True
    print('固定开销的层数', LIMIT - deep)                                    # 别改：期望是个位数
    show_count(2, '爆栈长度', crash_at)                                      # 别改
    show_count(3, '递归再深一层', deep)                                       # 别改