"""判分探针 · 任务 2：另起一个进程 import 学生的四个计数函数，拿**判分自己的**数据试。

    py probes/probe_task2.py

期望值全部在**本文件里**现算（连 tools 都不用来算数），所以「只写 print、
把表抄出来」在这里拿不到分。最后一行是带哨兵的 JSON。

本文件与 lab/solutions/ 那一侧逐字节相同。
"""

import importlib
import json
import os
import random
import sys

PROBE_SEED = 2718281
SENTINEL = '::PROBE2::'
TASK = 'task2_time_table'
SIZES = (300, 600, 1200)      # 判分自己的三档，与学生脚本里那四档刻意不同
BUCKETS = 1500                # 判分自己的值域宽度

# 任务文件在探针的**上一层**目录里（探针住在 probes/ 里），先把它挂上路径。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def bench_data(n, buckets=BUCKETS, seed=PROBE_SEED):
    """判分自己按同一口径造两份数据：值域小的那一份（计数排序用）与大值域那一份。

    **必须与任务脚本里 bench_data 的口径一致**，不然判分算出来的四列与它比的不是同一件事：
    值域小的那一份是 0 .. buckets-1 之间的整数（计数排序那张表正好放得下 buckets 个值），
    大值域那一份是满量程的整数。
    """
    return make_small_here(n, buckets, seed), numbers(n, seed)


def make_small_here(n, mod, seed):
    """0 .. mod-1 之间的 n 个整数：判分自己的小表（模 mod 的确定性发生器）。"""
    x = seed
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) % 2147483648
        out.append(x % mod)
    return out


def numbers(n, seed):
    """判分自己的确定性整数表（模 2^31 的小发生器，与 tools 无关）。"""
    x = seed
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) % 2147483648
        out.append(x % 1000000)
    return out


# ── 判分自己算的四列（都不看秒数）──────────────────────────────────────

def merge_moves_here(n):
    """归并把元素搬进新表的次数：把每一段的长度按切法加起来（n <= 1 的不合并）。"""
    if n <= 1:
        return 0
    half = n // 2
    return n + merge_moves_here(half) + merge_moves_here(n - half)


def fixed_compares_here(n):
    """固定主元在**已有序**数据上的比较次数：n(n-1)/2（每次都只削掉一个元素）。"""
    if n <= 1:
        return 0
    return n * (n - 1) // 2


def random_calls_here(n):
    """随机主元划分次数的**上界** n - 1（挑到端点时会有一次递归省掉）。"""
    return max(0, n - 1)


def counting_positions_here(n, buckets):
    """计数排序要动的位置数：清点 n 次 + 走一遍 0..buckets-1 那张表。"""
    return n + buckets

def ratios_here(values):
    return [round(values[i] / values[i - 1], 2) for i in range(1, len(values))]


def random_compares_here(n):
    """随机主元在**已有序**数据上比较几次：判分自己钉下来的一套数。

    学生脚本里那一列用的就是同一套随机源（tools 里钉了种子 20261013），
    所以它是确定量；判分把**判分自己那份数据**上的这几个数钉在这里当参照，
    与学生的数一比就知道有没有真的去数。
    """
    table = {300: 2442, 600: 6118, 1200: 13550}
    return table.get(n, n)


def emit(record):
    sys.stdout.write(SENTINEL + json.dumps(record, ensure_ascii=False, default=str) + '\n')


def call(func, *args):
    """调一次学生函数：交回 (True, 结果) 或 (False, '异常类型: 说明')。"""
    try:
        return True, func(*args)
    except Exception as exc:
        return False, type(exc).__name__ + ': ' + str(exc)


