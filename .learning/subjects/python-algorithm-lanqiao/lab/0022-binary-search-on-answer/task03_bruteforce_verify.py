"""任务 3 · 暴力验算：二分答案真的对吗？

二分答案看起来很快，但它有一个前提：check 函数是**单调**的。这一课就是让你自己
来验——在小数据上，暴力枚举所有可能的答案（从 1 到 max(woods)），看二分答案找到
的是不是真·最大值。

任务：
  + TODO 1：暴力枚举 —— 从大到小试每一个 x，找到第一个 check 返回 True 的
  + TODO 2：对拍验证 —— 在 200+ 组随机小数据上，比对暴力结果与二分结果

木材长度 ≤ 60，答案 ≤ 60，数据足够小，暴力枚举一定能跑完。

接口：函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的两段。

跑： py task03_bruteforce_verify.py
判： py run_tests.py
"""

import random
from tools import make_woods, show_count, show_time, timed


# 把任务 1 的 check 和二分拿过来用————TODO 1 和 TODO 2 已经写过了。
# 如果还没写 task01，先回去写。
try:
    from task01_wood_cutting import check_wood, max_wood_length
except ImportError:
    # 兜底：独立版，让学生改了 task01 之后这里自然能用
    def check_wood(woods, x, M):
        cnt = 0
        for w in woods:
            cnt += w // x
        return cnt >= M

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


# ══ TODO 1 ══════════════════════════════════════════════════════
# 写 brute_max_wood_length(woods, M)：从大到小枚举 x，找到第一个可行的。
# 既然数据很小（woods ≤ 60），从 max(woods) 往下查到 1 就好。
#
# 要点：
#   for x in range(max(woods), 0, -1):
#       if check_wood(woods, x, M):
#           return x
#   return 0
def brute_max_wood_length(woods, M):
    return 0


# ══ TODO 2 ══════════════════════════════════════════════════════
# 写 verify_on_random_data(n_cases=200, max_wood_len=60, max_M=20)：
# 生成 n_cases 组随机小数据，对每组：
#   1. 用暴力找真·最大值
#   2. 用二分答案找最大值
#   3. 比较两者是否一致
# 打印不一致的组数，最后给一句总结。
#
# 要点：
#   bad = 0
#   for _ in range(n_cases):
#       n = random.randint(1, 10)
#       woods = [random.randint(1, max_wood_len) for _ in range(n)]
#       M = random.randint(1, max_M)
#       b = brute_max_wood_length(woods, M)
#       bs = max_wood_length(woods, M)
#       if b != bs:
#           bad += 1
#           print('不一致', woods, 'M=' + str(M), '暴力', b, '二分', bs)
#   print('共', n_cases, '组，不一致', bad)
#   return bad
def verify_on_random_data(n_cases=200, max_wood_len=60, max_M=20):
    return -1


if __name__ == '__main__':                     # 别改
    random.seed(20261111)                      # 别改：固定种子，判分结果一致

    # ── 先对课件数据验一下暴力对不对 ─────────────────────────
    woods = [10, 10, 10]                       # 别改
    print('暴力 M=3', brute_max_wood_length(woods, 3))     # 别改：期望 10
    print('暴力 M=6', brute_max_wood_length(woods, 6))     # 别改：期望 5
    print('暴力 M=7', brute_max_wood_length(woods, 7))     # 别改：期望 3

    # ── 对拍验证 ─────────────────────────────────────────────
    bad = verify_on_random_data(200, 60, 20)               # 别改

    print('全部不一致组数', bad)                             # 别改

    # ── 计数行 ───────────────────────────────────────────────
    show_count('01', '暴力 M=3', brute_max_wood_length(woods, 3))     # 别改
    show_count('02', '暴力 M=6', brute_max_wood_length(woods, 6))     # 别改
    show_count('03', '不一致组数', bad)                                 # 别改