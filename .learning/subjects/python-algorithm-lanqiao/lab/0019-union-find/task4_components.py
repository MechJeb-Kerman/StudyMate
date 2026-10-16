#!/usr/bin/env python3
"""任务 4 · 连通分量计数 + 邻接表遍历验证

两件事：
  1. 用并查集回答若干组询问「丙和丁是不是亲戚」，并数出连通块个数
  2. 用邻接表 DFS/BFS 再数一遍连通块，确认两个数相同

判分读三块输出（标签 = 接口，别改）。
"""

from __future__ import annotations

from collections import deque

from tools import PROBE_DATA


# ═══════════════════════════════════════════════════════════
#  你的 DSU（补全三个方法）
# ═══════════════════════════════════════════════════════════

class DSU:
    """并查集，带路径压缩 + 按大小合并。"""

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        """路径压缩。"""
        # ══ TODO 01 ══
        # 两遍走法：先找根，再把沿途结点挂到根上
        return x

    def union(self, a, b):
        """按大小合并。"""
        # ══ TODO 02 ══
        # 1. 找根，2. 判相等，3. 保证 ra 是较大的那个，4. 挂载
        return False


# ═══════════════════════════════════════════════════════════
#  邻接表遍历数连通块（补全 TODO 03）
# ═══════════════════════════════════════════════════════════

def count_components_adj(n, edges):
    """用邻接表 + BFS/DFS 数连通块个数。

    做法：
      1. 建邻接表 adj = [[] for _ in range(n)]
         for a, b in edges: adj[a].append(b); adj[b].append(a)
      2. visited = [False] * n, comps = 0
      3. 遍历所有点，没访问过的就 BFS/DFS 把整个连通块走完，comps += 1
    """
    # ══ TODO 03 ══
    # 1. 建邻接表
    # 2. visited 数组
    # 3. 遍历每个点，发现未访问的就 BFS 或 DFS 标记整块
    return 0


# ═══════════════════════════════════════════════════════════
#  主流程（别改）
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    d = PROBE_DATA['task4']
    n = d['n']
    edges = d['edges']
    queries = d['queries']

    dsu = DSU(n)
    for a, b in edges:
        dsu.union(a, b)

    # 第一部分：回答每对询问
    print('询问结果:')
    for a, b in queries:
        ans = dsu.find(a) == dsu.find(b)
        print(f'  {a} 和 {b}: {ans}')

    # 第二部分：并查集的连通块个数
    comps_dsu = sum(1 for i in range(n) if dsu.parent[i] == i)
    print(f'并查集连通块个数: {comps_dsu}')

    # 第三部分：邻接表遍历验证
    comps_adj = count_components_adj(n, edges)
    print(f'邻接表遍历连通块个数: {comps_adj}')

    same = comps_dsu == comps_adj
    print(f'两个结果一致: {same}')