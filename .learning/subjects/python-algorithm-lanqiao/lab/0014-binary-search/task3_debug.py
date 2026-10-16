"""任务 3 · 三种错法的现场

课件介绍了三种容易写错的二分版本。把它们抄下来，用同一套边界数据跑一遍，
记录每一种错法在哪几组数据上暴露出来。再给每种错法写一句说明：
「哪一行导致了它」。

这三种错法是：
  1. bug_no_shrink   —— mid 之后 `lo = mid` 而不是 `lo = mid + 1`，区间不收缩
  2. bug_lose_last   —— 闭区间上用了 `while lo < hi` 而不是 `lo <= hi`，漏最后一个
  3. bug_no_check    —— 直接返回 lower_bound 的下标，不检查越界与值是否相等

这段要做的三件事：
  1. 把三种错法从课件抄下来，名字对应好；
  2. 用同一套边界数据跑一遍（task2 的 boundary_data），记录每种错法在
     哪些组上「暴露」了（回答与正确版本不一致）；
  3. 对每种错法打印一句「哪一行导致的」。

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
#
# 直接从课件抄：
#   lo, hi = 0, len(a)
#   while lo < hi:
#       mid = (lo + hi) // 2
#       if a[mid] < x:
#           lo = mid       # ← 故意写成 mid 而不是 mid + 1
#       else:
#           hi = mid
#   return lo
#
# hi = lo + 1 时 mid 正好等于 lo，而 a[mid] < x 又把 lo 赋值成 mid，
# 区间长度一直不变 → 死循环。
# 注意加上 steps 保护（超过 50 步就返回），否则死循环会卡死这个脚本。
def bug_no_shrink(a, x):
    return 0


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 bug_lose_last(a, x) → 错法二：漏最后一个元素。
#
# 直接从课件抄：
#   lo, hi = 0, len(a) - 1
#   while lo < hi:              # ← 故意写成 < 而不是 <=
#       mid = (lo + hi) // 2
#       if a[mid] == x:
#           return mid
#       if a[mid] < x:
#           lo = mid + 1
#       else:
#           hi = mid - 1
#   return -1
#
# 闭区间还剩一个元素时（lo == hi），while 条件不满足，
# 那个元素永远不被检查。答案恰好在那个位置时就丢了。
def bug_lose_last(a, x):
    return -1


# ══ TODO 3 ═════════════════════════════════════════════════
# 写 bug_no_check(a, x) → 错法三：直接返回插入位置，不检查存在性。
#
# 直接从课件抄（就是 lower_bound 的写法，但直接返回 lo）：
#   lo, hi = 0, len(a)
#   while lo < hi:
#       mid = (lo + hi) // 2
#       if a[mid] < x:
#           lo = mid + 1
#       else:
#           hi = mid
#   return lo
#
# 缺少了 k < len(a) and a[k] == x 这步验证。
# x 不存在时 lo 照样返回一个「插入位置」，但这个位置的值不等于 x。
# x 比所有元素都大时 lo == len(a)，直接取 a[lo] 会越界。
def bug_no_check(a, x):
    return 0


# ══ TODO 4 ═════════════════════════════════════════════════
# 写 detect(bugs, seqs, correct_funcs) → 跑每套参数，返回暴露记录。
#
# bugs = {'bug名': 函数, ...}  三个错版
# seqs = [(名字, 数组, 目标, 'hit'/'miss'), ...]  边界数据
# correct_funcs = {'bsearch_closed': 函数, 'contains': 函数}
#    用来判断正确答案（用正确版本跑的结果作为参照）
#
# 返回值是一个列表，每项是：
#   {
#       'bug': 'bug_no_shrink',
#       'data': '空',           # 名字
#       'arr': [], 'x': 1,
#       'exposed': True/False,   # 是否暴露
#       'bug_value': ...,        # 错版返回的值
#       'correct_value': ...     # 正确版本返回的值
#   }
#
# 暴露的判断标准：
#   · 对于有 hits/miss 信息的数据：错版的结果（用 contains 逻辑判断）
#     与正确版本的 contains 结果不一致
#   · 或者错版抛了异常 / 死循环（steps 超限）
def detect(bugs, seqs, correct_funcs):
    return []


# ══ TODO 5 ═════════════════════════════════════════════════
# 写 print_exposure(results) → 打印每种错法的暴露情况。
#
# 格式（判分读这几行）：
#   暴露 01 bug_no_shrink 暴露于: 全部(8组)
#   暴露 02 bug_lose_last 暴露于: 目标在左端、目标在右端
#   暴露 03 bug_no_check 暴露于: 单元素不中、全相同不中、目标不存在
#
# 每种错法一行。
def print_exposure(results):
    pass


# ══ TODO 6 ═════════════════════════════════════════════════
# 写 CONCISE_EXPLANATIONS = {...}：对每种错法写一句「哪一行导致了它」。
#
# 格式（判分读这个字典）：
#   'bug_no_shrink': '第 N 行 lo = mid：区间长度为 1 时 mid == lo，
#                     赋值后区间不收缩，导致死循环'
#   'bug_lose_last': '第 N 行 while lo < hi：闭区间还剩一个元素时条件不满足，
#                     那个元素不被检查'
#   'bug_no_check': '缺少 k < len(a) and a[k] == x 的检查，
#                    目标不存在时返回错误下标'
#
# 每一句里要包含哪一行（行号）。判分核的是：行号是否指向了真正的病灶行。
# 注意这里的行号是 task3_debug.py 里的行号。
CONCISE_EXPLANATIONS = {
    'bug_no_shrink': '',
    'bug_lose_last': '',
    'bug_no_check': '',
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
    if records:
        print_exposure(records)
    else:
        # TODO 4 还没填：兜底打几条
        for bname, bfunc in bugs.items():
            revealed = []
            for name, arr, x, expect in seqs:
                with steps_limit(50):
                    val = attempt(bfunc, arr, x)
                    correct_v = attempt(contains, arr, x)
                    exposed = (val.ok and correct_v.ok
                               and val.value != correct_v.value)
                    exposed = exposed or (val.ok and isinstance(val.value, str)
                                          and '死循环' in str(val.value))
                    if exposed:
                        revealed.append(name)
            text = '、'.join(revealed) if revealed else '无'
            show('暴露', sorted(bugs.keys()).index(bname) + 1, bname,
                 '暴露于: ' + text)

    # 打印解释
    print('解释')
    for i, (bname, expl) in enumerate(sorted(CONCISE_EXPLANATIONS.items()), 1):
        print(f'  错法 {i} {bname}：{expl}')