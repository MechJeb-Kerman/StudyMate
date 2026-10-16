"""任务 1 · 合并果子两种写法：列表版每轮排序，堆版每轮弹两个压一个

课件「合并果子两种写法」那一节：要让总代价最小，每轮都挑**当前最轻的两堆**合并，
所以每一步都在问同一个问题——**现在最小的是哪一堆？**

    列表版 merge_list(a)：每轮 a.sort() 一次，取 a[0]、a[1] 合并，追加后**又排一次**
    堆版   merge_heap(a)：heapq.heapify(a) 一次，每轮 heappop 两次、heappush 一次

两边答案一模一样，差别只在代价：

    每轮的动作     列表版                    堆版
    找最小的两个   排序一次 O(n log n)       弹两次，各 O(log n)
    放回新堆       追加后又要重排            压入一次 O(log n)
    一轮合计       O(n log n)               O(log n)
    n 轮合计       O(n^2 log n)             O(n log n)

堆版每一步都是对数时间，因为它不需要知道其余元素的顺序——**只要保证最小那个在顶上**。
这就是「少维护一些信息」换来速度的地方。

这一份要把两种写法各写一遍，在 n = 1000 / 2000 / 4000 上各量一次，确认两边答案一致。
判分看的是**趋势**（规模翻四倍时列表版涨多少倍、堆版涨多少倍），不核对具体秒数：
秒数每次运行都会浮动，同一段代码第二次跑就不一样。

这一份另外要交出合并的顺序（`merge_plan`）：把每轮合并的两个数记下来，
前几行能直接看出「每轮取最小的两个」这条贪心规则。

接口：文件名、函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那几段。

跑： py task1_merge_fruit.py
判： py run_tests.py
"""

import heapq
import random

from tools import best_of, show_count, show_label, show_pair, show_time

SIZES = (1000, 2000, 4000)                     # 别改：与课件量过的那三档一样
REPEATS = 5                                    # 别改：每档跑这么多次，取最快的一次
SEED = 11                                      # 别改：课件那段就是 random.seed(11)


# ══ TODO 1 ═════════════════════════════════════════════════
# 补 merge_list(a)：列表版——每轮排序一次。
#   a = sorted(a) 起手；while len(a) > 1：
#     x = a.pop(0)；y = a.pop(0)；s = x + y；total += s；a.append(s)；a.sort()
#   注意 a.sort() 在**每轮末尾**都要有：少一次就变成拿旧顺序取最小值，答案会错。
#   这一版就是要留着的**对照**（它算得对、只是每轮多排一次序），别偷偷改成堆版。
def merge_list(a):
    # TODO 1
    return 0


# ══ TODO 2 ═════════════════════════════════════════════════
# 补 merge_heap(a)：堆版——每轮弹出两个最小的、压回一个和。
#   **先复制一份再动它**：h = list(a)；heapq.heapify(h)；
#   while len(h) > 1：x = heapq.heappop(h)；y = heapq.heappop(h)；
#                     s = x + y；total += s；heapq.heappush(h, s)
#
#   为什么必须复制：heappop 与 heappush 都是**原地改列表**，而这一份要在同一批数据上
#   反复量耗时。不复制的话，第一次调用就把传进来的列表掏空了，后面几次量的都是
#   一个几乎空的列表——秒数会小到 0.000000，那不是「堆快」，是「没干活」。
#   （列表版不用刻意复制：它起手那句 a = sorted(a) 自己就另起了一张表。）
#   heapify 这一句也必不可少：少了它 h 只是普通列表，堆序性质不成立。
#   循环条件写 len(h) > 1：只剩一堆时不用再合并。写成 while h 会在空列表上
#   heappop 报 IndexError: index out of range。
def merge_heap(a):
    # TODO 2
    return 0


# ══ TODO 3 ═════════════════════════════════════════════════
# 补 merge_plan(a)：用堆把合并的**过程**记下来——每轮合并出 (x, y, x + y) 三元组，
#   按顺序 append 进一个列表交回（x、y 是这一轮挑出的两个最轻的，先弹出的在前）。
#   写法与 TODO 2 只差一行：把 s 压回堆的同时，把 (x, y, s) 记进结果里。
#   这一份不只要最后的和，还要那条「每轮取最小的两个」的轨迹。
def merge_plan(a):
    # TODO 3
    return []


