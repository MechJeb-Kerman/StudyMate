#!/usr/bin/env python3
"""任务 2 · 路径压缩 + 按大小合并 + 链退化演示 —— 参考解"""

from __future__ import annotations
from tools import PROBE_DATA, height_of, find_steps


class DSU:
    """带两个优化的并查集。"""

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return True


if __name__ == '__main__':
    N = PROBE_DATA['task2']['n']

    ds = DSU(N)
    for i in range(N - 1):
        ds.union(i, i + 1)

    h = height_of(ds.parent)
    print(f'树高 {h}')

    s1 = find_steps(ds, 0)
    print(f'find(0) 第 1 次 {s1} 步')

    s2 = find_steps(ds, 0)
    print(f'find(0) 第 2 次 {s2} 步')