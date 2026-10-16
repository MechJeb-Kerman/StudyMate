"""任务 2 · 依次上三到四招，每招都留记录（lab 0029）· 参考解

课件要的顺序是：**换容器 → 整体读入 → 提前算不变式 → 用内置**。
顺序不是随便排的：换容器省 23000%，抠语法省 10%，先把钱大的做掉。

    第 0 级  起点：列表 in + 逐行读入                    ← 能算对，就是慢
    第 1 招  换容器：列表 in → 集合 in                    ← 这一招最值钱
    第 2 招  整体读入：逐行 → 一次 read().split()          ← 最便宜的一招
    第 3 招  提前算不变式：集合提到循环外面                 ← 每轮少建一次容器
    第 4 招  用内置：手写循环 → sum + generator            ← 循环搬进 C 层

**每一招之后都要回验答案。** 这一段把「答案」也当成一格数据打出来（`答案 N 级`），
就是让回验这件事长出眼睛看得见的样子：四招上完，答案必须还是同一个数。

课件那两个数量级差在这里都能看见（括号里是判分核对的**确定量**）：

    换容器     第 0 级每个键扫一整条数组 → 第 1 级每个键一步（循环次数 1600 万 → 400）
    整体读入   逐行一次 → 一次读完（读入调用 size 次 → 1 次）
    提前不变式 第 2 级每轮都在重建集合（建集合 keys 次）→ 提到循环外（1 次）
    用内置     手写的计数循环（keys 次）→ sum + generator（1 次）

判分核对的是上面那四格**次数**，外加「四级答案一致」；耗时只在换容器那一处参考着看，
而且带噪声容差与退化守卫——不留白版那个占位值 0.000000 当证据用。

跑： py task2_tuning.py
判： py run_tests.py
"""

from tools import (DATA, LEVELS, ReadCounter, TIERS, canonical_count,
                   fmt_seconds, input_text, judge_guard, key_table,
                   median_seconds, sample_data, show_banner, show_line)

# 这个数组里不该被数进去的那个值（题目里的「坏值」）。它只影响答案，不影响次数。
IGNORE = -1


def optimization_steps():
    """四招的名字，一级一条（判分逐条核对）。"""
    return list(TIERS)


def make_reader(text='', read_all=None, read_line=None):
    """造一个会记账的读入器：整体读被调一次、逐行读被调一次，都记在 calls 里。

    真代码里逐行读是 int(input())，整体读是 sys.stdin.buffer.read().split()；
    这里把它们当成可替换的两条路传进来，就既跑得动、又数得清调了几次、
    还真的读得出数据（逐行读那一条带游标，每调一次交回下一行）。
    """
    return ReadCounter(read_all, read_line).load(text)


def tier_steps(level, size=DATA['size'], keys=DATA['keys'], seed=DATA['seed'],
               reader=None):
    """第 level 招之后各做了多少次操作 → (循环次数, 相等比较次数, 读入次数, 建集合次数)。

    **这四格是确定量**：同一台机器上每次都是同一个整数。课件说「定位瓶颈看次数，
    不看形状」——判分核的就是这四格，耗时只在容器那一处参考着看。

    口径（四招各改掉了什么，一格一格看得很清楚）：

      第 0 级  手写循环里的 `in`：容器是列表，每个键要扫 n 次 → 循环次数 = keys * n
      第 1 招  容器换成集合：每个键一步 → 循环次数 = keys（相等的比较也降到 keys）
      第 2 招  整体读入：逐行一次 → 一次读入调用，读入次数从 size 降到 1
      第 3 招  集合提到循环外：第 2 级每轮都还在重建集合（建集合 keys 次），
               提到外面之后建集合只有 1 次
      第 4 招  手写计数换成 sum + generator：循环次数从 keys 降到 1

    传了 reader 就**真的读一遍**（读入次数那一格由 reader 自己记账，是真调出来的），
    这样这一格既是本级的结论，又是可复核的证据。
    """
    size = int(size)
    keys = int(keys)
    if level >= 4:
        loops = 1                       # sum 的循环搬进 C 层，Python 层一轮不绕
    elif level >= 1:
        loops = keys                    # 每个键一步
    else:
        loops = keys * size             # 每个键扫一整条数组
    eq_ops = keys if level >= 3 else keys * size
    reads = 1 if level >= 2 else size
    builds = keys if level == 2 else 1
    if reader is not None:
        if level >= 2:
            reader.read_all()
        else:
            for _ in range(size):
                reader.next_number()
        reads = reader.total()
    return loops, eq_ops, reads, builds


