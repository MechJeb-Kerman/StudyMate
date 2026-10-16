"""任务 4 · 轮数表与线性扫描 vs 二分时间

课件最后一段：造一张轮数表，n = 10、1000、100000、2000000，
数出二分查找的最多轮数，看它是不是每翻一倍只加一轮；
再对同一个大规模数组比一次「线性扫描找最后一个元素」与「二分找同一个目标」的耗时。

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
def max_rounds_for(n, probes=None):
    if probes is None:
        probes = (0, n // 3, n // 2, n * 3 // 4, n - 1, n + 5)
    a = list(range(n))
    worst = 0
    for x in probes:
        lo, hi = 0, n
        c = 0
        while lo < hi:
            c += 1
            mid = (lo + hi) // 2
            if a[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        if c > worst:
            worst = c
    return worst


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 linear_find_last(a, x) → 线性扫描找最后一个等于 x 的元素，返回下标。
def linear_find_last(a, x):
    last = -1
    for i in range(len(a)):
        if a[i] == x:
            last = i
    return last


# ══ TODO 3 ═════════════════════════════════════════════════
# 写 binary_find_last(a, x) → 用 bisect_right 找最后一个等于 x 的位置。
def binary_find_last(a, x):
    k = bisect.bisect_right(a, x) - 1
    return k if k >= 0 and a[k] == x else -1


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