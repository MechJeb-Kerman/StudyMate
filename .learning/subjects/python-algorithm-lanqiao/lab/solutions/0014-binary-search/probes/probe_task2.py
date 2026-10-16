"""判分探针 · 任务 2：另起一个进程 import 学生的 boundary 与 search 函数，
拿**判分自己的**边界数据再试一遍。

    py probes/probe_task2.py

本文件与 lab/solutions/ 那一侧逐字节相同。
"""

import importlib
import json
import os
import sys

PROBE_SEED = 2718281
SENTINEL = '::PROBE2::'
TASK = 'task2_boundary'

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def bisect_left_here(a, x):
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def try_call(func, *args):
    try:
        value = func(*args)
        return True, value
    except Exception as exc:
        return False, type(exc).__name__


def probe_boundary_data():
    """探针自己的边界数据（与标准版刻意不同）。"""
    return [
        ('空', [], 1, 'miss'),
        ('单元素命中', [3], 3, 'hit'),
        ('单元素不中', [3], 0, 'miss'),
        ('全相同命中', [4] * 5, 4, 'hit'),
        ('全相同不中', [4] * 5, 5, 'miss'),
        ('左端', [2, 4, 6, 8, 10], 2, 'hit'),
        ('右端', [2, 4, 6, 8, 10], 10, 'hit'),
        ('不存在', [2, 4, 6, 8, 10], 7, 'miss'),
    ]


def emit(record):
    sys.stdout.write(SENTINEL + json.dumps(record, ensure_ascii=False, default=str) + '\n')


def run():
    task = importlib.import_module(TASK)

    # 检查模块里的函数
    names = ['boundary_data', 'run_each', 'print_table']
    record = {'module': TASK,
              'missing': [name for name in names
                          if not callable(getattr(task, name, None))],
              'boundary': []}

    # 从 task1 引入三个搜索函数（前提是 task2 能用它们）
    try:
        t1 = importlib.import_module('task1_bsearch')
        bsearch_closed = getattr(t1, 'bsearch_closed')
        lower_bound = getattr(t1, 'lower_bound')
        contains = getattr(t1, 'contains')
    except Exception as exc:
        record['import_error'] = str(exc)
        emit(record)
        return

    seqs = probe_boundary_data()
    for name, arr, x, expect in seqs:
        want_k = bisect_left_here(arr, x)
        want_found = want_k < len(arr) and arr[want_k] == x

        row = {'name': name, 'arr': list(arr), 'x': x, 'expect': expect}

        ok_c, v_c = try_call(bsearch_closed, list(arr), x)
        ok_l, v_l = try_call(lower_bound, list(arr), x)
        ok_ct, v_ct = try_call(contains, list(arr), x)

        row['bsearch_closed'] = v_c if ok_c else 'err:' + str(v_c)
        row['lower_bound'] = v_l if ok_l else 'err:' + str(v_l)
        row['contains'] = v_ct if ok_ct else 'err:' + str(v_ct)

        row['want_closed_found'] = want_found
        row['want_lower_bound'] = want_k
        row['want_contains'] = want_found

        row['closed_ok'] = ok_c and ((expect == 'hit' and v_c >= 0 and arr[v_c] == x) or
                                     (expect == 'miss' and v_c == -1))
        row['lb_ok'] = ok_l and v_l == want_k
        row['contains_ok'] = ok_ct and v_ct == want_found

        record['boundary'].append(row)

    # 汇总
    total = len(seqs)
    closed_pass = sum(1 for r in record['boundary'] if r['closed_ok'])
    lb_pass = sum(1 for r in record['boundary'] if r['lb_ok'])
    contains_pass = sum(1 for r in record['boundary'] if r['contains_ok'])
    record['summary'] = {
        'total': total,
        'bsearch_closed_pass': closed_pass,
        'lower_bound_pass': lb_pass,
        'contains_pass': contains_pass,
    }

    emit(record)


if __name__ == '__main__':
    run()