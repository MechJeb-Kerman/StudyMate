"""tools.py · lab 0026 的公共工具（给好的，别改）

这里放四样东西，四个任务都从这里取：

  1. show_count(index, label, value)
     打印一行计数。格式：计数 NN <label> <value>
     例：  计数 01 石子合并 从小到大 19

  2. show_time(index, label, extra, seconds)
     打印一行耗时（六位小数）。格式：耗时 NN <label> <extra> <秒数> 秒
     例：  耗时 01 石子合并 区间DP n=200 0.012345 秒

  3. show_label(label, value) / show_pair(label, first, second)
     打印一行普通结果、或一行「一个标签带两个值」的结果。
     例：  LIS 两版长度一致 True
           石子合并 [4, 1, 2, 3] 从小 19 从大 10

  4. timed(func, *args) 与 best_of(func, *args, repeats=…)
     计时口径与第 3 课一致：前后各取一次 perf_counter、相减，中间不夹别的代码。
     timed 交回 (函数交回的值, 秒数)；best_of 跑 repeats 次、交回**最快**那一次的秒数——
     一次计时太容易被别的进程、垃圾回收、第一次跑的热身抬起来，取最快的一次才稳。

这一课的四样东西（LIS 的 DP 版与二分版、LCS 的状态表、最长回文子序列、石子合并）
与这份工具是配套的：留白版原样跑时，所有计数都会打出 0 / True / False（占位值）、
所有耗时都会打出 0.000000——那是起点，不是 bug。
"""

import time

# ══ 打印：格式就是判分接口 ══════════════════════════════════════════════


def show_count(index, label, value):
    """打印一行计数。index 是两位编号，label 是中文标签。"""
    print('计数 ' + str(index).zfill(2) + ' ' + label + ' ' + str(value))


def show_time(index, label, extra, seconds):
    """打印一行耗时（六位小数）。extra 是规模标签，例如 'n=200'。"""
    print('耗时 ' + str(index).zfill(2) + ' ' + label + ' ' + str(extra)
          + ' ' + f'{seconds:.6f}' + ' 秒')


def show_label(label, value):
    """打印一行普通结果：<label> <value>。"""
    print(str(label) + ' ' + str(value))


def show_pair(label, first, second):
    """打印一行「一个标签带两个值」：<label> <first> <second>。"""
    print(str(label) + ' ' + str(first) + ' ' + str(second))


# ══ 计时 ════════════════════════════════════════════════════════════════


def timed(func, *args):
    """跑一次并量耗时 → (函数交回的值, 秒数)。

    前后各取一次 perf_counter、相减，中间不夹别的代码。
    """
    start = time.perf_counter()
    value = func(*args)
    end = time.perf_counter()
    return value, end - start


def best_of(func, *args, repeats=1):
    """把 func(*args) 跑 repeats 次，交回**最快**那一次的秒数（一个 float）。

    每一次都单独计时（调 timed），不是把 repeats 次塞进一次计时——
    那样量到的是总时间，翻倍与倍数都看不出来了。
    """
    best = None
    for _ in range(repeats):
        _, seconds = timed(func, *args)
        if best is None or seconds < best:
            best = seconds
    return best
