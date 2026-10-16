"""probes/probe_task01.py · 任务 1 的判分探针（给好的，别改）

判分脚本另起一个进程跑这个文件：它 import 你的 task01_wood_cutting.py，
拿一组判分自己的数据去试 check_wood 和 max_wood_length。

最后一行以 PROBE 开头，后面是 JSON——判分脚本读的就是它。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import task01_wood_cutting as t
from tools import make_woods

# ── 小数据 ──────────────────────────────────────────────────────
cases = []
groups = [
    ([5, 7, 9], 3, 5),          # 木长 [5,7,9], 要 3 段 → x=5: 1+1+1=3≥3. x=6: 0+1+1=2<3. 答案=5
    ([5, 7, 9], 6, 3),          # 要 6 段 → x=3: 1+2+3=6≥6. x=4: 1+1+2=4<6. 答案=3
    ([12, 12, 12], 8, 4),       # 要 8 段 → x=4: 3+3+3=9≥8. x=5: 2+2+2=6<8. 答案=4
    ([1, 1, 1], 3, 1),          # 要 3 段 → x=1: 1+1+1=3. 答案=1
    ([100], 5, 20),             # 要 5 段 → x=20: 5≥5. x=21: 4<5. 答案=20
    ([7], 1, 7),                # 要 1 段 → x=7
    ([7], 8, 0),                # 要 8 段 → 不可能，答案=0
    ([], 1, 0),                 # 空数组 → 答案=0
]
for woods, M, want in groups:
    got = t.max_wood_length(list(woods), M)
    cases.append([str(woods) + ' M=' + str(M), got, want])

# ── 更多边界 ────────────────────────────────────────────────────
more_cases = []
more_groups = [
    ([10, 10, 10], 3, 10),
    ([10, 10, 10], 6, 5),
    ([10, 10, 10], 9, 3),
    ([10, 10, 10], 15, 2),
    ([2, 3, 5, 7, 11], 3, 5),
    ([2, 3, 5, 7, 11], 10, 2),
]
for woods, M, want in more_groups:
    got = t.max_wood_length(list(woods), M)
    more_cases.append([str(woods) + ' M=' + str(M), got, want])

# ── 规模数据 ────────────────────────────────────────────────────
scales = []
for n in [5, 20, 50]:
    woods = make_woods(n, 60)
    M = n // 2
    got = t.max_wood_length(woods, M)
    scales.append([n, got])

print('PROBE ' + json.dumps([cases, more_cases, scales], ensure_ascii=False))