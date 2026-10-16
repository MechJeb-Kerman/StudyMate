---
title: 搜索：把图走一遍
goal: 能写出 DFS 与 BFS 两套模板，并说出求最少步数为什么必须用 BFS。
---

## 从起点往外走

上一课把图存进了内存。这一课回答第一个问题：**从起点出发，能走到哪些点，最少几步。**

两种走法：

- **深度优先（DFS）**：走到一个点，挑一个还没去过的邻居就继续往前走；走不动了再退回来换一个。
- **广度优先（BFS）**：先把起点的所有邻居走完，再把邻居的邻居走完，一圈一圈往外扩。

两者都靠一个「记录去过哪里」的标记数组保证每个点只处理一次。这个数组叫 `visited`，用点数量大小的布尔列表就够了——它和第 15 课那个 `seen` 是同一个东西。

先用一个方格图当例子。`. ` 是能走的格子，`#` 是墙，每次可以往上、下、左、右走一格：

```python
from collections import deque

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def make_blocked(n, m, cells):
    g = [[False] * m for _ in range(n)]
    for r, c in cells:
        g[r][c] = True
    return g


def bfs(n, m, blocked, start, target):
    """从 start 一层层往外扩，返回走到 target 的最少步数。"""
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


n = m = 5
b = make_blocked(n, m, [(1, 1), (1, 2), (2, 2), (3, 2)])
print('  最少步数:', bfs(n, m, b, (0, 0), (4, 4)))
```

```text
  最少步数: 8
```

队列里存的是 `(行, 列, 走了几步)`。每出队一个格子，就把它的四个邻居里没去过、不是墙的格子入队，步数写 `d + 1`。

步数是**跟格子一起存进队列的**，不是另外维护一个「当前第几层」的变量。这样写有两个好处：不用在换层时做额外判断，而且每个格子拿到的步数天然就是它自己的——同一个时刻队列里可能同时存在第 3 层和第 4 层的格子，用一个全局变量根本分不开。

::: quiz 理解 锚点：BFS 里层数是记在哪里的
:::

::: quiz 理解 锚点：DFS 与 BFS 的搜索顺序差在哪里
:::

## visited 标记的时机

上面那段代码里有一句很容易挪错位置：`seen[nr][nc] = True` 写在**入队的时候**。

另一种写法是把它挪到**出队的时候**：入队时不看 `seen`，等出队了再检查、再标记。这样写出来的代码看起来更「顺」——先出队，再判断这个点是不是处理过，没处理过就标记并扩展。两种写法跑出来的答案完全一样：

```python
def bfs2(n, m, blocked, start, target, mark_on_push):
    """mark_on_push=True 在入队时标记；False 在出队时标记。返回 (步数, 入队次数, 队列最长)。"""
    seen = [[False] * m for _ in range(n)]
    q = deque([(start[0], start[1], 0)])
    pushes = 1
    maxq = 1
    if mark_on_push:
        seen[start[0]][start[1]] = True
    while q:
        if len(q) > maxq:
            maxq = len(q)
        r, c, d = q.popleft()
        if not mark_on_push:
            if seen[r][c]:
                continue
            seen[r][c] = True
        if (r, c) == target:
            return d, pushes, maxq
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and not blocked[nr][nc]:
                if mark_on_push:
                    if not seen[nr][nc]:
                        seen[nr][nc] = True
                        q.append((nr, nc, d + 1))
                        pushes += 1
                else:
                    q.append((nr, nc, d + 1))
                    pushes += 1
    return -1, pushes, maxq


for size in (10, 50, 100):
    e = make_blocked(size, size, [])
    d1, p1, q1 = bfs2(size, size, e, (0, 0), (size - 1, size - 1), True)
    d2, p2, q2 = bfs2(size, size, e, (0, 0), (size - 1, size - 1), False)
    print(f'  {size}x{size}: 入队时标记 步数 {d1} 入队 {p1:>6} 次 队列最长 {q1:>5}')
    print(f'  {" " * len(str(size))}      出队时标记 步数 {d2} 入队 {p2:>6} 次 队列最长 {q2:>5}  {p2 / p1:.2f} 倍')
```

```text
  10x10: 入队时标记 步数 18 入队    100 次 队列最长    10
          出队时标记 步数 18 入队    359 次 队列最长    38  3.59 倍
  50x50: 入队时标记 步数 98 入队   2500 次 队列最长    50
          出队时标记 步数 98 入队   9799 次 队列最长   198  3.92 倍
  100x100: 入队时标记 步数 198 入队  10000 次 队列最长   100
           出队时标记 步数 198 入队  39599 次 队列最长   398  3.96 倍
```

**答案一模一样，代价差近四倍。**

