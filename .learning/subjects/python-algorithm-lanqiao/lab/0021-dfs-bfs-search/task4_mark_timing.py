"""任务 4 · visited 标记的时机：答案一样，代价差四倍

同一套 BFS，只改一句话的位置：

  入队时标记（正确版）：  seen[nr][nc] = True; q.append((nr, nc, d + 1))
  出队时标记（慢的那版）：q.append((nr, nc, d + 1))  —— 入队时**不看 seen**，
                          等 popleft 出来再检查、再标记

课件「visited 标记的时机」那一节量过：两种写法**跑出来的答案完全一样**，
代价却差近四倍——同一个格子会被它的每个邻居各入队一次，一个格子最多四个邻居，
所以入队次数最多是点数的四倍，实测往 3.96 倍收敛。

所以这一份要交三个数：**步数、入队次数、队列最长长度**。

  TODO 1  bfs_trace(n, m, blocked, start, target, mark_on_push)
          交回 (步数, 入队次数, 队列最长长度)；mark_on_push 是 True 就在入队时标记，
          False 就在出队时标记。两个版本都要能算完（出队时标记要多判一次 seen）。
  TODO 2  bfs_trace_grid(size, mark_on_push)
          空方格图 size×size，起点 (0, 0)、终点 (size-1, size-1)，
          再包一层调用 TODO 1。

两个版本都别改答案：这一份里**出队时标记**是要保留的写法（它是要看的对象），
不是要改的错——改掉它就看不出四倍的差距了。

接口：文件名、函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那两段。

跑： py task4_mark_timing.py
判： py run_tests.py
"""

from collections import deque

from tools import (DIRS, make_grid, make_maze, show_count, show_label,
                   show_note, show_pair, show_same, show_time, timed)

# ── 给好的数据（别改）──────────────────────────────────────────────

