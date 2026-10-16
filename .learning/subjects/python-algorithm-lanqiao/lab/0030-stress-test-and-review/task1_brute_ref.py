"""任务 1 · 独立参考解对拍（lab 0030 · 提交前自检）

课件那一节量出来的第一组硬事实是：**对拍器不是护身符**。

候选解是第一课就写过的最大子段和，但 best 从 0 起步：

    best = cur = 0
    for x in a:
        cur = max(0, cur + x)
        best = max(best, cur)
    return best

这个 bug 只在「全都不是正数」的数据上出现：cur 被 max(0, ...) 按回 0，best 也就一直是 0，
于是交回 0，而正确答案是那个最大的负数。题目只保证「子段非空」时，`[-7]` 的答案就是 -7。

现在做对拍。两把尺子：

    ref_same_idea —— 照候选解**同一个错思路**再写一遍，只是行文不同（它也在 0 起步）；
    ref_brute     —— 独立参考解：枚举所有子段一个不漏（在 tools 里）。

课件量出来的结果是：

    500 组随机数据（取值 -9..9，n 到 8）：
        与「同一个思路的参考解」对拍，不一致的:   0 组
        与「独立暴力解」对拍，不一致的        :  58 组
    独立暴力抓到的第一个反例：数据 [-7]  候选解给 0  暴力解给 -7

**同一个 bug、同一批 500 组数据：同思路的参考解一组都没抓到，独立暴力抓到 58 组。**
差别的唯一来源是这两把尺子**独立不独立**，不是数据造得好不好。

最后一段是反向验证，专门证明「这个对拍器是活的」：把 best 的初值从 0 改成 -inf
（tools.cand_fixed 就是这一版），同一个对拍器、同一批数据应该交出 0 组不一致。
要是改好之后还是抓出一堆不一致，说明对拍器本身在乱报，它抓到的 58 组也就不算数了。

本任务的随机口径全部写死在 tools 里，别改：
    T1_SEED = 1、T1_TRIALS = 500、n ∈ 1..T1_N_HI、取值 T1_LO..T1_HI（-9..9）
判分自己用**同一个种子**重造这 500 组，再拿自己另写的两份参考解算一遍期望值，
和你打印的每一格对照。所以数字不能写死，「看着差不多」也不行。

接口：文件名、函数名、带 print 的行都是判分接口，别改；要写的是四个 TODO。

跑： py task1_brute_ref.py
判： py run_tests.py
"""

import random

from tools import (T1_HI, T1_LO, T1_N_HI, T1_SEED, T1_TRIALS, cand_buggy, cand_fixed,
                   draw_case, ref_brute, ref_same_idea, show_banner, show_line,
                   values_equal)

# 占位那一格长这样：留白版打出来一眼就知道这一段还没接上。
MISSING = '（还没接上）'


def cell(value):
    """打印一格：值还是占位。"""
    return MISSING if value is None else str(value)


def count_cell(value):
    """打印「几组」那一格。"""
    return MISSING if value is None else str(value) + ' 组'


# ══ TODO 1 ═════════════════════════════════════════════════
# run_trials(trials=T1_TRIALS, seed=T1_SEED)：把同一批随机数据喂给三把尺子，
# 数出**各抓到几组不一致**：{(候选解, 尺子): 组数}。
#
# 键名就这四个，别改（判分按这四个键取值）：
#     ('cand_buggy', 'same_idea') —— 候选解 vs 同一个思路的「参考解」
#     ('cand_buggy', 'brute')     —— 候选解 vs 独立暴力解
#     ('cand_buggy', 'dc')        —— 候选解 vs 独立分治解（tools.ref_dc）
#     ('cand_fixed', 'brute')     —— 修好初值之后的候选解 vs 独立暴力解
#
# 三件事必须照做：
#
#   (1) 数据用 random.Random(seed) 造，**每组先抽 n、再抽数组**——
#       就是 tools.draw_case(rng, T1_N_HI, T1_LO, T1_HI) 这一句，别自己改次序。
#       改一个次序，同一个种子就抽出另一批数据，四个数字全变。
#
#   (2) 比之前过 values_equal：**JSON 往返会把 tuple 变成 list**，
#       直接 == 比会在那些位置凭空多出一堆「不一致」，而那跟 bug 没关系。
#
#   (3) 'cand_fixed' 那一格要真的换函数（tools.cand_fixed），不是把数改成 0。
#       它是这一段的**反向验证**：改好之后应该一组不一致都没有。
#       一格都不写、或者写成 0，判分的探针会当场发现（它拿自己造的数据另算一遍）。
def run_trials(trials=T1_TRIALS, seed=T1_SEED):
    rng = random.Random(seed)
    counts = {('cand_buggy', 'same_idea'): None, ('cand_buggy', 'brute'): None,
              ('cand_buggy', 'dc'): None, ('cand_fixed', 'brute'): None}
    for _ in range(trials):
        a = draw_case(rng, T1_N_HI, T1_LO, T1_HI)
        pass
    return counts


# ══ TODO 2 ═════════════════════════════════════════════════
# first_bad(trials=T1_TRIALS, seed=T1_SEED) → (组号, 数据, 候选解给的, 独立暴力给的)
#
# 用**同一个种子**重造那批数据（random.Random(seed)，次序与 TODO 1 一样），
# 从头扫，交出**独立暴力解抓到的第一个反例**。一组都没抓到就交回 (None, None, None, None)。
#
# 组号从 0 开始数（第 1 组是 0）——这个数判分要核对。
#
# 判据只能是 cand_buggy(a) != ref_brute(a)：**不许用 ref_same_idea**。
# 用同思路那把尺子来找反例，永远找不到，这一段的结论就成了「没有反例」。
def first_bad(trials=T1_TRIALS, seed=T1_SEED):
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
