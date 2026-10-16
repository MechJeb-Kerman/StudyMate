"""tools.py · lab 0029 的公共工具（给好的，别改）

这一课要量的是**常数因子**：同一个量级下，写法不同能差出几百倍。量这件事有个陷阱——
**看时间会被噪声骗**。所以这个 lab 的判分采用两层证据：

    第一层（确定量）  「操作次数 / 调用次数 / 语句执行次数」——同一台机器、同一份数据，
                     每次都是同一个整数。判分核对的就是这些数。
    第二层（参考量）  耗时。只用来给学生看「快了多少」，判分只在**两边规模差出几十倍**的地方
                     拿它当辅助证据，而且一定带噪声容差与退化守卫（见 judge_guard）。

这里放的是**四道题必须用同一个口径**的那几样东西：

  1. LCG(seed) / sample_data(seed, n, keys)
     本课的数据造法。课件里那些数据是 random.Random(seed).randint(...) 造的，
     可那在自由线程版上每造一个数要 3.5 微秒，量常数因子时**造数据的钱比要量的钱还多**。
     所以这里换成一个线性同余发生器（LCG）：同样确定、同样「看着随机」，
     但一个数只要几十纳秒。四道题都用它，判分也用同一份——**种子一样，数据就一样**。

  2. DATA（任务 2 的数据）与 SEG（任务 1 的三段数据）
     参数就在下面这几个常量里。判分拿**另一组参数**造数据去试学生的函数，
     所以「把答案写死」在这四道题里都会露。

  3. SEGMENTS / SEG_ROLE / segment_ops_canonical
     任务 1 的三段是什么、各做多少次操作。操作次数是**算出来的**（由规模决定），
     不是计时出来的——这正是课件那句「定位瓶颈看次数，不看形状」。

  4. TIERS / canonical_count / canonical_trace
     任务 2 的四招优化（换容器 → 整体读入 → 提前算不变式 → 用内置）与它们的唯一口径。
     canonical_count 用**内置**实现（set + sum），canonical_trace 用**手写循环**实现，
     两个必须给出同一个答案——这就是「优化不许改答案」在代码里的样子。

  5. expect_answer / expect_times / expect_recursion_ceiling / recursion_edge
     任务 3 那几栏「和内置比」的期望值：答案、以及**这一栏两边各做多少次值访问**。
     倍率是参考，值访问次数是判据。
     expect_recursion_ceiling 与 recursion_edge 记的是**机制**（哪个 n 撑得住、
     哪个 n 已经 RecursionError），不是一个写死的 998——调用点深浅不同这个数会浮动。

  5b. canonical_answer_of
     任务 2 收尾那一格：按判分自己的参数算一遍「数组里出现过的键有几个」，
     用来核「改正之后不一致 0 组」这一条。它不吃脚本里那个数。

  6. count_matches / audit_cases / audit_run / audit_break
     任务 4 的对拍。count_matches 里的那句 `if i < n: ... v = values[i]` 就是
     「故意写错一次」的那个开关：n 写成 n - 1，最后一个元素就漏掉了，答案会小一点。

  7. judge_guard(t_optimized, t_baseline, floor=1e-4)
     耗时断言的**两层保护**：噪声容差（>= 0.75 倍）+ 退化守卫（基线太快就不判）。
     留白版的时间常常正好是 0.000000——没有守卫的话「0 跟 0 比」会变成掷硬币，
     分项计数会在两次运行之间抖动。

  8. PROBE_SENTINEL / probe_main_source(module)
     探针。判分**不读学生脚本自己打印的行**就下结论：它另起一个进程，
     import 学生的函数，拿**判分自己造的（与被测数据刻意不同的）**数据去试，
     最后打一行哨兵 + JSON 回来。模板在这里给好，四道题共用。

判分不 replace 这份文件里的任何东西来「帮你过」：它做的是**另算一遍**——
用自己的参数重新造数据、重新算期望值，再跟学生函数交回的东西对上。
所以只写 print、不写实现是过不去的。
"""

import heapq
import io
import json
import random
import time


# ── 1. 造数据：一个线性同余发生器 ────────────────────────────────────────

LCG_A = 1103515245
LCG_C = 12345
LCG_M = 2147483648          # 2 ** 31


