"""判分探针 · 任务 1：另起一个进程 import 学生的二分函数，拿**判分自己的**数据试一遍。

    py probes/probe_task1.py

运行的目录就是学生那份任务文件所在的目录。打回来的最后一行是带哨兵的 JSON，
判分只读那一行。这一份的期望值全都在**本文件里**现算。

本文件与 lab/solutions/ 那一侧逐字节相同：两侧都是判分的东西，不是学生的作业。
"""

import importlib
import json
import os
import sys

PROBE_SEED = 2718281          # 判分自己的种子，与学生脚本里那批数据刻意不同
SENTINEL = '::PROBE1::'
TASK = 'task1_bsearch'

# 任务文件在探针的**上一层**目录里（探针住在 probes/ 里），先把它挂上路径。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── 判分自己的数据 ─────────────────────────────────────────────────────

def randoms(n, seed):
    """判分自己的确定性整数表。"""
    x = seed
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) % 2147483648
        out.append(x % 1000000)
    return out


def cases():
    """判分要试的每一组：(名字, 数组, 目标值, 期望类型)。

    覆盖边界：空数组、单元素、两个、全相同、已有序、逆序、随机、重复值。
    """
    base = sorted(randoms(40, PROBE_SEED))
    return [
        ('空', [], 1, 'miss'),
        ('单元素命中', [5], 5, 'hit'),
        ('单元素不中', [5], 3, 'miss'),
        ('两元素命中左', [1, 2], 1, 'hit'),
        ('两元素命中右', [1, 2], 2, 'hit'),
        ('两元素不中', [1, 2], 3, 'miss'),
        ('全相同命中', [7] * 6, 7, 'hit'),
        ('全相同不中', [7] * 6, 8, 'miss'),
        ('目标在左端', base, base[0], 'hit'),
        ('目标在右端', base, base[-1], 'hit'),
        ('目标不存在(小)', base, base[0] - 1, 'miss'),
        ('目标不存在(大)', base, base[-1] + 1, 'miss'),
        ('目标不存在(中间)', base, (base[0] + base[1]) // 2, 'miss'),
        ('随机大数组', sorted(randoms(1000, PROBE_SEED + 1)), -1, 'miss'),
    ]


def want_of(arr, x, expect):
    """判分自己的标准解法（与工具函数一致）。"""
    k = bisect_left_here(arr, x)
    found = k < len(arr) and arr[k] == x
    return k, found


def bisect_left_here(a, x):
    """自己实现一个 bisect_left（不用 import bisect，探针完全独立）。"""
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def try_call(func, *args):
    """调用学生函数：成功交回 (True, 结果)，抛异常交回 (False, '异常类型')。"""
    try:
        value = func(*args)
        return True, value
    except Exception as exc:
        return False, type(exc).__name__


def emit(record):
    sys.stdout.write(SENTINEL + json.dumps(record, ensure_ascii=False, default=str) + '\n')


def run():
    task = importlib.import_module(TASK)
    names = ['bsearch_closed', 'lower_bound', 'contains']
    record = {'module': TASK,
              'missing': [name for name in names
                          if not callable(getattr(task, name, None))],
              'boundary': {}}

    # ── 边界数据逐组验证 ─────────────────────────────────────────────
    for name, arr, x, expect in cases():
        want_k, want_found = want_of(arr, x, expect)
        row = {}

        closed_func = getattr(task, 'bsearch_closed', None)
        if callable(closed_func):
            ok, val = try_call(closed_func, list(arr), x)
            if ok:
                closed_found = val >= 0 and val < len(arr) and arr[val] == x
                row['bsearch_closed'] = 'ok' if closed_found == want_found else (
                    'wrong: returned ' + str(val))
            else:
                row['bsearch_closed'] = 'err:' + str(val)
        else:
            row['bsearch_closed'] = 'missing'

        lb_func = getattr(task, 'lower_bound', None)
        if callable(lb_func):
            ok, val = try_call(lb_func, list(arr), x)
            if ok:
                row['lower_bound'] = 'ok' if val == want_k else (
                    'wrong: got ' + str(val) + ' want ' + str(want_k))
            else:
                row['lower_bound'] = 'err:' + str(val)
        else:
            row['lower_bound'] = 'missing'

        ct_func = getattr(task, 'contains', None)
        if callable(ct_func):
            ok, val = try_call(ct_func, list(arr), x)
            if ok:
                row['contains'] = 'ok' if val == want_found else (
                    'wrong: got ' + str(val))
            else:
                row['contains'] = 'err:' + str(val)
        else:
            row['contains'] = 'missing'

        record['boundary'][name] = row

    # ── 随机数组批量比对 ─────────────────────────────────────────────
    record['random_check'] = {}
    for seed_offset in range(3):
        arr = sorted(randoms(200, PROBE_SEED + seed_offset))
        targets = [arr[0], arr[len(arr) // 3], arr[len(arr) // 2],
                   arr[-1], -1, 999999, arr[0] - 1, arr[-1] + 1,
                   (arr[0] + arr[1]) // 2]
        ok_all = True
        issues = []
        for x in targets:
            want_k, want_found = want_of(arr, x, '?')
            ct_func = getattr(task, 'contains', None)
            lb_func = getattr(task, 'lower_bound', None)
            if callable(ct_func):
                _, val = try_call(ct_func, list(arr), x)
                if val != want_found:
                    ok_all = False
                    issues.append(f'contains({x})={val}')
            if callable(lb_func):
                _, val = try_call(lb_func, list(arr), x)
                if val != want_k:
                    ok_all = False
                    issues.append(f'lower_bound({x})={val} want={want_k}')
        record['random_check']['set_' + str(seed_offset)] = {
            'ok': ok_all, 'issues': issues[:5] if issues else []
        }

    emit(record)


if __name__ == '__main__':
    run()