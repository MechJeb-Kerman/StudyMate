"""tools.py · lab 0022 的公共工具（给好的，别改）

这里放三样东西，四个任务都从这里取：

  1. make_woods(n, max_len) — 造一份确定性的木头长度数组，种子固定，结果可复现

  2. make_river_stones(river_len, n) — 造一份确定性的石头位置数组，已排序、含两端

  3. show_count(index, label, value) / show_time(index, label, extra, seconds)
     — 打印固定格式的计数行和耗时行，判分按行读它们。
     格式： 计数 NN <label> <value>
            耗时 NN <label> <n=…> <秒数> 秒

这一课的四个任务（木材切割、跳石头、暴力验算、单调性破坏）与这份工具是配套的：
留白版原样跑时，所有计数都会打出 0、所有耗时都会打出 0.000000——那是起点，不是 bug。
"""

import time


# ── 确定性数据 ─────────────────────────────────────────────────────────────

_MOD = 2147483648


def _lcg(x):
    """一步线性同余（取模 2^31）。"""
    return (1103515245 * x + 12345) % _MOD


def make_woods(n, max_len=100):
    """n 根木头，每根长度在 [1, max_len] 之间，确定性序列。"""
    x = 20261111
    out = []
    for _ in range(n):
        x = _lcg(x)
        out.append(x % max_len + 1)
    return out


def make_river_stones(river_len, n):
    """n 块石头的位置（已排序），终点是 river_len，确定性序列。"""
    x = 7777777
    stones = set()
    for _ in range(n * 2):                 # 多造一些保证够 n 个
        x = _lcg(x)
        pos = x % (river_len - 1) + 1       # (0, river_len) 之间
        stones.add(pos)
        if len(stones) >= n:
            break
    return sorted(stones)


# ── 打印：格式就是判分接口 ──────────────────────────────────────────────

def show_count(index, label, value):
    """打印一行计数。index 是两位编号，label 是中文标签。"""
    print('计数 ' + str(index).zfill(2) + ' ' + label + ' ' + str(value))


def show_time(index, label, extra, seconds):
    """打印一行耗时（六位小数）。extra 是规模标签，例如 'n=1000'。"""
    print('耗时 ' + str(index).zfill(2) + ' ' + label + ' ' + str(extra)
          + ' ' + f'{seconds:.6f}' + ' 秒')


# ── 计时 ────────────────────────────────────────────────────────────────

def timed(func, *args):
    """跑一次并量耗时 → (函数交回的值, 秒数)。"""
    start = time.perf_counter()
    value = func(*args)
    end = time.perf_counter()
    return value, end - start