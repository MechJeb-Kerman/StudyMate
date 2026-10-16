"""tools.py · lab 0011 的公共工具（给好的，别改）

这里放四样东西，五个任务都从这里取：

  1. make_sorted_unique(n)
     造一份**严格递增**（已排好序、没有重复值）的数组，n 个数。造法是从一个固定种子
     出发，每一步取一个 1 到 19 之间的增量叠加上去——这样既保证递增、又保证没有重复值，
     而且同一份数据每次跑出来都一样，判分才能核对确切的下标对与轮数。

  2. make_sorted_with_dups(n)
     造一份**非降序**（已排好序、允许重复）的数组，n 个数：每个位置大约三分之一是重复的。
     原地去重那一题要用它——没有重复值的数组上，去重版与没去重版看不出区别。

  3. make_unsorted(n)
     造一份**没有排序**的数组（0 到 n-1 的一个排列）。它是「有序这条前提」要用的反例。

  4. show_count(index, label, value) / show_time(index, label, extra, seconds)
     / ratio_hint(index, label, got, base)
     打印固定格式的计数行、耗时行、倍数行，判分按行读它们。
     格式： 计数 NN <label> <value>
            耗时 NN <label> <n=…> <秒数> 秒
            倍数 NN <label> <倍数>
     例：   计数 01 去重后个数 4
            耗时 02 对撞 n=16000 0.001709 秒

这一课的四个任务（两数之和、原地去重、回文判定、合并两个有序数组）与这份工具是配套的：
留白版原样跑时，所有计数都会打出 0、所有耗时都会打出 0.000000——那是起点，不是 bug。
"""

import time

# ── 确定性数据 ─────────────────────────────────────────────────────────────

_MOD = 2147483648


def _lcg(x):
    """一步线性同余（取模 2^31）。"""
    return (1103515245 * x + 12345) % _MOD


def make_sorted_unique(n):
    """n 个严格递增的整数（每个数都不一样）。"""
    x = 20261111
    out = []
    total = 0
    for _ in range(n):
        x = _lcg(x)
        total += x % 19 + 1
        out.append(total)
    return out


def make_sorted_with_dups(n):
    """n 个非降序的整数（约三分之一是重复值）。"""
    x = 55555
    out = []
    total = 0
    for i in range(n):
        x = _lcg(x)
        if i % 3 != 0:                 # 三分之二的位置沿用上一个值 → 有重复
            out.append(total)
            continue
        total += x % 5 + 1
        out.append(total)
    return out


def make_unsorted(n):
    """0 到 n-1 的一个排列：有值、但顺序是乱的（没有按非降序排好）。"""
    def key_of(i):
        return _lcg(98765 + i * 7919) % 1000

    return sorted(range(n), key=key_of)


# ── 打印：格式就是判分接口 ──────────────────────────────────────────────

def show_count(index, label, value):
    """打印一行计数。index 是两位编号，label 是中文标签。"""
    print('计数 ' + str(index).zfill(2) + ' ' + label + ' ' + str(value))


def show_time(index, label, extra, seconds):
    """打印一行耗时（六位小数）。extra 是规模标签，例如 'n=16000'。"""
    print('耗时 ' + str(index).zfill(2) + ' ' + label + ' ' + str(extra)
          + ' ' + f'{seconds:.6f}' + ' 秒')


def ratio_hint(index, label, got, base):
    """打印一行「相对基准的倍数」——任务 1 用它把翻倍的关系写成数字。"""
    if base <= 0:
        print('倍数 ' + str(index).zfill(2) + ' ' + label + ' 0.00')
        return
    print('倍数 ' + str(index).zfill(2) + ' ' + label + ' ' + f'{got / base:.2f}')


# ── 计时 ────────────────────────────────────────────────────────────────

def timed(func, *args):
    """跑一次并量耗时 → (函数交回的值, 秒数)。

    计时口径与第 3 课一致：前后各取一次 perf_counter、相减，
    中间不夹别的代码。
    """
    start = time.perf_counter()
    value = func(*args)
    end = time.perf_counter()
    return value, end - start
