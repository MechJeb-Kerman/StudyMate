"""任务 3 · 岛屿数量与连通块计数

同一套模板改几行就是两道题，这一份把两道都写出来，再用第 19 课的并查集对一遍。

  TODO 1  count_islands(rows)               `1`/`0` 网格里有几块互不相连的陆地
  TODO 2  count_components(n, edges)        一般的点边列表里有几个连通块（搜索版）
  TODO 3  count_components_uf(n, edges)     同一个量，用并查集再数一遍
  TODO 4  reach_all(n, adj, starts)         从这几个起点出发，一共能走到几个点

第 19 课的并查集**不遍历**图（它只是把边两端的点合并起来），搜索是**一层层走**
过去的——两条路完全不一样，数出来却必须是同一个数。这就是 TODO 2 与 TODO 3
要互相对照的原因。

TODO 4 是另一种「多个起点」的题：起点可能有重叠，也可能有一条边把两个起点
连在同一块里，所以**不能把每个起点的结果加起来**——要一张共用的 seen，
几个起点全部先标上、一起入队，最后数走过多少个点。

接口：文件名、函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那四段。

跑： py task3_islands.py
判： py run_tests.py
"""

from collections import deque

from tools import (BIG_EDGES, DIRS, UnionFind, count_bfs, count_reach_grid,
                   make_adj, make_grid, make_maze, show_count, show_label,
                   show_same, show_time, timed)

# ── 给好的数据（别改）──────────────────────────────────────────────

# 岛屿：四行 `1`/`0`。中间那两行有对角线——斜着挨着不算连在一起，
# 所以角上那些 `1` 是各自独立的陆地，不是一块。
ISLAND_ROWS = [
    '1100000',
    '0010000',
    '0100110',
    '0000101',
]

# 简化版：只有两块陆地，用来先对齐口径
ISLAND_SMALL = [
    '11000',
    '11010',
    '00100',
    '00011',
]

# 课件那一节的四行（逐字对照用）
COURSE = ['11000', '11010', '00100', '00011']


def islands_from_rows(rows):
    """把 `1`/`0` 的字符网格变成任务里用的 blocked 表（给好的，别改）。

    与课件 make_blocked 的口径一致：`True` 表示**不能走**——
    也就是 `'0'` 那块海；`'1'` 是陆地，`False`。
    （这个约定写反了程序照样跑，只是答案全错。）
    """
    n = len(rows)
    m = len(rows[0])
    return n, m, make_grid(n, m, [(r, c) for r in range(n) for c in range(m)
                                  if rows[r][c] == '0'])


# 连通块那个图：3000 个点、4002 条边，分成 7 块
C_N = 3000
C_EDGES = [(k, k + 1) for k in range(0, 3000, 500) for k in range(k, k + 499)]
C_EDGES += [(1000, 1600), (2600, 1050), (500, 900), (2500, 2999)]

# 多起点那道题：一个 15×15 的迷宫 + 四个起点（有两个起点落在墙上）
MR = MC = 15
M_BLOCKED = make_maze()
M_STARTS = [(0, 0), (14, 14), (7, 7), (10, 14)]

# 多起点那道题的另一种数据：一般的点边列表（编号 0..n-1）
G_N = 600
G_EDGES = [(k, k + 1) for k in range(0, 600, 100) for k in range(k, k + 99)]
G_EDGES += [(7, 300), (0, 5), (300, 302), (400, 401)]
G_STARTS = [0, 3, 300, 599]


# ══ TODO 1 ═════════════════════════════════════════════════════
# 补 count_islands(rows)：数 `1`/`0` 网格里有几块陆地。
#   先用给好的 islands_from_rows(rows) 拿到 (n, m, blocked)；
#   再遍历每个格子：是海、或者已经走过的，就跳过；
#   否则**计数加一**，然后从这一格起把整块陆地走完、全部标上 seen——
#   一圈一圈扩（BFS 的队列）或者一条路走到黑（DFS 的栈）都行，数出来是同一个。
#   四行判断与任务 1 一样：不越界、不是海（not blocked[nr][nc]）、没走过。
def count_islands(rows):
    # TODO 1
    return 0


