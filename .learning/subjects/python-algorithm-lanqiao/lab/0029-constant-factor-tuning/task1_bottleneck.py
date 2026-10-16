"""任务 1 · 分段计时定位瓶颈（lab 0029）

课件这一节的第一句话是「不测就猜瓶颈在哪」。所以这一段要做的不是优化，是**量**。

三段代码，同一批数据，只做的事不同：

    A 段  把元素装进集合                 看着最重
    B 段  排序这同一批元素                看着也重
    C 段  若干次「这个键在不在数组里」      看着最无害（只有几百次循环，比 A、B 小三个数量级）

凭直觉多数人会指向 A 或 B。实测是反的。为什么？**因为「哪一段慢」不能看代码形状，
要看每一段各执行多少次操作。**

接口：文件名、函数名、带 print 的行都是判分接口，别改；要写的是五个 TODO：

    TODO 1  segment_ops                    三段各做多少次操作（算出来的，不是计时出来的）
    TODO 2  analyze_segments               原以为哪段最慢、实测是哪段
    TODO 3  segment_list_in / set_in       同一件事，列表与集合各数一遍命中
    TODO 4  count_size_calls               条件里的 size() 被调了 n + 1 次
    TODO 5  count_between                  一个最小的「干活的循环」

判分怎么判：五条**确定量**——三段各多少次操作（判分拿另两组规模复算）、
原以为最慢的是哪段 / 实测是哪段（判分给两次不一样的实测值）、`size()` 被调 n + 1 次、
两段在判分自己的数据上交回同一个命中数、那个干活的循环数得对。
耗时只在打印里给人看，不当判据。

跑： py task1_bottleneck.py
判： py run_tests.py
"""

from tools import (SEG, SEG_ROLE, SEGMENTS, fmt_seconds, median_seconds,
                   sample_data, segment_ops_canonical, show_banner, show_line)


class Counter:
    """一个会自己数「被调用了几次」的对象（课件里那个 Counter 的原样）。"""

    def __init__(self, size):
        self.size_value = size
        self.calls = 0

    def size(self):
        self.calls += 1
        return self.size_value


def build_segment_data(size=SEG['size'], keys=SEG['keys'], seed=SEG['seed']):
    """把三段要用的数据一次造好：三段**共用同一个数组**，C 段另有一张键表。"""
    arr, wanted = sample_data(seed, size, keys)
    return arr, wanted


def segment_build_set(arr, *rest):
    """A 段：把数组装进集合。一个元素一次操作，一步步来（不是 set(arr) 那一行就完）。"""
    box = set()
    for value in arr:
        box.add(value)
    return box


def segment_sort(arr, *rest):
    """B 段：排序。用内置的 sorted——这一段要比的是「排序本身要多少比较」，不是手写排序。"""
    return sorted(arr)


def segment_list_in(arr, wanted, *rest):
    """C 段：若干次「键在不在数组里」，容器是**列表**。"""
    return 0


def segment_set_in(arr, wanted, *rest):
    """C 段的正身：同一件事，容器换成**集合**。一样的答案，少两个数量级的操作。"""
    return 0


# 三段各是一个「吃一份数据、交回一个结果」的函数——这样计时器对三段一视同仁，
# 比的是代码本身，不是「谁被包得更容易量」。
SEGMENT_FUNCS = {
    'A_set': segment_build_set,
    'B_sort': segment_sort,
    'C_in': segment_list_in,
}


def measure_segments(data=None, repeats=SEG['repeats']):
    """三段各量一次，交回 {段名: 秒数}。

    计时的口径与课件一致：跑 repeats 次取**中位数**——单次计时会被调度、
    被别的进程影响。判分不拿这里的秒数当判据（它只核「不能一格都没量」），
    但打印出来的那几行就是给人看的证据，所以这一段要真跑。
    """
    if data is None:
        data = build_segment_data()
    times = {}
    for name in SEGMENTS:
        call = SEGMENT_FUNCS[name]
        args = data[name] if isinstance(data, dict) else data
        seconds, _ = median_seconds(lambda call=call, args=args: call(*args), repeats)
        times[name] = seconds
    return times


# ══ TODO 1 ═════════════════════════════════════════════════
# segment_ops(size, keys)：三段各做多少次操作——**算出来的，不是计时出来的**。
#
# 这就是课件那个口径：不看代码长什么样，只看每段各执行多少次操作。
# 三段的公式（tools.segment_ops_canonical 就是这三行）：
#
#     A 段  一个元素一次操作                → size
#     B 段  排序要比较 nlogn 量级            → size * log2(size)
#     C 段  列表的 in 是线性扫描，一个键扫整条数组 → keys * size
#
# 交回 {'A_set': …, 'B_sort': …, 'C_in': …} 这样一个字典（键名是判分接口）。
# 判分用**另两组规模**复算，所以把三个数写死会立刻露。
def segment_ops(size=SEG['size'], keys=SEG['keys']):
    return {'A_set': 0, 'B_sort': 0, 'C_in': 0}


# ══ TODO 2 ═════════════════════════════════════════════════
# analyze_segments(times=None)：这一段的主结论——**原以为哪段最慢**、实测是哪段。
#
# 交回一个字典（键名是判分接口，别改）：
#
#     slower_true  实测最慢的那一段：`max(SEGMENTS, key=lambda name: times[name])`
#                  ——注意它必须从**传进来的 times 里查**，不能写死某一段
#     slower_guess 凭形状猜的那一段：'A_set'（看着最重的那个）
#     ops          三段的操作次数：segment_ops()
#     times        三段耗时（times 是 None 时自己量一次：measure_segments()）
#     verdict      一句话，把 slower_true 与 slower_guess 都写进去
#
# 判分给两次**不一样的**实测值（一次 C 最慢、一次 A 最慢），所以
# slower_true 跟着传进来的值走才算对，写成常数会当场露。
def analyze_segments(times=None):
    return {'slower_true': None, 'slower_guess': None, 'ops': {},
            'times': {}, 'verdict': ''}


