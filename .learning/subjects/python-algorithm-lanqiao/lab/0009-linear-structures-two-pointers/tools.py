"""tools.py · lab 0009 的公共工具（给好的，别改）

这里放三样东西，六个任务都从这里取：

  1. make_positive_array(n) / make_mixed_array(n)
     两份**确定性**的数组。不用 random 是有意的：同一份数据每次跑出来都一样，
     判分才能核对确切的答案，你自己跑两次也能对照。
     make_positive_array 造 n 个 1 到 100 之间的正整数。
     make_mixed_array   造 n 个 -30 到 30 之间的整数（含负数与 0）。

  2. show_count(index, label, value)
     打印一行固定格式的计数，判分按行读它。
     格式： 计数 NN <label> <value>
     例：   计数 01 暴力 9

  3. show_time(index, label, n, seconds) / ratio_hint(index, label, got, base)
     打印耗时与倍数。任务 3、4、5 用它们把「三种走法的差距」变成数字。
     格式： 耗时 NN <label> n=<n> <秒数> 秒
            倍数 NN <label> <倍数>

这两份数据与这一课的 lab 是配套的：留白版原样跑时，所有计数都会打出 0，
所有耗时都会打出 0.000000——那是起点，不是 bug。
"""

# ── 数组生成：线性同余，写死种子，每台机器上跑出来都一样 ────────────────

def _next(x):
    """一步线性同余（取模 2^31）。"""
    return (1103515245 * x + 12345) % 2147483648


def make_positive_array(n):
    """n 个 1 到 100 之间的正整数（确定性）。"""
    x = 20261005
    out = []
    for _ in range(n):
        x = _next(x)
        out.append(x % 100 + 1)
    return out


def make_mixed_array(n):
    """n 个 -30 到 30 之间的整数，含负数与 0（确定性）。"""
    x = 12345
    out = []
    for _ in range(n):
        x = _next(x)
        out.append(x % 61 - 30)
    return out


# ── 打印：格式就是判分接口 ──────────────────────────────────────────────

def show_count(index, label, value):
    """打印一行计数。index 是两位编号，label 是中文标签。"""
    print('计数 ' + str(index).zfill(2) + ' ' + label + ' ' + str(value))


def show_time(index, label, n, seconds):
    """打印一行耗时（六位小数）。"""
    print('耗时 ' + str(index).zfill(2) + ' ' + label + ' n=' + str(n)
          + ' ' + f'{seconds:.6f}' + ' 秒')


def ratio_hint(index, label, got, base):
    """打印一行「相对基准的倍数」——任务 5 用它把翻倍、四倍的关系写成数字。

    base 是同一列上一行的秒数（基准），got 是这一行的秒数。
    base 太小或为 0 时打 0.00，免得除出个没意义的大数。
    """
    if base <= 0:
        print('倍数 ' + str(index).zfill(2) + ' ' + label + ' 0.00')
        return
    print('倍数 ' + str(index).zfill(2) + ' ' + label + ' ' + f'{got / base:.2f}')


def timed(func, *args):
    """跑一次并量耗时 → (函数交回的值, 秒数)。

    计时口径与第 3 课一致：前后各取一次 perf_counter、相减，
    中间不夹别的代码。
    """
    import time
    start = time.perf_counter()
    value = func(*args)
    end = time.perf_counter()
    return value, end - start
