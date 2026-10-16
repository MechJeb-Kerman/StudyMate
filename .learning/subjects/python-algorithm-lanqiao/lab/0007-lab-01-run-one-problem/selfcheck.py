"""任务 3 · 写你自己的自测脚本（实验一里真正要交的东西之一）

它要和评测机做同一件事：把样例 `.in` 接到 solve 脚本的标准输入上，
拿它打印出来的东西与 `.out` 逐字比对，一组一组地报出来。

输出格式（判分按行读，**别改**）：

    样例 A1 PASS
    样例 A2 PASS
    样例 B1 PASS
    样例 B2 PASS
    自测通过 4/4 组

三条硬要求：

1. 四组样例各打印一行，标签是 A1 / A2 / B1 / B2，后面跟 `PASS` 或 `FAIL`；
2. 最后一行打印「自测通过 N/4 组」；
3. **路径按这个脚本自己所在的目录算**：`os.path.dirname(os.path.abspath(__file__))`。
   判分会把整个目录复制一份，再把 `solve_a.py` 换成一份故意写错的解，看你会不会报 FAIL——
   只报 PASS 的自测脚本给不了任何保证。

自己跑： py selfcheck.py
判分：   py run_tests.py

这一课允许你用 `sys` / `os` / `subprocess` 这三个标准库：它们是脚本的工具，不是算法的一部分。
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# 样例表（给好的，别改）：标签、输入文件、期望输出文件、跑哪个脚本
SAMPLES = [
    ('A1', 'sample_a1.in', 'sample_a1.out', 'solve_a.py'),
    ('A2', 'sample_a2.in', 'sample_a2.out', 'solve_a.py'),
    ('B1', 'sample_b1.in', 'sample_b1.out', 'solve_b.py'),
    ('B2', 'sample_b2.in', 'sample_b2.out', 'solve_b.py'),
]

TIMEOUT = 60


# ══ TODO 1 ═════════════════════════════════════════════════════════════════
# run_solver(script, in_path)：(标准输出, 退出码, 标准错误) 交回调用处。
# 提示：subprocess.run([sys.executable, 脚本路径], cwd=HERE, input=输入文本,
#       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, ...)；
#       输入文本就是 in_path 那个文件的内容。
def run_solver(script, in_path):
    return '', 1, ''


# ══ TODO 2 ═════════════════════════════════════════════════════════════════
# normalize(text)：比对前的整理——去掉每行行尾空白与末尾的空行，交回行的列表。
# 提示：与 run_tests.py 同一条规矩：行尾空白不算差别，其余逐字比。
def normalize(text):
    return []


# ══ TODO 3 ═════════════════════════════════════════════════════════════════
# check_one(label, in_name, out_name, script)：比对一组样例，打印那一行，交回 True / False。
# 提示：先跑脚本；退出码不是 0 就直接判 FAIL（把标准错误的最后一行打出来，那正是报错原因）；
#       再读 .out 文件，用 normalize 整理两份输出后比一比。
def check_one(label, in_name, out_name, script):
    return False


# ── 入口（给好的，别改）──────────────────────────────────────────────────
def main():
    passed = 0
    for label, in_name, out_name, script in SAMPLES:
        if check_one(label, in_name, out_name, script):
            passed += 1
    print('自测通过 ' + str(passed) + '/' + str(len(SAMPLES)) + ' 组')
    return 0 if passed == len(SAMPLES) else 1


sys.exit(main())
