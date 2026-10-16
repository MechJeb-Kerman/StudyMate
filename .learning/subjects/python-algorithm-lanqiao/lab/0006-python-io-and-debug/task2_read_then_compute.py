"""任务 2 · 同一份数，换行位置换掉就静默算错

题面：第一行 n m，接下来是 n×m 个整数，求所有数之和。

同 12 个数、两种排版（答案都是 78）：

    sample3.in（整齐）           sample6.in（折行）
    3 4                          3 4
    1 2 3 4                      1 2 3 4
    5 6 7 8                      5 6
    9 10 11 12                   7 8
                                 9 10 11 12

「边读边算」的版本（下面 TODO 1 里那份，给好的，别改）每调一次 input() 就吃掉一行，
于是「第 i 次循环」与「输入的第 i 行」绑死了：折行版只读到三行，最后一行没被读，
打出 36 —— 一个错字都没报。

这一份要做的是把它改写成「先读完、再算」，让两种排版都打出 78。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。

跑： Get-Content sample6.in -Raw | py task2_read_then_compute.py tokens
判： py run_tests.py
"""

import sys


def read_all():
    """唯一碰标准输入的地方（给好的，别改）。"""
    return sys.stdin.read()


# ══ TODO 1 ══════════════════════════════════════════════════
# 下面这一版是「边读边算」：input() 每调一次吃一行，读的位置与数据的行列绑死了。
# 它跑 sample3.in（整齐）得 78 是对的，跑 sample6.in（折行）得 36 是错的。
# 别改它 —— 它是这一课要看的对照。
def sum_rows_running():
    """边读边算版（给好的对照，别改）。"""
    n, m = map(int, input().split())
    total = 0
    for _ in range(n):
        row = list(map(int, input().split()))
        total += sum(row)
    return total


# ══ TODO 2 ══════════════════════════════════════════════════
# 把它改写成「先读完、再算」：整份文本已经由 read_all() 交到你手上，
# 从这里开始不要出现 input()、也不要再碰 sys.stdin。
# 提示：split() 只认空白、不区分空白长什么样，所以换行怎么排都不影响 token 表；
#      矩阵的第 i 行是从 token 表上按 m 个一段切出来的，切的位置由 n、m 决定。
# 期望：sample3.in 与 sample6.in 都得到 78。
def sum_rows_tokens(text):
    """先读完再算版：交回所有数之和。"""
    return 0


# ══ TODO 3 ══════════════════════════════════════════════════
# 把上面那份也改写成解析函数加算法两段：parse_matrix(text) 只面对字符串、
# 交回 (n, m, 二维列表)；sum_matrix(a) 只面对数据结构、不碰输入。
# 提示：这就是课件里那三条纪律的形状——读入只写在一处、解析函数里不出现读入、
#      算的部分看不到读入。
def parse_matrix(text):
    """字符串进来，数据结构出去。"""
    return 0, 0, []


def sum_matrix(a):
    """只面对数据结构：交回二维列表里所有数之和。"""
    return 0


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
