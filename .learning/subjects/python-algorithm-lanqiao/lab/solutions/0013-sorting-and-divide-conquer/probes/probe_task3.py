"""判分探针 · 任务 3：另起一个进程 import 学生的函数，拿**判分自己的**数据试那条机制。

    py probes/probe_task3.py

这一段要把「撞不撞递归上限」变成一个**确定**的对照，所以：

  · 探针把递归上限显式设成自己的一个固定值（PROBE_LIMIT = 800）；
  · 在**同一份已有序数据**上，固定主元那一路要交回 RecursionError、
    随机主元那一路要交回一个正常的深度 —— 一个爆、一个不爆，都在同一个上限下；
  · 两个规模都比 PROBE_LIMIT 深得多，所以「爆」不是差一点点，而是必然。

探针只认**交回的那个报错类型名**（不看深度是多少层 —— 那个数与机器无关但与调用位置有关）。
本文件与 lab/solutions/ 那一侧逐字节相同。
"""

import importlib
import json
import os
import sys

PROBE_SEED = 2718281
SENTINEL = '::PROBE3::'
TASK = 'task3_sorted_degrade'
PROBE_LIMIT = 800               # 判分自己钉死的递归上限（学生交回的 LIMIT 不参与判分）
SIZES = (1200, 2000)            # 已有序数据的两个规模：都远深于 PROBE_LIMIT

# 任务文件在探针的**上一层**目录里（探针住在 probes/ 里），先把它挂上路径。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ordered(n):
    """判分自己造的**已有序**数据：严格递增（与学生脚本里那一份刻意不同）。"""
    x = PROBE_SEED
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) % 2147483648
        out.append(x % 1000000)
    return sorted(out)


def call(func, *args):
    try:
        return True, func(*args)
    except Exception as exc:
        return False, type(exc).__name__


def cell(got, name):
    """从学生交回的那本字典里取一个格（不是字典就交回 None）。"""
    if isinstance(got, dict):
        return got.get(name)
    return None


def digest(got):
    """把一个个案交回的东西整理成探针统一的形状。"""
    return {'error': cell(got, 'error'), 'cmp': cell(got, 'cmp'),
            'move': cell(got, 'move'), 'jobs': cell(got, 'jobs'),
            'depth': cell(got, 'depth')}


def emit(record):
    sys.stdout.write(SENTINEL + json.dumps(record, ensure_ascii=False, default=str) + '\n')


def run():
    sys.setrecursionlimit(PROBE_LIMIT)
    task = importlib.import_module(TASK)
    names = ['degrade_fixed', 'degrade_random', 'pivot_moves']
    record = {'module': TASK, 'limit': PROBE_LIMIT, 'sizes': list(SIZES),
              'missing': [name for name in names
                          if not callable(getattr(task, name, None))],
              'fixed': {}, 'random': {}, 'moves': {}, 'expected': {}}

    for n in SIZES:
        data = ordered(n)

        # ── 固定主元：判分的期望是「交回的 error 是 RecursionError」──────────
        sys.setrecursionlimit(PROBE_LIMIT)
        func = getattr(task, 'degrade_fixed', None)
        if callable(func):
            ok, got = call(func, list(data), PROBE_LIMIT)
            record['fixed'][str(n)] = digest(got) if ok else ('call:' + str(got))
        else:
            record['fixed'][str(n)] = 'missing'

        # ── 随机主元：同一份数据、同一条上限，判分的期望是「交回的 error 是 None」──
        sys.setrecursionlimit(PROBE_LIMIT)
        func = getattr(task, 'degrade_random', None)
        if callable(func):
            ok, got = call(func, list(data), PROBE_LIMIT)
            record['random'][str(n)] = digest(got) if ok else ('call:' + str(got))
        else:
            record['random'][str(n)] = 'missing'

        # ── 搬动次数：固定主元在已有序数据上**一次都不搬**，随机主元要搬百次 ────
        func = getattr(task, 'pivot_moves', None)
        if callable(func):
            sys.setrecursionlimit(PROBE_LIMIT)
            ok_a, got_a = call(func, list(data), 'fixed')
            sys.setrecursionlimit(PROBE_LIMIT)
            ok_b, got_b = call(func, list(data), 'random')
            record['moves'][str(n)] = {'fixed': got_a if ok_a else 'call:' + str(got_a),
                                       'random': got_b if ok_b else 'call:' + str(got_b)}
        else:
            record['moves'][str(n)] = 'missing'

    # ── 判分自己的期望（都是能算出来的结构量）──────────────────────────────
    record['expected'] = {
        'fixed_error': dict((str(n), 'RecursionError') for n in SIZES),
        'random_error': dict((str(n), None) for n in SIZES),
        # 完整跑完是 n(n-1)/2；撞上限时会提前停下，所以这一格是**上界**
        'fixed_cmp_no_more_than': dict((str(n), n * (n - 1) // 2) for n in SIZES),
        'fixed_move': dict((str(n), 0) for n in SIZES),
        'random_moves_at_least': dict((str(n), 2 * (n - 1)) for n in SIZES),
    }
    emit(record)


if __name__ == '__main__':
    run()
