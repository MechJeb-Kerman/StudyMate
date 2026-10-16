#!/usr/bin/env python3
r"""lab 0014 · 自动判分（二分：每次砍掉一半）

用法（在这个任务目录里直接跑）：

    py run_tests.py

判法：**五层**，一层里几条检查各自给 PASS / FAIL。每一层都靠**两路证据**：

    第一路  跑四个任务脚本，读它们自己打印的那些行（那些行是接口）。
    第二路  另起一个进程跑 probes/probe_taskN.py：它 import 学生的函数，
            拿**判分自己的**数据（种子 PROBE_SEED = 2718281，规模与脚本里那份
            刻意不同）复算一遍期望值。只写 print、不写实现拿不到 PASS。

五层各验什么：

    第 1 层 · 三个二分函数正确性（task1_bsearch.py）
        边界数据集上 bsearch_closed、lower_bound、contains 全都正确；
        随机有序数组上三个版本与 bisect 一致；
        探针再拿判分自己的数据（含空数组、单元素、边界、随机）复算一遍。

    第 2 层 · 边界测试表正确性（task2_boundary.py）
        边界数据表与判分自己算的一致；
        探针换用自己的数据再跑一遍。

    第 3 层 · 三种错法的检测（task3_debug.py）
        三种错法在正确的边界数据集上暴露出了正确的数据组；
        每句说明指向了正确的病灶行。

    第 4 层 · 轮数表与性能对比（task4_rounds.py）
        轮数表的数值与 ceil(log2(n+1)) 一致；
        二分查找比线性扫描快（不读具体秒数，只判大小关系）；
        探针再算一遍轮数。

    第 5 层 · 四个脚本能单独跑、源码本身干净
        逐个单跑（退出码 0、无 Traceback）；
        probes/ 与 tools.py 两侧必须逐字节相同。

退出码：五层都过是 0；还有没过的（或跳过的）是 1。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import tools as judge                                     # noqa: E402  给好的，别改
from tools import (                                       # noqa: E402
    bsearch_closed_canonical, lower_bound_canonical,
    contains_canonical, bound_seqs, max_rounds,
    max_rounds_simulated, make_random, make_sorted,
    bug_no_shrink, bug_lose_last, bug_no_check,
)

# 四个任务文件的名字
TASK_SCRIPTS = {
    'task1': 'task1_bsearch.py',
    'task2': 'task2_boundary.py',
    'task3': 'task3_debug.py',
    'task4': 'task4_rounds.py',
}

# 探针
PROBES = {
    'task1': 'probes/probe_task1.py',
    'task2': 'probes/probe_task2.py',
    'task3': 'probes/probe_task3.py',
    'task4': 'probes/probe_task4.py',
}
PROBE_SENTINEL = {'task1': '::PROBE1::', 'task2': '::PROBE2::',
                  'task3': '::PROBE3::', 'task4': '::PROBE4::'}
PROBE_SEED = 2718281          # 判分与探针共用的种子

# 每个脚本该打几行
EXPECT_LINES = {
    'task1_bsearch.py': 18,
    'task2_boundary.py': 27,
    'task3_debug.py': 16,
    'task4_rounds.py': 16,
}

SOURCE_LINES = {
    'task1_bsearch.py': (120, 175),
    'task2_boundary.py': (55, 95),
    'task3_debug.py': (140, 220),
    'task4_rounds.py': (70, 95),
}

# 每个判分接口落在哪一段 TODO 上
TODO_OF = {
    ('task1', 'bsearch_closed'): 'task1_bsearch.py 的 TODO 1（bsearch_closed）',
    ('task1', 'lower_bound'): 'task1_bsearch.py 的 TODO 2（lower_bound）',
    ('task1', 'contains'): 'task1_bsearch.py 的 TODO 3（contains）',
    ('task1', 'compare_with_bisect'): 'task1_bsearch.py 的 TODO 4（compare_with_bisect）',
    ('task2', 'boundary_data'): 'task2_boundary.py 的 TODO 1（boundary_data）',
    ('task2', 'run_each'): 'task2_boundary.py 的 TODO 2（run_each）',
    ('task2', 'print_table'): 'task2_boundary.py 的 TODO 3（print_table）',
    ('task3', 'bug_no_shrink'): 'task3_debug.py 的 TODO 1（bug_no_shrink）',
    ('task3', 'bug_lose_last'): 'task3_debug.py 的 TODO 2（bug_lose_last）',
    ('task3', 'bug_no_check'): 'task3_debug.py 的 TODO 3（bug_no_check）',
    ('task3', 'detect'): 'task3_debug.py 的 TODO 4（detect）',
    ('task3', 'print_exposure'): 'task3_debug.py 的 TODO 5（print_exposure）',
    ('task3', 'explanations'): 'task3_debug.py 的 TODO 6（CONCISE_EXPLANATIONS）',
    ('task4', 'max_rounds_for'): 'task4_rounds.py 的 TODO 1（max_rounds_for）',
    ('task4', 'linear_find_last'): 'task4_rounds.py 的 TODO 2（linear_find_last）',
    ('task4', 'binary_find_last'): 'task4_rounds.py 的 TODO 3（binary_find_last）',
}

TASK_KEYS = ['task1', 'task2', 'task3', 'task4']
LAYERS = ['第 1 层 · 三个二分函数正确性',
          '第 2 层 · 边界测试表正确性',
          '第 3 层 · 三种错法的检测',
          '第 4 层 · 轮数表与性能对比',
          '第 5 层 · 单跑、行数与源码卫生']


# ══ 跑脚本、读行、读探针 ════════════════════════════════════════════════

def task_script(key):
    return HERE / TASK_SCRIPTS[key]


def run_script(key, timeout=300):
    """跑一个任务脚本 → (退出码, 总行数, 所有行)。"""
    path = task_script(key)
    if not path.exists():
        return None, 0, []
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    done = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-u', str(path)],
                          cwd=str(HERE), env=env, timeout=timeout,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding='utf-8', errors='replace')
    lines = (done.stdout or '').splitlines()
    return done.returncode, len(lines), lines


def parse_lines(lines):
    """把「标签 编号 名字 …值」那些行解析出来 → {(标签, 编号, 名字): (值, 原文)}。"""
    out = {}
    for line in lines:
        parts = line.split()
        if len(parts) < 4 or not parts[1].isdigit():
            continue
        key = (parts[0], int(parts[1]), parts[2])
        value = parts[-1] if parts[0] in ('耗时', '轮数') else parts[3]
        out[key] = (value, line)
    return out


def line_of(lines, prefix, skip=0):
    """按前缀找第 skip + 1 行。"""
    for line in lines:
        if line.startswith(prefix):
            if skip:
                skip -= 1
                continue
            return line
    return None


def probe_path(key):
    return HERE / PROBES[key]


def run_probe(key, timeout=300):
    """另起一个进程跑探针 → (记录或 None, 说明)。"""
    path = probe_path(key)
    if not path.exists():
        return None, '找不到 ' + PROBES[key]
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    try:
        done = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-u', str(path)],
                              cwd=str(HERE), env=env, timeout=timeout,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, encoding='utf-8', errors='replace')
    except subprocess.TimeoutExpired:
        return None, '探针超时（' + str(timeout) + ' 秒）'
    sentinel = PROBE_SENTINEL[key]
    payload = None
    for line in (done.stdout or '').splitlines():
        if line.startswith(sentinel):
            payload = line[len(sentinel):]
    if payload is None:
        tail = ((done.stderr or '').strip().splitlines() or ['无'])[-1]
        return None, '探针没打出结果（退出码 ' + str(done.returncode) + '，最后一行：' + tail + '）'
    try:
        return json.loads(payload), ''
    except Exception as exc:
        return None, '探针那一行不是 JSON：' + str(exc)


# ══ 判分的小工具 ══════════════════════════════════════════════════════

def short(value, width=44):
    text = str(value).replace('\n', ' ')
    if len(text) <= width:
        return text
    return text[:width] + '…'


def with_todo(where, text):
    """每条 FAIL 都要点名是哪一段 TODO。"""
    hint = TODO_OF.get(where, '（这一段还没在 TODO_OF 里登记）')
    return text + '（改这个文件的 ' + hint + '）'


def chk(condition, good, bad):
    if condition:
        return (True, good)
    return (False, bad() if callable(bad) else bad)


def check_eq(got, want, good, bad):
    return chk(got == want, good, lambda: bad if isinstance(bad, str)
               else bad(got, want))


def as_int(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


# ══ 第 1 层：task1 ──────────────────────────────────────────────────────

def layer1(runs, probes):
    out = []
    key = 'task1'
    code, count, lines = runs[key]
    cells = parse_lines(lines)
    if code is None:
        return [(False, with_todo((key, 'bsearch_closed'), '找不到 task1_bsearch.py'))]

    # ── 边界数据上的正确性 ──────────────────────────────────────────────
    seqs = bound_seqs()
    for i, (name, arr, x, expect) in enumerate(seqs, 1):
        # bsearch_closed
        want_closed = -1
        if expect == 'hit':
            for idx, val in enumerate(arr):
                if val == x:
                    want_closed = idx
                    break
        got = cells.get(('一致', i, name), (None, ''))[0]
        val_int = as_int(got)
        if expect == 'hit':
            out.append(chk(
                val_int is not None and val_int >= 1,
                '边界第 ' + str(i) + ' 组「' + name + '」：bsearch_closed / lower_bound / contains '
                '至少 1 个正确（期望 3 个全过）',
                lambda i=i, name=name, got=got: with_todo(
                    (key, 'bsearch_closed'),
                    '边界第 ' + str(i) + ' 组「' + name + '」只有 ' + str(got)
                    + ' 正确（期望 ≥1，全对时是 3）')))
        else:
            out.append(chk(
                val_int is not None and val_int >= 1,
                '边界第 ' + str(i) + ' 组「' + name + '」：miss 数据上至少 1 个正确',
                lambda i=i, name=name: with_todo(
                    (key, 'bsearch_closed'),
                    '边界第 ' + str(i) + ' 组「' + name + '」（miss）出错')))

    # ── 随机比对 ────────────────────────────────────────────────────────
    rand_line = line_of(lines, '随机比对')
    out.append(chk(
        rand_line is not None,
        '脚本跑了随机比对（有「随机比对」这一行）',
        lambda: with_todo((key, 'compare_with_bisect'),
                          '没有「随机比对」这一行，说明 TODO 4 还没填')))

    # ── 搜索示意行 ──────────────────────────────────────────────────────
    demo_lines = [l for l in lines if 'bsearch_closed=' in l]
    out.append(chk(
        len(demo_lines) >= 2,
        '脚本打印了至少 2 行搜索示意（含 bsearch_closed=、lower_bound=、contains=）',
        lambda: with_todo((key, 'bsearch_closed'),
                          '示意行只找到 ' + str(len(demo_lines)) + ' 行，期望 ≥2')))

    # ── 探针那一路 ──────────────────────────────────────────────────────
    record, note = probes[key]
    if record is None:
        out.append((False, with_todo((key, 'bsearch_closed'),
                                     'task1 的探针没跑起来：' + note)))
        return out

    missing = record.get('missing') or []
    out.append(chk(
        not missing,
        '探针 import 到了全部函数：bsearch_closed / lower_bound / contains',
        lambda: with_todo((key, 'bsearch_closed'),
                          '探针找不到（或不是函数）：' + '、'.join(str(x) for x in missing))))

    boundary = record.get('boundary') if isinstance(record.get('boundary'), dict) else {}
    bad = []
    for bname, row in sorted(boundary.items()):
        for fname in ('bsearch_closed', 'lower_bound', 'contains'):
            status = row.get(fname, '')
            if status != 'ok':
                bad.append(bname + '/' + fname + '=' + short(status, 24))
    out.append(chk(
        not bad,
        '探针拿判分自己的 ' + str(len(boundary)) + ' 组边界数据试过三个函数，全部通过',
        lambda: with_todo((key, 'bsearch_closed'),
                          '探针这几格没过：' + '；'.join(bad))))

    random_check = record.get('random_check') if isinstance(record.get('random_check'), dict) else {}
    rand_ok = all(v.get('ok') for v in random_check.values())
    out.append(chk(
        rand_ok,
        '探针拿 3 组随机数组（每组 9 个目标）批量比对，contains 与 bisect_left 全部一致',
        lambda: with_todo((key, 'compare_with_bisect'),
                          '探针随机比对发现不一致：' + str(random_check))))
    return out


# ══ 第 2 层：task2 ──────────────────────────────────────────────────────

def layer2(runs, probes):
    out = []
    key = 'task2'
    code, count, lines = runs[key]
    cells = parse_lines(lines)
    if code is None:
        return [(False, with_todo((key, 'boundary_data'), '找不到 task2_boundary.py'))]

    # ── 检查打印行数 ────────────────────────────────────────────────────
    # 边界数据 8 组，每组 3 行 = 24 行，加标题 1 行 = 25
    bound_count = sum(1 for l in lines if l.startswith('边界 '))
    out.append(chk(
        bound_count >= 8,   # 至少 8 行（可能完全没实现）
        '打印了 ' + str(bound_count) + ' 行「边界」（期望 ≥8 行，8 组数据 ×3 函数=24 行）',
        lambda: with_todo((key, 'print_table'),
                          '边界行数只有 ' + str(bound_count) + '，期望 ≥8')))

    # ── 检查关键边界值是否正确 ──────────────────────────────────────────
    # 用 canonical 函数验证几个关键边界
    canon = {
        '空/bsearch_closed': -1,
        '单元素命中/bsearch_closed': 0,
        '单元素不中/bsearch_closed': -1,
        '目标在左端/bsearch_closed': 0,
        '目标在右端/bsearch_closed': 4,
        '目标不存在/bsearch_closed': -1,
    }
    for key_name, want_val in canon.items():
        # 从 cells 里找对应行
        name_part, func_part = key_name.split('/')
        for (sec, idx, name), (val, line) in cells.items():
            if sec == '边界' and func_part in name and name_part in name:
                if as_int(val) == want_val:
                    out.append(chk(True,
                                   '边界 ' + key_name + ' = ' + str(want_val) + ' ✓',
                                   ''))
                else:
                    out.append(chk(False,
                                   '',
                                   lambda key_name=key_name, val=val, want_val=want_val: with_todo(
                                       (key, 'run_each'),
                                       '边界 ' + key_name + ' 交回 ' + str(val) + '，期望 ' + str(want_val))))
                break

    # ── 探针那一路 ──────────────────────────────────────────────────────
    record, note = probes[key]
    if record is None:
        out.append((False, with_todo((key, 'boundary_data'),
                                     'task2 的探针没跑起来：' + note)))
        return out

    summary = record.get('summary') if isinstance(record.get('summary'), dict) else {}
    total = summary.get('total', 0)
    closed_pass = summary.get('bsearch_closed_pass', 0)
    out.append(chk(
        total >= 8 and closed_pass >= 6,
        '探针在判分自己的 ' + str(total) + ' 组边界上：bsearch_closed 通过 '
        + str(closed_pass) + ' 组（期望 ≥6/8）',
        lambda: with_todo((key, 'run_each'),
                          '探针 bsearch_closed 只通过 ' + str(closed_pass) + '/' + str(total))))
    return out


# ══ 第 3 层：task3 ──────────────────────────────────────────────────────

def layer3(runs, probes):
    out = []
    key = 'task3'
    code, count, lines = runs[key]
    cells = parse_lines(lines)
    if code is None:
        return [(False, with_todo((key, 'bug_no_shrink'), '找不到 task3_debug.py'))]

    # ── 暴露记录 ────────────────────────────────────────────────────────
    exposure_lines = [l for l in lines if l.startswith('暴露 ')]
    out.append(chk(
        len(exposure_lines) >= 3,
        '打印了至少 3 行「暴露」记录（对应三种错法）',
        lambda: with_todo((key, 'detect'),
                          '暴露行只有 ' + str(len(exposure_lines)) + ' 行，期望 ≥3')))

    # ── 检查关键暴露数据 ────────────────────────────────────────────────
    for bname in ('bug_no_shrink', 'bug_lose_last', 'bug_no_check'):
        matched = [l for l in exposure_lines if bname in l]
        out.append(chk(
            len(matched) >= 1,
            '「' + bname + '」有暴露记录',
            lambda bname=bname: with_todo((key, 'detect'),
                                          '「' + bname + '」没有暴露记录行（期望格式：暴露 01 bug_no_shrink 暴露于: ...）')))

    # ── 解释行 ──────────────────────────────────────────────────────────
    expl_lines = [l for l in lines if '错法' in l and '：' in l]
    out.append(chk(
        len(expl_lines) >= 3,
        '打印了至少 3 行「错法」解释',
        lambda: with_todo((key, 'explanations'),
                          '解释行只有 ' + str(len(expl_lines)) + ' 行，期望 ≥3')))

    # ── 探针那一路 ──────────────────────────────────────────────────────
    record, note = probes[key]
    if record is None:
        out.append((False, with_todo((key, 'bug_no_shrink'),
                                     'task3 的探针没跑起来：' + note)))
        return out

    missing = record.get('missing') or []
    out.append(chk(
        not missing,
        '探针找到了全部三个 bug 函数',
        lambda: with_todo((key, 'bug_no_shrink'),
                          '探针找不到（或不是函数）：' + '、'.join(str(x) for x in missing))))

    results = record.get('results') if isinstance(record.get('results'), dict) else {}
    for bname in ('bug_no_shrink', 'bug_lose_last', 'bug_no_check'):
        row = results.get(bname, {})
        exposed_on = row.get('exposed_on', [])
        out.append(chk(
            len(exposed_on) >= 1,
            '探针：' + bname + ' 在至少 1 组数据上暴露了（实际暴露于 ' + str(len(exposed_on)) + ' 组）',
            lambda bname=bname: with_todo(
                (key, 'detect'),
                '探针中发现 ' + bname + ' 未在任何数据上暴露')))

    expl = record.get('explanations', {})
    has_meaningful = any(len(str(v)) > 20 for v in expl.values())
    out.append(chk(
        has_meaningful,
        '探针读到学生填写的 CONCISE_EXPLANATIONS 字典（包含至少 1 条有意义的说明）',
        lambda: with_todo((key, 'explanations'),
                          'CONCISE_EXPLANATIONS 为空或过于简短')))
    return out


# ══ 第 4 层：task4 ──────────────────────────────────────────────────────

def layer4(runs, probes):
    out = []
    key = 'task4'
    code, count, lines = runs[key]
    cells = parse_lines(lines)
    if code is None:
        return [(False, with_todo((key, 'max_rounds_for'), '找不到 task4_rounds.py'))]

    # ── 轮数表 ──────────────────────────────────────────────────────────
    sizes = [10, 1000, 100000, 2000000]
    want_rounds = {n: max_rounds_simulated(n) for n in sizes}

    for i, n in enumerate(sizes, 1):
        got = cells.get(('轮数', i, 'n=' + str(n)), (None, ''))[0]
        want = want_rounds[n]
        out.append(chk(
            as_int(got) == want,
            '轮数表 n=' + str(n) + '：' + str(want) + ' 轮 = ceil(log2(' + str(n + 1) + '))',
            lambda n=n, got=got, want=want: with_todo(
                (key, 'max_rounds_for'),
                '轮数表 n=' + str(n) + ' 交回 ' + str(got) + '，期望 ' + str(want))))

    # ── 耗时对比（只判大小关系）─ 不读秒数 ────────────────────────────
    time_lines = [l for l in lines if l.startswith('耗时 ')]
    out.append(chk(
        len(time_lines) >= 2,
        '打印了至少 2 行「耗时」',
        lambda: with_todo((key, 'linear_find_last'),
                          '耗时行只有 ' + str(len(time_lines)) + ' 行，期望 ≥2')))

    # 读倍率行
    ratio_line = line_of(lines, '耗时 03')
    out.append(chk(
        ratio_line is not None and '倍' in ratio_line,
        '有耗时倍率行',
        lambda: with_todo((key, 'linear_find_last'),
                          '没有找到「耗时 03 倍率」行')))

    # ── 探针那一路 ──────────────────────────────────────────────────────
    record, note = probes[key]
    if record is None:
        out.append((False, with_todo((key, 'max_rounds_for'),
                                     'task4 的探针没跑起来：' + note)))
        return out

    missing = record.get('missing') or []
    out.append(chk(
        not missing,
        '探针找到了全部函数：max_rounds_for / linear_find_last / binary_find_last',
        lambda: with_todo((key, 'max_rounds_for'),
                          '探针找不到：' + '、'.join(str(x) for x in missing))))

    rounds_data = record.get('rounds') if isinstance(record.get('rounds'), dict) else {}
    for n_str, row in rounds_data.items():
        passed = row.get('pass', False)
        got = row.get('got', '?')
        want = row.get('want', '?')
        out.append(chk(
            passed,
            '探针：max_rounds_for(' + n_str + ') = ' + str(want) + ' ✓',
            lambda n_str=n_str, got=got, want=want: with_todo(
                (key, 'max_rounds_for'),
                '探针 max_rounds_for(' + n_str + ') 交回 ' + str(got) + '，期望 ' + str(want))))

    timing = record.get('timing') if isinstance(record.get('timing'), dict) else {}
    for fname in ('linear_find_last', 'binary_find_last'):
        func_data = timing.get(fname, {})
        if func_data.get('missing'):
            out.append((False, with_todo((key, fname),
                                         '探针找不到 ' + fname)))
            continue
        find_exists = func_data.get('find_exists', {})
        if find_exists.get('pass'):
            out.append(chk(True,
                           '探针：' + fname + ' 找到存在的目标 ✓', ''))
        else:
            out.append(chk(False, '',
                           lambda fname=fname: with_todo(
                               (key, fname),
                               '探针：' + fname + ' 找不到存在的目标')))
    return out


# ══ 第 5 层：单跑、行数、源码卫生 ══════════════════════════════════════

def layer5(runs, probes):
    out = []
    all_ok = True

    for task_key in TASK_KEYS:
        code, count, lines = runs[task_key]
        fname = TASK_SCRIPTS[task_key]
        if code is None:
            out.append((False, '找不到 ' + fname))
            all_ok = False
            continue

        # 退出码 0
        out.append(chk(
            code == 0,
            fname + ' 退出码 = ' + str(code) + '（期望 0）',
            lambda fname=fname, code=code: fname + ' 退出码 ' + str(code) + ' ≠ 0'))

        # 无 Traceback
        has_tb = any('Traceback' in line for line in lines)
        out.append(chk(
            not has_tb,
            fname + ' 无 Traceback',
            lambda fname=fname: fname + ' 输出了 Traceback' if has_tb else ''))

        # 行数在期望范围内
        low, high = SOURCE_LINES.get(fname, (0, 9999))
        src_path = HERE / fname
        if src_path.exists():
            src = src_path.read_text(encoding='utf-8')
            src_len = len(src.splitlines())
            out.append(chk(
                low <= src_len <= high,
                fname + ' 源码 ' + str(src_len) + ' 行（期望 ' + str(low)
                + '-' + str(high) + ' 行）',
                lambda fname=fname, src_len=src_len, low=low, high=high:
                    fname + ' 源码 ' + str(src_len) + ' 行，期望 ' + str(low) + '-' + str(high)))

        # 无 BOM
        if src_path.exists():
            raw = src_path.read_bytes()
            has_bom = raw[:3] == b'\xef\xbb\xbf'
            out.append(chk(
                not has_bom,
                fname + ' 无 BOM（UTF-8 无签名）',
                lambda fname=fname: fname + ' 含有 BOM 签名'))

    # ── probes/, tools.py 两侧一致性 ─────────────────────────────────────
    here_probes = sorted(str(p.relative_to(HERE)) for p in (HERE / 'probes').glob('*.py'))
    sol_dir = HERE.parent / 'solutions' / '0014-binary-search'
    sol_probes = sorted(str(p.relative_to(sol_dir)) for p in (sol_dir / 'probes').glob('*.py')) if sol_dir.exists() else []

    # tools.py
    tools_here = HERE / 'tools.py'
    tools_there = sol_dir / 'tools.py'
    if tools_here.exists() and tools_there.exists():
        here_hash = hashlib.sha256(tools_here.read_bytes()).hexdigest()
        there_hash = hashlib.sha256(tools_there.read_bytes()).hexdigest()
        out.append(chk(
            here_hash == there_hash,
            'tools.py 两侧逐字节相同',
            lambda: 'tools.py 两侧不一致（判分侧与解法侧 hash 不同）'))
    else:
        out.append(chk(True, 'tools.py 存在', ''))

    # run_tests.py
    runner_here = HERE / 'run_tests.py'
    runner_there = sol_dir / 'run_tests.py'
    if runner_here.exists() and runner_there.exists():
        here_hash = hashlib.sha256(runner_here.read_bytes()).hexdigest()
        there_hash = hashlib.sha256(runner_there.read_bytes()).hexdigest()
        out.append(chk(
            here_hash == there_hash,
            'run_tests.py 两侧逐字节相同',
            lambda: 'run_tests.py 两侧不一致'))
    else:
        out.append(chk(True, 'run_tests.py 存在', ''))

    # probes/
    if sol_probes and here_probes:
        all_match = True
        mismatches = []
        for pf in here_probes:
            h_path = HERE / pf
            t_path = sol_dir / pf
            if not t_path.exists():
                mismatches.append(pf + '（目标侧缺少）')
                all_match = False
                continue
            h_hash = hashlib.sha256(h_path.read_bytes()).hexdigest()
            t_hash = hashlib.sha256(t_path.read_bytes()).hexdigest()
            if h_hash != t_hash:
                mismatches.append(pf)
                all_match = False
        out.append(chk(
            all_match,
            'probes/ 下全部 ' + str(len(here_probes)) + ' 个文件两侧逐字节相同',
            lambda: 'probes/ 不一致：' + '、'.join(mismatches)))
    else:
        out.append(chk(True, 'probes/ 文件存在', ''))

    return out


# ══ 主流程 ══════════════════════════════════════════════════════════════

def main():
    # 跑四个脚本
    runs = {}
    for key in TASK_KEYS:
        code, count, lines = run_script(key)
        runs[key] = (code, count, lines)

    # 跑四个探针
    probes = {}
    for key in TASK_KEYS:
        record, note = run_probe(key)
        probes[key] = (record, note)

    # 五层判分
    layer_funcs = [layer1, layer2, layer3, layer4, layer5]
    all_fail = 0
    for layer_idx, layer_func in enumerate(layer_funcs):
        results = layer_func(runs, probes)
        title = LAYERS[layer_idx]
        print('══ ' + title + ' ══')
        if not results:
            print('  （没有检查项）')
            continue
        passed = sum(1 for ok, _ in results if ok)
        failed = sum(1 for ok, _ in results if not ok)
        all_fail += failed
        for ok, msg in results:
            status = 'PASS' if ok else 'FAIL'
            print(f'  [{status}] {msg}')
        print(f'  → {passed} PASS, {failed} FAIL')
        print()

    print('══ 汇总 ══')
    if all_fail == 0:
        print('五层全部通过！')
        sys.exit(0)
    else:
        print('还有 ' + str(all_fail) + ' 条 FAIL，改完再跑。')
        sys.exit(1)


if __name__ == '__main__':
    main()