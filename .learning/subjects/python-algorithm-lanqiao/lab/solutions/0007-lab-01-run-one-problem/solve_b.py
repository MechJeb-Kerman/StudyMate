"""参考解 · 题目 B · 成绩单（实验一）

五个函数各管一件事（第 4 课）：

    read_all()          唯一碰标准输入的地方（第 6 课）
    parse_input(text)   token 表 → (n, m, grid)，grid 是 n 行 m 列的二维列表
    row_maxes(grid)     每个学生的最高分（第 5 课：推导式 + max）
    most_common(grid)   出现次数最多的分数与次数（并列取较小的分数）
    solve()             串起来，按题面要求打印两行

跑： cat sample_b1.in | py solve_b.py
判： py run_tests.py
"""

import sys


def read_all():
    """整份输入读成一个字符串。"""
    return sys.stdin.read()


def parse_input(text):
    """token 表 → (n, m, grid)。

    矩阵按空白读（第 6 课）：先把 n*m 个数取成一段 vals，再按 m 个一段切开；
    这样换行排在哪里都不影响结果——题目 B 的 `tests/b3.in` 就是换过排版的同一份数。
    """
    tokens = text.split()
    n, m = int(tokens[0]), int(tokens[1])
    vals = [int(x) for x in tokens[2:2 + n * m]]
    grid = [vals[i * m:(i + 1) * m] for i in range(n)]
    return n, m, grid


def row_maxes(grid):
    """每个学生的最高分：一行一个 max（第 5 课）。"""
    return [max(row) for row in grid]


def key_of(pair):
    """计数排序的键：次数多的在前；次数相同时分数小的在前（第 5 课：命名键函数）。"""
    score, times = pair
    return (-times, score)


def most_common(grid):
    """出现次数最多的分数与它的次数（并列取较小的分数）。

    计数用字典：查一次、加一次都是平均 O(1)（第 3 课）；
    用列表 `in` 做计数在数据一大就退化成平方级。
    """
    counts = {}
    for row in grid:
        for score in row:
            if score in counts:
                counts[score] = counts[score] + 1
            else:
                counts[score] = 1
    best_score, best_times = sorted(counts.items(), key=key_of)[0]
    return best_score, best_times


def solve():
    """按题面要求打印两行。"""
    n, m, grid = parse_input(read_all())
    print(' '.join(str(x) for x in row_maxes(grid)))
    score, times = most_common(grid)
    print(score, times)


solve()
