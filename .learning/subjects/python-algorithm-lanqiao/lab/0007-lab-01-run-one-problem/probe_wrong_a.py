"""判分用的「故意写错的解」（给好的，别改）

它和 solve_a.py 干的事一样，只有一处不同：**忘了去重**，直接把 n 个数都算上。

判分拿它验证你的自测脚本真的在比对：把你的 solve_a.py 换成这一份之后，
`selfcheck.py` 必须报「样例 A1 FAIL」「样例 A2 FAIL」，而 B 的两组仍然 PASS
（只报 FAIL、或永远报 PASS 的自测脚本都不算数）。

文件名是判分接口，别改；也别把它拷成 solve_a.py 当交差——它在大数据上同样是错答案。
"""

import sys


def read_all():
    return sys.stdin.read()


def parse_input(text):
    tokens = text.split()
    n = int(tokens[0])
    return n, [int(x) for x in tokens[1:1 + n]]


def count_distinct(a):
    """写错的：数了所有数，没有去重。"""
    return len(a)


def solve():
    n, a = parse_input(read_all())
    print(count_distinct(a))


solve()
