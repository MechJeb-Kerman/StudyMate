"""任务 2 · 边界测试数据表

造一整套边界数据（空、单元素命中、单元素不中、全相同、答案在两端、
答案不存在），逐个目标跑 bsearch_closed、lower_bound、contains 与 bisect，
把结果做成一张表。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。

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
def boundary_data():
    return [
        ('空', [], 1, 'miss'),
        ('单元素命中', [5], 5, 'hit'),
        ('单元素不中', [5], 3, 'miss'),
        ('全相同命中', [7] * 6, 7, 'hit'),
        ('全相同不中', [7] * 6, 8, 'miss'),
        ('目标在左端', [1, 3, 5, 7, 9], 1, 'hit'),
        ('目标在右端', [1, 3, 5, 7, 9], 9, 'hit'),
        ('目标不存在', [1, 3, 5, 7, 9], 4, 'miss'),
    ]


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 run_each(seqs, funcs_dict) → 在每组数据上跑所有函数，返回结果表。
def run_each(seqs, funcs_dict):
    results = []
    for name, arr, x, expect in seqs:
        row = [name]
        for func_name, func in funcs_dict.items():
            ca = attempt(func, list(arr), x)
            row.append(ca.value if ca.ok else 'ERR:' + str(ca.error))
        results.append(tuple(row))
    return results


# ══ TODO 3 ═════════════════════════════════════════════════
# 写 print_table(results) → 把结果打印成判分能读的固定格式行。
def print_table(results):
    for idx, row in enumerate(results, 1):
        name = row[0]
        base_idx = idx * 3 - 2
        # 三个函数分别是 bsearch_closed, lower_bound, contains
        show('边界', base_idx, name + '_bsearch_closed', row[1])
        show('边界', base_idx + 1, name + '_lower_bound', row[2])
        show('边界', base_idx + 2, name + '_contains', row[3])


# ── 给好的部分：主块（别改）─────────────────────────────────────────────
if __name__ == '__main__':
    print('任务 2 · 边界测试数据表')

    from task1_bsearch import bsearch_closed, lower_bound, contains

    seqs = boundary_data()

    funcs = {'bsearch_closed': bsearch_closed,
             'lower_bound': lower_bound,
             'contains': contains}
    results = run_each(seqs, funcs)

    print_table(results)