class LCG:
    """课件那套 random.Random(seed).randint(0, 10**6) 的替身：一样确定，快 50 倍。

    自由线程版上每造一个数，random.Random 要 3.5 微秒，这个只要几十纳秒。
    量常数因子的时候，造数据的开销不能比要量的东西还大。
    """

    def __init__(self, seed):
        self.state = ((seed * LCG_A + LCG_C) % LCG_M) or 1

    def next_int(self, lo, hi):
        """交回 [lo, hi] 里的一个整数——同一对 (seed, 第几次调用) 永远交回同一个数。"""
        self.state = (self.state * LCG_A + LCG_C) % LCG_M
        span = hi - lo + 1
        return lo + (self.state >> 7) % span

    def make(self, count, lo, hi):
        out = []
        for _ in range(count):
            out.append(self.next_int(lo, hi))
        return out


def sample_data(seed, n, keys):
    """造 (数组, 键表) 两样：先造 n 个数组元素，再造 keys 个键——顺序就是随机流的顺序。"""
    rand = LCG(seed)
    arr = rand.make(n, 0, 1000000)
    wanted = rand.make(keys, 0, 1000000)
    return arr, wanted


def sum_of(values):
    """手写求和（这一课里它是「内置的对立面」，慢 4.8 倍那一版）。"""
    total = 0
    for value in values:
        total += value
    return total


# ── 2. 任务 1 与任务 2 的参数（判分拿另一组参数复算，别写死）──────────────

# 任务 1：三段各做一件事。2000 次「列表 in」在 20 万元素上要 1.9 秒，
# 那个规模放进 lab 太慢，这里按同样的形状缩小：比的是**形状**（次数关系），不是绝对秒数。
SEG = {'size': 60000, 'keys': 350, 'seed': 101, 'repeats': 3}

# 任务 2：四招优化。level 0 是「每个键扫一整条数组」，跑一次 0.1 秒上下。
DATA = {'size': 80000, 'keys': 400, 'seed': 7, 'repeats': 3}

# 判分自己用的那组参数（**刻意与上面不同**）：写死的答案在这里会露。
JUDGE_SEG = {'size': 23000, 'keys': 500, 'seed': 909}
JUDGE_DATA = {'size': 17000, 'keys': 250, 'seed': 515}

SEGMENTS = ['A_set', 'B_sort', 'C_in']
SEG_ROLE = {
    'A_set': '20 万个元素装进集合（看着最重）',
    'B_sort': '排序同一批元素',
    'C_in': '若干次「这个键在不在数组里」（看着最无害）',
}

# 任务 2 的四招，顺序就是课件里那四步。LEVELS 是每加到第几招的编号。
TIERS = [
    (0, '起点：列表 in + 逐行读入'),
    (1, '第 1 招：换容器（列表 in → 集合 in）'),
    (2, '第 2 招：整体读入（逐行 → 一次 read().split()）'),
    (3, '第 3 招：提前算不变式（集合提到循环外）'),
    (4, '第 4 招：用内置（手写循环 → sum + generator）'),
]
LEVELS = [level for level, _ in TIERS]


def tier_name(level):
    for number, name in TIERS:
        if number == level:
            return name
    return '（没有这一级）'


# ── 3. 操作次数的口径：算出来的，不是计时出来的 ──────────────────────────

def segment_ops_canonical(size, keys):
    """三段各做多少次操作（课件那张「不看形状，看次数」的表就按这个口径算）。

    A 段：一个元素一次操作 → size 次；
    B 段：排序要比较 nlogn 量级 → size * log2(size) 次（sort_work 那个数就这么来的）；
    C 段：列表的 in 是**线性扫描** → 一个键要扫过整条数组 → keys * size 次。

    这三行里只有 C 是「看着无害、算出来最吓人」的那个：它比 A 多 keys 倍。
    """
    bits = max(1, size.bit_length() - 1)          # log2 的整数下界
    return {
        'A_set': size,
        'B_sort': size * bits,
        'C_in': keys * size,
    }


def canonical_answer_of(size, keys, seed=7):
    """任务 2 那一组参数上「数组里出现过的键有几个」→ (答案, 键表长度)。

    判分拿这个核「改正之后不一致 0 组」那一格：**答案是从数据算出来的**，
    不是脚本里那个数。键表由数组自己派生（tools.key_table），两边口径一致。
    """
    arr, _wanted = sample_data(seed, size, keys)
    wanted = key_table(arr, keys)
    return canonical_count(arr, wanted), len(wanted)


def build_segments(size=60000, keys=350, seed=101):
    """任务 1 的三段各用哪份数据：三段**共用**同一个数组，C 段另有键表。

    共用一个数组是刻意的：三段量的都是同一批 20 万个元素，只有「怎么用」不同。
    """
    arr, wanted = sample_data(seed, size, keys)
    return {
        'A_set': (arr,),
        'B_sort': (arr,),
        'C_in': (arr, wanted, False),                  # 第三格：容器是不是集合
    }


