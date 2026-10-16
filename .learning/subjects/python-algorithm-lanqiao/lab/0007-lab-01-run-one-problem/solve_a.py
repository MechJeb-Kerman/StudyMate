"""任务 1 · 题目 A：把整条链路跑通（读入 → 求解 → 打印）

题面在 `problems.md` 的「题目 A · 不一样的数」；样例就在同目录：
`sample_a1.in` / `sample_a1.out`、`sample_a2.in` / `sample_a2.out`。

三段各一个函数（**文件名与函数名是判分接口，别改**）：

    read_all()          唯一碰标准输入的地方：把整份输入读成一个字符串
    parse_input(text)   字符串进来、数据结构出去：交出 (n, a)
    count_distinct(a)   求解：a 里不同的数有几个
    solve()             把上面三段串起来打印答案（这一段给好了，别改）

自己跑： cat sample_a1.in | py solve_a.py      （PowerShell 里 cat 就是 Get-Content）
判分：   py run_tests.py
"""

import sys


# ══ TODO 1 ═════════════════════════════════════════════════════════════════
# read_all()：把整份输入读成一个字符串。
# 提示（第 6 课）：别用 input() 一行一行读——读过的位置拿不回来，换行一变就读错。
def read_all():
    return ''


# ══ TODO 2 ═════════════════════════════════════════════════════════════════
# parse_input(text)：(n, a) 交回调用处。n 是第一个整数，a 是后面 n 个整数组成的列表。
# 提示：整份输入按空白切分成 token 表之后，换行排在哪里都不影响结果；
#       别忘了 token 表里全是字符串（第 6 课：在解析层一次转完 int）。
def parse_input(text):
    return 0, []


# ══ TODO 3 ═════════════════════════════════════════════════════════════════
# count_distinct(a)：a 里不同的数有几个。
# 提示（第 2、3 课）：这个函数在大数据上要跑多少次操作？拿不准就先写完任务 4 的
# scale_check.py 量一次——同一件事换一个容器，代价能差两个数量级。
def count_distinct(a):
    return 0


# ── 入口（给好的，别改）──────────────────────────────────────────────────
def solve():
    n, a = parse_input(read_all())
    print(count_distinct(a))


solve()
