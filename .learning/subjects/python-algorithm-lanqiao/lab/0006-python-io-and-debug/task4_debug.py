"""任务 4 · 用打印把出错范围缩小

这一节的手法都围绕一件事：**先把出错的位置缩小，再改代码**。在二十行代码里随机加
print，只会让输出变长。可操作的手法有六条（课件「用打印定位错误」一节）：

  1. 先跑最小样例（题面给的第一组，别从大样例开始）
  2. 打印数据结构与它的长度，与题面给的 n、m 对一遍
  3. 用 repr() 看不可见的字符（引号、\\n、多余空格）
  4. 把「读」与「算」分开打印：数据结构对而答案错 → 问题在算法；数据结构就错 → 先修解析
  5. 二分注释掉一半，看答案从哪一半开始不对
  6. 打印指针下标（pos 与 len(tokens)），一句话告诉你读多了还是读少了

这一份里的 parse_matrix 是**故意写错的**（切片右端少取了 1 个数）：
每行会变成 3 个数、总和变成 54。这个 bug 不报错，只会让结果偏小，
属于必须靠打印长度才能找出来的那一类。

要写的是标着 TODO 的那几段：先用打印把手法定下来，再把切片改对。
带 print 的行是判分接口，别改。

跑： Get-Content sample3.in -Raw | py task4_debug.py diagnose
判： py run_tests.py
"""

import sys


def read_all():
    """唯一碰标准输入的地方（给好的，别改）。"""
    return sys.stdin.read()


# ══ TODO 1 ══════════════════════════════════════════════════
# 下面这个解析函数里有一处切片写错了：每行少取了 1 个数。
# 先别改它 —— 先把 TODO 2 的打印写出来，让自己看见「每行长度是 3，而题面说 m 是 4」。
# 找到之后，把右端改对（提示：切片右端不包含，所以右端该写什么自己推）。
def parse_matrix(text):
    """第一行 n m，再 n×m 个整数 → (n, m, 二维列表)。这里有一处 bug。"""
    tokens = text.split()
    n, m = int(tokens[0]), int(tokens[1])
    vals = [int(x) for x in tokens[2:2 + n * m]]
    return n, m, [vals[i * m:i * m + m - 1] for i in range(n)]


# ══ TODO 2 ══════════════════════════════════════════════════
# 打印出「能定位这个 bug」的那几行。要打出四样东西（各占一行，前缀别改）：
#   · 题面给的 n 与 m
#   · 每一行的长度与内容（用 enumerate 拿行号）
#   · 总和的当前值
# 提示：第 2 条手法就够用了 —— 输出里的 n m 说每行该有 4 个数，
#      紧接着的「行长度」说只有 3 个，结论当场就出来了。
def diagnose():
    """打印 n m、每行长度与内容、总和（判分按前缀读这几行）。"""
    n, m, a = parse_matrix(read_all())
    # TODO 2：把下面三行 print 补全（前缀别改）。
    #   print('诊断 n m', ...)
    #   for i, row in enumerate(a): print('诊断 第', i, '行长度', ..., ...)
    #   print('诊断 总和', ...)
    return a


# ══ TODO 3 ══════════════════════════════════════════════════
# 用 repr() 看不可见的字符：把**第一行**原文的真实形状打出来。
# 提示：repr 会把引号、\n、多余空格显示出来 —— 空行导致的 ValueError 靠它一眼
#      分清读到的是 '\n' 还是 ''。判分拿 sample1.in 试它（那一行末尾有个换行符）。
# 注意：别用 splitlines() 取这一行——它会把行尾的换行符去掉，repr 出来就看不见
#      \n 了，这一条手法也就白做了。按第一个换行符切、把换行符留在左边这一行上。
# 期望（对着 sample1.in）："'3 1 4 1 5 9 2 6\n'"
def show_repr(text):
    """交回第一行的 repr()。"""
    return ''


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
