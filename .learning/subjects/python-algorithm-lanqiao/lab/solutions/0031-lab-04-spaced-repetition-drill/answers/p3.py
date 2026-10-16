#!/usr/bin/env python3
r"""P3 · 数颜色（离线 + 树状数组）

问「区间里有多少种不同的颜色」，重复出现的颜色只能算一次。
做法：把所有询问按**右端点**从小到大处理，同时只让每种颜色在「最后一个出现
位置」上留一个 1：

    扫到位置 i 时：若颜色 c 上一次出现在 last[c]，就把 last[c] 上的 1 减掉、
    把 i 上的 1 加上（树状数组），然后处理所有右端点 == i 的询问。
    这时 [l, r] 里出现的颜色，恰好是「最后一个出现位置 >= l」的那些颜色，
    答案就是 bit.sum(r) - bit.sum(l - 1)。

为什么对（不变式）：扫到 r 时，树状数组里位置 p 上是 1 ⟺ 存在颜色 c 使
    p 是 c 在 [1, r] 中最后一次出现的位置。
    ——颜色 c 在 [l, r] 里出现过 ⟺ c 的最后一次出现位置 p_c 满足 l <= p_c <= r。
    所以 [l, r] 里的颜色数 = 树状数组在 [l, r] 上的和。

淘汰规模：O((n + q) log n)。
    离线做法在 n = q = 2×10^5 时约 800 万次操作，Python 一两秒；
    而「每个询问现场两重循环」那一版是 O(nq) = 4×10^10，
    n 到 3000、q 到 3000 就已经是 9×10^6 起步、再翻十倍就干不动了。
"""

import sys


def main():
    data = sys.stdin.buffer.read().split()
    pos = 0
    n = int(data[pos]); pos += 1
    q = int(data[pos]); pos += 1
    a = [0] * (n + 1)
    for i in range(1, n + 1):
        a[i] = int(data[pos]); pos += 1
    queries = []
    for idx in range(q):
        left = int(data[pos]); pos += 1
        right = int(data[pos]); pos += 1
        queries.append((right, left, idx))

    size = n + 2
    bit = [0] * (size + 1)

    def add(i, delta):
        while i <= size:
            bit[i] += delta
            i += i & (-i)

    def pref(i):
        total = 0
        while i > 0:
            total += bit[i]
            i -= i & (-i)
        return total

    by_right = {}
    for right, left, idx in queries:
        by_right.setdefault(right, []).append((left, idx))

    last = {}
    answer = [0] * q
    for i in range(1, n + 1):
        color = a[i]
        old = last.get(color)
        if old is not None:
            add(old, -1)
        last[color] = i
        add(i, 1)
        for left, idx in by_right.get(i, ()):
            answer[idx] = pref(i) - pref(left - 1)

    sys.stdout.write('\n'.join(str(value) for value in answer) + '\n')


if __name__ == '__main__':
    main()
