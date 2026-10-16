"""参考解 · 题目 A · 不一样的数（实验一）

整条链路就三段，一段一个函数（第 4 课）：

    read_all()          唯一碰标准输入的地方：整份输入读成一个字符串（第 6 课）
    parse_input(text)   字符串进来、数据结构出去：交出 (n, a)
    count_distinct(a)   求解：不同的数有几个（第 3 课：集合查重是 O(n)，列表 in 是 O(n²)）
    solve()             把上面几个串起来，把答案打印出来

跑： cat sample_a1.in | py solve_a.py      （PowerShell 里 cat 就是 Get-Content）
判： py run_tests.py
"""

import sys


def read_all():
    """整份输入读成一个字符串：读入只发生一次（第 6 课的规矩）。"""
    return sys.stdin.read()


def parse_input(text):
    """token 表 → (n, a)。

    按空白切分对折行免疫：题面只约定「n 与 n 个数」的个数与先后顺序，
    换行排在哪里都不影响 tokens（第 6 课那两份矩阵样例的教训）。
    """
    tokens = text.split()
    n = int(tokens[0])
    a = [int(x) for x in tokens[1:1 + n]]
    return n, a


def count_distinct(a):
    """不同的数有几个。

    集合的 add 与 in 都是平均 O(1)，整段是 O(n)；
    换成列表 `if x in seen` 就是 O(n²)——题目 A 的大数据正是卡在这里（第 2、3 课）。
    """
    seen = set()
    for x in a:
        seen.add(x)
    return len(seen)


def solve():
    """读入 → 解析 → 求解 → 打印，一行都不多打。"""
    n, a = parse_input(read_all())
    print(count_distinct(a))


solve()
