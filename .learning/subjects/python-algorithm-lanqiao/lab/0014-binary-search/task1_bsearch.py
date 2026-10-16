"""任务 1 · 两个模板与 contains + 用 bisect 对照

把课件里两个二分模板抄下来：闭区间版 bsearch_closed 与左闭右开版 lower_bound，
再补一个 contains 函数。然后用 bisect 当参照，在一批随机有序数组上逐目标比对。

三件事一起做：
  1. 抄两个模板：bsearch_closed（闭区间）与 lower_bound（左闭右开）；
  2. 写 contains（用 lower_bound 判断 x 是否在数组里）；
  3. 拿一批随机有序数组与 bisect 对照：对每个目标同时跑三个版本与 bisect，
     不一致就打印那一组数据。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。
判分还会另起一个进程 import 你这个文件里的函数，拿它自己造的小数据再试一遍——
所以函数名与参数必须与下面写的一致。

跑： py task1_bsearch.py
判： py run_tests.py
"""

import random
import sys
import bisect

from tools import (
    make_random, make_sorted, show, show_error, attempt,
)


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 bsearch_closed(a, x)：闭区间二分查找。
#
# 区间表示：[lo, hi]，两端都能取到。
# 循环不变式：若 x 在数组里，它的下标一定在 [lo, hi] 内。
#
#   lo = 0
#   hi = len(a) - 1
#   while lo <= hi:                    # 闭区间：lo == hi 时还有最后一个元素
#       mid = (lo + hi) // 2
#       if a[mid] == x:
#           return mid                 # 命中：返回下标
#       if a[mid] < x:
#           lo = mid + 1               # mid 已经确定不是，从 mid + 1 开始
#       else:
#           hi = mid - 1               # 同理，到 mid - 1 结束
#   return -1                          # 没找到
#
# 三个关键细节（少一个就错）：
#   1. while lo <= hi（不是 <，写 < 会漏掉最后一个元素）
#   2. lo = mid + 1（不是 mid，否则区间不收缩，死循环）
#   3. hi = mid - 1（不是 mid，理由同上）
def bsearch_closed(a, x):
    return -1


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 lower_bound(a, x)：左闭右开二分查找。
#
# 区间表示：[lo, hi)，hi 本身不是候选。
# 循环不变式：若 x 在数组里，它的下标一定在 [lo, hi) 内。
# 返回值：第一个 >= x 的位置（x 不存在时它照样返回一个合法下标）。
#
#   lo = 0
#   hi = len(a)                         # 注意：不是 len(a) - 1
#   while lo < hi:                      # 左闭右开：lo == hi 时区间已空
#       mid = (lo + hi) // 2
#       if a[mid] < x:
#           lo = mid + 1                 # mid 比 x 小，排掉左半边
#       else:
#           hi = mid                     # mid >= x，左移右边界（hi 本身不取）
#   return lo                            # 第一个 >= x 的位置
#
# 与闭区间模板的差别集中在三处：
#   初值       lo=0, hi=len(a)        vs lo=0, hi=len(a)-1
#   循环条件   while lo < hi          vs while lo <= hi
#   收缩       hi = mid               vs hi = mid - 1
def lower_bound(a, x):
    return 0


# ══ TODO 3 ═════════════════════════════════════════════════
# 写 contains(a, x)：用 lower_bound 判断 x 是否在 a 里 → True/False。
#
#   k = lower_bound(a, x)
#   return k < len(a) and a[k] == x
#
# 两步判断不能省：
#   · k < len(a)：x 比所有元素都大时 k 正好等于 len(a)，直接取 a[k] 越界
#   · a[k] == x：lower_bound 返回的是「插入位置」，不等于「已找到」
def contains(a, x):
    return False


