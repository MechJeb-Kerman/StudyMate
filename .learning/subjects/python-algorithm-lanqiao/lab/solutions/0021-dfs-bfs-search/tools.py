"""tools.py · lab 0021 的公共工具（给好的，别改）

这里放六样东西，四个任务都从这里取：

  1. 图的两种表示与造图（都是第 20 课那一课的约定）
     make_grid(n, m, cells)   网格图：`True` 表示**不能走**（墙），`False` 表示能走。
                              cells 是要砌成墙的那些 (行, 列)。
     make_adj(n, edges)       邻接表：n 个点（编号 0..n-1）+ 一串无向边，
                              两边都加一次（第 20 课那节课件里量过：只加一个方向，
                              图就变了）。
     make_maze()              本课用的那个迷宫：15×15、425 个墙格。
     BLOCKED_BIG / BIG_EDGES  连通、不连通两张大图（2500 点），任务 1 与任务 3 共用。

  2. 连通块的判定与第 19 课那种并查集
     count_bfs(n, adj, start) 从这里出发能走到几个点（BFS 版，只用来做对照）
     UnionFind(n) / uf.find(x) / uf.union(a, b) / uf.components()
                              并查集：不遍历，只合并，最后数一共有几组。

  3. 打印：格式就是判分接口
     show_count(index, label, value)      计数 NN <label> <value>
     show_time(index, label, extra, sec)  耗时 NN <label> <n=…> <秒数> 秒
     show_label(label, value)             <label> <value>
     show_pair(label, first, second)      <label> <first> <second>
     show_note(label, note)               <label> <note>（备注那一列）
     show_check(label, ok, note='')       <label> True  或  <label> False <note>
     show_same(label, a, b)               <label> True/False <另一个值>

  4. 计时
     timed(func, *args)       跑一次并量耗时 → (函数交回的值, 秒数)。

  5. 小工具
     shifts(n, m, r, c)       从一个格子出发、按「下 上 右 左」的固定次序能走到的邻居。
     path_string(path)        把一串格子写成 "(0,0)->(1,0)" 这样一行。

  6. 判分要读的常量
     DIRS                     四个方向：下 上 右 左。任务里的 DFS/BFS 要照这个次序走，
                              因为判分拿两份**独立的实现**做对照，
                              而「先走哪个邻居」会决定 try 出来的那条路径长什么样。

这两点合起来是一句话：**判分读的是你脚本自己 print 出来的那些行**，
所以第 3 节的打印函数与第 6 节的 DIRS 别改。
留白版原样跑时，所有计数都会打出 0、答案行会打出空表或 None——那是起点，不是 bug。
"""

# ── 搜索方向：下 上 右 左（顺序是判分接口，别改）───────────────────────

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


# ── 一、图的两种表示与造图 ──────────────────────────────────────────────


def make_grid(n, m, cells):
    """网格图：n 行 m 列，cells 里的 (行, 列) 砌成墙。

    返回 blocked：`blocked[r][c] is True` 表示**不能走**（墙），
    `False` 表示能走。与课件 make_blocked 的口径逐字相同。
    """
    blocked = [[False] * m for _ in range(n)]
    for r, c in cells:
        blocked[r][c] = True
    return blocked


def make_adj(n, edges):
    """邻接表：n 个点（编号 0..n-1）加一串无向边，返回长度 n 的表。

    无向边的两边都要加——第 20 课量过：只加一个方向，图就不是那张图了。
    """
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return adj


def make_maze():
    """本课用的那个迷宫：15×15 的网格，起点 (0, 0)、终点 (14, 14)。

    墙砌成「蛇形走廊」：第 3、7、11 行整行都是墙，各只留**一个缺口**——
    第 3 行留在最右（第 14 列）、第 7 行留在最左（第 0 列）、
    第 11 行又留回最右。于是要走到终点只能来回横穿三次，
    最短路 168 步，而起点与终点的直线距离只有 28 步。

    量这个迷宫之前留意一句：**迷宫必须先连通**，否则 BFS 交回的是 -1（走不到），
    量出来的就不是「最少步数」了。改这张图之后，
    先拿 tools.count_reach_grid(15, 15, MAZE, [(0, 0)]) 看一眼是不是 225
    （15×15 的格子全走得到），不是 225 就说明缺口留错了。
    """
    walls = []
    for r, gap in ((3, 14), (7, 0), (11, 14)):
        for c in range(0, 15):
            if c != gap:
                walls.append((r, c))
    return make_grid(15, 15, walls)