# ── 4. 任务 2 的唯一口径：两个实现，一个答案 ─────────────────────────────

def canonical_count(arr, wanted):
    """**答案的唯一口径**：数组里出现过的键有几个（键表里去重之后再数）。

    用内置实现（set + sum + generator）写；canonical_trace 用手写循环写。
    两个必须交回同一个答案——这就是「优化不许改答案」。
    """
    seen = set(arr)
    return sum(1 for key in wanted if key in seen)


def canonical_trace(level, size=40000, keys=400, seed=7):
    """第 level 招之后，各做了多少次操作 → (循环次数, 相等比较次数, 读入调用次数)。

    这一串数是**确定量**：同一台机器上每次都是同一个整数，判分核对的就是它。
    耗时会被调度、被别的进程影响，次数不会——这正是本课要教的那件事。

    口径（四招各改掉了什么，看得很清楚）：

      第 0 级  手写循环里 `v = arr[i]`：每个键扫 n 次 → 循环次数 = keys * n
      第 1 招  容器换成集合：每个键一步 → 循环次数 = keys
      第 2 招  整体读入：逐行一次 → 一次 read() 调用，读入次数从 n 降到 1
      第 3 招  集合提到循环外：相等比较次数从 keys * n 降到 keys（第 2 级时
               循环次数已经降到 keys，可 `key in set(arr)` 每轮还在重建集合）
      第 4 招  手写计数换成 sum + generator：循环次数从 keys 降到 1
    """
    if level >= 4:
        loops = 1
    elif level >= 1:
        loops = keys
    else:
        loops = keys * size
    eq_ops = keys if level >= 3 else keys * size
    reads = 1 if level >= 2 else size
    return loops, eq_ops, reads


def canonical_trace_table(size=40000, keys=400, seed=7):
    """任务 2 那张表的唯一口径：{第几招: (循环次数, 相等比较次数, 读入调用次数)}。"""
    return {level: canonical_trace(level, size, keys, seed) for level in LEVELS}


# ── 5. 任务 3：四栏「和内置比」的期望值 ──────────────────────────────────

WORK_REPEATS = {
    'contain': 1,
    'sort': 3,
    'sum': 3,
    'min': 5,
    'role': 3,
}

WORK_SIZES = {
    'contain': {'arr': 100000, 'keys': 1200},
    'sort': {'n': 2500, 'k': 40},
    'sum': {'n': 300000},
    'min': {'n': 100000, 'k': 64},
    'role': {'n': 60000, 'keys': 40000},
}


def expect_answer(job, seed, sizes):
    """这一栏两边应该交回的同一个答案（优化不许改答案，内置也不许）。"""
    if job == 'contain':
        arr, wanted = sample_data(seed, sizes['arr'], sizes['keys'])
        return sum(1 for key in wanted if key in set(arr))
    if job == 'sort':
        rand = LCG(seed)
        values = rand.make(sizes['n'], 0, 1000000)
        return sorted(values)[:sizes['k']]
    if job == 'sum':
        rand = LCG(seed)
        values = rand.make(sizes['n'], -1000, 1000)
        return sum_of(values)
    if job == 'min':
        rand = LCG(seed)
        values = rand.make(sizes['n'], 0, 1000000000)
        return heapq.nsmallest(sizes['k'], values)[sizes['k'] - 1]
    if job == 'role':
        rand = LCG(seed)
        values = rand.make(sizes['n'], 0, 3)
        counts = [0] * 16
        for value in values:
            counts[(value * 5) % 16] += 1
        return counts
    return None


def expect_times(job, seed, sizes, repeats):
    """这一栏两边各做多少次**值访问** → (手写版, 内置版)。

    「值访问」= 真正读到一个元素的值。手写版每一轮 Python 都绕一圈，内置版在 C 里绕——
    差的就是这一层。次数差在哪，倍率就出在哪，判分核的是次数这一半。
    """
    if job == 'contain':
        arr, wanted = sample_data(seed, sizes['arr'], sizes['keys'])
        builtin = sum(1 for key in wanted if key in set(arr))       # 命中才读到值
        return sizes['keys'] * sizes['arr'], builtin
    if job == 'sort':
        # 冒泡每一对都比一次；Timsort 只在取 key 时读一次值，剩下在 C 里比。
        return sizes['n'] * (sizes['n'] - 1) // 2, sizes['n']
    if job == 'sum':
        return sizes['n'], sizes['n']
    if job == 'min':
        # 反复 min：每取一个都要把整条数组看一遍；nsmallest 每个元素只看一次。
        return sizes['n'] * WORK_REPEATS['min'], sizes['n']
    if job == 'role':
        # 16 个桶的 if/elif 链：落在后面的桶平均要比 8 次；查表一个值只取出来一次。
        return sizes['n'] * 8, sizes['n']
    return None, None


