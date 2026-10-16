"""判分探针 · 任务 4：另起一个进程 import 学生的函数，拿**判分自己的**值域试一遍。

    py probes/probe_task4.py

这一段的期望值全部能**算出来**（一个位置 8 字节、表长 maxv + 1、四档分类的界线），
所以判分不看学生打印的那一行：它自己换几个值域再问一遍。

探针**不在自己的进程里**去开那张 10^9 的表 —— 那一步会把这个进程带走，
而它要留着把 JSON 打完。所以从 10^9 那一档起，探针只核三件能算的事：
表的账目、分类、以及「接住报错」这个写法本身还认不认得出 999 那一档。
真去开表那件事由任务脚本与判分各自另起进程做。

本文件与 lab/solutions/ 那一侧逐字节相同。
"""

import importlib
import json
import os
import sys

PROBE_SEED = 2718281
SENTINEL = '::PROBE4::'
TASK = 'task4_counting_range'
PROBE_SMALL = 12345           # 判分自己的小值域：真的跑一遍、真的对答案
PROBE_NEAR = 10 ** 9 - 1      # 再大一点点：分类跨过 huge 的界线
PROBE_HUGE = 10 ** 9          # 与任务脚本里那一档一样大（但探针**不**在本地开它）

# 任务文件在探针的**上一层**目录里（探针住在 probes/ 里），先把它挂上路径。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def numbers(n, seed, mod):
    """判分自己的确定性整数表（模 2^31 的小发生器，与 tools 无关）。"""
    x = seed
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) % 2147483648
        out.append(x % mod)
    return out


def call(func, *args):
    try:
        return True, func(*args)
    except Exception as exc:
        return False, type(exc).__name__


def range_class_here(maxv):
    """判分自己那一份四档分类（只看表的长度，不看 n）。"""
    slots = maxv + 1
    if slots < 10 ** 4:
        return 'tiny'
    if slots < 10 ** 6:
        return 'small'
    if slots < 10 ** 9:
        return 'large'
    return 'huge'


def emit(record):
    sys.stdout.write(SENTINEL + json.dumps(record, ensure_ascii=False, default=str) + '\n')


def run():
    task = importlib.import_module(TASK)
    names = ['table_slots', 'table_bytes', 'value_range_of', 'digest_of',
             'run_at_range', 'open_table_here']
    record = {'module': TASK, 'missing': [name for name in names
                                          if not callable(getattr(task, name, None))],
              'slots': {}, 'bytes': {}, 'classify': {}, 'digest': 'missing',
              'small_run': 'missing', 'open_small': 'missing', 'expected': {}}

    # ── 表的账目：判分自己的几个值域 ────────────────────────────────────
    for maxv in (0, 999, PROBE_SMALL, 10 ** 6 - 1, 10 ** 7, PROBE_NEAR, PROBE_HUGE):
        key = str(maxv)
        func = getattr(task, 'table_slots', None)
        if callable(func):
            ok, got = call(func, maxv)
            record['slots'][key] = got if ok else 'err:' + str(got)
        func = getattr(task, 'table_bytes', None)
        if callable(func):
            ok, got = call(func, maxv)
            record['bytes'][key] = got if ok else 'err:' + str(got)
        func = getattr(task, 'value_range_of', None)
        if callable(func):
            ok, got = call(func, maxv)
            record['classify'][key] = got if ok else 'err:' + str(got)
        record['expected'].setdefault('slots', {})[key] = maxv + 1
        record['expected'].setdefault('bytes', {})[key] = (maxv + 1) * 8
        record['expected'].setdefault('classify', {})[key] = range_class_here(maxv)

    # ── 操作账目：判分自己的数据、自己的值域 ─────────────────────────────
    data = numbers(400, PROBE_SEED, PROBE_SMALL + 1)
    func = getattr(task, 'digest_of', None)
    if callable(func):
        ok, got = call(func, list(data), PROBE_SMALL)
        record['digest'] = got if ok else 'err:' + str(got)
    record['expected']['digest'] = [len(data), PROBE_SMALL + 1]

    # ── 小值域真的跑一遍：结果要与判分自己排的一模一样 ────────────────────
    func = getattr(task, 'run_at_range', None)
    if callable(func):
        ok, got = call(func, list(data), PROBE_SMALL)
        if ok and isinstance(got, (list, tuple)) and len(got) == 3:
            ran, value, error = got[0], got[1], got[2]
            same = False
            if ran:
                try:
                    same = list(value) == sorted(data)
                except TypeError:
                    same = False
            record['small_run'] = {'ran': ran, 'same': same, 'error': error}
        else:
            record['small_run'] = 'err:' + str(got) if not ok else repr(got)[:120]
    record['expected']['small_run'] = {'ran': True, 'same': True, 'error': None}

    # ── 开表那一步：小值域要开得出来（大到 10^9 那一档判分另起进程去试）────
    func = getattr(task, 'open_table_here', None)
    if callable(func):
        ok, got = call(func, 999)
        if ok and isinstance(got, (list, tuple)) and len(got) == 3:
            record['open_small'] = {'opened': got[0], 'length': got[1], 'error': got[2]}
        else:
            record['open_small'] = 'err:' + str(got) if not ok else repr(got)[:120]
    record['expected']['open_small'] = {'opened': True, 'length': 1000, 'error': None}

    emit(record)


if __name__ == '__main__':
    run()