def make_big_graph():
    """两张大图（各 2500 个点），任务 1 与任务 3 共用：

      BLOCKED_BIG  50×50 的网格，墙砌成 5 条竖墙与 6 条横墙，**整张图连通**——
                   从 (0, 0) 出发能走到全部 2500 个格子。
      BIG_EDGES    50×50 的网格上那一套点边列表（每个格子连到右、下两个邻居），
                   再单独挖掉右下角那 5×5 一小块——同一些点、同一批边，
                   但是**不连通**（能走 2475 个）。

    两张大图一样大，正好用来分辨「答案对不上」的两种原因：
    容器用错（集合版 vs 列表版只差快慢）与图看错（点数、边、起点读错）。
    """
    n = m = 50
    walls = []
    for c in (8, 16, 24, 32, 40):
        for r in range(0, n):
            if r % 7 != 5:
                walls.append((r, c))
    for r in (7, 14, 21, 28, 35, 42):
        for c in range(0, m):
            if c % 6 != 3:
                walls.append((r, c))
    blocked = make_grid(n, m, walls)

    edges = []
    for r in range(n):
        for c in range(m):
            u = r * m + c
            if c + 1 < m:
                edges.append((u, u + 1))
            if r + 1 < n:
                edges.append((u, u + m))
    return blocked, edges


BLOCKED_BIG, BIG_EDGES = make_big_graph()


def shifts(n, m, r, c):
    """从一个格子出发、按 DIRS 那个固定次序能直接走到的邻居（不判墙、不判去过）。

    只用来对拍：它与任务里手写的四行 if 应当是同一件事。
    """
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < n and 0 <= nc < m:
            out.append((nr, nc))
    return out


def path_string(path):
    """把一串格子写成 "(0,0)->(1,0)->(1,1)" 这样一行；None 写成 None。"""
    if path is None:
        return 'None'
    return '->'.join('(' + str(r) + ',' + str(c) + ')' for r, c in path)


# ── 二、连通块：BFS 对照版与并查集 ──────────────────────────────────────


def count_bfs(n, adj, start):
    """从 start 出发、在邻接表 adj 上能走到几个点（本文件自带的 BFS 对照版）。

    这是**判分与留白骨架共用的对照**，不是任务 1 要写的那两套模板：
    任务 1 的 dfs_reach / bfs_reach 要自己写。
    """
    seen = [False] * n
    seen[start] = True
    q = [start]
    head = 0
    while head < len(q):
        u = q[head]
        head += 1
        for v in adj[u]:
            if not seen[v]:
                seen[v] = True
                q.append(v)
    return sum(1 for x in seen if x)


def count_reach_grid(n, m, blocked, starts):
    """从 starts 里这几个格子出发、一共能走到几个格子（本文件自带的对照版）。

    与 count_bfs 是同一件事，只是一个走邻接表、一个走网格。
    几个起点共用同一张 seen——两个起点通着的话，答案不是「各走一遍再相加」。
    """
    seen = [[False] * m for _ in range(n)]
    q = []
    for r, c in starts:
        if not blocked[r][c] and not seen[r][c]:
            seen[r][c] = True
            q.append((r, c))
    head = 0
    while head < len(q):
        r, c = q[head]
        head += 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and not blocked[nr][nc] and not seen[nr][nc]:
                seen[nr][nc] = True
                q.append((nr, nc))
    return sum(1 for row in seen for x in row if x)


class UnionFind:
    """第 19 课那种并查集：`find` 带路径压缩，`union` 按大小合并。

    它**不遍历**图——只是把边两端的点合并起来，最后 `components()` 数一共有几组。
    任务 3 拿它与 BFS 数出来的连通块个数对照。
    """

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.count = n

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
        self.count -= 1
        return True

    def components(self):
        """并查集数出来的连通块个数。"""
        return self.count


# ── 三、打印：格式就是判分接口 ──────────────────────────────────────────


def show_count(index, label, value):
    """打印一行计数。index 是两位编号，label 是中文标签。"""
    print('计数 ' + str(index).zfill(2) + ' ' + label + ' ' + str(value))


def show_time(index, label, extra, seconds):
    """打印一行耗时（六位小数）。extra 是规模标签，例如 'n=6x6'。"""
    print('耗时 ' + str(index).zfill(2) + ' ' + label + ' ' + str(extra)
          + ' ' + f'{seconds:.6f}' + ' 秒')


def show_label(label, value):
    """打印一行普通结果：<label> <value>。"""
    print(str(label) + ' ' + str(value))


def show_pair(label, first, second):
    """打印一行「一个标签带两个值」：<label> <first> <second>。"""
    print(str(label) + ' ' + str(first) + ' ' + str(second))


def show_note(label, note):
    """打印一行「标签 + 备注」：<label> <note>（任务 2 的爆栈那一行用它）。"""
    print(str(label) + ' ' + str(note))


def show_check(label, ok, note=''):
    """打印一行判定：<label> True 或 <label> False <备注>。"""
    tail = '' if note == '' else ' ' + str(note)
    print(str(label) + ' ' + str(bool(ok)) + tail)


def show_same(label, a, b):
    """打印一行「一致吗」以及另一个值：<label> True/False <b>。

    任务 2 用它把「两版答案一致吗」与「DFS 那条路多长」打在同一行上。
    """
    print(str(label) + ' ' + str(a == b) + ' ' + str(b))


# ── 四、计时 ────────────────────────────────────────────────────────────


def timed(func, *args):
    """跑一次并量耗时 → (函数交回的值, 秒数)。

    计时口径与第 3 课一致：前后各取一次 perf_counter、相减，
    中间不夹别的代码。
    """
    import time
    start = time.perf_counter()
    value = func(*args)
    end = time.perf_counter()
    return value, end - start
