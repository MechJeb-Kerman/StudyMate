"""任务 3 · 最长回文子序列：区间 DP，必须按区间长度从小到大枚举

课件「区间 DP：最长回文子序列」那一节：这次的状态是**一个区间**——

    dp[i][j] = s[i..j] 这段里的最长回文子序列长度

转移看两头：$s_i = s_j$ 时两头能配上、取 $dp[i+1][j-1] + 2$；
不同就至少丢一头、取 $\\max(dp[i+1][j], dp[i][j-1])$。

要害在枚举顺序：$dp[i][j]$ 依赖的是 **$dp[i+1][\\cdot]$ 与 $dp[\\cdot][j-1]$——
比它更小的区间**。所以填表顺序不能随便，**必须先算短的区间，再算长的**：

    for length in range(2, n + 1):            ← 长度从 2 往上长
        for i in range(0, n - length + 1):
            j = i + length - 1

这就是区间 DP 跟任务 2 的 LCS 最大的不同：LCS 的依赖方向（左、上、左上）天然对应
逐行逐列，而区间 DP 的依赖是「更短的区间」，**必须显式按区间长度枚举**。
单格区间 (`length == 1`) 先各自填 1——一个字符自己就是回文。

这一份的暴力版按「枚举全部子序列」写：挑出的字符保持原顺序，最多 $2^n$ 种，
$n$ 到 12 就够判了。

接口：文件名、函数名、带 print 的行都是判分接口，别改；要写的是标着 TODO 的那几段。

跑： py task3_palindrome.py
判： py run_tests.py
"""

import random

from tools import best_of, show_count, show_label, show_pair, show_time

CASES = ('character', 'abba', 'abcda', 'aaaa')     # 别改：课件量过的四组
TRIALS = 200                                       # 别改：随机对拍的组数
SEED = 7                                           # 别改：这一份的对拍种子
SIZES = (100, 200, 400)                            # 别改：量耗时的那三档规模
REPEATS = 3                                        # 别改：每档跑这么多次，取最快的一次


# ══ TODO 1 ═════════════════════════════════════════════════
# 补 lps(s)：最长回文子序列的长度（区间 DP）。
#   n = len(s)；n == 0 时交回 0。
#   dp = [[0] * n for _ in range(n)]
#   先把单格填上 1：for i in range(n): dp[i][i] = 1
#   再 for length in range(2, n + 1)：          ← **长度从 2 往上长**，这一行是本题命门
#          for i in range(0, n - length + 1):
#              j = i + length - 1
#              s[i] == s[j] 就 dp[i][j] = dp[i + 1][j - 1] + 2
#              否则           dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
#   交回 dp[0][n - 1]
#   写反了（length 从 n 往 2 减）会怎样：算长区间要用的短区间还没算过、dp 里还是 0，
#   于是「丢一头」那一路取到 0——长度整体偏小，而且小得离谱。
def lps(s):
    # TODO 1
    return 0


# ══ TODO 2 ═════════════════════════════════════════════════
# 补 lps_brute(s)：暴力版——枚举全部子序列，取其中是回文的那个最长长度。
#   写法（不递归，一层层加长）：
#       seqs = ['']
#       for ch in s:
#           seqs = seqs + [x + ch for x in seqs]      # 每个已有子序列各接上这个字符
#       best = 0
#       for x in seqs:
#           if x == x[::-1] and len(x) > best: best = len(x)
#   交回 best。空串也在 seqs 里、长度 0，所以 s 为空时自然交回 0。
#   这个版本只用来在**短串**上给个独立答案——它是 $2^n$ 的，别拿它跑长串。
def lps_brute(s):
    # TODO 2
    return 0


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声

    # ── 一、课件那四组（这几行别改）──────────────────────────────
    for s in CASES:                            # 别改
        show_label('LPS ' + s, lps(s))         # 别改
    show_label('character 是5', lps('character') == 5)     # 别改：期望 True
    show_label('abba 是4', lps('abba') == 4)               # 别改：期望 True
    show_label('abcda 是3', lps('abcda') == 3)             # 别改：期望 True
    show_label('aaaa 是4', lps('aaaa') == 4)               # 别改：期望 True
    show_count(1, 'character', lps('character'))           # 别改：期望 5
    show_count(2, 'abba', lps('abba'))                     # 别改：期望 4
    show_count(3, 'abcda', lps('abcda'))                   # 别改：期望 3
    show_count(4, 'aaaa', lps('aaaa'))                     # 别改：期望 4

    # ── 二、与暴力版对拍（这一段别改）────────────────────────────
    for s in ('a', 'ab', 'aa', 'abc', 'aab', 'racecar', 'abcba'):      # 别改
        show_pair('暴力对照 ' + s, lps(s), lps_brute(s))                # 别改
    show_label('短串上两版都对',                                         # 别改：期望 True
               all(lps(s) == lps_brute(s) for s in ('a', 'ab', 'aa', 'abc', 'aab',
                                                    'racecar', 'abcba')))    # 别改
    show_count(5, 'racecar 两版都给', lps('racecar'))                    # 别改：期望 7

    # ── 三、边界（这一段别改）────────────────────────────────────
    show_label('空串 0', lps('') == 0)                                  # 别改：期望 True
    show_label('单字符 1', lps('z') == 1)                               # 别改：期望 True
    show_label('两个相同 2', lps('zz') == 2)                            # 别改：期望 True
    show_label('两个不同 1', lps('zy') == 1)                            # 别改：期望 True
    show_label('全相同 等于长度', lps('aaaaaaaa') == 8)                   # 别改：期望 True
    show_label('与倒序串的 LCS 一致',                                     # 别改：期望 True
               lps('character') == lps('character'[::-1]))              # 别改

    # ── 四、200 组随机小串：与暴力版逐组对拍（这一段别改）──────────
    random.seed(SEED)                          # 别改
    bad = 0                                    # 别改
    for _ in range(TRIALS):                    # 别改
        n = random.randint(0, 12)              # 别改
        s = ''.join(random.choice('abc') for _ in range(n))      # 别改
        if lps(s) != lps_brute(s):             # 别改
            bad += 1                           # 别改
    show_label('随机对拍 组数', TRIALS)                     # 别改
    show_label('随机对拍 与暴力不一致组数', bad)             # 别改：期望 0
    show_count(6, '随机对拍 不一致组数', bad)                # 别改：期望 0

    # ── 五、耗时趋势（这一段别改）────────────────────────────────
    random.seed(SEED + 1)                      # 别改
    BIG = ''.join(random.choice('abcdefghij') for _ in range(SIZES[-1]))    # 别改
    rows = []                                  # 别改
    for n in SIZES:                            # 别改
        piece = BIG[:n]                        # 别改
        t_lps = best_of(lps, piece, repeats=REPEATS)               # 别改
        rows.append((n, t_lps))                # 别改
        show_time(1, 'LPS 区间DP', 'n=' + str(n), t_lps)            # 别改
    first, last = rows[0], rows[-1]            # 别改
    show_label('倍数 规模翻四倍', round(last[1] / max(first[1], 1e-9), 2))     # 别改
    show_label('规模大的一档更慢', last[1] > first[1])                        # 别改：期望 True
    show_label('耗时没有一行是0', all(s > 0 for _, s in rows))                # 别改：期望 True
    show_count(7, '最大一档长度', len(BIG[:SIZES[-1]]))                      # 别改：期望 400
