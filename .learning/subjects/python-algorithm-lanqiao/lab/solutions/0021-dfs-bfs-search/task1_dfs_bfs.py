"""任务 1 · 两套模板与两种走法

这一课要写四段：

  TODO 1  dfs_reach(n, m, blocked, start)       DFS 显式栈版：从 start 能走到几个格子
  TODO 2  bfs_reach(n, m, blocked, start)       BFS 队列版：同一个问题的另一个写法
  TODO 3  dfs_walk_order(n, m, blocked, start)  DFS 访问的次序（第一个看到的是几号点……）
  TODO 4  bfs_walk_order(n, m, blocked, start)  BFS 访问的次序

四段都用**显式栈与队列**写，不写递归（课件「DFS 递归会爆栈」那一节：
递归上限 1000、实际 998 层，网格图一条路就能走到几千格）。队列从 collections
里取，本文件开头已经 import 好了。

四行邻居判断是这一课最容易写错的地方，三件事都在里面：

  * 边界与墙：0 <= nr < n and 0 <= nc < m and not blocked[nr][nc]
    （`blocked` 的 True 表示**不能走**，这个约定写反了程序也照样跑，只是答案全错）
  * 走没走过：not seen[nr][nc]
  * **标记的时机**：`seen[nr][nc] = True` 写在**入队（入栈）的那一刻**，
    不是等出队再标记。课件「visited 标记的时机」那一节量过：
    挪到出队时答案一模一样，入队次数却涨到 3.96 倍。任务 4 会把两版摆在一起。

次序一律照 tools.DIRS 那个固定次序（下 上 右 左）走——任务 3 会拿
tools.shifts()（「四行判断」的另一份实现）与它逐格对拍。

接口：文件名、函数名、上面那些给好的数据、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那四段。

跑： py task1_dfs_bfs.py
判： py run_tests.py
"""

from collections import deque

from tools import (BLOCKED_BIG, DIRS, make_adj, make_grid, show_count,
                   show_label, show_same, timed)

# ── 给好的数据（别改）──────────────────────────────────────────────

