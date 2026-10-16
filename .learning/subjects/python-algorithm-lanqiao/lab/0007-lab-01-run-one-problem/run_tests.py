#!/usr/bin/env python3
"""lab 0007 · 自动判分：跑你的 solve 脚本，按层给反馈。

用法（在 lab/0007-lab-01-run-one-problem/ 目录里）：

    py run_tests.py

判分分五层，**每层的失败指向不同的原因**——别只盯一个「不通过」：

  第 1 层 · 样例（题面给的四组，小数据）         → 读入 / 求解 / 输出 哪一段没接上
  第 2 层 · 换行被打乱的小数据（同一份数、另一种排版）→ 输入解析层（先读完、再算）
  第 3 层 · 大数据（题目 A 十万个数，限时 2 秒）  → 复杂度：容器选错还是写错了
  第 4 层 · 你自己的自测脚本 selfcheck.py        → 它是不是真的在比对
                                                   （判分会拿一份故意写错的解试它）
  第 5 层 · 规模对照 scale_check.py              → 列表 in 与集合 in 的量级差，
                                                   以及「放大 10 倍」的估算

第 1、2 层没过时，第 3–5 层直接跳过：样例都没过，大数据组的失败信息没有参考价值
（这正是「写完直接扔进大测试」的那个坑）。

比对的规矩与评测机一样：只看标准输出，行尾空白与末尾空行不算差别，其余逐字比。

退出码：0 = 五层都过；1 = 还有没过的。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

SAMPLE_TIMEOUT = 20.0        # 样例与折行组：只拦死循环、等输入这类
BIG_TIMEOUT = 2.0            # 大数据组：题面时限 1 秒，本机放宽到 2 秒
SELFCHECK_TIMEOUT = 120.0    # 自测脚本自己会起子进程，给它宽一点

# ── 第 1 层：题面给的四组样例 ───────────────────────────────────────────────
LAYER1 = [
    ('A1', 'sample_a1.in', 'sample_a1.out', 'solve_a.py'),
    ('A2', 'sample_a2.in', 'sample_a2.out', 'solve_a.py'),
    ('B1', 'sample_b1.in', 'sample_b1.out', 'solve_b.py'),
    ('B2', 'sample_b2.in', 'sample_b2.out', 'solve_b.py'),
]

# ── 第 2 层：同一份数、换行位置不同（第 4 个字段：它是谁的另一种排版）────────
LAYER2 = [
    ('A3', 'tests/a3.in', 'tests/a3.out', 'solve_a.py', 'A2'),
    ('B3', 'tests/b3.in', 'tests/b3.out', 'solve_b.py', 'B2'),
]

# ── 第 3 层：大数据（跑不完就是复杂度问题）──────────────────────────────────
LAYER3 = [
    ('A-大数据', 'tests/a_big.in', 'tests/a_big.out', 'solve_a.py'),
    ('B-大数据', 'tests/b_big.in', 'tests/b_big.out', 'solve_b.py'),
]

SELFCHECK_LINE_RE = re.compile(r'^样例\s*(A1|A2|B1|B2)\s*(PASS|FAIL)\s*$')
LIST_RE = re.compile(r'^n=(\d+) 列表 in 用时 ([0-9.]+) 秒 不同元素 (\d+)$')
SET_RE = re.compile(r'^n=(\d+) 集合 in 用时 ([0-9.]+) 秒 不同元素 (\d+)$')
PRED_RE = re.compile(r'^列表版放大 10 倍预计 ([0-9.]+) 秒 超出 1 秒时限 (True|False)$')

MISSING_HINT = ('先在目录里建好这个文件（文件名是判分接口，别改）；'
                '留白版里标着 TODO 的那几段就是要你写的')

# 文件名与函数名是判分接口：这一段对应第 4 课「把一段代码变成函数」那条验收
INTERFACES = {
    'solve_a.py': ('read_all', 'parse_input', 'count_distinct', 'solve'),
    'solve_b.py': ('read_all', 'parse_input', 'row_maxes', 'most_common', 'solve'),
    'selfcheck.py': ('run_solver', 'normalize', 'check_one'),
    'scale_check.py': ('distinct_by_list', 'distinct_by_set'),
}


def check_interface(report, filename):
    """文件里有没有按给好的名字分段；缺了哪一个会点名。"""
    names = INTERFACES[filename]
    text = read_text(HERE / filename)
    if text is None:
        report.check(False, '还没建这个文件：' + filename)
        return
    gone = [name for name in names if 'def ' + name + '(' not in text]
    if gone:
        report.check(False, filename + ' 里没找到这几个函数定义：' + '、'.join(gone) + '\n'
                      + '文件名与函数名是给好的接口，别改；要写的是它们里面的 TODO')
        return
    report.check(True, filename + ' 按给好的名字分成了 ' + str(len(names)) + ' 个函数：'
                  + '、'.join(names))


def read_text(path):
    """读文件；读不出来交回 None。"""
    try:
        with open(path, encoding='utf-8', errors='replace') as handle:
            return handle.read()
    except OSError:
        return None


def normalize(text):
    """逐字比对前的整理：去掉每行行尾空白与末尾的空行。"""
    lines = [line.rstrip() for line in (text or '').splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def brief(lines, limit=3, width=90):
    """把几行结果压成一行短句（打印反馈用）。"""
    if not lines:
        return '（一行都没有）'
    shown = []
    for line in lines[:limit]:
        text = line if line else '（空行）'
        shown.append(text if len(text) <= width else text[:width] + '…')
    if len(lines) > limit:
        shown.append('…（还有 ' + str(len(lines) - limit) + ' 行）')
    return ' | '.join(shown)


def run_solver(script, in_path, timeout):
    """跑一个脚本，把输入文件接到它的标准输入上 → (状态, 标准输出, 备注)。

    状态：ok / missing / crash / timeout。
    """
    script_path = HERE / script
    if not script_path.is_file():
        return 'missing', '', '还没建这个文件：' + script
    in_file = HERE / in_path
    if not in_file.is_file():
        return 'missing', '', '判分用的数据文件不在了：' + in_path + '（别删 tests/ 与 sample_*.in）'
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    try:
        done = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(HERE), env=env, timeout=timeout,
            input=in_file.read_text(encoding='utf-8', errors='replace'),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return 'timeout', '', ''
    if done.returncode != 0:
        tail = (done.stderr or '').strip().splitlines()[-3:]
        return 'crash', done.stdout or '', ('脚本报错退出（退出码 ' + str(done.returncode) + '）：\n'
                                            + '\n'.join(tail))
    return 'ok', done.stdout or '', ''


def expected_lines(out_path):
    """期望输出那几行（读 .out 文件）。"""
    return normalize(read_text(HERE / out_path) or '')


def run_plain(script, timeout):
    """跑一个不读输入的脚本（scale_check.py 自己造数据）→ (状态, 标准输出, 备注)。"""
    script_path = HERE / script
    if not script_path.is_file():
        return 'missing', '', '还没建这个文件：' + script
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    try:
        done = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(HERE), env=env, timeout=timeout,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return 'timeout', '', script + ' 跑了 ' + str(timeout) + ' 秒还没结束'
    if done.returncode != 0:
        tail = (done.stderr or '').strip().splitlines()[-3:]
        return 'crash', done.stdout or '', ('脚本报错退出（退出码 ' + str(done.returncode) + '）：\n'
                                            + '\n'.join(tail))
    return 'ok', done.stdout or '', ''


class Report:
    """收集每一层的 PASS / FAIL 行：一层里几条检查，全 PASS 才算这层过。"""

    def __init__(self, title):
        self.title = title
        self.lines = []
        self.failed = 0

    def check(self, ok, message):
        self.lines.append(('PASS' if ok else 'FAIL', message))
        if not ok:
            self.failed += 1

    def passed(self):
        return self.failed == 0 and bool(self.lines)

    def show(self):
        print(self.title)
        for kind, message in self.lines:
            for index, piece in enumerate(message.split('\n')):
                head = '  ' + kind + '  ' if index == 0 else '        '
                print(head + piece)
        print()


# ══════════════════════════════════════════════════════════════════
# 第 1、2 层：样例与折行组
# ══════════════════════════════════════════════════════════════════

def check_case(report, label, in_name, out_name, script, timeout, twin=None):
    """跑一组数据、比对期望输出；把结论写进 report。"""
    want = expected_lines(out_name)
    status, out, note = run_solver(script, in_name, timeout)

    twin_hint = ''
    if twin:
        twin_hint = ('\n这一组与样例 ' + twin + ' 是**同一份数**，只是换行位置不同，答案必须一样。\n'
                     '如果你在样例 ' + twin + ' 上本来是对的，那问题在输入读的那一层：\n'
                     '用 input() 逐行读，会把「第几次读」与「数据的第几行」绑在一起。按第 6 课\n'
                     '的规矩改：一次读完（sys.stdin.read()）→ 按空白切分 → 解析成数据结构，\n'
                     '算法只看数据结构。如果样例 ' + twin + ' 也没过，先修好它，这一组自然会跟着对。')

    if status == 'missing':
        report.check(False, label + '  ' + note + '——' + MISSING_HINT)
        return False
    if status == 'crash':
        report.check(False, label + '  ' + script + ' 在 ' + in_name + ' 上报错退出：\n'
                      + note + '\n先按报错的行号看过去；' + script + ' 里那一行是它指的地方'
                      + twin_hint)
        return False
    if status == 'timeout':
        report.check(False, label + '  ' + script + ' 在 ' + in_name + ' 上跑了 '
                      + str(timeout) + ' 秒还没结束（死循环？还是在等输入？）')
        return False
    got = normalize(out)
    if got == want:
        report.check(True, label + '  ' + script + ' 打出 ' + brief(want)
                     + '，与 ' + out_name + ' 逐字一致')
        return True

    shown = brief(got)
    if twin:
        report.check(False, label + '  期望 ' + brief(want) + '，实际 ' + shown + twin_hint)
        return False
    if not got:
        report.check(False, label + '  期望 ' + brief(want) + '，实际一行都没打印\n'
                      + 'solve() 里还有没填的 TODO（或者打印那一行被删了）')
        return False
    report.check(False, label + '  期望 ' + brief(want) + '，实际 ' + shown + '\n'
                  + '把「读入解析」与「求解」分开各打印一次（第 6 课的定位手法）：\n'
                  + '解析出来的数据结构对不对（个数、维度、元素类型），不对就是解析层；\n'
                  + '数据结构对了而答案不对，才是求解那一段。')
    return False


def layer12():
    """第 1 层与第 2 层：都过了才允许往下跑。"""
    report1 = Report('第 1 层 · 样例（题面给的四组，小数据）')
    for label, in_name, out_name, script in LAYER1:
        check_case(report1, label, in_name, out_name, script, SAMPLE_TIMEOUT)
    check_interface(report1, 'solve_a.py')
    check_interface(report1, 'solve_b.py')
    report1.show()

    report2 = Report('第 2 层 · 换行被打乱的小数据（同一份数、另一种排版）')
    for label, in_name, out_name, script, twin in LAYER2:
        check_case(report2, label, in_name, out_name, script, SAMPLE_TIMEOUT, twin=twin)
    report2.show()
    return report1, report2


# ══════════════════════════════════════════════════════════════════
# 第 3 层：大数据
# ══════════════════════════════════════════════════════════════════

BIG_TIMEOUT_HINT = {
    'A-大数据': ('这一组是 100000 个数。先把「你的循环一共要跑多少次」数出来：\n'
                 '列表查重是一次次比过去（约 n²/2 次比较，n=10^5 就是几十亿次）；\n'
                 '换成集合或字典，每次查是平均 O(1)，整段是 O(n)（第 2、3 课）。\n'
                 '这不是「写错了」，是容器选错——任务 4 的 scale_check.py 量的就是这个差距。'),
    'B-大数据': ('这一组是 300×100 个数。先看解析：100000 这个量级的 token 要用一次读完的写法\n'
                 '（sys.stdin.read().split()），逐行 input() 在 30000 个数上就开始拖时间；\n'
                 '再看计数那一层用的是不是字典（第 3 课）。'),
}


def check_big(report, label, in_name, out_name, script):
    want = expected_lines(out_name)
    started = time.perf_counter()
    status, out, note = run_solver(script, in_name, BIG_TIMEOUT)
    elapsed = time.perf_counter() - started
    hint = BIG_TIMEOUT_HINT.get(label, '')
    if status == 'missing':
        report.check(False, label + '  ' + note + '——' + MISSING_HINT)
        return
    if status == 'timeout':
        report.check(False, label + '  超过 ' + str(BIG_TIMEOUT) + ' 秒还没跑完（题面时限 1 秒）\n'
                      + hint)
        return
    if status == 'crash':
        report.check(False, label + '  ' + script + ' 在 ' + in_name + ' 上报错退出：\n' + note)
        return
    got = normalize(out)
    if got == want:
        report.check(True, label + '  ' + str(round(elapsed, 3)) + ' 秒跑完，答案与 '
                     + out_name + ' 一致（限时 ' + str(BIG_TIMEOUT) + ' 秒）')
        return
    report.check(False, label + '  跑完了（' + str(round(elapsed, 3)) + ' 秒）但答案不对：\n'
                  + '期望 ' + brief(want) + '\n实际 ' + brief(got) + '\n'
                  + '没超时说明复杂度没问题，问题在正确性：先确认解析出来的数据结构\n'
                  + '（个数、维度）与题面一致，再看求解在数据量变大时的边界。')


# ══════════════════════════════════════════════════════════════════
# 第 4 层：学生自己的自测脚本
# ══════════════════════════════════════════════════════════════════

def run_selfcheck(directory, timeout=SELFCHECK_TIMEOUT):
    """在目录里跑 selfcheck.py → (状态, 标准输出, 备注)。"""
    script = Path(directory) / 'selfcheck.py'
    if not script.is_file():
        return 'missing', '', '还没建这个文件：selfcheck.py'
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    try:
        done = subprocess.run(
            [sys.executable, str(script)], cwd=str(directory), env=env, timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return 'timeout', '', 'selfcheck.py 跑了 ' + str(timeout) + ' 秒还没结束'
    if done.returncode not in (0, 1):        # 自测脚本自己「发现不过」时退 1 是正常的
        tail = (done.stderr or '').strip().splitlines()[-3:]
        return 'crash', done.stdout or '', ('selfcheck.py 报错退出（退出码 '
                                            + str(done.returncode) + '）：\n' + '\n'.join(tail))
    return 'ok', done.stdout or '', ''


def read_selfcheck_lines(out):
    """从自测脚本的输出里取 {标签: PASS/FAIL}。"""
    seen = {}
    for line in (out or '').splitlines():
        match = SELFCHECK_LINE_RE.match(line.strip())
        if match:
            seen[match.group(1)] = match.group(2)
    return seen


def probe_selfcheck():
    """把目录复制一份、把 solve_a.py 换成故意写错的解，看自测脚本会不会报 FAIL。

    交回 (状态, 自测脚本输出, 备注)：状态 ok / missing / crash / timeout。
    """
    wrong = HERE / 'probe_wrong_a.py'
    if not wrong.is_file():
        return 'missing', '', '判分用的 probe_wrong_a.py 不在了（那是给好的文件，别删别改）'
    tmp_root = tempfile.mkdtemp(prefix='lab0007-probe-')
    target = Path(tmp_root) / 'task'
    try:
        shutil.copytree(str(HERE), str(target),
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copyfile(str(wrong), str(target / 'solve_a.py'))
        status, out, note = run_selfcheck(target)
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    return status, out, note


def layer4(report):
    check_interface(report, 'selfcheck.py')
    status, out, note = run_selfcheck(HERE)
    if status == 'missing':
        report.check(False, note + '——' + MISSING_HINT)
        return
    if status == 'timeout':
        report.check(False, note)
        return
    if status == 'crash':
        report.check(False, note)
        return

    seen = read_selfcheck_lines(out)
    labels = ['A1', 'A2', 'B1', 'B2']
    gone = [label for label in labels if label not in seen]
    if gone:
        report.check(False, '自测脚本没有按格式报出这几组：' + '、'.join(gone) + '\n'
                      + '每一组要打印一行「样例 <标签> PASS」或「样例 <标签> FAIL」；\n'
                      + '它现在打印的是：' + brief(normalize(out)))
    else:
        failed = [label for label in labels if seen[label] == 'FAIL']
        if failed:
            report.check(False, '这四组在自测脚本里报的是 FAIL：' + '、'.join(failed) + '\n'
                          + 'solve 已经过了第 1 层，所以问题在自测脚本本身：它要按自己所在的'
                          + '目录\n（__file__）跑 solve_a.py / solve_b.py，把标准输出与 .out 逐字比。')
        else:
            report.check(True, '四组样例在自测脚本里都是 PASS')

    summary = [line for line in normalize(out) if line.startswith('自测通过')]
    if summary and '4/4' in summary[-1]:
        report.check(True, '汇总行在：' + summary[-1])
    else:
        report.check(False, '最后一行要打印「自测通过 4/4 组」这类的汇总（现在没有这一行，'
                      + '或者数字不对）')

    status, probe_out, probe_note = probe_selfcheck()
    if status == 'missing':
        report.check(False, probe_note)
        return
    if status in ('crash', 'timeout'):
        report.check(False, '探针没跑成：' + probe_note)
        return
    probed = read_selfcheck_lines(probe_out)
    a_ok = [label for label in ('A1', 'A2') if probed.get(label) == 'FAIL']
    b_bad = [label for label in ('B1', 'B2') if probed.get(label) != 'PASS']
    if len(a_ok) == 2 and not b_bad:
        report.check(True, '探针：把 solve_a.py 换成故意写错的解之后，A1/A2 报 FAIL、'
                      'B1/B2 仍 PASS——你的自测脚本真的在比对')
        return
    if len(a_ok) < 2:
        report.check(False, '探针：把 solve_a.py 换成故意写错的解之后，你的自测脚本'
                      + ('仍然报 PASS' if probed.get('A1') == 'PASS' or probed.get('A2') == 'PASS'
                         else '没有报出这两组') + '\n'
                      + '这样的自测脚本给不了任何保证。它必须真的去跑 solve 脚本、\n'
                      + '拿标准输出与 .out 文件逐字比；判分会在一个**副本目录**里试它，\n'
                      + '所以路径要按脚本自己所在的目录（__file__）算。')
        return
    report.check(False, '探针：B 的两组在你这里也报 FAIL（' + '、'.join(b_bad) + '）\n'
                  + 'B 的数据没有换过，正常应当 PASS —— 比对的期望文件可能接错了一组。')


# ══════════════════════════════════════════════════════════════════
# 第 5 层：规模对照
# ══════════════════════════════════════════════════════════════════

def layer5(report):
    check_interface(report, 'scale_check.py')
    status, out, note = run_plain('scale_check.py', 120.0)
    if status == 'missing':
        report.check(False, note + '——' + MISSING_HINT)
        return
    if status == 'timeout':
        report.check(False, note)
        return
    if status == 'crash':
        report.check(False, 'scale_check.py 报错退出：\n' + note)
        return

    lines = normalize(out)
    list_line = set_line = pred_line = None
    for line in lines:
        if LIST_RE.match(line):
            list_line = LIST_RE.match(line)
        elif SET_RE.match(line):
            set_line = SET_RE.match(line)
        elif PRED_RE.match(line):
            pred_line = PRED_RE.match(line)
    if list_line is None or set_line is None or pred_line is None:
        report.check(False, '三行输出没打全（判分按行读它们）：\n'
                      + 'n=20000 列表 in 用时 X 秒 不同元素 K\n'
                      + 'n=20000 集合 in 用时 X 秒 不同元素 K\n'
                      + '列表版放大 10 倍预计 X.XX 秒 超出 1 秒时限 True\n'
                      + '现在打出的是：' + brief(lines))
        return

    t_list, k_list = float(list_line.group(2)), int(list_line.group(3))
    t_set, k_set = float(set_line.group(2)), int(set_line.group(3))
    predicted = float(pred_line.group(1))
    over = pred_line.group(2) == 'True'

    if k_list == k_set and k_list > 0:
        report.check(True, '两种写法数出来的「不同元素」一致：' + str(k_list))
    else:
        report.check(False, '两种写法数出来的结果不一样（列表 ' + str(k_list) + '、集合 '
                      + str(k_set) + '）：先让两个函数在同一份数据上给出同一个答案')
        return

    if t_list >= 0.3:
        report.check(True, '列表 in 量到了：' + str(t_list) + ' 秒（20000 个数）')
    else:
        report.check(False, '列表 in 只用了 ' + str(t_list) + ' 秒，量级不对\n'
                      + '它每次查都要从头比过去，20000 个数上应当是零点几秒——'
                      + 'distinct_by_list 的 TODO 填了吗？')
    if t_set <= 0.05:
        report.check(True, '集合 in 量到了：' + str(t_set) + ' 秒')
    else:
        report.check(False, '集合 in 用了 ' + str(t_set) + ' 秒，不该这么慢——'
                      + '集合里是不是又用了列表那一套？')
    if t_set > 0 and t_list / t_set >= 20:
        report.check(True, '列表比集合慢 ' + str(round(t_list / t_set)) + ' 倍（≥ 20 倍）：'
                      + '同一件事换容器，代价差两个数量级')
    else:
        report.check(False, '列表与集合的差距只有 ' + str(round(t_list / max(t_set, 1e-9)))
                      + ' 倍，没量出差距：两个函数是不是写成了同一种容器？')

    if over and predicted > 1.0:
        report.check(True, '放大 10 倍预计 ' + str(predicted) + ' 秒，超出 1 秒时限 True')
    else:
        report.check(False, '「放大 10 倍预计 ' + str(predicted) + ' 秒 超出 1 秒时限 '
                      + pred_line.group(2) + '」不对\n'
                      + 'n 从 2 万到 20 万是 10 倍规模；列表查重的比较次数按规模**平方**涨，\n'
                      + '所以耗时要涨约 100 倍（不是 10 倍）——那一行正是要你推这个数。')
    if predicted >= t_list * 20:
        report.check(True, '预计值（' + str(predicted) + ' 秒）与「平方级」相符（≥ 实测×20）')
    else:
        report.check(False, '预计值 ' + str(predicted) + ' 秒偏小：它至少要接近实测的 100 倍\n'
                      + '（实测 ' + str(t_list) + ' 秒 → 放大 10 倍规模约 '
                      + str(round(t_list * 100, 1)) + ' 秒）。')


# ══════════════════════════════════════════════════════════════════
# 入口
# ══════════════════════════════════════════════════════════════════

def skip(title, reason):
    print(title)
    print('  ----  ' + reason)
    print()


def main():
    print('StudyMate lab 0007 · 自动判分（实验一：把一道题跑通）')
    print('目录：' + str(HERE))
    print()

    report1, report2 = layer12()
    front_ok = report1.passed() and report2.passed()

    report3 = Report('第 3 层 · 大数据（题目 A 十万个数；限时 ' + str(BIG_TIMEOUT) + ' 秒）')
    if front_ok:
        for label, in_name, out_name, script in LAYER3:
            check_big(report3, label, in_name, out_name, script)
        report3.show()
    else:
        skip(report3.title, '跳过：先把第 1、2 层过了再看大数据')

    report4 = Report('第 4 层 · 你自己的自测脚本（selfcheck.py）')
    if front_ok:
        layer4(report4)
        report4.show()
    else:
        skip(report4.title, '跳过：先把第 1、2 层过了')

    report5 = Report('第 5 层 · 规模对照（scale_check.py）')
    if front_ok:
        layer5(report5)
        report5.show()
    else:
        skip(report5.title, '跳过：先把第 1、2 层过了')

    reports = [
        ('第 1 层 · 样例', report1),
        ('第 2 层 · 换行被打乱的小数据', report2),
        ('第 3 层 · 大数据', report3),
        ('第 4 层 · 自测脚本', report4),
        ('第 5 层 · 规模对照', report5),
    ]
    print('─' * 60)
    done = [name for name, rep in reports if rep.passed()]
    undone = [name for name, rep in reports if not rep.passed() and rep.lines]
    skipped = [name for name, rep in reports if not rep.lines]
    print('五层：' + str(len(done)) + ' 层通过，' + str(len(undone)) + ' 层还没过'
          + ('，' + str(len(skipped)) + ' 层跳过' if skipped else ''))
    if undone:
        print('没过的：' + '、'.join(undone))
        if not front_ok:
            print('先把第 1、2 层过了（样例与分段检查）：这两层没过时，后面几层的结果没有参考价值'
                  '——这就是「别写完直接扔进大测试」。')
        print('卡住了先读 ../README.md 的「卡壳顺序」：读错误信息 → 自己跑一遍 → 看 FAIL 行 → 再对线索。')
        return 1
    if skipped:
        print('跳过的：' + '、'.join(skipped))
        return 1
    print('五层都过了。现在去对照 ../solutions/0007-lab-01-run-one-problem/：')
    print('比一比你的写法与参考解，再回答一句「哪一行决定了题目 A 能不能跑完 10 万个数」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
