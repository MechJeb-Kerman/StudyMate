"""任务 2 · 最长公共子序列：把那张状态表打印出来

课件「两维状态：最长公共子序列」那一节：这次要**同时盯住两个字符串**，所以状态是两维的——

    dp[i][j] = s 的前 i 个字符与 t 的前 j 个字符的 LCS 长度

转移分两种：末尾字符相同（$s_{i-1} = t_{j-1}$）就把这一对配起来、取 $dp[i-1][j-1] + 1$；
不同就至少有一个字符用不上，取 $\\max(dp[i-1][j], dp[i][j-1])$。

**把这张表打印出来，是这一课最省事的自查手段。** 三个规矩一眼可查：

    第一行和第一列全是 0（空串配任何串，公共子序列长度都是 0）；
    每一格只依赖**左边、上边、左上**三个方向；
    表是**逐行逐列**填的——「前 i 前 j」这种定义天然符合递推顺序，
    不需要像区间 DP（任务 3、4）那样操心枚举顺序。

接口：文件名、函数名、带 print 的行都是判分接口，别改；要写的是标着 TODO 的那几段。

跑： py task2_lcs.py
判： py run_tests.py
"""

from tools import show_count, show_label, show_pair

S1, S2 = 'ABCBDAB', 'BDCABA'                   # 别改：课件量过的那对字符串
CASES = (                                      # 别改：几组小数据（判分自己另算一遍）
    ('AGGTAB', 'GXTXAYB'),
    ('abcde', 'ace'),
    ('aaa', 'aa'),
    ('', 'ABC'),
    ('XYZ', 'PQR'),
)


# ══ TODO 1 ═════════════════════════════════════════════════
# 补 lcs(s, t)：交回 (LCS 长度, 整张 dp 表)。
#   n, m = len(s), len(t)
#   dp = [[0] * (m + 1) for _ in range(n + 1)]     长宽各多一行/一列，就是那些 0
#   for i in range(1, n + 1):
#       for j in range(1, m + 1):
#           if s[i - 1] == t[j - 1]:  dp[i][j] = dp[i - 1][j - 1] + 1
#           else:                     dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
#   交回 (dp[n][m], dp)
#   注意下标：dp 的第 i 行对应 s 的**前 i 个**字符，所以比的是 s[i - 1] 与 t[j - 1]。
#   空串也是合法的：n 或 m 是 0 时表里只剩那一行/一列的 0，答案就是 0。
def lcs(s, t):
    # TODO 1
    return 0, []


# ══ TODO 2 ═════════════════════════════════════════════════
# 补 table_shape(table, s, t)：交回 (表的行数, 表的列数, 全是 0 的那一条边上的 0 有几个)。
#   「全是 0 的那一条边」= 第一行 + 第一列：空串配任何串，公共子序列长度都是 0。
#   第三个值按「第一行的 0 个数 + 第一列的 0 个数 - 1」算（左上角那个 0 被数了两次，减掉一次）。
#   表还没建出来（空表）时交回 (0, 0, 0)。
#   这一条是给「表建对了没」用的：行数该是 len(s) + 1、列数该是 len(t) + 1。
def table_shape(table, s, t):
    # TODO 2
    return 0, 0, 0


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声

    # ── 一、课件那对字符串：答案与整张表（这几行别改）──────────────
    L, table = lcs(S1, S2)                     # 别改
    print('s =', S1, '   t =', S2)                                     # 别改
    print('最长公共子序列长度', L)                                        # 别改
    print('dp 表（s 往下、t 往右，都是前 i / 前 j 个字符）：')                # 别改
    print('     ""  ' + '  '.join(S2))                                 # 别改
    for i, row in enumerate(table):            # 别改
        tag = '"' if i == 0 else S1[i - 1]     # 别改
        print('   ' + tag.rjust(3) + '  ' + '  '.join('%2d' % v for v in row))   # 别改
    show_label('LCS 长度', L)                                            # 别改：期望 4
    show_pair('dp 表 行数列数', len(table), len(table[0]) if table else 0)   # 别改：期望 8 7
    show_count(1, 'LCS 长度', L)                                         # 别改：期望 4
    show_count(2, 'dp 表 行数', len(table))                               # 别改：期望 8
    show_count(3, 'dp 表 列数', len(table[0]) if table else 0)             # 别改：期望 7

    # ── 二、第一行与第一列（这一段别改）──────────────────────────
    first_row = list(table[0]) if table else []                        # 别改
    first_col = [row[0] for row in table] if table else []             # 别改
    blank_edge = (sum(1 for v in first_row if v == 0)
                  + sum(1 for v in first_col if v == 0)
                  - (1 if first_row and first_col and first_row[0] == 0 else 0))    # 别改
    show_label('第一行', str(first_row))                                # 别改
    show_label('第一列', str(first_col))                                # 别改
    show_label('第一行第一列 全是0', bool(table) and all(v == 0 for v in first_row)
               and all(v == 0 for v in first_col))                     # 别改：期望 True
    show_pair('第一行的0个数与第一列的0个数',
              sum(1 for v in first_row if v == 0), sum(1 for v in first_col if v == 0))   # 别改
    show_count(4, '两条边上的0共', blank_edge)                          # 别改：期望 13

    # ── 三、表的形状与右下角（这一段别改）────────────────────────
    rows, cols, edge = table_shape(table, S1, S2)                      # 别改
    show_pair('表的行数列数', rows, cols)                                # 别改：期望 8 7
    show_label('两条边上的0（由 table_shape 算）', edge)                    # 别改：期望 13
    bottom_right = table[-1][-1] if table else -1                      # 别改
    show_label('右下角', bottom_right)                                   # 别改：期望 4
    show_label('右下角等于长度', bottom_right == L and L == 4)             # 别改：期望 True
    show_count(5, '右下角', bottom_right)                                # 别改：期望 4

    # ── 四、几组小数据（这几行别改）──────────────────────────────
    for left, right in CASES:                  # 别改
        value, tb = lcs(left, right)           # 别改
        show_label('LCS ' + str(left) + ' ' + str(right), value)       # 别改
        show_label('表形状 ' + str(left) + ' ' + str(right),
                   str((len(tb), len(tb[0]) if tb else 0)))            # 别改
    show_label('空串那组是0', lcs('', 'ABC')[0] == 0)                    # 别改：期望 True
    show_label('没有公共字符那组是0', lcs('XYZ', 'PQR')[0] == 0)          # 别改：期望 True
    show_label('aaa 与 aa 是2', lcs('aaa', 'aa')[0] == 2)               # 别改：期望 True
    show_count(6, 'AGGTAB 与 GXTXAYB', lcs('AGGTAB', 'GXTXAYB')[0])     # 别改：期望 4
    show_count(7, 'abcde 与 ace', lcs('abcde', 'ace')[0])               # 别改：期望 3