def solve_tier(level, size=DATA['size'], keys=DATA['keys'], seed=DATA['seed'],
               text=None, reader=None):
    """把第 level 招之后的写法真跑一遍，交回答案。

    四级的答案**必须一样**——这就是「优化不许改答案」那一条。
    读入按级切换：0 到 1 级逐行读，2 级起一次读完。
    """
    if text is None:
        text = input_text(sample_data(seed, size, keys)[0])
    if reader is None:
        reader = make_reader(text)
    if level >= 2:
        # 第 2 招：整体读入——一次 read().split()，剩下的是 int() 转换。
        values = [int(token) for token in reader.read_all().split()]
    else:
        # 第 0/1 级：逐行读——每行一次函数调用加一次解析。
        values = [reader.next_number() for _ in range(size)]

    # 第 1 招：换容器。这里是四级真正的分水岭——列表的 in 是线性扫描，
    # 集合的 in 平均一步；只看 400 次的循环次数，看不出这一点。
    if level >= 1:
        container = set(values)
    else:
        container = values

    wanted = key_table(values, keys)
    if level >= 4:
        # 第 4 招：手写循环换成 sum + generator——循环搬进 C 层。
        return sum(1 for item in wanted if item in container and item != IGNORE)
    total = 0
    for key in wanted:
        if key in container and key != IGNORE:
            total += 1
    return total


def tier_times(size=DATA['size'], seed=DATA['seed'], repeats=DATA['repeats']):
    """每一级各量一次 → {级: 秒数}。

    第 0 级最贵（列表扫描），取中位数；其余跑一遍就够看趋势。
    这里用的是**中位数**，不是「跑得最快的那一次」——课件第一次量全局名时
    就是被噪声盖住了效应（量出 1.00）。

    判分对这几格的用法只有两条，都在这一课最容易被坑的地方：
      (a) **退化守卫**：四级全是 0.000000 就 FAIL（占位值不算量过）；
      (b) 换容器那一处带噪声容差地判一次（>= 0.75 倍）。
    判死人的是 tier_steps 那四行**次数**，不是这里。
    """
    keys = DATA['keys']
    text = input_text(sample_data(seed, size, keys)[0])
    out = {}
    for level in LEVELS:
        reps = repeats if level in (0, 4) else 1
        seconds, _ = median_seconds(
            lambda level=level: solve_tier(level, size, keys, seed, text), reps)
        out[level] = seconds
    return out


def audit_answers(size=DATA['size'], keys=DATA['keys'], seed=DATA['seed']):
    """改正之后对拍一次：四级答案与标准答案 → (不一致组数, 总组数)。

    「不一致组数」是**确定量**：同一台机器上每次都是 0，判分拿自己的参数复算一遍。
    这一格就是「每改一处都要回验」在代码里的样子：四招上完，不一致必须是 0 组。
    """
    arr = sample_data(seed, size, keys)[0]
    wanted = key_table(arr, keys)
    standard = canonical_count(arr, wanted)
    bad = 0
    for level in LEVELS:
        if solve_tier(level, size, keys, seed) != standard:
            bad += 1
    return bad, len(LEVELS)


