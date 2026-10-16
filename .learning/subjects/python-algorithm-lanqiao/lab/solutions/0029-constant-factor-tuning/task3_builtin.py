"""任务 3 · 和内置实现比一次（lab 0029）· 参考解

上一段把写法优化了一遍，这一段换个问法：**优化完的写法，和内置还差多远？**

课件那一节有两条看起来很像、其实不同的结论：

    求和   手写 for 循环 vs sum        快 4.8 倍     ← 差的是**循环那一层**
    排序   手写冒泡    vs sorted      快 1134 倍    ← 绝大部分是**复杂度**，
                                                    只有一小部分是常数

加起来的倍率很好看，但「差在哪一层」才是要写下来的东西。这一段每一栏都交回三样：

    answer      两边交回的答案（必须一样——优化也好、换内置也好，都不许改答案）
    hand_work   手写版做多少次「值访问」
    builtin_work 内置版做多少次「值访问」
    layer       差在哪一层（一句话，判分按关键词认）

**「值访问」是这一段的主判据**：真正读到一个元素的值算一次。手写版每一轮 Python
都要绕一圈（FOR_ITER + 加法 + STORE_FAST），内置版在 C 里绕——
差的就是这一层。次数是确定量，倍率是参考量。

四栏的对应关系（课件那张「类似的对应关系还有」的小节）：

    contain  列表 in       → set        反复查在不在
    sort     手写冒泡      → sorted     排序：这一栏的倍率主要来自**复杂度**
    sum      手写循环      → sum        求和
    min      反复 min      → heapq      反复取最小（堆）

跑： py task3_builtin.py
判： py run_tests.py
"""

import heapq
import time

from tools import (FLOOR, LCG, WORK_REPEATS, WORK_SIZES, count_key_calls,
                   fmt_seconds, judge_guard, median_seconds, sample_data,
                   show_banner, show_line, sum_of)

# 每一栏「差在哪一层」。判分按关键词认这几句，所以关键词（写在括号里那些词）别删。
LAYERS = {
    'contain': '查找那一层：列表是线性扫描 O(n)，集合是平均 O(1)',
    'sort': '复杂度那一层：冒泡是 O(n^2)，Timsort 是 O(n log n)；常数只占一小部分',
    'sum': '循环那一层：手写每轮 FOR_ITER + 加法 + STORE_FAST，sum 整个循环在 C 里跑',
    'min': '每轮代价那一层：反复 min 一遍遍扫全表，nsmallest 用堆 O(n log k)',
    'role': '分支那一层：if/elif 是一路比下来的，查表只索引一次',
}


def layer_of(job):
    """这一栏「差在哪一层」的那句话（判分按关键词认）。"""
    return LAYERS.get(job, '')


def compute_answer(job, seed=4242, sizes=None):
    """这一栏两边应该交回的**同一个答案**——独立算一遍，不经过那两个函数。

    判分拿它当尺子：手写版与内置版都必须交回这个值。
    「优化不许改答案」也好、「换成内置」也好，答案都得是这一个。
    """
    sizes = dict(WORK_SIZES[job] if sizes is None else sizes)
    if job == 'contain':
        arr, wanted = sample_data(seed, sizes['arr'], sizes['keys'])
        return sum(1 for key in wanted if key in set(arr))
    if job == 'sort':
        return sorted(LCG(seed).make(sizes['n'], 0, 1000000))[:sizes['k']]
    if job == 'sum':
        return sum_of(LCG(seed).make(sizes['n'], -1000, 1000))
    if job == 'min':
        # 第 k 小的那个（k 从 1 数起）。
        values = LCG(seed).make(sizes['n'], 0, 1000000000)
        return heapq.nsmallest(sizes['k'], values)[sizes['k'] - 1]
    if job == 'role':
        values = LCG(seed).make(sizes['n'], 0, 3)
        counts = [0] * 16
        for value in values:
            counts[(value * 5) % 16] += 1
        return counts
    raise ValueError('没有这一栏：' + str(job))


