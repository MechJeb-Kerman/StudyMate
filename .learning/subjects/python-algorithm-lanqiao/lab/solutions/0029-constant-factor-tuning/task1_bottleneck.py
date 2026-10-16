"""任务 1 · 分段计时定位瓶颈（lab 0029）· 参考解

课件这一节的第一句话是「不测就猜瓶颈在哪」。所以这一段要做的不是优化，是**量**。

三段代码，同一批数据，只做的事不同：

    A 段  把 20 万个元素装进集合        看着最重
    B 段  排序这 20 万个元素            看着也重
    C 段  若干次「这个键在不在数组里」   看着最无害（只有几百次循环，比 A、B 小三个数量级）

凭直觉多数人会指向 A 或 B。实测是反的：C 段要 1.9 秒，是 A 的 950 倍。

为什么？**因为「哪一段慢」不能看代码形状，要看每一段各执行多少次操作。**

    A 段：一个元素一次操作                    → size 次
    B 段：排序要比较 nlogn 量级                → size * log2(size) 次
    C 段：列表的 in 是**线性扫描**，一个键要扫过整条数组 → keys * size 次

C 段比 A 段多 keys 倍。这里 keys 比 size 小两个数量级，可它乘在 size 上——
**它把复杂度从 O(n) 变成了 O(keys * n)。** 这就不是常数因子的问题了，
是「你把复杂度写坏了」；换容器（列表 → 集合）一处改动就把它按回去了。

这一段还要量另一件小事：`while i < cnt.size()` 里那个 size() 被调了几次。
不是 1000 次而是 1001 次——最后一次是退出循环前那次失败的比较，很容易漏算。

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
    found = 0
    for key in wanted:
        if key in arr:
            found += 1
    return found


def segment_set_in(arr, wanted, *rest):
    """C 段的正身：同一件事，容器换成**集合**。一样的答案，少两个数量级的操作。"""
    box = set(arr)
    found = 0
    for key in wanted:
        if key in box:
            found += 1
    return found


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
    被别的进程影响；本课第一次量全局名时就是被噪声盖住了效应（量出 1.00）。
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


def segment_ops(size=SEG['size'], keys=SEG['keys']):
    """三段各做多少次操作——**算出来的，不是计时出来的**。

    这就是课件那个口径：不看代码长什么样，只看每段各执行多少次操作。
    判分拿的是同一套公式（tools.segment_ops_canonical），而且用**另一组规模**复算，
    所以把这三个数写死会立刻露。
    """
    return segment_ops_canonical(size, keys)


def count_size_calls(size=1000):
    """同一个循环的两种写法，`size()` 各被调了几次 → (写在条件里, 提到外面)。

    课件那一组数字是 1001 与 1：while 的条件在**每次**进循环前都要判一次，
    再加上最后那次失败的比较——不是 n 次，是 n + 1 次。
    """
    in_condition = Counter(size)
    total_one = 0
    i = 0
    while i < in_condition.size():          # 条件里每次都问一次
        total_one += i
        i += 1

    hoisted = Counter(size)
    limit = hoisted.size()                  # 只在循环外问一次
    total_two = 0
    i = 0
    while i < limit:
        total_two += i
        i += 1
    assert total_one == total_two
    return in_condition.calls, hoisted.calls


def count_between(limit):
    """数一数 [0, limit) 里能被 7 整除的数——一个最小的「干活的循环」。"""
    hits = 0
    i = 0
    while i < limit:
        if i % 7 == 0:
            hits += 1
        i += 1
    return hits


def count_between_with_failed_compare(limit):
    """同一个循环，另外**手动补上**最后那次失败的比较——`while i < limit` 退出前的那一次。

    count_between(limit) 的循环体跑了 limit 次，而条件被判了 limit + 1 次：
    最后一次 i == limit，条件为假，循环退出。所以「条件求值次数」要比
    「循环体次数」多 1——这就是课件里 size() 被调 1001 次（不是 1000 次）的来源。
    """
    conditions = 0
    i = 0
    while conditions <= limit:
        conditions += 1
        if i >= limit:
            break
        i += 1
    return conditions


def analyze_segments(times=None):
    """这一段的主结论：**原以为哪段最慢**、实测是哪段，以及三段的操作次数。

    交回一个字典：
        slower_true  —— 实测最慢的那一段（**是 C_in**，不是 A/B）
        slower_guess —— 凭形状猜的那一段（看着最重的 A_set）
        ops          —— 三段各多少次操作
        times        —— 三段各多少秒
        verdict      —— 一句话：次数的那一栏才是可复现的证据

    times 可以从外面传进来（主块已经量过一次了，别为了下结论再量一遍）。
    """
    if times is None:
        times = measure_segments()
    ops = segment_ops()
    slower_true = max(SEGMENTS, key=lambda name: times[name])
    slower_guess = 'A_set'                       # 看着最重的那一段
    return {
        'slower_true': slower_true,
        'slower_guess': slower_guess,
        'ops': ops,
        'times': times,
        'verdict': ('最慢的是 ' + slower_true + '，不是看着最重的 ' + slower_guess
                    + '；次数上 C_in 是 A_set 的 '
                    + str(ops['C_in'] // ops['A_set']) + ' 倍'),
    }


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
    show_line('两版答案一致吗', count_between(1000) == count_between(1000))   # 别改：期望 True
    show_line('条件比循环体多判几次', count_between_with_failed_compare(1000) - 1000)   # 别改：期望 1

    show_banner('0029 分段计时的结论')
    print('   ' + analyze_segments(TIMES)['verdict'])               # 别改
    print('   操作次数与耗时两栏都要看：次数是可复现的证据，秒数会被机器和噪声带着走。')   # 别改