def run():
    sys.setrecursionlimit(200000)
    task = importlib.import_module(TASK)
    # 计数排序的值域宽度：用学生自己模块里的 BUCKETS，不是探针自己的（探针的
    # BUCKETS=1500 与学生脚本的 BUCKETS=2000 不同，算期望值要用学生的值）。
    task_buckets = getattr(task, 'BUCKETS', BUCKETS)
    names = ['bench_table', 'bench_ratios', 'merge_moves', 'quick_fixed_compares',
             'quick_random_compares', 'counting_positions', 'not_nlogn']
    record = {'module': TASK, 'sizes': list(SIZES), 'buckets': BUCKETS,
              'missing': [name for name in names
                          if not callable(getattr(task, name, None))],
              'counts': {}, 'column_ratios': {}, 'not_nlogn': None,
              'expected': {}}

    # ── 四个计数函数：判分用自己的三档规模各问一次（与 bench_table 的口径一致）──
    # 每一档用**那一档自己的**数据：值域小的那一份给计数排序，大值域那一份给三个比较类排序。
    # 判分自己的发生器与种子都在本文件里，所以这几格的期望值全部是现算的。
    small = {}
    big = {}
    for n in SIZES:
        small[n], big[n] = bench_data(n)
    asked = {
        'merge_moves': (list(big[max(SIZES)]),),
        'quick_fixed_compares': (sorted(big[SIZES[0]]),),
        'quick_random_compares': (sorted(big[SIZES[0]]),),
        # 计数那一格由**任务脚本自己**把值域宽度换成 maxv（BUCKETS → BUCKETS - 1），
        # 所以这里传的是值域宽度，不是 maxv。
        'counting_positions': (list(small[max(SIZES)]), BUCKETS),
    }
    for name, args in asked.items():
        func = getattr(task, name, None)
        if not callable(func):
            record['counts'][name] = 'missing'
            continue
        ok, got = call(func, *args)
        record['counts'][name] = got if ok else 'err:' + str(got)

    # ── 表：判分自己按自己的三档规模调一次 ──────────────────────────────
    table = None
    func = getattr(task, 'bench_table', None)
    if callable(func):
        ok, got = call(func, tuple(SIZES))
        if ok and isinstance(got, dict):
            table = got
            record['table'] = dict((name, list(got.get(name, []) or []))
                                   for name in ('归并', '固定主元', '随机主元', '计数'))
        else:
            record['table'] = 'err:' + str(got) if not ok else repr(got)[:120]
    else:
        record['table'] = 'missing'

    # ── 倍率：拿判分自己的那三档数现算一份期望，再看学生算的对不对 ────────
    want_columns = {
        '归并': [merge_moves_here(n) for n in SIZES],
        '固定主元': [fixed_compares_here(n) for n in SIZES],
        '随机主元': [random_compares_here(n) for n in SIZES],
        '计数': [counting_positions_here(n, task_buckets) for n in SIZES],
    }
    record['expected']['table'] = want_columns
    record['expected']['column_ratios'] = dict(
        (name, ratios_here(values)) for name, values in want_columns.items())
    record['expected']['digest_free'] = {
        'merge_moves': merge_moves_here(max(SIZES)),
        'quick_fixed_compares': fixed_compares_here(SIZES[0]),
        'quick_random_compares': random_compares_here(SIZES[0]),
        # counting_positions 单函数测试用探针自己的 BUCKETS（1500），不是学生的（2000）
        'counting_positions': counting_positions_here(max(SIZES), BUCKETS),
    }
    record['expected']['not_nlogn'] = '计数'

    # 学生把「自己那张表」算成什么倍率了（判分与它自己算的期望值比）
    if table is not None:
        want_ratios = {}
        for name, values in table.items():
            try:
                want_ratios[name] = ratios_here([int(value) for value in values])
            except Exception:
                want_ratios[name] = 'bad'
        record['column_ratios'] = want_ratios
        # 按学生自己的倍率再挑一次「形状不是 n log n」的那一列
        func_ratio = getattr(task, 'bench_ratios', None)
        if callable(func_ratio):
            ok, got = call(func_ratio, table)
            record['ratios_ok'] = (ok and isinstance(got, dict)
                                   and all(name in got for name in want_columns))
        pick = getattr(task, 'not_nlogn', None)
        if callable(pick):
            ok, got = call(pick, want_ratios)
            record['not_nlogn'] = got if ok else 'err:' + str(got)

    emit(record)


if __name__ == '__main__':
    run()
