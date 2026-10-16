"""任务 2 · 最长公共子序列：把那张状态表打印出来

参考解。课件「两维状态：最长公共子序列」那一节：$dp[i][j]$ = s 的前 i 个字符
与 t 的前 j 个字符的 LCS 长度；末尾相同就取 $dp[i-1][j-1] + 1$，
不同就取 $\\max(dp[i-1][j], dp[i][j-1])$。第一行与第一列全是 0。
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


def lcs(s, t):
    """交回 (LCS 长度, 整张 dp 表)。"""
    n, m = len(s), len(t)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m], dp


def table_shape(table, s, t):
    """交回 (表的行数, 表的列数, 两条边上的 0 有几个)。"""
    if not table:
        return 0, 0, 0
    rows = len(table)
    cols = len(table[0])
    edge = (sum(1 for v in table[0] if v == 0)
            + sum(1 for row in table if row[0] == 0)
            - (1 if table[0][0] == 0 else 0))
    return rows, cols, edge


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
