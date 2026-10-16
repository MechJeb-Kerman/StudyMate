#!/usr/bin/env python3
"""lab 0021 · 自动判分：跑四个任务脚本，读它们打印的行，另起探针 import 学生代码。

用法（在 lab/0021-dfs-bfs-search/ 目录里）：

    py run_tests.py

判法：
  - 四个任务各起一个进程跑，只读它们打印出来的固定格式行，不 import 学生代码；
  - 期望值不是抄来的：判分自己按课件那套口径搭图、算「能走到几个点」、
    算两串访问次序、算最短路、数岛屿与连通块，再与学生打印的行逐字对照——
    **答案对了才算过，不是「打印了就算过」**；
  - 四个任务另起**探针进程** import 学生的函数，拿判分自己的数据去试：
    任务 1 试网格与邻接表上的两套模板；任务 2 试最短路、DFS 的调用次数、
    「带调用上限的 DFS」；任务 3 试岛屿、连通块、并查集对照与多起点；
    任务 4 试两种标记时机的入队次数、队列最长长度与答案一致性。

三条口径来自课件正文：
  - **visited 在入队（入栈）那一刻就标记**：出队时才标记的话答案一样、
    入队次数涨到近四倍（课件实测 3.59、3.92、3.96）；
  - **求最少步数只能用 BFS**：DFS 得把所有路试完才敢下结论，
    它的调用次数随边长指数增长（课件实测 1271 → 90111 → 18470411）；
  - **步数跟着格子一起存进队列**，不是另外维护「当前第几层」。

DFS 那几项**一律限量**：课件里 6×6 空方格的 DFS 要跑 9.68 秒、
1847 万次调用，所以判分不把它放到大数据上——要不用小规模（4×4、5×5 空方格），
要不带上调用上限（任务 2 的 dfs_calls_limited）。秒数只判趋势不核绝对值。

退出码：0 = 四个任务都通过；1 = 还有没通过的。
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMEOUT = 180

TODO_RE = re.compile(r'TODO\s+(\d+)')
FILE_LINE_RE = re.compile(r'File "([^"]*)", line (\d+)')

TASKS = [
    ('任务 1 · 两套模板与两种走法', 'task1_dfs_bfs.py', None),
    ('任务 2 · 迷宫最短路与 DFS 的代价', 'task2_maze_shortest.py', None),
    ('任务 3 · 岛屿数量、连通块与多起点', 'task3_islands.py', None),
    ('任务 4 · visited 标记的时机', 'task4_mark_timing.py', None),
]

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

# 任务 2、任务 4 里那个调用上限（与任务文件里的 CALL_LIMIT 一致）
CALL_LIMIT = 400000

# 两个**确定值**来自课件（第 21 课「求最少步数只能用 BFS」那一节）：
# 空方格图上 DFS 的递归调用次数，4×4 是 1271、5×5 是 90111。
DFS_CALLS_4X4 = 1271
DFS_CALLS_5X5 = 90111


# ══ 参照模型：判分自己的图与口径（期望值都从这里来，不抄）══════════════════

def model_grid(n, m, cells):
    g = [[False] * m for _ in range(n)]
    for r, c in cells:
        g[r][c] = True
    return g


# 任务 1 那张 6×6 的墙（与任务文件里给好的那一串逐字相同）
WALLS_6 = [(1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (4, 1), (4, 2)]

# 任务 1 那张 20 个点、23 条边的图
G_N = 20
G_EDGES = [(1, 2), (2, 3), (3, 4), (4, 5), (1, 6), (6, 7), (7, 8), (8, 9),
           (9, 10), (10, 11), (11, 12), (12, 13), (13, 14), (14, 15), (15, 5),
           (7, 16), (9, 17), (11, 18), (13, 19), (2, 8), (4, 7), (6, 9), (11, 14)]

# 任务 3 的岛屿网格
ISLAND_SMALL = ['11000', '11010', '00100', '00011']
ISLAND_ROWS = ['1100000', '0010000', '0100110', '0000101']
COURSE_ROWS = ['11000', '11010', '00100', '00011']

# 任务 3 的连通块图（与任务文件里给好的那一串逐条相同）
C_N = 3000
C_EDGES = [(k, k + 1) for k in range(0, 3000, 500) for k in range(k, k + 499)]
C_EDGES += [(1000, 1600), (2600, 1050), (500, 900), (2500, 2999)]

# 任务 3 的多起点那张图
H_N = 600
H_EDGES = [(k, k + 1) for k in range(0, 600, 100) for k in range(k, k + 99)]
H_EDGES += [(7, 300), (0, 5), (300, 302), (400, 401)]
H_STARTS = [0, 3, 300, 599]


def model_adj(n, edges):
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return adj


def model_maze_walls():
    """与 tools.make_maze 同一张迷宫：三行墙、各留一个缺口。

    判分自己按这个规则砌一遍，不 import 学生那边的 tools —— 学生改了 tools.py
    也骗不过判分（本目录的 tools.py 是给好的，正常不该动）。
    """
    walls = []
    for r, gap in ((3, 14), (7, 0), (11, 14)):
        for c in range(0, 15):
            if c != gap:
                walls.append((r, c))
    return walls


MAZE = model_grid(15, 15, model_maze_walls())
MN = MM = 15


def model_reach_grid(n, m, blocked, start):
    """从 start 出发能走到几个格子（判分自己的实现）。"""
    seen = [[False] * m for _ in range(n)]
    seen[start[0]][start[1]] = True
    count = 1
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and not blocked[nr][nc] and not seen[nr][nc]:
                seen[nr][nc] = True
                count += 1
                stack.append((nr, nc))
    return count


def model_dfs_order(n, adj, start):
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


def model_bfs_order(n, adj, start):
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


def model_bfs_steps(n, m, blocked, start, target):
    """最少步数（判分自己的实现）；走不到交回 -1。"""
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


def model_path(n, m, blocked, start, target):
    """最短路上的一条路径（判分用父指针重建，用来算「这条路上有几个宝箱」）。"""
    seen = [[False] * m for _ in range(n)]
    par = {}
    q = deque([(start[0], start[1], 0)])
    seen[start[0]][start[1]] = True
    while q:
        r, c, d = q.popleft()
        if (r, c) == target:
            path = [(r, c)]
            cur = (r, c)
            while cur != start:
                cur = par[cur]
                path.append(cur)
            path.reverse()
            return path
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and not blocked[nr][nc] and not seen[nr][nc]:
                seen[nr][nc] = True
                par[(nr, nc)] = (r, c)
                q.append((nr, nc, d + 1))
    return None


TREASURE = [(2, 3), (6, 10), (10, 5), (12, 14)]

# 探针里另外摆的一副宝箱（8×8 空方格图上，摆在一条最短路会经过的格子上）
TREASURE_PROBE = [(1, 0), (2, 0), (7, 1), (7, 4)]


def model_treasure_probe():
    """探针那副宝箱的期望值：(最少步数, 那条最短路上有几个宝箱)。"""
    trail = model_grid(8, 8, TREASURE_PROBE)
    path = model_path(8, 8, model_grid(8, 8, []), (0, 0), (7, 7))
    if path is None:
        return None
    return len(path) - 1, sum(1 for r, c in path if trail[r][c])


def model_treasure():
    """（最少步数, 这条最短路上有几个宝箱）——判分自己算。

    注意用的是 MAZE 那张图（有墙的那张）：宝箱摆的是一条固定最短路上的格子。
    """
    trail = model_grid(MN, MM, TREASURE)
    path = model_path(MN, MM, MAZE, (0, 0), (14, 14))
    if path is None:
        return None
    boxes = sum(1 for r, c in path if trail[r][c])
    return len(path) - 1, boxes


def model_islands(rows):
    n = len(rows)
    m = len(rows[0])
    blocked = [[rows[r][c] == '0' for c in range(m)] for r in range(n)]
    seen = [[False] * m for _ in range(n)]
    islands = 0
    for r0 in range(n):
        for c0 in range(m):
            if blocked[r0][c0] or seen[r0][c0]:
                continue
            islands += 1
            seen[r0][c0] = True
            q = deque([(r0, c0)])
            while q:
                r, c = q.popleft()
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < m and not blocked[nr][nc] and not seen[nr][nc]:
                        seen[nr][nc] = True
                        q.append((nr, nc))
    return islands


def model_components(n, edges):
    adj = model_adj(n, edges)
    seen = [False] * n
    count = 0
    for s in range(n):
        if seen[s]:
            continue
        count += 1
        seen[s] = True
        stack = [s]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    stack.append(v)
    return count


def model_reach_starts(n, adj, starts):
    seen = [False] * n
    q = deque()
    for s in starts:
        if not seen[s]:
            seen[s] = True
            q.append(s)
    while q:
        u = q.popleft()
        for v in adj[u]:
            if not seen[v]:
                seen[v] = True
                q.append(v)
    return sum(1 for x in seen if x)


def model_trace(n, m, blocked, start, target, mark_on_push):
    """（步数, 入队次数, 队列最长）——两种标记时机，判分自己算。"""
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


def same(got, want):
    """逐字一致：拖尾空白不算差别，其余（顺序、元素）都算。"""
    return got == want


# ══ 跑脚本与探针 ═════════════════════════════════════════════════════════

def _env():
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    return env


def run_script(name, timeout=TIMEOUT):
    """跑一个任务脚本 → dict(status, out, note)。状态：ok / missing / crash / timeout。"""
    path = HERE / name
    if not path.is_file():
        return {'status': 'missing', 'out': '', 'note': '还没建这个文件：' + name}
    try:
        done = subprocess.run(
            [sys.executable, '-B', str(path)],
            cwd=str(HERE), env=_env(), timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'out': '',
                'note': '跑了 ' + str(timeout) + ' 秒还没结束（DFS 没限量？或者哪里死循环了）'}
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-5:])
        return {'status': 'crash', 'out': done.stdout or '',
                'err': done.stderr or '',
                'note': ('脚本报错退出（退出码 ' + str(done.returncode) + '）'
                         + todo_hint(name, done.stderr or '') + '：\n' + tail)}
    return {'status': 'ok', 'out': done.stdout or '', 'err': '', 'note': ''}


def run_probe(module, code, timeout=TIMEOUT):
    """另起一个进程 import 学生的某个任务文件，跑一小段探针代码。"""
    header = ('import json\n'
              'import sys\n'
              'sys.setrecursionlimit(1000)\n'
              'import ' + module + ' as m\n')
    try:
        done = subprocess.run(
            [sys.executable, '-B', '-c', header + code],
            cwd=str(HERE), env=_env(), timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return None, '探针跑了 ' + str(timeout) + ' 秒还没结束'
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-6:])
        return None, '探针报错退出（多半是拿到的不是能调用的函数）：\n' + tail
    for line in (done.stdout or '').splitlines():
        if line.startswith('PROBE '):
            return line[len('PROBE '):], ''
    return None, '探针没有给出结果（stdout 里没有 PROBE 行）'


def todo_hint(name, err):
    """从 traceback 里找出报错落在哪个 TODO 段；认不出来就交回空串。"""
    lineno = None
    for line in err.splitlines():
        m = FILE_LINE_RE.search(line)
        if m and m.group(1).replace('\\', '/').endswith('/' + name):
            lineno = int(m.group(2))
    if lineno is None:
        return ''
    path = HERE / name
    if not path.is_file():
        return ''
    todo = None
    for i, text in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        m = TODO_RE.search(text)
        if m and i <= lineno:
            todo = m.group(1)
    if todo is None:
        return ''
    return '，报错落在 TODO ' + todo + ' 那一段（第 ' + str(lineno) + ' 行）'


# ══ 读输出 ═══════════════════════════════════════════════════════════════

def get_line(out, prefix):
    """按前缀取一整行剩下的内容；没打到那一行就交回 None。"""
    for line in out.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def get_lines(out, prefix):
    return [line[len(prefix):].strip() for line in out.splitlines()
            if line.startswith(prefix)]


def want_line(out, prefix):
    raw = get_line(out, prefix)
    return None if raw is None else raw.split()


def show(value, limit=90):
    text = repr(value)
    return text[:limit] + '…' if len(text) > limit else text


INT_RE = re.compile(r'^-?\d+$')


def int_value(out, index):
    """取 `计数 NN 标签 值` 里的整数（从后往前找第一个像整数的段）。"""
    for entry in get_lines(out, '计数 ' + index + ' '):
        parts = entry.split()
        for piece in reversed(parts):
            if INT_RE.match(piece):
                return int(piece)
    return None


def count_text(out, index):
    for entry in get_lines(out, '计数 ' + index + ' '):
        parts = entry.split()
        for piece in reversed(parts):
            if INT_RE.match(piece):
                return piece
    return None


def label_bool(out, label):
    """取一行「标签 后面跟一个 True/False」的结果。"""
    raw = get_line(out, label)
    if raw is None:
        return None
    for piece in raw.split():
        if piece in ('True', 'False'):
            return piece == 'True'
    return None


def label_int(out, label):
    raw = get_line(out, label)
    if raw is None:
        return None
    parts = raw.split()
    if not parts:
        return None
    try:
        return int(parts[0])
    except ValueError:
        return None


def label_text(out, label):
    return get_line(out, label)


def pair_values(out, label):
    """取 `标签 值1 值2` 那两个值（原样字符串）。"""
    raw = get_line(out, label)
    if raw is None:
        return None
    parts = raw.split()
    if len(parts) < 2:
        return None
    return parts[0], parts[1]


def time_values(out, prefix, size=None):
    """取 `耗时 NN 标签 [n=…] 秒` 里的秒数（前缀匹配整行开头，按标签区分）。

    两个任务里的耗时行有两种写法：任务 3 带规模标签（`n=3000`），
    任务 1/2/4 直接写规模文字（`6x6`）。所以按**前缀**取行、再抓那一行末尾的秒数。
    """
    values = []
    for entry in get_lines(out, prefix):
        m = re.search(r'([\d.]+)\s*秒', entry)
        if m:
            values.append(float(m.group(1)))
    return values


def find_seconds(out, prefix, must=None):
    """按前缀取第一行耗时里的秒数；must 给了就要求那一行含这个子串。"""
    for line in out.splitlines():
        if line.startswith(prefix) and (must is None or must in line):
            m = re.search(r'([\d.]+)\s*秒', line)
            if m:
                return float(m.group(1))
    return None


def parse_list(text):
    if text is None:
        return None
    try:
        value = ast.literal_eval(text.strip())
    except (ValueError, SyntaxError):
        return None
    return value if isinstance(value, list) else None


# ══ 任务 1 · 两套模板与两种走法 ══════════════════════════════════════════

PROBE_TASK1 = '''
def order_of(f, n, adj, start):
    try:
        got = f(n, adj, start)
    except TypeError as exc:
        return 'TypeError: ' + str(exc)
    if isinstance(got, list) and got and all(isinstance(x, tuple) and len(x) == 2 for x in got):
        return {'pairs': [list(x) for x in got[:40]]}
    return got

out = {}
out['grid_reach_dfs'] = m.dfs_reach(6, 6, m.BLOCKED, (0, 0))
out['grid_reach_bfs'] = m.bfs_reach(6, 6, m.BLOCKED, (0, 0))

# 判分自己搭的图：一张 5×5 的空网格 + 一张有墙的网格
empty5 = [[False] * 5 for _ in range(5)]
out['empty5_dfs'] = m.dfs_reach(5, 5, empty5, (0, 0))
out['empty5_bfs'] = m.bfs_reach(5, 5, empty5, (0, 0))
out['empty5_corner_dfs'] = m.dfs_reach(5, 5, empty5, (4, 4))
walled7 = [[False] * 7 for _ in range(7)]
for r in range(7):
    for c in range(7):
        if (r + c) % 3 == 0 and (r, c) not in ((0, 0), (6, 6)):
            walled7[r][c] = True
out['walled7_dfs'] = m.dfs_reach(7, 7, walled7, (0, 0))
out['walled7_bfs'] = m.bfs_reach(7, 7, walled7, (0, 0))

# 单点图：只有起点自己能走
one = [[False]]
out['one_dfs'] = m.dfs_reach(1, 1, one, (0, 0))
out['one_bfs'] = m.bfs_reach(1, 1, one, (0, 0))

# 邻接表上的两串次序（学生那两个 walk_order 收的是点号）
adj = m.G_ADJ
out['dfs_order'] = order_of(m.dfs_walk_order, m.G_N, adj, m.G_START)
out['bfs_order'] = order_of(m.bfs_walk_order, m.G_N, adj, m.G_START)

# 判分自己搭的小图：1-2, 1-3, 2-4, 3-4（环）+ 一个孤点 5
small = [[] for _ in range(6)]
for a, b in ((1, 2), (1, 3), (2, 4), (3, 4)):
    small[a].append(b)
    small[b].append(a)
out['small_dfs'] = order_of(m.dfs_walk_order, 6, small, 1)
out['small_bfs'] = order_of(m.bfs_walk_order, 6, small, 1)

print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task1():
    checks = []
    run = run_script('task1_dfs_bfs.py')
    if run['status'] != 'ok':
        return [(False, 'task1_dfs_bfs.py 没跑通：' + run['note'])]
    out = run['out']

    xx = model_grid(6, 6, WALLS_6)
    want = model_reach_grid(6, 6, xx, (0, 0))

    # ── 一、网格上两套模板的个数 ─────────────────────────────────
    for index, label, todo in (('01', '网格 DFS 到达', 'TODO 1'), ('02', '网格 BFS 到达', 'TODO 2')):
        got = int_value(out, index)
        if got is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行：带 print 的行别改、别删'))
        elif got == want:
            checks.append((True, '计数 ' + index + '：' + label + ' ' + str(got)
                                 + '（判分自己数出来也是 ' + str(want) + '）'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + show(got) + '，期望 ' + str(want)
                           + '：' + todo + ' 只数了起点（或者四行判断没写全）。'
                             '这一张图上 (0, 0) 能走到 ' + str(want) + ' 个格子'))
    value = label_bool(out, '两套模板个数一致')
    if value is None:
        checks.append((False, '没看到「两套模板个数一致 …」这一行'))
    elif value:
        checks.append((True, '两套模板个数一致 True（两套模板回答的是同一个问题）'))
    else:
        checks.append((False, '两套模板个数一致 打出 False：TODO 1 与 TODO 2 数出来的必须一样，'
                              '对不上说明其中一套的四行判断写错了'))

    # ── 二、两种走法的次序 ───────────────────────────────────────
    dfs_order = parse_list(label_text(out, '次序 DFS') or '')
    bfs_order = parse_list(label_text(out, '次序 BFS') or '')
    want_dfs = model_dfs_order(G_N, model_adj(G_N, G_EDGES), 1)
    want_bfs = model_bfs_order(G_N, model_adj(G_N, G_EDGES), 1)
    if dfs_order is None or bfs_order is None:
        checks.append((False, '没看到「次序 DFS …」「次序 BFS …」这两行：'
                              'TODO 3、TODO 4 还没交出列表'))
    else:
        if same(dfs_order, want_dfs):
            checks.append((True, '次序 DFS 与判分自己算的一致（' + str(len(dfs_order)) + ' 个点，'
                                 '第一个是 ' + str(dfs_order[0]) + '，第二个是 ' + str(dfs_order[1]) + '）'))
        else:
            checks.append((False, '次序 DFS 打出 ' + show(dfs_order) + '，期望 ' + show(want_dfs)
                           + '：TODO 3 要按邻接表里邻居的先后压栈（先压的后弹）'))
        if same(bfs_order, want_bfs):
            checks.append((True, '次序 BFS 与判分自己算的一致（' + str(len(bfs_order)) + ' 个点，'
                                 '第二个是 ' + str(bfs_order[1]) + '）'))
        else:
            checks.append((False, '次序 BFS 打出 ' + show(bfs_order) + '，期望 ' + show(want_bfs)
                           + '：TODO 4 的出队要用 popleft（用 pop 就不是广度优先了）'))
        if len(dfs_order) == len(bfs_order) and dfs_order and bfs_order \
                and dfs_order[1] != bfs_order[1]:
            checks.append((True, '两串次序的第二个点不一样（' + str(dfs_order[1]) + ' vs '
                                 + str(bfs_order[1]) + '）：DFS 一条路走到黑、BFS 先扫完邻居——'
                                   '这一课要看的差别就在这一位'))
    for label, expect, note in (('次序 点数一致吗', True, '两套模板都要走完同样多的点'),
                                ('次序 第二个点一样吗', False,
                                 '两串次序从第二个位置就该分开（如果这里打出 True，'
                                 '多半是两套模板写成了同一个东西）')):
        value = label_bool(out, label)
        if value is None:
            checks.append((False, '没看到「' + label + ' …」这一行'))
        elif value == expect:
            checks.append((True, label + ' ' + str(value) + '：' + note))
        else:
            checks.append((False, label + ' 打出 ' + str(value) + '，期望 ' + str(expect)
                           + '：' + note + '（先把 TODO 3、TODO 4 交出来的两串次序对上）'))

    # ── 三、大图 ─────────────────────────────────────────────────
    big_want = model_reach_grid(50, 50, big_blocked_model(), (0, 0))
    for index, label, todo in (('03', '大图 DFS 到达', 'TODO 1'), ('04', '大图 BFS 到达', 'TODO 2')):
        got = int_value(out, index)
        if got is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        elif got == big_want:
            checks.append((True, '计数 ' + index + '：' + label + ' ' + str(got)
                                 + '（判分自己数也是 ' + str(big_want) + '，2500 个格子里有 '
                                 + str(2500 - big_want) + ' 个被墙隔开）'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + show(got) + '，期望 ' + str(big_want)
                           + '：' + todo + ' 在大图上要真的走完（' + str(big_want) + ' 个格子）'))
    value = label_bool(out, '大图 两套都走完')
    if value is None:
        checks.append((False, '没看到「大图 两套都走完 …」这一行'))
    elif value:
        checks.append((True, '大图 两套都走完 True：两套模板在大图上给出同一个数'))
    else:
        checks.append((False, '大图 两套都走完 打出 False：两套模板在大图上必须给出同一个数'
                              '（先把 TODO 1 与 TODO 2 都写出来，它们回答的是同一个问题）'))
    value = label_bool(out, '大图 两套都没超过总点数')
    if value is None:
        checks.append((False, '没看到「大图 两套都没超过总点数 …」这一行'))
    elif value:
        checks.append((True, '大图 两套都没超过总点数 True：没有把墙数进去、也没有重复计数'))
    else:
        checks.append((False, '大图 两套都没超过总点数 打出 False：数出来的比 2500 还大，'
                              '多半是 seen 只在出队时才标记、同一个格子被数了好几次'))

    # ── 四、探针 ─────────────────────────────────────────────────
    raw, err = run_probe('task1_dfs_bfs', PROBE_TASK1)
    if raw is None:
        checks.append((False, '任务 1 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)

    for name, n, m, cells, start, todo in (
            ('empty5_dfs', 5, 5, [], (0, 0), 'TODO 1'),
            ('empty5_bfs', 5, 5, [], (0, 0), 'TODO 2'),
            ('empty5_corner_dfs', 5, 5, [], (4, 4), 'TODO 1'),
            ('one_dfs', 1, 1, [], (0, 0), 'TODO 1'),
            ('one_bfs', 1, 1, [], (0, 0), 'TODO 2')):
        got = data.get(name)
        want = model_reach_grid(n, m, model_grid(n, m, cells), start)
        if got == want:
            checks.append((True, '探针：' + name + ' → ' + str(got) + '（判分自己搭的 '
                                 + str(n) + '×' + str(m) + ' 图）'))
        else:
            checks.append((False, '探针：' + name + ' 打出 ' + show(got) + '，期望 ' + str(want)
                           + '：' + todo + ' 在判分自己搭的图上也要对'))
    w7 = model_grid(7, 7, [(r, c) for r in range(7) for c in range(7)
                           if (r + c) % 3 == 0 and (r, c) not in ((0, 0), (6, 6))])
    for name, todo in (('walled7_dfs', 'TODO 1'), ('walled7_bfs', 'TODO 2')):
        got = data.get(name)
        want = model_reach_grid(7, 7, w7, (0, 0))
        if got == want:
            checks.append((True, '探针：' + name + ' → ' + str(got)
                                 + '（判分自己砌的 7×7 带墙图，起点周围被墙围了几格）'))
        else:
            checks.append((False, '探针：' + name + ' 打出 ' + show(got) + '，期望 ' + str(want)
                           + '：' + todo + ' 的四行判断里别忘了 not blocked[nr][nc]'
                             '（blocked 的 True 是**不能走**）'))

    for name, f, todo, note in (('dfs_order', model_dfs_order, 'TODO 3', 'DFS 的次序'),
                                ('bfs_order', model_bfs_order, 'TODO 4', 'BFS 的次序')):
        got = data.get(name)
        want = f(G_N, model_adj(G_N, G_EDGES), 1)
        if isinstance(got, dict) and 'pairs' in got:
            checks.append((False, '探针：' + note + ' 交回的是格子的坐标对而不是点号：'
                           + show(got['pairs'][:4]) + '——这一份的 walk_order 收的是'
                             '邻接表上的**点号**（整数），不是 (行, 列)')) 
        elif got == want:
            checks.append((True, '探针：' + note + '与判分自己算的逐项一致（' + str(want) + '）'))
        else:
            checks.append((False, '探针：' + note + '打出 ' + show(got) + '，期望 ' + show(want)
                           + '：见 ' + todo))

    small = [[] for _ in range(6)]
    for a, b in ((1, 2), (1, 3), (2, 4), (3, 4)):
        small[a].append(b)
        small[b].append(a)
    for name, f, todo in (('small_dfs', model_dfs_order, 'TODO 3'),
                          ('small_bfs', model_bfs_order, 'TODO 4')):
        got = data.get(name)
        want = f(6, small, 1)
        if got == want:
            checks.append((True, '探针：判分自己搭的那个小图上，' + name + ' → ' + str(want)))
        else:
            checks.append((False, '探针：' + name + ' 打出 ' + show(got) + '，期望 ' + show(want)
                           + '：见 ' + todo + '（这张图里 5 号点是孤点、走不到，'
                             '所以次序里不该出现它）'))
    return checks


def big_blocked_model():
    """判分自己砌那张 50×50 的大图（与 tools.BLOCKED_BIG 同一套规则）。"""
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
    return model_grid(n, m, walls)


# ══ 任务 2 · 迷宫最短路与 DFS 的代价 ═════════════════════════════════════

PROBE_TASK2 = '''
def show(v):
    if isinstance(v, tuple):
        return list(v)
    return v

out = {}
maze = m.MAZE if 'MAZE' in dir(m) else None
out['maze_steps'] = m.bfs_steps(15, 15, maze, (0, 0), (14, 14))

# 判分自己搭的空方格图：4×4 / 5×5 / 6×6，起点左上、终点右下
def opengrid(size):
    return [[False] * size for _ in range(size)]

out['open4'] = m.bfs_steps(4, 4, opengrid(4), (0, 0), (3, 3))
out['open6'] = m.bfs_steps(6, 6, opengrid(6), (0, 0), (5, 5))
out['open12'] = m.bfs_steps(12, 12, opengrid(12), (0, 0), (11, 11))

# 起点就是终点：0 步
out['same'] = m.bfs_steps(3, 3, opengrid(3), (1, 1), (1, 1))

# 走不到：一堵竖墙把左右隔开
sep = opengrid(5)
for r in range(5):
    sep[r][2] = True
out['blocked'] = m.bfs_steps(5, 5, sep, (0, 0), (0, 4))

# DFS 的调用次数：4×4 与 5×5 两个**确定值**（课件实测 1271 / 90111）
r4 = m.dfs_calls(4, 4, opengrid(4), (0, 0), (3, 3))
out['dfs4'] = list(r4) if isinstance(r4, tuple) else r4
r5 = m.dfs_calls(5, 5, opengrid(5), (0, 0), (4, 4))
out['dfs5'] = list(r5) if isinstance(r5, tuple) else r5

# 带调用上限的 DFS：上限之下要能算出答案，上限之上要交回 None
r_ok = m.dfs_calls_limited(4, 4, opengrid(4), (0, 0), (3, 3), 200000)
out['limited_ok'] = list(r_ok) if isinstance(r_ok, tuple) else r_ok
r_stop = m.dfs_calls_limited(6, 6, opengrid(6), (0, 0), (5, 5), 5000)
out['limited_stop'] = list(r_stop) if isinstance(r_stop, tuple) else r_stop

# 宝箱：判分自己摆一遍（都摆在 8×8 空方格图那条最短路会经过的格子上）
trail = [[False] * 8 for _ in range(8)]
for (r, c) in ((1, 0), (2, 0), (7, 1), (7, 4)):
    trail[r][c] = True
tg = m.bfs_treasure(8, 8, opengrid(8), trail, (0, 0), (7, 7))
out['treasure'] = list(tg) if isinstance(tg, tuple) else tg

# DFS 的步数（小规模，不带限）
out['dfs_steps_4'] = m.dfs_steps(4, 4, opengrid(4), (0, 0), (3, 3))
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task2():
    checks = []
    run = run_script('task2_maze_shortest.py')
    if run['status'] != 'ok':
        return [(False, 'task2_maze_shortest.py 没跑通：' + run['note'])]
    out = run['out']

    maze_steps = model_bfs_steps(MN, MM, MAZE, (0, 0), (14, 14))
    free = model_reach_grid(MN, MM, MAZE, (0, 0))

    # ── 一、迷宫那一行 ───────────────────────────────────────────
    got = int_value(out, '01')
    if got is None:
        checks.append((False, '没看到「计数 01 迷宫 BFS 最少步数 …」这一行：'
                              '带 print 的行别改、别删'))
    elif got == maze_steps and got > 0:
        checks.append((True, '计数 01：迷宫最少步数 ' + str(got) + '（判分自己算也是 '
                             + str(maze_steps) + '；这张图 15×15 里能走的 '
                             + str(free) + ' 个格子，直线距离只有 28 步）'))
    elif got == -1:
        checks.append((False, '计数 01 打出 -1（走不到）：TODO 1 的四行判断写错了，'
                              '或者 seen 一开始就把起点以外的格子标住了'))
    else:
        checks.append((False, '计数 01 打出 ' + show(got) + '，期望 ' + str(maze_steps)
                       + '：TODO 1 的队列里要存 (行, 列, 步数)，'
                         '出队时判一次终点、把邻居写成 d + 1 再入队'))
    value = label_bool(out, '迷宫 DFS 撞上限了吗')
    if value is None:
        checks.append((False, '没看到「迷宫 DFS 撞上限了吗 …」这一行'))
    elif value:
        checks.append((True, '迷宫 DFS 撞上限了吗 True：DFS 在 183 个格子的迷宫上'
                             '试到 ' + str(CALL_LIMIT) + ' 次还没试完——'
                               '它得把所有路都走一遍才敢说最短'))
    else:
        checks.append((False, '迷宫 DFS 撞上限了吗 打出 False：这个迷宫上 DFS 不该算得完'
                              '（它的调用次数是指数级的）。'
                              '要么 TODO 5 没在上限处收手，要么 TODO 3/4 的搜索写成 BFS 了'))
    calls = int_value(out, '02')
    if calls is None:
        checks.append((False, '没看到「计数 02 迷宫 DFS 调用次数 …」这一行'))
    elif calls > CALL_LIMIT:
        checks.append((True, '计数 02：迷宫 DFS 调用次数 ' + str(calls)
                             + '（超过上限 ' + str(CALL_LIMIT) + ' 就收手了）'))
    else:
        checks.append((False, '计数 02 打出 ' + show(calls) + '，期望大于 ' + str(CALL_LIMIT)
                       + '：TODO 5 的限量要在超过 limit 时交回 (None, calls)，'
                         'calls 是它试过的次数'))
    value = label_bool(out, '迷宫 DFS 步数一致')
    if value is None:
        checks.append((False, '没看到「迷宫 DFS 步数一致 …」这一行'))
    elif not value:
        checks.append((True, '迷宫 DFS 步数一致 False：DFS 没算出答案（None），'
                             'BFS 交回 ' + str(maze_steps) + ' 步——这正是这一课要看的现象'))
    else:
        checks.append((False, '迷宫 DFS 步数一致 打出 True：这一份里 DFS 是限量跑的，'
                              '交回 None 才对；交回步数说明 TODO 5 没在上限处收手'))
    value = label_bool(out, '迷宫 DFS 交回')
    if label_text(out, '迷宫 DFS 交回') == 'None':
        checks.append((True, '迷宫 DFS 交回 None：跑不完被叫停了（不是「走不到」——'
                             '走不到交回的是 -1）'))
    elif value is None:
        checks.append((False, '没看到「迷宫 DFS 交回 None」这一行：TODO 5 写上「超过 limit 就'
                              '交回 (None, calls)」之后，这一行才会打出 None'))
    else:
        checks.append((False, '迷宫 DFS 交回 打出 ' + show(label_text(out, '迷宫 DFS 交回'))
                       + '，期望 None：TODO 5 超过调用上限要交回 None，别交回 -1'
                         '（-1 是「走不到」的意思）'))

    # ── 二、空方格图四行 ─────────────────────────────────────────
    lines = get_lines(out, '方格 ')
    if len(lines) < 4:
        checks.append((False, '「方格 …」那四行没打全（打了 ' + str(len(lines)) + ' 行）'))
    for size in (4, 6, 8, 12):
        prefix = '方格 ' + str(size) + 'x' + str(size)
        row = want_line(out, prefix + ' ')
        want_steps = model_bfs_steps(size, size, model_grid(size, size, []), (0, 0), (size - 1, size - 1))
        if row is None or len(row) < 3:
            checks.append((False, '没看到「' + prefix + ' <步数> <调用次数> <备注>」这一行'))
            continue
        try:
            steps_got = int(row[0])
            calls_got = int(row[1])
        except ValueError:
            checks.append((False, prefix + ' 那一行读不出两个整数：' + show(' '.join(row))))
            continue
        if steps_got != want_steps:
            checks.append((False, prefix + ' 的步数打出 ' + str(steps_got) + '，期望 ' + str(want_steps)
                           + '：TODO 1 还没写对（空方格图的最短路就是两条边之和）'))
            continue
        if size == 4:
            if calls_got == DFS_CALLS_4X4:
                checks.append((True, prefix + '：BFS ' + str(steps_got) + ' 步；DFS 试了 '
                                     + str(calls_got) + ' 次（与课件那个确定值一致）'))
            else:
                checks.append((False, prefix + ' 的 DFS 调用次数打出 ' + str(calls_got) + '，期望 '
                               + str(DFS_CALLS_4X4) + '：TODO 4 每进一次 walk 加一，'
                                 '而且要把所有路都试完（seen 试完要收回来）'))
        else:
            if calls_got > CALL_LIMIT:
                checks.append((True, prefix + '：BFS ' + str(steps_got) + ' 步；DFS 试到上限 '
                                     + str(CALL_LIMIT) + ' 次就收手了（4×4 只要 '
                                     + str(DFS_CALLS_4X4) + ' 次，边长每加一格就翻几十倍）'))
            else:
                checks.append((False, prefix + ' 的 DFS 调用次数打出 ' + str(calls_got)
                               + '，期望大于 ' + str(CALL_LIMIT)
                               + '：TODO 5 的限量应当在这么大（或更大）的图上真的撞上上限'))
        if '跑不完' in ' '.join(row) and calls_got > CALL_LIMIT:
            pass
        elif size == 4 and calls_got == DFS_CALLS_4X4:
            pass
        else:
            checks.append((False, prefix + ' 那一行的备注是 ' + show(' '.join(row[2:]))
                           + '：4×4 那一档该写「与 BFS 一致」，更大的档该写「跑不完」'))

    # ── 三、耗时与倍数（只看趋势） ───────────────────────────────
    bfs_t = find_seconds(out, '耗时 01 ', '6x6')
    dfs_t = find_seconds(out, '耗时 02 ', '6x6')
    if bfs_t is None or dfs_t is None:
        checks.append((False, '没看到「耗时 01 BFS 6x6 … 秒」「耗时 02 DFS 带上限 6x6 … 秒」这两行'))
    elif bfs_t <= 0 or dfs_t <= 0:
        checks.append((False, '6×6 那两行的秒数是 0.000000：TODO 1 / TODO 5 还没写出来'))
    elif dfs_t >= bfs_t * 5:
        checks.append((True, '耗时：6×6 上 BFS ' + f'{bfs_t:.6f}' + ' 秒，'
                             '带上限的 DFS ' + f'{dfs_t:.6f}' + ' 秒，差 '
                             + f'{dfs_t / bfs_t:.1f}' + ' 倍'
                               '（秒数只判趋势不核绝对值：换台机器就变）'))
    else:
        checks.append((False, '耗时：6×6 上 BFS ' + f'{bfs_t:.6f}' + ' 秒、DFS '
                       + f'{dfs_t:.6f}' + ' 秒，差得不够多（' + f'{dfs_t / bfs_t:.2f}'
                       + ' 倍）：DFS 那一档应当明显更慢——它在把所有路试一遍'))
    raw = label_text(out, '倍数 01 DFS 调用次数')
    if raw is None:
        checks.append((False, '没看到「倍数 01 DFS 调用次数 …」这一行'))
    else:
        parts = raw.split()
        nums = [int(p) for p in parts if INT_RE.match(p)]
        if len(nums) >= 2 and nums[0] == DFS_CALLS_5X5 and nums[1] == 8:
            checks.append((True, '倍数 01：5×5 空方格上 DFS 调用 ' + str(nums[0])
                                 + ' 次，BFS 只看了 ' + str(nums[1]) + ' 步（课件的确定值）'))
        else:
            checks.append((False, '倍数 01 打出 ' + show(raw) + '，期望「' + str(DFS_CALLS_5X5)
                           + ' 次，BFS 只看了 8 步」：TODO 4 的调用次数与 TODO 1 的步数'))

    for label, expect, hint in (('5x5 DFS 步数', 8, 'TODO 3：所有路试完取最短'),
                                ('5x5 BFS 步数', 8, 'TODO 1：一层层扩'),
                                ('5x5 DFS 调用次数', DFS_CALLS_5X5, 'TODO 4：每进一次 walk 加一')):
        got = label_int(out, label)
        if got is None:
            checks.append((False, '没看到「' + label + ' …」这一行'))
        elif got == expect:
            checks.append((True, label + ' ' + str(got) + '（与判分/课件一致）'))
        else:
            checks.append((False, label + ' 打出 ' + show(got) + '，期望 ' + str(expect)
                           + '：' + hint))
    value = label_bool(out, '5x5 两版步数一致')
    if value is None:
        checks.append((False, '没看到「5x5 两版步数一致 …」这一行'))
    elif value:
        checks.append((True, '5x5 两版步数一致 True：两个都给出最短的那个步数，'
                             '代价却差四个数量级'))
    else:
        checks.append((False, '5x5 两版步数一致 打出 False：TODO 3 的 DFS 要把所有路试完'
                              '（seen 收回来）才敢说最短'))

    # ── 四、宝箱那一题 ───────────────────────────────────────────
    want_treasure = model_treasure()
    pair = pair_values(out, '宝箱 最少步数 与 捡到个数')
    if pair is None:
        checks.append((False, '没看到「宝箱 最少步数 与 捡到个数 …」这一行'))
    else:
        try:
            got_pair = (int(pair[0]), int(pair[1]))
        except ValueError:
            got_pair = None
        if got_pair == want_treasure:
            checks.append((True, '宝箱：最少步数 ' + str(got_pair[0]) + '、捡到 '
                                 + str(got_pair[1]) + ' 个（判分自己走那条最短路也是这个数）'))
        else:
            checks.append((False, '宝箱 打出 ' + show(got_pair) + '，期望 '
                           + show(list(want_treasure)) + '：TODO 2 要把'
                             '「到这一格为止捡到的个数」跟步数一起放进队列'
                             '（这一份的宝箱在 (2,3) (6,10) (10,5) (12,14) 四格上）'))
    got = int_value(out, '04')
    if got is None:
        checks.append((False, '没看到「计数 04 宝箱 捡到个数 …」这一行'))
    elif want_treasure and got == want_treasure[1]:
        checks.append((True, '计数 04：宝箱捡到个数 ' + str(got)))
    else:
        checks.append((False, '计数 04 打出 ' + show(got) + '，期望 '
                       + str(want_treasure[1] if want_treasure else '?')
                       + '：TODO 2 要把「到这一格为止捡到的个数」跟步数一起放进队列'))

    # ── 五、12×12 那几行与探针 ───────────────────────────────────
    b12 = label_int(out, '12x12 BFS 步数')
    if b12 is None:
        checks.append((False, '没看到「12x12 BFS 步数 …」这一行'))
    elif b12 == 22:
        checks.append((True, '12x12 BFS 步数 22（判分自己算也是 22）'))
    else:
        checks.append((False, '12x12 BFS 步数 打出 ' + show(b12) + '，期望 22：TODO 1'))
    value = label_bool(out, '12x12 DFS 也算出来了吗')
    if value is None:
        checks.append((False, '没看到「12x12 DFS 也算出来了吗 …」这一行'))
    elif not value:
        checks.append((True, '12x12 DFS 也算出来了吗 False：12×12 上 DFS 撞上上限、'
                             '没算出答案（6×6 就已经要 1847 万次调用了）'))
    else:
        checks.append((False, '12x12 DFS 也算出来了吗 打出 True（交回 '
                       + show(label_int(out, '12x12 DFS 步数')) + '）：这一档应当撞上上限'
                       + '、交回 None——先看 TODO 5 有没有在超过 limit 时收手'))
    value = label_bool(out, '12x12 DFS 撞上上限了吗')
    if value is None:
        checks.append((False, '没看到「12x12 DFS 撞上上限了吗 …」这一行'))
    elif value:
        checks.append((True, '12x12 DFS 撞上上限了吗 True'))
    else:
        checks.append((False, '12x12 DFS 撞上上限了吗 打出 False：TODO 5 的限量'))

    raw, err = run_probe('task2_maze_shortest', PROBE_TASK2)
    if raw is None:
        checks.append((False, '任务 2 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)

    got = data.get('maze_steps')
    if got == maze_steps:
        checks.append((True, '探针：判分自己按同一规则砌的迷宫上，bfs_steps → ' + str(got)))
    else:
        checks.append((False, '探针：判分自己砌的迷宫上 bfs_steps 打出 ' + show(got)
                       + '，期望 ' + str(maze_steps) + '：TODO 1 别只对着给好的那张图调'))
    for name, size in (('open4', 4), ('open6', 6), ('open12', 12)):
        want = model_bfs_steps(size, size, model_grid(size, size, []), (0, 0), (size - 1, size - 1))
        got = data.get(name)
        if got == want:
            checks.append((True, '探针：' + name + ' → ' + str(got) + '（判分自己搭的空方格图）'))
        else:
            checks.append((False, '探针：' + name + ' 打出 ' + show(got) + '，期望 ' + str(want)
                           + '：TODO 1 在判分自己搭的图上也要对'))
    if data.get('same') == 0:
        checks.append((True, '探针：起点就是终点时交回 0 步（不是 -1）'))
    else:
        checks.append((False, '探针：起点就是终点时打出 ' + show(data.get('same'))
                       + '，期望 0：TODO 1 在**入队前**就该判一次起点是不是终点，'
                         '或者写清「出队时判、起点也会出队」'))
    if data.get('blocked') == -1:
        checks.append((True, '探针：被墙隔开时交回 -1（走不到与「0 步」是两件事）'))
    else:
        checks.append((False, '探针：被墙隔开时打出 ' + show(data.get('blocked'))
                       + '，期望 -1：走不到要交回 -1'))

    for name, size, want, todo in (('dfs4', 4, DFS_CALLS_4X4, 'TODO 4'),
                                   ('dfs5', 5, DFS_CALLS_5X5, 'TODO 4')):
        got = data.get(name)
        if isinstance(got, list) and len(got) == 2 and got[0] == (size - 1) * 2 \
                and got[1] == want:
            checks.append((True, '探针：判分自己搭的 ' + str(size) + '×' + str(size)
                                 + ' 空方格上，DFS 交回步数 ' + str(got[0])
                                 + '、调用 ' + str(got[1]) + ' 次（课件的确定值）'))
        else:
            checks.append((False, '探针：' + name + ' 打出 ' + show(got) + '，期望 ['
                           + str((size - 1) * 2) + ', ' + str(want) + ']：' + todo
                           + ' 的搜索要「试完所有路」——seen 在当前格返回前要收回'
                             '（seen[r][c] = False），不然试不出第二条路'))
    got = data.get('limited_ok')
    if isinstance(got, list) and got[0] == 6 and got[1] == DFS_CALLS_4X4:
        checks.append((True, '探针：上限 200000 之下，4×4 算得出答案（6 步、'
                             + str(DFS_CALLS_4X4) + ' 次调用）'))
    else:
        checks.append((False, '探针：dfs_calls_limited 在 4×4 上打出 ' + show(got)
                       + '，期望 [6, ' + str(DFS_CALLS_4X4) + ']：TODO 5 在'
                         '「上限没撞上」时要把正常的答案交回（不是 (-1, 0)）'
                         '——它要复用 TODO 4 那套搜索'))
    got = data.get('limited_stop')
    if isinstance(got, list) and got[0] is None and got[1] > 5000:
        checks.append((True, '探针：上限 5000 之下，6×6 交回 (None, ' + str(got[1])
                             + ')：超过上限立刻收手（而不是交回 -1）'))
    elif isinstance(got, list) and got[0] == -1 and got[1] > 5000:
        checks.append((False, '探针：dfs_calls_limited 打出 (-1, ' + str(got[1])
                       + ')：超过上限要交回 **None**，-1 是「走不到」的意思'))
    else:
        checks.append((False, '探针：dfs_calls_limited 在上限 5000 的 6×6 上打出 ' + show(got)
                       + '，期望 [None, 大于 5000 的数]：TODO 5 一进 walk 就加一、'
                         '超过 limit 立刻交回'))
    want_t = model_treasure_probe()
    got = data.get('treasure')
    if isinstance(got, list) and want_t is not None and tuple(got) == want_t:
        checks.append((True, '探针：判分自己摆的宝箱上 bfs_treasure → ' + str(got)
                             + '（8×8 空方格，宝箱在 (1,0) (2,0) (7,1) (7,4)；'
                               '判分自己走那条最短路也是这个数）'))
    else:
        checks.append((False, '探针：bfs_treasure 打出 ' + show(got) + '，期望 '
                       + show(list(want_t) if want_t else None)
                       + '：TODO 2 要把「这一格捡到了吗」算进带进队列的那个数里'
                         '（8×8 空方格，宝箱在 (1,0) (2,0) (7,1) (7,4)）'))
    if data.get('dfs_steps_4') == 6:
        checks.append((True, '探针：dfs_steps 在 4×4 上给出 6 步（与 BFS 一致）'))
    else:
        checks.append((False, '探针：dfs_steps 在 4×4 上打出 ' + show(data.get('dfs_steps_4'))
                       + '，期望 6：TODO 3'))
    return checks


# ══ 任务 3 · 岛屿数量、连通块与多起点 ═══════════════════════════════════

PROBE_TASK3 = '''
out = {}
out['islands_small'] = m.count_islands(m.ISLAND_SMALL)
out['islands_rows'] = m.count_islands(m.ISLAND_ROWS)

# 判分自己摆的几张岛屿图
out['islands_all_water'] = m.count_islands(['000', '000', '000'])
out['islands_all_land'] = m.count_islands(['111', '111'])
out['islands_diagonal'] = m.count_islands(['100', '010', '001'])
out['islands_single'] = m.count_islands(['1'])

# 连通块：判分自己给的点边列表
edges = [(0, 1), (1, 2), (3, 4), (5, 6), (6, 7), (7, 5)]
out['comp_search'] = m.count_components(9, edges)
out['comp_uf'] = m.count_components_uf(9, edges)
out['comp_none'] = m.count_components(4, [])
out['comp_chain'] = m.count_components(10, [(i, i + 1) for i in range(9)])

# 多起点：两个起点通着时，答案是「一共几个点」而不是相加
adj = [[], [2], [1], [4], [3]]
out['reach_two'] = m.reach_all(5, adj, [1, 3])
out['reach_same'] = m.reach_all(5, adj, [1, 1, 2])
out['reach_empty'] = m.reach_all(5, adj, [])
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task3():
    checks = []
    run = run_script('task3_islands.py')
    if run['status'] != 'ok':
        return [(False, 'task3_islands.py 没跑通：' + run['note'])]
    out = run['out']

    # ── 一、三道岛屿题 ───────────────────────────────────────────
    for index, rows, label, todo in (('01', ISLAND_SMALL, '小网格', 'TODO 1'),
                                     ('02', ISLAND_ROWS, '对角线', 'TODO 1'),
                                     ('03', COURSE_ROWS, '课件', 'TODO 1')):
        want = model_islands(rows)
        got = int_value(out, index)
        if got is None:
            checks.append((False, '没看到「计数 ' + index + ' ' + label + ' 岛屿数量 …」这一行'))
        elif got == want:
            checks.append((True, '计数 ' + index + '：' + label + ' 岛屿数量 ' + str(got)
                                 + '（判分自己数也是 ' + str(want) + '；课件那个例子是 '
                                 + str(model_islands(COURSE_ROWS)) + '）'))
        else:
            checks.append((False, '计数 ' + index + '（' + label + '）打出 ' + show(got)
                           + '，期望 ' + str(want) + '：' + todo + ' 是「遇到没走过的陆地就'
                             '计数加一，然后把整块走完」——斜着挨着不算连着'))
    value = label_int(out, '对角线 网格行数')
    if value is None:
        checks.append((False, '没看到「对角线 网格行数 …」这一行'))
    else:
        checks.append((True, '对角线 网格行数 ' + str(value)))

    # ── 二、连通块两种数法 ───────────────────────────────────────
    want_comp = model_components(C_N, C_EDGES)
    got_search = int_value(out, '04')
    got_uf = int_value(out, '05')
    for index, got, label, todo in (('04', got_search, '搜索版', 'TODO 2'),
                                    ('05', got_uf, '并查集版', 'TODO 3')):
        if got is None:
            checks.append((False, '没看到「计数 ' + index + ' 连通块 ' + label + ' …」这一行'))
        elif got == want_comp:
            checks.append((True, '计数 ' + index + '：连通块 ' + label + ' ' + str(got)
                                 + '（判分自己数也是 ' + str(want_comp) + '）'))
        else:
            checks.append((False, '计数 ' + index + '（连通块 ' + label + '）打出 ' + show(got)
                           + '，期望 ' + str(want_comp) + '：' + todo
                           + '（3000 个点里有 4000 条边，数出来是 ' + str(want_comp) + ' 块）'))
    value = label_bool(out, '连通块 两种数法一致')
    if value is None:
        checks.append((False, '没看到「连通块 两种数法一致 …」这一行'))
    elif value:
        checks.append((True, '连通块 两种数法一致 True：搜索遍历与并查集不遍历，'
                             '两条完全不同的路数出同一个数'))
    else:
        checks.append((False, '连通块 两种数法一致 打出 False：TODO 2 与 TODO 3 必须一样'))
    value = label_bool(out, '两条路各量一次 答案仍一致')
    if value is None:
        checks.append((False, '没看到「两条路各量一次 答案仍一致 …」这一行'))
    elif value:
        checks.append((True, '两条路各量一次 答案仍一致 True'))
    else:
        checks.append((False, '两条路各量一次 答案仍一致 打出 False：两个函数都还没写对'))
    sv = time_values(out, '耗时 01 ', 3000)
    uv = time_values(out, '耗时 02 ', 3000)
    if not sv or not uv:
        checks.append((False, '没看到「耗时 01/02 连通块 …」这两行：带 print 的行别改'))
    elif sv[0] <= 0 or uv[0] <= 0:
        checks.append((False, '连通块那两行的秒数是 0.000000：TODO 2 / TODO 3 还没写出来'))
    else:
        checks.append((True, '耗时 01/02：连通块 搜索版 ' + f'{sv[0]:.6f}' + ' 秒、并查集版 '
                             + f'{uv[0]:.6f}' + ' 秒（两条路各有各的代价，秒数只看趋势）'))

    # ── 三、多起点 ───────────────────────────────────────────────
    want_maze_reach = model_reach_grid(MN, MM, MAZE, (0, 0))
    got = int_value(out, '06')
    if got is None:
        checks.append((False, '没看到「计数 06 迷宫 多起点到达 …」这一行'))
    elif got == want_maze_reach:
        checks.append((True, '计数 06：迷宫多起点到达 ' + str(got)
                             + '（判分自己数也是 ' + str(want_maze_reach)
                             + '；四个起点里 (7, 7) 落在墙上）'))
    else:
        checks.append((False, '计数 06 打出 ' + show(got) + '，期望 ' + str(want_maze_reach)
                       + '：多起点那道题**不是**每个起点各走一遍再相加，'
                         '几个起点共用一张 seen（(7, 7) 是墙，走不了）'))
    wall_flags = [line for line in out.splitlines() if line.startswith('起点 ')]
    if len(wall_flags) < 4:
        checks.append((False, '没看到四行「起点 … 是墙吗 …」'))
    else:
        checks.append((True, '四个起点的墙判定都打出来了：' + ' / '.join(
            line.split()[-1] for line in wall_flags)))
    got = int_value(out, '09')
    want_two = model_reach_grid(50, 50, model_grid(50, 50, []), (0, 0))
    if got is None:
        checks.append((False, '没看到「计数 09 大空图 两个起点到达 …」这一行'))
    elif got == want_two:
        checks.append((True, '计数 09：大空图两个起点到达 ' + str(got)
                             + '（两个起点在 50×50 里通着，所以是 ' + str(want_two)
                             + ' 而不是相加的 5000）'))
    else:
        checks.append((False, '计数 09 打出 ' + show(got) + '，期望 ' + str(want_two)
                       + '：两个起点通着时要共用一张 seen'))
    got = int_value(out, '07')
    want_h = model_reach_starts(H_N, model_adj(H_N, H_EDGES), H_STARTS)
    if got is None:
        checks.append((False, '没看到「计数 07 点边列表 多起点到达 …」这一行'))
    elif got == want_h:
        checks.append((True, '计数 07：点边列表多起点到达 ' + str(got)
                             + '（判分自己数也是 ' + str(want_h) + '；起点 0 与 3 在同一块里）'))
    else:
        checks.append((False, '计数 07 打出 ' + show(got) + '，期望 ' + str(want_h)
                       + '：TODO 4 里几个起点要全部先标上 seen、一起入队'))
    got = label_int(out, '点边列表 单起点对照')
    want_single = len(_component_of(H_N, model_adj(H_N, H_EDGES), 0))
    if got is None:
        checks.append((False, '没看到「点边列表 单起点对照 …」这一行'))
    elif got == want_single:
        checks.append((True, '点边列表 单起点对照 ' + str(got) + '（判分自己算也是 '
                             + str(want_single) + '）'))
    else:
        checks.append((False, '点边列表 单起点对照 打出 ' + show(got) + '，期望 ' + str(want_single)))

    # ── 四、大图连通块 ───────────────────────────────────────────
    got = int_value(out, '08')
    big_edges = []
    for r in range(50):
        for c in range(50):
            u = r * 50 + c
            if c + 1 < 50:
                big_edges.append((u, u + 1))
            if r + 1 < 50:
                big_edges.append((u, u + 50))
    want_big = model_components(2500, big_edges)
    if got is None:
        checks.append((False, '没看到「计数 08 大图 连通块 …」这一行'))
    elif got == want_big:
        checks.append((True, '计数 08：50×50 那张点边列表的连通块 ' + str(got)
                             + '（判分自己数也是 ' + str(want_big) + '）'))
    else:
        checks.append((False, '计数 08 打出 ' + show(got) + '，期望 ' + str(want_big)
                       + '：TODO 2 要能处理大图（2500 个点）'))
    got = label_int(out, '大图 从 0 号点走得到几个')
    if got is None:
        checks.append((False, '没看到「大图 从 0 号点走得到几个 …」这一行'))
    else:
        checks.append((True, '大图 从 0 号点走得到几个 ' + str(got) + '（给好的对照行）'))

    # ── 五、探针 ─────────────────────────────────────────────────
    raw, err = run_probe('task3_islands', PROBE_TASK3)
    if raw is None:
        checks.append((False, '任务 3 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)

    for name, rows, todo in (('islands_small', ISLAND_SMALL, 'TODO 1'),
                             ('islands_rows', ISLAND_ROWS, 'TODO 1'),
                             ('islands_all_water', ['000', '000', '000'], 'TODO 1'),
                             ('islands_all_land', ['111', '111'], 'TODO 1'),
                             ('islands_diagonal', ['100', '010', '001'], 'TODO 1'),
                             ('islands_single', ['1'], 'TODO 1')):
        got = data.get(name)
        want = model_islands(rows)
        if got == want:
            extra = '（全海是 0 块、全陆是 1 块、单格是 1 块——边界也要对）' \
                if name in ('islands_all_water', 'islands_all_land', 'islands_single') else ''
            checks.append((True, '探针：' + name + ' → ' + str(got) + ' ' + extra))
        else:
            checks.append((False, '探针：' + name + ' 打出 ' + show(got) + '，期望 ' + str(want)
                           + '：' + todo + '（判分自己摆的岛屿图）'))
    probe_edges = [(0, 1), (1, 2), (3, 4), (5, 6), (6, 7), (7, 5)]
    want_search = model_components(9, probe_edges)
    for name, todo in (('comp_search', 'TODO 2'), ('comp_uf', 'TODO 3')):
        got = data.get(name)
        if got == want_search:
            checks.append((True, '探针：' + name + ' → ' + str(got)
                                 + '（判分自己给的 9 个点：3 块 + 2 个孤点）'))
        else:
            checks.append((False, '探针：' + name + ' 打出 ' + show(got) + '，期望 '
                           + str(want_search) + '：' + todo + '（孤点自己算一块）'))
    for name, want, note in (('comp_none', 4, '一条边都没有时每个点各算一块（TODO 2 / TODO 3）'),
                             ('comp_chain', 1, '一条链上的 10 个点算一块（TODO 2 / TODO 3）')):
        got = data.get(name)
        if got == want:
            checks.append((True, '探针：' + name + ' → ' + str(got) + '（' + note + '）'))
        else:
            checks.append((False, '探针：' + name + ' 打出 ' + show(got) + '，期望 ' + str(want)
                           + '：' + note))
    for name, n, adj, starts, todo in (
            ('reach_two', 5, [[], [2], [1], [4], [3]], [1, 3],
             'TODO 4：两个起点在同一块里时，答案是 3 而不是各走一遍相加'),
            ('reach_same', 5, [[], [2], [1], [4], [3]], [1, 1, 2],
             'TODO 4：起点重复出现在表里也不该把它数两遍'),
            ('reach_empty', 5, [[], [2], [1], [4], [3]], [],
             'TODO 4：起点表是空的时候能走到 0 个点')):
        got = data.get(name)
        want = model_reach_starts(n, adj, starts)
        if got == want:
            checks.append((True, '探针：' + name + ' → ' + str(got) + '（判分自己搭的图）'))
        else:
            checks.append((False, '探针：' + name + ' 打出 ' + show(got) + '，期望 ' + str(want)
                           + '：' + todo))
    return checks


def _component_of(n, adj, start):
    seen = set()
    stack = [start]
    seen.add(start)
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


# ══ 任务 4 · visited 标记的时机 ═════════════════════════════════════════

PROBE_TASK4 = '''
out = {}
def opengrid(size):
    return [[False] * size for _ in range(size)]

# 判分自己搭的三档空方格图：两种标记时机各试一遍
for size in (6, 10, 20):
    out['push' + str(size)] = list(m.bfs_trace_grid(size, True))
    out['pop' + str(size)] = list(m.bfs_trace_grid(size, False))

# 直接给图给起终点（不经过 bfs_trace_grid）
out['dir_push'] = list(m.bfs_trace(5, 5, opengrid(5), (0, 0), (4, 4), True))
out['dir_pop'] = list(m.bfs_trace(5, 5, opengrid(5), (0, 0), (4, 4), False))

# 有墙的一张小图：答案必须一样
walls = opengrid(6)
for (r, c) in ((1, 1), (1, 2), (2, 2), (3, 2)):
    walls[r][c] = True
out['walled_push'] = list(m.bfs_trace(6, 6, walls, (0, 0), (5, 5), True))
out['walled_pop'] = list(m.bfs_trace(6, 6, walls, (0, 0), (5, 5), False))

# 走不到：一张被竖墙隔开的图
sep = opengrid(5)
for r in range(5):
    sep[r][2] = True
out['sep_push'] = list(m.bfs_trace(5, 5, sep, (0, 0), (0, 4), True))
out['sep_pop'] = list(m.bfs_trace(5, 5, sep, (0, 0), (0, 4), False))
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task4():
    checks = []
    run = run_script('task4_mark_timing.py')
    if run['status'] != 'ok':
        return [(False, 'task4_mark_timing.py 没跑通：' + run['note'])]
    out = run['out']

    # ── 一、有墙那张 6×6 ─────────────────────────────────────────
    walls6 = model_grid(6, 6, [(1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (4, 1), (4, 2)])
    want_push = model_trace(6, 6, walls6, (0, 0), (5, 5), True)
    want_pop = model_trace(6, 6, walls6, (0, 0), (5, 5), False)
    got1 = int_value(out, '01')
    got2 = int_value(out, '02')
    if got1 is None or got2 is None:
        checks.append((False, '没看到「计数 01/02 6x6 … 入队次数 …」这两行：'
                              '带 print 的行别改、别删'))
    elif got1 == want_push[1] and got2 == want_pop[1]:
        checks.append((True, '计数 01/02：6×6 上入队时标记 ' + str(got1) + ' 次、'
                             '出队时标记 ' + str(got2) + ' 次（判分自己算也是 '
                             + str(want_push[1]) + ' / ' + str(want_pop[1]) + '）'))
    else:
        checks.append((False, '计数 01/02 打出 ' + show((got1, got2)) + '，期望 ('
                       + str(want_push[1]) + ', ' + str(want_pop[1]) + ')：'
                         'TODO 1 里两个版本的入队次数要分开数——'
                         '出队时标记那一版**入队时不看 seen**，同一个格子会被每个邻居各入一次'))
    value = label_bool(out, '6x6 两版答案一致')
    if value is None:
        checks.append((False, '没看到「6x6 两版答案一致 …」这一行'))
    elif value:
        checks.append((True, '6x6 两版答案一致 True：两种标记时机给出的步数一样'
                             '（这一课的要害：答案一样、代价差近四倍）'))
    else:
        checks.append((False, '6x6 两版答案一致 打出 False：两种写法必须给出同一个步数'))
    pair = pair_values(out, '6x6 入队时标记 入队次数 队列最长')
    if pair is None:
        checks.append((False, '没看到「6x6 入队时标记 入队次数 队列最长 …」这一行'))
    elif pair[0] == str(want_push[1]):
        checks.append((True, '6x6 入队时标记那一行：入队 ' + pair[0] + ' 次、队列最长 '
                             + pair[1] + '（判分自己算也是 ' + str(want_push[1]) + ' / '
                             + str(want_push[2]) + '）'))
    else:
        checks.append((False, '6x6 入队时标记 那一行打出 ' + show(pair) + '，入队次数期望 '
                       + str(want_push[1]) + '：TODO 1'))
    raw = label_text(out, '倍数 01 入队次数 出队时标记')
    if raw is None:
        checks.append((False, '没看到「倍数 01 入队次数 出队时标记 …」这一行'))
    else:
        m_ratio = re.search(r'([\d.]+)', raw)
        ratio = float(m_ratio.group(1)) if m_ratio else None
        want_ratio = want_pop[1] / want_push[1]
        if ratio is not None and abs(ratio - want_ratio) < 0.05:
            checks.append((True, '倍数 01：出队时标记的入队次数是入队时标记的 '
                                 + f'{ratio:.2f}' + ' 倍（判分自己算也是 '
                                 + f'{want_ratio:.2f}' + ' 倍）'))
        else:
            checks.append((False, '倍数 01 打出 ' + show(raw) + '，期望 ' + f'{want_ratio:.2f}'
                           + ' 倍：TODO 1 那两个入队次数还没数对，倍数自然也不算不出来'))

    # ── 二、空方格图三档 ─────────────────────────────────────────
    for size in (6, 10, 20):
        wp = model_trace(size, size, model_grid(size, size, []), (0, 0),
                         (size - 1, size - 1), True)
        wq = model_trace(size, size, model_grid(size, size, []), (0, 0),
                         (size - 1, size - 1), False)
        prefix = '方格 ' + str(size) + 'x' + str(size) + ' '
        value = label_bool(out, prefix + '两版答案一致')
        if value is None:
            checks.append((False, '没看到「' + prefix + '两版答案一致 …」这一行'))
        elif value:
            checks.append((True, prefix + '两版答案一致 True（步数 ' + str(wp[0])
                                 + '，两版一样）'))
        else:
            checks.append((False, prefix + '两版答案一致 打出 False：TODO 1/2'))
        got_push = None
        # 计数 10/11 带规模标签，按标签取
        line_push = get_line(out, '计数 10 方格 ' + str(size) + 'x' + str(size) + ' 入队时标记 入队')
        line_pop = get_line(out, '计数 11 方格 ' + str(size) + 'x' + str(size) + ' 出队时标记 入队')
        try:
            got_p = int(line_push) if line_push is not None else None
        except ValueError:
            got_p = None
        try:
            got_q = int(line_pop) if line_pop is not None else None
        except ValueError:
            got_q = None
        if got_p is None or got_q is None:
            checks.append((False, '没看到「计数 10/11 方格 ' + str(size) + 'x' + str(size)
                           + ' … 入队 …」这两行'))
        elif got_p == wp[1] and got_q == wq[1]:
            checks.append((True, '计数 10/11（' + str(size) + 'x' + str(size) + '）：入队时标记 '
                                 + str(got_p) + ' 次、出队时标记 ' + str(got_q)
                                 + ' 次（判分自己算也是 ' + str(wp[1]) + ' / ' + str(wq[1])
                                 + '，' + f'{wq[1] / wp[1]:.2f}' + ' 倍）'))
        else:
            checks.append((False, '计数 10/11（' + str(size) + 'x' + str(size) + '）打出 ('
                           + show(got_p) + ', ' + show(got_q) + ')，期望 (' + str(wp[1])
                           + ', ' + str(wq[1]) + ')：TODO 1 的入队次数从 1 开始数'
                             '——入队时标记那一版每个格子只入一次队（' + str(size) + '×'
                           + str(size) + ' 就是 ' + str(size * size) + ' 次上下），'
                             '出队时标记那一版入队时不看 seen，会到四倍左右'))
        pair = pair_values(out, '方格 ' + str(size) + 'x' + str(size) + ' 队列最长 两版')
        if pair is None:
            checks.append((False, '没看到「方格 ' + str(size) + 'x' + str(size)
                           + ' 队列最长 两版 …」这一行'))
        elif pair[0] == str(wp[2]) and pair[1] == str(wq[2]):
            checks.append((True, '队列最长（' + str(size) + 'x' + str(size) + '）：'
                                 + str(wp[2]) + ' / ' + str(wq[2])
                                 + '（入队时标记的队列最长就是一圈的长度）'))
        else:
            checks.append((False, '队列最长 两版（' + str(size) + 'x' + str(size) + '）打出 '
                           + show(pair) + '，期望 (' + str(wp[2]) + ', ' + str(wq[2])
                           + ')：TODO 1 要在每次出队前记一次 len(q) 的最大值'
                             '（maxq 从 1 起算）'))

    # ── 三、迷宫 ─────────────────────────────────────────────────
    mp = model_trace(MN, MM, MAZE, (0, 0), (14, 14), True)
    mq = model_trace(MN, MM, MAZE, (0, 0), (14, 14), False)
    value = label_bool(out, '迷宫 两版答案一致')
    if value is None:
        checks.append((False, '没看到「迷宫 两版答案一致 …」这一行'))
    elif value:
        checks.append((True, '迷宫 两版答案一致 True（步数 ' + str(mp[0]) + '）'))
    else:
        checks.append((False, '迷宫 两版答案一致 打出 False：TODO 1'))
    pair = pair_values(out, '迷宫 入队次数 两版')
    if pair is None:
        checks.append((False, '没看到「迷宫 入队次数 两版 …」这一行'))
    elif pair[0] == str(mp[1]) and pair[1] == str(mq[1]):
        checks.append((True, '迷宫：入队次数两版 ' + str(mp[1]) + ' / ' + str(mq[1])
                             + '（判分自己算也是这个数）'))
    else:
        checks.append((False, '迷宫 入队次数 两版 打出 ' + show(pair) + '，期望 ('
                       + str(mp[1]) + ', ' + str(mq[1]) + ')：TODO 1'))

    # ── 四、60×60 与队列最长 ─────────────────────────────────────
    big = model_grid(60, 60, [])
    want_g = model_trace(60, 60, big, (0, 0), (59, 59), True)
    want_b = model_trace(60, 60, big, (0, 0), (59, 59), False)
    for label, expect in (('60x60 入队时标记 步数', want_g[0]),
                          ('60x60 出队时标记 步数', want_b[0])):
        got = label_int(out, label)
        if got is None:
            checks.append((False, '没看到「' + label + ' …」这一行'))
        elif got == expect:
            checks.append((True, label + ' ' + str(got) + '（判分自己算也是 ' + str(expect) + '）'))
        else:
            checks.append((False, label + ' 打出 ' + show(got) + '，期望 ' + str(expect)
                           + '：TODO 1 的 (行, 列, 步数) 要跟着格子走（空方格图上就是'
                             '两条边之和）'))
    value = label_bool(out, '60x60 两版步数一致')
    if value is None:
        checks.append((False, '没看到「60x60 两版步数一致 …」这一行'))
    elif value:
        checks.append((True, '60x60 两版步数一致 True：3600 个格子上两版给出同一个步数'))
    else:
        checks.append((False, '60x60 两版步数一致 打出 False：TODO 1 里两种标记时机'
                              '必须给出同一个步数'))
    maxq_got = label_int(out, '队列最长 入队时标记')
    maxq_want = model_trace(100, 100, model_grid(100, 100, []), (0, 0), (99, 99), True)[2]
    if maxq_got is None:
        checks.append((False, '没看到「队列最长 入队时标记 …」这一行'))
    elif maxq_got == maxq_want:
        checks.append((True, '队列最长 入队时标记 ' + str(maxq_got)
                             + '（100×100 的图上；入队时标记的队列最长就是一层的长度）'))
    else:
        checks.append((False, '队列最长 入队时标记 打出 ' + show(maxq_got) + '，期望 '
                       + str(maxq_want) + '：那是 bfs_trace_grid(100, True) 的第三个数'
                         '（TODO 2 只是把 TODO 1 包了一层，别在包装里丢掉第三个值）'))
    maxq_pop_got = label_int(out, '队列最长 出队时标记')
    maxq_pop_want = model_trace(100, 100, model_grid(100, 100, []), (0, 0), (99, 99), False)[2]
    if maxq_pop_got is None:
        checks.append((False, '没看到「队列最长 出队时标记 …」这一行'))
    elif maxq_pop_got == maxq_pop_want:
        checks.append((True, '队列最长 出队时标记 ' + str(maxq_pop_got)
                             + '（100×100 的图上；出队时标记的队列会涨到四倍上下）'))
    else:
        checks.append((False, '队列最长 出队时标记 打出 ' + show(maxq_pop_got) + '，期望 '
                       + str(maxq_pop_want) + '：那是 bfs_trace_grid(100, False) 的第三个数'
                         '（TODO 1 里出队时标记那一版也要记 len(q) 的最大值）'))
    tv = time_values(out, '耗时 01 ', 3600)
    tv2 = time_values(out, '耗时 02 ', 3600)
    if not tv or not tv2:
        checks.append((False, '没看到「耗时 01/02 60x60 …」这两行'))
    elif tv[0] <= 0 or tv2[0] <= 0:
        checks.append((False, '60×60 那两行的秒数是 0.000000：TODO 1 还没写出来'))
    else:
        checks.append((True, '耗时 01/02：60×60 上入队时标记 ' + f'{tv[0]:.6f}'
                             + ' 秒、出队时标记 ' + f'{tv2[0]:.6f}' + ' 秒'
                               '（这一档两者差得不多——入队次数差四倍，但格子本身不多；'
                               '秒数只看趋势）'))

    # ── 五、探针：换判分自己的图 ─────────────────────────────────
    raw, err = run_probe('task4_mark_timing', PROBE_TASK4)
    if raw is None:
        checks.append((False, '任务 4 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)

    bad = []
    for size in (6, 10, 20):
        wp = model_trace(size, size, model_grid(size, size, []), (0, 0),
                         (size - 1, size - 1), True)
        wq = model_trace(size, size, model_grid(size, size, []), (0, 0),
                         (size - 1, size - 1), False)
        got_p = data.get('push' + str(size))
        got_q = data.get('pop' + str(size))
        if got_p != list(wp):
            bad.append('push' + str(size) + ' 打出 ' + show(got_p) + '，期望 ' + show(list(wp)))
        if got_q != list(wq):
            bad.append('pop' + str(size) + ' 打出 ' + show(got_q) + '，期望 ' + show(list(wq)))
    if bad:
        checks.append((False, '探针：判分自己搭的空方格图上（6/10/20）两种标记时机对不上：'
                       + show('；'.join(bad)) + '：TODO 1/2'))
    else:
        checks.append((True, '探针：判分自己搭的 6×6 / 10×10 / 20×20 空方格图上，'
                             '两种标记时机的 (步数, 入队次数, 队列最长) 三项全对'
                             '——入队次数一个是 n²、一个往 4 倍收敛'))
    w5 = model_grid(5, 5, [])
    if data.get('dir_push') == list(model_trace(5, 5, w5, (0, 0), (4, 4), True)) \
            and data.get('dir_pop') == list(model_trace(5, 5, w5, (0, 0), (4, 4), False)):
        checks.append((True, '探针：直接给图给起终点，5×5 上两版都对'))
    else:
        checks.append((False, '探针：直接调 bfs_trace 时两版打出 ' + show((data.get('dir_push'),
                                                                        data.get('dir_pop')))
                       + '，期望 ' + show((list(model_trace(5, 5, w5, (0, 0), (4, 4), True)),
                                            list(model_trace(5, 5, w5, (0, 0), (4, 4), False))))
                       + '：TODO 1 的签名是 (n, m, blocked, start, target, mark_on_push)'))
    walls = model_grid(6, 6, [(1, 1), (1, 2), (2, 2), (3, 2)])
    if data.get('walled_push') == list(model_trace(6, 6, walls, (0, 0), (5, 5), True)) \
            and data.get('walled_pop') == list(model_trace(6, 6, walls, (0, 0), (5, 5), False)):
        checks.append((True, '探针：有墙的 6×6 上两版都对（出队时标记那版要多判一次 seen）'))
    else:
        checks.append((False, '探针：有墙的 6×6 上打出 ' + show((data.get('walled_push'),
                                                                data.get('walled_pop')))
                       + '，期望 ' + show((list(model_trace(6, 6, walls, (0, 0), (5, 5), True)),
                                            list(model_trace(6, 6, walls, (0, 0), (5, 5), False))))
                       + '：TODO 1'))
    sep = model_grid(5, 5, [(r, 2) for r in range(5)])
    ok_push = data.get('sep_push') == list(model_trace(5, 5, sep, (0, 0), (0, 4), True))
    ok_pop = data.get('sep_pop') == list(model_trace(5, 5, sep, (0, 0), (0, 4), False))
    if ok_push and ok_pop:
        checks.append((True, '探针：走不到时两版都交回 -1 步，且入队次数与队列最长也对'))
    else:
        checks.append((False, '探针：被墙隔开时打出 ' + show((data.get('sep_push'), data.get('sep_pop')))
                       + '，期望 ' + show((list(model_trace(5, 5, sep, (0, 0), (0, 4), True)),
                                            list(model_trace(5, 5, sep, (0, 0), (0, 4), False))))
                       + '：TODO 1 走不到要交回步数 -1，'
                         '但入队次数与队列最长照样要数对（-1 只影响步数那一位）'))
    return checks


CHECKERS = {
    'task1_dfs_bfs.py': check_task1,
    'task2_maze_shortest.py': check_task2,
    'task3_islands.py': check_task3,
    'task4_mark_timing.py': check_task4,
}


def main():
    print('StudyMate lab 0021 · 自动判分（搜索：把图走一遍）')
    print('目录：' + str(HERE))
    print()
    failed = []
    for title, filename, _ in TASKS:
        print(title + '（' + filename + '）')
        if not (HERE / filename).is_file():
            print('  FAIL  还没建这个文件：' + filename)
            print()
            failed.append(filename)
            continue
        checks = CHECKERS[filename]()
        all_ok = True
        for ok, message in checks:
            print('  ' + ('PASS' if ok else 'FAIL') + '  ' + message)
            if not ok:
                all_ok = False
        if all_ok:
            print('  → 这个任务过了')
        else:
            failed.append(filename)
        print()

    print('─' * 60)
    print('4 个任务：' + str(4 - len(failed)) + ' 个通过，' + str(len(failed)) + ' 个还没通过')
    if failed:
        print('没过的：' + '、'.join(failed))
        print('卡住了先读 ../README.md 的「卡壳顺序」：读错误信息 → 自己跑一遍 → 看 FAIL 行 → 再对线索。')
        print('四个任务都过了，再对照 ../solutions/0021-dfs-bfs-search/ 看参考解。')
        return 1
    print('四个任务都过了。现在去对照 ../solutions/0021-dfs-bfs-search/：')
    print('比一比你的写法与参考解，再用一句话回答「求最少步数为什么必须用 BFS、'
          '而 visited 为什么要在入队那一刻就标记」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