# ── 5b. 任务 3 的递归那两栏：机制，不是一个写死的数 ─────────────────────

def _recursive_total(values, index):
    """与任务 3 的 sum_rec 同形：一层一层加下去，深度跟着 n 长。"""
    if index == len(values):
        return 0
    return values[index] + _recursive_total(values, index + 1)


def expect_recursion_ceiling(n):
    """判分自己在**同一个位置**上试一遍：交回和，撑不住就交回 None。

    与任务 3 里那个 recursion_ceiling 的**层数一样**（两边都是「一层包装 + 一递归」），
    所以同样的 n 应该得到同样的结论。**核的是机制**（哪个 n 撑得住、哪个不行），
    不是一个写死的 998——调用点多一层少一层，这个数就会跟着浮动。
    """
    try:
        return _recursive_total(list(range(n)), 0)
    except RecursionError:
        return None


def recursion_edge(high=1500):
    """判分自己二分一遍：最大的那个「还撑得住」的 n（本机 998 上下）。"""
    lo, hi = 1, int(high)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if expect_recursion_ceiling(mid) is None:
            hi = mid - 1
        else:
            lo = mid
    return lo


# ── 6. 任务 4：对拍那套 ─────────────────────────────────────────────────

AUDIT = {'cases': 50, 'size': 40, 'value_hi': 6, 'low': 3, 'high': 6, 'seed': 2029}


def count_matches(values, lo, hi, broken=False):
    """数一数 values 里有几个落在 [lo, hi] 里。broken=True 时**故意写错一次**。

    错法就是课件那个：把循环条件写成 `i < n - 1` 而不是 `i < n`——最后**一个**元素不看了。
    只有一个元素的数组，答案会直接变成 0：错得不多，但已经错了。

    这段代码长得跟「对的那个」几乎一模一样，肉眼几乎看不出来——
    这正是它值得当例子的原因：**改一处都要回验**，靠看是看不住的。
    """
    counts = [0, 0, 0, 0]
    n = len(values)
    stop = n - 1 if broken else n
    i = 0
    while i < stop:
        v = values[i]
        counts[v % 4] += 1
        i += 1
    low = 1 if lo <= 0 else 0
    high = 2 if hi >= 3 else 1
    return counts[low] + counts[high]


def audit_cases(count=50, size=40, value_hi=6, seed=2029):
    """造 count 组随机数据（种子钉死 → 每组数据每次都一样）。"""
    rand = LCG(seed)
    cases = []
    for _ in range(count):
        length = rand.next_int(1, size)
        cases.append(rand.make(length, 0, value_hi))
    return cases


def audit_run(cases, low=3, high=6, broken=False):
    """把每一组数据分别交给「对的那个」和「坏的那个」，数有几组对不上。

    交回 (对的那版答案, 坏的那版答案, 对不上的组数, 第一组对不上的证据)。
    证据那一格是 (数组, 对的答案, 坏的答案)；全都对得上时是 None。
    """
    right_total = 0
    wrong_total = 0
    misses = 0
    evidence = None
    for case in cases:
        right = count_matches(case, low, high, False)
        wrong = count_matches(case, low, high, broken)
        right_total += right
        wrong_total += wrong
        if right != wrong:
            misses += 1
            if evidence is None:
                evidence = (list(case), right, wrong)
    return right_total, wrong_total, misses, evidence


def audit_break(cases, low=3, high=6):
    """坏的那一版跑一遍，交回一句「抓到没有」的结论 (抓到吗, 对不上的组数, 证据)。"""
    _right, _wrong, misses, evidence = audit_run(cases, low, high, True)
    return misses > 0, misses, evidence


def audit_pair(cases, low=3, high=6, broken=False):
    """对拍结果归成一个字典（判分按这几个键取值）。"""
    right, wrong, misses, evidence = audit_run(cases, low, high, broken)
    return {
        'cases': len(cases),
        'right': right,
        'wrong': wrong,
        'misses': misses,
        'same': misses == 0,
        'evidence': evidence,
    }


def audit_fixed(seed=None, count=None):
    """**修好之后**再对拍一次：交回 (对不上的组数, 总组数)。固定种子 → 确定值。"""
    seed = AUDIT['seed'] if seed is None else seed
    count = AUDIT['cases'] if count is None else count
    cases = audit_cases(count, AUDIT['size'], AUDIT['value_hi'], seed)
    _right, _wrong, misses, _evidence = audit_run(
        cases, AUDIT['low'], AUDIT['high'], False)
    return misses, len(cases)