def make_job(job, seed, sizes=None, repeats=None):
    """造这一栏要用的数据与两个函数 → (手写版, 内置版, 答案算得对不对的检查)。

    两边的数据是**同一份**——课件那个 warn 说的就是这件事：两个版本除了要比的那一点，
    别的地方真的一样吗？
    """
    sizes = dict(WORK_SIZES[job] if sizes is None else sizes)
    repeats = WORK_REPEATS[job] if repeats is None else repeats

    if job == 'contain':
        arr, wanted = sample_data(seed, sizes['arr'], sizes['keys'])

        def hand():
            hits = 0
            for key in wanted:
                for value in arr:               # 线性扫描：每个键看一整条数组
                    if value == key:
                        hits += 1
                        break
            return hits

        def builtin():
            box = set(arr)
            return sum(1 for key in wanted if key in box)

        return hand, builtin, repeats

    if job == 'sort':
        values = LCG(seed).make(sizes['n'], 0, 1000000)

        def hand():
            data = list(values)
            for i in range(len(data) - 1):      # 冒泡：每一对都比一次
                for j in range(len(data) - 1 - i):
                    if data[j] > data[j + 1]:
                        data[j], data[j + 1] = data[j + 1], data[j]
            return data[:sizes['k']]            # 两边只交回最小的一小撮，方便比

        def builtin():
            # 走一个计数器当 key：这样「真调了 Timsort」这件事有证据，
            # 不是「交回一张排好的表」就算数。
            ordered, _calls = count_key_calls(values)
            return ordered[:sizes['k']]

        return hand, builtin, 1

    if job == 'sum':
        values = LCG(seed).make(sizes['n'], -1000, 1000)

        def hand():
            return sum_of(values)

        def builtin():
            return sum(values)

        return hand, builtin, repeats

    if job == 'min':
        values = LCG(seed).make(sizes['n'], 0, 1000000000)

        def hand():
            box = list(values)
            for _ in range(sizes['k'] - 1):
                box.remove(min(box))            # 每取一个都要把整条数组看一遍
            return min(box)                     # 剩下的最小值就是第 k 小的那个

        def builtin():
            # 第 k 小的那个：堆只用一次，每个元素只看一遍。
            return heapq.nsmallest(sizes['k'], values)[sizes['k'] - 1]

        return hand, builtin, repeats

    if job == 'role':
        # 16 个桶，一条 16 分支的 if/elif 链对上一张查表。
        # 课件那一节：2 个分支时查表只快 1.06 倍（噪声边缘），
        # 8 个以上稳赢 2.65 倍起——分支越多越该换查表。
        values = LCG(seed).make(sizes['n'], 0, 3)     # 桶号由 value * 5 % 16 定
        table = [0] * 16

        def bucket_of(value):
            return (value * 5) % 16

        def hand():
            counts = [0] * 16
            for value in values:
                if bucket_of(value) == 0:                 # 一路比下来
                    counts[0] += 1
                elif bucket_of(value) == 1:
                    counts[1] += 1
                elif bucket_of(value) == 2:
                    counts[2] += 1
                elif bucket_of(value) == 3:
                    counts[3] += 1
                elif bucket_of(value) == 4:
                    counts[4] += 1
                elif bucket_of(value) == 5:
                    counts[5] += 1
                elif bucket_of(value) == 6:
                    counts[6] += 1
                elif bucket_of(value) == 7:
                    counts[7] += 1
                elif bucket_of(value) == 8:
                    counts[8] += 1
                elif bucket_of(value) == 9:
                    counts[9] += 1
                elif bucket_of(value) == 10:
                    counts[10] += 1
                elif bucket_of(value) == 11:
                    counts[11] += 1
                elif bucket_of(value) == 12:
                    counts[12] += 1
                elif bucket_of(value) == 13:
                    counts[13] += 1
                elif bucket_of(value) == 14:
                    counts[14] += 1
                else:
                    counts[15] += 1
            return counts

        def builtin():
            counts = list(table)
            for value in values:
                counts[bucket_of(value)] += 1             # 查表：一次索引
            return counts

        return hand, builtin, repeats

    raise ValueError('没有这一栏：' + str(job))


def compare_with_builtin(job, seed=4242, sizes=None, repeats=None):
    """跑一栏：手写 vs 内置，交回 {answer, hand, builtin, hand_work, builtin_work,
    hand_time, builtin_time, layer}。

    答案两边必须一样——不一样就说明这一栏的「两个版本」其实是两件事，
    量出来的倍率再好看也没意义（课件那个「查表反而慢 12%」就是这么写错的）。
    """
    hand, builtin, reps = make_job(job, seed, sizes, repeats)
    hand_time, hand_answer = median_seconds(hand, reps)
    builtin_time, builtin_answer = median_seconds(builtin, reps)
    hand_work = work_of(job, seed, sizes, 'hand')
    builtin_work = work_of(job, seed, sizes, 'builtin')
    return {
        'answer': compute_answer(job, seed, sizes),     # 与两边各自算的对上才算数
        'hand': hand_answer,
        'builtin': builtin_answer,
        'hand_work': hand_work,
        'builtin_work': builtin_work,
        'hand_time': hand_time,
        'builtin_time': builtin_time,
        'layer': layer_of(job),
    }


