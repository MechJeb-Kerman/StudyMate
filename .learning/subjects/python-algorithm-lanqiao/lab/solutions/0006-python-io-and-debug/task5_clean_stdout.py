"""任务 5 · 提示文字混进标准输出（参考解）

蓝桥杯评测机把标准输入接到数据文件上、跑你的程序，然后拿**标准输出**与标准答案
**逐字比对**：多一个字符、多一行、少一个换行都算错。

而 input() 的提示走哪条流，官方文档在讲 sys.stdin 的地方写明了：stdout 用于
print() 和表达式语句的输出，**以及用于 input() 的提示符**。提示与答案走同一条流：

    $ echo 10 | py prompt_demo.py > out.txt 2> err.txt
    $ cat out.txt
    请输入 N：20
    $ cat err.txt
    （空的）

两条规矩：竞赛代码里 input() 括号不写参数；print 只打印答案本身。
"""

import sys


# ── TODO 1 · 干净的版本 ──────────────────────────────────────────────────
def clean():
    """干净版：标准输出只有答案。"""
    n = int(input())
    print(n * 2)


# ── TODO 2 · 脏的版本（把两个错都犯上）──────────────────────────────────
def dirty():
    """脏版：提示与调试串混进了标准输出。"""
    n = int(input('请输入 N：'))       # 提示会被写进 stdout
    print('答案是：', n * 2)           # 与答案无关的前缀，评测机逐字比对会判错


def solve():
    """按命令行给的模式跑一种（判分接口，别改）。"""
    which = sys.argv[1] if len(sys.argv) > 1 else 'clean'
    if which == 'clean':
        clean()
    elif which == 'dirty':
        dirty()


solve()
