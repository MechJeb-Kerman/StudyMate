"""任务 1 · 五种格式解析成指定的数据结构

同一份动作要在五种输入格式上各练一遍：**先读完、再算**。每一种都写成同一个骨架：

    read_all()       唯一碰标准输入的地方
    parse_xxx(text)  字符串进来，数据结构出去
    solve()          只面对数据结构

五种格式与它们要产出的数据结构（这一段就是判分接口，别改）：

    样例文件              格式                          产出
    sample1.in            一行 8 个整数                 [3, 1, 4, 1, 5, 9, 2, 6]
    sample2.in            第一行 n，再 n 行每行一个     [3, -1, 4, 2, 7]
    sample3.in            第一行 n m，再 n×m 个整数     [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]
    sample4.in            n m、矩阵、q、再 q 组行列     [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]
                                                          [(1, 1), (3, 4)]
    sample5.in            组数 t，组间有空行、末尾空行   [[1, 2, 3], [10, 20, 30, 40]]

课件里那五份模板就是答案的形状，但别照抄——照着骨架自己写一遍，写完用
`Get-Content sample1.in -Raw | py task1_parse.py` 跑一次，对着上面那张表核。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。

跑： Get-Content sample1.in -Raw | py task1_parse.py
判： py run_tests.py
"""

import sys


# ══ TODO 1 ══════════════════════════════════════════════════
# 唯一碰标准输入的地方：把整份输入读成一个字符串。
# 提示：读法在课件「把整个输入读成一块」一节；读完之后不该再有第二处读入。
def read_all():
    """交回整份标准输入的文本。"""
    return ''


# ══ TODO 2 ══════════════════════════════════════════════════
# 按空白切分整份输入，逐个转成整数。
# 提示：不带参数的 split() 把空格、制表符、换行都当分隔符，连续几个算一个。
# 期望（对着 sample1.in）：[3, 1, 4, 1, 5, 9, 2, 6]
def parse_one_line(text):
    """sample1.in：一行 8 个整数 → 一个整数列表。"""
    return []


# ══ TODO 3 ══════════════════════════════════════════════════
# 第一行是 n，接下来 n 行每行一个整数。
# 提示：按行切分用 splitlines()；要按题面给的 n 取，不是取到末尾；
#      空行会被切成空字符串，int('') 会报 ValueError，所以要筛掉。
# 期望（对着 sample2.in）：[3, -1, 4, 2, 7]
def parse_n_then_lines(text):
    """sample2.in：第一行 n，再 n 行每行一个整数 → 整数列表。"""
    return []


# ══ TODO 4 ══════════════════════════════════════════════════
# 第一行 n m，接下来是 n×m 个整数，排成 n 行每行 m 个。
# 提示：按空白读最稳（换行位置不影响结果）——token 从头取 n*m 个，
#      再按 m 个一段切开。切片右端不包含。
# 期望（对着 sample3.in）：[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]
def parse_matrix(text):
    """sample3.in：n m 加 n×m 个整数 → (n, m, 二维列表)。"""
    return 0, 0, []


# ══ TODO 5 ══════════════════════════════════════════════════
# 还是先 n m 加矩阵，后面多一块：一行给查询个数 q，再 q 行每行两个整数。
# 提示：读的位置用一个显式下标变量拿着（课件里叫 pos），
#      每读完一段就把它往前推；这样它可打印、可对照长度。
# 期望（对着 sample4.in）：
#   matrix  [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]
#   queries [(1, 1), (3, 4)]
def parse_matrix_and_queries(text):
    """sample4.in：矩阵 + q + q 组「行 列」 → (二维列表, 元组的列表)。"""
    return [], []


# ══ TODO 6 ══════════════════════════════════════════════════
# 第一行是组数 t；每组先一行 n，再来 n 个数。组与组之间有空行，末尾还有一个空行。
# 提示：空行在按空白切分的读法下什么都不用做（它就是一种空白）；
#      每组读完要把下标推过 n 个数，别忘了那句 pos += n。
# 期望（对着 sample5.in）：[[1, 2, 3], [10, 20, 30, 40]]
def parse_groups(text):
    """sample5.in：t 组数据，组间与末尾有空行 → 列表的列表。"""
    return []


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