# ══ TODO 4 ═════════════════════════════════════════════════
# 写 compare_with_bisect(sizes, trials)：批量比对三个版本与 bisect。
#
# 对每一档规模，生成 trials 个随机有序数组，在每个数组上选几个目标值，
# 同时用 bsearch_closed、lower_bound、contains 与 bisect 跑一遍，
# 把不一致的记录下来打印。
#
# 目标值要覆盖：左端、中点附近、右端、不在范围内的数。
# 打印格式（判分读这些行）：
#   「一致 01 随机 n=100 4/4」—— 四个版本（含 bisect）的答案一致，4/4
#   「一致 01 随机 n=100 3/4 —— bsearch_closed 在目标 5 上交回 -1，bisect 是 2」
#
# 四个版本分别是：
#   a. bisect.bisect_left(a, x)         标准库
#   b. bsearch_closed(a, x)            你写的闭区间版
#   c. lower_bound(a, x)               你写的左闭右开版
#   d. contains(a, x)与 x in a 核对   你写的 contains 函数
#
# 注意：bsearch_closed 返回的是下标或 -1，lower_bound 返回的是插入位置，
# contains 返回的是布尔值。所以比对的方案是：
#   · 对 bisect_left(a, x)，检查「a[k] == x」（越界保护）→ 得到「是否找到」
#   · bisect 版本的「是否找到」与 contains(a, x) 比对
#   · bsearch_closed 的返回下标与「bisect 版本的找到位置」比对
#   · lower_bound(a, x) 与 bisect.bisect_left(a, x) 直接比对
#
# 这里可以简化：只核三个一致：
#   1. bsearch_closed 的「返回 True/False」是否等于 contains（= bisect 结果）
#   2. lower_bound 是否等于 bisect_left
#   3. contains 是否等于 (x in a)
def compare_with_bisect(sizes, trials):
    pass


# ── 给好的部分：主块（别改）─────────────────────────────────────────────
if __name__ == '__main__':
    print('任务 1 · 两个模板与 contains + 用 bisect 对照')

    # ── 第 1 段：边界数据集上逐个验证 ──────────────────────────────────
    from tools import bound_seqs

    for i, (name, arr, x, expect) in enumerate(bound_seqs(), 1):
        closed = attempt(bsearch_closed, arr, x)
        lb = attempt(lower_bound, arr, x)
        ct = attempt(contains, arr, x)
        bisect_val = bisect.bisect_left(arr, x)
        bisect_found = bisect_val < len(arr) and arr[bisect_val] == x

        ok = 0
        label = name

        # bsearch_closed 的逻辑：命中时返回下标 >= 0，未命中返回 -1
        if closed.ok:
            if (expect == 'hit' and closed.value >= 0
                    and closed.value < len(arr)
                    and arr[closed.value] == x):
                ok += 1
            elif expect == 'miss' and closed.value == -1:
                ok += 1
            elif closed.error:
                show_error(i, label + ' bsearch_closed', closed.error)
            # 不报错但逻辑错：不计数

        # lower_bound 的逻辑：返回第一个 >= x 的位置
        if lb.ok:
            if lb.value == bisect_val:
                ok += 1
            elif lb.error:
                show_error(i, label + ' lower_bound', lb.error)

        # contains 的逻辑：必须与 bisect_found 一致
        if ct.ok:
            if ct.value == bisect_found:
                ok += 1
            elif ct.error:
                show_error(i, label + ' contains', ct.error)

        show('一致', i, label, ok)

    # ── 第 2 段：随机有序数组上批量比对 ────────────────────────────────
    print('随机比对')
    sizes = [100, 1000]
    for n in sizes:
        for trial in range(5):
            arr = sorted(random.sample(range(0, n * 10), n))
            targets = [arr[0], arr[n // 4], arr[n // 2],
                       arr[n * 3 // 4], arr[-1], -1, n * 10 + 5]
            for x in targets:
                bisect_val = bisect.bisect_left(arr, x)
                bisect_found = bisect_val < len(arr) and arr[bisect_val] == x

                closed_ok, closed_val = True, bsearch_closed(arr, x)
                lb_ok, lb_val = True, lower_bound(arr, x)
                ct_ok, ct_val = True, contains(arr, x)

                # 收集不一致
                closed_found = closed_val >= 0
                issues = []
                if closed_found != bisect_found:
                    issues.append('bsearch_closed')
                if lb_val != bisect_val:
                    issues.append('lower_bound')
                if ct_val != bisect_found:
                    issues.append('contains')

                if issues:
                    print(f'  不一致 n={n} x={x}  '
                          f'bisect={bisect_val}(found={bisect_found})  '
                          f'closed={closed_val}  lower={lb_val}  '
                          f'contains={ct_val}  —— {", ".join(issues)}')

    # ── 第 3 段：三个版本的结果示意 ────────────────────────────────────
    demo = [1, 3, 5, 7, 9, 11]
    for x in (7, 4):
        c = bsearch_closed(demo, x)
        lb = lower_bound(demo, x)
        ct = contains(demo, x)
        print(f'  搜索 {x}: bsearch_closed={c}  lower_bound={lb}  contains={ct}')