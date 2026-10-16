"""任务 4 · 手写一个最小堆：上浮与下沉

课件「上浮与下沉」那一节：`heapq` 提供的两个内部动作就叫**上浮**（sift up）与**下沉**（sift down）。

    · 上浮：新元素追加到末尾（树的最下面一层靠右），不断与父结点比较，
            比父结点小就交换，直到不再比父结点小。**用于插入**。
    · 下沉：把末尾元素搬到根上，不断与**较小的那个孩子**比较，
            比孩子大就交换，直到不再比孩子大。**用于弹出**。

两者的共同点是**每一层只走一步**，所以一次操作最多走树高那么多步，也就是 $O(\\log n)$。

堆在列表里的下标关系是固定的（课件那张表）：

    结点 i 的左孩子 2i + 1      右孩子 2i + 2      父结点 (i - 1) // 2

`pop` 里那三步的顺序最容易写反：**先记下根（答案）、再把末尾元素取出来、
然后把它放到根上往下沉**。如果先把根删掉再取末尾，下标就乱了——
这是手写堆最常见的错。

这一份要在随机数上与 `heapq` 对照：弹出的序列必须完全一致。

接口：文件名、类名、方法名、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那几段。

跑： py task4_min_heap.py
判： py run_tests.py

参考解。与任务目录里的同名文件只差标着 TODO 的四段。
"""

import heapq
import random

from tools import best_of, show_count, show_label, show_pair, show_time

N = 1000                                       # 别改：随机数的个数
REPEATS = 200                                  # 别改：量耗时就跑这么多次
SEED = 9                                       # 别改：课件那段就是 random.seed(9)

# 给好的验证器（别改）：交回「手写堆弹出的序列」与「排序后的顺序」是否逐项相同。
# 两边都是升序：手写堆是从小到大弹出来的，排序也是。
#
# 每一步都拿**非空**的堆检查堆序性质。写成一堆 `all(... for i in range(len // 2))`
# 的话，堆还是空的时候那个生成器什么都没走，`all` 会空着交回 True——
# 「还没开始就宣布成立」是这类检查最容易骗过自己的地方，所以这里先判长度再往深里比。
def heap_ok(heap):
    """堆序性质：每个结点都不大于它的两个孩子。空堆与单元素都算成立。"""
    a = heap.a
    n = len(a)
    for i in range(n):
        left, right = 2 * i + 1, 2 * i + 2
        if left < n and a[i] > a[left]:
            return False
        if right < n and a[i] > a[right]:
            return False
    return True


def check_pushes(vals):
    """每推一个数之后都要：元素个数跟着长，而且堆序性质仍然成立。"""
    h = MinHeap()
    ok = True
    for i, v in enumerate(vals, 1):
        h.push(v)
        if len(h.a) != i or not heap_ok(h):
            ok = False
    return ok


def check_pops(vals):
    """每弹一个数之后都要：元素个数跟着减，而且堆序性质仍然成立。"""
    h = MinHeap()
    for v in vals:
        h.push(v)
    ok = True
    for i in range(len(vals) - 1, -1, -1):
        h.pop()
        if len(h.a) != i or not heap_ok(h):
            ok = False
    return ok


def ascending(vals):
    """照顺序 push 完，再全部 pop 出来——一条升序序列。"""
    h = MinHeap()
    for v in vals:
        h.push(v)
    return [h.pop() for _ in range(len(vals))]


def check_mixed(vals):
    """随机穿插 push / pop，每一步都核对弹出的值与堆的合法性，交回 [对不对, 剩下几个]。"""
    h = MinHeap()
    mirror = []
    ok = True
    for v in vals:
        h.push(v)
        mirror.append(v)
        if len(h.a) != len(mirror) or not heap_ok(h):
            ok = False
        if v % 3 == 0:
            got = h.pop()
            want = min(mirror)
            mirror.remove(want)
            if got != want or len(h.a) != len(mirror) or not heap_ok(h):
                ok = False
    return [ok, len(h.a)]


