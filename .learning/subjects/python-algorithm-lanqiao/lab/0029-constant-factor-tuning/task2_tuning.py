"""任务 2 · 依次上三到四招，每招都留记录（lab 0029）

课件要的顺序是：**换容器 → 整体读入 → 提前算不变式 → 用内置**。
顺序不是随便排的：换容器省的是复杂度，抠语法省的是常数，先把钱大的做掉。

    第 0 级  起点：列表 in + 逐行读入                    ← 能算对，就是慢
    第 1 招  换容器：列表 in → 集合 in
    第 2 招  整体读入：逐行 → 一次 read().split()
    第 3 招  提前算不变式：集合提到循环外面
    第 4 招  用内置：手写循环 → sum + generator

**每一招之后都要回验答案。** 所以主块会把「答案 N 级」也当成一格打出来：
四招上完，答案必须还是同一个数。

接口：文件名、函数名、带 print 的行都是判分接口，别改；要写的是五个 TODO：

    TODO 1  optimization_steps   四招的名字（顺序也是接口）
    TODO 2  tier_steps           每一级各做了多少次操作（四格确定量）
    TODO 3  solve_tier           把第 level 招之后的写法真跑一遍，交回答案
    TODO 4  tier_times           每一级各量一次耗时
    TODO 5  audit_answers        四招上完再对拍一次：不一致必须是 0 级

判分怎么判：**四格确定量**（循环次数 / 相等比较次数 / 读入次数 / 建集合次数）逐级对照，
外加「读入器的账目」与「四级答案一致」。耗时只做两件事：退化守卫
（四级全是 0.000000 就 FAIL）+ 换容器那一处的噪声容差。

跑： py task2_tuning.py
判： py run_tests.py
"""

from tools import (DATA, LEVELS, ReadCounter, TIERS, canonical_count,
                   fmt_seconds, input_text, judge_guard, key_table,
                   median_seconds, sample_data, show_banner, show_line)

# 这个数组里不该被数进去的那个值（题目里的「坏值」）。它只影响答案，不影响次数。
IGNORE = -1


# ══ TODO 1 ═════════════════════════════════════════════════
# optimization_steps()：四招的名字，一级一条（判分逐条核对，顺序也是接口）。
#
# 一行就够：`return list(TIERS)`——四招叫什么、什么顺序，tools 里已经定好了
# （起点、换容器、整体读入、提前算不变式、用内置）。别自己另起一套名字。
def optimization_steps():
    return []


# ══ TODO 2 ═════════════════════════════════════════════════
# tier_steps(level, size, keys, seed, reader)：第 level 招之后各做了多少次操作
# → (循环次数, 相等比较次数, 读入次数, 建集合次数)。
#
# **这四格是这一段的判据**：同一台机器上每次都是同一个整数。四招各改掉了什么：
#
#   第 0 级  手写循环里的 `in`：容器是列表，每个键要扫 n 次 → 循环次数 = keys * size
#   第 1 招  容器换成集合：每个键一步 → 循环次数 = keys（相等的比较也降到 keys）
#   第 2 招  整体读入：逐行一次 → 一次读入调用，读入次数从 size 降到 1
#   第 3 招  集合提到循环外：第 2 级每轮都还在重建集合（建集合 keys 次），
#            提到外面之后建集合只有 1 次
#   第 4 招  手写计数换成 sum + generator：循环次数从 keys 降到 1
#
# 四个数怎么算：
#
#     loops   = 1 if level >= 4 else (keys if level >= 1 else keys * size)
#     eq_ops  = keys if level >= 3 else keys * size
#     reads   = 1 if level >= 2 else size
#     builds  = keys if level == 2 else 1
#
# **读入那一格必须由 reader 自己记出来**，不能只按公式写：传进来的 reader 就是
# 那个会记账的读入器（tools.ReadCounter）。第 2 级起走一次整体读
# `reader.read_all()`；第 0、1 级走逐行读，每行一次 `reader.next_number()`，
# 一行一次、一共 size 次——最后把 `reader.total()` 交回当读入次数那一格。
# 判分不光比这四个数，还会**自己再数一遍 reader 的账**，所以那一格必须真调出来。
def tier_steps(level, size=DATA['size'], keys=DATA['keys'], seed=DATA['seed'],
               reader=None):
    return (0, 0, 0, 0)


