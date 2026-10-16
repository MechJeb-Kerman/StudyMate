"""任务 2 · 题目 B：换一种输入格式再来一次（第一行 n m，接下来是矩阵）

题面在 `problems.md` 的「题目 B · 成绩单」；样例：`sample_b1.in` / `.out`、`sample_b2.in` / `.out`。

五个函数各管一件事（**文件名与函数名是判分接口，别改**）：

    read_all()          唯一碰标准输入的地方
    parse_input(text)   token 表 → (n, m, grid)，grid 是 n 行 m 列的二维列表
    row_maxes(grid)     每个学生的最高分（一个列表，按学生顺序）
    most_common(grid)   出现次数最多的分数与它的次数（并列取较小的分数）
    solve()             按题面要求打印两行（这一段给好了，别改）

自己跑： cat sample_b1.in | py solve_b.py
判分：   py run_tests.py
"""

import sys


# ══ TODO 1 ═════════════════════════════════════════════════════════════════
# read_all()：整份输入读成一个字符串（与任务 1 同一个动作）。
def read_all():
    return ''


# ══ TODO 2 ═════════════════════════════════════════════════════════════════
# parse_input(text)：(n, m, grid) 交回调用处。grid 是 n 行、每行 m 个整数。
# 提示（第 6 课）：矩阵有两份模板——按行读的那版依赖「换行与题面一致」，
#       按空白读的那版先把 n*m 个数取成一段、再按 m 个一段切开。
#       题面写明了「只约定个数与先后顺序」，那该用哪一版？
def parse_input(text):
    return 0, 0, []


# ══ TODO 3 ═════════════════════════════════════════════════════════════════
# row_maxes(grid)：每个学生的最高分（第 5 课：推导式配内置函数，一行就够）。
def row_maxes(grid):
    return []


# ══ TODO 4 ═════════════════════════════════════════════════════════════════
# most_common(grid)：(分数, 次数) 交回调用处。
# 提示（第 3、5 课）：一边扫一边统计要用哪个容器？最后「次数最多、分数最小」
#       这两个条件怎么一次挑出第一条——想想第 5 课那个「排行榜」的键函数。
def most_common(grid):
    return 0, 0


# ── 入口（给好的，别改）──────────────────────────────────────────────────
def solve():
    n, m, grid = parse_input(read_all())
    print(' '.join(str(x) for x in row_maxes(grid)))
    score, times = most_common(grid)
    print(score, times)


solve()
