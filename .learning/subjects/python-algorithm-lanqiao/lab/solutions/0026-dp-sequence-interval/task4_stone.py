"""任务 4 · 石子合并：断点枚举，以及「枚举顺序写反」的后果

参考解。课件「断点枚举：石子合并」那一节：$dp[i][j]$ = 把第 i 堆到第 j 堆合成一堆的
最小代价，转移枚举断点 $k$、末尾再加上区间和 $\text{sum}(i..j)$——那是这次合并本身
的代价。长度**从大到小**枚举会让短区间还没算过、代价全被漏掉，答案偏小。
"""

import random
from functools import lru_cache

from tools import best_of, show_count, show_label, show_pair, show_time

ST = [4, 1, 2, 3]                              # 别改：课件量过的第一组
CASES = ([4, 1, 2, 3], [3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6])    # 别改：课件量过的三组
TRIALS = 200                                   # 别改：随机对拍的组数
SEED = 9                                       # 别改：这一段就是课件里的 random.seed(9)
SIZES = (60, 120, 240)                         # 别改：量耗时的那三档规模
REPEATS = 3                                    # 别改：每档跑这么多次，取最快的一次


def stone_dp(a, order='asc'):
    """区间 DP：交回把整排石子合成一堆的最小总代价。

    lengths 决定枚举顺序：asc 是从小到大（对的），desc 是从大到小（错的）。
    """
    n = len(a)
    if n < 2:
        return 0
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] + a[i]
    dp = [[0] * n for _ in range(n)]
    big = float('inf')
    lengths = range(2, n + 1) if order == 'asc' else range(n, 1, -1)
    for length in lengths:
        for i in range(0, n - length + 1):
            j = i + length - 1
            best = big
            for k in range(i, j):
                cand = dp[i][k] + dp[k + 1][j]
                if cand < best:
                    best = cand
            dp[i][j] = best + pre[j + 1] - pre[i]
    return dp[0][n - 1]


def stone_desc(a):
    """长度枚举写反的那一版：交回它给出的（偏小的）答案。"""
    return stone_dp(a, 'desc')


