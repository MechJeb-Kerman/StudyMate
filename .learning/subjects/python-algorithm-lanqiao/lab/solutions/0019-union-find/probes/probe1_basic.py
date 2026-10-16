#!/usr/bin/env python3
"""探针 1 · 基本连通性（独立数据）

import 学生的 task1_basic_dsu.DSU，用一组独立的边测试是否正确。
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from task1_basic_dsu import DSU

edges = [(2, 5), (5, 8), (0, 3), (3, 7), (9, 4)]
n = 10

dsu = DSU(n)
for a, b in edges:
    dsu.union(a, b)

checks = [
    ((2, 8), True, '2 和 8 应该连通'),
    ((0, 7), True, '0 和 7 应该连通'),
    ((2, 3), False, '2 和 3 不该连通'),
    ((1, 1), True, '自己和自己是连通的'),
    ((9, 4), True, '9 和 4 应该连通'),
    ((1, 6), False, '1 和 6 不该连通'),
]

errors = 0
for pair, expected, msg in checks:
    a, b = pair
    result = dsu.find(a) == dsu.find(b)
    if result != expected:
        print(f'FAIL 探针1: {msg} —— find({a})==find({b}) 得到 {result}，期望 {expected}')
        errors += 1

if errors == 0:
    print('OK 探针1: 基本连通性测试通过')
else:
    print(f'探针1: {errors} 个错误')
    sys.exit(1)