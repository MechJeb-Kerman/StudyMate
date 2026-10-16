#!/usr/bin/env python3
"""任务 4 · 连通分量计数 + 邻接表遍历验证 —— 参考解"""

from __future__ import annotations

from collections import deque

from tools import PROBE_DATA


class DSU:
    """并查集，带路径压缩 + 按大小合并。"""

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


def count_components_adj(n, edges):
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)

    visited = [False] * n
    comps = 0

    for i in range(n):
        if not visited[i]:
            comps += 1
            q = deque([i])
            visited[i] = True
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if not visited[v]:
                        visited[v] = True
                        q.append(v)
    return comps


if __name__ == '__main__':
    d = PROBE_DATA['task4']
    n = d['n']
    edges = d['edges']
    queries = d['queries']

    dsu = DSU(n)
    for a, b in edges:
        dsu.union(a, b)

    print('询问结果:')
    for a, b in queries:
        ans = dsu.find(a) == dsu.find(b)
        print(f'  {a} 和 {b}: {ans}')

    comps_dsu = sum(1 for i in range(n) if dsu.parent[i] == i)
    print(f'并查集连通块个数: {comps_dsu}')

    comps_adj = count_components_adj(n, edges)
    print(f'邻接表遍历连通块个数: {comps_adj}')

    same = comps_dsu == comps_adj
    print(f'两个结果一致: {same}')