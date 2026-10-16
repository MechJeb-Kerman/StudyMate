#!/usr/bin/env python3
"""工具库 · 0019 并查集 lab

供五个任务与判分共用。不改。
"""

from __future__ import annotations

import random
import time


# ═══════════════════════════════════════════════════════════
#  四种 DSU 实现（按需取用）
# ═══════════════════════════════════════════════════════════

class DSU_None:
    """谁都不上 —— 基础版 DSU（固定方向合并，无优化）。"""

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
        self.parent[ra] = rb      # 固定方向：ra 挂到 rb
        return True


class DSU_Compress:
    """只路径压缩。"""

    def __init__(self, n):
        self.parent = list(range(n))

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
        self.parent[ra] = rb
        return True


class DSU_Size:
    """只按大小合并。"""

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return True


class DSU_Both:
    """两个优化都上。"""

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


# ═══════════════════════════════════════════════════════════
#  测量工具
# ═══════════════════════════════════════════════════════════

def height_of(parent):
    """返回 parent 数组表示的森林的最大树高。"""
    h = 0
    for i in range(len(parent)):
        k = 0
        x = i
        while parent[x] != x:
            x = parent[x]
            k += 1
        if k > h:
            h = k
    return h


def find_steps(dsu, x):
    """返回从 x 做一次 find 需要走的步数。"""
    steps = 0
    while dsu.parent[x] != x:
        x = dsu.parent[x]
        steps += 1
    return steps


def build_chain(n):
    """用递增边 (0,1),(1,2),...,(n-2,n-1) 建树，返回建好的 DSU。"""
    d = DSU_None(n)
    for i in range(n - 1):
        d.union(i, i + 1)
    return d


def dsu_variants():
    """返回 [(类名, 类), …] 四种变体。"""
    return [
        ('谁都不上', DSU_None),
        ('只路径压缩', DSU_Compress),
        ('只按大小', DSU_Size),
        ('两个都上', DSU_Both),
    ]


# ═══════════════════════════════════════════════════════════
#  探针数据（独立于任务）
# ═══════════════════════════════════════════════════════════

PROBE_DATA = {
    # task1: 基本连通性测试
    'task1': {
        'edges': [(0, 1), (1, 2), (3, 4), (5, 6)],
        'n': 7,
        'queries': [(0, 2), (0, 3), (2, 3)],
        'expected': {
            (0, 2): True,
            (0, 3): False,
            (2, 3): False,
            'components': 3,
        },
    },
    # task2: 链退化 (n=4000 增量边)
    'task2': {
        'n': 4000,
        'chain_n': 4000,
        'query_target': 0,
    },
    # task3: 2×2 比较 (n=2000, 20000 queries — 步数测量，不是秒数)
    'task3': {
        'n': 2000,
        'queries': 20000,
    },
    # task4: 连通分量
    'task4': {
        'n': 10,
        'edges': [(0, 1), (1, 2), (3, 4), (0, 4), (5, 6), (6, 7), (8, 9)],
        'queries': [(0, 3), (0, 2), (5, 7), (8, 9), (1, 9)],
        'expected_answers': [True, True, True, True, False],
        'expected_components': 3,
    },
}


# ═══════════════════════════════════════════════════════════
#  固定格式打印（判分接口读这些行）
# ═══════════════════════════════════════════════════════════

def show_line(label, *values):
    """打印判分要读的固定格式行。"""
    parts = [str(label)] + [str(v) for v in values]
    print(' '.join(parts))