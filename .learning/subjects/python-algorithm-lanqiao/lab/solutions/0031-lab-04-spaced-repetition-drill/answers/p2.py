#!/usr/bin/env python3
r"""P2 · 四边形合并（区间 DP + 剩余堆数）

一堆石子排成一行，每次把**连续三堆**合成一堆，代价 = 这三堆大小之和。
每次少两堆，所以只要 (n - 1) % 2 == 0 就一定能合到只剩一堆。

状态比普通石子合并多一维：区间 [i, j] 合到还剩 l 堆是多少代价。
    dp[i][j][l] = min over 断点 k、左剩 l1 堆、右剩 l2 堆 of 两段的代价 + 合并的代价

关键在于「合并的代价」怎么算。这一段的堆数是 l1 + l2；只要还 > 3 就能继续合，
每次付一次「这一段的总和」（合并出来的那一堆就是这一段的和），堆数减 2：

    能合几次 merges = (l1 + l2 - 1) // 2      合完剩 (l1 + l2) - 2 * merges 堆
    代价 = dp[i][k][l1] + dp[k+1][j][l2] + merges × (这一段的和)

两件必须想清的事：
  1. l 这一维要留。合到只剩一堆之前，中间形态是「还剩 3 堆」——不留这一维
     就不知道现在能不能再合，也就不知道该不该把这次代价记上。
  2. 不能把「堆数已经减少」的代价重复算，也不能漏算：
     两段的代价里已经含了它们各自内部的合并，这里的 merges 只算**跨越断点**的那几次。
     区间长度 L 与剩余堆数 l 同奇偶（每次合并少 2 堆），这一条把状态砍掉一半。

为什么枚举断点 + l1 + l2 就够（不变式）：两段各自内部怎么合，与另一边无关；
    任何合法方案的最后一次跨越断点的合并，一定发生在某个断点两侧，
    两侧此前都只在自己那半区间内合过——所以按断点枚举、两侧各自取最优，不重不漏。

淘汰规模：状态 O(n^2 × 3)、转移 O(n × 9) → O(n^3)。
    n = 300 时内层约两三百万次，Python 一两秒；
    n 到 2000 就是 8×10^9 起步，一定超时——那时要换 GarsiaWachs 那一类专门算法。
"""

import sys

INF = float('inf')

# 区间长度 → 可能的剩余堆数（每次合并少 2 堆，所以同奇偶）
REACHABLE = {}
for _size in range(1, 400):
    REACHABLE[_size] = tuple(v for v in (1, 2, 3, 4, 5, 6)
                             if v % 2 == _size % 2 and v <= _size)


def solve_case(a):
    n = len(a)
    if n == 1:
        return 0
    if n % 2 == 0:
        return -1

    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] + a[i]

    # dp[i][j][l]：把 a[i..j] 合到剩 l 堆（l 与区间长度同奇偶）的最小代价
    dp = [[None] * n for _ in range(n)]
    for i in range(n):
        row = [INF] * 7
        row[1] = 0
        dp[i][i] = row

    for length in range(2, n + 1):
        levels = REACHABLE[length]
        for i in range(0, n - length + 1):
            j = i + length - 1
            cur = [INF] * 7
            segment = pre[j + 1] - pre[i]
            for k in range(i, j):
                left = dp[i][k]
                right = dp[k + 1][j]
                for l1 in REACHABLE[k - i + 1]:
                    base = left[l1]
                    if base == INF:
                        continue
                    for l2 in REACHABLE[j - k]:
                        other = right[l2]
                        if other == INF:
                            continue
                        total = l1 + l2
                        merges = (total - 1) // 2
                        rest = total - 2 * merges
                        if rest not in levels:
                            continue
                        value = base + other + merges * segment
                        if value < cur[rest]:
                            cur[rest] = value
            dp[i][j] = cur
    answer = dp[0][n - 1][1]
    return answer if answer != INF else -1


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    a = [int(x) for x in data[1:1 + n]]
    sys.stdout.write(str(solve_case(a)) + '\n')


if __name__ == '__main__':
    main()
