#!/usr/bin/env python3
"""探针 2 · 链退化（独立数据）

用小规模 n=100 的链，验证路径压缩后第二次 find 步数远小于第一次。
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from task2_optimizations import DSU, find_steps, height_of
from tools import PROBE_DATA

N = 100

ds = DSU(N)
for i in range(N - 1):
    ds.union(i, i + 1)

h = height_of(ds.parent)

s1 = find_steps(ds, 0)

s2 = find_steps(ds, 0)

errors = 0
if h > N:
    print(f'FAIL 探针2: 树高 {h} > {N}，不可能大于 N')
    errors += 1

if s2 > s1 // 2 and s1 > 1:
    print(f'FAIL 探针2: 路径压缩没生效？第 1 次 {s1} 步，第 2 次 {s2} 步')
    errors += 1

if errors == 0:
    print(f'OK 探针2: 链退化测试通过（树高 {h}，第 1 次 {s1} 步，第 2 次 {s2} 步）')
else:
    print(f'探针2: {errors} 个错误')
    sys.exit(1)