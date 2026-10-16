#!/usr/bin/env python3
r"""P5 · 雨天迷宫（0-1 BFS）

地图上四种字符：`.` 起点与终点、`-` 裂冰、`b` 完整冰、`#` 走不过去。

走一格的代价有一条例外：
    从裂冰走到**另一格裂冰** —— 代价 0（裂缝连成一片，一步就跨过去了）
    其余任何一步（踩上完整冰、踩上没裂的地面、从地面走向裂冰）—— 代价 1
求 S 到 T 的最小总代价，到不了输出 -1。

于是边权只有 0 与 1 两种，把 BFS 的队列换成双端队列：

    这一步代价 0 → 从队**头**压进去（它和当前点同一层）
    这一步代价 1 → 从队**尾**压进去（下一层）

为什么对（不变式）：从队头取出一个点时，它的距离一定已经是最小的——
队列里任意两点的距离最多差 1，且队内距离是**单调不减**的
（代价 0 从头进、代价 1 从尾进，恰好保持有序）。所以每个点第一次被取出时
拿到的就是最短距离。

淘汰规模：点数 N = n·m，每条边最多进队一次 → O(N)。
    600×600 = 36 万点在 Python 里零点几秒；这类写法在 2000×2000（400 万点）上
    会开始吃力，再往上（比如 10^7 点）就该换更省常数的一维数组 + 手写队列。
    真正会被淘汰的是两类写法：把每一步都当 1 的普通 BFS（裂冰连片那一档的 0 丢了），
    以及「先搜一条路、再沿途打折」的贪心（它算的是某条路的代价，不是最小代价）。
"""

import sys
from collections import deque


def solve(grid, n, m):
    if grid[0][0] == '#' or grid[n - 1][m - 1] == '#':
        return -1
    dist = [[-1] * m for _ in range(n)]
    dist[0][0] = 0
    dq = deque([(0, 0)])
    while dq:
        r, c = dq.popleft()
        d = dist[r][c]
        if r == n - 1 and c == m - 1:
            return d
        step_free = grid[r][c] == '-'
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and grid[nr][nc] != '#':
                cost = 0 if (step_free and grid[nr][nc] == '-') else 1
                if dist[nr][nc] == -1 or dist[nr][nc] > d + cost:
                    dist[nr][nc] = d + cost
                    if cost == 0:
                        dq.appendleft((nr, nc))
                    else:
                        dq.append((nr, nc))
    return dist[n - 1][m - 1]


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    m = int(data[1])
    grid = [data[2 + i].decode() for i in range(n)]
    sys.stdout.write(str(solve(grid, n, m)) + '\n')


if __name__ == '__main__':
    main()