def work_of(job, seed, sizes, side):
    """这一栏这一边做多少次「值访问」——**按规模算出来的**，不是计时出来的。

    手写版每一轮 Python 都绕一圈；内置版在 C 里绕。次数差在哪，倍率就出在哪。
    """
    sizes = dict(WORK_SIZES[job] if sizes is None else sizes)
    if job == 'contain':
        if side == 'hand':
            # 最坏情况下一个键要看完整条数组（就是课件那个 keys * size）。
            return sizes['keys'] * sizes['arr']
        arr, wanted = sample_data(seed, sizes['arr'], sizes['keys'])
        box = set(arr)
        return sum(1 for key in wanted if key in box)       # 命中才真正读到值
    if job == 'sort':
        if side == 'hand':
            return sizes['n'] * (sizes['n'] - 1) // 2       # 冒泡每一对都比一次
        return sizes['n']                                   # Timsort 取 key 只读一次值
    if job == 'sum':
        return sizes['n']
    if job == 'min':
        if side == 'hand':
            return sizes['n'] * WORK_REPEATS['min']          # 每取一个扫一遍全表
        return sizes['n']                                    # nsmallest 每个元素只看一次
    if job == 'role':
        if side == 'hand':
            return sizes['n'] * 8                            # 落在最后一个桶平均比 8 次
        return sizes['n']                                    # 查表：一个值只取出来一次
    raise ValueError('没有这一栏：' + str(job))


def recursion_ceiling(n):
    """递归求和能不能撑到 n 层：撑得住交回和，撑不住交回 None。

    课件量出来的是「n = 998 还行、n = 999 就 RecursionError」——
    跟第 12 课、第 17 课量到的是同一个数（默认上限 1000，主模块本身占一层）。
    **边界值随你在第几层调用浮动**（调用点是探针、是函数、还是主块顶层，差几层），
    所以这里量的是「哪个 n 还撑得住、哪个 n 已经不行」，不是一个写死的 998。
    """
    try:
        return sum_rec(list(range(n)))
    except RecursionError:
        return None


def recursion_edge(high=1500):
    """二分找出边界：最大的那个「还撑得住」的 n。

    这本机实测是 998：默认上限 1000，主模块本身占一层。这个数会随调用深度
    与 Python 版本浮动，所以判分核的是**机制**——边界那个 n 撑得住、
    再深一层就 RecursionError——而不是那个具体的数。
    """
    lo, hi = 1, int(high)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if recursion_ceiling(mid) is None:
            hi = mid - 1
        else:
            lo = mid
    return lo


def recursion_probe():
    """贴着边界试两步 → [边界 n, 边界撑得住吗, 再往上顶一层还撑得住吗]。

    为什么第二探是 `edge + 2` 而不是 `edge + 1`：多一层调用就少一层栈，
    所以拿同一个 n 去问「再深一层」时会差一格。**这里要证明的是机制**
    ——「有个 n 撑得住、再往上就不行了」——差一格是量法的事，不是结论的事。
    判分核的是这个机制（第二个真、第三个假），不是一个写死的边界值。
    """
    edge = recursion_edge()
    return [edge,
            recursion_ceiling(edge) is not None,
            recursion_ceiling(edge + 2) is not None]


def sum_rec(values, i=0):
    """递归求和。**深度跟着 n 长的递归一律改迭代**——不只是慢 6.7 倍，
    更要紧的是它到不了任意深。"""
    if i == len(values):
        return 0
    return values[i] + sum_rec(values, i + 1)


def sum_iter(values):
    """同一个和的迭代版：不建栈帧，深度与 n 无关。"""
    total = 0
    for value in values:
        total += value
    return total


def iteration_passes(values, floor=FLOOR, cap=256, probe_reps=32):
    """决定「迭代版跑几遍」：跑到中位数能被量出来为止。

    n = 900 的迭代求和只要 20 微秒上下，跑一遍的话秒数还落在噪声里。
    这一课量的是常数因子，量小了没意义——所以先估一估一遍要多久，
    再把「每次计时都跑够 floor 秒」折成遍数。**别用 median_seconds 在这里探**：
    它一次就按倍率跑满（32 次），再乘上遍数就白烧掉几千倍的时间。
    最多 cap 遍。

    **这一格是「让秒数可量」用的，不是判据。** 判分核的是两样确定量：
    递归版与迭代版的和一样、以及递归边界那个 n 到哪儿为止（这是个机制）。
    """
    reps = max(1, int(probe_reps))
    start = time.perf_counter()
    for _ in range(reps):
        sum_iter(values)
    each = (time.perf_counter() - start) / reps
    if each <= 0:
        return 1
    passes = int(floor / each) + 1
    return max(1, min(int(cap), passes))


