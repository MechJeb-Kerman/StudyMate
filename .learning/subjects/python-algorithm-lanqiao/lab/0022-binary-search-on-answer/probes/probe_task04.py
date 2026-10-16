"""probes/probe_task04.py · 任务 4 的判分探针（给好的，别改）
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import task04_break_monotonicity as t

# ── check_bad 单调性测试 ────────────────────────────────────────
check_vals = {}
for x in range(1, 21):
    check_vals[x] = t.check_bad(x)

# ── 多个区间上的二分结果 ────────────────────────────────────────
intervals = []
for lo, hi in [(1, 20), (1, 10), (1, 8), (1, 5), (3, 10), (5, 20)]:
    bs = t.binary_search_on_answer(t.check_bad, lo, hi)
    bf = t.brute_best(t.check_bad, lo, hi)
    intervals.append([lo, hi, bs, bf, bs == bf])

# ── 单调对照 ────────────────────────────────────────────────────
good_intervals = []
for lo, hi in [(1, 20), (1, 10)]:
    bs = t.binary_search_on_answer(t.check_good, lo, hi)
    bf = t.brute_best(t.check_good, lo, hi)
    good_intervals.append([lo, hi, bs, bf, bs == bf])

print('PROBE ' + json.dumps([check_vals, intervals, good_intervals], ensure_ascii=False))