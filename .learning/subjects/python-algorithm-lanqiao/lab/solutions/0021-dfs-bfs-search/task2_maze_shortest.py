"""任务 2 · 迷宫最短路：为什么这一步非得用 BFS

同一道题「从起点走到终点，最少几步」要写五段：

  TODO 1  bfs_steps(n, m, blocked, start, target)     BFS：交回最少步数（走不到交回 -1）
  TODO 2  bfs_treasure(n, m, blocked, start, target)  同一套模板再解一道题：
                                                       走到目标时顺手交回捡到的宝箱个数
  TODO 3  dfs_steps(n, m, blocked, start, target)     DFS：把所有路都试一遍，取最短
  TODO 4  dfs_calls(n, m, blocked, start, target)     同一个 DFS，只数「递归调用了几次」
  TODO 5  dfs_calls_limited(..., limit)               带**调用次数上限**的版本：
                                                       超过上限立刻交回 (None, calls)

步数是跟格子**一起存进队列的**（课件「从起点往外走」那一节）：
队列里放 (行, 列, 走了几步)，每出队一个格子就把邻居写成 d + 1 再入队。
不要在 BFS 外面另外维护一个「当前第几层」的变量——同一个时刻队列里
可能同时存在第 3 层和第 4 层的格子，用全局变量根本分不开。

出队的时机也要留意：**BFS 第一次把终点弹出队列时，那个步数就是最短的**
（一层一层扩，终点不可能有更短的路还没被走到）。DFS 没有这个性质，
它得把所有路试完才敢下结论——TODO 3/4/5 就是它的代价。

这三段 DFS 都是递归写法，而且都**不改递归上限**：本文件用到的最大规模是 12×12，
一步一格的话深度最多几十层，撞不上那个 1000 的线（课件里爆栈的是「一条几千格的
长走廊」那种形状，不是这里）。要留意的是另一件事：**它是指数级的**。
所以 TODO 5 给了一个调用次数上限——判分与主块都用它，免得一段代码跑十分钟。

接口：文件名、函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那五段。

跑： py task2_maze_shortest.py
判： py run_tests.py
"""

from collections import deque

from tools import (DIRS, make_grid, make_maze, path_string, show_count,
                   show_label, show_note, show_pair, show_same, show_time, timed)

# ── 给好的数据（别改）──────────────────────────────────────────────

# 15×15 的迷宫，425 个墙格；起点 (0, 0)、终点 (14, 14)
MAZE = make_maze()
MN, MM = 15, 15
MAZE_START = (0, 0)
MAZE_TARGET = (14, 14)

# 空方格图：没有墙、每走一步代价一样，边长 4 / 6 / 8 / 12
OPEN = {size: make_grid(size, size, []) for size in (4, 6, 8, 12)}

# 调用次数上限：DFS 的调用次数随边长指数增长，留着它免得跑太久。
CALL_LIMIT = 400000


# ══ TODO 1 ═════════════════════════════════════════════════════
# 补 bfs_steps：BFS 求最少步数，走不到交回 -1。
#   seen 与 q 都按上面那两行给好的样子写；队列里放三元组 (行, 列, 步数)；
#   起点先标 seen 再入队（**入队的那一刻就标记**）；
#   每弹出一个就判一次「是不是终点」，是就直接交回那个步数；
#   不是就把四个邻居里没去过、不是墙的标上 seen、按 d + 1 入队。
#   数不出步数时交回 -1（走不到）——注意别把「走不到」与「0 步」混了。
def bfs_steps(n, m, blocked, start, target):
    seen = [[False] * m for _ in range(n)]
    q = deque([(start[0], start[1], 0)])
    seen[start[0]][start[1]] = True
    while q:
        r, c, d = q.popleft()
        if (r, c) == target:
            return d
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and not blocked[nr][nc] and not seen[nr][nc]:
                seen[nr][nc] = True
                q.append((nr, nc, d + 1))
    return -1


# ══ TODO 2 ═════════════════════════════════════════════════════
# 补 bfs_treasure：同一套模板解另一道题——从 start 往 target 走，
# 沿途捡宝箱，走到 target 的那一刻交回 (最少步数, 捡到的宝箱个数)。
#   宝箱的位置在 blocked_treasure 那一张表里（True 表示这格有宝箱）。
#   **别绕路去捡**：只走最短路。
#   提示：把「捡了几个」跟步数一起放进队列——队列里存
#   (行, 列, 步数, 到这一格为止捡到的个数)，这才叫「状态跟着一起带」。
#   起点的宝箱也要算上；走不到就交回 (-1, 0)。
#   这一份用的那张图上，起点到终点的**最短路只有一条**，
#   所以「最短路上捡到几个」是个确定的数，判分就拿这个数对。
def bfs_treasure(n, m, blocked, blocked_treasure, start, target):
    seen = [[False] * m for _ in range(n)]
    start_boxes = 1 if blocked_treasure[start[0]][start[1]] else 0
    q = deque([(start[0], start[1], 0, start_boxes)])
    seen[start[0]][start[1]] = True
    while q:
        r, c, d, boxes = q.popleft()
        if (r, c) == target:
            return d, boxes
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and not blocked[nr][nc] and not seen[nr][nc]:
                seen[nr][nc] = True
                nxt = boxes + (1 if blocked_treasure[nr][nc] else 0)
                q.append((nr, nc, d + 1, nxt))
    return -1, 0


