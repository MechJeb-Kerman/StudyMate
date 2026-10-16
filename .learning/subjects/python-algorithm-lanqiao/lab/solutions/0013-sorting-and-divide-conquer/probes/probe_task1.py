"""判分探针 · 任务 1：另起一个进程 import 学生的五个函数，拿**判分自己的**数据试一遍。

    py probes/probe_task1.py

运行的目录就是学生那份任务文件所在的目录。打回来的最后一行是带哨兵的 JSON，
判分只读那一行。这一份的期望值全都在**本文件里**现算（连 tools 都不用来算数），
所以「只写 print、不写实现」在这里拿不到分。

本文件与 lab/solutions/ 那一侧逐字节相同：两侧都是判分的东西，不是学生的作业。
"""

import importlib
import json
import os
import random
import sys

PROBE_SEED = 2718281          # 判分自己的种子，与学生脚本里那批数据刻意不同
SENTINEL = '::PROBE1::'
TASK = 'task1_sort_three'
DEEP = 200000                 # 递归上限：让归并（十几层）与快排（几十层）都跑得动

# 任务文件在探针的**上一层**目录里（探针住在 probes/ 里），先把它挂上路径。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── 判分自己的数据：三个小规模，四类形状 ────────────────────────────────

def randoms(n, seed):
    """判分自己的确定性整数表：拿一个与 tools 无关的小发生器造（模 2^31）。"""
    x = seed
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) % 2147483648
        out.append(x % 1000000)
    return out


def look_alike(n):
    """n 个只有少数几种取值的整数（重复值很多）。"""
    return [i % 3 for i in range(n)]


def cases():
    """判分要试的每一组：(名字, 数据)。边界都在里面：空数组、单个、两个。"""
    out = [
        ('empty', []),
        ('one', [7]),
        ('two', [2, 1]),
        ('same', [5, 5, 5, 5, 5]),
        ('sorted', sorted(randoms(60, PROBE_SEED))),
        ('reversed', sorted(randoms(60, PROBE_SEED + 1), reverse=True)),
        ('random', randoms(60, PROBE_SEED + 2)),
        ('dups', look_alike(80)),
        ('big', randoms(1000, PROBE_SEED + 3)),
    ]
    return out


def want_of(a):
    """唯一的标准：与 sorted(a) 逐字相同。"""
    return sorted(a)


def straight(a):
    """把一串数按大小收进一张新表——用**不用排序**的写法，做第二个独立的参照。"""
    counts = {}
    for value in a:
        counts[value] = counts.get(value, 0) + 1
    out = []
    for value in sorted(counts):
        out.extend([value] * counts[value])
    return out


def try_call(func, *args):
    """调用学生函数：成功交回 (True, 结果)，抛异常交回 (False, '异常类型: 说明')。

    返回值先归一成 list 再做比较 —— 交回元组（或其它序列）也算对，
    只要元素顺序与 sorted(a) 逐字相同。
    """
    try:
        value = func(*args)
    except Exception as exc:
        return False, type(exc).__name__ + ': ' + str(exc)
    if value is None:
        return True, None
    try:
        return True, list(value)
    except TypeError:
        return True, value


def same(got, want):
    return isinstance(got, list) and got == want


# ── 判分自己的小工具：两个数一样、一个深度公式 ──────────────────────────

def merge_depth_here(n):
    """归并排序的最大递归深度：ceil(log2 n) + 1。判分自己一层层数。"""
    if n <= 1:
        return 1
    level = [n]
    depth = 0
    while level:
        depth += 1
        nxt = []
        for size in level:
            if size > 1:
                half = size // 2
                nxt.append(half)
                nxt.append(size - half)
        level = nxt
    return depth


def merge_moves_here(n):
    """归并把元素搬进新表的次数：把每一段的长度只按切法加起来（n<=1 的不合并）。"""
    if n <= 1:
        return 0
    half = n // 2
    return n + merge_moves_here(half) + merge_moves_here(n - half)


