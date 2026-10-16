"""任务 3 · 形状与递归深度：树高是一回事，递归能走多深是另一回事

课件「树高与递归深度」那一节：**递归深度等于树高，所以它取决于形状、不取决于规模**。

  · 平衡树：$n$ 个结点的树高约 $\\log_2 n$——十万个结点也只有 17 层；
  · 链状树：树高就是 $n$——不到一千层就爆栈。

这一份要亲手把这两条量出来。三种规模各取一次，两种形状各量一遍：

  01 平衡树 树高 10000 → 14        （1 万个结点，dfs 只走 14 层）
  02 链状 爆栈长度 → 999           （不到 1000 就撞上递归上限）
  03 递归再深一层 → 997 上下        （树高等于它时还跑得动，再深一层就报错）

第 03 行是这一份的关键：它说明「爆栈的长度减一」差不多就是递归能走的层数。
它与 sys.getrecursionlimit() 之间还差着几层固定开销（Python 进入 height、
递归里调用 max、以及解释器自己占的那几层，本机是 2-3 层）。

这一行**注定差得动一两层**：贴着上限试，差的就是一两个栈帧——在函数里试比在主块
顶层试要少一层（函数自己那一帧）。所以判分接受的是一小段（995-998），
真正的判据是「它贴着上限、而且在那个深度上 height 交回的树高等于深度本身」。
别为了凑一个漂亮的数去改递归上限。

两种形状都用**同一个** height(t) 来量：它只在 None 上停，
所以在链状树上它会一直递归到树底——爆栈就发生在那里。

接口：文件名、函数名、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那几段。

跑： py task3_depth_shape.py
判： py run_tests.py
"""

import sys

from tools import node, show_count, show_label, show_pair, show_recursion_error

SIZES = (100, 1000, 10000)                     # 别改：三种规模


# ══ TODO 1 ═════════════════════════════════════════════════
# 补 build_balanced(n)：n 个结点的平衡树，照课件那一版写：
#
#     def rec(k):
#         if k == 0:
#             return None
#         left = k // 2
#         return node(k, rec(left), rec(k - 1 - left))
#
# 根的值是 k，左子树放 k // 2 个结点，其余留给右子树。
# 这样分出来的树高是 ⌈log2(n+1)⌉：n=100 是 7，n=1000 是 10，n=10000 是 14。
def build_balanced(n):
    # TODO 1
    return None


# ══ TODO 2 ═════════════════════════════════════════════════
# 补 build_chain(n)：链状树，每个结点只有左孩子。
#   从空树开始，for i in range(n): t = node(i, t, None)
#   搭出来是一条一直往左下的链，树高就是 n。
def build_chain(n):
    # TODO 2
    return None


# ══ TODO 3 ═════════════════════════════════════════════════
# 补 height(t)：与任务 2 同一个口径——空树 0，否则 1 + max(两个孩子的高度)。
#   **不许改成显式栈的迭代版**：这一份量的就是递归深度，改成迭代就量不到了。
#   链状树上它会递归到树底，撞上递归上限时抛出 RecursionError——
#   别在函数里接住它，交给调用处接（下面那些 try 已经写好了）。
def height(t):
    # TODO 3
    return 0


# ══ TODO 4 ═════════════════════════════════════════════════
# 补 max_safe_depth()：「树高等于它时还跑得动、再深一层就报 RecursionError」的最大值。
#   1) 从 limit - 5 开始试（limit 是调用处的 sys.getrecursionlimit()，本机 1000；
#      别从 limit 本身开始试：那已经贴着上限了）；
#   2) 试的办法就是 height(build_chain(试的那个值))，外面套 try / except RecursionError——
#      **别改递归上限**来处理它，这一份量的就是默认上限下的那条线；
#   3) 跑得动就把答案记成这个值、再加一继续试；报 RecursionError 就说明到顶了，
#      break 出来交回「上一次跑得动」的那个值。
#   期望在 995-998 之间（本机 997-998，差一层是函数自己那一帧），
#   而且它比 limit 只小几层——小的那几层就是进入 height、递归里调用 max
#   与解释器自己占的固定开销。
def max_safe_depth():
    # TODO 4
    return 0


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