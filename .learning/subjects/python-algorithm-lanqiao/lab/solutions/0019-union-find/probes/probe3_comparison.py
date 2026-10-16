#!/usr/bin/env python3
"""探针 3 · 2×2 对照验证（独立数据）

用小规模 n=200 快速验证四种变体的树高和步数关系。
最多只能有一格「谁都不上」退化了。
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from tools import DSU_None, DSU_Compress, DSU_Size, DSU_Both, height_of, find_steps

N = 200

def measure(cls):
    d = cls(N)
    for i in range(N - 1):
        d.union(i, i + 1)
    h = height_of(d.parent)
    s1 = find_steps(d, 0)
    s2 = find_steps(d, 0)
    return h, s1, s2

results = {
    '谁都不上': measure(DSU_None),
    '只路径压缩': measure(DSU_Compress),
    '只按大小': measure(DSU_Size),
    '两个都上': measure(DSU_Both),
}

errors = 0
none_h, none_s1, none_s2 = results['谁都不上']
if none_h < N // 2:
    print(f'FAIL 探针3: 谁都不上 树高 {none_h}，应该接近 {N}（没退化？）')
    errors += 1

if none_s1 != none_s2:
    print(f'FAIL 探针3: 谁都不上 两次步数不同：{none_s1} vs {none_s2}（不该有压缩效果）')
    errors += 1

for name in ['只路径压缩', '只按大小', '两个都上']:
    h, s1, s2 = results[name]
    if s2 > s1 and s1 > 1:
        print(f'FAIL 探针3: {name} 路径压缩没生效？第1次 {s1} 步，第2次 {s2} 步')
        errors += 1

if errors == 0:
    print('OK 探针3: 2×2 对照验证通过')
    for name, (h, s1, s2) in results.items():
        print(f'  {name}: 树高 {h}, 第1次 {s1} 步, 第2次 {s2} 步')
else:
    print(f'探针3: {errors} 个错误')
    sys.exit(1)