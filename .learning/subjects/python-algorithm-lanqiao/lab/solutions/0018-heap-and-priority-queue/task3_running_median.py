"""任务 3 · 数据流中位数：两个堆一起用，中位数就在堆顶上

课件「对顶堆求中位数」那一节：**两个堆一起用**——
一个存较小的一半（用负数存成最大堆），一个存较大的一半（最小堆），两个堆的大小差不超过一。

每来一个数只做三件事（课件那段代码一行一行照抄）：

    1. 先无条件压进 lo            heapq.heappush(lo, -v)
    2. 把 lo 顶上那个挪到 hi      heapq.heappush(hi, -heapq.heappop(lo))
    3. hi 比 lo 长就把 hi 顶挪回来 if len(hi) > len(lo): heappush(lo, -heappop(hi))

维持的是两条**不变式**（与第 14 课二分的「循环不变式」是同一套思路）：
先说清每一步结束时什么一定成立，再写代码维持它。

    · lo 里的每个数都不大于 hi 里的每个数（第 2 步把 lo 的最大值挪走，就是在维持它）
    · 两个堆的长度差不超过一（第 3 步把 hi 的长度压回去，就是在维持它）

这两条一立住，中位数只能出现在两个堆顶里：总数为奇数时 lo 顶上是中位数，
偶数时取两个堆顶的平均。

这一份除了中位数序列，还要**单独打印每一步之后两个堆的长度与堆顶**，
用来看那两条不变式是怎么一步一步维持住的。

接口：文件名、函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那几段。

跑： py task3_running_median.py
判： py run_tests.py

参考解。与任务目录里的同名文件只差标着 TODO 的两段。
"""

import heapq

from tools import show_count, show_label, show_pair

STREAM = (5, 15, 1, 3, 8, 7, 9, 10, 6, 11, 4)      # 别改：与课件那串数一样
REPEATS = 50                                        # 别改：量耗时就跑这么多次


# ══ TODO 1 ═════════════════════════════════════════════════
# 补 running_median(stream)：按课件的对顶堆写法，每来一个数就交出一个中位数，
#   交回的是一条与 stream 等长的序列（不是只交回最后一个）。
#     lo = []（存负数，所以它是最大堆）；hi = []（最小堆）；out = []
#     for v in stream:
#         heapq.heappush(lo, -v)
#         heapq.heappush(hi, -heapq.heappop(lo))
#         if len(hi) > len(lo):
#             heapq.heappush(lo, -heapq.heappop(hi))
#         if len(lo) > len(hi):
#             out.append(-lo[0])                总数为奇数：lo 顶上是中位数
#         else:
#             out.append((-lo[0] + hi[0]) / 2)  偶数个：两个堆顶的平均
#   注意 hi 为空时不能去取 hi[0]：上面第 2 步保证 hi 至少有一个数之后才轮到取值，
#   顺序写反了会在单个元素上就报 IndexError: index out of range。
def running_median(stream):
    """对顶堆：每来一个数交出一个中位数。"""
    lo = []          # 较小的一半，用负数存成最大堆
    hi = []          # 较大的一半，最小堆
    out = []
    for v in stream:
        heapq.heappush(lo, -v)
        heapq.heappush(hi, -heapq.heappop(lo))
        if len(hi) > len(lo):
            heapq.heappush(lo, -heapq.heappop(hi))
        if len(lo) > len(hi):
            out.append(-lo[0])
        else:
            out.append((-lo[0] + hi[0]) / 2)
    return out


# ══ TODO 2 ═════════════════════════════════════════════════
# 补 median_state(stream)：交回「每一步之后两个堆的状态」，一步一步走给你看。
#
#     lo、hi 与 TODO 1 完全一样地维护（三步一步都不能少）；
#     每处理完一个数 v，就往结果里 append 一个**四元组**：
#         (len(lo), -lo[0], len(hi), hi[0] if hi else None)
#     也就是「lo 的长度、lo 的堆顶（原数，记着它是负数存的要转回来）、
#             hi 的长度、hi 的堆顶（hi 为空时给 None）」。
#   hi 为空时不能写 hi[0]（会 IndexError），要写成 hi[0] if hi else None。
def median_state(stream):
    """每一步之后两个堆的长度与堆顶，用来看两条不变式怎么维持。"""
    lo = []
    hi = []
    out = []
    for v in stream:
        heapq.heappush(lo, -v)
        heapq.heappush(hi, -heapq.heappop(lo))
        if len(hi) > len(lo):
            heapq.heappush(lo, -heapq.heappop(hi))
        out.append((len(lo), -lo[0], len(hi), hi[0] if hi else None))
    return out


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声

    # ── 一、中位数序列（这几行别改）────────────────────────────
    med = running_median(STREAM)               # 别改
    print('数据流', list(STREAM))                                  # 别改
    print('中位数', [int(m) if m == int(m) else m for m in med])    # 别改
    show_label('中位数 个数', len(med))                             # 别改：期望 11
    show_label('中位数 是每一步的序列', isinstance(med, list) and len(med) == len(STREAM))   # 别改：期望 True

    # ── 二、每一步之后两个堆的长度与堆顶（这一段别改）────────────
    states = median_state(STREAM)              # 别改
    for i, row in enumerate(states, 1):        # 别改
        lo_n, lo_top, hi_n, hi_top = row       # 别改
        print('第' + str(i) + ' 步', lo_n, lo_top, hi_n, hi_top,
              ' 中位数', med[i - 1] if i <= len(med) else '?')   # 别改
    show_label('不变式 每一步都有序', True)                          # 别改
    show_pair('不变式 最后一行的两个堆顶', str(states[-1][1]) if states else '空',
              str(states[-1][3]) if states else '空')                # 别改

    # ── 三、两条不变式的两条计数（这一段别改）──────────────────
    show_count(1, '不变式 长度差不超过一', all(
        abs(row[0] - row[2]) <= 1 for row in states))                # 别改：期望 True
    show_count(2, '不变式 lo 顶不大于 hi 顶', all(
        row[3] is None or row[1] <= row[3] for row in states))       # 别改：期望 True

    # ── 四、边界（这一段别改）──────────────────────────────────
    print('空流 中位数', running_median([]))                         # 别改：期望 []
    print('一个数 中位数', running_median([7]))                      # 别改：期望 [7]
    print('两个数 中位数', running_median([4, 9]))                   # 别改：期望 [4, 6.5]
    print('第一个数的状态', median_state([7]))                       # 别改：期望 [(1, 7, 0, None)]
    show_count(3, '单个数 的中位数', running_median([7])[0] if running_median([7]) else 0)
