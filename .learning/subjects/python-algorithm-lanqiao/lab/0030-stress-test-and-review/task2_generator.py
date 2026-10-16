"""任务 2 · 生成器的范围要对（lab 0030 · 提交前自检）

课件那一节量出来的第二组硬事实是：**数据造得不对，等于没测。**

同一个 bug（任务 1 那个「best 从 0 起步」的候选解）、同一个对拍器、同样是 300 组数据，
只换一个生成器，抓到的组数就从 33 变成 0：

    def gen_positive(n, rng):      # 只造「至少有一个正数」的数据
        while True:
            a = [rng.randint(-9, 9) for _ in range(n)]
            if max(a) > 0:
                return a

    def gen_any(n, rng):           # 照题面造：允许全负
        return [rng.randint(-9, 9) for _ in range(n)]

课件量出来的结果：

    只造有正数的      ：300 组里抓到 bug 的有   0 组
    允许全负的       ：300 组里抓到 bug 的有  33 组

多了一句 max(a) > 0，整类「全负」数据就被挡在门外了，而本课那个 bug 恰好只住在那儿。
**这就是「测了个寂寞」**：跑了三百组，一组都没碰到问题所在。

支架（不用你写，已经给好）：两个生成器就在 tools 里（tools.gen_positive / tools.gen_any），
「跑一批数据、数抓到几组」这件事由本文件的 _count_bad / _first_bad 现算——
它们跟任务 1 的对拍器是同一个口径，所以 0 与 33 这两个数是可以逐字对上的。
真要你写的是 TODO 里那一个 run_pair：**把「跑一批、数几组」这件事抽成一个函数**，
因为它是整节最容易写歪的一段。

本任务的随机口径写死在 tools 里，别改：
    T2_SEED = 2、T2_TRIALS = 300，每组**先抽 n**（1..T1_N_HI）、再抽数组（-9..9）
两个生成器各自**从同一个种子重新开始**（random.Random(T2_SEED) 各起一个），
不然先跑的那个会把随机流吃掉一段，两个数字就没有可比性了。

接口：文件名、函数名、带 print 的行都是判分接口，别改；要写的是 TODO 那一个函数。

跑： py task2_generator.py
判： py run_tests.py
"""

import random

from tools import (T1_HI, T1_LO, T1_N_HI, T2_SEED, T2_TRIALS, cand_buggy, gen_any,
                   gen_positive, ref_brute, show_banner, show_line, values_equal)

# 占位那一格长这样：留白版打出来一眼就知道这一段还没接上。
MISSING = '（还没接上）'

# 判分接口：这一行告诉判分「每组的 n 是从哪里抽的」，别改。
GEOMETRY = (1, T1_N_HI, T1_LO, T1_HI)


def cell(value):
    """打印一格：值还是占位。"""
    return MISSING if value is None else str(value)


def count_cell(value):
    """打印「几组」那一格。"""
    return MISSING if value is None else str(value) + ' 组'


def caught_cell(value, trials=T2_TRIALS):
    """打印「<trials> 组里抓到 bug 的有 N 组」那一格。"""
    return (str(trials) + ' 组里抓到 bug 的有 ' + count_cell(value))


# ══ TODO ═══════════════════════════════════════════════════
# run_pair(gen, trials=T2_TRIALS, seed=T2_SEED, until_bad=None)
#     → {'caught': 抓到 bug 的组数, 'groups': 实际跑完的组数,
#        'first': 抓到的第一组 (组号, 数据, 候选解给的, 独立暴力给的)，一组没抓到就是 None}
#
# 每一组这样走：
#     ① n = rng.randint(1, T1_N_HI)            ← 先抽 n
#     ② a = gen(n, rng)                        ← 再由生成器抽数组（它会吃掉不同数量的随机数）
#     ③ cand_buggy(a) 与 ref_brute(a) 比：不一致就把 'caught' 加一
#        （比之前过 tools.values_equal）
#
# 三条要点：
#
#   · 用 random.Random(seed) **从种子重新开始**。「先 seed 再抽」这个次序不能少：
#     两个生成器必须从同一个随机流起点出发，0 与 33 才是可比的。
#     也不要用模块级的 random（模块级 random 的种子是别处设的，跑第二次就不一样了）。
#
#   · 抽 n 只能写 rng.randint(1, T1_N_HI)，别写死 n、也别换上限——
#     换了上限，同一个种子抽出的是另一批数据，33 就不是 33 了。
#
#   · until_bad 不是 None 时，抓到第一组就停：'first' 记下它、'groups' 记下跑了几组。
#     注意 gen 可能会交回空数组（那是占位生成器的样子），别让 a[0] 之类的写法崩掉；
#     用 cand_buggy(a) / ref_brute(a) 比较就够了，它们自己会处理空表。
def run_pair(gen, trials=T2_TRIALS, seed=T2_SEED, until_bad=None):
    return {'caught': None, 'groups': None, 'first': None}


def count_bad(gen, trials=T2_TRIALS, seed=T2_SEED):
    """照同一个口径数「这批数据抓到几组」。支架，不用改。"""
    rng = random.Random(seed)
    caught = 0
    for _ in range(trials):
        a = gen(rng.randint(1, T1_N_HI), rng)
        if not values_equal(cand_buggy(a), ref_brute(a)):
            caught += 1
    return caught


def first_bad(gen, trials=T2_TRIALS, seed=T2_SEED):
    """同一批数据里抓到的那一组（组号, 数据, 候选解给的, 独立暴力给的）。支架，不用改。"""
    rng = random.Random(seed)
    for i in range(trials):
        a = gen(rng.randint(1, T1_N_HI), rng)
        if not values_equal(cand_buggy(a), ref_brute(a)):
            return (i, a, cand_buggy(a), ref_brute(a))
    return None


if __name__ == '__main__':                      # 别改：判分读的就是下面这些行
    show_banner('0030 生成器的范围：同一个 bug、同一个对拍器、同样 300 组')

    for name, gen in (('只造有正数的', gen_positive), ('允许全负的', gen_any)):
        show_line('   ' + name,
                  str(T2_TRIALS) + ' 组里抓到 bug 的有 ' + count_cell(count_bad(gen)))

    print('   前 3 组数据（同一个种子，两个生成器各起一个）：')
    for label, gen in (('只造有正数的', gen_positive), ('允许全负的', gen_any)):
        rng = random.Random(T2_SEED)
        for i in range(3):
            a = gen(rng.randint(1, T1_N_HI), rng)
            print('      ' + label + ' 第 ' + str(i) + ' 组 n=' + str(len(a))
                  + ' 数据 ' + str(a)
                  + ' 候选解给 ' + str(cand_buggy(a))
                  + ' 暴力解给 ' + str(ref_brute(a))
                  + ' 一致吗 ' + str(values_equal(cand_buggy(a), ref_brute(a))))

    print('   换成你自己写的 run_pair 跑一遍（同一个种子、同一个生成器）：')
    mine = run_pair(gen_any)
    print('      自己的 run_pair 在「允许全负的」上：' + count_cell(mine.get('groups'))
          + ' 里抓到 ' + count_cell(mine.get('caught')))

    print('   独立暴力抓到的第一个反例:')
    first = first_bad(gen_any)
    if first is None:
        show_line('      出现在第', cell(None) + ' 组')
        show_line('      数据', cell(None))
        show_line('      候选解给', cell(None))
        show_line('      独立暴力给', cell(None))
    else:
        show_line('      出现在第', str(first[0]) + ' 组')
        show_line('      数据', str(first[1]))
        show_line('      候选解给', str(first[2]))
        show_line('      独立暴力给', str(first[3]))
