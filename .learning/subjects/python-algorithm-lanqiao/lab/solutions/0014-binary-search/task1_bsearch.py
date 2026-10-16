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
def bsearch_closed(a, x):
    lo = 0
    hi = len(a) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] == x:
            return mid
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 lower_bound(a, x)：左闭右开二分查找。
def lower_bound(a, x):
    lo = 0
    hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


# ══ TODO 3 ═════════════════════════════════════════════════
# 写 contains(a, x)：用 lower_bound 判断 x 是否在 a 里 → True/False。
def contains(a, x):
    k = lower_bound(a, x)
    return k < len(a) and a[k] == x


# ══ TODO 4 ═════════════════════════════════════════════════
# 写 compare_with_bisect(sizes, trials)：批量比对三个版本与 bisect。
def compare_with_bisect(sizes, trials):
    for n in sizes:
        for trial in range(trials):
            arr = sorted(random.sample(range(0, n * 10), n))
            targets = [arr[0], arr[n // 4], arr[n // 2],
                       arr[n * 3 // 4], arr[-1], -1, n * 10 + 5]
            for x in targets:
                bisect_val = bisect.bisect_left(arr, x)
                bisect_found = bisect_val < len(arr) and arr[bisect_val] == x
                closed_val = bsearch_closed(arr, x)
                lb_val = lower_bound(arr, x)
                ct_val = contains(arr, x)
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

        if closed.ok:
            if (expect == 'hit' and closed.value >= 0
                    and closed.value < len(arr)
                    and arr[closed.value] == x):
                ok += 1
            elif expect == 'miss' and closed.value == -1:
                ok += 1
            elif closed.error:
                show_error(i, label + ' bsearch_closed', closed.error)

        if lb.ok:
            if lb.value == bisect_val:
                ok += 1
            elif lb.error:
                show_error(i, label + ' lower_bound', lb.error)

        if ct.ok:
            if ct.value == bisect_found:
                ok += 1
            elif ct.error:
                show_error(i, label + ' contains', ct.error)

        show('一致', i, label, ok)

    # ── 第 2 段：随机有序数组上批量比对 ────────────────────────────────
    print('随机比对')
    compare_with_bisect([100, 1000], 5)

    # ── 第 3 段：三个版本的结果示意 ────────────────────────────────────
    demo = [1, 3, 5, 7, 9, 11]
    for x in (7, 4):
        c = bsearch_closed(demo, x)
        lb = lower_bound(demo, x)
        ct = contains(demo, x)
        print(f'  搜索 {x}: bsearch_closed={c}  lower_bound={lb}  contains={ct}')