N = M = 6
# 6×6 上的一串墙，起点 (0, 0)
BLOCKED = make_grid(N, M, [(1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (4, 1), (4, 2)])
START = (0, 0)

# 第二个例子：一张 20 个点、23 条无向边的图（网格用邻接表表示的样子）。
# 1 有两条去 5 的路，一短一长：
#   短的是 1-2-3-4-5；
#   长的是 1-6-7-8-9-10-11-12-13-14-15，再从 15 回到 5（15 上还挂着 16..19）。
# 照着 DIRS 那个次序走，BFS 从 1 出发会很快摸到 5 那一侧，
# DFS 从 1 出发会一头扎进 2、3、4、5 那条短边——两串次序从第二个位置就分开了。
# 这个例子正是用来看「两种走法差在哪里」的。
G_N = 20
G_EDGES = [(1, 2), (2, 3), (3, 4), (4, 5), (1, 6), (6, 7), (7, 8), (8, 9),
           (9, 10), (10, 11), (11, 12), (12, 13), (13, 14), (14, 15), (15, 5),
           (7, 16), (9, 17), (11, 18), (13, 19), (2, 8), (4, 7), (6, 9), (11, 14)]
G_START = 1
G_ADJ = make_adj(G_N, G_EDGES)
BIG_START = (0, 0)


# ══ TODO 1 ═════════════════════════════════════════════════════
# 补 dfs_reach(n, m, blocked, start)：DFS 显式栈版，交回从 start 出发
# 能走到的格子个数（含 start 自己）。
#   seen = [[False] * m for _ in range(n)]；起点先标上 True、计数记 1；
#   stack = [start]；while stack: 弹一个出来（pop，弹的是最后一个），
#   按 DIRS 的次序看它的四个邻居，没越界、不是墙、没去过就
#   **当场标记**（seen[nr][nc] = True）、计数加一、压进栈。
#   整个图走完时计数就是答案——走不到的点自然没被数进去。
#   四行判断缺哪一条都会算错：忘了判墙会把墙数进去，
#   忘了判 seen 会在环上转不停（本文件的房子形状里就有环）。
def dfs_reach(n, m, blocked, start):
    seen = [[False] * m for _ in range(n)]
    seen[start[0]][start[1]] = True
    reach = 1
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and not blocked[nr][nc] and not seen[nr][nc]:
                seen[nr][nc] = True
                reach += 1
                stack.append((nr, nc))
    return reach


# ══ TODO 2 ═════════════════════════════════════════════════════
# 补 bfs_reach(n, m, blocked, start)：BFS 队列版，同一个问题。
#   与 TODO 1 只差容器：q = deque([start])，进队用 append、出队用 popleft。
#   次序变了不要紧——数出来的个数必须与 DFS 版一样：
#   两套模板回答的都是「从起点能走到哪些点」，只是走的先后不同。
def bfs_reach(n, m, blocked, start):
    seen = [[False] * m for _ in range(n)]
    seen[start[0]][start[1]] = True
    reach = 1
    q = deque([start])
    while q:
        r, c = q.popleft()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and not blocked[nr][nc] and not seen[nr][nc]:
                seen[nr][nc] = True
                reach += 1
                q.append((nr, nc))
    return reach


# ══ TODO 3 ═════════════════════════════════════════════════════
# 补 dfs_walk_order(n, adj, start)：在**邻接表** adj 上走一遍，
# 交回 DFS **访问的次序**——一个列表，里面是「弹出来时」记下的点号，
# 第一个是 start，长度就是能走到的点数。
#   seen = [False] * n；起点先标上 True；out 收次序；stack = [start]；
#   while stack: 弹一个出来收进 out，再把它**没去过的**邻居标上 True、压进栈。
#   次序由邻接表里邻居的排列次序决定：`for v in adj[u]` 按表里的先后一个个压，
#   先压进去的后弹出来——本文件那两个例子正是靠这一点让你看清两种走法的差别。
def dfs_walk_order(n, adj, start):
    seen = [False] * n
    seen[start] = True
    out = []
    stack = [start]
    while stack:
        u = stack.pop()
        out.append(u)
        for v in adj[u]:
            if not seen[v]:
                seen[v] = True
                stack.append(v)
    return out


# ══ TODO 4 ═════════════════════════════════════════════════════
# 补 bfs_walk_order(n, adj, start)：同一个起点、同一张邻接表，
# 交回 BFS 访问的次序（也是一个点号的列表）。
#   BFS 是「一圈一圈往外扩」：同一个点的邻居会连着被看到，再轮到邻居的邻居；
#   DFS 是「一条路走到黑」：先挑一个没去过的邻居一路往下钻。
#   所以两串次序从第二个位置起就不一样了——打印出来那两行就是这一课要看的现象。
def bfs_walk_order(n, adj, start):
    seen = [False] * n
    seen[start] = True
    out = []
    q = deque([start])
    while q:
        u = q.popleft()
        out.append(u)
        for v in adj[u]:
            if not seen[v]:
                seen[v] = True
                q.append(v)
    return out


if __name__ == '__main__':                       # 别改：这层守卫让判分 import 它时不出声
    # ── 1. 两套模板数出来的个数要一致（别改）──────────────────────
    d = dfs_reach(N, M, BLOCKED, START)                                      # 别改
    b = bfs_reach(N, M, BLOCKED, START)                                      # 别改
    show_count('01', '网格 DFS 到达', d)                                      # 别改
    show_count('02', '网格 BFS 到达', b)                                      # 别改
    show_same('两套模板个数一致', d, b)                                        # 别改

    # ── 2. 两种走法的次序差在哪里（别改）─────────────────────────
    dfs_order = dfs_walk_order(G_N, G_ADJ, G_START)                           # 别改
    bfs_order = bfs_walk_order(G_N, G_ADJ, G_START)                           # 别改
    print('次序 DFS', dfs_order)                                              # 别改
    print('次序 BFS', bfs_order)                                              # 别改
    print('次序 点数一致吗', len(dfs_order) == len(bfs_order))                 # 别改
    print('次序 第二个点一样吗', dfs_order[:2] == bfs_order[:2])               # 别改

    # ── 3. 大图上跑一遍：两套都要走完同样多的点（别改）────────────
    BIG_TOTAL = 50 * 50                                                      # 别改
    big_d, big_td = timed(dfs_reach, 50, 50, BLOCKED_BIG, BIG_START)          # 别改
    big_b, big_tb = timed(bfs_reach, 50, 50, BLOCKED_BIG, BIG_START)          # 别改
    show_count('03', '大图 DFS 到达', big_d)                                   # 别改
    show_count('04', '大图 BFS 到达', big_b)                                   # 别改
    show_label('大图 两套都走完', big_d == big_b and big_d > 0)                 # 别改
    show_label('大图 两套都没超过总点数', big_d <= BIG_TOTAL and big_b <= BIG_TOTAL)   # 别改

    # ── 4. 邻接表那张图的规模（别改）─────────────────────────────
    show_label('小图 点数', G_N)                                              # 别改
    show_label('小图 边数', len(G_EDGES))                                      # 别改
    show_label('小图 起点', G_START)                                           # 别改
