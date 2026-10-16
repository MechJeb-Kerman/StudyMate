"""任务 3 · 三种错法的现场

课件介绍了三种容易写错的二分版本。把它们抄下来，用同一套边界数据跑一遍，
记录每一种错法在哪几组数据上暴露出来。再给每种错法写一句说明：
「哪一行导致了它」。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。

跑： py task3_debug.py
判： py run_tests.py
"""

import sys
import bisect

from tools import (
    bound_seqs, show, show_error, attempt, is_sorted,
)


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 bug_no_shrink(a, x) → 错法一：区间不收缩。
def bug_no_shrink(a, x):
    lo = 0
    hi = len(a)
    steps = 0
    while lo < hi:
        steps += 1
        if steps > 50:
            return '步数超限，死循环', steps
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid      # ← 故意写成 mid 而不是 mid + 1
        else:
            hi = mid
    return lo, steps


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 bug_lose_last(a, x) → 错法二：漏最后一个元素。
def bug_lose_last(a, x):
    lo = 0
    hi = len(a) - 1
    while lo < hi:          # ← 故意写成 < 而不是 <=
        mid = (lo + hi) // 2
        if a[mid] == x:
            return mid
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


# ══ TODO 3 ═════════════════════════════════════════════════
# 写 bug_no_check(a, x) → 错法三：直接返回插入位置，不检查存在性。
def bug_no_check(a, x):
    lo = 0
    hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo               # ← 少了 k < len(a) and a[k] == x 验证


# ══ TODO 4 ═════════════════════════════════════════════════
# 写 detect(bugs, seqs, correct_funcs) → 跑每套参数，返回暴露记录。
def detect(bugs, seqs, correct_funcs):
    records = []
    for bname, bfunc in bugs.items():
        for name, arr, x, expect in seqs:
            val = attempt(bfunc, list(arr), x)
            correct_val = attempt(correct_funcs['contains'], list(arr), x)
            exposed = False
            bug_value = val.value if val.ok else 'ERR'
            correct_value = correct_val.value if correct_val.ok else 'ERR'

            if val.ok and correct_val.ok:
                if bname == 'bug_no_shrink':
                    # 错法一：死循环（步数超限）
                    if isinstance(val.value, tuple) and len(val.value) >= 2:
                        if '死循环' in str(val.value[0]):
                            exposed = True
                        else:
                            lo_val = val.value[0]
                            # 死循环没触发时，lo = mid 导致 lo 可能落后于正确位置
                            correct_lb = correct_funcs.get('lower_bound',
                                                           lambda a, x: 0)(list(arr), x)
                            if isinstance(lo_val, int):
                                correct_idx = correct_lb if isinstance(correct_lb, int) else 0
                                if isinstance(correct_lb, int) and lo_val != correct_lb:
                                    exposed = True
                    elif isinstance(val.value, str) and '死循环' in str(val.value):
                        exposed = True

                elif bname == 'bug_lose_last':
                    # 错法二：闭区间 while lo < hi 漏掉最后一个元素
                    # 对 hit 类数据，如果目标恰好在区间仅剩的那个位置上 → 漏掉
                    if expect == 'hit':
                        # 看 bug 是否返回 -1（没找到）但值实际在数组里
                        bug_found = val.value >= 0
                        exposed = (bug_found != correct_val.value)
                    else:
                        # miss 类数据上也可能误报找到
                        bug_found = val.value >= 0
                        exposed = (bug_found != correct_val.value)

                elif bname == 'bug_no_check':
                    # 错法三：返回插入位置但不验证
                    # 在 miss 数据上，返回的索引指向的值 != x（但函数自己没检查）
                    # 在 hit 数据上也可能返回错的插入位置而非命中位置
                    if expect == 'miss':
                        # 检查返回的索引是否指向错误的值
                        if isinstance(val.value, int):
                            # 如果 arr[result] != x 且能拿到值，就是暴露了
                            if 0 <= val.value < len(arr):
                                # 对于 miss，函数应返回的插入位置恰好使得 arr[result] >= x 或 == x
                                # 关键是函数没告诉你 "没找到"
                                arr_val = arr[val.value]
                                exposed = (arr_val != x)
                            else:
                                # 越界了
                                exposed = True
                        else:
                            exposed = True
                    else:
                        # hit 数据上应该返回命中位置
                        if isinstance(val.value, int):
                            found = (0 <= val.value < len(arr) and arr[val.value] == x)
                            exposed = (found != correct_val.value)
                        else:
                            exposed = True

                else:
                    # 兜底
                    bug_found = (val.value >= 0 and val.value < len(arr)
                                 and arr[val.value] == x)
                    exposed = (bug_found != correct_val.value)

            elif not val.ok:
                exposed = True  # 抛异常也是暴露

            records.append({
                'bug': bname,
                'data': name,
                'arr': list(arr), 'x': x,
                'exposed': exposed,
                'bug_value': bug_value,
                'correct_value': correct_value,
            })
    return records


# ══ TODO 5 ═════════════════════════════════════════════════
# 写 print_exposure(results) → 打印每种错法的暴露情况。
def print_exposure(results):
    bugs_seen = {}
    for rec in results:
        bname = rec['bug']
        if bname not in bugs_seen:
            bugs_seen[bname] = []
        if rec['exposed']:
            bugs_seen[bname].append(rec['data'])

    bug_order = ['bug_no_shrink', 'bug_lose_last', 'bug_no_check']
    for idx, bname in enumerate(bug_order, 1):
        exposed_on = bugs_seen.get(bname, [])
        text = '、'.join(exposed_on) if exposed_on else '无'
        show('暴露', idx, bname, '暴露于: ' + text)


# ══ TODO 6 ═════════════════════════════════════════════════
# 写 CONCISE_EXPLANATIONS = {...}：对每种错法写一句「哪一行导致了它」。
CONCISE_EXPLANATIONS = {
    'bug_no_shrink': '第 60 行 lo = mid：区间长度为 1 时 mid == lo，赋值后区间不收缩，导致死循环',
    'bug_lose_last': '第 73 行 while lo < hi：闭区间还剩一个元素时条件不满足，那个元素不被检查',
    'bug_no_check': '缺少 k < len(a) and a[k] == x 的检查，目标不存在时返回错误下标或越界',
}


# ── 给好的部分：主块（别改）─────────────────────────────────────────────
if __name__ == '__main__':
    print('任务 3 · 三种错法的现场')

    from task1_bsearch import bsearch_closed, lower_bound, contains

    seqs = bound_seqs()

    bugs = {
        'bug_no_shrink': bug_no_shrink,
        'bug_lose_last': bug_lose_last,
        'bug_no_check': bug_no_check,
    }
    correct = {
        'bsearch_closed': bsearch_closed,
        'contains': contains,
    }

    records = detect(bugs, seqs, correct)
    print_exposure(records)

    # 打印解释
    print('解释')
    for i, (bname, expl) in enumerate(sorted(CONCISE_EXPLANATIONS.items()), 1):
        print(f'  错法 {i} {bname}：{expl}')