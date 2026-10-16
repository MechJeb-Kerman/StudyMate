"""任务 3 · 和内置实现比一次（lab 0029）

上一段把写法优化了一遍，这一段换个问法：**优化完的写法，和内置还差多远？**

课件那一节有两条看起来很像、其实不同的结论：

    求和   手写 for 循环 vs sum        快几倍        ← 差的是**循环那一层**
    排序   手写冒泡    vs sorted      快上千倍      ← 绝大部分是**复杂度**，
                                                    只有一小部分是常数

加起来的倍率很好看，但「差在哪一层」才是要写下来的东西。所以每一栏都交回：
两边交回的答案（必须一样）、两边各做多少次「值访问」、以及差在哪一层。

**「值访问」是这一段的主判据**：真正读到一个元素的值算一次。手写版每一轮 Python
都要绕一圈（FOR_ITER + 加法 + STORE_FAST），内置版在 C 里绕——差的就是这一层。
次数是确定量，倍率是参考量。

接口：文件名、函数名、带 print 的行都是判分接口，别改；要写的是六个 TODO：

    TODO 1  compare_with_builtin   一栏跑完，交回那一整行的八个键
    TODO 2  compute_answer         这一栏两边应该交回的同一个答案（独立算一遍）
    TODO 3  work_of                这一栏这一边做多少次值访问（按规模算出来的）
    TODO 4  recursion_ceiling      递归求和撑得住交回和、撑不住交回 None
    TODO 5  recursion_probe        贴着边界试两步 → [边界 n, 撑得住吗, 再顶一层呢]
    TODO 6  distance               两个答案差多远（不是数字就按一样 / 不一样）

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


def make_job(job, seed, sizes=None, repeats=None):
    """造这一栏要用的数据与两个函数 → (手写版, 内置版, 这一栏跑几遍)。

    两边的数据是**同一份**——两个版本除了要比的那一点，别的地方真的一样吗？
    这一段要量的是「循环那一层」「查找那一层」这些差别，所以两边必须严格可比。
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


# ══ TODO 1 ═════════════════════════════════════════════════
# compare_with_builtin(job, seed=4242, sizes=None, repeats=None)：跑一栏，交回一个字典
# （这八个键是判分接口，别改）：
#
#     answer        这一栏两边**应该**交回的答案：compute_answer(job, seed, sizes)
#     hand          手写版交回的答案        ┐ 两个都要与 answer 一致
#     builtin       内置版交回的答案        ┘
#     hand_work     手写版做多少次值访问    ┐ 都由 work_of(...) 按规模算出来
#     builtin_work  内置版做多少次值访问    ┘
#     hand_time     手写版的耗时（中位数）  ┐ 只当参考
#     builtin_time  内置版的耗时（中位数）  ┘
#     layer         这一栏差在哪一层：layer_of(job)
#
# 骨架（那一栏的两个函数与遍数由 make_job 给好）：
#
#     hand, builtin, reps = make_job(job, seed, sizes, repeats)
#     hand_time, hand_answer = median_seconds(hand, reps)
#     builtin_time, builtin_answer = median_seconds(builtin, reps)
#     ...
#
# **两边的答案必须一样**：不一样就说明这一栏的「两个版本」其实是两件事，
# 量出来的倍率再好看也没意义。判分三处都核：answer、hand、builtin 要互相对得上。
def compare_with_builtin(job, seed=4242, sizes=None, repeats=None):
    return {'answer': None, 'hand': None, 'builtin': None,
            'hand_work': 0, 'builtin_work': 0,
            'hand_time': 0.0, 'builtin_time': 0.0, 'layer': layer_of(job)}


# ══ TODO 2 ═════════════════════════════════════════════════
# compute_answer(job, seed=4242, sizes=None)：这一栏两边应该交回的**同一个答案**。
#
# 独立算一遍，不经过那两个函数——判分拿它当尺子。五栏各算什么：
#
#     contain  数组里有几个键出现过：sum(1 for key in wanted if key in set(arr))
#              （arr, wanted = sample_data(seed, sizes['arr'], sizes['keys'])）
#     sort     排序后**最小的一小撮**：sorted(值表)[:sizes['k']]
#     sum      所有元素的和：sum_of(值表)
#     min      第 k 小的那个（k 从 1 数起）：heapq.nsmallest(k, 值表)[k - 1]
#     role     16 个桶各多少个：(value * 5) % 16 落哪个桶
#
# 值表都用 `LCG(seed).make(n, lo, hi)` 造，上下界与 make_job 里那份保持一致
# （求和的元素可以是负的：-1000 到 1000）。
def compute_answer(job, seed=4242, sizes=None):
    sizes = dict(WORK_SIZES[job] if sizes is None else sizes)
    if job == 'contain':
        return 0
    if job == 'sort':
        return []
    if job == 'sum':
        return 0
    if job == 'min':
        return 0
    if job == 'role':
        return [0] * 16
    raise ValueError('没有这一栏：' + str(job))