原因是：出队时才标记，同一个格子会被它的每个邻居各入队一次。一个格子最多有四个邻居，所以入队次数最多是点数的四倍——实测的倍数 3.59、3.92、3.96 正在往 4 收敛。队列最长的那一项也跟着涨：100×100 的图上从 100 涨到 398。

这个错误的危险程度和上一课的「无向图只加一个方向」不一样。那个会改答案，这个**不改答案、只是慢**，所以拿样例测永远测不出来，只有把数据开大、或者把入队次数打出来才看得见。

**一句话记法：入队的那一刻就标记，别等到出队。**

::: quiz 排错 锚点：visited 在出队时才标记会付出什么代价
:::

## 求最少步数只能用 BFS

DFS 也能算「最少步数」，但它的做法是**把所有路都试一遍，取最短的那条**。BFS 不是——BFS 第一次走到终点时，那个步数就是最短的。

为什么？因为 BFS 是一层一层扩的：第 $d$ 步能到的所有格子，一定在第 $d+1$ 步能到的格子之前全部出队。所以终点第一次被访问时，不可能存在另一条更短的路还没被走到。

DFS 没有这个性质。它一头扎进去，可能绕很远才到终点，而它没法因此断定「这就是最短」——必须退回来把别的路也走完。在空方格上量一下：

```python
def dfs_shortest(n, m, blocked, start, target):
    """把所有路径都试一遍，才敢说最短。返回 (最少步数, 递归调用次数)。"""
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
    return best[0], calls[0]


for size in (4, 5, 6):
    e = make_blocked(size, size, [])
    steps, calls = dfs_shortest(size, size, e, (0, 0), (size - 1, size - 1))
    best = bfs(size, size, e, (0, 0), (size - 1, size - 1))
    print(f'  {size}x{size}: BFS {best} 步   DFS {steps} 步，试了 {calls} 次')
```

```text
  4x4: BFS 6 步   DFS 6 步，试了 1271 次
  5x5: BFS 8 步   DFS 8 步，试了 90111 次
  6x6: BFS 10 步   DFS 10 步，试了 18470411 次
```

两个都给出正确答案，但 DFS 的尝试次数是 **1271 → 90111 → 18470411**：边长每加一格，次数就涨七十倍、再涨两百倍。这是指数增长，方格再大一点就再也算不完了。

| 规模 | BFS 耗时 | DFS 耗时 |
| --- | --- | --- |
| 4×4 | 0.000020 秒 | 0.000627 秒 |
| 5×5 | 0.000013 秒 | 0.039947 秒 |
| 6×6 | 0.000024 秒 | 9.678944 秒 |

（本机实测，跑两遍结果一致。BFS 那三个数在噪声里几乎没动，DFS 在翻倍。）

6×6 的方格上，DFS 已经要 9.68 秒，BFS 还是 0.000024 秒——**差四十万倍**。边长再加一格，DFS 还要按两百倍继续涨，也就是半小时上下；而竞赛的时限通常只有一两秒。这就是「求最少步数别用 DFS」的真实后果：不是答案错，是**根本跑不完**。

判断规则：**题目里出现「最少」「最短」「至少几步」，且每走一步的代价相同 —— 用 BFS，不要用 DFS。** 如果每步代价不同（比如修路费用不一样），BFS 也不够用，那是后面最短路算法的事。

::: quiz 应用 锚点：求最少步数为什么不能用 DFS
:::

## 队列该用哪种容器

BFS 需要一个「队尾进、队头出」的容器。Python 里两个候选：`list` 配 `pop(0)`，或者 `collections.deque` 配 `popleft()`。

`list.pop(0)` 要把后面所有元素往前挪一格，是 $O(\text{队列长度})$；`deque.popleft()` 是 $O(1)$。按这个说法，`list` 应该慢很多。但实测在方格图上两者**没有差别**：

| 方格图 BFS | `deque` | `list.pop(0)` | 慢多少 |
| --- | --- | --- | --- |
| 60×60 | 0.0016 秒 | 0.0014 秒 | 0.9 倍 |
| 120×120 | 0.0065 秒 | 0.0067 秒 | 1.0 倍 |
| 200×200 | 0.0199 秒 | 0.0187 秒 | 0.9 倍 |

原因在这一课开头那个数字里：**方格图的队列从来就不长。** BFS 队列里装的是「当前这一圈还没处理完的格子」，而一圈的长度就是周长。200×200 的方格有 40000 个格子，队列最长只有 798 个——挪 798 个元素的代价，和扩展这些格子的代价是同一个量级，所以看不出来。

队列真的会变长的时候，差别立刻出现。造一个「中心点连到一大堆叶子」的图（菊花图）：

```python
def bfs_star(k, use_deque):
    n = k + 1
    adj = [[] for _ in range(n)]
    for i in range(1, n):
        adj[0].append(i)
        adj[i].append(0)
    seen = [False] * n
    q = deque([0]) if use_deque else [0]
    seen[0] = True
    while q:
        u = q.popleft() if use_deque else q.pop(0)
        for v in adj[u]:
            if not seen[v]:
                seen[v] = True
                q.append(v)
```

