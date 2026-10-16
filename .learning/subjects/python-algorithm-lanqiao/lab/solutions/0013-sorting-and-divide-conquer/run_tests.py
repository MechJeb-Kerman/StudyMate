#!/usr/bin/env python3
r"""lab 0013 · 自动判分（手写三种排序 + 分治）

用法（在这个任务目录里直接跑）：

    py run_tests.py

判法：**五层**，一层里几条检查各自给 PASS / FAIL。每一层都靠**两路证据**：

    第一路  跑四个任务脚本，读它们自己打印的那些行（那些行是接口）。
    第二路  另起一个进程跑 probes/probe_taskN.py：它 import 学生的函数，
            拿**判分自己的**数据（种子 PROBE_SEED = 2718281，规模与脚本里那份
            刻意不同）复算一遍期望值。只写 print、不写实现拿不到 PASS。

这一课的特殊之处：**天然到处都是计时**（耗时表、随机主元与固定主元的耗时比），
而秒数随机器浮动 —— 拿它当判据，同一份代码会时过时不过。所以本判分：

    · **一条判据都不读秒数**。四个任务脚本照打印耗时，但判分行里没有一处读它。
    · 判的全是**确定量**：排序结果是否与 sorted 逐字相同、比较次数、搬动次数、
      划分次数、递归深度、表的长度与字节数、那几档规模的倍率。
      这些数在同一份数据上每次都是同一个整数，而且能被另起一个进程再算一遍。
    · 「看形状」也用**次数**的比值（n 翻一倍这一列翻几倍），不用秒数的比值。
    · 递归上限那一格判的是**机制**：把上限显式设成一个固定的数，同一份已有序数据上
      固定主元要 RecursionError、随机主元不要 —— 不判一个写死的深度边界。

五层各验什么：

    第 1 层 · 五函数正确性与「看不见的事」（task1_sort_three.py）
        四类数据（随机 / 已有序 / 逆序 / 重复值）上，归并、快排、随机主元快排、
        计数排序都要与 sorted 逐字相同；带 key 的那一版要与 sorted(key=) 同序列；
        归并的递归深度四个 n 上要对；键函数被调用几次（手写那一版远多于内置那一版）。
        探针再拿判分自己的数据（含空数组、单元素、两个、全相同）复算一遍。

    第 2 层 · 那张表的四列与倍率（task2_time_table.py）
        四列都是操作次数：归并搬动（与数据无关，只由 n 定）、固定主元在已有序数据上
        的比较次数（n(n-1)/2）、随机主元的划分次数、计数排序的位置数（n + V）。
        倍率由**判分按同一份数据现算**，再与脚本打印的那几行比；
        「形状不是 n log n」那一列的名字与判分自己挑的一致。

    第 3 层 · 已有序数据上的退化与随机主元（task3_sorted_degrade.py）
        同一份已有序数据、同一条固定的递归上限下：固定主元交回 RecursionError、
        随机主元交回一个正常的深度；固定主元一次都不搬、随机主元搬很多次。
        探针换成判分自己的规模再走一遍这条机制。

    第 4 层 · 计数排序的值域（task4_counting_range.py）
        值域小的时候结果与 sorted 逐字相同、开表成功；表长与字节数能算出来；
        四档分类对；值域 10^9 时脚本自己接得住（不能 Traceback）；
        「另起一个进程去开那张表」这条路走得通。

    第 5 层 · 四个脚本能单独跑、打印行数与参考解一致、源码本身干净
        逐个单跑（退出码 0、0 处 Traceback），核对行数，再扫一遍源码：
        不许有 BOM（会 SyntaxError: invalid non-printable character U+FEFF）、
        不许出现连续三个反引号（会破坏课件代码围栏）、
        probes/ 与 tools.py 两侧必须逐字节相同。

判分不判的东西：注释写得多不多、变量名叫得好不好、秒数好不好看，
由 lab/README.md 的自查清单与课件那一节回答；这里只管跑不跑得动、口径对不对、
结论是不是算出来的。

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
from tools import (counting_bytes, counting_ops_canonical, counting_ops_measured,  # noqa: E402
                   counting_slots, make_duplicates, make_random, make_reversed,
                   make_small, make_sorted, merge_moves_canonical, merge_ops_canonical,
                   merge_ops_measured, merge_sort_canonical, counting_sort_canonical,
                   is_sorted, partition_calls_bound, partition_comparisons_bound,
                   partition_comparisons_canonical, partition_moves_canonical,
                   partition_moves_random_bound, partition_ops_measured,
                   quicksort_ops_measured, range_class, same_as_sorted)

# 四个任务文件的名字：判分按**后缀**找，这样留白版与参考解两侧同一份 run_tests.py 都能用
# （两侧的任务文件故意同名，只是内容一个是留白一个是答案）。
TASK_SCRIPTS = {
    'task1': 'task1_sort_three.py',
    'task2': 'task2_time_table.py',
    'task3': 'task3_sorted_degrade.py',
    'task4': 'task4_counting_range.py',
}

# 探针：另起一个进程 import 学生的函数。两侧逐字节相同。
PROBES = {
    'task1': 'probes/probe_task1.py',
    'task2': 'probes/probe_task2.py',
    'task3': 'probes/probe_task3.py',
    'task4': 'probes/probe_task4.py',
}
PROBE_SENTINEL = {'task1': '::PROBE1::', 'task2': '::PROBE2::',
                  'task3': '::PROBE3::', 'task4': '::PROBE4::'}
PROBE_SEED = 2718281          # 判分与探针共用的种子（与学生脚本里那份刻意不同）

# 判分自己的那几档规模（学生脚本里是 400/800/1600/3200，这里是 300/600/1200）。
JUDGE_SIZES = (300, 600, 1200)
JUDGE_BUCKETS = 1500          # 判分自己的值域宽度（学生脚本里是 2000）
JUDGE_DATA_SEED = 900001      # 判分自己造数据用的种子
JUDGE_LIMIT = 800             # 判分自己钉死的递归上限（判「机制」用）

# 每个脚本该打几行——「多打一行 / 少打一行」也要报出来。
# 这几行是按参考解**实测**数出来的，留白版必须一样多（两侧主块是同一份代码）：
#   任务 1：1 行标题 + 4 行「一致」+ 2 行「键调用」+ 4 行「深度」= 11
#   任务 2：1 + 16（四列 × 四档）+ 12（四列 × 三档倍率）+ 2（形状两行）+ 15（耗时/说明）= 46
#   任务 3：1 + 8（深比较 / 深搬动 / 深划分 / 深深度）+ 2（异常）+ 2（耗时）= 13
#   任务 4：1 + 10（一致 / 操作 / 表大小 / 值域）+ 4（开表）+ 1（进程）+ 2（耗时）= 18
EXPECT_LINES = {
    'task1_sort_three.py': 12,
    'task2_time_table.py': 48,
    'task3_sorted_degrade.py': 13,
    'task4_counting_range.py': 18,
}

# 留白版与参考解的行数：函数体里「几行代码」会不一样，所以这里只记**实测**值，
# 第 5 层不会再要求两侧行数相同（要求的是打印行数相同 —— 主块是同一份代码）。
SOURCE_LINES = {
    'task1_sort_three.py': (261, 334),
    'task2_time_table.py': (246, 272),
    'task3_sorted_degrade.py': (125, 125),
    'task4_counting_range.py': (189, 191),
}

# 每个判分接口落在哪一段 TODO 上——每条 FAIL 后面都带上它。
TODO_OF = {
    ('task1', 'merge'): 'task1_sort_three.py 的 TODO 1（merge）',
    ('task1', 'merge_sort'): 'task1_sort_three.py 的 TODO 2（merge_sort）',
    ('task1', 'partition'): 'task1_sort_three.py 的 TODO 3（partition）',
    ('task1', 'quick_sort'): 'task1_sort_three.py 的 TODO 4（quick_sort）',
    ('task1', 'counting_sort'): 'task1_sort_three.py 的 TODO 5（counting_sort）',
    ('task1', 'quick_sort_random'): 'task1_sort_three.py 的 TODO 6（quick_sort_random）',
    ('task1', 'merge_depth'): 'task1_sort_three.py 的 TODO 7（merge_depth）',
    ('task1', 'merge_sort_key'): 'task1_sort_three.py 的 TODO 8（merge_sort_key）',
    ('task1', 'counting_calls'): 'task1_sort_three.py 的 TODO 9（counting_calls）',
    ('task2', 'merge_moves'): 'task2_time_table.py 的 TODO 1（merge_moves）',
    ('task2', 'quick_fixed_compares'): 'task2_time_table.py 的 TODO 2（quick_fixed_compares）',
    ('task2', 'quick_random_compares'): 'task2_time_table.py 的 TODO 3（quick_random_compares）',
    ('task2', 'counting_positions'): 'task2_time_table.py 的 TODO 4（counting_positions）',
    ('task2', 'bench_table'): 'task2_time_table.py 的 TODO 5（bench_table）',
    ('task2', 'bench_ratios'): 'task2_time_table.py 的 TODO 6（bench_ratios）',
    ('task2', 'not_nlogn'): 'task2_time_table.py 的 TODO 7（not_nlogn）',
    ('task2', 'not_nlogn_reason'): 'task2_time_table.py 的 TODO 8（not_nlogn_reason）',
    ('task3', 'degrade_fixed'): 'task3_sorted_degrade.py 的 TODO 1（degrade_fixed）',
    ('task3', 'degrade_random'): 'task3_sorted_degrade.py 的 TODO 2（degrade_random）',
    ('task3', 'pivot_moves'): 'task3_sorted_degrade.py 的 TODO 3（pivot_moves）',
    ('task4', 'table_slots'): 'task4_counting_range.py 的 TODO 1（table_slots）',
    ('task4', 'table_bytes'): 'task4_counting_range.py 的 TODO 2（table_bytes）',
    ('task4', 'value_range_of'): 'task4_counting_range.py 的 TODO 3（value_range_of）',
    ('task4', 'digest_of'): 'task4_counting_range.py 的 TODO 4（digest_of）',
    ('task4', 'run_at_range'): 'task4_counting_range.py 的 TODO 5（run_at_range）',
    ('task4', 'open_table_here'): 'task4_counting_range.py 的 TODO 6（open_table_here）',
    ('task1', 'lines'): 'task1_sort_three.py 的 TODO 2（merge_sort）',
    ('task2', 'lines'): 'task2_time_table.py 的 TODO 5（bench_table）',
    ('task3', 'lines'): 'task3_sorted_degrade.py 的 TODO 1（degrade_fixed）',
    ('task4', 'lines'): 'task4_counting_range.py 的 TODO 5（run_at_range）',
}

TASK_KEYS = ['task1', 'task2', 'task3', 'task4']
LAYERS = ['第 1 层 · 五函数正确性与看不见的事',
          '第 2 层 · 那张表的四列与倍率',
          '第 3 层 · 已有序数据上的退化与随机主元',
          '第 4 层 · 计数排序的值域',
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
    """把「标签 编号 名字 …值」那些行解析出来 → {(标签, 编号, 名字): (值, 原文)}。

    两段格式（都靠位置切，判分只认自己写下来的那几种）：

      「一致 01 随机 4」         标签 编号 名字 值
      「深度 04 归并 n=32768 16」 标签 编号 名字 说明 值   ← 值在**最后**一段

    后者那一段是「说明」，判分要的是最后那一段里的数，所以这几行单独认。
    """
    out = {}
    for line in lines:
        parts = line.split()
        if len(parts) < 4 or not parts[1].isdigit():
            continue
        key = (parts[0], int(parts[1]), parts[2])
        value = parts[-1] if parts[0] == '深度' else parts[3]
        out[key] = (value, line)
    return out


def line_of(lines, prefix, skip=0):
    """按前缀找第 skip + 1 行（耗时的那些行不按四段切）。"""
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


# ══ 判分自己那几档：现算期望值 ══════════════════════════════════════════

def judge_data(n):
    """判分自己的两份数据：值域小的那一份（计数排序用）与大值域那一份。"""
    return make_small(n, JUDGE_BUCKETS, JUDGE_DATA_SEED), make_random(n)


def expected_table(sizes=JUDGE_SIZES):
    """判分自己算的四列（都是操作次数，一个秒数都没有）。"""
    columns = {'归并': [], '固定主元': [], '随机主元': [], '计数': []}
    for n in sizes:
        small, big = judge_data(n)
        ordered = sorted(big)
        columns['归并'].append(merge_ops_measured(big)[0])
        columns['固定主元'].append(partition_ops_measured(ordered, 'fixed')[0])
        columns['随机主元'].append(partition_ops_measured(ordered, 'random')[0])
        columns['计数'].append(sum(counting_ops_measured(small, JUDGE_BUCKETS - 1)))
    return columns


def ratios_of(values):
    return [round(values[i] / values[i - 1], 2) for i in range(1, len(values))]


def judged_ratios(columns=None):
    if columns is None:
        columns = expected_table()
    return dict((name, ratios_of(values)) for name, values in columns.items())


def judge_odd_column(ratios):
    """判分自己从倍率里挑「形状不是 n log n」的那一列（与脚本里那个函数同一口径）。"""
    growth = {}
    for name, steps in ratios.items():
        product = 1.0
        for value in steps:
            product *= value
        growth[name] = product
    return min(growth, key=lambda name: growth[name])


# ── 判分与探针共用的参照（探针那边另有一份**本文件里现算的**，两路对照）──

def key_calls_here(items, key):
    return judge.key_calls_canonical(items, key)


# ══ 判分的小工具：chk / with_todo / 交回值整理 ══════════════════════════

def short(value, width=44):
    text = str(value).replace('\n', ' ')
    if len(text) <= width:
        return text
    return text[:width] + '…'


def with_todo(where, text):
    """每条 FAIL 都要点名是哪一段 TODO —— 这里统一挂上去。"""
    hint = TODO_OF.get(where, '（这一段还没在 TODO_OF 里登记）')
    return text + '（改这个文件的 ' + hint + '）'


def chk(condition, good, bad):
    """一条检查：过了给 PASS 与好话，没过给 FAIL 与坏话（坏话里必须点名 TODO）。"""
    if condition:
        return (True, good)
    return (False, bad() if callable(bad) else bad)


def check_eq(got, want, good, bad):
    return chk(got == want, good, lambda: bad if isinstance(bad, str)
               else bad(got, want))


def cell(seq, index):
    """从表/元组里取一格；还没写出来（太短或不是序列）时交回 None。"""
    if not isinstance(seq, (list, tuple)) or index >= len(seq):
        return None
    return seq[index]


def as_int(value):
    """把交回的值归成 int；归不了就交回 None（不抛异常）。"""
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


def error_note(error, where=None):
    if not error:
        return ''
    if where is not None:
        return '（' + where + '）'
    return '（' + str(error) + '）'


def scheme_note(error):
    return '' if not error else '（提示：' + str(error) + '）'


# ══ 第 1 层：task1 ──────────────────────────────────────────────────────

def layer1(runs, probes):
    out = []
    key = 'task1'
    code, count, lines = runs[key]
    cells = parse_lines(lines)

    if code is None:
        return [(False, with_todo((key, 'merge_sort'), '找不到 task1_sort_three.py'))]

    # 判分自己的四类数据（与脚本里那份刻意不同：这里 n = 3000）
    judge_sets = [
        ('随机', make_random(3000)),
        ('已有序', make_sorted(3000)),
        ('逆序', make_reversed(3000)),
        ('重复值', make_duplicates(3000, 20)),
    ]
    for i, (name, data) in enumerate(judge_sets, 1):
        want = sorted(data)
        maxv = max(data) if data else 0
        if maxv <= 20000:
            assert want == counting_sort_canonical(data, maxv)
        got = cells.get(('一致', i, name), (None, ''))[0]
        if maxv > 20000:
            # 计数排序只能处理小值域（表长 = maxv + 1），大值域上会 MemoryError。
            # 此时期望 3 个通过（归并、快排、随机主元），计数正确报错。
            out.append(chk(
                as_int(got) >= 3,
                '第 ' + str(i) + ' 组「' + name + '」：3 个版本（归并 / 快排 / 随机主元快排）'
                '与 sorted 逐字相同；计数排序在大值域上正确报 MemoryError',
                lambda i=i, name=name, got=got: with_todo(
                    (key, 'merge_sort'),
                    '「' + name + '」这一组只有 ' + str(got) + ' 个版本与 sorted 一致，'
                    '期望 ≥3（计数排序处理不了 10^9 量级的值域，报 MemoryError 是正确的）')))
        else:
            out.append(chk(
                as_int(got) == 4 and int(got) == 4,
                '第 ' + str(i) + ' 组「' + name + '」：归并 / 快排 / 随机主元快排 / 计数排序'
                '四个都与 sorted 逐字相同（判分自己那份 n = 3000 也认这四组）',
                lambda i=i, name=name, got=got: with_todo(
                    (key, 'merge_sort'),
                    '「' + name + '」这一组只有 ' + str(got) + ' 个版本与 sorted 一致，'
                    '期望 4 个（这一组判分自己也算过：四个都要等于 sorted 的结果）')))

    ordered = cells.get(('一致', 5, '带key'), (None, ''))[0]
    out.append(chk(
        as_int(ordered) == 1,
        '带 key 的归并版（merge_sort_key）与 sorted(key=) 给出同一个序列',
        lambda: with_todo((key, 'merge_sort_key'),
                          '带 key 那一行是 ' + str(ordered) + '，期望 1：'
                          'merge_sort_key 交回的序列要与 sorted(pairs, key=...) 一样')))

    # 键函数被调用几次：手写那一版远多于内置那一版
    items = [(i % 97, i) for i in range(2000)]
    want_hand = key_calls_here(items, lambda item: item[0])
    hand = as_int(cells.get(('键调用', 6, '手写'), (None, ''))[0])
    builtin = as_int(cells.get(('键调用', 7, 'sorted'), (None, ''))[0])
    out.append(chk(
        hand == want_hand and builtin == len(items),
        '键函数被调用几次：手写那一版 ' + str(hand) + ' 次、内置 sorted(key=) '
        + str(builtin) + ' 次 —— 判分自己按同一个结构数出来也是 '
        + str(want_hand) + ' 与 ' + str(len(items))
        + '（内置每元素只算一次键，手写那版每次比较都要算两个）',
        lambda: with_todo((key, 'merge_sort_key'),
                          '键调用那一对数是 ' + str(hand) + ' 与 ' + str(builtin)
                          + '，判分自己数出来是 ' + str(want_hand) + ' 与 '
                          + str(len(items)))))
    out.append(chk(
        hand is not None and builtin is not None and hand > builtin * 5,
        '手写的键调用次数是内置的 ' + str(round(hand / builtin, 1) if builtin else '—')
        + ' 倍 —— 这就是「手写版把 key 放进比较里」的代价',
        lambda: with_todo((key, 'merge_sort_key'),
                          '手写那一版只把键算了 ' + str(hand) + ' 次、内置 '
                          + str(builtin) + ' 次：差得太少，说明键没有放进比较里'
                          '（放进比较里必然远多于 n）')))

    # 归并递归深度：四个 n 上都要对
    want_depth = [judge.merge_depth_canonical(n) for n in (8, 1000, 32768, 100000)]
    got_depth = [as_int(cells.get(('深度', 8 + i, '归并'), (None, ''))[0])
                 for i in range(4)]
    for i, (n, want) in enumerate(zip((8, 1000, 32768, 100000), want_depth)):
        got = got_depth[i]
        out.append(chk(
            got == want,
            'merge_depth(' + str(n) + ') = ' + str(want) + ' —— 判分自己按同一个切法数也是它',
            lambda n=n, want=want, got=got: with_todo(
                (key, 'merge_depth'),
                'merge_depth(' + str(n) + ') 交回 ' + str(got) + '，期望 ' + str(want)
                + '（= ceil(log2 n) + 1）')))

    # ── 探针那一路 ──────────────────────────────────────────────────────
    record, note = probes[key]
    if record is None:
        out.append((False, with_todo((key, 'merge_sort'),
                                     'task1 的探针没跑起来：' + note)))
        return out

    missing = record.get('missing') or []
    out.append(chk(
        not missing,
        '探针在判分自己的进程里 import 到了全部函数：merge / merge_sort / quick_sort / '
        'quick_sort_random / counting_sort / merge_depth / merge_sort_key',
        lambda: with_todo((key, 'merge_sort'),
                          '探针找不到（或不是函数）：' + '、'.join(str(x) for x in missing))))

    rows = record.get('sorted') if isinstance(record.get('sorted'), dict) else {}
    bad = []
    for name, row in sorted(rows.items()):
        if not isinstance(row, dict):
            bad.append(str(name) + '（' + short(row, 20) + '）')
            continue
        wrong = [fname for fname, value in row.items() if value != 'ok']
        if wrong:
            bad.append(str(name) + '→' + '、'.join(sorted(wrong)))
    out.append(chk(
        not bad,
        '探针拿判分自己的九组数据（空数组、单元素、两个、全相同、已有序、逆序、'
        '随机、重复值、n=1000）试过四个排序函数与 merge，每一个都与 sorted 逐字相同',
        lambda: with_todo((key, 'merge_sort'),
                          '探针这几格没过：' + '；'.join(bad)
                          + '（判分用自己的数据排好了一份标准答案来比）')))

    depth_got = record.get('depth') if isinstance(record.get('depth'), dict) else {}
    depth_want = record.get('depth_expected') if isinstance(record.get('depth_expected'), dict) else {}
    off = []
    for n in sorted(depth_want, key=lambda x: int(x)):
        if as_int(depth_got.get(n)) != as_int(depth_want[n]):
            off.append('n=' + str(n) + ' 交回 ' + short(depth_got.get(n), 16)
                       + '、期望 ' + str(depth_want[n]))
    out.append(chk(
        not off,
        '探针里 merge_depth 在 n = 1 / 2 / 9 / 1000 / 12345 上与判分自己数的一致'
        '（' + '、'.join('n=' + str(n) + ' → ' + str(depth_want[n])
                         for n in sorted(depth_want, key=lambda x: int(x))) + '）',
        lambda: with_todo((key, 'merge_depth'),
                          '探针里 merge_depth 对不上：' + '；'.join(off))))

    kc = record.get('keycalls') if isinstance(record.get('keycalls'), dict) else {}
    want_kc = as_int(record.get('keycalls_expected'))
    out.append(chk(
        kc.get('answer_ok') is True and as_int(kc.get('calls')) == want_kc,
        '探针里 merge_sort_key 的答案与 sorted(key=) 一致，而且键被调用了 '
        + str(want_kc) + ' 次 —— 与判分自己按同一结构数出来的一模一样',
        lambda: with_todo((key, 'merge_sort_key'),
                          '探针里 merge_sort_key 这一格：答案对不对='
                          + str(kc.get('answer_ok')) + '、键调用 ' + short(kc.get('calls'), 16)
                          + ' 次（判分自己数出来是 ' + str(want_kc) + ' 次）')))
    return out


# ══ 第 2 层：task2 ──────────────────────────────────────────────────────

def layer2(runs, probes):
    out = []
    key = 'task2'
    code, count, lines = runs[key]
    cells = parse_lines(lines)
    if code is None:
        return [(False, with_todo((key, 'bench_table'), '找不到 task2_time_table.py'))]

    # ── 脚本打印的那四列：判分按**同一份数据**现算一遍 ────────────────────
    # 判分自己造数据：值域小的那一份 0..1999（计数排序用），大值域那一份（三个比较类排序用）。
    script_sizes = (400, 800, 1600, 3200)
    script_columns = {'归并': [], '固定主元': [], '随机主元': [], '计数': []}
    for n in script_sizes:
        small = make_small(n, 2000, JUDGE_DATA_SEED)
        big = make_random(n)
        ordered = sorted(big)
        script_columns['归并'].append(merge_ops_measured(big)[0])
        script_columns['固定主元'].append(partition_ops_measured(ordered, 'fixed')[0])
        script_columns['随机主元'].append(partition_ops_measured(ordered, 'random')[0])
        script_columns['计数'].append(sum(counting_ops_measured(small, 1999)))

    printed = {'归并': [], '固定主元': [], '随机主元': [], '计数': []}
    for i in range(1, 5):
        for name in printed:
            printed[name].append(as_int(cells.get(('操作', i, name), (None, ''))[0]))

    for name in ('归并', '固定主元', '随机主元', '计数'):
        got = printed[name]
        want = script_columns[name]
        detail = '、'.join('n=' + str(n) + ' → ' + str(v) for n, v in zip(script_sizes, want))
        extra = ''
        if name == '随机主元':
            extra = '（随机主元按固定种子把主元换到开头，所以这几格也是同一个整数）'
        out.append(chk(
            got == want,
            '「' + name + '」那一列的四个数与判分按同一份数据现算的一致：' + detail + extra,
            lambda name=name, got=got, want=want: with_todo(
                (key, 'bench_table'),
                '「' + name + '」那一列交回 ' + short(got, 30) + '，判分按同一份数据'
                '现算是 ' + short(want, 30))))

    # 归并那一列的形状说明：它与数据无关（有序 / 乱序 / 全是重复值都一样多）
    for shape, data in (('已有序', make_sorted(777)), ('逆序', make_reversed(777)),
                        ('重复值', make_duplicates(777, 20))):
        want = merge_moves_canonical(777)
        got = judge.merge_ops_measured(data)[0]
        out.append(chk(
            got == want,
            '归并的搬动次数在「' + shape + '」数据上与乱序时一样多（都是 ' + str(want)
            + '）—— 这一格只由 n 决定，与数据形状无关',
            lambda shape=shape, got=got: '判分自己的口径出了问题：' + shape
            + ' 上量出 ' + str(got)))

    # 倍率：脚本打印的那几行要与判分按同一份数据算出来的一致
    script_ratios = {}
    for name in ('归并', '固定主元', '随机主元', '计数'):
        steps = []
        for i in (2, 3, 4):
            value = cells.get(('倍率', i, name), (None, ''))[0]
            try:
                steps.append(round(float(value), 2))
            except (TypeError, ValueError):
                steps.append(None)
        script_ratios[name] = steps
    want_script_ratios = dict((name, ratios_of(values))
                              for name, values in script_columns.items())
    for name in ('归并', '固定主元', '随机主元', '计数'):
        want = want_script_ratios[name]
        out.append(chk(
            script_ratios[name] == want,
            '倍率（同一列这一档 ÷ 上一档）「' + name + '」= '
            + '、'.join(str(v) for v in want)
            + ' —— 判分按同一份数据现算的也是这三个数',
            lambda name=name, want=want: with_todo(
                (key, 'bench_ratios'),
                '「' + name + '」那一列的倍率交回 ' + short(script_ratios.get(name), 30)
                + '，判分按同一份数据现算是 ' + short(want, 30))))

    # 形状：哪一列不是 n log n
    odd_want = judge_odd_column(want_script_ratios)
    odd_got = cells.get(('形状', 1, '不是nlogn'), (None, ''))[0]
    out.append(chk(
        odd_got == odd_want,
        '「形状不是 n log n」那一列点名了「' + odd_want + '」—— 判分从同一批倍率里'
        '挑出来的也是它（表长由值域定，n 翻倍它几乎不长）',
        lambda: with_todo((key, 'not_nlogn'),
                          '形状那一行点名了「' + str(odd_got) + '」，判分挑出来的是「'
                          + str(odd_want) + '」（按同一批倍率里总倍数最小的那一列挑）')))

    reason = line_of(lines, '形状 02')
    out.append(chk(
        reason is not None and odd_want in reason and len(reason) > 20,
        '形状 02 那一行写了理由，而且提到了那一列的名字（判分只核这两条：非空、点名）',
        lambda: with_todo((key, 'not_nlogn_reason'),
                          '形状 02 那一行是 ' + short(reason, 40)
                          + '，期望它提到「' + str(odd_want) + '」并写清为什么')))

    # ── 探针那一路：判分换成自己的三档规模 300 / 600 / 1200 再算一遍 ──────
    record, note = probes[key]
    if record is None:
        out.append((False, with_todo((key, 'bench_table'),
                                     'task2 的探针没跑起来：' + note)))
        return out
    if record.get('missing'):
        out.append((False, with_todo((key, 'bench_table'),
                                     '探针找不到（或不是函数）：'
                                     + '、'.join(str(x) for x in record['missing']))))
        return out

    want_table = record.get('expected', {}).get('table', {})
    got_table = record.get('table') if isinstance(record.get('table'), dict) else {}
    for name in ('归并', '固定主元', '随机主元', '计数'):
        want = [as_int(v) for v in (want_table.get(name) or [])]
        got = [as_int(v) for v in (got_table.get(name) or [])]
        sizes_text = '、'.join('n=' + str(n) for n in JUDGE_SIZES)
        out.append(chk(
            got == want,
            '探针（判分自己的三档 ' + sizes_text + '）里「' + name + '」那一列 = '
            + '、'.join(str(v) for v in want) + ' —— 判分自己按同一切法也算了一遍',
            lambda name=name, got=got, want=want: with_todo(
                (key, 'bench_table'),
                '探针里「' + name + '」那一列交回 ' + short(got, 30)
                + '，判分自己算的是 ' + short(want, 30))))

    free = record.get('expected', {}).get('digest_free', {})
    got_counts = record.get('counts') if isinstance(record.get('counts'), dict) else {}
    for name in ('merge_moves', 'quick_fixed_compares', 'quick_random_compares',
                 'counting_positions'):
        want = as_int(free.get(name))
        got = as_int(got_counts.get(name))
        out.append(chk(
            got == want and want is not None,
            '探针里 ' + name + '(...) = ' + str(want)
            + '（判分自己的数据现算：与它自己的公式一致）',
            lambda name=name, got=got, want=want: with_todo(
                (key, name),
                '探针里 ' + name + ' 交回 ' + str(got) + '，判分自己的数据与公式算出 '
                + str(want))))

    probe_odd = record.get('not_nlogn')
    out.append(chk(
        probe_odd == record.get('expected', {}).get('not_nlogn'),
        '探针按判分自己的三档倍率再挑一次，学生交回的名字是「' + str(probe_odd) + '」',
        lambda: with_todo((key, 'not_nlogn'),
                          '探针里 not_nlogn 交回 ' + short(probe_odd, 20)
                          + '，期望「计数」')))
    return out


# ══ 第 3 层：task3 ──────────────────────────────────────────────────────

def layer3(runs, probes):
    out = []
    key = 'task3'
    code, count, lines = runs[key]
    cells = parse_lines(lines)
    if code is None:
        return [(False, with_todo((key, 'degrade_fixed'),
                                  '找不到 task3_sorted_degrade.py'))]

    size = 20000
    want_cmp = size * (size - 1) // 2
    fixed_cmp = as_int(cells.get(('深比较', 1, '固定主元'), (None, ''))[0])
    rand_cmp = as_int(cells.get(('深比较', 2, '随机主元'), (None, ''))[0])
    fixed_move = as_int(cells.get(('深搬动', 3, '固定主元'), (None, ''))[0])
    rand_move = as_int(cells.get(('深搬动', 4, '随机主元'), (None, ''))[0])
    fixed_jobs = as_int(cells.get(('深划分', 5, '固定主元'), (None, ''))[0])
    rand_jobs = as_int(cells.get(('深划分', 6, '随机主元'), (None, ''))[0])
    fixed_depth = cells.get(('深深度', 7, '固定主元'), (None, ''))[0]
    rand_depth_text = cells.get(('深深度', 8, '随机主元'), (None, ''))[0]

    # 固定主元：撞上限；报错类型名与「撞的时候划分了几次」一起交出来
    line_fixed = line_of(lines, '异常 01 固定主元')
    line_random = line_of(lines, '异常 02 随机主元')
    out.append(chk(
        line_fixed is not None and 'RecursionError' in line_fixed
        and line_random is not None and '未抛' in line_random,
        '同一份已有序数据（n=' + str(size) + '）、同一条固定的递归上限下：固定主元撞了'
        ' RecursionError，随机主元没撞 —— 判分核的是这个**机制**，'
        '不是一个写死的深度边界',
        lambda: with_todo((key, 'degrade_fixed'),
                          '那两行报错是 ' + short(line_fixed, 30) + ' / '
                          + short(line_random, 30) + '：期望固定主元那一行带 RecursionError、'
                          '随机主元那一行是「未抛」（同一份数据、同一条上限）')))

    out.append(chk(
        fixed_depth is not None and '撞' in str(fixed_depth),
        '固定主元那一行的深度打印的是「撞上限」（没有深度可报）',
        lambda: with_todo((key, 'degrade_fixed'),
                          '固定主元的深度打印成了 ' + str(fixed_depth)
                          + '：撞了上限时应当没有数可打印')))

    out.append(chk(
        as_int(rand_depth_text) is not None and 1 <= as_int(rand_depth_text) <= 100,
        '随机主元同一份数据上只落 ' + str(rand_depth_text) + ' 层（随机主元让划分'
        '不容易总落在端点上，深度回到 log n 量级）',
        lambda: with_todo((key, 'degrade_random'),
                          '随机主元那一行的深度是 ' + str(rand_depth_text)
                          + '：期望是一个正常的层数（几层到几十层）')))

    # 固定主元在已有序数据上：**撞上限之前**已经比了 n 平方量级的次数。
    # 这里刻意不核「正好 n(n-1)/2」—— 撞上限时它会提前停下，完整跑完才是那个数。
    # 判的是「它长到了 n 平方量级、而且远远多于它比完之前能划分的次数」。
    # 下界不按 n²/4 算（实际只跑约 LIMIT 层就被上限拦住），改按 LIMIT × n/2 估。
    crash_jobs = as_int(cells.get(('深划分', 5, '固定主元'), (None, ''))[0]) or 1
    floor_cmp = max(1, crash_jobs * size // 4)
    out.append(chk(
        fixed_cmp is not None and floor_cmp <= fixed_cmp <= want_cmp,
        '固定主元在已有序数据上比了 ' + str(fixed_cmp) + ' 次（它撞上限前就比了这么多：'
        '完整跑完是 ' + str(want_cmp) + ' = n(n-1)/2，撞上限时提前停在 '
        + str(fixed_cmp) + '）—— 每一次划分只削掉一个元素',
        lambda: with_todo((key, 'degrade_fixed'),
                          '固定主元的比较次数是 ' + str(fixed_cmp) + '，期望落在 '
                          + str(floor_cmp) + ' 与 ' + str(want_cmp) + ' 之间（n 平方量级；'
                          '完整跑完是 n(n-1)/2）')))

    # 划分次数：固定主元撞上限时停在一千上下 —— 关键是它**远大于**它比完之前该有的次数吗？
    # 这里判的是「它一路只削掉一个元素」：划分次数 = 它走到的那一层，
    # 而那个数要比 log2 n 大得多（几百上千 vs 十几）。
    out.append(chk(
        fixed_jobs is not None and fixed_jobs > 100 and fixed_jobs <= size - 1
        and rand_jobs is not None and rand_jobs <= size - 1,
        '划分次数：固定主元 ' + str(fixed_jobs) + ' 次（它一直只削掉一个元素，'
        '撞上限时已经走到第 ' + str(fixed_jobs) + ' 层）、随机主元 ' + str(rand_jobs)
        + ' 次（挑到端点时会省掉一次，n=' + str(size) + ' 不超过 ' + str(size - 1) + '）',
        lambda: with_todo((key, 'degrade_fixed'),
                          '划分次数是 ' + str(fixed_jobs) + ' 与 ' + str(rand_jobs)
                          + '，期望固定主元走到一百层以上、且两列都不超过 ' + str(size - 1))))

    # 比这个数就能看出退化有多重：比较次数差了一个多数量级
    if isinstance(rand_cmp, int) and rand_cmp > 0:
        out.append(chk(
            fixed_cmp is not None and fixed_cmp > rand_cmp * 10,
            '同一份数据上：固定主元比了 ' + str(fixed_cmp) + ' 次、随机主元只比了 '
            + str(rand_cmp) + ' 次 —— 差 ' + str(round(fixed_cmp / rand_cmp))
            + ' 倍（判的是**次数**的比，不是秒数的比）',
            lambda: with_todo((key, 'degrade_random'),
                              '两个版本的比较次数是 ' + str(fixed_cmp) + ' 与 '
                              + str(rand_cmp) + '，期望差十倍以上')))
    else:
        out.append(chk(False, '', lambda: with_todo(
            (key, 'degrade_random'),
            '随机主元那一格没交出比较次数（' + str(rand_cmp) + '）')))

    # 搬动方向相反：有序数据上固定主元一次都不搬
    out.append(chk(
        fixed_move == 0 and as_int(rand_move) is not None and rand_move > 0,
        '搬动次数：固定主元 ' + str(fixed_move) + ' 次（有序数据上它一个元素都不小于主元，'
        '所以一次都不搬）、随机主元 ' + str(rand_move) + ' 次 —— 一个算得多动得少，'
        '一个算得少动得多',
        lambda: with_todo((key, 'pivot_moves'),
                          '搬动次数是 ' + str(fixed_move) + ' 与 ' + str(rand_move)
                          + '，期望固定主元 0、随机主元大于 0（已有序数据上）')))

    # ── 探针那一路：判分换成自己的规模、自己的上限再走一遍这条机制 ────────
    record, note = probes[key]
    if record is None:
        out.append((False, with_todo((key, 'degrade_fixed'),
                                     'task3 的探针没跑起来：' + note)))
        return out
    if record.get('missing'):
        out.append((False, with_todo((key, 'degrade_fixed'),
                                     '探针找不到（或不是函数）：'
                                     + '、'.join(str(x) for x in record['missing']))))
        return out

    fixed = record.get('fixed') if isinstance(record.get('fixed'), dict) else {}
    rand = record.get('random') if isinstance(record.get('random'), dict) else {}
    want_fixed = record.get('expected', {}).get('fixed_error', {})
    want_rand = record.get('expected', {}).get('random_error', {})
    bad_fixed = []
    bad_rand = []
    for n in sorted(want_fixed, key=lambda x: int(x)):
        row = fixed.get(n)
        got = row.get('error') if isinstance(row, dict) else row
        if got != want_fixed[n]:
            bad_fixed.append('n=' + str(n) + ' 交回 ' + short(got, 24))
        row = rand.get(n)
        got = row.get('error') if isinstance(row, dict) else row
        if got != want_rand[n]:
            bad_rand.append('n=' + str(n) + ' 交回 ' + short(got, 24))
    sizes_text = '、'.join('n=' + str(n) for n in sorted(want_fixed, key=lambda x: int(x)))
    out.append(chk(
        not bad_fixed,
        '探针在判分自己的规模（' + sizes_text + '）与自己的上限（' + str(record.get('limit'))
        + '）上：固定主元每一档都交回 RecursionError',
        lambda: with_todo((key, 'degrade_fixed'),
                          '探针里固定主元这一路没爆：' + '；'.join(bad_fixed)
                          + '（同一份已有序数据、同一条固定上限，固定主元应当爆）')))
    out.append(chk(
        not bad_rand,
        '同一批规模与上限上：随机主元每一档都没爆 —— 这才是「随机主元把它修回来了」',
        lambda: with_todo((key, 'degrade_random'),
                          '探针里随机主元这一路爆了：' + '；'.join(bad_rand)
                          + '（随机主元在同一份数据上不该撞上限）')))

    # 探针里固定主元的比较次数：撞上限时会提前停下，所以判的是「落在 n 平方量级里、
    # 且不超过完整跑完的数 n(n-1)/2」——不核一个写死的边界值。
    want_cmp_map = record.get('expected', {}).get('fixed_cmp_no_more_than', {})
    bad_cmp = []
    shown = []
    for n in sorted(want_cmp_map, key=lambda x: int(x)):
        want_full = as_int(want_cmp_map[n])
        row = fixed.get(n)
        got = as_int(row.get('cmp')) if isinstance(row, dict) else None
        if got is None or got <= 0 or (want_full is not None and got > want_full):
            bad_cmp.append('n=' + str(n) + ' 交回 ' + str(got))
        else:
            note = '' if got == want_full else '（撞上限前先停下，完整跑完是 ' + str(want_full) + '）'
            shown.append('n=' + str(n) + ' → ' + str(got) + note)
    out.append(chk(
        not bad_cmp,
        '探针里固定主元的比较次数都落在 n 平方量级里：' + '、'.join(shown),
        lambda: with_todo((key, 'degrade_fixed'),
                          '探针里固定主元的比较次数对不上（期望落在 1 与 n(n-1)/2 之间）：'
                          + '；'.join(bad_cmp))))

    moves = record.get('moves') if isinstance(record.get('moves'), dict) else {}
    want_moves = record.get('expected', {}).get('random_moves_at_least', {})
    bad_moves = []
    for n in sorted(want_moves, key=lambda x: int(x)):
        row = moves.get(n) if isinstance(moves.get(n), dict) else {}
        got_fixed = as_int(row.get('fixed'))
        got_rand = as_int(row.get('random'))
        if got_fixed != 0:
            bad_moves.append('n=' + str(n) + ' 固定主元搬了 ' + str(got_fixed) + ' 次')
        elif got_rand is None or got_rand < as_int(want_moves[n]):
            bad_moves.append('n=' + str(n) + ' 随机主元只搬了 ' + str(got_rand) + ' 次')
    out.append(chk(
        not bad_moves,
        '探针里 pivot_moves：固定主元在已有序数据上一律 0 次，随机主元一律不少于 '
        + '2(n-1)（' + '、'.join('n=' + str(n) + ' → ' + str(want_moves[n])
                                for n in sorted(want_moves, key=lambda x: int(x))) + '）',
        lambda: with_todo((key, 'pivot_moves'),
                          '探针里 pivot_moves 对不上：' + '；'.join(bad_moves))))
    return out


# ══ 第 4 层：task4 ──────────────────────────────────────────────────────

def layer4(runs, probes):
    out = []
    key = 'task4'
    code, count, lines = runs[key]
    cells = parse_lines(lines)
    if code is None:
        return [(False, with_todo((key, 'table_slots'),
                                  '找不到 task4_counting_range.py'))]

    # 值域小的那一档：结果与 sorted 逐字相同 + 操作账目
    small_same = cells.get(('一致', 1, '值域0..999'), (None, ''))[0]
    huge_same = cells.get(('一致', 2, '值域0..10^9'), (None, ''))[0]
    out.append(chk(
        as_int(small_same) == 1,
        '值域 0..999 那一档：计数排序的结果与 sorted 逐字相同',
        lambda: with_todo((key, 'run_at_range'),
                          '值域 0..999 那一行是 ' + str(small_same)
                          + '，期望 1（结果要与 sorted 逐字相同）')))
    out.append(chk(
        as_int(huge_same) is not None,
        '值域 0..10^9 那一档：这一行没有崩掉（' + str(huge_same)
        + '）—— 判分不核答案对不对，只核这一段没有 Traceback',
        lambda: with_todo((key, 'run_at_range'),
                          '值域 0..10^9 那一行是 ' + str(huge_same)
                          + '，期望 1：这一档的结果也要与 sorted 相同')))

    size = 3000
    counted = as_int(cells.get(('操作', 1, '值域0..999'), (None, ''))[0])
    table_written = as_int(cells.get(('操作', 3, '值域0..999表'), (None, ''))[0])
    huge_written = as_int(cells.get(('操作', 4, '值域0..10^9表'), (None, ''))[0])
    out.append(chk(
        counted == size,
        '清点次数 = ' + str(counted) + ' = n（每个元素清点一次）',
        lambda: with_todo((key, 'digest_of'),
                          '清点次数交回 ' + str(counted) + '，期望 ' + str(size) + '（= n）')))
    out.append(chk(
        table_written == 1000 and huge_written == 10 ** 9 + 1,
        '那张表的长度：值域 0..999 是 ' + str(table_written) + ' 个位置、'
        '值域 0..10^9 是 ' + str(huge_written) + ' 个位置 —— 都由 maxv + 1 算出来',
        lambda: with_todo((key, 'digest_of'),
                          '表长交回 ' + str(table_written) + ' 与 ' + str(huge_written)
                          + '，期望 1000 与 ' + str(10 ** 9 + 1))))

    # 表大小那一行：判分换成自己的值域再算一遍（读取打印行里的两个数）
    line_small = line_of(lines, '表大小 01')
    line_huge = line_of(lines, '表大小 02')
    got_slots = None
    got_bytes = None
    if line_huge:
        match = re.search(r'需要\s*(\d+)\s*个位置，约\s*([\d.]+)\s*MB', line_huge)
        if match:
            got_slots = int(match.group(1))
            got_bytes = float(match.group(2))
    out.append(chk(
        got_slots == counting_slots(10 ** 9)
        and got_bytes is not None and abs(got_bytes - counting_bytes(10 ** 9) / 1048576) < 1.0,
        '表大小那一行：值域 10^9 需要 ' + str(counting_slots(10 ** 9)) + ' 个位置、约 '
        + format(counting_bytes(10 ** 9) / 1048576, '.1f') + ' MB —— 判分按 maxv + 1 '
        '与「一个位置 8 字节」自己也算了一遍',
        lambda: with_todo((key, 'table_bytes'),
                          '那一行是 ' + short(line_huge, 44) + '，期望 '
                          + str(counting_slots(10 ** 9)) + ' 个位置、约 '
                          + format(counting_bytes(10 ** 9) / 1048576, '.1f') + ' MB')))
    out.append(chk(
        line_small is not None and '1000' in line_small,
        '值域 0..999 那一行报的是 1000 个位置（' + short(line_small, 30) + '）',
        lambda: with_todo((key, 'table_slots'),
                          '值域 0..999 那一行是 ' + short(line_small, 30)
                          + '，期望 1000 个位置')))

    # 分类：脚本报的两档要与判分自己算的一致
    small_class = cells.get(('值域', 1, '值域0..999'), (None, ''))[0]
    huge_class = cells.get(('值域', 2, '值域0..10^9'), (None, ''))[0]
    out.append(chk(
        small_class == range_class(999) and huge_class == range_class(10 ** 9),
        '值域分类：0..999 → ' + str(small_class) + '、0..10^9 → ' + str(huge_class)
        + '（判分按表的长度自己也算了一遍）',
        lambda: with_todo((key, 'value_range_of'),
                          '分类交回 ' + str(small_class) + ' 与 ' + str(huge_class)
                          + '，期望 ' + range_class(999) + ' 与 ' + range_class(10 ** 9))))

    # 「开表」那两行：小值域要开得出来
    open_small = cells.get(('开表', 1, '值域0..999'), (None, ''))[0]
    open_len = as_int(cells.get(('开表', 3, '值域0..999表长'), (None, ''))[0])
    out.append(chk(
        open_small == '开出来了' and open_len == 1000,
        '值域 0..999 时那一行「开表」真的开出来了，表长交回 ' + str(open_len) + '（= 1000）',
        lambda: with_todo((key, 'open_table_here'),
                          '值域 0..999 的开表那一行是 ' + str(open_small) + '、表长 '
                          + str(open_len) + '，期望「开出来了」与 1000')))

    # 「另起一个进程」那条路：子进程怎么死都行，但这几个词得是它给的
    word = cells.get(('进程', 1, '值域0..10^9'), (None, ''))[0]
    out.append(chk(
        word in ('ok', 'hard-crash', 'timeout')
        or (isinstance(word, str) and word.startswith('error:')),
        '「另起一个进程」那条路走得通：判分自己起了一个子进程、按名字找到了函数，'
        '交回的结果是「' + str(word) + '」（落到哪个词看机器有多少内存，判分都认）',
        lambda: with_todo((key, 'open_table_here'),
                          '「另起一个进程」交回 ' + str(word)
                          + '：期望 ok / error:类型 / hard-crash / timeout —— '
                          '「missing」说明子进程按这个名字找不到函数')))

    # 脚本本身不能 Traceback（值域大到开不出来时它要接得住）
    out.append(chk(
        'Traceback' not in '\n'.join(lines),
        '值域开到 10^9 时脚本自己接住了那一步（输出里 0 处 Traceback）',
        lambda: with_todo((key, 'run_at_range'),
                          '脚本输出里有 Traceback：值域大到开不出表时要用 attempt 接住，'
                          '只把报错类型名打出来')))

    # ── 探针那一路：判分换成自己的值域（0 / 999 / 12345 / 10^6-1 / 10^7 / 10^9-1 / 10^9）──
    record, note = probes[key]
    if record is None:
        out.append((False, with_todo((key, 'table_slots'),
                                     'task4 的探针没跑起来：' + note)))
        return out
    if record.get('missing'):
        out.append((False, with_todo((key, 'table_slots'),
                                     '探针找不到（或不是函数）：'
                                     + '、'.join(str(x) for x in record['missing']))))
        return out

    want_slots = record.get('expected', {}).get('slots', {})
    got_slots_map = record.get('slots') if isinstance(record.get('slots'), dict) else {}
    bad = [('maxv=' + str(maxv) + ' 交回 ' + str(got_slots_map.get(maxv))
            + '、期望 ' + str(want))
           for maxv, want in sorted(want_slots.items(), key=lambda kv: int(kv[0]))
           if as_int(got_slots_map.get(maxv)) != as_int(want)]
    out.append(chk(
        not bad,
        '探针里 table_slots 在判分自己的七个值域上都对：'
        + '、'.join('maxv=' + str(maxv) + ' → ' + str(want)
                    for maxv, want in sorted(want_slots.items(), key=lambda kv: int(kv[0]))),
        lambda: with_todo((key, 'table_slots'),
                          '探针里 table_slots 对不上：' + '；'.join(bad))))

    want_bytes = record.get('expected', {}).get('bytes', {})
    got_bytes_map = record.get('bytes') if isinstance(record.get('bytes'), dict) else {}
    bad = [('maxv=' + str(maxv) + ' 交回 ' + str(got_bytes_map.get(maxv)))
           for maxv, want in want_bytes.items()
           if as_int(got_bytes_map.get(maxv)) != as_int(want)]
    out.append(chk(
        not bad,
        '探针里 table_bytes = 表的长度 × 8 字节，七个值域上逐一核对过'
        '（值域 10^9 那一格是 ' + str(want_bytes.get('1000000000')) + ' 字节）',
        lambda: with_todo((key, 'table_bytes'),
                          '探针里 table_bytes 对不上：' + '；'.join(bad))))

    want_class = record.get('expected', {}).get('classify', {})
    got_class = record.get('classify') if isinstance(record.get('classify'), dict) else {}
    bad = [('maxv=' + str(maxv) + ' 交回 ' + str(got_class.get(maxv)))
           for maxv, want in want_class.items() if got_class.get(maxv) != want]
    out.append(chk(
        not bad,
        '探针里 value_range_of 的七个值域分类都对：'
        + '、'.join(str(maxv) + '→' + str(want)
                    for maxv, want in sorted(want_class.items(), key=lambda kv: int(kv[0]))),
        lambda: with_todo((key, 'value_range_of'),
                          '探针里 value_range_of 对不上：' + '；'.join(bad))))

    want_digest = record.get('expected', {}).get('digest')
    got_digest = record.get('digest')
    out.append(chk(
        isinstance(got_digest, (list, tuple)) and len(got_digest) == 2
        and [as_int(got_digest[0]), as_int(got_digest[1])] == list(want_digest),
        '探针里 digest_of 交回 ' + str(want_digest) + ' = (n, maxv + 1)'
        '（判分自己的数据是 400 个元素、值域 12345）',
        lambda: with_todo((key, 'digest_of'),
                          '探针里 digest_of 交回 ' + short(got_digest, 24) + '，期望 '
                          + str(want_digest))))

    run_small = record.get('small_run') if isinstance(record.get('small_run'), dict) else {}
    out.append(chk(
        run_small.get('ran') is True and run_small.get('same') is True
        and run_small.get('error') is None,
        '探针里 run_at_range 在值域 12345 上真的跑了一遍，结果与判分自己排的逐字相同',
        lambda: with_todo((key, 'run_at_range'),
                          '探针里 run_at_range 那一格是 ' + short(run_small, 40)
                          + '，期望 ran=True、same=True、error=None')))

    open_small_probe = record.get('open_small') if isinstance(record.get('open_small'), dict) else {}
    out.append(chk(
        open_small_probe.get('opened') is True
        and as_int(open_small_probe.get('length')) == 1000,
        '探针里 open_table_here(999) 真的把那张表开出来了，长度交回 1000',
        lambda: with_todo((key, 'open_table_here'),
                          '探针里 open_table_here(999) 那一格是 '
                          + short(open_small_probe, 40) + '，期望 opened=True、length=1000')))
    return out


# ══ 第 5 层：单跑、行数、源码卫生 ═══════════════════════════════════════

def scan_sources():
    """扫一遍源码：BOM、连续三个反引号、两侧该一致的文件。"""
    problems = []
    targets = []
    for key in TASK_KEYS:
        targets.append(task_script(key))
    targets.append(HERE / 'tools.py')
    targets.append(HERE / 'run_tests.py')
    for path in sorted((HERE / 'probes').glob('*.py')):
        targets.append(path)
    for path in targets:
        if not path.exists():
            continue
        raw = path.read_bytes()
        if raw.startswith(b'\xef\xbb\xbf'):
            problems.append(path.name + ' 带 BOM（会 SyntaxError: invalid non-printable '
                            'character U+FEFF）')
        text = raw.decode('utf-8', errors='replace')
        if '\u0060\u0060\u0060' in text:
            problems.append(path.name + ' 里有连续三个反引号（会破坏课件代码围栏）')
        if b'\r\n' in raw:
            problems.append(path.name + ' 里是 CRLF 换行（这一套文件统一用 LF）')
    return problems


def other_side():
    """另一侧（留白版 ↔ 参考解）的目录；找不到就交回 None。

    目录名两侧都是 0013-sorting-and-divide-conquer：
      留白版  lab/0013-sorting-and-divide-conquer/
      参考解  lab/solutions/0013-sorting-and-divide-conquer/
    """
    name = HERE.name
    if HERE.parent.name == 'solutions':
        other = HERE.parent.parent / name          # 从参考解一侧看留白版
    else:
        other = HERE.parent / 'solutions' / name   # 从留白版一侧看参考解
    return other if other.exists() else None


def compare_two_sides():
    """留白版与参考解两侧：run_tests.py / tools.py / probes/*.py 必须逐字节相同。"""
    other = other_side()
    if other is None:
        return None, '另一侧不在（' + str(HERE.parent / 'solutions' / HERE.name) + '）'
    same_files = ['tools.py', 'run_tests.py'] + [
        'probes/' + p.name for p in sorted((HERE / 'probes').glob('*.py'))]
    problems = []
    for rel in same_files:
        mine = HERE / rel
        theirs = other / rel
        if not theirs.exists():
            problems.append('另一侧缺 ' + rel)
            continue
        digest_mine = hashlib.sha256(mine.read_bytes()).hexdigest()[:16]
        digest_theirs = hashlib.sha256(theirs.read_bytes()).hexdigest()[:16]
        if digest_mine != digest_theirs:
            problems.append(rel + ' 两侧不同（' + digest_mine + ' vs '
                            + digest_theirs + '）')
    return other, problems


def layer5(runs, probes):
    out = []
    for key in TASK_KEYS:
        name = TASK_SCRIPTS[key]
        code, count, lines = runs[key]
        if code is None:
            out.append((False, with_todo((key, 'merge_sort'), '找不到 ' + name)))
            continue
        text = '\n'.join(lines)
        out.append(chk(
            code == 0,
            name + ' 单跑退出码 0（输出 ' + str(count) + ' 行）',
            lambda name=name, code=code: with_todo(
                (key, 'merge_sort'),
                name + ' 单跑退出码 ' + str(code) + '，期望 0')))
        out.append(chk(
            'Traceback' not in text,
            name + ' 单跑 0 处 Traceback',
            lambda name=name, lines=lines: with_todo(
                (key, 'merge_sort'),
                name + ' 单跑里有 Traceback（最后一行：'
                + (lines[-1] if lines else '无') + '）')))
        want = EXPECT_LINES.get(name)
        # 允许 >= want：reference 版在 counting_sort 报 MemoryError 时会多打几行
        # 异常信息，而 blank 版不报（stub 不崩溃），两侧行数天然不同。
        out.append(chk(
            count >= want,
            name + ' 打印的行数不少于参考解（' + str(count) + ' ≥ ' + str(want) + ' 行）',
            lambda name=name, count=count, want=want: with_todo(
                (key, 'lines'),
                name + ' 打印了 ' + str(count) + ' 行，参考解基数是 ' + str(want)
                + ' 行（多出来的行是报错信息，不算错）')))

    # 源码行数：留白版与参考解的差只该差在「函数体里那几行代码」上。
    # 这里核的是那个差**落在预期区间里**（不能把 TODO 的注解整段删掉、也不能多塞实现）。
    other = other_side()
    if other is not None:
        bad = []
        for key in TASK_KEYS:
            name = TASK_SCRIPTS[key]
            mine = HERE / name
            theirs = other / name
            want = SOURCE_LINES.get(name)
            if not theirs.exists() or want is None:
                continue
            mine_n = len(mine.read_text(encoding='utf-8').splitlines())
            theirs_n = len(theirs.read_text(encoding='utf-8').splitlines())
            here_want = want[0] if HERE.parent.name != 'solutions' else want[1]
            if mine_n != here_want:
                bad.append(name + ' 这边 ' + str(mine_n) + ' 行，预期 ' + str(here_want)
                           + ' 行（另一侧 ' + str(theirs_n) + ' 行）')
        out.append(chk(
            not bad,
            '四个任务文件的行数与实测值一致（留白版与参考解的差只在函数体里那几行代码上）',
            lambda: with_todo(('task1', 'lines'),
                              '行数对不上：' + '；'.join(bad)
                              + '（TODO 的注解要留着；函数体只该剩一行占位 return）')))

    problems = scan_sources()
    out.append(chk(
        not problems,
        '源码卫生：四个任务文件、tools.py、run_tests.py、四个探针都没有 BOM、'
        '没有连续三个反引号、换行都是 LF',
        lambda: with_todo(('task1', 'merge_sort'), '源码卫生有问题：'
                          + '；'.join(problems))))

    other, problems = compare_two_sides()
    if other is None:
        out.append((False, with_todo(('task1', 'merge_sort'),
                                     '两侧对照没做成：' + problems)))
    else:
        out.append(chk(
            not problems,
            'run_tests.py / tools.py / probes/ 四个探针在两侧逐字节相同（sha256 前 16 位一致）',
            lambda: with_todo(('task1', 'merge_sort'),
                              '两侧该一致的文件不一致：' + '；'.join(problems))))
    return out


# ══ 主流程 ══════════════════════════════════════════════════════════════

def main():
    # 判分自己要量的那几档规模里，固定主元在**已有序**数据上要落 n 层（n 到 3200），
    # 默认上限（1000）撑不住。这一段量的是「干了多少活」，不是「会不会撞上限」——
    # 撞上限那件事是第 3 层用一个**显式钉死的小上限**去判的（那才是题目）。
    sys.setrecursionlimit(200000)

    runs = {}
    for key in TASK_KEYS:
        try:
            runs[key] = run_script(key)
        except Exception as exc:
            runs[key] = (None, 0, ['（跑不起来：' + str(exc) + '）'])

    probes = {}
    for key in TASK_KEYS:
        try:
            probes[key] = run_probe(key)
        except Exception as exc:
            probes[key] = (None, '探针起不来：' + str(exc))

    print('lab 0013 · 自动判分（手写三种排序 + 分治）')
    print('判据全是确定量：排序结果、比较次数、搬动次数、划分次数、递归深度、'
          '表的长度与字节数、倍率。')
    print('耗时那几行照打印，但判分**一条都不读秒数**。')
    print('两路证据：脚本打印的行 ＋ probes/ 里另起进程 import 学生函数的复算'
          '（种子 ' + str(PROBE_SEED) + '，规模 ' + str(list(JUDGE_SIZES)) + '）。')
    print()

    layers = {
        LAYERS[0]: layer1,
        LAYERS[1]: layer2,
        LAYERS[2]: layer3,
        LAYERS[3]: layer4,
        LAYERS[4]: layer5,
    }

    passed = 0
    failed = 0
    layers_ok = 0
    for title in LAYERS:
        print(title)
        results = layers[title](runs, probes)
        layer_ok = True
        for ok, message in results:
            if ok:
                passed += 1
                print('  PASS  ' + message)
            else:
                layer_ok = False
                failed += 1
                print('  FAIL  ' + message)
        if layer_ok:
            layers_ok += 1
        print('  → 这一层' + ('过了' if layer_ok else '还没过'))
        print()

    print('─' * 60)
    print('五层：' + str(layers_ok) + ' 层通过、' + str(len(LAYERS) - layers_ok)
          + ' 层还没过（共 ' + str(passed) + ' 条 PASS、' + str(failed) + ' 条 FAIL）')
    if failed == 0:
        print('五层全过。现在去对照 ../solutions/0013-sorting-and-divide-conquer/：')
        print('比一比那四类数据是怎么造出来的、随机主元是怎么把深度拉回去的、'
              '计数排序那张表是怎么把代价挪到值域上的，'
              '再用一句话回答「为什么这一课的判据全是次数，不是秒数」。')
        return 0
    print('卡住了先读 ../README.md 的「卡壳顺序」，再看每条 FAIL 后面点出的那一段 TODO。')
    print('判分读的就是四个脚本打印出来的行与 probes/ 里那次复算，也别改那些 print。')
    return 1


if __name__ == '__main__':
    sys.exit(main())
