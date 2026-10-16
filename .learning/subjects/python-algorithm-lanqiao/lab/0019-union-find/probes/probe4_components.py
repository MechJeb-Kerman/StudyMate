#!/usr/bin/env python3
"""探针 4 · 连通分量计数（独立数据）

用独立数据集测试 task4_components 的 DSU 和连通分量计数。
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from task4_components import DSU, count_components_adj

# 独立数据
n = 8
edges = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (6, 7)]
queries = [(0, 2), (0, 3), (3, 5), (6, 7), (1, 7)]
expected = [True, False, True, True, False]

dsu = DSU(n)
for a, b in edges:
    dsu.union(a, b)

errors = 0
for i, (a, b) in enumerate(queries):
    ans = dsu.find(a) == dsu.find(b)
    if ans != expected[i]:
        print(f'FAIL 探针4: 询问 {a} 和 {b} 得到 {ans}，期望 {expected[i]}')
        errors += 1

comps_dsu = sum(1 for i in range(n) if dsu.parent[i] == i)
comps_adj = count_components_adj(n, edges)

if comps_dsu != comps_adj:
    print(f'FAIL 探针4: 连通块数不一致 —— DSU {comps_dsu}，邻接表 {comps_adj}')
    errors += 1

if comps_dsu != 3:
    print(f'FAIL 探针4: DSU 连通块数应为 3，得到 {comps_dsu}')
    errors += 1

if errors == 0:
    print(f'OK 探针4: 连通分量测试通过（{comps_dsu} 个连通块，邻接表验证一致）')
else:
    print(f'探针4: {errors} 个错误')
    sys.exit(1)