中心的四个邻居一入队，队列就涨到 $k$ 个元素，而且一直保持那么长：

| 叶子数 | `deque` | `list.pop(0)` | 慢多少 |
| --- | --- | --- | --- |
| 20000 | 0.0027 秒 | 0.0134 秒 | 4.9 倍 |
| 50000 | 0.0066 秒 | 0.0806 秒 | 12.2 倍 |
| 100000 | 0.0110 秒 | 0.3272 秒 | 29.7 倍 |

（都是本机实测。）

结论不是「必须用 deque」，而是更准确的一句：**队列长度会不会涨到接近点数，取决于图的形状。** 方格图不会，菊花图会。既然 `deque` 用起来不比 `list` 麻烦，默认用它——省得去判断「我这张图算不算宽」。

::: quiz 应用 锚点：deque 与 list.pop(0) 什么时候才看得出差别
:::

## 迷宫、岛屿与连通块

同一套模板改几行就是三道不同的题。

**岛屿数量**：给一个由 `1`（陆地）和 `0`（海）组成的网格，问有多少块互不相连的陆地。做法是遍历每个格子，遇到没访问过的陆地就计数加一，然后从这个格子开始把整块陆地走完、全部标记。

```python
sea = [
    '11000',
    '11010',
    '00100',
    '00011',
]
n = len(sea)
m = len(sea[0])
b = make_blocked(n, m, [(r, c) for r in range(n) for c in range(m) if sea[r][c] == '0'])
seen = [[False] * m for _ in range(n)]
islands = 0
for r in range(n):
    for c in range(m):
        if b[r][c] or seen[r][c]:
            continue
        islands += 1
        q = deque([(r, c)])
        seen[r][c] = True
        while q:
            cr, cc = q.popleft()
            for dr, dc in DIRS:
                nr, nc = cr + dr, cc + dc
                if 0 <= nr < n and 0 <= nc < m and not b[nr][nc] and not seen[nr][nc]:
                    seen[nr][nc] = True
                    q.append((nr, nc))
for row in sea:
    print('    ' + row)
print('  岛屿数量', islands)
```

```text
    11000
    11010
    00100
    00011
  岛屿数量 4
```

**连通块计数**：把「陆地」换成「所有格子」，就是第 19 课用并查集数过的那个量。两条路都得同一个答案——并查集不遍历，搜索遍历，但数出来的是同一个东西。

**迷宫最短路**：和本课第一个例子的区别只在「能走的条件」。方格图判的是邻格不是墙，迷宫判的可能是「这一格能不能踩」「转向要不要额外代价」等等，模板本身不动。

给迷宫加墙时注意一点：`make_blocked` 里的 `True` 表示**不能走**，而不是「能走」。这个约定写反了程序也能跑，只是答案全错——第 20 课那个「编号错一位」是同一类问题。

::: quiz 应用 锚点：岛屿数量与连通块计数是不是同一件事
:::

## 状态也是点

三道题里的「点」都长着格子的样子，容易让人以为 BFS 只能走网格。其实不是——**任何「东西」都能当点**，包括看不见的状态。

回想第 20 课开头那四段描述里的最后一段：「若干个状态，每次操作从一个状态变到另一个状态」。那里：

- **一个状态就是一个点**。
- **一次合法操作就是一条边**，从操作前的状态指向操作后的状态。
- 起点是初始状态，终点是目标状态。
- 求「最少几步到目标状态」就是求最短路，用 BFS。
- `visited` 不再是「这个格子走过吗」，而是「这个状态出现过吗」。

迷宫是它的一个特例：状态就是「人在哪个格子」。倒水问题、开关灯、拼图、数字变换，全都是同一套模板——**把状态编码成一个能放进 `set` 或当作列表下标的东西**（一个整数、一个元组、一段字符串都行），剩下的和走迷宫一模一样。

这一步抽象做不出来，就会觉得「这题不是网格，BFS 用不上」，然后去写枚举或者 DFS。**看出状态就是点，是搜索题最重要的一步。**

::: quiz 理解 锚点：状态空间搜索里的点和边是什么
:::

## DFS 递归会爆栈

DFS 的递归写法和第 12 课一样，深度受 `sys.getrecursionlimit()` 限制。方格图上一条路最长可以走到几千格，递归写法会当场爆栈：