# 6×6 上的一串墙（与任务 1 同一张），起点 (0, 0)、终点 (5, 5)
N = M = 6
BLOCKED = make_grid(N, M, [(1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (4, 1), (4, 2)])
START = (0, 0)
TARGET = (5, 5)

# 本课第一个例子的迷宫也量一遍：起点 (0, 0)、终点 (14, 14)
MAZE = make_maze()
MAZE_START = (0, 0)
MAZE_TARGET = (14, 14)

# 空方格图那几档规模（判分读的就是这几档的入队次数）
SIZES = (6, 10, 20)


# ══ TODO 1 ═════════════════════════════════════════════════════
# 补 bfs_trace(n, m, blocked, start, target, mark_on_push)：
# 交回 (步数, 入队次数, 队列最长长度)。
#   seen = [[False] * m for _ in range(n)]
#   q = deque([(start[0], start[1], 0)])、pushes = 1、maxq = 1
#   mark_on_push 为真时，起点先标上 seen；为假时不标（等它出队再标）
#   while q:
#       先看一眼 len(q) 有没有超过 maxq（队列最长长度就是在这里记的）
#       r, c, d = q.popleft()
#       若 mark_on_push 为假：这一格要是已经见过了就 continue（同格被入队多次），
#       否则当场 seen[r][c] = True
#       是终点就交回 (d, pushes, maxq)
#       四个邻居：不越界、不是墙——
#           mark_on_push 为真：没走过就标记 + 入队 + pushes 加一
#           为假：**无条件入队**（同一格可能被每个邻居各入一次）+ pushes 加一
#   走不到交回 (-1, pushes, maxq)
#   注意「步数是跟格子一起存进队列的」：入队时写 d + 1，
#   不要另外维护一个「当前第几层」的变量。
def bfs_trace(n, m, blocked, start, target, mark_on_push):
    # TODO 1
    return -1, 0, 0


# ══ TODO 2 ═════════════════════════════════════════════════════
# 补 bfs_trace_grid(size, mark_on_push)：搭一张 size×size 的空方格图
# （make_grid(size, size, [])），起点 (0, 0)、终点 (size - 1, size - 1)，
# 把 TODO 1 的结果原样交回。
def bfs_trace_grid(size, mark_on_push):
    # TODO 2
    return -1, 0, 0


if __name__ == '__main__':                       # 别改：这层守卫让判分 import 它时不出声
    # ── 1. 有墙那张 6×6：两个版本逐项对照（别改）─────────────────
    good = bfs_trace(N, M, BLOCKED, START, TARGET, True)                      # 别改
    bad = bfs_trace(N, M, BLOCKED, START, TARGET, False)                     # 别改
    show_same('6x6 两版答案一致', good[0], bad[0])                             # 别改
    show_pair('6x6 入队时标记 入队次数 队列最长', good[1], good[2])             # 别改
    show_pair('6x6 出队时标记 入队次数 队列最长', bad[1], bad[2])               # 别改
    show_count('01', '6x6 入队时标记 入队次数', good[1])                        # 别改
    show_count('02', '6x6 出队时标记 入队次数', bad[1])                         # 别改
    if good[1] > 0:                                                          # 别改
        show_note('倍数 01 入队次数 出队时标记', f'{bad[1] / good[1]:.2f} 倍')  # 别改
    else:                                                                    # 别改
        show_note('倍数 01 入队次数 出队时标记', '还没量出来')                  # 别改

    # ── 2. 空方格图三档：两版的步数一样，入队次数一个线性、一个近四倍 ──
    for size in SIZES:                                                       # 别改
        g = bfs_trace_grid(size, True)                                        # 别改
        b = bfs_trace_grid(size, False)                                       # 别改
        show_same('方格 ' + str(size) + 'x' + str(size) + ' 两版答案一致', g[0], b[0])   # 别改
        show_count('10', '方格 ' + str(size) + 'x' + str(size) + ' 入队时标记 入队', g[1])   # 别改
        show_count('11', '方格 ' + str(size) + 'x' + str(size) + ' 出队时标记 入队', b[1])   # 别改
        show_pair('方格 ' + str(size) + 'x' + str(size) + ' 队列最长 两版', g[2], b[2])       # 别改
        if g[1] > 0:                                                          # 别改
            show_note('倍数 02 方格 ' + str(size) + 'x' + str(size), f'{b[1] / g[1]:.2f} 倍')   # 别改

    # ── 3. 迷宫上也量一遍（同一套模板，只换了那张图）（别改）──────
    maze_good = bfs_trace(15, 15, MAZE, MAZE_START, MAZE_TARGET, True)         # 别改
    maze_bad = bfs_trace(15, 15, MAZE, MAZE_START, MAZE_TARGET, False)         # 别改
    show_same('迷宫 两版答案一致', maze_good[0], maze_bad[0])                   # 别改
    show_pair('迷宫 入队次数 两版', maze_good[1], maze_bad[1])                  # 别改

    # ── 4. 60×60 那一档：同一个答案，两版的耗时（别改）───────────
    big = make_grid(60, 60, [])                                              # 别改
    tgt = (59, 59)                                                           # 别改
    steps_g, t_g = timed(bfs_trace, 60, 60, big, (0, 0), tgt, True)           # 别改
    steps_b, t_b = timed(bfs_trace, 60, 60, big, (0, 0), tgt, False)          # 别改
    show_label('60x60 入队时标记 步数', steps_g[0])                             # 别改
    show_label('60x60 出队时标记 步数', steps_b[0])                             # 别改
    show_label('60x60 两版步数一致', steps_g[0] == steps_b[0])                 # 别改
    show_time('01', '60x60 入队时标记', 'n=60x60', t_g)                        # 别改
    show_time('02', '60x60 出队时标记', 'n=60x60', t_b)                        # 别改

    # ── 5. 队列最长长度：两种写法差多少（别改）───────────────────
    show_label('队列最长 入队时标记', bfs_trace_grid(100, True)[2])             # 别改
    show_label('队列最长 出队时标记', bfs_trace_grid(100, False)[2])            # 别改
