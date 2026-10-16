#!/usr/bin/env python3
r"""P1 · 舞台高度（二分答案）

标准解法：答案有单调性——高度越高、能看清的人越少。
    count(h) = sum(a_i // h)
「让 count(h) >= k 的最大 h」用二分找：h 越大 count 越小，是单调不增的。
区间 [1, max(a)]，二分 O(log 10^9) 次，每次 O(n)。

为什么对：任何 h 能让 k 个人看清，比 h 小的 h' 也一定能让至少 k 个人看清
（a_i // h' >= a_i // h）——可行性是**单调**的，所以可以二分。
淘汰规模：这个解法是 O(n log V)，n 到 10^7 都还在跑；
被淘汰的不是它，而是「枚举 h 从 1 试到 max(a)」那一版（O(n·V)）。
"""

import sys


def solve_case(n, k, a):
    lo, hi = 1, max(a)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        seats = 0
        for value in a:
            seats += value // mid
            if seats >= k:
                break
        if seats >= k:
            lo = mid
        else:
            hi = mid - 1
    return lo


def main():
    data = sys.stdin.buffer.read().split()
    pos = 0
    n = int(data[pos]); pos += 1
    k = int(data[pos]); pos += 1
    a = [int(x) for x in data[pos:pos + n]]
    sys.stdout.write(str(solve_case(n, k, a)) + '\n')


if __name__ == '__main__':
    main()