# ══ TODO 3 ═════════════════════════════════════════════════════
# 补 dfs_steps：DFS 求最少步数——把所有路都试一遍，取最短的那条。
#   内层写一个递归的 walk(r, c, d)：
#     走到 target 就拿 d 去更新 best；
#     否则把当前格标记 seen，按 DIRS 试四个邻居（没越界、不是墙、没去过就递归），
#     **试完把 seen 收回来**（seen[r][c] = False）——不收回就走不出第二条路，
#     best 里的那条路常常不是最短的。
#   走不到交回 -1。best 与 seen 是外层函数的局部名字，内层直接改它们就行
#   （best 用一个单元素列表 [None]，内层改 best[0]）。
def dfs_steps(n, m, blocked, start, target):
    best = [None]
    seen = [[False] * m for _ in range(n)]

    def walk(r, c, d):
        if (r, c) == target:
            if best[0] is None or d < best[0]:
                best[0] = d
            return
        seen[r][c] = True
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and not blocked[nr][nc] and not seen[nr][nc]:
                walk(nr, nc, d + 1)
        seen[r][c] = False

    walk(start[0], start[1], 0)
    return -1 if best[0] is None else best[0]


# ══ TODO 4 ═════════════════════════════════════════════════════
# 补 dfs_calls：与 TODO 3 一模一样的搜索，只多交回一个数——
# **递归调用了几次**（每进一次 walk 就加一）。
#   这个数就是这一课要看的量：它不加限也会算完，只是随边长指数增长。
def dfs_calls(n, m, blocked, start, target):
    best = [None]
    seen = [[False] * m for _ in range(n)]
    calls = [0]

    def walk(r, c, d):
        calls[0] += 1
        if (r, c) == target:
            if best[0] is None or d < best[0]:
                best[0] = d
            return
        seen[r][c] = True
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and not blocked[nr][nc] and not seen[nr][nc]:
                walk(nr, nc, d + 1)
        seen[r][c] = False

    walk(start[0], start[1], 0)
    return (-1 if best[0] is None else best[0]), calls[0]


# ══ TODO 5 ═════════════════════════════════════════════════════
# 补 dfs_calls_limited：同一个 DFS，但**调用次数超过 limit 就立刻收手**，
# 交回 (None, calls)：第一个 None 表示「没算出答案、是跑不完被叫停的」，
# 不是「走不到」（走不到交回 (-1, calls)）。
#   内层递归每进去一次就把计数加一，加完立刻判一次「超过 limit 了吗」，
#   超了就交回（用 nonlocal 或单元素列表都行）。
#   判分与主块拿这个函数在 12×12 上量 DFS 的代价——课本上 6×6 的 DFS
#   要跑 9.68 秒、1847 万次调用，12×12 按这个势头是根本算不完的，
#   所以我们不硬等它，而是给它一个上限、看它撞上来。
def dfs_calls_limited(n, m, blocked, start, target, limit):
    best = [None]
    seen = [[False] * m for _ in range(n)]
    calls = [0]

    def walk(r, c, d):
        calls[0] += 1
        if calls[0] > limit:
            return
        if (r, c) == target:
            if best[0] is None or d < best[0]:
                best[0] = d
            return
        seen[r][c] = True
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and not blocked[nr][nc] and not seen[nr][nc]:
                walk(nr, nc, d + 1)
                if calls[0] > limit:
                    return
        seen[r][c] = False

    walk(start[0], start[1], 0)
    if calls[0] > limit or best[0] is None:
        return None, calls[0]
    return best[0], calls[0]


