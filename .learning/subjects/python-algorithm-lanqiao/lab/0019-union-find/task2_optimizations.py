#!/usr/bin/env python3
"""任务 2 · 路径压缩 + 按大小合并 + 链退化演示

做三件事：
  1. 给 DSU 加上「路径压缩」—— find 时把沿途的结点直接挂到根上
  2. 给 union 加上「if ra == rb: return False」守卫（少这句会死循环）
  3. 加上「按大小合并」—— 小的树挂到大的树下面

再用递增的边 (0,1),(1,2),…,(N-2,N-1) 造一条链，先量树高，再量 find(0) 两次各走几步，
与课件里的表对照。

判分读四行固定格式的输出（标签 = 接口，别改）。
"""

from __future__ import annotations

from tools import PROBE_DATA, height_of, find_steps


# ═══════════════════════════════════════════════════════════
#  改造后的 DSU
# ═══════════════════════════════════════════════════════════

class DSU:
    """带两个优化的并查集。"""

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n                     # 按大小合并要用

    def find(self, x):
        """路径压缩版。

        第一遍：沿着 parent 找到根。
        第二遍：把这一路上的结点都直接挂到根上。
        """
        # ══ TODO 01 ══
        # 第一遍：root = x; while parent[root] != root: root = parent[root]
        # 第二遍：while parent[x] != root: parent[x], x = root, parent[x]
        # 最后 return root
        return x

    def union(self, a, b):
        """按大小合并版。

        先 find 出两个根 ra, rb：
          - 如果 ra == rb，return False（重要：少了这句两个根会互相指）
          - 保证 size[ra] >= size[rb]（不够就交换）
          - 把 rb 挂到 ra 下面：parent[rb] = ra; size[ra] += size[rb]
        """
        # ══ TODO 02 ══
        # 1. ra, rb = self.find(a), self.find(b)
        # 2. 如果 ra == rb: return False
        # 3. 如果 size[ra] < size[rb]: 交换 ra, rb
        # 4. parent[rb] = ra; size[ra] += size[rb]; return True
        return False


# ═══════════════════════════════════════════════════════════
#  测链退化（别改）
# ═══════════════════════════════════════════════════════════

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