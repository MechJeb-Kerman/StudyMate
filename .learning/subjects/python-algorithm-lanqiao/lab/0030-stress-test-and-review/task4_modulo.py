"""任务 4 · 取模：小数据上看不出来（lab 0030 · 提交前自检）

课件那一节量出来的第四组硬事实是：**取模错在小数据上看不出。**

题面写「答案对 10^9 + 7 取模」的时候，最常见的错法是**中途忘了取**。两版斐波那契：

    def fib_nomod(n):                   def fib_mod(n):
        a, b = 0, 1                         a, b = 0, 1
        for _ in range(n):                  for _ in range(n):
            a, b = b, a + b                     a, b = b, (a + b) % MOD
        return a                            return a

课件量出来的表：

    MOD = 1,000,000,007
    n        不取模（末 14 位）        取模后的值      两者相等吗
       10      …            55               55   True
       30      …        832040           832040   True
       50      …   12586269025        586268941   False
      100      …48179261915075        687995182   False
     1000      …95166849228875        517691607   False
    10000      …10059947366875        271496360   False
    不取模在 n = 10000 时的位数: 2090 位

**n <= 30 时两版一模一样，n = 50 开始分道扬镳。** 你拿小样例试，永远试不出来。

那分道扬镳的点到底在哪？第 45 个斐波那契数是 1,134,903,170——它第一次超过 10^9 + 7。
所以**第一个分家的 n 是 45**：n = 44 还相等，n = 45 就不等了。
这个数不是背下来的，是循环找出来的（本任务第一个 TODO 就干这件事）。

Python 的整数不会溢出（这是它的好处），所以「忘了取模」在 Python 里带来的**不是报错，
而是静默地交出一个错误的数**——比 C++ 里溢出成一个负数更难发现。

还要量一件事：**不取模那一版在 n = 10000 时是多少位**。答案是 2090 位——
而取模之后永远是 10 位以内。这就是「小数据看不出」的量化说法：
两版在 n = 30 上逐字相同，在 n = 10000 上差了 2080 位。

接口：文件名、函数名、带 print 的行都是判分接口，别改；要写的是四个 TODO。

跑： py task4_modulo.py
判： py run_tests.py
"""

from tools import (MOD, T4_BIG, T4_ROWS, T4_TAIL, fib_count, fib_mod, fib_nomod,
                   show_banner, show_line)

# 占位那一格长这样：留白版打出来一眼就知道这一段还没接上。
MISSING = '（还没接上）'


def cell(value):
    """打印一格：值还是占位。"""
    return MISSING if value is None else str(value)


# ══ TODO 1 ═════════════════════════════════════════════════
# first_diff(lo=1, hi=200) → 第一个让 fib_nomod(n) != fib_mod(n) 的 n；到 hi 都没找到就交回 None。
#
# 循环 n 从 lo 到 hi（含 hi），逐个比两版：
#
#     if fib_nomod(n) != fib_mod(n):
#         return n
#     return None
#
# 判分要把 45 这个数单独核对一遍——它不是背下来的，是这个循环找出来的：
# n = 44 两版还相等，n = 45 就不等了（第 45 个数 1134903170 第一次超过 MOD）。
def first_diff(lo=1, hi=200):
    return None


# ══ TODO 2 ═════════════════════════════════════════════════
# tail14(x) → 不取模那一版**末 14 位**的字符串（课件那一列就是这么打的）。
#
#     text = str(x)
#     return text[-T4_TAIL:]        ← 比 14 位短就原样交回
#
# x 是 None 时交回 None（空数据那一档要跟别的行长得一样，不能报错）。
# 末 14 位只是为了让一列里塞得下一个几千位的数；**位数**那一格另算，见 TODO 4。
def tail14(x):
    return None