if __name__ == '__main__':                       # 别改：这层守卫让判分 import 它时不出声
    # ── 1. 迷宫：BFS 给出最少步数；DFS 在同一个迷宫上跑不完（别改）──
    maze_steps = bfs_steps(MN, MM, MAZE, MAZE_START, MAZE_TARGET)             # 别改
    maze_dfs, maze_calls = dfs_calls_limited(MN, MM, MAZE, MAZE_START, MAZE_TARGET, CALL_LIMIT)   # 别改
    show_count('01', '迷宫 BFS 最少步数', maze_steps)                          # 别改
    show_same('迷宫 DFS 步数一致', maze_steps, maze_dfs)                        # 别改
    show_label('迷宫 DFS 交回', maze_dfs)                                       # 别改
    show_count('02', '迷宫 DFS 调用次数', maze_calls)                           # 别改
    show_label('迷宫 DFS 撞上限了吗', maze_calls > CALL_LIMIT)                  # 别改
    show_label('迷宫 直线距离 28 步 而最短路', maze_steps)                       # 别改

    # ── 2. 空方格图上：答案一样、代价差得离谱（别改）─────────────
    for size in (4, 6, 8, 12):                                               # 别改
        grid = OPEN[size]                                                     # 别改
        target = (size - 1, size - 1)                                         # 别改
        steps = bfs_steps(size, size, grid, (0, 0), target)                   # 别改
        dfs_len, calls = dfs_calls_limited(size, size, grid, (0, 0), target, CALL_LIMIT)   # 别改
        if calls > CALL_LIMIT:                                                # 别改
            note = '超过调用上限 ' + str(CALL_LIMIT) + ' 次，跑不完'           # 别改
        else:                                                                # 别改
            note = 'BFS ' + str(dfs_len) + ' 步，与 BFS 一致 ' + str(dfs_len == steps)   # 别改
        print('方格 ' + str(size) + 'x' + str(size), steps, calls, note)       # 别改

    # ── 3. 6×6 那一档：课本量过 DFS 要 9.68 秒（这里带上限量）（别改）─
    grid6 = OPEN[6]                                                          # 别改
    t6 = (5, 5)                                                              # 别改
    steps6, t_bfs6 = timed(bfs_steps, 6, 6, grid6, (0, 0), t6)                # 别改
    _, t_dfs6 = timed(dfs_calls_limited, 6, 6, grid6, (0, 0), t6, CALL_LIMIT)  # 别改
    show_time('01', 'BFS', '6x6', t_bfs6)                                     # 别改
    show_time('02', 'DFS 带上限', '6x6', t_dfs6)                               # 别改
    show_count('03', '6x6 最少步数', steps6)                                   # 别改
    # 倍数 1：BFS 与**不带限**的 DFS 在同一档规模上各花了多少代价
    grid5x5 = make_grid(5, 5, [])                                            # 别改
    _, calls5 = dfs_calls(5, 5, grid5x5, (0, 0), (4, 4))                      # 别改
    b5, _ = timed(bfs_steps, 5, 5, grid5x5, (0, 0), (4, 4))                   # 别改
    show_note('倍数 01 DFS 调用次数', str(calls5) + ' 次，BFS 只看了 ' + str(b5) + ' 步')   # 别改

    # ── 3b. 5×5 空方格图：两版都给出最短的那个步数，代价差四个数量级（别改）─
    grid5, t5 = grid5x5, (4, 4)                                              # 别改
    d5 = dfs_steps(5, 5, grid5, (0, 0), t5)                                   # 别改
    b5_steps = bfs_steps(5, 5, grid5, (0, 0), t5)                             # 别改
    dfs_c5 = dfs_calls(5, 5, grid5, (0, 0), t5)                               # 别改
    show_label('5x5 DFS 步数', d5)                                            # 别改
    show_label('5x5 BFS 步数', b5_steps)                                       # 别改
    show_label('5x5 DFS 调用次数', dfs_c5[1])                                  # 别改
    show_label('5x5 两版步数一致', d5 == b5_steps)                             # 别改

    # ── 4. 同一个搜法、两道题：宝箱跟着状态一起带（别改）─────────
    # 用迷宫那张图：它的最短路只有一条，四个宝箱都摆在这条路上
    treasure = make_grid(MN, MM, [])                                          # 别改
    for r, c in ((2, 3), (6, 10), (10, 5), (12, 14)):                         # 别改
        treasure[r][c] = True                                                 # 别改
    steps, boxes = bfs_treasure(MN, MM, MAZE, treasure, MAZE_START, MAZE_TARGET)   # 别改
    show_pair('宝箱 最少步数 与 捡到个数', steps, boxes)                        # 别改
    show_label('宝箱 四个宝箱都在这条最短路上', True)                            # 别改
    show_count('04', '宝箱 捡到个数', boxes)                                    # 别改

    # ── 5. 两版 DFS 的对照（别改）───────────────────────────────
    grid12 = OPEN[12]                                                        # 别改
    t12 = (11, 11)                                                           # 别改
    b12, _ = timed(bfs_steps, 12, 12, grid12, (0, 0), t12)                    # 别改
    d12, c12 = dfs_calls_limited(12, 12, grid12, (0, 0), t12, CALL_LIMIT)     # 别改
    show_label('12x12 BFS 步数', b12)                                          # 别改
    show_label('12x12 DFS 步数', d12)                                          # 别改
    show_label('12x12 DFS 也算出来了吗', d12 is not None)                       # 别改
    show_label('12x12 DFS 撞上上限了吗', c12 > CALL_LIMIT)                     # 别改
    show_note('12x12 路径前后', path_string([(0, 0), (0, 1)]) + ' … ' + path_string([t12]))  # 别改