```python
import sys

print('  递归深度上限:', sys.getrecursionlimit())


def chain(n):
    """一条 n 格长的直走廊，递归写法。"""
    if n == 0:
        return 0
    return 1 + chain(n - 1)


def chain_stack(n):
    """同一条走廊，显式栈写法。"""
    depth = 0
    stack = [(0, n)]
    while stack:
        depth, left = stack.pop()
        if left > 0:
            stack.append((depth + 1, left - 1))
    return depth


for n in (996, 997, 998, 999, 1000):
    try:
        print(f'  走廊 {n} 格：递归写法交回 {chain(n)}')
    except RecursionError:
        print(f'  走廊 {n} 格：递归写法 RecursionError')
print('  走廊 200000 格：显式栈交回', chain_stack(200000))
```

```text
  递归深度上限: 1000
  走廊 996 格：递归写法交回 996
  走廊 997 格：递归写法交回 997
  走廊 998 格：递归写法交回 998
  走廊 999 格：递归写法 RecursionError
  走廊 1000 格：递归写法 RecursionError
  走廊 200000 格：显式栈交回 200000
```

第 12 课量过：上限 1000，实际能到 998 层。一条 1000 格长的走廊就会把递归写法的 DFS 顶爆。

两种应对：

- **改写成显式栈**。用一个列表当栈，`while stack:` 循环，不再有递归深度这回事。前几课的 DFS 都是这么写的，就是为了避开这一点。
- **调大递归上限**（`sys.setrecursionlimit(300000)`）。能顶一时，但 Python 的栈是有限的，调得太大可能真的把解释器撞崩，而且爆栈时给的是崩溃而不是报错。

竞赛里推荐第一种。方格图、隐式图这类「深度可能很深」的题，一律用显式栈写 DFS。

::: quiz 排错 锚点：DFS 递归写法在网格图上为什么容易爆栈
:::

## 这一课用到的判断

- **DFS 走一条路走到黑，BFS 一圈一圈往外扩**；两者都靠 `visited` 保证每个点只处理一次。
- **`visited` 必须在入队（或入栈）的那一刻标记，不能等到出队**：出队时标记会让同一个格子被每个邻居各入队一次，实测入队次数涨到 3.96 倍、答案却完全一样。
- **求「最少步数」必须用 BFS**：BFS 一层层扩，第一次到达即最短；DFS 得把所有路试完才敢下结论，实测在空方格上尝试次数 1271 → 90111 → 18470411、6×6 上要 9.68 秒（BFS 是 0.000024 秒）。
- **每步代价相同才谈得上「最少步数」**；代价不同要用最短路算法，不是 BFS。
- **网格 BFS 的队列长度是周长，不是点数**（200×200 的图上只有 798），所以 `deque` 和 `list.pop(0)` 在网格上没差别；菊花图上队列涨到接近点数，差别就变成 29.7 倍。默认用 `deque`。
- **BFS 的层数跟着队列里的元素一起存**：入队时写 `d + 1`，不用另外记层。
- **数连通块与岛屿数量是同一套模板**，只是「能不能走」的判断换一下；结果必然与第 19 课并查集数出的一致。
- **DFS 递归会爆栈**（上限 1000、实际 998 层），深度可能很深的题一律用显式栈写。

::: practice 上手做 | 两套模板三答题

这一课的动手部分落在 lab 里（任务与断言见 [lab/0021-dfs-bfs-search/](../lab/0021-dfs-bfs-search/)，做完对照 [lab/solutions/](../lab/solutions/)）。要做的是四件事。

1. 写出 **DFS 显式栈**与 **BFS 队列**两套模板，都能返回「从起点能到达的所有点」的个数。用同一个图跑两套模板，确认个数相同。
2. 做**迷宫最短路**：给一个带墙的网格与起点终点，BFS 交回最少步数；再故意用 DFS 写一遍同一个函数，把网格开大到 12×12，量出两者耗时并把 DFS 跑不完的现象记下来。
3. 做**岛屿数量**与**连通块计数**：前者给 `1`/`0` 网格，后者给一般的点边列表。用并查集再算一遍连通块，两组答案对照。
4. 把 BFS 改一版「出队时才标记 `visited`」，在同一个网格上打出**入队次数**与**队列最长长度**，和正确版本对照，确认答案相同而次数涨到近四倍。

:::

::: resources
- [OI Wiki · DFS（图论）](https://oi-wiki.org/graph/dfs/) | 深度优先搜索的图论口径、递归与栈、时间戳与 DFS 序
- [OI Wiki · BFS（图论）](https://oi-wiki.org/graph/bfs/) | 广度优先搜索、层数与最短步数、队列的实现
- [Python 官方文档 · collections.deque](https://docs.python.org/3/library/collections.html#collections.deque) | `popleft()` 是 O(1)，两端操作都支持
- 《算法导论（第 3 版）》第 22 章 图的基本算法 | 书 · 广度优先搜索与深度优先搜索、最短路径性质
- [第 20 课：把问题画成一张图](0020-graph-representation.html) | 上一课把图存进内存，这一课开始在图上走
:::
