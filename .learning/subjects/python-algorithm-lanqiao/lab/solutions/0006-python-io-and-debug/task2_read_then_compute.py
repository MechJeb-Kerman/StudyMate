"""任务 2 · 同一份数，换行位置换掉就静默算错（参考解）

要害就在这一组对照上：

    sample3.in（整齐）      sample6.in（折行）        正确答案
    3 4                     3 4
    1 2 3 4                 1 2 3 4
    5 6 7 8                 5 6
    9 10 11 12              7 8
                            9 10 11 12               都是 78

「边读边算」版每调一次 input() 就吃掉一行，于是「第 i 次循环」与「输入的第 i 行」
绑死了：折行版只读到三行，最后一行没被读，打出 36 —— 一个错字都没报。

修法不是「把循环次数改对」，而是换掉这个前提：**先读完、再算**。
split() 只认空白、不区分空白长什么样，所以换行怎么排都不影响 token 表；
矩阵的第 i 行是从 token 表上按 m 个一段切出来的，切的位置由 n、m 决定。
"""

import sys


def read_all():
    """唯一碰标准输入的地方（给好的，别改）。"""
    return sys.stdin.read()


# ── 给好的对照：边读边算版（别改）────────────────────────────────────────
def sum_rows_running():
    """边读边算版（给好的对照，别改）。"""
    n, m = map(int, input().split())
    total = 0
    for _ in range(n):
        row = list(map(int, input().split()))
        total += sum(row)
    return total


# ── TODO 2 · 改写成「先读完、再算」───────────────────────────────────────
def sum_rows_tokens(text):
    """先读完再算版：交回所有数之和。

    文本已经在手上，从这里开始不出现 input()、也不再碰 sys.stdin。
    """
    tokens = text.split()
    n, m = int(tokens[0]), int(tokens[1])
    vals = [int(x) for x in tokens[2:2 + n * m]]
    return sum(vals)


# ── TODO 3 · 拆成解析函数 + 算法两段 ─────────────────────────────────────
def parse_matrix(text):
    """字符串进来，数据结构出去。"""
    tokens = text.split()
    n, m = int(tokens[0]), int(tokens[1])
    vals = [int(x) for x in tokens[2:2 + n * m]]
    return n, m, [vals[i * m:(i + 1) * m] for i in range(n)]


def sum_matrix(a):
    """只面对数据结构：交回二维列表里所有数之和。"""
    return sum(sum(row) for row in a)


def solve():
    """按命令行给的模式跑一种，打印结果（判分接口，别改）。"""
    which = sys.argv[1] if len(sys.argv) > 1 else 'tokens'
    if which == 'running':
        print('边读边算', sum_rows_running())
    elif which == 'tokens':
        print('先读完再算', sum_rows_tokens(read_all()))
    elif which == 'parsed':
        n, m, a = parse_matrix(read_all())
        print('解析 n m', n, m)
        print('每行长度', [len(row) for row in a])
        print('解析后求和', sum_matrix(a))


solve()