# ══ TODO 3 ═════════════════════════════════════════════════
# work_of(job, seed, sizes, side)：这一栏这一边做多少次「值访问」——**按规模算出来**，
# 不是计时出来的。side 是 'hand' 或 'builtin'。
#
# 真正读到一个元素的值算一次。五栏的口径：
#
#     contain  手写：最坏情况一个键看完整条数组 → sizes['keys'] * sizes['arr']
#              内置：命中才真正读到值     → sum(1 for key in wanted if key in set(arr))
#     sort     手写：冒泡每一对都比一次   → n * (n - 1) // 2
#              内置：Timsort 取 key 只读一次值 → n
#     sum      两边都是 n（一个元素读一次）——差的是**谁在绕这个循环**
#     min      手写：每取一个都要扫一遍全表 → n * WORK_REPEATS['min']
#              内置：nsmallest 每个元素只看一次 → n
#     role     手写：落在最后的桶平均比 8 次 → n * 8
#              内置：查表一个值只取出来一次   → n
#
# 这几个数都是确定量，判分拿自己的规模复算一遍。
def work_of(job, seed, sizes, side):
    return 0


def sum_rec(values, i=0):
    """递归求和。**深度跟着 n 长的递归一律改迭代**——不只是慢几倍，
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


# ══ TODO 4 ═════════════════════════════════════════════════
# recursion_ceiling(n)：递归求和能不能撑到 n 层：撑得住交回**和**，撑不住交回 **None**。
#
#     try:
#         return sum_rec(list(range(n)))
#     except RecursionError:
#         return None
#
# 为什么用它做判据：递归的边界不是一个固定的数（默认上限 1000，主模块本身占一层，
# 你在第几层调用还会再吃掉几层）。**记住的是机制**——「有个 n 撑得住、
# 再往上就不行了」——不是一个写死的 998。判分在**同一个位置上**另试一遍同样的 n。
def recursion_ceiling(n):
    return None


def recursion_edge(high=1500):
    """二分找出边界：最大的那个「还撑得住」的 n（**给好的，别改**）。

    这本机实测在 998 上下：默认上限 1000，主模块本身占一层。
    这个数会随调用深度与 Python 版本浮动，所以判分核的是**机制**
    ——边界那个 n 撑得住、再往上就不行——而不是那个具体的数。
    """
    lo, hi = 1, int(high)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if recursion_ceiling(mid) is None:
            hi = mid - 1
        else:
            lo = mid
    return lo


# ══ TODO 5 ═════════════════════════════════════════════════
# recursion_probe()：贴着边界试两步 → [边界 n, 边界撑得住吗, 再往上顶一层还撑得住吗]。
#
# 交回**三格的表**（判分就认这三格）：
#
#     edge = recursion_edge()              # 最大的那个「还撑得住」的 n（二分找）
#     return [edge, recursion_ceiling(edge) is not None,
#             recursion_ceiling(edge + 2) is not None]
#
# 为什么第二探是 `edge + 2` 而不是 `edge + 1`：多一层调用就少一层栈，
# 拿同一个 n 去问「再深一层」时会差一格。这里要证明的是**机制**
# ——「有个 n 撑得住、再往上就不行了」——差一格是量法的事，不是结论的事。
#
# recursion_edge(high=1500) 也在这个文件里（二分，已经给好了），别改它。
def recursion_probe():
    return [0, True, False]


def brief(value, limit=4):
    """打印用：长表只留前几个，后面写成「… 共 N 个」。"""
    if isinstance(value, (list, tuple)):
        shown = list(value)[:limit]
        return str(shown) + ' … 共 ' + str(len(value)) + ' 个'
    return str(value)


# ══ TODO 6 ═════════════════════════════════════════════════
# distance(hand, builtin)：两个答案差多远。
#
#     · 一样 → 0
#     · 都是数字 → abs(hand - builtin)
#     · 其它（表、字符串…）→ 1（等价于「不一样」）
#
# 「优化不许改答案」在代码里就是这一句：四种写法交回的答案必须逐字一致。
def distance(hand, builtin):
    return 0


def iteration_passes(values, floor=FLOOR, cap=256, probe_reps=32):
    """决定「迭代版跑几遍」：跑到中位数能被量出来为止。

    小段计时会被噪声盖住效应，跑一遍量不出东西。这里先估一估一遍要多久，
    再把「每次计时都跑够 floor 秒」折成遍数，最多 cap 遍。
    **这一格是「让秒数可量」用的，不是判据。**
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
