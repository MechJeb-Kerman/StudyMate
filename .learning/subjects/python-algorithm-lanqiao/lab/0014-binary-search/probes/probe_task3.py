"""判分探针 · 任务 3：另起一个进程 import 学生的 bug 函数，拿**判分自己的**
边界数据跑一次，验证每种错法在哪几组数据上暴露。

    py probes/probe_task3.py

本文件与 lab/solutions/ 那一侧逐字节相同。
"""

import importlib
import json
import os
import sys

PROBE_SEED = 2718281
SENTINEL = '::PROBE3::'
TASK = 'task3_debug'

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


def probe_data():
    """探针自己的边界数据。"""
    return [
        ('空', [], 1, 'miss'),
        ('单元素命中', [5], 5, 'hit'),
        ('单元素不中', [5], 3, 'miss'),
        ('全相同命中', [7] * 6, 7, 'hit'),
        ('全相同不中', [7] * 6, 8, 'miss'),
        ('目标在左端', [1, 3, 5, 7, 9], 1, 'hit'),
        ('目标在右端', [1, 3, 5, 7, 9], 9, 'hit'),
        ('目标不存在', [1, 3, 5, 7, 9], 4, 'miss'),
    ]


def emit(record):
    sys.stdout.write(SENTINEL + json.dumps(record, ensure_ascii=False, default=str) + '\n')


def bug_exposed(bug_func, bug_name, arr, x, expect, correct_contains):
    """判断错版是否暴露：结果与 correct_contains 不一致，或死循环。"""
    ok, val = try_call(bug_func, list(arr), x)
    if not ok:
        return True, 'error:' + str(val)
    # 检查死循环指示（返回带「死循环」的字符串）
    if isinstance(val, tuple) and len(val) >= 2:
        if isinstance(val[0], str) and '死循环' in val[0]:
            return True, 'dead_loop'
    if isinstance(val, str) and '死循环' in val:
        return True, 'dead_loop'

    if bug_name == 'bug_no_check':
        # 错法三：返回插入位置但不验证存在性
        # 暴露判断：对 miss 数据，返回的索引（有效或越界）不能直接用作「找到」
        # 对 hit 数据，返回的索引应指向 x
        if isinstance(val, int):
            if expect == 'hit':
                bug_found = (0 <= val < len(arr) and arr[val] == x)
                return bug_found != correct_contains, f'bug_val={val} correct_found={correct_contains}'
            else:
                # miss 数据上，bug_no_check 返回插入位置（一个有效 int）
                # 但 arr[val] != x —— 这是暴露
                if 0 <= val < len(arr):
                    return arr[val] != x, f'bug_val={val} arr[val]={"?" if val>=len(arr) else arr[val]} x={x}'
                else:
                    # 越界：直接暴露
                    return True, f'bug_val={val} OOB len={len(arr)}'
        return True, f'unexpected_return={val}'

    # 对 bug_lose_last 和 bug_no_shrink，判断结果是否等于正确 found
    if isinstance(val, int):
        if val == -1:
            bug_found = False
        elif 0 <= val < len(arr):
            bug_found = arr[val] == x
        else:
            bug_found = False  # 越界等
        return bug_found != correct_contains, f'bug_val={val} correct_found={correct_contains}'
    return True, f'unexpected_return={val}'


def run():
    task = importlib.import_module(TASK)

    # 从 task1 导入正确的 contains
    try:
        t1 = importlib.import_module('task1_bsearch')
        correct_contains_func = getattr(t1, 'contains')
    except Exception as exc:
        emit({'error': 'cannot_import_task1: ' + str(exc)})
        return

    bug_names = ['bug_no_shrink', 'bug_lose_last', 'bug_no_check']
    record = {'module': TASK,
              'missing': [name for name in bug_names
                          if not callable(getattr(task, name, None))],
              'results': {}, 'explanations': {}}

    # 检查 CONCISE_EXPLANATIONS
    expl = getattr(task, 'CONCISE_EXPLANATIONS', {})
    if isinstance(expl, dict):
        record['explanations'] = dict((k, str(v)[:120]) for k, v in expl.items())

    seqs = probe_data()
    for bname in bug_names:
        bfunc = getattr(task, bname, None)
        if not callable(bfunc):
            continue

        exposures = []
        for name, arr, x, expect in seqs:
            _, correct_val = try_call(correct_contains_func, list(arr), x)
            exposed, detail = bug_exposed(bfunc, bname, arr, x, expect, correct_val)
            if exposed:
                exposures.append({'data': name, 'x': x, 'detail': detail})

        record['results'][bname] = {
            'exposed_on': [e['data'] for e in exposures],
            'details': exposures,
        }

    # 记录判分自己的期望暴露情况
    record['expected_exposure'] = {
        'bug_no_shrink': ['空', '单元素命中', '单元素不中', '全相同命中',
                          '全相同不中', '目标在左端', '目标在右端', '目标不存在'],
        'bug_lose_last': ['目标在左端', '目标在右端'],
        'bug_no_check': ['单元素不中', '全相同不中', '目标不存在'],
    }

    emit(record)


if __name__ == '__main__':
    run()