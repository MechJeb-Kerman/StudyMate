"""任务 2 · 一张「干活的多少」表 + 看形状

课件第二件事：按 n = 400 / 800 / 1600 / 3200 排四列 —— 归并、固定主元快排、
随机主元快排、`sorted` —— 把每一档「干了多少活」数出来，算相邻两档的倍率，
指出哪一列**不是** n log n 的形状。

## 这一课最关键的一个决定：表里不填秒数

「干活的多少」可以有两种记法：秒数，或者**操作次数**。这一课选了后者，理由是：

    n 翻一倍时，秒数只会翻个大概（同一份代码在不同机器上还不一样），
    而「比较了几次、搬动了几次、划分了几次」是同一份数据上的**同一个整数**，
    换台机器再跑还是它 —— 判分也能自己算一遍来核对。

所以这张表里四列全是次数。判分一条秒数都不读；秒数是下面单独打印的参考行。

## 四列各是什么

  · 归并      把元素搬进新表的次数。**与数据形状无关**，只由 n 决定。
              它并不是 n * log2(n)：最底下那层长度 1 的小段根本不合并，要减掉一截
              （n = 400 时 n*log2(n) 是 4000，实际是 3488）。
  · 固定主元  在**已有序数据**上比较了几次。主元永远取开头，而已有序时它就是这一段最小
              的那一个 —— 每次都只削掉一个元素，于是 n(n-1)/2，倍率正好 4.00。
  · 随机主元  主元随机挑（种子固定，所以次数确定）。同样在**已有序数据**上，
              它没有退化：比较次数是 n log n 那一类，倍率在 2.0 上下。
              这一列与上一列并排放，就是「同一个算法、只换了主元怎么挑」的对照，
              也是第三个任务的预告。
  · 计数      计数排序要动的「位置」数 = 清点 n 次 + 走一遍 0..V-1 那张表。
              值域 V 固定住，所以 n 翻倍时它长得**比 n log n 还慢** ——
              这一列就是那个「不是 n log n」的答案。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。

跑： py task2_time_table.py
判： py run_tests.py
"""

import sys

from tools import (
    make_small, make_random, show, show_factor, attempt, timed,
    merge_ops_measured, partition_ops_measured, counting_ops_measured,
    merge_ops_canonical, partition_comparisons_canonical, partition_calls_bound,
    counting_ops_canonical, merge_depth_canonical,
)

# 四档规模与值域宽度（判分会换成自己的 300 / 600 / 1200 再算一遍）。
SIZES = (400, 800, 1600, 3200)
BUCKETS = 2000                  # 计数排序那张表的值域宽度 V
DATA_SEED = 900001              # 造数据用的固定种子：同一份数据每次都能重现


def bench_data(n, buckets=BUCKETS, seed=DATA_SEED):
    """造这一档要用的两份数据（给好的）：值域小的那一份与大值域那一份。

    · 值域小的那一份：0..buckets-1 之间的整数，给计数排序用（它的表长 = 值域宽度）
    · 大值域那一份：满量程的整数，给三个比较类排序用
    """
    return [], []


def sample_ratios(sizes=SIZES):
    """序列里相邻两项的比值（给好的）：[0.5, 2.0] → [2.0]。"""
    return []


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 merge_moves(a)：数归并把元素搬进新表搬了几次。
#
#   return merge_ops_measured(a)[0]
#
# tools.merge_ops_measured(a) 交回 (搬动次数, 比较次数, 递归深度)，我们要第一个。
# 三个要点：
#   · 这个数与数据**无关**：有序、乱序、全是重复值，搬动次数一模一样
#   · 它**不是** n * log2(n)：最底下那一层长度 1 的小段不合并，要减掉一截
#     （n = 400 时 n*log2(n) 是 4000，实际是 3488）
#   · 它每层都要把全部元素搬一遍，所以它与快排的「比较次数」不是同一个量
def merge_moves(a):
    return 0


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 quick_fixed_compares(a)：数「固定主元」快排在**已有序数据**上比较了几次。
#
#   return partition_ops_measured(a, 'fixed')[0]
#
# 主元永远取这一段的开头。已有序时主元就是这一段里最小的那一个，
# 后面每个元素都要比一次，可是一个都进不了「小于主元」那一段 —— 每次都只削掉一个元素。
# 结果是 n(n-1)/2 次比较，n 翻一倍就翻两番（正好 4.00 倍）。
#
# 注意**不要在函数里把 a 真的排序**：要数的就是交给你的这一份数据。
def quick_fixed_compares(a):
    return 0


