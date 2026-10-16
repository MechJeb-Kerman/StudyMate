#!/usr/bin/env python3
"""lab 0011 · 自动判分：跑五个任务脚本，比对固定格式行，另起探针 import 学生代码。

用法（在 lab/0011-two-pointers-applications/ 目录里）：

    py run_tests.py

判法：
  - 每个任务单独起一个进程跑，只看 stdout 里的固定格式行，不 import 学生代码；
  - 计数行（`计数 NN 标签 值`）是判分接口，按两位编号取，编号与前缀都对得上才算；
  - **对撞指针靠对拍验**：任务 1 的对撞版在课件那三组、四组边界、四组规模上都与两层
    循环的基准一致；任务 2 的 while 版在五组数据上与基准一致，而 if 版**必须**漏解；
  - **原地改写靠探针验**：任务 3 的原地去重交回的是「个数」，内容在数组里，
    所以另起一个进程拿判分自己的数据试 (k, a[:k]) 两段；任务 5 的三个函数同样各试一组；
  - **「两数之和」只判交回的对合不合法，不写死是哪一对**：`[0, 0, 0]` 目标和 0 时
    (0, 1)、(0, 2)、(1, 2) 都对，对撞版给 (0, 2)、两层循环给 (0, 1)，两个都算对；
  - **耗时行一条都不判**：脚本会打印 `耗时 NN … 秒` 与 `倍数 NN …`，那是给学生自己看的。
    耗时随机器浮动，拿它当判据会让同一份代码时过时不过，所以整套判分只用确定值；
  - 任务 2 另有一条：if 版**必须漏解**——五组数据里只有 `[1, 4, 5, 9, 11] / 10`
    那一组它交回 None，共 1 组（其余四组第一次比较就命中，或者和一直偏小、r 不用动）。

退出码：0 = 五个任务都通过；1 = 还有没通过的。
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMEOUT = 180
SCALE_TIMEOUT = 300

TASKS = [
    ('任务 1 · 有序数组的两数之和（对撞指针）', 'task1_two_sum_sorted.py', None),
    ('任务 2 · 该收一格还是收到位（if 与 while）', 'task2_if_vs_while.py', None),
    ('任务 3 · 原地去重（快慢指针）', 'task3_dedup_inplace.py', None),
    ('任务 4 · 回文判定（两头向中间）', 'task4_palindrome.py', None),
    ('任务 5 · 合并两个有序数组（新列表版与原地版）', 'task5_merge_sorted.py', None),
]


# ── 跑脚本 ────────────────────────────────────────────────────────────────

def _env():
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    return env


def run_script(name, timeout=TIMEOUT):
    """跑一个任务脚本 → dict(status, out, note)。状态：ok / missing / crash / timeout。"""
    path = HERE / name
    if not path.is_file():
        return {'status': 'missing', 'out': '', 'note': '还没建这个文件：' + name}
    try:
        done = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(HERE), env=_env(), timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'out': '',
                'note': '跑了 ' + str(timeout) + ' 秒还没结束（死循环？）'}
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-5:])
        return {'status': 'crash', 'out': done.stdout or '',
                'note': ('脚本报错退出（退出码 ' + str(done.returncode) + '）：\n' + tail)}
    return {'status': 'ok', 'out': done.stdout or '', 'note': ''}


def run_probe(filename, timeout=TIMEOUT):
    """另起一个进程跑 probes/<filename>（它 import 学生代码）→ (out, note)。"""
    path = HERE / 'probes' / filename
    if not path.is_file():
        return None, '没找到探针文件 probes/' + filename
    try:
        done = subprocess.run(
            [sys.executable, '-B', str(path)],
            cwd=str(HERE), env=_env(), timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return None, '探针跑了 ' + str(timeout) + ' 秒还没结束'
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-6:])
        return None, '探针报错退出：\n' + tail
    return done.stdout or '', ''


def probe_json(filename):
    """跑探针并解析它最后一行 PROBE 后面的 JSON → (数据, 错误说明)。"""
    out, note = run_probe(filename)
    if out is None:
        return None, note
    line = None
    for text in out.splitlines():
        if text.startswith('PROBE '):
            line = text[len('PROBE '):]
    if line is None:
        return None, '探针没打出 PROBE 那一行'
    try:
        return json.loads(line), ''
    except Exception as exc:
        return None, '探针结果读不出来：' + str(exc)


# ── 读输出 ────────────────────────────────────────────────────────────────

def get_line(out, prefix):
    """按前缀取一整行剩下的内容；没打到那一行就返回 None。"""
    for line in out.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def get_seg_line(out, prefix):
    """同上，但要求前缀之后紧跟一个空格——也就是前缀是**整段**，不是别段的前几个字。

    `get_line` 用前缀匹配，`第一处错位 abca` 会先撞上 `第一处错位 abcabc (0, 5)`，
    于是「abca 的错位」读到的是 abcabc 那一行。凡是前缀可能互为前缀的地方都用这个。
    """
    for line in out.splitlines():
        if line == prefix:
            return ''
        if line.startswith(prefix + ' '):
            return line[len(prefix):].strip()
    return None


def as_pair(value):
    """把 [i, j] / None 翻成元组，方便与 print 出来的 '(0, 3)' 对照。"""
    if value is None:
        return None
    if isinstance(value, list) and len(value) == 2:
        return (value[0], value[1])
    return value


def parse_printed_pair(text):
    """把脚本 print 出来的 '(0, 3)' / 'None' 翻成 (0, 3) / None。"""
    text = ('' if text is None else str(text)).strip()
    if text == 'None':
        return None
    match = re.fullmatch(r'\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)', text)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return text          # 认不出来就原样交回，由 valid_sum_pair 判 False


def valid_sum_pair(got, a, target):
    """判 got 是不是「有序数组两数之和」这组数据的**合法答案**。

    合法有两条路：有解时交回一对满足 i < j 且 a[i] + a[j] == target 的下标；
    无解时交回 None。**不指定必须是哪一对**——[0, 0, 0] 目标和 0 时
    (0, 1)、(0, 2)、(1, 2) 都对，对撞版给 (0, 2)、两层循环给 (0, 1)，
    两个都是对的，写死其中一个会让正确的解被判错。

    got 既可能是探针交回的 [i, j]，也可能是脚本打印的 '(i, j)' 字符串，两种都收。
    """
    if isinstance(got, str):
        got = parse_printed_pair(got)
    pair = as_pair(got)
    has_answer = any(a[i] + a[j] == target
                     for i in range(len(a)) for j in range(i + 1, len(a)))
    if pair is None:
        return not has_answer
    if not (isinstance(pair, tuple) and len(pair) == 2):
        return False
    i, j = pair
    if isinstance(i, bool) or isinstance(j, bool):
        return False
    if not (isinstance(i, int) and isinstance(j, int)):
        return False
    if not (0 <= i < j < len(a)):
        return False
    return a[i] + a[j] == target


def get_lines(out, prefix):
    return [line[len(prefix):].strip() for line in out.splitlines() if line.startswith(prefix)]


def count_value(out, index):
    """取 `计数 NN 标签 值` 里的值（只按编号找）。"""
    for entry in get_lines(out, '计数 ' + index + ' '):
        parts = entry.split()
        if len(parts) >= 2:
            return parts[-1]
    return None


def short(text, limit=60):
    text = '' if text is None else str(text)
    return text if len(text) <= limit else text[:limit] + '…'


# ══ 任务 1 · 两数之和（对撞指针）══════════════════════════════════════════

PROBE1_WANT = {
    '[] / 5': [None, None],
    '[7] / 14': [None, None],
    '[3, 3] / 6': [[0, 1], [0, 1]],
    '[-5, -1, 0, 2] / -6': [[0, 1], [0, 1]],
    '[1, 4, 5, 9, 11] / 10': [[0, 3], [0, 3]],
    '[1, 4, 5, 9, 11] / 100': [None, None],
    '[0, 0, 0] / 0': [[0, 2], [0, 2]],
    '[2, 7, 11, 15] / 9': [[0, 1], [0, 1]],
    '[1, 2, 3, 4, 5, 6] / 11': [[4, 5], [4, 5]],
    '[1, 1, 1, 1] / 2': [[0, 3], [0, 3]],
}


def check_task1():
    run = run_script('task1_two_sum_sorted.py')
    if run['status'] != 'ok':
        return [(False, 'task1_two_sum_sorted.py 没跑通：' + run['note'])]
    checks = []

    want = [
        ('课件数据 目标 10', '(0, 3)', '课件那一组、目标 10 上是 (0, 3)：1 + 9'),
        ('课件数据 目标 20', '(2, 5)', '同一组、目标 20 上是 (2, 5)：5 + 15'),
        ('课件数据 目标 100', 'None', '目标 100 上没有这样的一对，交回 None'),
        ('课件数据 暴力对照', '[(0, 3), (2, 5), None]', '两层循环的基准版在同一组上给出同一批答案'),
    ]
    for prefix, expect, good in want:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 2 的 while l < r 里每轮只动一个下标，'
                             '和偏小 l += 1、和偏大 r -= 1'))

    for prefix, good, hint in [
        ('课件数据 三组一致', '对撞版与基准版在课件的三组上完全一致',
         '三组都要与两层循环的基准一致'),
        ('边界四组 对撞与暴力一致', '四组边界（空表、单元素、两个相同的数、负数）上都与基准一致',
         '空表与单元素都应当交回 None；[3, 3]、目标 6 应当是 (0, 1)'),
        ('四组规模 对撞与暴力全一致', '四组规模（20 / 200 / 2000 / 8000）上都与基准一致',
         '规模大起来之后答案都在右上角，对撞版要从两端收到那里'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == 'True':
            if prefix == '四组规模 对撞与暴力全一致' and get_line(run['out'], '课件数据 三组一致') != 'True':
                checks.append((False, prefix + ' 是 True，但课件那三组还没对上：先写 TODO 2'))
            else:
                checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 True：' + hint))

    # 逐档的答案行与轮数
    lines = get_lines(run['out'], '规模 ')
    ok_rows = 0
    for entry in lines:
        parts = entry.split()
        # 打出来是「规模  20 对撞 (18, 19) 暴力 (18, 19) 一致 True」，
        # 去掉前缀之后是 9 段（下标里的空格也会切开），所以按记号认，不数段数。
        if (parts and parts[0].isdigit() and '对撞' in parts and '暴力' in parts
                and len(parts) >= 2 and parts[-2] == '一致' and parts[-1] == 'True'):
            ok_rows += 1
    if lines and ok_rows == len(lines):
        checks.append((True, str(ok_rows) + ' 档规模的答案与基准逐档一致（答案都在右上角）'))
    elif not lines:
        checks.append((False, '没看到「规模 …」这几行'))
    else:
        checks.append((False, str(len(lines)) + ' 档里有 ' + str(len(lines) - ok_rows)
                       + ' 档两版不一致：先看对撞版把哪一格丢了'))

    rounds = get_line(run['out'], '每档的轮数')
    rounds_ok = get_line(run['out'], '轮数与 n-1 相同')
    if rounds == '[19, 199, 1999, 7999]' and rounds_ok == 'True':
        checks.append((True, '四档的轮数是 n - 1：每轮至少有一个指针移动一格，合计最多走 n - 1 格'))
    elif rounds is None:
        checks.append((False, '没看到「每档的轮数 …」这一行'))
    else:
        checks.append((False, '每档的轮数 打出 ' + short(rounds) + '，期望 [19, 199, 1999, 7999]：'
                       'TODO 3 那四个 0 还没换；目标值取最后两项之和时两个指针要收到右上角，'
                       '正好 n - 1 轮'))

    for index, expect, label in [('01', 'True', '课件三组一致'), ('02', 'True', '边界四组一致'),
                                 ('03', 'True', '四组规模一致'), ('04', 'True', '轮数正确')]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))

    checks += probe_task1_checks()
    return checks


def probe_task1_checks():
    data, note = probe_json('probe_task1.py')
    if data is None:
        return [(False, '任务 1 的探针跑不起来：' + note)]
    cases, scales = data
    checks = []
    bad = []
    for label, got_sorted, got_brute in cases:
        if label not in PROBE1_WANT:
            continue
        arr_str, target_str = label.rsplit(' / ', 1)
        arr = ast.literal_eval(arr_str)
        target = int(target_str)
        for who, got in (('对撞', got_sorted), ('基准', got_brute)):
            if not valid_sum_pair(got, arr, target):
                bad.append(label + '：' + who + ' 交出 ' + short(got)
                           + '，它不是这组数据的合法答案')
    if not bad:
        checks.append((True, '判分小数据十组：对撞版与基准版交回的都是合法答案'
                             '（含空表、单元素、[3, 3]、负数、[0, 0, 0] 这种多解、无解那一组）'))
    else:
        checks.append((False, '判分小数据有 ' + str(len(bad)) + ' 组不对：' + short('；'.join(bad))))

    bad_scale = []
    for n, got_sorted, got_brute in scales:
        if as_pair(got_sorted) != as_pair(got_brute):
            bad_scale.append('n=' + str(n) + '：对撞 ' + short(got_sorted)
                             + '、基准 ' + short(got_brute))
        elif as_pair(got_sorted) != (n - 2, n - 1):
            bad_scale.append('n=' + str(n) + '：交回 ' + short(got_sorted)
                             + '，期望 ' + short((n - 2, n - 1)))
    if not bad_scale:
        checks.append((True, '判分三档规模上对撞版都交出 (n-2, n-1) 并与基准一致'))
    else:
        checks.append((False, '判分三档规模上有问题：' + short('；'.join(bad_scale))
                       + '：目标值取最后两项之和，答案就是最后两个下标'))
    return checks


# ══ 任务 2 · if 与 while ══════════════════════════════════════════════════

def check_task2():
    run = run_script('task2_if_vs_while.py')
    if run['status'] != 'ok':
        return [(False, 'task2_if_vs_while.py 没跑通：' + run['note'])]
    checks = []

    for prefix, expect, good in [
        ('课件数据 if 版', 'None', 'if 版在课件那一组上漏掉了 1 + 9，交回 None'),
        ('课件数据 while 版', '(0, 3)', 'while 版在课件那一组上交出 (0, 3)：1 + 9'),
        ('课件数据 两版不同', 'True', '两版在同一组数据上给出不同结果——这就是这一课要看的东西'),
        ('if 版第 1 轮之后 r 已经收到', '3', 'if 版第 1 轮就把 r 收到 3，而 (0, 3) 要等到第 2 轮才该被比'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 1 是**故意漏解**的那一版（右指针每轮只收一格），'
                             'TODO 2 才是对的（一直收到不再偏大）；两版的差别就是一处 if/while'))

    rows = {}
    for line in run['out'].splitlines():
        if not line.startswith('数据 '):
            continue
        parts = line[len('数据 '):].split()
        # 行格式：数据 <数组> <目标值> if <结果> while <结果> while对 <True>
        # 数组与结果里都含空格（`[1, 4, 5]`、`(0, 3)`），所以按 'if' / 'while' /
        # 'while对' 这三个记号切开：记号左边的最后一段是目标值，记号之间的是结果。
        # **别要求记号之间恰好差 2 段**——结果是 `(0, 3)` 时占两段，不是一段。
        if 'if' not in parts or 'while' not in parts or 'while对' not in parts:
            continue
        i_if = parts.index('if')
        i_while = parts.index('while')
        i_ok = parts.index('while对')
        if not (0 < i_if < i_while < i_ok):
            continue
        key = (' '.join(parts[:i_if - 1]), parts[i_if - 1])
        rows[key] = [' '.join(parts[i_if + 1:i_while]),
                     ' '.join(parts[i_while + 1:i_ok]),
                     parts[i_ok + 1]]
    # 每组只要 while 版交出「合法答案」就算对，不写死是哪一对。
    want_rows = ['[1, 4, 5, 9, 11] / 10', '[2, 3, 4] / 6', '[1, 2, 3, 4, 5] / 9',
                 '[1, 1, 2] / 3', '[5, 6, 7, 8] / 13']
    bad = []
    for label in want_rows:
        arr_str, target_str = label.rsplit(' / ', 1)
        arr = ast.literal_eval(arr_str)
        target = int(target_str)
        got = rows.get((arr_str, target_str))
        if got is None:
            bad.append(label + '（这一行没打出来）')
            continue
        if got[2] != 'True':
            bad.append(label + ' 的 while 版没与基准一致')
            continue
        if not valid_sum_pair(got[1], arr, target):
            bad.append(label + ' 的 while 版交回 ' + got[1] + '，它不合法')
    if not bad:
        checks.append((True, '五组数据里 while 版都与基准一致（含 [2, 3, 4]/6、(3, 4) 这类要看两轮的）'))
    else:
        checks.append((False, '五组数据里有问题：' + short('；'.join(bad))
                       + '：TODO 2 的内层要写 while l < r and a[l] + a[r] > target:'))

    for prefix, expect, label, hint in [
        ('if 版漏解组数', '1', 'if 版漏解组数',
         '五组里只有 [1, 4, 5, 9, 11] / 10 这一组 if 版交回 None 而 while 版找到了答案——'
         '其余四组第一次比较就命中，或者和一直偏小、r 根本不用动。'
         '打出 0 说明 if 版被写成 while 版了，打出 5 说明它整组都没找到'),
        ('while 版与暴力一致组数', '5', 'while 版一致组数',
         '五组都要对上；有一组不对就是 TODO 2 的边界（l < r）或弹出条件写偏了'),
        ('if 版把 (0, 3) 那一对跳过了', 'True', 'if 版跳过 (0, 3)', '这一行是给好的对照'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, label + ' ' + expect))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect + '：' + hint))

    for index, expect, label in [('01', 'True', '两版不同'), ('02', '1', 'if 版漏解组数'),
                                 ('03', '5', 'while 版一致组数')]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))
    return checks


# ══ 任务 3 · 原地去重 ═════════════════════════════════════════════════════

def check_task3():
    run = run_script('task3_dedup_inplace.py')
    if run['status'] != 'ok':
        return [(False, 'task3_dedup_inplace.py 没跑通：' + run['note'])]
    checks = []

    for prefix, expect, good in [
        ('课件数据 个数', '4', '课件那一组 [1, 1, 2, 3, 3, 5] 交回 4'),
        ('课件数据 前 k 项', '[1, 2, 3, 5]', '前 k 项是 [1, 2, 3, 5]——去重后的内容也对'),
        ('课件数据 整个数组', '[1, 2, 3, 5, 3, 5]', '整个数组是 [1, 2, 3, 5, 3, 5]：只有前 k 项有效'),
        ('错版 个数', '1', '漏掉 slow += 1 的错版交回 1（它声称只剩一个元素）'),
        ('错版 整个数组', '[5, 1, 2, 3, 3, 5]', '错版把数组写花成 [5, 1, 2, 3, 3, 5]——两个错互相解释'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 1 是正确版（先 slow += 1 再写），TODO 2 是故意删掉那一行的错版；'
                             '两版别写成一模一样'))

    for prefix, expect, label, hint in [
        ('空数组交回 0', 'True', '空数组交回 0', 'len(a) == 0 时直接交回 0，不然 a[0] 会报错'),
        ('单个元素交回 1', 'True', '单个元素交回 1', '只有一个元素时去重后就是它自己，个数 1'),
        ('全部相同交回 1', 'True', '全部相同交回 1', '[4, 4, 4, 4] 去重后是 [4]，个数 1'),
        ('三组数据全部正确', 'True', '三组数据全部正确',
         '三组都要「个数对 + 前 k 项对」；只对个数不对内容是最常见的半对'),
        ('20000 个数 去重后个数', None, '20000 个数去重后个数', ''),
    ]:
        if prefix == '20000 个数 去重后个数':
            continue
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, label + '：' + hint if hint else label))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect + '：' + hint))

    big = get_line(run['out'], '20000 个数 去重后个数')
    if big is None:
        checks.append((False, '没看到「20000 个数 去重后个数 …」这一行'))
    else:
        parts = big.split()
        # 打出来是「20000 个数 去重后个数 6667 参照个数 6667」，
        # 去掉前缀之后是 3 段：<个数> 参照个数 <参照个数>。
        if len(parts) == 3 and parts[0] == parts[2] and parts[0].isdigit() and int(parts[0]) > 1000:
            checks.append((True, '20000 个数去重后剩 ' + parts[0]
                                 + ' 个，与参照个数一致（不是 1，也不是 20000）'))
        else:
            checks.append((False, '20000 个数 去重后个数 打出 ' + short(big)
                           + '，期望「去重后个数 = 参照个数」且大于 1000：'
                             '打出 1 是漏了 slow += 1；打出 20000 是根本没去重'))

    pairs = get_line(run['out'], '20000 个数 前后两项')
    if pairs == '[5, 8] [20096, 20101]':
        checks.append((True, '20000 个数去重后的前两项是 [5, 8]、有效部分的最后两项是 [20096, 20101]'))
    elif pairs is None:
        checks.append((False, '没看到「20000 个数 前后两项 …」这一行'))
    else:
        checks.append((False, '20000 个数 前后两项 打出 ' + short(pairs)
                       + '，期望 [5, 8] [20096, 20101]：'
                         '原地去重之后前 k 项应当就是那份数据去重后的全部值（先小后大）；'
                         '对不上说明写入位置写错了'))

    for index, expect, label in [('01', '4', '课件数据个数'), ('02', 'True', '课件数据前 k 项'),
                                 ('03', '1', '错版个数'), ('04', '3', '三组数据正确个数'),
                                 ('05', 'True', '20000 个数个数一致')]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))

    checks += probe_task3_checks()
    return checks


def probe_task3_checks():
    data, note = probe_json('probe_task3.py')
    if data is None:
        return [(False, '任务 3 的探针跑不起来：' + note)]
    checks = []
    bad_count = []
    bad_body = []
    for entry in data:
        if not isinstance(entry, list) or len(entry) != 4:
            continue
        label, k, body, want = entry
        if want == 'expect-1-and-written-over':
            if k == 1 and body == [5, 1, 2, 3, 3, 5]:
                checks.append((True, '探针：错版交回 1 且把数组写成 [5, 1, 2, 3, 3, 5]'))
            else:
                checks.append((False, '探针：错版交出 (' + short(k) + ', ' + short(body) + ')，'
                               + '期望 (1, [5, 1, 2, 3, 3, 5])：'
                                 'TODO 2 要整段照抄正确版、只删掉 slow += 1 那一行'))
            continue
        if k != len(want):
            bad_count.append(label + '：个数 ' + short(k) + '，期望 ' + str(len(want)))
        elif body != want:
            bad_body.append(label + '：前 k 项 ' + short(body) + '，期望 ' + short(want))
    if not bad_count and not bad_body:
        checks.append((True, '探针：判分自己的六组数据（含空数组、全部相同、负数）上，'
                             '个数与前 k 项都对'))
    if bad_count:
        checks.append((False, '探针：有 ' + str(len(bad_count)) + ' 组个数不对：' + short('；'.join(bad_count))))
    if bad_body:
        checks.append((False, '探针：有 ' + str(len(bad_body)) + ' 组内容不对：' + short('；'.join(bad_body))
                       + '：原地改写的函数必须把「哪一段有效」交代清楚，前 k 项就是答案'))
    return checks


# ══ 任务 4 · 回文判定 ═════════════════════════════════════════════════════

PAL_WANT = [
    ('上海自来水来自海上', True, -1),
    ('abccba', True, -1),
    ('abcabc', False, (0, 5)),
    ([1, 2, 3, 2, 1], True, -1),
    ([1, 2, 2, 1], True, -1),
    ([], True, -1),
    ([9], True, -1),
    ('a', True, -1),
    ('ab', False, (0, 1)),
    ([1, 2], False, (0, 1)),
]


def check_task4():
    run = run_script('task4_palindrome.py')
    if run['status'] != 'ok':
        return [(False, 'task4_palindrome.py 没跑通：' + run['note'])]
    checks = []

    rows = {}
    for line in run['out'].splitlines():
        if not line.startswith('用例 '):
            continue
        parts = line[len('用例 '):].split()
        # 行格式：用例 <用 repr 打出来的对象> <is_palindrome> <first_mismatch>
        # **从右边数**着切：列表的 repr 里含空格（`[1, 2, 3, 2, 1]`），
        # 而且 first_mismatch 本身也含空格——回文时是 `-1`（一段），
        # 不是时是 `(0, 5)`（两段）。数总段数会把这两种情况都切错。
        # 字符串的 repr 带引号，查表那边也去掉引号，两边对齐。
        if len(parts) < 3:
            continue
        if parts[-1] == '-1':
            head, pal, mis = parts[:-2], parts[-2], parts[-1]
        elif len(parts) >= 4:
            head, pal, mis = parts[:-3], parts[-3], ' '.join(parts[-2:])
        else:
            continue
        rows[' '.join(head).strip("'\"")] = (pal, mis)
    if not rows:
        return [(False, '没看到「用例 …」这几行：带 print 的行别改、别删')]

    bad = []
    for text, want_pal, want_mis in PAL_WANT:
        label = repr(text)
        got = rows.get(repr(text).strip("'\""))
        if got is None:
            bad.append(label + '（这一行没打出来）')
            continue
        if got[0] != str(want_pal):
            bad.append(label + ' 的判定是 ' + got[0] + '，期望 ' + str(want_pal))
        if want_mis == -1 and got[1] != '-1':
            bad.append(label + ' 的错位是 ' + got[1] + '，期望 -1（它是回文）')
        elif want_mis != -1:
            want_text = '(' + str(want_mis[0]) + ', ' + str(want_mis[1]) + ')'
            if got[1] != want_text:
                bad.append(label + ' 的错位是 ' + got[1] + '，期望 ' + want_text)
    if not bad:
        checks.append((True, '十组用例（字符串与列表、含空序列与单元素）的判定与第一处错位全对'))
    else:
        checks.append((False, '十组用例里有 ' + str(len(bad)) + ' 处不对：' + short('；'.join(bad))
                       + '：TODO 1 相等时两个指针都要动（只动一个会原地打转），'
                         '不相等直接给结论；TODO 2 是同一趟走法、只把 False 换成那一对下标'))

    for prefix, expect, label in [
        ('十组用例的判定对上', '10', '十组判定对上'),
        ('两版判定完全一致', 'True', '两版判定完全一致'),
        ('第一处错位 abcabc', '(0, 5)', 'abcabc 的第一处错位是 (0, 5)'),
        ('第一处错位 [1, 2, 2, 3]', '(0, 3)', '[1, 2, 2, 3] 的第一处错位是 (0, 3)'),
        ('第一处错位 abca', '(1, 2)', 'abca 的第一处错位是 (1, 2)——不是 (0, 3)'),
    ]:
        # 前缀 `第一处错位 abca` 是 `第一处错位 abcabc` 的前缀，必须按整段认。
        value = get_seg_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, label))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect))

    for index, expect, label in [('01', '10', '判定对上组数'), ('02', 'True', '两版一致'),
                                 ('03', 'True', 'abcabc 错位'), ('04', 'True', '列表错位')]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))
    return checks


# ══ 任务 5 · 合并两个有序数组 ═════════════════════════════════════════════

def check_task5():
    run = run_script('task5_merge_sorted.py')
    if run['status'] != 'ok':
        return [(False, 'task5_merge_sorted.py 没跑通：' + run['note'])]
    checks = []

    for prefix, expect, good in [
        ('第一组 合并', '[1, 2, 3, 4, 5, 6, 7]', '课件第一组 [1, 3, 5, 7] 与 [2, 4, 6] 合并成 [1, 2, 3, 4, 5, 6, 7]'),
        ('第一组 原数组没动', '[1, 3, 5, 7] [2, 4, 6]', '新列表版没有改动两个输入数组'),
        ('第二组 合并', '[1, 2, 2, 2, 3, 9]', '课件第二组 [1, 2, 3] 与 [2, 2, 9] 合并成 [1, 2, 2, 2, 3, 9]'),
        ('原地 合并', '[1, 2, 4, 5, 6, 7]', '原地版从后往前写：[1, 4, 7] 与 [2, 5, 6] 合成 [1, 2, 4, 5, 6, 7]'),
        ('原地 b 更短', '[0, 1, 2, 3, 4]', 'b 比空位短时也能对：[1, 2, 3] 与 [0, 4] 合成 [0, 1, 2, 3, 4]'),
        ('原地 b 更长', '[1, 2, 3, 4, 5, 6, 7]', 'b 正好填满空位：[4, 5, 6] 与 [1, 2, 3, 7] 合成 [1, 2, 3, 4, 5, 6, 7]'),
        ('原地 有重复值', '[1, 2, 2, 3, 3]', '[2, 3] 与 [1, 2, 3] 合成 [1, 2, 2, 3, 3]'),
        ('前 3 项', '[1, 2, 3]', '只取前 3 项：[1, 2, 3]'),
        ('前 10 项', '[1, 2, 3, 4, 5, 8, 9, 11]', 'k 大于总长时把能给的都给出来'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 1 的收尾两个 while 都要写（漏一个会丢尾巴）；'
                             'TODO 2 从后往前写，条件是 q >= 0；'
                             'TODO 3 取满 k 项就交回'))

    value = get_line(run['out'], '六组与基准一致')
    if value == '6':
        checks.append((True, '六组数据（含空数组、一边为空、全是同一个值）都与现成的 sorted(x + y) 一致'))
    elif value is None:
        checks.append((False, '没看到「六组与基准一致 …」这一行'))
    else:
        checks.append((False, '六组与基准一致 打出 ' + short(value) + '，期望 6：'
                       '有哪一组不对，看上面「数据 … 与 sorted 一致 False」那一行'))

    for index, expect, label in [('01', '6', '六组与基准一致'), ('02', 'True', '原地第一组'),
                                 ('03', 'True', '原地 b 更长'), ('04', 'True', '前 3 项')]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))

    checks += probe_task5_checks()
    return checks


def probe_task5_checks():
    data, note = probe_json('probe_task5.py')
    if data is None:
        return [(False, '任务 5 的探针跑不起来：' + note)]
    checks = []
    merged, inplace, short_rows = data

    bad = []
    for label, got, want in merged:
        if got != want:
            bad.append(label + ' 交回 ' + short(got) + '，期望 ' + short(want))
    if not bad:
        checks.append((True, '探针：判分自己的六组数据上，新列表版都与 sorted(a + b) 一致'))
    else:
        checks.append((False, '探针：新列表版有 ' + str(len(bad)) + ' 组不对：' + short('；'.join(bad))))

    bad = []
    for label, got, want in inplace:
        if got != want:
            bad.append(label + ' 结果是 ' + short(got) + '，期望 ' + short(want))
    if not bad:
        checks.append((True, '探针：原地版的四组都比对得上（b 短、正好、末尾两格的情形都在里面）'))
    else:
        checks.append((False, '探针：原地版有 ' + str(len(bad)) + ' 组不对：' + short('；'.join(bad))
                       + '：从后往前写，p 从 m - 1 起、q 从 len(b) - 1 起、w 从末尾起'))

    bad = []
    for label, got, want in short_rows:
        if got != want:
            bad.append(label + ' 交回 ' + short(got) + '，期望 ' + short(want))
    if not bad:
        checks.append((True, '探针：前 k 项的四组都对（k 小于 / 大于总长、k = 0、一边为空）'))
    else:
        checks.append((False, '探针：前 k 项有 ' + str(len(bad)) + ' 组不对：' + short('；'.join(bad))
                       + '：取满 k 项就交回，k 大于总长时把能给的都给出来'))
    return checks


# ══ 主流程 ════════════════════════════════════════════════════════════════

CHECKERS = {
    'task1_two_sum_sorted.py': check_task1,
    'task2_if_vs_while.py': check_task2,
    'task3_dedup_inplace.py': check_task3,
    'task4_palindrome.py': check_task4,
    'task5_merge_sorted.py': check_task5,
}

# 每条 FAIL 都要能指回「去改哪个 TODO」。计数行与探针的汇总消息天然说不出这一点，
# 所以在打印那一刻统一补上——留白版跑完必须有「每条 FAIL 都点名 TODO」这条性质。
#
# 但「探针文件没找到」不是学生的 TODO 问题：那是 **probes/ 这个子目录没被一起拷过来**
# （只拷 *.py 就会这样）。那种 FAIL 上贴一句「改这个文件的 TODO 1 是…」会把人指错方向，
# 所以这两类消息一律不加提示。
NO_TODO_HINT = ('没找到探针文件', '探针跑不起来', '还没建这个文件')

TODO_HINT = {
    'task1_two_sum_sorted.py': 'TODO 1 是两层循环的基准版、TODO 2 是对撞版、'
                               'TODO 3 是把每档的轮数写出来（每轮至少有一个指针移动一格，'
                               '合计最多走 n - 1 格，所以正好 n - 1 轮）',
    'task2_if_vs_while.py': 'TODO 1 是**故意漏解**的 if 版（右指针每轮只收一格）、'
                            'TODO 2 才是对的 while 版（一直收到不再偏大）',
    'task3_dedup_inplace.py': 'TODO 1 是正确版去重（先 slow += 1 再写）、'
                              'TODO 2 是整段照抄正确版、只删掉 slow += 1 那一行的错版',
    'task4_palindrome.py': 'TODO 1 是判定回文（相等时两个指针都要动、只动一个会原地打转）、'
                           'TODO 2 是同一趟走法、只把 False 换成那一对下标',
    'task5_merge_sorted.py': 'TODO 1 是新列表版（收尾两个 while 都要写，漏一个会丢尾巴）、'
                             'TODO 2 是原地版从后往前写、TODO 3 是取满 k 项就交回',
}


def main():
    print('StudyMate lab 0011 · 自动判分（双指针：两个下标的配合）')
    print('目录：' + str(HERE))
    print()
    failed = []
    for title, filename, _ in TASKS:
        print(title + '（' + filename + '）')
        if not (HERE / filename).is_file():
            print('  FAIL  还没建这个文件：' + filename)
            print()
            failed.append(filename)
            continue
        checks = CHECKERS[filename]()
        all_ok = True
        for ok, message in checks:
            if (not ok and 'TODO' not in message
                    and not any(mark in message for mark in NO_TODO_HINT)):
                message = message + '（改这个文件的 ' + TODO_HINT[filename] + '）'
            print('  ' + ('PASS' if ok else 'FAIL') + '  ' + message)
            if not ok:
                all_ok = False
        if all_ok:
            print('  → 这个任务过了')
        else:
            failed.append(filename)
        print()

    print('─' * 60)
    print('5 个任务：' + str(5 - len(failed)) + ' 个通过，' + str(len(failed)) + ' 个还没通过')
    if failed:
        print('没过的：' + '、'.join(failed))
        print('卡住了先读 ../README.md 的「卡壳顺序」：读错误信息 → 自己跑一遍 → 看 FAIL 行 → 再对线索。')
        print('五个任务都过了，再对照 ../solutions/0011-two-pointers-applications/ 看参考解。')
        return 1
    print('五个任务都过了。现在去对照 ../solutions/0011-two-pointers-applications/：')
    print('比一比你的写法与参考解，再用一句话回答「这四道题里，每个指针各自保证什么」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
