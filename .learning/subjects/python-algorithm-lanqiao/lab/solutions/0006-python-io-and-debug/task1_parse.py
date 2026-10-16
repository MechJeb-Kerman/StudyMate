"""任务 1 · 五种格式解析成指定的数据结构（参考解）

同一份动作在五种输入格式上各练一遍：**先读完、再算**。骨架都是同一个：

    read_all()       唯一碰标准输入的地方
    parse_xxx(text)  字符串进来，数据结构出去
    solve()          只面对数据结构

五种格式的产出（与课件写死的结构逐字一致）：
    sample1.in   [3, 1, 4, 1, 5, 9, 2, 6]
    sample2.in   [3, -1, 4, 2, 7]
    sample3.in   [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]
    sample4.in   同一个矩阵 + [(1, 1), (3, 4)]
    sample5.in   [[1, 2, 3], [10, 20, 30, 40]]

关键的一条：矩阵**按空白读**（token 从头取 n*m 个、再按 m 个一段切开），
不按行切——sample6.in 与 sample3.in 是同一份数、换行位置被打乱，
按行切会读出 [[1, 2, 3, 4], [5, 6], [7, 8]]。
"""

import sys


def read_all():
    """整份输入读成一个字符串。读入只发生在这里，而且只发生一次。"""
    return sys.stdin.read()


# ── TODO 2 · 单行多整数 → 整数列表 ────────────────────────────────────────
def parse_one_line(text):
    """sample1.in：一行 8 个整数 → 一个整数列表。"""
    return [int(x) for x in text.split()]


# ── TODO 3 · 多行整数（第一行给 n）→ 整数列表 ─────────────────────────────
def parse_n_then_lines(text):
    """sample2.in：第一行 n，再 n 行每行一个整数 → 整数列表。"""
    lines = [line for line in text.splitlines() if line.strip()]
    n = int(lines[0])
    return [int(line) for line in lines[1:n + 1]]


# ── TODO 4 · 矩阵 n×m → 二维列表 ──────────────────────────────────────────
def parse_matrix(text):
    """sample3.in：n m 加 n×m 个整数 → (n, m, 二维列表)。"""
    tokens = text.split()
    n, m = int(tokens[0]), int(tokens[1])
    vals = [int(x) for x in tokens[2:2 + n * m]]
    return n, m, [vals[i * m:(i + 1) * m] for i in range(n)]


# ── TODO 5 · 混合行列 → 矩阵 + 查询两块 ───────────────────────────────────
def parse_matrix_and_queries(text):
    """sample4.in：矩阵 + q + q 组「行 列」 → (二维列表, 元组的列表)。"""
    tokens = text.split()
    n, m = int(tokens[0]), int(tokens[1])
    pos = 2
    vals = [int(x) for x in tokens[pos:pos + n * m]]
    pos += n * m
    matrix = [vals[i * m:(i + 1) * m] for i in range(n)]
    q = int(tokens[pos])
    pos += 1
    queries = []
    for _ in range(q):
        r, c = int(tokens[pos]), int(tokens[pos + 1])
        pos += 2
        queries.append((r, c))
    return matrix, queries


# ── TODO 6 · 多组数据 → 列表的列表 ────────────────────────────────────────
def parse_groups(text):
    """sample5.in：t 组数据，组间与末尾有空行 → 列表的列表。"""
    tokens = text.split()
    t = int(tokens[0])
    pos = 1
    groups = []
    for _ in range(t):
        n = int(tokens[pos])
        pos += 1
        groups.append([int(x) for x in tokens[pos:pos + n]])
        pos += n
    return groups


def solve():
    """按命令行给的格式名跑其中一份样例，打印一行结果（判分接口，别改）。

    一份程序只用一种读入口、而且只读一次，所以这里一次只跑一种格式：
    判分脚本按格式各起一次进程，把对应的样例接到标准输入上。
    """
    which = sys.argv[1] if len(sys.argv) > 1 else 'one'
    text = read_all()
    if which == 'one':
        print('01 单行多整数', parse_one_line(text))
    elif which == 'lines':
        print('02 多行整数', parse_n_then_lines(text))
    elif which == 'matrix':
        n, m, a = parse_matrix(text)
        print('03 矩阵 n m', n, m)
        print('03 矩阵', a)
    elif which == 'mq':
        matrix, queries = parse_matrix_and_queries(text)
        print('04 矩阵与查询', matrix)
        print('04 查询', queries)
    elif which == 'groups':
        print('05 多组数据', parse_groups(text))


solve()