def key_calls_here(items, key):
    """在比较里调 key 的归并版：一共调用了几次 key（判分自己数一遍）。"""
    box = {'calls': 0}

    def counted(item):
        box['calls'] += 1
        return key(item)

    def rec(part):
        if len(part) <= 1:
            return list(part)
        mid = len(part) // 2
        left = rec(part[:mid])
        right = rec(part[mid:])
        out = []
        i = 0
        j = 0
        while i < len(left) and j < len(right):
            if counted(left[i]) <= counted(right[j]):
                out.append(left[i])
                i += 1
            else:
                out.append(right[j])
                j += 1
        out.extend(left[i:])
        out.extend(right[j:])
        return out

    rec(list(items))
    return box['calls']


def emit(record):
    sys.stdout.write(SENTINEL + json.dumps(record, ensure_ascii=False, default=str) + '\n')


def run():
    sys.setrecursionlimit(DEEP)
    task = importlib.import_module(TASK)
    names = ['merge', 'merge_sort', 'quick_sort', 'quick_sort_random',
             'counting_sort', 'merge_depth', 'merge_sort_key']
    record = {'module': TASK,
              'missing': [name for name in names
                          if not callable(getattr(task, name, None))],
              'sorted': {}, 'depth': {}, 'moves': {}, 'keycalls': None}

    # ── 五个函数：每一组数据上都要求与 sorted(a) 逐字相同 ────────────────
    for name, data in cases():
        want = want_of(data)
        assert want == straight(data)          # 两个独立的参照必须一致
        row = {}
        for func_name in ('merge_sort', 'quick_sort', 'quick_sort_random', 'counting_sort'):
            func = getattr(task, func_name, None)
            if not callable(func):
                row[func_name] = 'missing'
                continue
            if func_name == 'counting_sort':
                top = max(data) if data else 0     # 空数组也要能排（值域给 0 就够）
                ok, got = try_call(func, list(data), top)
            else:
                ok, got = try_call(func, list(data))
            row[func_name] = ('ok' if same(got, want) else
                              ('err:' + str(got) if not ok else 'different'))
        # merge 单独试一次：两段已经有序时它要交回拼好的表
        merge_func = getattr(task, 'merge', None)
        if callable(merge_func):
            left = sorted(randoms(7, PROBE_SEED + 10))
            right = sorted(randoms(7, PROBE_SEED + 11))
            ok, got = try_call(merge_func, left, right)
            row['merge'] = 'ok' if same(got, sorted(left + right)) else (
                'err:' + str(got) if not ok else 'different')
        else:
            row['merge'] = 'missing'
        record['sorted'][name] = row

    # ── merge_depth：n = 1 / 2 / 9 / 1000 / 12345 上都要对 ───────────────
    depth_func = getattr(task, 'merge_depth', None)
    for n in (1, 2, 9, 1000, 12345):
        if not callable(depth_func):
            record['depth'][str(n)] = 'missing'
            continue
        ok, got = try_call(depth_func, n)
        record['depth'][str(n)] = got if isinstance(got, int) else (
            'err:' + str(got) if not ok else got)

    # ── merge_sort_key：先与 sorted(key=) 对答案，再数键被调用了几次 ─────
    items = [(i * 7919 % 101, i) for i in range(300)]
    want_pairs = sorted(items, key=lambda item: item[0])
    key_func = getattr(task, 'merge_sort_key', None)
    box = {'calls': 0}

    def counted(item):
        """交给学生函数的就是**这个**键函数：它自己记数。"""
        box['calls'] += 1
        return item[0]

    if callable(key_func):
        ok, got = try_call(key_func, list(items), counted)
        record['keycalls'] = {'answer_ok': same(got, want_pairs),
                              'calls': box['calls'] if ok else None}
    else:
        record['keycalls'] = {'answer_ok': False, 'calls': 'missing'}

    # 判分自己按同一个结构数一遍：学生在比较里调了两次键，这里也调两次
    record['keycalls_expected'] = key_calls_here(items, lambda item: item[0])

    # ── merge_depth 与 merge_sort 的搬动次数：判分自己的公式现算 ─────────
    for n in (1, 2, 3, 8, 1000, 12345):
        record['moves'][str(n)] = merge_moves_here(n)
    record['depth_expected'] = dict((str(n), merge_depth_here(n))
                                    for n in (1, 2, 9, 1000, 12345))
    emit(record)


if __name__ == '__main__':
    run()
