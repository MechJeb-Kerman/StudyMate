"""任务 2 · 生成器的范围要对（lab 0030 · 提交前自检）· 参考解

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

本机量出来的结果（种子 2、300 组、n 到 8）：

    只造有正数的      ：300 组里抓到 bug 的有   0 组
    允许全负的       ：300 组里抓到 bug 的有  33 组

多了一句 max(a) > 0，整类「全负」数据就被挡在门外了，而本课那个 bug 恰好只住在那儿。
**这就是「测了个寂寞」**：跑了三百组，一组都没碰到问题所在。

顺带一个能看出生成器差别的小现象：两个生成器都从种子 2 出发，但**第 0 组就分开了**——
「只造有正数的」那一版把第一个随机数 2 拿去当 n 之后还要反复重抽，直到抽出一个正数；
「允许全负的」那一版第 0 组恰好就是 [-7]，也就是它抓到的第一个反例（组号 0）。

支架（不用你写，已经给好）：两个生成器就在 tools 里（tools.gen_positive / tools.gen_any），
「跑一批数据、数抓到几组」这件事由本文件的 _count_bad / _first_bad 现算。
要你写的是 run_pair：**把「跑一批、数几组」抽成一个函数**，
它是整节最容易写歪的一段（种子要在循环外面定一次、n 的上限要照判分接口写）。

本任务的随机口径写死在 tools 里，别改：
    T2_SEED = 2、T2_TRIALS = 300，每组**先抽 n**（1..T1_N_HI）、再抽数组（-9..9）
两个生成器各自**从同一个种子重新开始**（random.Random(T2_SEED) 各起一个），
不然先跑的那个会把随机流吃掉一段，两个数字就没有可比性了。

接口：文件名、函数名、带 print 的行都是判分接口，别改。

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


def run_pair(gen, trials=T2_TRIALS, seed=T2_SEED, until_bad=None):
    """跑一批数据、数出「候选解与独立暴力不一致」的组数。

    三处最容易写歪的地方，这里一处都不许松：
      · 种子在循环**外面**定一次：rng = random.Random(seed)。放进循环里，
        300 组就是同一组数据重复 300 遍；
      · n 只能从 rng.randint(1, T1_N_HI) 抽，而且是**每组重抽**——写死 n 或
        换掉上限，同一个种子就抽出另一批数据，33 就不是 33 了；
      · until_bad 为真时抓到第一组就停，'groups' 记下跑了几组。
    """
    rng = random.Random(seed)
    caught = 0
    first = None
    groups = 0
    for i in range(trials):
        a = gen(rng.randint(1, T1_N_HI), rng)
        groups += 1
        if not values_equal(cand_buggy(a), ref_brute(a)):
            caught += 1
            if first is None:
                first = (i, a, cand_buggy(a), ref_brute(a))
            if until_bad:
                break
    return {'caught': caught, 'groups': groups, 'first': first}


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
