"""任务 1 · 木材切割（二分答案：猜一个再验一遍）

题目：有 N 根木头，第 i 根的长度是 woods[i]。现在要把它们切成长度相等的小段（每根木头
切成整数段，剩余部分扔掉）。如果一共需要至少 M 段，最大能切成多长？

二分答案的关键两步：
  1. check(x) —— 给定候选长度 x，判断能不能切出至少 M 段
  2. 在 [1, max(woods)] 里二分猜答案

接口：函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的两段。

跑： py task01_wood_cutting.py
判： py run_tests.py
"""

from tools import make_woods, show_count, show_time, timed


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 check_wood(woods, x, M)：判断能否从 woods 中切出至少 M 段长度为 x 的小段。
#
# 要点：
#   count = 0
#   for w in woods:
#       count += w // x         每根木头能切出 w // x 段
#   return count >= M
def check_wood(woods, x, M):
    cnt = 0
    for w in woods:
        cnt += w // x
    return cnt >= M


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 max_wood_length(woods, M) —— 二分答案找最大的可行长度 x。
#
# 要点：
#   lo = 1, hi = max(woods)
#   当 lo < hi 时：
#       mid = (lo + hi + 1) // 2      ← 上取整防死循环
#       if check_wood(woods, mid, M):
#           lo = mid                   可行 → 往大猜
#       else:
#           hi = mid - 1              不可行 → 往小猜
#   return lo
def max_wood_length(woods, M):
    if not woods or M <= 0:
        return 0
    lo, hi = 1, max(woods)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if check_wood(woods, mid, M):
            lo = mid
        else:
            hi = mid - 1
    return lo if check_wood(woods, lo, M) else 0


if __name__ == '__main__':                      # 别改：这层守卫让判分 import 它时不出声
    woods = [10, 10, 10]                        # 别改
    print('木头', woods)                         # 别改

    # ── 验证 check 函数 ─────────────────────────────────────
    print('check 段长 10 段数 3', check_wood(woods, 10, 3))    # 别改：期望 True
    print('check 段长 11 段数 3', check_wood(woods, 11, 3))    # 别改：期望 False
    print('check 段长 4 段数 6',  check_wood(woods, 4, 6))     # 别改：期望 True
    print('check 段长 5 段数 7',  check_wood(woods, 5, 7))     # 别改：期望 False

    # ── 验证二分答案 ─────────────────────────────────────────
    print('M=3 最大段长', max_wood_length(woods, 3))            # 别改：期望 10
    print('M=6 最大段长', max_wood_length(woods, 6))            # 别改：期望 5
    print('M=9 最大段长', max_wood_length(woods, 9))            # 别改：期望 3

    # ── 多一点数据 ───────────────────────────────────────────
    for M in [1, 2, 4, 5, 7, 8, 15]:                           # 别改
        print('M=' + str(M), max_wood_length(woods, M))         # 别改（检查完整性）

    # ── 边界 ─────────────────────────────────────────────────
    print('空数组 M=1', max_wood_length([], 1))                 # 偏改：期望 0
    print('单根 M=1',   max_wood_length([7], 1))                # 别改：期望 7
    print('单根 M=8',   max_wood_length([7], 8))                # 别改：期望 0

    # ── 计数行 ───────────────────────────────────────────────
    ans3, _ = timed(max_wood_length, woods, 3)                  # 别改
    ans6, _ = timed(max_wood_length, woods, 6)                  # 别改
    show_count('01', 'M=3 答案', ans3)                          # 别改
    show_count('02', 'M=6 答案', ans6)                          # 别改