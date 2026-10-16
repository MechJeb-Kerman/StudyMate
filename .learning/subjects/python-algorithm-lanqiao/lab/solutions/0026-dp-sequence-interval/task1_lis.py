"""任务 1 · 最长递增子序列：DP 版、二分版，以及「那条子序列本身」

参考解。课件「以 i 结尾」与「二分版与它的 tails」两节：LIS 的状态必须带上结尾——
$dp[i]$ = 以 $a_i$ 结尾的最长递增子序列长度，答案取 $\\max(dp)$（不是 $dp[n-1]$）。
"""

import bisect
import random

from tools import best_of, show_count, show_label, show_pair, show_time

A = [10, 9, 2, 5, 3, 7, 101, 18]               # 别改：课件量过的那组数据
DUP = [5, 5, 5, 5]                             # 别改：全相同元素，两版都该给 1
TRIALS = 500                                   # 别改：随机对拍的组数
SEED = 11                                      # 别改：这一份的对拍种子
SIZES = (400, 800, 1600)                       # 别改：量耗时的那三档规模
REPEATS = 3                                    # 别改：每档跑这么多次，取最快的一次


def lis_dp(a):
    """O(n^2) 的 DP 版：交回 (最长长度, dp 数组)。"""
    n = len(a)
    if n == 0:
        return 0, []
    dp = [1] * n
    for i in range(1, n):
        for j in range(i):
            if a[j] < a[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
    return max(dp), dp


def lis_bisect(a):
    """O(n log n) 的二分版：交回 (长度, tails 数组)。

    tails[k] = 所有长度为 k+1 的递增子序列里，结尾最小的那个值。
    严格递增用 bisect_left；换成 bisect_right 就变成不下降。
    """
    tails = []
    for x in a:
        k = bisect.bisect_left(tails, x)
        if k == len(tails):
            tails.append(x)
        else:
            tails[k] = x
    return len(tails), tails


def lis_recover(a):
    """老老实实从 dp 加 prev 数组回溯出一条真正的最长递增子序列。"""
    n = len(a)
    if n == 0:
        return []
    dp = [1] * n
    prev = [-1] * n
    for i in range(1, n):
        for j in range(i):
            if a[j] < a[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j
    best = max(range(n), key=lambda i: dp[i])
    out = []
    while best != -1:
        out.append(a[best])
        best = prev[best]
    return out[::-1]


# 给好的（别改）：判「seq 是不是 a 的子序列」——按顺序在 a 里找 seq 的每一项。
# 这就是「恢复出的序列是原序列的子序列」这句话变成 True / False 的地方。
def is_subsequence(seq, a):
    """seq 按原顺序出现在 a 里就交回 True。"""
    pos = 0
    for x in a:
        if pos < len(seq) and seq[pos] == x:
            pos += 1
    return pos == len(seq)


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声

    # ── 一、课件那组数据：三个函数的答案（这几行别改）──────────────
    L, dp = lis_dp(A)                          # 别改
    L2, tails = lis_bisect(A)                  # 别改
    real = lis_recover(A)                      # 别改
    print('序列', A)                                                    # 别改
    print('dp（以每个位置结尾的长度）', dp)                                # 别改
    print('LIS 长度（DP 版）', L)                                        # 别改
    print('LIS 长度（二分版）', L2)                                      # 别改
    print('tails 数组', tails)                                          # 别改
    print('恢复出的子序列', real)                                        # 别改
    show_label('LIS 两版长度一致', L == L2 and L == 4)                   # 别改：期望 True
    show_label('tails 与恢复出的子序列相同吗', tails == real)             # 别改：期望 False
    show_pair('LIS 长度与恢复出的长度', L, len(real))                     # 别改：期望 4 4
    show_label('恢复出的就是判分要的那一条', real == [2, 5, 7, 101])       # 别改：期望 True
    show_label('恢复出的是原序列的子序列吗', is_subsequence(real, A))      # 别改：期望 True
    show_label('恢复出的严格递增',                                          # 别改：期望 True
               bool(real) and all(real[i] < real[i + 1] for i in range(len(real) - 1)))
    show_label('恢复出的长度等于 LIS 长度', bool(real) and len(real) == L and L == 4)   # 别改
    show_count(1, 'LIS 长度', L)                                            # 别改：期望 4
    show_count(2, '恢复出的长度', len(real))                                 # 别改：期望 4
    show_label('tails 数组', str(tails))                                    # 别改
    show_label('恢复出的子序列', str(real))                                  # 别改

    # ── 二、全相同元素：两版都该给 1（这一段别改）──────────────────
    d_dp = lis_dp(DUP)[0]                      # 别改
    d_bi = lis_bisect(DUP)[0]                  # 别改
    d_rc = lis_recover(DUP)                    # 别改
    show_pair('全相同元素 两版长度', d_dp, d_bi)                # 别改：期望 1 1
    show_label('全相同元素 长度都是1', d_dp == 1 and d_bi == 1)   # 别改：期望 True
    show_label('全相同元素 恢复出的长度', len(d_rc))              # 别改：期望 1
    show_count(3, '全相同元素 两版都给', d_dp if d_dp == d_bi else -1)     # 别改：期望 1

    # ── 三、边界（这一段别改）────────────────────────────────────
    show_label('空序列 两版都是0', lis_dp([])[0] == 0 and lis_bisect([])[0] == 0)   # 别改
    show_label('空序列 恢复出空表', lis_recover([]) == [])                          # 别改
    show_label('单个元素 长度1', lis_dp([7])[0] == 1 and lis_bisect([7])[0] == 1)    # 别改
    show_label('单个元素 恢复出它自己', lis_recover([7]) == [7])                     # 别改
    show_label('严格递减 长度1', lis_dp([9, 8, 7, 6])[0] == 1)                       # 别改
    show_label('严格递增 全长', lis_dp([1, 2, 3, 4, 5])[0] == 5)                     # 别改

    # ── 四、500 组随机数据：两版长度对拍（这一段别改）──────────────
    # 判分拿同一种造法（random.seed(SEED)、randint(1, 30)、长度 0~40）另造一批核一遍。
    random.seed(SEED)                          # 别改
    bad = 0                                    # 别改
    for _ in range(TRIALS):                    # 别改
        n = random.randint(0, 40)              # 别改
        row = [random.randint(1, 30) for _ in range(n)]     # 别改
        if lis_dp(row)[0] != lis_bisect(row)[0]:            # 别改
            bad += 1                           # 别改
    show_label('随机对拍 组数', TRIALS)                       # 别改
    show_label('随机对拍 两版长度不一致组数', bad)             # 别改：期望 0
    show_count(4, '随机对拍 不一致组数', bad)                  # 别改：期望 0

    # ── 五、恢复出的那条子序列在随机数据上也要成立（这一段别改）────
    random.seed(SEED + 1)                      # 别改
    rec_bad = grow_bad = len_bad = 0           # 别改
    for _ in range(TRIALS):                    # 别改
        n = random.randint(0, 30)              # 别改
        row = [random.randint(1, 30) for _ in range(n)]     # 别改
        seq = lis_recover(row)                 # 别改
        if not is_subsequence(seq, row):       # 别改
            rec_bad += 1                       # 别改
        if seq and not all(seq[i] < seq[i + 1] for i in range(len(seq) - 1)):   # 别改
            grow_bad += 1                      # 别改
        if len(seq) != lis_dp(row)[0]:         # 别改
            len_bad += 1                       # 别改
    show_label('恢复出的 不是子序列的组数', rec_bad)            # 别改：期望 0
    show_label('恢复出的 不是严格递增的组数', grow_bad)          # 别改：期望 0
    show_label('恢复出的 长度不对的组数', len_bad)               # 别改：期望 0
    show_label('恢复出的一条都没错', rec_bad == 0 and grow_bad == 0 and len_bad == 0)   # 别改

    # ── 六、两版的耗时趋势（这一段别改）──────────────────────────
    random.seed(SEED + 2)                      # 别改
    BIG = [random.randint(1, 1000) for _ in range(SIZES[-1])]      # 别改
    rows = []                                  # 别改
    for n in SIZES:                            # 别改
        data = BIG[:n]                         # 别改
        t_dp = best_of(lis_dp, data, repeats=REPEATS)              # 别改
        t_bi = best_of(lis_bisect, data, repeats=REPEATS)          # 别改
        rows.append((n, t_dp, t_bi))           # 别改
        show_time(1, 'LIS DP 版  ', 'n=' + str(n), t_dp)           # 别改
        show_time(2, 'LIS 二分版 ', 'n=' + str(n), t_bi)           # 别改
    first = rows[0]                            # 别改
    last = rows[-1]                            # 别改
    show_label('倍数 DP版 1600/400', round(last[1] / max(first[1], 1e-9), 2))     # 别改
    show_label('倍数 二分版 1600/400', round(last[2] / max(first[2], 1e-9), 2))   # 别改
    print('二分版每一档都更快',                                    # 别改：期望 True
          all(r[1] > 0 and r[2] > 0 and r[2] < r[1] for r in rows))    # 别改
    # 两版的秒数都得真的量到、且末档比首档大，这一条才谈得上「涨得更多」——
    # 全是 0.000000 时两边都是 0，比值没有意义（留白版就是那样）。
    print('规模翻四倍时 DP 版涨得更多',                              # 别改：期望 True
          0 < first[1] < last[1] and 0 < first[2] < last[2]
          and last[1] / first[1] > last[2] / first[2])           # 别改
    show_count(5, '二分版在最大一档更快', last[2] < last[1])        # 别改：期望 True