def brief(value, limit=4):
    """打印用：长表只留前几个，后面写成「… 共 N 个」。"""
    if isinstance(value, (list, tuple)):
        shown = list(value)[:limit]
        return str(shown) + ' … 共 ' + str(len(value)) + ' 个'
    return str(value)


def distance(hand, builtin):
    """两个答案差多远（数字）；不是数字就按「一样 / 不一样」交回 0 或 1。

    「优化不许改答案」在代码里就是这一句：四种写法交回的答案必须逐字一致。
    """
    if hand == builtin:
        return 0
    if isinstance(hand, (int, float)) and isinstance(builtin, (int, float)):
        return abs(hand - builtin)
    return 1


if __name__ == '__main__':                      # 别改：判分读的就是下面这几行
    show_banner('0029 和内置比：四栏')
    ROWS = {JOB: compare_with_builtin(JOB)
            for JOB in ('contain', 'sort', 'sum', 'min', 'role')}
    for JOB in ('contain', 'sort', 'sum', 'min', 'role'):
        ROW = ROWS[JOB]
        print('   ' + JOB + ' 答案手写 ' + str(ROW['hand'])
              + ' 内置 ' + str(ROW['builtin'])
              + ' 一致 ' + str(ROW['hand'] == ROW['builtin']))        # 别改
        show_line('手写 ' + JOB, str(ROW['hand_work']) + ' 次值访问 '
                  + fmt_seconds(ROW['hand_time']) + ' 秒')             # 别改
        show_line('内置 ' + JOB, str(ROW['builtin_work']) + ' 次值访问 '
                  + fmt_seconds(ROW['builtin_time']) + ' 秒')          # 别改
        show_line('差在哪一层 ' + JOB, ROW['layer'])                   # 别改

    show_banner('0029 倍率只当参考')
    for JOB in ('sum', 'sort', 'min'):
        ROW = ROWS[JOB]
        GUARD_ON, FASTER, NOTE = judge_guard(ROW['builtin_time'], ROW['hand_time'])   # 别改
        print('   ' + JOB + ' 手写 ' + fmt_seconds(ROW['hand_time']) + ' 秒 → 内置 '
              + fmt_seconds(ROW['builtin_time']) + ' 秒；'
              + ('判了' if GUARD_ON else '没判')
              + ('、过了' if FASTER else '、还没过') + '：' + NOTE)     # 别改
    print('   排序那一栏的倍率分两层看：绝大部分是复杂度（O(n^2) 对 O(n log n)），')   # 别改
    print('   只有一小部分是常数——它证明的是「别手写排序」，不是「内置快一千倍」。')      # 别改

    show_banner('0029 递归与迭代')
    show_line('n=900 递归求和', sum_rec(list(range(900))))        # 别改
    show_line('n=900 迭代求和', sum_iter(list(range(900))))       # 别改
    ARGS = list(range(900))
    ITER_PASSES = iteration_passes(ARGS)                                    # 别改
    # 这两格**用 floor=0 量**：要的就是那个真实的微秒数，别被守卫的地板截平。
    ITER_TIME, _ = median_seconds(lambda: sum_iter(ARGS), ITER_PASSES, 0.0)  # 别改
    REC_TIME, _ = median_seconds(lambda: sum_rec(ARGS), ITER_PASSES, 0.0)   # 别改
    show_line('n=900 迭代耗时', fmt_seconds(ITER_TIME) + ' 秒')    # 别改
    show_line('n=900 递归耗时', fmt_seconds(REC_TIME) + ' 秒')     # 别改
    print('   两版各跑 ' + str(ITER_PASSES) + ' 遍取中位数'
          + '（小段计时会被噪声盖住效应，跑够遍数才量得出来）')       # 别改
    print('   递归每层都要建一个栈帧，所以同样是 900 层，慢的那一版就是它；'
          '更硬的问题是它到不了任意深。')                            # 别改
    EDGE, EDGE_OK, NEXT_OK = recursion_probe()                     # 别改
    print('   n = ' + str(EDGE) + ' 递归版'
          + ('撑住了' if EDGE_OK else 'RecursionError'))            # 别改
    print('   n = ' + str(EDGE + 2) + ' 递归版'
          + ('撑住了' if NEXT_OK else 'RecursionError'))            # 别改
    show_line('递归的边界', EDGE)                                  # 别改
    print('   边界就卡在 ' + str(EDGE) + ' 与 ' + str(EDGE + 2)
          + ' 之间：默认上限 1000，主模块本身占一层；')                # 别改
    print('   多一层调用就少一层栈，所以这个数会跟着调用位置浮动几层。')      # 别改
    print('   深度跟着 n 长的递归一律改迭代——不只是慢，更要紧的是它到不了任意深。')   # 别改