def stone_brute(a):
    """暴力版：递归枚举每一次合并的是相邻哪两堆，用 lru_cache 记在元组上。"""

    @lru_cache(maxsize=None)
    def go(t):
        if len(t) == 1:
            return 0
        best = float('inf')
        for k in range(len(t) - 1):
            cost = t[k] + t[k + 1]
            nxt = t[:k] + (cost,) + t[k + 2:]
            best = min(best, cost + go(nxt))
        return best

    return go(tuple(a))


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声

    # ── 一、课件那三组：从小到大、从大到小、暴力（这几行别改）────────
    for st in CASES:                           # 别改
        show_label('石子 ' + str(st), str(st))                              # 别改
        show_pair('从小从大 ' + str(st), stone_dp(st), stone_desc(st))        # 别改
        show_label('暴力对照 ' + str(st), stone_brute(st))                    # 别改
    show_label('[4, 1, 2, 3] 从小到大是19', stone_dp(ST) == 19)                # 别改：期望 True
    show_label('[4, 1, 2, 3] 从大到小更小', stone_desc(ST) < stone_dp(ST))      # 别改：期望 True
    show_label('[3, 4, 5, 6, 7] 从小到大是57', stone_dp([3, 4, 5, 6, 7]) == 57)     # 别改
    show_label('[1, 2, 3, 4, 5, 6] 从小到大是51', stone_dp([1, 2, 3, 4, 5, 6]) == 51)   # 别改
    show_count(1, '石子[4, 1, 2, 3] 从小到大', stone_dp(ST))                    # 别改：期望 19
    show_count(2, '石子[4, 1, 2, 3] 从大到小', stone_desc(ST))                  # 别改：期望 10
    show_count(3, '石子[3, 4, 5, 6, 7] 从小到大', stone_dp([3, 4, 5, 6, 7]))    # 别改：期望 57
    show_count(4, '石子[3, 4, 5, 6, 7] 从大到小', stone_desc([3, 4, 5, 6, 7]))  # 别改：期望 25
    show_count(5, '石子[1, 2, 3, 4, 5, 6] 从小到大', stone_dp([1, 2, 3, 4, 5, 6]))   # 别改：期望 51
    show_count(6, '石子[1, 2, 3, 4, 5, 6] 从大到小', stone_desc([1, 2, 3, 4, 5, 6])) # 别改：期望 21
    show_count(7, '暴力[4, 1, 2, 3]', stone_brute(ST))                          # 别改：期望 19

    # ── 二、三组上与暴力逐一对上（这一段别改）──────────────────────
    same_asc = all(stone_dp(st) == stone_brute(st) for st in CASES)     # 别改
    same_desc = all(stone_desc(st) == stone_brute(st) for st in CASES)  # 别改
    show_label('从小到大 三组都与暴力一致', same_asc)                     # 别改：期望 True
    show_label('从大到小 三组都与暴力一致', same_desc)                    # 别改：期望 False
    show_count(8, '从小到大 与暴力一致', same_asc)                        # 别改：期望 True

    # ── 三、边界（这一段别改）────────────────────────────────────
    show_label('单堆 0', stone_dp([7]) == 0)                            # 别改：期望 True
    show_label('两堆 是它们的和', stone_dp([3, 5]) == 8)                 # 别改：期望 True
    # 全相同时「先合哪两堆」也会影响总代价：四个 5 先合成两个 10、再合成 20，
    # 代价 10 + 10 + 20 = 40；要是先合出一个 15，后面就贵了。
    show_label('全相同 四个5是40', stone_dp([5, 5, 5, 5]) == 40)          # 别改：期望 True
    show_label('三个9是45', stone_dp([9, 9, 9]) == 45)                   # 别改：期望 True
    show_label('单堆 暴力也是0', stone_brute([7]) == 0)                   # 别改：期望 True
    show_label('空排 0', stone_dp([]) == 0)                             # 别改：期望 True
    show_count(9, '两堆 3与5', stone_dp([3, 5]))                         # 别改：期望 8
    show_count(10, '全相同四个5', stone_dp([5, 5, 5, 5]))                 # 别改：期望 40

    # ── 四、200 组随机对拍：从小到大错几组、从大到小错几组（这一段别改）──
    random.seed(SEED)                          # 别改
    bad_asc = bad_desc = 0                     # 别改
    for _ in range(TRIALS):                    # 别改
        n = random.randint(1, 7)               # 别改
        row = [random.randint(1, 20) for _ in range(n)]     # 别改
        want = stone_brute(row)                # 别改
        if stone_dp(row) != want:              # 别改
            bad_asc += 1                       # 别改
        if stone_desc(row) != want:            # 别改
            bad_desc += 1                      # 别改
    show_label('随机对拍 组数', TRIALS)                       # 别改
    show_label('从小到大 与暴力不一致组数', bad_asc)           # 别改：期望 0
    show_label('从大到小 与暴力不一致组数', bad_desc)          # 别改：期望 137
    show_label('顺序写反是错的一版', bad_desc > 0 and bad_asc == 0)     # 别改：期望 True
    show_count(11, '从小到大 不一致组数', bad_asc)             # 别改：期望 0
    show_count(12, '从大到小 不一致组数', bad_desc)            # 别改：期望 137

    # ── 五、耗时趋势（这一段别改）────────────────────────────────
    random.seed(SEED + 1)                      # 别改
    BIG = [random.randint(1, 1000) for _ in range(SIZES[-1])]      # 别改
    rows = []                                  # 别改
    for n in SIZES:                            # 别改
        data = BIG[:n]                         # 别改
        t_asc = best_of(stone_dp, data, repeats=REPEATS)           # 别改
        rows.append((n, t_asc))                # 别改
        show_time(1, '石子合并 区间DP', 'n=' + str(n), t_asc)        # 别改
    first, last = rows[0], rows[-1]            # 别改
    show_label('倍数 规模翻四倍', round(last[1] / max(first[1], 1e-9), 2))     # 别改
    # 秒数得真的量到（0.000000 说明 TODO 1 还是占位值），这一条才有意义。
    show_label('耗时没有一行是0', all(s > 0 for _, s in rows))                # 别改：期望 True
    show_count(13, '最大一档堆数', len(BIG[:SIZES[-1]]))                     # 别改：期望 240