class MinHeap:
    """数组实现的最小堆：内部只有一个列表 a，a[0] 永远是最小值。"""

    def __init__(self):
        # 别改
        self.a = []

    # ══ TODO 1 ═════════════════════════════════════════════
    # 补 push(v)：把 v 追加到末尾，再让它**上浮**到合适的位置。
    #     self.a.append(v)
    #     self._up(len(self.a) - 1)
    #   追加之后新元素的下标是 len(self.a) - 1（追加完了才取长度）。
    def push(self, v):
        # TODO 1
        self.a.append(v)
        self._up(len(self.a) - 1)

    # ══ TODO 2 ═════════════════════════════════════════════
    # 补 pop()：弹出并交回最小的那个（a[0]）。
    #     a = self.a
    #     top = a[0]                 ① 先记下根——这就是答案
    #     last = a.pop()             ② 再把末尾元素取出来
    #     if a:                      ③ 剩下的非空才把它放到根上往下沉
    #         a[0] = last
    #         self._down(0)
    #     return top
    #   这三步的顺序不能换：先删根再取末尾，下标就乱了。
    #   空堆上调用会走到 a[0] 上，报 IndexError: list index out of range——那是应该的。
    def pop(self):
        # TODO 2
        a = self.a
        top = a[0]                 # ① 先记下根——这就是答案
        last = a.pop()             # ② 再把末尾元素取出来
        if a:                      # ③ 剩下的非空才把它放到根上往下沉
            a[0] = last
            self._down(0)
        return top

    # ══ TODO 3 ═════════════════════════════════════════════
    # 补 _up(i)：上浮。与**父结点**比，比父结点小就换上去。
    #     a = self.a
    #     while i > 0:
    #         p = (i - 1) // 2             父结点的下标
    #         if a[p] <= a[i]: break       已经不比自己小了，停
    #         a[p], a[i] = a[i], a[p]      换上去
    #         i = p                        接着从父结点那一层往上比
    #   循环条件是 i > 0：根没有父结点，走到根就停（漏了它会去取 a[-1]，
    #   那是最末尾的元素——堆会被悄悄弄坏，而且不一定报错）。
    def _up(self, i):
        # TODO 3
        a = self.a
        while i > 0:
            p = (i - 1) // 2             # 父结点的下标
            if a[p] <= a[i]:
                break                    # 已经不比自己小了，停
            a[p], a[i] = a[i], a[p]      # 换上去
            i = p                        # 接着从父结点那一层往上比

    # ══ TODO 4 ═════════════════════════════════════════════
    # 补 _down(i)：下沉。与**较小的那个孩子**比，比孩子大就换下去。
    #     a = self.a
    #     n = len(a)
    #     while True:
    #         l = 2 * i + 1
    #         r = l + 1
    #         m = i                        先假设自己最小
    #         if l < n and a[l] < a[m]: m = l
    #         if r < n and a[r] < a[m]: m = r
    #         if m == i: break             两个孩子都不比自己小，停
    #         a[i], a[m] = a[m], a[i]
    #         i = m
    #   两处下标判断（l < n、r < n）一个都不能少：孩子不存在时去取 a[l] 会
    #   IndexError；先与左孩子比、再与右孩子比，m 记住的才是**较小的那个**。
    def _down(self, i):
        # TODO 4
        a = self.a
        n = len(a)
        while True:
            l = 2 * i + 1
            r = l + 1
            m = i                        # 先假设自己最小
            if l < n and a[l] < a[m]:
                m = l
            if r < n and a[r] < a[m]:
                m = r
            if m == i:
                break                    # 两个孩子都不比自己小，停
            a[i], a[m] = a[m], a[i]
            i = m


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声

    random.seed(SEED)                          # 别改
    VALS = [random.randrange(1000) for _ in range(N)]      # 别改

    # ── 一、与 heapq 对照弹出序列（这几行别改）──────────────────
    mine_seq = ascending(VALS)                 # 别改
    theirs = list(VALS)                        # 别改
    heapq.heapify(theirs)                      # 别改
    theirs_seq = [heapq.heappop(theirs) for _ in range(len(theirs))]     # 别改
    print('手写堆弹出序列与 heapq 一致', mine_seq == theirs_seq)      # 别改：期望 True
    show_label('手写堆 与 heapq 一致', mine_seq == theirs_seq)       # 别改：期望 True
    print('与原数组排序一致', mine_seq == sorted(VALS))              # 别改：期望 True
    show_label('手写堆 前 8 个弹出', str(mine_seq[:8]))               # 别改
    show_label('原数组 前 8 小', str(sorted(VALS)[:8]))               # 别改

    # ── 二、逐步验证：每一步之后堆序性质都成立（这一段别改）──────
    probe_vals = [random.randrange(1000) for _ in range(50)]      # 别改
    ok_push = check_pushes(probe_vals)         # 别改
    ok_pop = check_pops(probe_vals)            # 别改
    print('每推一个数之后 堆序性质都成立', ok_push)                   # 别改：期望 True
    print('每弹一个数之后 堆序性质都成立', ok_pop)                    # 别改：期望 True
    show_count(1, '推完 50 个数之后 元素个数', len(probe_vals))        # 别改：期望 50
    show_label('推完 50 个数之后 元素个数', len(probe_vals))           # 别改：期望 50

    # ── 三、随机穿插 push / pop（这一段别改）────────────────────
    mixed = check_mixed(probe_vals)            # 别改
    print('穿插 push/pop 之后 弹出值都对', mixed[0])                  # 别改：期望 True
    show_count(2, '穿插之后 剩下元素个数', mixed[1])                  # 别改
    show_label('穿插之后 剩下元素个数', mixed[1])                     # 别改

    # ── 四、与 heapq 比一次耗时（这一段别改）────────────────────
    def push_all(vals):
        t = MinHeap()
        for v in vals:
            t.push(v)
        return None

    def push_all_heapq(vals):
        t = []
        for v in vals:
            heapq.heappush(t, v)
        return None

    mine_cost = best_of(push_all, VALS, repeats=REPEATS)           # 别改
    theirs_cost = best_of(push_all_heapq, VALS, repeats=REPEATS)   # 别改
    show_time(1, '推 ' + str(N) + ' 个数 手写堆', 'n=' + str(N), mine_cost)     # 别改
    show_time(2, '推 ' + str(N) + ' 个数 heapq ', 'n=' + str(N), theirs_cost)   # 别改
    print('手写堆与 heapq 的差距', round(mine_cost / max(theirs_cost, 1e-9), 2), '倍')   # 别改
    show_label('耗时对照 手写堆比heapq慢', round(mine_cost / max(theirs_cost, 1e-9), 2))  # 别改

    # ── 五、边界（这一段别改）──────────────────────────────────
    one = MinHeap()                            # 别改
    one.push(5)                                # 别改
    first_out = one.pop()                      # 别改
    print('单元素弹出', first_out, '剩下', len(one.a))               # 别改：期望 5 剩下 0
    print('空堆弹出报错', end=' ')                                    # 别改
    try:                                       # 别改
        MinHeap().pop()                        # 别改
        print('没有报错')                       # 别改
    except IndexError as exc:                  # 别改
        print('IndexError: ' + str(exc))        # 别改
    show_label('空堆弹出报错类型', 'IndexError')                       # 别改
