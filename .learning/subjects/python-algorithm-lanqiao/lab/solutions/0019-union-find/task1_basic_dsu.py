#!/usr/bin/env python3
"""任务 1 · 写出 DSU 的基本操作 —— 参考解"""

from __future__ import annotations
from tools import PROBE_DATA


class DSU:
    """并查集（基础版）。"""

    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, x):
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        self.parent[ra] = rb
        return True


if __name__ == '__main__':
    d = PROBE_DATA['task1']
    n = d['n']
    edges = d['edges']

    dsu = DSU(n)
    for a, b in edges:
        dsu.union(a, b)

    q = d['queries']
    for a, b in q:
        result = dsu.find(a) == dsu.find(b)
        print(f'{a} 和 {b} 是亲戚: {result}')

    comps = sum(1 for i in range(n) if dsu.parent[i] == i)
    print(f'连通块个数: {comps}')