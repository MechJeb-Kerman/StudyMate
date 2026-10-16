"""任务 4 · 轮数表与线性扫描 vs 二分时间

课件最后一段：造一张轮数表，n = 10、1000、100000、2000000，
数出二分查找的最多轮数，看它是不是每翻一倍只加一轮；
再对同一个大规模数组比一次「线性扫描找最后一个元素」与「二分找同一个目标」的耗时。

两件事：
  1. 轮数表：n 取四档，对几个关键位置（左端、中点附近、右端、不在范围内）
     各跑一遍二分，取最大轮数。打印成表。
  2. 耗时对比：对一个 n=2000000 的大数组，量一次线性扫描找到最末元素
     花了多少秒，再量一次二分找同一个目标花了多少秒。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。

跑： py task4_rounds.py
判： py run_tests.py
"""

import sys
import bisect
import time

from tools import (
    make_random, make_sorted, show, show_time, attempt, timed, best_of,
)


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 max_rounds_for(n, probes) → 对一组目标值跑二分，返回最大轮数。
#
# probes 是要查找的目标值列表。
# 对每个目标，用「左闭右开」模板跑一次二分查找，数 while 循环执行了几次，
# 取所有目标中的最大值作为这一档 n 的「最多轮数」。
#
# 实现要点：
#   · 自己写一遍二分查找的过程来数轮数（不是调 bisect）
#   · 用 a = list(range(n)) 作为有序数组
#   · 对每个 x in probes，用 while lo < hi 跑一遍，每次循环 c += 1
#   · 返回最大 c
def max_rounds_for(n, probes=None):
    if probes is None:
        probes = (0, n // 3, n // 2, n * 3 // 4, n - 1, n + 5)
    a = list(range(n))
    worst = 0
    for x in probes:
        lo, hi = 0, n
        c = 0
        # TODO: 在这里填入二分查找循环，数 c 次
        while lo < hi:
            c += 1
            _ = (lo + hi) // 2
            # 填入收缩逻辑
            break  # 删掉这一行
        if c > worst:
            worst = c
    return worst


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 linear_find_last(a, x) → 线性扫描找最后一个等于 x 的元素，返回下标。
#
# 就是逐个看过去：for i in range(len(a))，如果 a[i] == x 就记录位置。
# 遍历完返回最后记录的那个下标。
# 这与二分查找做「同一个活儿」，看的是「把整个数组从头看到尾」要多久。
def linear_find_last(a, x):
    return -1


# ══ TODO 3 ═════════════════════════════════════════════════
# 写 binary_find_last(a, x) → 用 bisect_right 找最后一个等于 x 的位置。
#
#   k = bisect.bisect_right(a, x) - 1
#   return k if k >= 0 and a[k] == x else -1
#
# 或者自己写一个左闭右开模板来等价实现。
# 注意是「最后一个」，不是第一个。
def binary_find_last(a, x):
    return -1


# ── 给好的部分：主块（别改）─────────────────────────────────────────────
if __name__ == '__main__':
    print('任务 4 · 轮数表与线性扫描 vs 二分时间')

    # ── 第 1 段：轮数表 ────────────────────────────────────────────────
    sizes = [10, 1000, 100000, 2000000]
    print('轮数表')
    for n in sizes:
        worst = max_rounds_for(n)
        show('轮数', sizes.index(n) + 1, f'n={n}', worst)

    # ── 第 2 段：线性 vs 二分 耗时对比 ─────────────────────────────────
    N = 2000000
    arr = list(range(N))
    target = N - 1  # 最后一个元素，线性搜索要找最久

    _linear_val, sec_linear = timed(linear_find_last, arr, target)
    show_time('耗时', 1, '线性', N, sec_linear)

    _binary_val, sec_binary = timed(binary_find_last, arr, target)
    show_time('耗时', 2, '二分', N, sec_binary)

    if sec_binary > 0:
        ratio = sec_linear / sec_binary
        print(f'耗时 03 倍率 n={N} 线性是二分的约 {ratio:.0f} 倍')
    else:
        print('耗时 03 倍率 n={} 线性是二分的约 — 倍'.format(N))