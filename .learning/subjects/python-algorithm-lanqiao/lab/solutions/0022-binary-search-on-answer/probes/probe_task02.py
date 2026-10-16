"""probes/probe_task02.py · 任务 2 的判分探针（给好的，别改）
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import task02_river_hopping as t
from tools import make_river_stones

# ── 小数据 ──────────────────────────────────────────────────────
cases = []
groups = [
    ([2, 11, 14, 17, 21], 25, 2, 4),        # 课件数据
    ([2, 11, 14, 17, 21], 25, 0, 2),        # 不移→最小间距 2
    ([2, 11, 14, 17, 21], 25, 3, 6),        # 移 3 块 → 最大间距 6
    ([5, 10], 15, 1, 5),                    # 移 1 块 → 最大最小间距仍是 5
    ([5, 10], 15, 0, 5),                    # 不移 → 间隔 5, 5, 5 → 最小 5
    ([5, 10], 15, 1, 5),                    # 移 1 块 → 最大最小间距 5
    ([5, 10], 15, 2, 5),                    # 移 2 块 → 移除所有石头, 最大最小间距 5
    ([], 10, 0, 10),                        # 无石头 → 整个河面
    ([3], 10, 0, 3),                        # 一块石头不移
    ([3], 10, 1, 10),                       # 一块石头移掉
]
for stones, river_len, remove, want in groups:
    got = t.max_min_gap(list(stones), river_len, remove)
    cases.append([str(stones) + ' len=' + str(river_len) + ' rm=' + str(remove), got, want])

# ── 规模数据 ────────────────────────────────────────────────────
scales = []
for river_len in [50, 100, 500]:
    stones = make_river_stones(river_len, min(river_len // 5, 10))
    remove = len(stones) // 2
    got = t.max_min_gap(stones, river_len, remove)
    scales.append([river_len, len(stones), remove, got])

print('PROBE ' + json.dumps([cases, scales], ensure_ascii=False))