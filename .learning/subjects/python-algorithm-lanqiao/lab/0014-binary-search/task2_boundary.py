"""任务 2 · 边界测试数据表

造一整套边界数据（空、单元素命中、单元素不中、全相同、答案在两端、
答案不存在），逐个目标跑 bsearch_closed、lower_bound、contains 与 bisect，
把结果做成一张表。

这张表的目的不是「看看对不对就算了」，而是：
  · 每跑一组新数据，都能立刻发现一个模板的边界写没写对；
  · 八组边界数据合起来覆盖了最容易出问题的所有位置；
  · 三种错法（task3）在哪些数据上暴露出来，答案就在这张表里。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。
判分还会另起一个进程 import 你这个文件里的函数，拿它自己造的独立数据再试一遍——
所以函数名与参数必须与下面写的一致。

跑： py task2_boundary.py
判： py run_tests.py
"""

import sys
import bisect

from tools import (
    bound_seqs, show, show_error, attempt,
)


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 boundary_data() → 返回与 bound_seqs() 相同的 8 组边界数据。
#
# 这里不直接调 bound_seqs 是有意的：抄一次能确认你真的理解了每一条边界
# 代表了「哪一类容易出问题的位置」。
#
# 每组是 (名字, 数组, 目标值, 'hit'/'miss')，共 8 组：
#   ('空', [], 1, 'miss')
#   ('单元素命中', [5], 5, 'hit')
#   ('单元素不中', [5], 3, 'miss')
#   ('全相同命中', [7]*6, 7, 'hit')
#   ('全相同不中', [7]*6, 8, 'miss')
#   ('目标在左端', [1,3,5,7,9], 1, 'hit')
#   ('目标在右端', [1,3,5,7,9], 9, 'hit')
#   ('目标不存在', [1,3,5,7,9], 4, 'miss')
def boundary_data():
    return []


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 run_each(seqs, funcs_dict) → 在每组数据上跑所有函数，返回结果表。
#
# seqs 是 [(名字, 数组, 目标值, 期望类型), …]
# funcs_dict 是 {'函数名': 函数, …}（至少含 bsearch_closed / lower_bound / contains）
#
# 返回值是一个二维表：表头是函数名，行是每组数据。
# 格式（每一行一个元组，便于打印）：
#   name     bsearch_closed的返回值  lower_bound的返回值  contains的返回值
#
# 注意：
#   · bsearch_closed 返回下标（≥0）或 -1
#   · lower_bound 返回插入位置（0 到 len(arr) 之间）
#   · contains 返回 True/False
#   · 所有调用都用 attempt 保护，防止函数未实现时崩掉
def run_each(seqs, funcs_dict):
    return []


# ══ TODO 3 ═════════════════════════════════════════════════
# 写 print_table(results) → 把结果打印成判分能读的固定格式行。
#
# results 是 run_each 的交回值。
# 对每组数据打印三行，分别是三个函数的返回值：
#   边界 01 空 bsearch_closed -1
#   边界 02 空 lower_bound 0
#   边界 03 空 contains False
#   边界 04 单元素命中 bsearch_closed 0
#   ...
#
# 编号规则：每组数据占 3 行，按 (组号 * 3 - 2) 分配起始编号。
# 组号就是 1..len(results)。
#
# 这个打印格式判分会解析，注意：
#   · section 统一用「边界」
#   · 名称用「名字_函数名」的格式（不含空格）
def print_table(results):
    pass


# ── 给好的部分：主块（别改）─────────────────────────────────────────────
if __name__ == '__main__':
    print('任务 2 · 边界测试数据表')

    from task1_bsearch import bsearch_closed, lower_bound, contains

    seqs = boundary_data()
    if not seqs or len(seqs) < 8:
        # TODO 1 还没填：用参考数据兜底
        seqs = bound_seqs()

    funcs = {'bsearch_closed': bsearch_closed,
             'lower_bound': lower_bound,
             'contains': contains}
    results = run_each(seqs, funcs)

    if not results:
        # TODO 2 还没填：自己造一个
        results = []
        for name, arr, x, expect in seqs:
            closed_v = attempt(bsearch_closed, arr, x)
            lb_v = attempt(lower_bound, arr, x)
            ct_v = attempt(contains, arr, x)
            results.append((name, closed_v.value if closed_v.ok else 'ERR',
                           lb_v.value if lb_v.ok else 'ERR',
                           ct_v.value if ct_v.ok else 'ERR'))

    print_table(results)