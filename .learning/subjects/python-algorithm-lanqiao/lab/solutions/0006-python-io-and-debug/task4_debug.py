"""任务 4 · 用打印把出错范围缩小（参考解）

parse_matrix 里那处切片写错了右端（i * m + m - 1），每行少取 1 个数：
每行变成 3 个数、总和变成 54。这个 bug **不报错**，只会让结果偏小，
属于必须靠打印长度才能找出来的那一类。

定位只用了两行输出（课件的第 2 条手法）：

    诊断 n m 3 4          → 题面说每行该有 4 个数
    诊断 第 0 行长度 3 [1, 2, 3]   → 实际只有 3 个

两行一对照，结论就是「每行少了 1 个数，问题在切片的右端」。
切片右端不包含，所以要取 m 个数，右端得写 (i + 1) * m。
"""

import sys


def read_all():
    """唯一碰标准输入的地方（给好的，别改）。"""
    return sys.stdin.read()


# ── TODO 1 · 把切片右端改对 ──────────────────────────────────────────────
def parse_matrix(text):
    """第一行 n m，再 n×m 个整数 → (n, m, 二维列表)。"""
    tokens = text.split()
    n, m = int(tokens[0]), int(tokens[1])
    vals = [int(x) for x in tokens[2:2 + n * m]]
    # 原来是 i * m + m - 1：切片右端不包含，那样每行只取到 m - 1 个。
    return n, m, [vals[i * m:(i + 1) * m] for i in range(n)]


# ── TODO 2 · 打印出能定位它的那几行 ──────────────────────────────────────
def diagnose():
    """打印 n m、每行长度与内容、总和（判分按前缀读这几行）。"""
    n, m, a = parse_matrix(read_all())
    print('诊断 n m', n, m)
    for i, row in enumerate(a):
        print('诊断 第', i, '行长度', len(row), row)
    print('诊断 总和', sum(sum(row) for row in a))
    return a


# ── TODO 3 · 用 repr() 看不可见的字符 ────────────────────────────────────
def show_repr(text):
    """交回第一行的 repr()。

    注意别用 splitlines()：它把行尾的换行符去掉了，repr 出来就看不见 \\n，
    也就失去了「看清读到的是 \\n 还是空串」的意义。
    按第一个换行符切、把换行符留在左边这一行上才对。
    """
    if not text:
        return repr('')
    head, _sep, _rest = text.partition('\n')
    return repr(head + '\n') if _sep else repr(head)


def solve():
    """按命令行给的模式跑一种（判分接口，别改）。"""
    which = sys.argv[1] if len(sys.argv) > 1 else 'diagnose'
    if which == 'diagnose':
        a = diagnose()
        print('修复后 每行长度', [len(row) for row in a])
        print('修复后 总和', sum(sum(row) for row in a))
    elif which == 'repr':
        text = read_all()
        print('原文 repr', show_repr(text))
        print('原文长度', len(text.splitlines()[0]) if text.splitlines() else 0)


solve()
