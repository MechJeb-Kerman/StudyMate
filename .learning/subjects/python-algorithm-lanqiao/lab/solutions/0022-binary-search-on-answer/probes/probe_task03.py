"""probes/probe_task03.py · 任务 3 的判分探针（给好的，别改）
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import task03_bruteforce_verify as t
from tools import make_woods

# ── 小数据验证 ──────────────────────────────────────────────────
cases = []
groups = [
    ([10, 10, 10], 3, 10),
    ([10, 10, 10], 6, 5),
    ([10, 10, 10], 7, 3),
    ([12, 12, 12], 8, 4),
    ([1, 1, 1], 3, 1),
    ([7], 1, 7),
    ([7], 8, 0),
    ([], 1, 0),
    ([5, 7, 9], 3, 5),
    ([2, 3, 5, 7, 11], 10, 2),
]
for woods, M, want in groups:
    got = t.brute_max_wood_length(list(woods), M)
    cases.append([str(woods) + ' M=' + str(M), got, want])

# ── 暴力 vs 二分对拍 ────────────────────────────────────────────
import random
random.seed(20261111)
pairs = []
for _ in range(50):
    n = random.randint(1, 10)
    woods = [random.randint(1, 60) for _ in range(n)]
    M = random.randint(1, 20)
    b = t.brute_max_wood_length(list(woods), M)
    bs = t.max_wood_length(list(woods), M)
    pairs.append([str(woods) + ' M=' + str(M), b, bs, b == bs])

print('PROBE ' + json.dumps([cases, pairs], ensure_ascii=False))