# ══ TODO 3 ═════════════════════════════════════════════════
# solve_tier(level, size, keys, seed, text, reader)：把第 level 招之后的写法真跑一遍，
# 交回答案（一个整数）。
#
# 读入按级切换：
#
#     第 0、1 级  逐行读：values = [reader.next_number() for _ in range(size)]
#     第 2 级起   整体读：values = [int(token) for token in reader.read_all().split()]
#
# 容器按级切换（这一处才是四级真正的分水岭）：
#
#     第 0 级     container = values（**列表**：一个键扫一整条数组）
#     第 1 级起   container = set(values)（集合：平均一步）
#
# 然后拿 key_table(values, keys) 当键表，数一数「命中且不是 IGNORE」的键有几个：
#
#     wanted = key_table(values, keys)
#     total = 0
#     for key in wanted:
#         if key in container and key != IGNORE:
#             total += 1
#     return total
#
# 第 4 招再把这一个手写循环换成 sum + generator（循环搬进 C 层）：
#
#     return sum(1 for item in wanted if item in container and item != IGNORE)
#
# **四级的答案必须一样**——这就是「优化不许改答案」那一条。
# 判分拿自己的数据把四级各跑一遍，四级都必须等于它另算的那个数。
def solve_tier(level, size=DATA['size'], keys=DATA['keys'], seed=DATA['seed'],
               text=None, reader=None):
    return 0


# ══ TODO 4 ═════════════════════════════════════════════════
# tier_times(size, seed, repeats)：每一级各量一次 → {级: 秒数}。
#
#     text = input_text(sample_data(seed, size, keys)[0])
#     out = {}
#     for level in LEVELS:
#         reps = repeats if level in (0, 4) else 1      # 第 0 级最贵，多跑几遍取中位数
#         seconds, _ = median_seconds(
#             lambda level=level: solve_tier(level, size, keys, seed, text), reps)
#         out[level] = seconds
#     return out
#
# 口径是**中位数**，不是「跑得最快的那一次」。判分对这几格的用法只有两条：
# (a) 退化守卫——四级全是 0.000000 就 FAIL（占位值不算量过）；
# (b) 换容器那一处带噪声容差地判一次。判死人的是 tier_steps 那四行次数。
def tier_times(size=DATA['size'], seed=DATA['seed'], repeats=DATA['repeats']):
    text = input_text(sample_data(seed, size, DATA['keys'])[0])
    out = {}
    for level in LEVELS:
        seconds, _ = median_seconds(
            lambda level=level: solve_tier(level, size, DATA['keys'], seed, text), 1)
        out[level] = seconds
    return out


# ══ TODO 5 ═════════════════════════════════════════════════
# audit_answers(size, keys, seed)：改正之后对拍一次
# → (不一致级数, 总级数)。
#
# 口径：拿标准答案（`canonical_count(arr, key_table(arr, keys))`）当尺子，
# 把四级各跑一遍，数一数**有几级的答案与标准答案不一样**：
#
#     arr = sample_data(seed, size, keys)[0]
#     wanted = key_table(arr, keys)
#     standard = canonical_count(arr, wanted)
#     bad = 0
#     for level in LEVELS:
#         if solve_tier(level, size, keys, seed) != standard:
#             bad += 1
#     return bad, len(LEVELS)
#
# 这一格是**确定量**：四招上完，不一致必须是 0 级。判分拿自己的参数复算一遍。
def audit_answers(size=DATA['size'], keys=DATA['keys'], seed=DATA['seed']):
    return 0, len(LEVELS)


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


def _safe_four(values):
    """打印用：四级答案的表——拿不到就交回四个占位值（判分要读行数）。"""
    if isinstance(values, (list, tuple)) and len(values) == len(LEVELS):
        return list(values)
    return [0 for _level in LEVELS]


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
    ANSWERS = _safe_four(ANSWERS)                                   # 别改
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