# 给好的（别改）：检查 merge_heap / merge_plan 有没有**动过传进来的那个列表**。
# 「反复量同一批数据」的前提就是函数不能把传进去的列表掏空，这里把它变成一个数字。
def mutates(f):
    """跑一次 f，交回「传进去的那个列表有没有被改动」。"""
    source = [5, 3, 8, 1]
    before = list(source)
    try:
        f(source)
    except Exception:
        pass
    return source != before


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声

    random.seed(SEED)                          # 别改
    DATA = [random.randint(1, 1000) for _ in range(SIZES[-1])]     # 别改

    # ── 一、两边答案必须一样（这几行别改）────────────────────────
    small = DATA[:SIZES[0]]                    # 别改：n=1000 那一份，与课件同一批
    list_total = merge_list(list(small))       # 别改
    heap_total = merge_heap(list(small))       # 别改
    print('n=1000 列表版总和', list_total)                        # 别改
    print('n=1000 堆版总和', heap_total)                          # 别改
    print('两版答案一致', list_total == heap_total)                # 别改：期望 True
    show_label('合并果子 两版答案一致', list_total == heap_total)    # 别改：期望 True
    show_count(1, '合并果子 堆版总和', heap_total)                  # 别改

    # ── 二、合并的顺序：每轮取最小的两个（这一段别改）────────────
    plan = merge_plan(list(small))             # 别改
    show_pair('合并过程 轮数', len(plan), '合并 n-1 轮')           # 别改：期望 999
    show_label('合并过程 前三轮', str(list(plan[:3])))             # 别改
    show_label('合并过程 末轮总和', str(plan[-1:]))                # 别改

    # ── 二·五、函数动没动传进来的列表（这一段别改）──────────────
    # 反复量同一批数据的前提：函数不能把传进去的列表掏空。期望两行都是 False。
    print('merge_heap 动过传进来的列表', mutates(merge_heap))         # 别改：期望 False
    print('merge_plan 动过传进来的列表', mutates(merge_plan))         # 别改：期望 False
    show_count(4, 'merge_heap 动过传进来的列表', mutates(merge_heap))   # 别改：期望 False

    # ── 三、三档规模上各量一次（下面三段的打印都是判分接口，别改）──
    rows = []                                  # 别改
    for n in SIZES:                            # 别改
        data = DATA[:n]                        # 别改
        t_list = best_of(merge_list, list(data), repeats=REPEATS)      # 别改
        t_heap = best_of(merge_heap, list(data), repeats=REPEATS)      # 别改
        rows.append((n, t_list, t_heap))       # 别改
        show_time(1, '合并果子 列表版', 'n=' + str(n), t_list)          # 别改
        show_time(2, '合并果子 堆版  ', 'n=' + str(n), t_heap)          # 别改

    first = rows[0]                            # 别改
    last = rows[-1]                            # 别改
    show_label('倍数 列表版 4000/1000', round(last[1] / max(first[1], 1e-9), 2))    # 别改
    show_label('倍数 堆版 4000/1000', round(last[2] / max(first[2], 1e-9), 2))      # 别改
    print('列表版每一档都更慢',                                             # 别改：期望 True
          all(r[1] > r[2] for r in rows))                                  # 别改
    print('规模翻四倍时列表版涨得更多',                                       # 别改：期望 True
          last[1] / max(first[1], 1e-9) > last[2] / max(first[2], 1e-9))   # 别改
    show_count(2, '堆版第一档更快', first[2] < first[1])                    # 别改

    # ── 四、边界（这一段别改）──────────────────────────────────
    print('空列表 两版都是 0', merge_list([]) == 0 and merge_heap([]) == 0)   # 别改：期望 True
    print('单堆 两版都是 0', merge_list([7]) == 0 and merge_heap([7]) == 0)   # 别改：期望 True
    print('两堆 两版都是和', merge_list([3, 5]) == 8 and merge_heap([3, 5]) == 8)   # 别改：期望 True
    show_count(3, '两堆 堆版', merge_heap([3, 5]))                            # 别改：期望 8
