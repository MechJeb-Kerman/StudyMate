#!/usr/bin/env python3
"""任务 1 · 写出 DSU 的基本操作

写一个 DSU 类，三个方法：
  - __init__(self, n): 建一个长度为 n 的 parent 数组，每个元素指向自己
  - find(self, x): 顺着 parent 链找到代表元（根）并返回
  - union(self, a, b): 把 a 和 b 所在集合合并，返回 True（合并了）或 False（本来就是一伙的）

然后用课件那组边 (0,1),(1,2),(3,4),(5,6) 建图，打印四行结果，与课件对照。

判分看的是 print 行（标签 = 接口，别改）。
"""

from __future__ import annotations

from tools import PROBE_DATA


# ═══════════════════════════════════════════════════════════
#  你的 DSU：补全三个方法
# ═══════════════════════════════════════════════════════════

class DSU:
    """并查集（基础版）。"""

    def __init__(self, n):
        # ══ TODO 01 ══
        # 建一个长度为 n 的列表 self.parent，其中 parent[i] = i
        self.parent = None

    def find(self, x):
        """从 x 开始循着 parent 找到代表元。"""
        # ══ TODO 02 ══
        # while 循环：只要 parent[x] != x，就令 x = parent[x]
        # 最后返回 x
        return x

    def union(self, a, b):
        """合并 a 与 b 所在的集合。

        先找到各自的代表元 ra, rb：
          - 如果 ra == rb，返回 False（已经是一伙的）
          - 否则让 parent[ra] = rb，返回 True

        注意：缺少 ra == rb 判断会导致死循环（两个根互相指）。
        """
        # ══ TODO 03 ══
        # 1. ra = self.find(a), rb = self.find(b)
        # 2. 如果 ra == rb，return False
        # 3. self.parent[ra] = rb，return True
        return False


# ═══════════════════════════════════════════════════════════
#  验证（别改）
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    d = PROBE_DATA['task1']
    n = d['n']
    edges = d['edges']

    dsu = DSU(n)
    for a, b in edges:
        dsu.union(a, b)

    # 四行判分输出（格式与标签是接口）
    q = d['queries']
    for a, b in q:
        result = dsu.find(a) == dsu.find(b)
        print(f'{a} 和 {b} 是亲戚: {result}')

    # 连通块个数 = 代表元的个数
    comps = sum(1 for i in range(n) if dsu.parent is not None and dsu.parent[i] == i)
    print(f'连通块个数: {comps}')