# ══ TODO 3 ═════════════════════════════════════════════════
# 写 quick_random_compares(a)：数「随机主元」快排在同一份数据上比较了几次。
#
#   return partition_ops_measured(a, 'random')[0]
#
# 随机主元把主元随机换到开头（种子固定，所以每次数出来都一样），
# 已有序数据上它就不再退化了：比较次数回到 n log n 那一类，倍率在 2.0 上下。
#
# 为什么要与上一列并排：两列**用的是同一份已有序数据**，只有「主元怎么挑」这一处不同。
# 一个 4.00 倍、一个 2.0 倍，差别就出在那两行随机换位上 —— 第三个任务会把它放大到
# 「一个撞递归上限、一个不撞」。
def quick_random_compares(a):
    return 0


# ══ TODO 4 ═════════════════════════════════════════════════
# 写 counting_positions(a, buckets)：数计数排序要动几个「位置」。
#
#   counted, written = counting_ops_measured(a, buckets - 1)
#   return counted + written
#
# 两笔：清点每一个元素一次（len(a) 次），再走一遍 0..buckets-1 那张表（buckets 次）。
# 表长由**值域**决定，与有多少个元素无关 —— 这就是这一列的形状与别的列不同的原因。
def counting_positions(a, buckets):
    return 0


# ══ TODO 5 ═════════════════════════════════════════════════
# 写 bench_table(sizes)：把四列数的表造出来。
#
# 交回 {'归并': [...], '固定主元': [...], '随机主元': [...], '计数': [...]}，
# 四个表各按 sizes 的顺序放四档的数。**列名就是判分接口**，别改名。
#
# 每一档按下面的顺序来（四列要对齐到同一个 n 上）：
#   small, big = bench_data(n)
#   ordered = sorted(big)
#   · 归并        merge_moves(big)
#   · 固定主元    quick_fixed_compares(ordered)     ← 用已有序那一份，这才是要害
#   · 随机主元    quick_random_compares(ordered)    ← 同一份已有序数据，只换了主元
#   · 计数        counting_positions(small, BUCKETS)
def bench_table(sizes=SIZES):
    return {'归并': [], '固定主元': [], '随机主元': [], '计数': []}


# ══ TODO 6 ═════════════════════════════════════════════════
# 写 bench_ratios(table)：算每一列「这一档 ÷ 上一档」的倍率。
#
# 交回 {'归并': [...], '固定主元': [...], '随机主元': [...], '计数': [...]}，
# 每个表比 sizes 少一个数（四档只有三个倍率）。用 round(后 / 前, 2)。
#
# 三个倍率一起看的用处：
#   · n log n 一类的列，倍率在 2.0 到 2.4 之间（理论上 log 那一项还要长一点）
#   · n 平方那一列，倍率正好 4.00
#   · 值域固定住的那一列，倍率比 2.0 还小（n 长了，V 那一半没动）
def bench_ratios(table):
    return {'归并': [], '固定主元': [], '随机主元': [], '计数': []}


# ══ TODO 7 ═════════════════════════════════════════════════
# 写 not_nlogn(ratios)：从倍率里挑出「形状不是 n log n」的那一列，交回它的名字。
#
# 判法（只看倍率、不看秒数）：把每一列的三个倍率乘起来，得到「从 400 到 3200
# 一共长了几倍」，再挑**总倍数最小**的那一列。
#
# 为什么这么挑：四列都在同一个 n 序列上量，n log n 那一类总倍数在 8 倍上下
# （2.2 的三次方），n 平方那一列是 4 的三次方 = 64 倍，
# 而「值域固定住」的那一列长得比 8 倍还慢 —— 它最小。
def not_nlogn(ratios):
    return ''


# ══ TODO 8 ═════════════════════════════════════════════════
# 写 not_nlogn_reason(name)：用一句话说明为什么是它。
#
# 交回一个非空字符串即可（判分只核它非空、且提到那一列的名字）。
# 建议这样讲：计数排序那张表的长度由**值域** V 决定，与 n 无关；
# n 从 400 涨到 3200 时，它只多了 n 那一半，V 那一半一步没动，
# 所以它的倍率比 n log n 的 2.2 还小（1.17 / 1.29 / 1.44）。
def not_nlogn_reason(name):
    return ''


