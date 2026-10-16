"""任务 1 · 独立参考解对拍（lab 0030 · 提交前自检）· 参考解

课件那一节量出来的第一组硬事实是：**对拍器不是护身符。**

候选解是第一课就写过的最大子段和，但 best 从 0 起步：

    best = cur = 0
    for x in a:
        cur = max(0, cur + x)
        best = max(best, cur)
    return best

这个 bug 只在「全都不是正数」的数据上出现：cur 被 max(0, ...) 按回 0，best 也就一直是 0，
于是交回 0，而正确答案是那个最大的负数。题目只保证「子段非空」时，`[-7]` 的答案就是 -7。

现在做对拍。三把尺子：

    ref_same_idea —— 照候选解**同一个错思路**再写一遍，只是行文不同（它也在 0 起步）；
    ref_brute     —— 独立参考解：枚举所有子段一个不漏；
    ref_dc        —— 独立参考解：分治（左半 / 右半 / 跨中点）。

本机量出来的结果（种子 1、500 组、n 到 8、取值 -9..9）：

    与「同一个思路的参考解」对拍，不一致的:   0 组
    与「独立暴力解」对拍，不一致的        :  58 组
    与「独立分治解」对拍，不一致的        :  58 组
    独立暴力抓到的第一个反例：第 23 组 数据 [-7]  候选解给 0  暴力解给 -7

**同一个 bug、同一批 500 组数据：同思路的参考解一组都没抓到，两把独立的尺子各抓 58 组。**
58 组恰好等于「全是负数」的组数——这个 bug 的藏身处就只有那一类数据。

课件那张打印里，第一个反例写的是「数据 [-7]」却没有组号；按同一个种子从头扫，
这一组排在第 24 位（组号 23，从 0 数起）。这个数在参考解里如实报出来，判分也是这么找的。

最后一段是反向验证，专门证明「这个对拍器是活的」：把 best 的初值从 0 改成 -inf
（tools.cand_fixed 就是这一版），同一个对拍器、同一批数据应该交出 0 组不一致。
要是改好之后还是抓出一堆不一致，说明对拍器本身在乱报，它抓到的 58 组也就不算数了。

本任务的随机口径全部写死在 tools 里，别改：
    T1_SEED = 1、T1_TRIALS = 500、n ∈ 1..T1_N_HI、取值 T1_LO..T1_HI（-9..9）
判分自己用**同一个种子**重造这 500 组，再拿自己另写的两份参考解算一遍期望值，
和你打印的每一格对照。所以数字不能写死，「看着差不多」也不行。

接口：文件名、函数名、带 print 的行都是判分接口，别改。

跑： py task1_brute_ref.py
判： py run_tests.py
"""

import random

from tools import (T1_HI, T1_LO, T1_N_HI, T1_SEED, T1_TRIALS, cand_buggy, cand_fixed,
                   draw_case, ref_brute, ref_dc, ref_same_idea, show_banner, show_line,
                   values_equal)

# 占位那一格长这样：留白版打出来一眼就知道这一段还没接上。
MISSING = '（还没接上）'


def cell(value):
    """打印一格：值还是占位。"""
    return MISSING if value is None else str(value)


def count_cell(value):
    """打印「几组」那一格。"""
    return MISSING if value is None else str(value) + ' 组'


def run_trials(trials=T1_TRIALS, seed=T1_SEED):
    """同一批随机数据喂给四组「候选解 × 尺子」，数出各抓到几组不一致。

    四组都要真的跑：
      · 同思路那把尺子交回 0——它不是护身符，是装饰品；
      · 两把独立的尺子各交出 58——这个 bug 只住在一类数据里，能被独立尺子撞上；
      · 修好初值之后交回 0，这是对拍器自己的反向验证。
    """
    rng = random.Random(seed)
    counts = {('cand_buggy', 'same_idea'): 0, ('cand_buggy', 'brute'): 0,
              ('cand_buggy', 'dc'): 0, ('cand_fixed', 'brute'): 0}
    for _ in range(trials):
        a = draw_case(rng, T1_N_HI, T1_LO, T1_HI)
        c = cand_buggy(a)
        if not values_equal(c, ref_same_idea(a)):
            counts[('cand_buggy', 'same_idea')] += 1
        if not values_equal(c, ref_brute(a)):
            counts[('cand_buggy', 'brute')] += 1
        if not values_equal(c, ref_dc(a)):
            counts[('cand_buggy', 'dc')] += 1
        if not values_equal(cand_fixed(a), ref_brute(a)):
            counts[('cand_fixed', 'brute')] += 1
    return counts


def first_bad(trials=T1_TRIALS, seed=T1_SEED):
    """从头扫同一批数据，交出独立暴力解抓到的第一个反例。

    判据只能是 cand_buggy 与 ref_brute 比：拿同思路那把尺子来找，
    永远找不到反例——它和候选解错在同一个地方。
    """
    rng = random.Random(seed)
    for i in range(trials):
        a = draw_case(rng, T1_N_HI, T1_LO, T1_HI)
        got = cand_buggy(a)
        want = ref_brute(a)
        if not values_equal(got, want):
            return (i, a, got, want)
    return (None, None, None, None)


if __name__ == '__main__':                      # 别改：判分读的就是下面这些行
    show_banner('0030 对拍：两把尺子，同一批数据')
    cases = []
    rng = random.Random(T1_SEED)
    for _ in range(T1_TRIALS):
        cases.append(draw_case(rng, T1_N_HI, T1_LO, T1_HI))

    print('   种子 ' + str(T1_SEED) + '，' + str(T1_TRIALS) + ' 组随机数据（取值 '
          + str(T1_LO) + '..' + str(T1_HI) + '，n 到 ' + str(T1_N_HI) + '）：')

    counts = run_trials()
    show_line('   → 与「同一个思路的参考解」对拍，不一致的:',
              count_cell(counts.get(('cand_buggy', 'same_idea'))))
    show_line('   → 与「独立暴力解」对拍，不一致的        :',
              count_cell(counts.get(('cand_buggy', 'brute'))))
    show_line('   → 与「独立分治解」对拍，不一致的        :',
              count_cell(counts.get(('cand_buggy', 'dc'))))

    # 第一段小表：前 4 组长什么样。数据是脚本自己的种子造的，判分照着重造一遍。
    print('   前 4 组数据与两把尺子的判定:')
    for i in range(4):
        a = cases[i]
        print('      第 ' + str(i) + ' 组 n=' + str(len(a)) + ' 数据 ' + str(a)
              + ' 候选解给 ' + str(cand_buggy(a))
              + ' 暴力解给 ' + str(ref_brute(a))
              + ' 一致吗 ' + str(values_equal(cand_buggy(a), ref_brute(a))))

    print('   独立暴力抓到的第一个反例:')
    idx, data, got, want = first_bad()
    show_line('      在第', cell(idx) + ' 组')
    show_line('      数据', cell(data))
    show_line('      候选解给', cell(got))
    show_line('      独立暴力给', cell(want))

    show_line('   → 修好初值（best 从 -inf 起步）之后，与独立暴力对拍不一致的:',
              count_cell(counts.get(('cand_fixed', 'brute'))))
