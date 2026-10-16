"""判分探针 · 任务 4：另起一个进程 import 学生的轮数函数，
拿**判分自己的**规模再算一遍。

    py probes/probe_task4.py

本文件与 lab/solutions/ 那一侧逐字节相同。
"""

import importlib
import json
import os
import sys

PROBE_SEED = 2718281
SENTINEL = '::PROBE4::'
TASK = 'task4_rounds'

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def try_call(func, *args):
    try:
        value = func(*args)
        return True, value
    except Exception as exc:
        return False, type(exc).__name__


def max_rounds_here(n, probes=None):
    """判分自己的轮数计数（与课件写法一致）。"""
    if probes is None:
        probes = (0, n // 3, n // 2, n * 3 // 4, n - 1, n + 5)
    a = list(range(n))
    worst = 0
    for x in probes:
        lo, hi = 0, n
        c = 0
        while lo < hi:
            c += 1
            mid = (lo + hi) // 2
            if a[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        if c > worst:
            worst = c
    return worst


def emit(record):
    sys.stdout.write(SENTINEL + json.dumps(record, ensure_ascii=False, default=str) + '\n')


def run():
    task = importlib.import_module(TASK)

    names = ['max_rounds_for', 'linear_find_last', 'binary_find_last']
    record = {'module': TASK,
              'missing': [name for name in names
                          if not callable(getattr(task, name, None))],
              'rounds': {}, 'timing': {}}

    # ── 轮数验证 ─────────────────────────────────────────────────────
    probe_sizes = [10, 100, 1000, 100000]
    for n in probe_sizes:
        want = max_rounds_here(n)
        func = getattr(task, 'max_rounds_for', None)
        if callable(func):
            ok, val = try_call(func, n)
            record['rounds'][str(n)] = {
                'got': val if ok else 'err:' + str(val),
                'want': want,
                'pass': ok and val == want,
            }
        else:
            record['rounds'][str(n)] = {'got': 'missing', 'want': want, 'pass': False}

    # ── 线性和二分函数验证 ──────────────────────────────────────────
    small_arr = list(range(100))
    for fname in ('linear_find_last', 'binary_find_last'):
        func = getattr(task, fname, None)
        if callable(func):
            # 找存在的目标
            ok1, v1 = try_call(func, list(small_arr), 99)
            # 找不存在的目标
            ok2, v2 = try_call(func, list(small_arr), 100)
            record['timing'][fname] = {
                'find_exists': {'got': v1 if ok1 else 'err:' + str(v1), 'want': 99,
                               'pass': ok1 and v1 == 99},
                'find_missing': {'got': v2 if ok2 else 'err:' + str(v2), 'want': -1,
                                'pass': ok2 and v2 == -1},
            }
        else:
            record['timing'][fname] = {'missing': True}

    emit(record)


if __name__ == '__main__':
    run()