# ══ TODO 2 ═════════════════════════════════════════════════════
# 补 count_components(n, edges)：n 个点（编号 0..n-1）加一串无向边，
# 交回一共有几个连通块。
#   用给好的 make_adj 把边表变成邻接表（两边各加一次），
#   然后从每个还没去过的点出发，用栈或队列把它那一块走完、标上 seen，块数加一。
#   注意：孤点（一条边也没连的）自己算一块，所以每个点都得轮到。
def count_components(n, edges):
    # TODO 2
    return 0


# ══ TODO 3 ═════════════════════════════════════════════════════
# 补 count_components_uf(n, edges)：同一个量，改用第 19 课的并查集。
#   uf = UnionFind(n)；对每条边 uf.union(a, b)；最后交回 uf.components()。
#   它**不遍历**：合并不看图的形状，只看两个端点最后属不属于同一个根。
#   所以它与 TODO 2 的答案必须一样——两条完全不同的路数出同一个数。
def count_components_uf(n, edges):
    # TODO 3
    return 0


# ══ TODO 4 ═════════════════════════════════════════════════════
# 补 reach_all(n, adj, starts)：从 starts 里这几个起点出发，一共能走到几个点。
#   几个起点共用**同一张 seen**：先把 starts 里还没标过的点全部标上 seen、
#   全部入队，然后照 BFS 走；最后数 seen 里有几个 True。
#   注意起点表里可能有重复、也可能有几个起点本来就通着——
#   所以答案不是「每个起点各走一遍再相加」。
def reach_all(n, adj, starts):
    # TODO 4
    return 0


if __name__ == '__main__':                       # 别改：这层守卫让判分 import 它时不出声
    # ── 1. 三道岛屿题（别改）────────────────────────────────────
    show_count('01', '小网格 岛屿数量', count_islands(ISLAND_SMALL))            # 别改
    show_count('02', '对角线 岛屿数量', count_islands(ISLAND_ROWS))             # 别改
    show_count('03', '课件 岛屿数量', count_islands(COURSE))                    # 别改
    show_label('对角线 网格行数', len(ISLAND_ROWS))                            # 别改

    # ── 2. 连通块：搜索版与并查集版各数一遍（别改）───────────────
    comp_search = count_components(C_N, C_EDGES)                              # 别改
    comp_uf = count_components_uf(C_N, C_EDGES)                               # 别改
    show_count('04', '连通块 搜索版', comp_search)                             # 别改
    show_count('05', '连通块 并查集版', comp_uf)                               # 别改
    show_same('连通块 两种数法一致', comp_search, comp_uf)                      # 别改

    # ── 3. 两条路各量一次（别改）─────────────────────────────────
    got_search, t_search = timed(count_components, C_N, C_EDGES)              # 别改
    got_uf, t_uf = timed(count_components_uf, C_N, C_EDGES)                   # 别改
    show_time('01', '连通块 搜索版', 'n=' + str(C_N), t_search)                # 别改
    show_time('02', '连通块 并查集版', 'n=' + str(C_N), t_uf)                  # 别改
    show_label('两条路各量一次 答案仍一致', got_search == got_uf)               # 别改

    # ── 4. 多起点：几个起点共用一张 seen（别改）──────────────────
    show_count('06', '迷宫 多起点到达', count_reach_grid(MR, MC, M_BLOCKED, M_STARTS))   # 别改
    for (r, c) in M_STARTS:                                                   # 别改
        print('起点', (r, c), '是墙吗', M_BLOCKED[r][c])                       # 别改

    # 两个起点通着的时候，答案不是「各走一遍再相加」（别改）
    BIG_EMPTY = make_grid(50, 50, [])                                         # 别改
    show_count('09', '大空图 两个起点到达', count_reach_grid(50, 50, BIG_EMPTY, [(0, 0), (49, 49)]))   # 别改
    show_label('大空图 两个起点相加是多少', 2500 + 2500)                        # 别改

    h_adj = make_adj(G_N, G_EDGES)                                            # 别改
    show_count('07', '点边列表 多起点到达', reach_all(G_N, h_adj, G_STARTS))    # 别改
    show_label('点边列表 单起点对照', count_bfs(G_N, h_adj, 0))                 # 别改

    # ── 5. 同一张图的另一种规模（别改）───────────────────────────
    show_count('08', '大图 连通块', count_components(50 * 50, BIG_EDGES))      # 别改
    show_label('大图 点数', 50 * 50)                                           # 别改
    show_label('大图 从 0 号点走得到几个', count_bfs(50 * 50, make_adj(50 * 50, BIG_EDGES), 0))   # 别改
