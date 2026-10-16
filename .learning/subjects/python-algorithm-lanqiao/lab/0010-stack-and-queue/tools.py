"""tools.py · lab 0010 的公共工具（给好的，别改）

这里放四样东西，五个任务都从这里取：

  1. make_perm(n) / make_mixed(n)
     两份**确定性**的数据。不用 random 是有意的：同一份数据每次跑出来都一样，
     判分才能核对确切的答案，你自己跑两次也能对照。
     make_perm  造 0 到 n-1 的一个打乱顺序（每个数正好出现一次），
                用它当数组时可以一眼看出「哪个下标还在窗口里」。
     make_mixed 造 n 个 -50 到 49 之间的整数（有正有负、没有规律）。

  2. shuffle(seed, n) / rand_int(seed)
     每一步都重新给种子，所以整串随机操作**每次运行都一样**：同一段代码跑两次
     得到同一个结果，判分才能核对「你的结构与参照模型是不是一直一致」。
     这是第 2 课那条「可重复」的用法：判分要的是可复现，不是真随机。

  3. show_count(index, label, value) / show_time(index, label, extra, seconds)
     打印固定格式的计数行与耗时行，判分按行读它们。
     格式： 计数 NN <label> <value>
            耗时 NN <label> <n=… 或 k=…> <秒数> 秒
     例：   计数 01 栈 出栈 300
            耗时 01 popleft k=200000 0.013456 秒

  4. timed(func, *args)
     跑一次并量耗时 → (函数交回的值, 秒数)。计时口径与第 3 课一致：
     前后各取一次 perf_counter、相减，中间不夹别的代码。

这一课的两个结构（栈与队列）、四种题型（括号匹配、表达式求值、单调栈、
单调队列）与这份工具是配套的：留白版原样跑时，所有计数都会打出 0、
所有耗时都会打出 0.000000——那是起点，不是 bug。
"""

import time

# ── 确定性数据与确定性随机 ────────────────────────────────────────────────

_MOD = 2147483648


def _lcg(x):
    """一步线性同余（取模 2^31）。"""
    return (1103515245 * x + 12345) % _MOD


def rand_int(seed):
    """按种子给一个 0 到 999 之间的整数。同一种子永远给同一个数。"""
    return _lcg(seed) % 1000


def shuffle(seed, n):
    """把 0 到 n-1 打乱成一份**每次运行都一样**的顺序。

    写法是给每个位置现取一个随机数当排序关键字（第 5 课学过 sorted 与 key 指定的
    键函数，这里的键函数用 def 写），排完把顺序取出来。
    """
    def key_of(i):
        return rand_int(seed + i * 7919)

    order = sorted(range(n), key=key_of)
    return order


def make_perm(n):
    """0 到 n-1 的一个确定性排列：每个数正好出现一次。"""
    return shuffle(20261110, n)


def make_mixed(n):
    """n 个 -50 到 49 之间的整数（确定性）：有正有负、没有规律。"""
    x = 987654321
    out = []
    for _ in range(n):
        x = _lcg(x)
        out.append(x % 100 - 50)
    return out


# ── 打印：格式就是判分接口 ──────────────────────────────────────────────

def show_count(index, label, value):
    """打印一行计数。index 是两位编号，label 是中文标签。"""
    print('计数 ' + str(index).zfill(2) + ' ' + label + ' ' + str(value))


def show_time(index, label, extra, seconds):
    """打印一行耗时（六位小数）。extra 是规模标签，例如 'k=200000'。"""
    print('耗时 ' + str(index).zfill(2) + ' ' + label + ' ' + str(extra)
          + ' ' + f'{seconds:.6f}' + ' 秒')


def ratio_hint(index, label, got, base):
    """打印一行「相对基准的倍数」——任务 2、5 用它把差距写成数字。

    base 是同一列上一行的秒数（基准），got 是这一行的秒数。
    base 太小或为 0 时打 0.00，免得除出个没意义的大数。
    """
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
