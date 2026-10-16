#!/usr/bin/env python3
r"""P4 · 最长公共子串（二分答案 + 双哈希）

先把问题换个说法：答案 Ans 有单调性——「有没有长度 >= L 的公共子串」这件事，
L 越大越难成立。所以二分 L，把第一个字符串里所有长度为 L 的子串的哈希值收进
集合，再看第二个字符串里有没有某个长度为 L 的子串的哈希落在集合里。

    单调性：存在长度 L 的公共子串，就存在长度 L-1 的公共子串（把它切掉尾巴）。
    所以「能行」是一段前缀：L = 0, 1, …, Ans 都能行，再大就不行——可以二分。

哈希用**双模数**（两个大质数），把碰撞概率压到实际为零；长度不只靠哈希，
二分收敛到的最长长度就是答案。

淘汰规模：O((n + m) log min(n, m))，n = m = 10^5 时约 300 万次哈希运算，Python 两三秒。
    真正会被淘汰的是「DP 求最长公共子串」那一版——它的状态是 O(nm)：
    n = m = 5000 就已经是 2.5×10^7 个状态、内存先炸；
    这道题的 n 到 10^5，所以 O(nm) 从一开始就不该写。
    后缀数组 / 后缀自动机是 O(n) 的解法，代价是写起来慢得多。
"""

import sys

MOD_A = 1000000007
MOD_B = 998244353
BASE = 131


def has_common(s, t, length):
    """有没有长度 length 的公共子串（双哈希）。"""
    if length == 0:
        return True
    if length > len(s) or length > len(t):
        return False
    high_a = pow(BASE, length, MOD_A)
    high_b = pow(BASE, length, MOD_B)
    seen = set()
    ha = hb = 0
    for i in range(len(s)):
        ha = (ha * BASE + ord(s[i])) % MOD_A
        hb = (hb * BASE + ord(s[i])) % MOD_B
        if i >= length:
            ha = (ha - ord(s[i - length]) * high_a) % MOD_A
            hb = (hb - ord(s[i - length]) * high_b) % MOD_B
        if i >= length - 1:
            seen.add((ha, hb))
    ha = hb = 0
    for i in range(len(t)):
        ha = (ha * BASE + ord(t[i])) % MOD_A
        hb = (hb * BASE + ord(t[i])) % MOD_B
        if i >= length:
            ha = (ha - ord(t[i - length]) * high_a) % MOD_A
            hb = (hb - ord(t[i - length]) * high_b) % MOD_B
        if i >= length - 1 and (ha, hb) in seen:
            return True
    return False


def solve_case(s, t):
    lo, hi = 0, min(len(s), len(t))
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if has_common(s, t, mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


def main():
    data = sys.stdin.buffer.read().split()
    s = data[0].decode()
    t = data[1].decode()
    sys.stdout.write(str(solve_case(s, t)) + '\n')


if __name__ == '__main__':
    main()