# ══ TODO 3 ═════════════════════════════════════════════════
# sample_rows(ns=T4_ROWS) → [(n, 不取模的末 14 位, 取模的值, n 处两版相等吗), …]
#
# 一行一个 n，四个格子照上面那张表的顺序来：
#
#     for n in ns:
#         x, y = fib_nomod(n), fib_mod(n)
#         rows.append((n, tail14(x), y, x == y))
#
# 第四格必须是**布尔值**（True/False），不是 1/0、也不是 'True' 这种字符串：
# 「两者相等吗」这一列就是这一节的全部信息量。
def sample_rows(ns=T4_ROWS):
    return []


# ══ TODO 4 ═════════════════════════════════════════════════
# big_digits(n=T4_BIG) → 不取模那一版在 n 处的**十进制位数**。
#
# 一句话就够，但**要从 fib_nomod 上取**：
#
#     return len(str(fib_nomod(n)))
#
# 别写成 len(str(fib_mod(n)))：那样交回的是取模**之后**的位数（永远不到 10 位）。
# 这一格是「小数据看不出」的量化说法：n = 10000 时它是 2090 位，
# 而取模之后那一列全是 10 位以内——两版差了 2080 位，在 n = 30 上却逐字相同。
#
# tools.fib_count(n) 是**同一个口径的另一个写法**（一边递推一边数位数）。
# 判分拿它当另一个实现来对照：两边的数必须一样。
def big_digits(n=T4_BIG):
    return None


# 这两段是「另一个口径」的现算：300 组随机 n，看两版有没有不相等。
# 种子与区间写死在这里，是判分接口的一部分——判分自己拿同一批 n 另算一遍。
RANDY_SEED = 3
RANDY_TRIALS = 300
RANDY_LO = 21
RANDY_HI = 120


def random_bad(seed=RANDY_SEED, trials=RANDY_TRIALS, lo=RANDY_LO, hi=RANDY_HI):
    """这批随机 n 里两版不相等的组数。"""
    import random
    rng = random.Random(seed)
    bad = 0
    for _ in range(trials):
        n = rng.randint(lo, hi)
        if fib_nomod(n) != fib_mod(n):
            bad += 1
    return bad


def random_first(seed=RANDY_SEED, trials=RANDY_TRIALS, lo=RANDY_LO, hi=RANDY_HI):
    """同一批随机 n 里第一个不相等的 n；一组都没有就 None。"""
    import random
    rng = random.Random(seed)
    for _ in range(trials):
        n = rng.randint(lo, hi)
        if fib_nomod(n) != fib_mod(n):
            return n
    return None


def gap_cell(n=T4_BIG):
    """「两版差了 N 位」那一格：不取模的位数减掉取模之后最多可能的 10 位。"""
    digits = big_digits(n)
    return None if digits is None else digits - 10


if __name__ == '__main__':                      # 别改：判分读的就是下面这些行
    show_banner('0030 取模：小数据上看不出来')
    show_line('   MOD =', format(MOD, ','))

    print('   n        不取模（末 14 位）        取模后的值      两者相等吗')
    # 一行一个 n，**行数固定**：还没接上时每一格是占位，接上之后就是真值。
    # 行数不许随进度变——判分读的就是这几行，留白版与参考解的打印行数要一致。
    rows = {row[0]: row for row in sample_rows()}
    for n in T4_ROWS:
        row = rows.get(n)
        tail, value, same = (row[1], row[2], row[3]) if row else (None, None, None)
        print('   ' + str(n).rjust(5) + '      …' + cell(tail).rjust(T4_TAIL)
              + '   ' + cell(value).rjust(T4_TAIL) + '   ' + cell(same))

    show_line('   → 第一个分家的 n（两版从这里开始不等）:', cell(first_diff()))

    bad = random_bad()
    print('   300 组随机 n（种子 ' + str(RANDY_SEED) + '，n 在 ' + str(RANDY_LO) + '..'
          + str(RANDY_HI) + ' 之间）：')
    show_line('      其中两版不相等的组数:', cell(bad))
    show_line('      第一组不相等的 n:', cell(random_first()))

    show_line('   不取模在 n = ' + str(T4_BIG) + ' 时的位数:', cell(big_digits()) + ' 位')
    show_line('   取模后的值最多 10 位——两版差了',
              cell(gap_cell()) + ' 位，在 n = 30 上却逐字相同')
