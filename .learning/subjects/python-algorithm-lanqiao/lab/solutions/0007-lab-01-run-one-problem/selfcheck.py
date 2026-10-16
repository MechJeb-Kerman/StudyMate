"""参考解 · 任务 3 · 自己的自测脚本（实验一）

它做的事和评测机一样：把样例 `.in` 接到 solve 脚本的标准输入上，
拿它打印出来的东西与 `.out` 逐字比对，一组一行地报 PASS / FAIL。

输出格式（判分按行读，别改）：

    样例 A1 PASS
    样例 A2 PASS
    样例 B1 PASS
    样例 B2 PASS
    自测通过 4/4 组

比对规矩（与 run_tests.py 同一条）：行尾空白与末尾空行不算差别，其余逐字比。
路径一律按**这个脚本自己所在的目录**算：判分会把整个目录复制一份，再把 solve_a.py
换成一份故意写错的解，看你会不会报 FAIL。
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


def normalize(text):
    """逐字比对前的整理：去掉每行行尾空白与末尾的空行。"""
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def run_solver(script, in_path):
    """把 in_path 接到 script 的标准输入上跑一遍 → (标准输出, 退出码, 标准错误)。"""
    with open(in_path, encoding='utf-8') as handle:
        text = handle.read()
    done = subprocess.run(
        [sys.executable, os.path.join(HERE, script)],
        cwd=HERE, input=text, timeout=TIMEOUT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding='utf-8', errors='replace',
    )
    return done.stdout or '', done.returncode, done.stderr or ''


def check_one(label, in_name, out_name, script):
    """比对一组样例：打印那一行，交回 True / False。"""
    in_path = os.path.join(HERE, in_name)
    out_path = os.path.join(HERE, out_name)
    try:
        got, code, err = run_solver(script, in_path)
    except subprocess.TimeoutExpired:
        print('样例 ' + label + ' FAIL')
        print('  ' + script + ' 跑了 ' + str(TIMEOUT) + ' 秒还没结束（死循环？在等输入？）')
        return False

    with open(out_path, encoding='utf-8') as handle:
        want = handle.read()

    if code != 0:
        print('样例 ' + label + ' FAIL')
        tail = (err.strip().splitlines() or [''])[-1]
        print('  ' + script + ' 在 ' + in_name + ' 上报错退出（退出码 ' + str(code) + '）：' + tail)
        return False

    got_lines, want_lines = normalize(got), normalize(want)
    if got_lines == want_lines:
        print('样例 ' + label + ' PASS')
        return True

    print('样例 ' + label + ' FAIL')
    print('  跑的是 ' + script + '，输入 ' + in_name)
    print('  期望： ' + ' | '.join(want_lines))
    print('  实际： ' + ' | '.join(got_lines))
    return False


def main():
    passed = 0
    for label, in_name, out_name, script in SAMPLES:
        if check_one(label, in_name, out_name, script):
            passed += 1
    print('自测通过 ' + str(passed) + '/' + str(len(SAMPLES)) + ' 组')
    return 0 if passed == len(SAMPLES) else 1


sys.exit(main())