# ══ TODO 3 ═════════════════════════════════════════════════
# segment_list_in(arr, wanted, *rest) 与 segment_set_in(arr, wanted, *rest)：
# 同一件事、同一批数据，容器一个是**列表**一个是**集合**，各交回**找到了几个**。
#
# 列表版：
#
#     found = 0
#     for key in wanted:
#         if key in arr:        ← 列表的 in 是**线性扫描**：一个键要扫过整条数组
#             found += 1
#     return found
#
# 集合版：先把 arr 装进集合，然后**同样**数一遍：
#
#     box = set(arr)
#     found = 0
#     for key in wanted:
#         if key in box:        ← 集合的 in 平均一步
#             found += 1
#     return found
#
# 换容器的全部内容就是这一处：`in` 写在集合上是平均一步，写在列表上是一路扫过去。
# **答案必须一模一样**——换容器省的是操作次数，不是「顺便把答案改一改」。
# 判分拿**它自己的**数组与键表调这两个函数：命中个数要相等，而且要等于判分另算的那一个。


# ══ TODO 4 ═════════════════════════════════════════════════
# count_size_calls(size)：同一个循环的两种写法，`size()` 各被调了几次
# → (写在条件里那版, 提到外面那版)。
#
# 三行一个循环，写两遍就行：
#
#     c1 = Counter(size)                     c2 = Counter(size)
#     i = 0; total = 0                       limit = c2.size()   ← 只在外面问一次
#     while i < c1.size():                   i = 0; total = 0
#         total += i                         while i < limit:
#         i += 1                                 total += i
#                                                i += 1
#     return c1.calls, c2.calls
#
# **关键是这个数是 n + 1 而不是 n**：条件在每次进循环前都要判一次，
# 退出循环前还有一次失败的比较。课件那组数字就是 1001 与 1。
# 判分换成别的 n 再问一遍，所以写死 1001 会露。
def count_size_calls(size=1000):
    return (0, 0)


# ══ TODO 5 ═════════════════════════════════════════════════
# count_between(limit)：数一数 [0, limit) 里能被 7 整除的数——一个最小的「干活的循环」。
#
#     hits = 0
#     i = 0
#     while i < limit:
#         if i % 7 == 0:
#             hits += 1
#         i += 1
#     return hits
#
# 这一格是「一段真的在干活的代码」的最小样本。主块里那个
# 「条件比循环体多判几次」也用它：count_between(1000) 的循环体跑了 1000 次，
# 而条件被判了 **1001** 次——最后一次 i == 1000，条件为假，循环退出。
# count_between_with_failed_compare(limit) 就是把那个 1001 数出来交回，
# 所以你写完之后，主块那一行「1001 - 1000」应该是 1。
def count_between(limit):
    return 0


def count_between_with_failed_compare(limit):
    """同一个循环，另外**手动补上**最后那次失败的比较——交回条件被判了几次。"""
    return 0


if __name__ == '__main__':                      # 别改：判分读的就是下面这几行
    ARR, WANTED = build_segment_data()

    show_banner('0029 三段各量一次')
    print('   三段各是什么：')                                    # 别改
    for name in SEGMENTS:
        print('      ' + name + '  ' + SEG_ROLE[name])             # 别改
    TIMES = measure_segments({'A_set': (ARR,), 'B_sort': (ARR,),
                              'C_in': (ARR, WANTED, False)})
    for name in SEGMENTS:
        show_line('实测 ' + name, fmt_seconds(TIMES[name]) + ' 秒')  # 别改
    show_line('三段合计', fmt_seconds(sum(TIMES.values())) + ' 秒')  # 别改

    show_banner('0029 不看形状，看次数')
    OPS = segment_ops()
    for name in SEGMENTS:
        show_line('操作次数 ' + name, OPS[name])                    # 别改
    show_line('C 是 A 的几倍',
              max(1, OPS['C_in']) // max(1, OPS['A_set']))          # 别改

    show_banner('0029 原以为哪段最慢')
    show_line('凭形状猜最慢', 'A_set')                              # 别改
    show_line('实测最慢', max(SEGMENTS, key=lambda name: TIMES[name]))   # 别改
    show_line('猜的和实测一样吗', False)                            # 别改：这一课的第一句话

    show_banner('0029 循环条件里的重复求值')
    IN_COND, HOISTED = count_size_calls()                           # 别改
    show_line('写在条件里 size() 调用', IN_COND)                    # 别改：期望 1001
    show_line('提到循环外面 size() 调用', HOISTED)                  # 别改：期望 1
    show_line('两版答案一致吗',
              segment_list_in(ARR, WANTED) == segment_set_in(ARR, WANTED))   # 别改
    show_line('条件比循环体多判几次',
              count_between_with_failed_compare(1000) - count_between(1000))  # 别改

    show_banner('0029 分段计时的结论')
    print('   ' + analyze_segments(TIMES)['verdict'])               # 别改
    print('   操作次数与耗时两栏都要看：次数是可复现的证据，秒数会被机器和噪声带着走。')   # 别改