def trace():
    """这一段的主记录：每一级一行 (级, 循环次数, 相等比较次数, 读入次数, 建集合次数, 秒数)。

    主块拿它打印判分要读的那几行；判分也拿同一份口径去比（**它自己另算一遍**）。
    """
    times = tier_times()
    rows = []
    for level in LEVELS:
        loops, eq_ops, reads, builds = tier_steps(level)
        rows.append((level, loops, eq_ops, reads, builds, times[level]))
    return rows


def audit_tiers(size=DATA['size'], keys=DATA['keys'], seed=DATA['seed']):
    """四级各交回什么、标准答案是多少 → (四级答案的表, 标准答案)。

    **不入册**（不在 `PROBE_INTERFACE` 里）：判分接口是那五个函数，
    这里只是把主块要打印的那几格摊开，好让打印行里能顺手看出一致性。
    """
    arr = sample_data(seed, size, keys)[0]
    wanted = key_table(arr, keys)
    text = input_text(arr)
    answers = [solve_tier(level, size, keys, seed, text) for level in LEVELS]
    return answers, canonical_count(arr, wanted)


if __name__ == '__main__':                      # 别改：判分读的就是下面这几行
    ARR = sample_data(DATA['seed'], DATA['size'], DATA['keys'])[0]
    WANTED = key_table(ARR, DATA['keys'])
    TEXT = input_text(ARR)

    show_banner('0029 四招各是什么')
    for LEVEL, NAME in TIERS:                                       # 别改
        print('   第 ' + str(LEVEL) + ' 级  ' + NAME)                # 别改

    show_banner('0029 每一级的次数（确定量）')
    TIMES = tier_times()                                            # 别改
    for LEVEL in LEVELS:
        LOOPS, EQ_OPS, READS, BUILDS = tier_steps(LEVEL)            # 别改
        print('   第 ' + str(LEVEL) + ' 级 循环 ' + str(LOOPS)       # 别改
              + ' 次 相等比较 ' + str(EQ_OPS)
              + ' 次 读入 ' + str(READS)
              + ' 次 建集合 ' + str(BUILDS) + ' 次')
        print('   第 ' + str(LEVEL) + ' 级耗时 '
              + fmt_seconds(TIMES[LEVEL]) + ' 秒')                   # 别改

    show_banner('0029 每上一招，答案还对吗')
    ANSWERS, STANDARD = audit_tiers()                               # 别改
    for LEVEL in LEVELS:
        show_line('答案 ' + str(LEVEL) + ' 级', ANSWERS[LEVEL])      # 别改
    show_line('标准答案', STANDARD)                                 # 别改
    show_line('四级答案一致吗', len(set(ANSWERS)) == 1)              # 别改

    show_banner('0029 改正之后对拍一次')
    BAD, TOTAL = audit_answers()                                    # 别改
    show_line('四级答案不一致的组数', str(BAD) + ' 组')              # 别改：期望 0 组
    print('   四招上完再对拍一次：' + str(TOTAL) + ' 级里不一致 ' + str(BAD)   # 别改
          + ' 级——每改一处都要回验，这一格必须回到 0。')

    show_banner('0029 换容器那一处的耗时（只当参考）')
    GUARD_ON, CAN_SET, NOTE = judge_guard(TIMES[1], TIMES[0])        # 别改
    print('   第 0 级 ' + fmt_seconds(TIMES[0]) + ' 秒 → 第 1 级 '
          + fmt_seconds(TIMES[1]) + ' 秒（换容器）')                 # 别改
    print('   这一条' + ('判了' if GUARD_ON else '没判')
          + ('、过了' if CAN_SET else '、还没过') + '：' + NOTE)     # 别改

    show_banner('0029 收尾')
    print('   四招的顺序：换容器 → 整体读入 → 提前算不变式 → 用内置。')   # 别改
    print('   先把钱大的做掉：换容器省的是复杂度，抠语法省的是常数。')       # 别改