# ── 给好的部分：主块与打印（别改）───────────────────────────────────────

def cell(column, index):
    """从某一列里取第 index 个格；那个格子还没写出来时交回 None。

    这样「函数还没实现」时这一段照样把每一行打完（打印的是 —），
    而不是半路 IndexError —— 判分要看到的是每一条 FAIL 点了哪个 TODO。
    """
    if not isinstance(column, (list, tuple)) or index >= len(column):
        return None
    return column[index]


if __name__ == '__main__':
    print('任务 2 · 一张「干活的多少」表 + 看形状')

    # 「固定主元」那一列要在已有序数据上数到 n = 3200：递归会落到 3200 层，
    # 默认上限（1000）撑不住。所以这里把上限调大 —— 这一段量的是「干了多少活」，
    # 不是「会不会撞上限」（撞上限是第三个任务的主题）。
    sys.setrecursionlimit(20000)

    table = bench_table(SIZES)
    ratios = bench_ratios(table)

    # ── 第 1 段：四列的操作次数 ─────────────────────────────────────────
    for i, n in enumerate(SIZES, 1):
        show('操作', i, '归并', cell(table.get('归并'), i - 1))
        show('操作', i, '固定主元', cell(table.get('固定主元'), i - 1))
        show('操作', i, '随机主元', cell(table.get('随机主元'), i - 1))
        show('操作', i, '计数', cell(table.get('计数'), i - 1))

    # ── 第 2 段：相邻两档的倍率 ─────────────────────────────────────────
    for i, n in enumerate(SIZES[1:], 2):
        show_factor('倍率', i, '归并', cell(ratios.get('归并'), i - 2))
        show_factor('倍率', i, '固定主元', cell(ratios.get('固定主元'), i - 2))
        show_factor('倍率', i, '随机主元', cell(ratios.get('随机主元'), i - 2))
        show_factor('倍率', i, '计数', cell(ratios.get('计数'), i - 2))

    # ── 第 3 段：形状不是 n log n 的那一列 ──────────────────────────────
    odd = not_nlogn(ratios)
    if not odd:
        odd = '（还没交回名字）'
    show('形状', 1, '不是nlogn', odd)
    print('形状 02 为什么 ' + (not_nlogn_reason(odd) or '（还没写下理由）'))

    # ── 耗时（照量、照打印；判分一条都不读它）────────────────────────────
    # 这一段的四列是「次数」，下面这一批才是秒数：同一次运行里它们是可比的，
    # 但换台机器就会变 —— 所以判分只读上面那四列。
    for i, n in enumerate(SIZES, 1):
        one_small, one_big = bench_data(n)
        t_merge = timed(merge_ops_measured, list(one_big))[1]
        print('耗时 %02d 归并 n=%d %.6f 秒（参考，判分不读）' % (i, n, t_merge))
    for i, n in enumerate(SIZES, 5):
        one_small, one_big = bench_data(n)
        one_ordered = sorted(one_big)
        sys.setrecursionlimit(20000)
        t_fixed = timed(partition_ops_measured, list(one_ordered), 'fixed')[1]
        print('耗时 %02d 固定主元 已有序 n=%d %.6f 秒（参考，判分不读）' % (i, n, t_fixed))
    for i, n in enumerate(SIZES, 9):
        one_small, one_big = bench_data(n)
        one_ordered = sorted(one_big)
        t_rand = timed(partition_ops_measured, list(one_ordered), 'random')[1]
        print('耗时 %02d 随机主元 已有序 n=%d %.6f 秒（参考，判分不读）' % (i, n, t_rand))
    for i, n in enumerate(SIZES, 13):
        one_small, one_big = bench_data(n)
        t_count = timed(counting_ops_measured, list(one_small), BUCKETS - 1)[1]
        print('耗时 %02d 计数 n=%d %.6f 秒（参考，判分不读）' % (i, n, t_count))
    print('耗时 17 已有序 n=' + str(SIZES[-1])
          + ' 固定主元 见第三个任务（那一版会撞递归上限）')