def key_table(values, keys):
    """从**正在处理的那条数组**里取出一张键表：每隔一段挑一个，凑够 keys 个。

    任务 2 的键表必须由那一段数据本身决定——这样「答案」才与数据绑在一起，
    判分换成另一组数据时答案会跟着变（把答案写死的会立刻露）。
    判分算期望值时用的是同一个函数，所以两边口径一致。
    """
    step = max(1, len(values) // max(1, keys))
    return values[::step][:keys]


# ── 7. 耗时断言的两层保护 ───────────────────────────────────────────────

# 噪声容差：优化版的中位数只要落在「基线的 0.75 倍」以内就算它快，
# 不去核具体倍数——这一课的倍率在 1.06 到 230 之间浮动，核死会误伤。
NOISE = 0.75
# 退化守卫：基线快到 1e-4 秒以内，这一条就不判（留白版的占位时间常常正好是 0.000000，
# 「0 跟 0 比」是掷硬币，不是证据）。
FLOOR = 1e-4


def judge_guard(t_optimized, t_baseline, floor=FLOOR, noise=NOISE):
    """→ (要不要判这一条, 判的话过不过, 一句人话)。两层保护都在这里。

    第一层：基线太小（含占位值 0.0）→ 不判。这一条只写「跳过」，不算失败。
    第二层：过了守卫才比，而且给 25% 的噪声余量。
    """
    if not isinstance(t_baseline, (int, float)) or t_baseline < floor:
        return False, True, ('基线只有 ' + fmt_seconds(t_baseline)
                             + ' 秒（退化守卫：小于 ' + fmt_seconds(floor)
                             + ' 秒不判）——这一条只当参考')
    factor = t_optimized / t_baseline
    if factor <= noise:
        return True, True, ('优化版 ' + fmt_seconds(t_optimized) + ' 秒，基线 '
                            + fmt_seconds(t_baseline) + ' 秒，快 '
                            + format(1.0 / factor if factor else float('inf'), '.1f')
                            + ' 倍（噪声容差 ' + str(noise) + '）')
    return True, False, ('优化版 ' + fmt_seconds(t_optimized) + ' 秒 vs 基线 '
                         + fmt_seconds(t_baseline) + ' 秒：比值 ' + format(factor, '.2f')
                         + '，期望 <= ' + str(noise))


def fmt_seconds(seconds):
    """把秒数写成 0.000000 的样子（脚本打印的就是这个格式）。"""
    try:
        return format(float(seconds), '.6f')
    except (TypeError, ValueError):
        return '0.000000'


def median_seconds(callable_thing, repeats=3, floor=FLOOR):
    """跑 repeats 次取中位数 → (中位数秒数, 最后一次的返回值)。

    中位数是课件的口径：单次计时会被调度和别的进程影响，本课第一次量全局名时
    就是被噪声盖住了效应（量出 1.00）。
    """
    reps = max(1, int(repeats))
    samples = []
    answer = None
    for _ in range(reps):
        start = time.perf_counter()
        answer = callable_thing()
        samples.append(time.perf_counter() - start)
    samples.sort()
    middle = samples[len(samples) // 2]
    if len(samples) > 1 and len(samples) % 2 == 0:
        middle = (samples[len(samples) // 2 - 1] + samples[len(samples) // 2]) / 2.0
    return max(middle, floor), answer


def count_key_calls(values):
    """数一数开一个 key 函数给排序/prepare 用 → (排好的表, key 被调了几次)。

    计数器是一个**可调用对象**，它只增加一个整数、不碰数据——所以「排出来的表」
    与直接调用 Timsort 一模一样，多出来的只有「数了多少次」。
    判分用这个数分开「真调了内置」与「把答案抄出来了」。
    """
    box = {'calls': 0}

    class Counter:
        def __call__(self, value):
            box['calls'] += 1
            return value

    return sorted(values, key=Counter()), box['calls']


# ── 8. 打印统一走这里 ───────────────────────────────────────────────────

def show_banner(title):
    """打印一行小节标题，四个任务的脚本都用它开头。"""
    print('== ' + title + ' ==')


def show_line(label, value):
    """打印一行「标签 值」，判分按标签取。"""
    print(label + ' ' + str(value))


def read_all_text(text):
    """整体读入的样子：一次 read() 把整份文本拿回来（真代码这里是 sys.stdin.buffer.read()）。"""
    return io.StringIO(text).read()


def read_head_line(text):
    """逐行读入的第一个整数（真代码这里是 int(input())）——**每行调一次**这个函数。"""
    return int(io.StringIO(text).readline())


def input_text(arr):
    """把一个数组摊成「一行一个数」的文本（模拟题目给的输入）。"""
    return ''.join(str(value) + '\n' for value in arr)


class ReadCounter:
    """把「怎么读」包起来，并数一数各被调了几次。

    任务 2 的四级读入就用它：逐行读是 size 次调用、整体读是 1 次调用——
    同一个答案，调用次数差三个数量级。这就是课件「输入输出最便宜」那一节。

    接口就两个（判分第 2 层数的就是它）：

        read_all(text)   整体读：一次把整段文本交回来（真代码 sys.stdin.buffer.read()）
        next_number()    逐行读：一次交回**下一行**的那个整数（真代码 int(input())）
    """

    def __init__(self, read_all=None, read_line=None):
        self.read_all_impl = read_all or read_all_text
        self.read_line_impl = read_line or read_head_line
        self.text = ''
        self.lines = None
        self.cycle = 0
        self.calls = {'all': 0, 'line': 0}

    def load(self, text):
        """把这一次要读的那段文本交给它（相当于「题目给的输入」）。"""
        self.text = text
        self.lines = None
        self.cycle = 0
        return self

    def read_all(self, text=None):
        """整体读：一次调用，把整段交回来。"""
        self.calls['all'] += 1
        return self.read_all_impl(self.text if text is None else text)

    def next_number(self):
        """逐行读：一次调用，交回下一行那个整数（游标往前走一格）。

        文本读完了就**从头绕回去**：判分给的那段文本可能比 size 短
        （它只想数「被调了几次」，不想造 size 行文本），绕回去才能让
        「逐行读 size 次」这件事真的发生，而不是半路 StopIteration。
        """
        self.calls['line'] += 1
        if self.lines is None:
            self.lines = iter(self.text.splitlines())
        try:
            return self.read_line_impl(next(self.lines))
        except StopIteration:
            self.cycle += 1
            self.lines = iter(self.text.splitlines())
            return self.read_line_impl(next(self.lines))

    def total(self):
        """一共读了几次（整体读 + 逐行读）。"""
        return self.calls['all'] + self.calls['line']


# ── 9. 探针：判分另起一个进程 import 学生的函数 ───────────────────────────

# 探针打回来的那一行以它开头，判分只读最后一行带哨兵的输出。
PROBE_SENTINEL = '::PROBE_JSON::'

# 每个任务文件要有哪几个函数——四道缝各自独立，某一个文件坏了只有它那一层报载入失败。
# 这几个名字都是**判分接口**：改名 / 删掉都会点名。
PROBE_INTERFACE = {
    'task1_bottleneck': ['segment_ops', 'analyze_segments',
                         'segment_list_in', 'segment_set_in',
                         'count_size_calls', 'count_between'],
    'task2_tuning': ['optimization_steps', 'tier_steps', 'solve_tier',
                     'tier_times', 'audit_answers'],
    'task3_builtin': ['compare_with_builtin', 'layer_of',
                      'recursion_ceiling', 'recursion_probe'],
    'task4_break_it': ['audit_broken_once', 'audit', 'count_matches',
                       'audit_after_fix'],
}


def probe_module_source(module, sizes=None, seed=None):
    """交回探针脚本的源码文本（判分把它写成一个临时文件再跑）。

    模板按 `.format()` 走，所以正文里的花括号一律写成两对——**源码里不许出现
    连续三个反引号**，这个模板里也一个都没有。

    注意两个 `{sizes}` / `{seed}` 占位：正文里写的就是**一个值**（不是 `!r`），
    所以替进去的必须是 `repr(...)` 之后的**文本**——写成 `repr(dict(...))`
    会得到 `SIZES = "{'size': …}"`（一个字符串），探针一进门就
    `TypeError: string indices must be integers`。这一行踩过一次，别改回去。
    """
    if sizes is None:
        sizes = {}
    return PROBE_TEMPLATE.format(module=module, sentinel=PROBE_SENTINEL,
                                 sizes=str(dict(sizes)), seed=str(seed))


# 探针正文。{module} 是学生那个任务文件的模块名，{sentinel} 是哨兵的写法，
# {sizes} 与 {seed} 是**判分自己的**那组参数（与学生脚本里跑的那组刻意不同）。
PROBE_TEMPLATE = '''"""判分探针 · 另起一个进程 import 学生的函数，拿判分自己的数据试。

    py probe.py <学生任务文件所在目录>

只打一行带哨兵的 JSON 回来（前面那两行 START/END 是给人看的，判分只读最后一行）。
"""
import importlib
import json
import sys
import traceback

MODULE = {module!r}
SENTINEL = {sentinel!r}
SIZES = {sizes}
SEED = {seed}
AUDIT_SEED = SIZES['seed']
LEVELS = [0, 1, 2, 3, 4]
JOBS = ['contain', 'sort', 'sum', 'min', 'role']


def emit(record):
    sys.stdout.write(SENTINEL + json.dumps(record, ensure_ascii=False,
                                          default=str) + '\\n')


class Reader:
    """会记账的读入器（判分探针自己的一份，接口与 tools.ReadCounter 一样）。

    `read_all` 交回整段文本、`next_number` 交回下一行那个整数——各被调一次算一次读入。
    """

    def __init__(self, text):
        self.text = text
        self.lines = None
        self.cycle = 0
        self.calls = {{'all': 0, 'line': 0}}

    def load(self, text):
        self.text = text
        self.lines = None
        self.cycle = 0
        return self

    def read_all(self, text=None):
        self.calls['all'] += 1
        return self.text if text is None else text

    def next_number(self):
        """逐行读：一次调用交回下一行那个整数。

        文本读完了就**从头绕回去**——判分给的那段文本可能比 size 短
        （它只想数「被调了几次」，不想造 size 行文本），
        绕回去才能让「逐行读 size 次」这件事真的发生，而不是半路 StopIteration。
        """
        self.calls['line'] += 1
        if self.lines is None:
            self.lines = iter(self.text.splitlines())
        try:
            return int(next(self.lines))
        except StopIteration:
            self.cycle += 1
            self.lines = iter(self.text.splitlines())
            return int(next(self.lines))

    def total(self):
        return self.calls['all'] + self.calls['line']


def number(value):
    """把学生交回的数字归成 int / None（字符串数字也认）。"""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return None
    return None


def safe(label, func, *args, **kwargs):
    """调一次学生函数：出错就记成 'ERR 类型: 说明'，别让探针自己崩。"""
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        return 'ERR ' + label + ': ' + type(exc).__name__ + ': ' + str(exc)


def run():
    importlib.import_module('tools')
    task = importlib.import_module(MODULE)
    from tools import (LCG, PROBE_INTERFACE, audit_cases, audit_pair,
                       canonical_count, canonical_trace_table, median_seconds,
                       sample_data)

    record = {{'module': MODULE,
              'file': getattr(task, '__file__', ''),
              'missing': [name for name in PROBE_INTERFACE[MODULE]
                          if not callable(getattr(task, name, None))]}}

    # ── 任务 1：三段的操作次数 + 容器对照 + size() 调用次数 ─────────────
    if callable(getattr(task, 'segment_ops', None)):
        # 只传 (size, keys)：这个函数的签名就是这两个规模参数，种子与它无关。
        record['seg_ops'] = safe('segment_ops', task.segment_ops,
                                 SIZES['size'], SIZES['keys'])
    if callable(getattr(task, 'analyze_segments', None)):
        times = dict((name, 0.0) for name in ('A_set', 'B_sort', 'C_in'))
        times['C_in'] = 0.25                    # 判分自己给的一组实测值
        found = safe('analyze_segments', task.analyze_segments, times)
        if isinstance(found, dict):
            record['analyze'] = {{'slower_true': found.get('slower_true'),
                                 'slower_guess': found.get('slower_guess'),
                                 'ops': found.get('ops')}}
        else:
            record['analyze'] = found
    if callable(getattr(task, 'segment_list_in', None)) and callable(
            getattr(task, 'segment_set_in', None)):
        arr, wanted = sample_data(SEED, SIZES['size'], SIZES['keys'])
        t_list, hit_list = median_seconds(
            lambda: safe('segment_list_in', task.segment_list_in, arr, wanted), 1)
        t_set, hit_set = median_seconds(
            lambda: safe('segment_set_in', task.segment_set_in, arr, wanted), 1)
        record['seg_times'] = {{'list': t_list, 'set': t_set,
                               'hit_list': number(hit_list),
                               'hit_set': number(hit_set)}}
    if callable(getattr(task, 'count_size_calls', None)):
        record['size_calls'] = safe('count_size_calls', task.count_size_calls,
                                    SIZES.get('n', 1234))
    if callable(getattr(task, 'count_between', None)):
        record['between'] = safe('count_between', task.count_between,
                                 SIZES.get('n', 1234))

    # ── 任务 2：四招的名字、每一级四格计数、每一级的答案 ────────────────
    if callable(getattr(task, 'optimization_steps', None)):
        record['steps'] = safe('optimization_steps', task.optimization_steps)
    if callable(getattr(task, 'tier_steps', None)):
        counts = {{}}
        reads = {{}}
        for level in LEVELS:
            reader = Reader('0\\n')
            got = safe('tier_steps', task.tier_steps, level, SIZES['size'],
                       SIZES['keys'], SIZES['seed'], reader)
            if isinstance(got, (list, tuple)):
                counts[str(level)] = [number(cell) for cell in got[:4]]
            else:
                counts[str(level)] = got
            reads[str(level)] = dict(reader.calls)
        record['counts'] = counts
        record['reads'] = reads
        record['canonical_counts'] = {{
            str(level): list(canonical_trace_table(SIZES['size'], SIZES['keys'],
                                                   SIZES['seed'])[level])
            for level in LEVELS}}
    if callable(getattr(task, 'solve_tier', None)):
        answers = {{}}
        arr = LCG(SEED + 1).make(400, 0, 50)
        wanted = LCG(SEED + 2).make(60, 0, 50)
        text = ''.join(str(value) + '\\n' for value in arr)
        for level in LEVELS:
            reader = Reader(text)
            answers[str(level)] = safe(
                'solve_tier', task.solve_tier, level, 400, 60, SEED + 2, text,
                reader)
        record['answers'] = answers
        record['canonical_answer'] = canonical_count(arr, wanted)
    if callable(getattr(task, 'tier_times', None)):
        record['times'] = safe('tier_times', task.tier_times, SIZES['size'],
                               SIZES['seed'], 1)
    if callable(getattr(task, 'audit_answers', None)):
        record['audit_answers'] = safe('audit_answers', task.audit_answers,
                                       SIZES['size'], SIZES['keys'], SIZES['seed'])

    # ── 任务 3：五栏「和内置比」+ 递归上限 ───────────────────────────────
    if callable(getattr(task, 'compare_with_builtin', None)):
        table = {{}}
        for job in JOBS:
            row = safe('compare_with_builtin', task.compare_with_builtin, job, SEED)
            if isinstance(row, dict):
                table[job] = dict((key, row.get(key)) for key in
                                  ('answer', 'hand', 'builtin', 'hand_work',
                                   'builtin_work', 'hand_time', 'builtin_time',
                                   'layer'))
            else:
                table[job] = row
        record['compare'] = table
    if callable(getattr(task, 'layer_of', None)):
        record['layers'] = {{}}
        for job in JOBS:
            record['layers'][job] = safe('layer_of', task.layer_of, job)
    if callable(getattr(task, 'recursion_ceiling', None)):
        record['ceiling'] = [number(safe('recursion_ceiling',
                                         task.recursion_ceiling, n))
                             for n in (200, 400, 700)]
    if callable(getattr(task, 'recursion_probe', None)):
        got = safe('recursion_probe', task.recursion_probe)
        record['depth'] = got

    # ── 任务 4：对拍（判分自己造一组数据，broken 与 fixed 两遍）─────────
    # 这一格用的种子是**判分传进来的**那个（SIZES['seed']），不借用任务文件里的
    # SEED——判分那边就是按同一个数另算一遍 `audit_cases(9, 12, 6, 种子)` 来对账的。
    if callable(getattr(task, 'audit_broken_once', None)):
        record['audit'] = safe('audit_broken_once', task.audit_broken_once)
    if callable(getattr(task, 'count_matches', None)):
        record['probe_count'] = {{}}
        probes = [([1, 2, 3], 0, 3), ([], 0, 3), ([2], 0, 3),
                  ([0, 1, 2, 3, 4, 5], 3, 6), ([3], 3, 3)]
        for index, (values, lo, hi) in enumerate(probes):
            right = safe('count_matches', task.count_matches, values, lo, hi, False)
            wrong = safe('count_matches', task.count_matches, values, lo, hi, True)
            record['probe_count'][str(index)] = {{'values': values, 'lo': lo,
                                                  'hi': hi, 'right': right,
                                                  'wrong': wrong}}
    if callable(getattr(task, 'audit', None)):
        cases = audit_cases(9, 12, 6, AUDIT_SEED)
        record['audit_probe'] = audit_pair(cases, 3, 6, True)
        record['audit_probe_fixed'] = audit_pair(cases, 3, 6, False)
    if callable(getattr(task, 'audit_after_fix', None)):
        record['after_fix'] = safe('audit_after_fix', task.audit_after_fix)
    return record


if __name__ == '__main__':
    sys.path.insert(0, sys.argv[1])
    try:
        payload = run()
    except Exception:
        payload = {{'error': traceback.format_exc()}}
    emit(payload)
'''
