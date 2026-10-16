#!/usr/bin/env python3
"""lab 0017 · 自动判分：跑四个任务脚本，读它们打印的行，另起探针 import 学生代码。

用法（在 lab/0017-binary-tree-traversal/ 目录里）：

    py run_tests.py

判法：
  - 四个任务各起一个进程跑，只读它们打印出来的固定格式行，不 import 学生代码；
  - 期望值不是抄来的：判分自己按课件的表示约定搭树、按课件口径算出前中后序、
    层序、节点数、树高、对称性，再与学生打印的行逐字对照——**四种遍历的顺序对了
    才算过，不是「打印了就算过」**；
  - 任务 1、2、3、4 另起**探针进程** import 学生的函数，拿判分自己的小数据去试；
    任务 2 还会验 `is_mirror` 的四个分支（都空 / 只有一个空 / 都非空 / 左对右）、
    验 `height` 是拿两个孩子交回的值算出来的（试一个挑高的形状）；
  - 任务 3 的探针按**判分自己**的 998 / 999 两步复核：998 层的链必须算得出，
    999 层的链必须抛 RecursionError 且不能被学生接住；
  - 任务 3 还要与**系统递归上限**对照（高度正是撞上限的地方，两者只差几层固定开销）；
  - 任务 4 看**趋势不看常数**：链状那一列「拼接」随规模翻倍涨 2.5 倍以上、
    「累加器」涨 3 倍以内，而且链状上「拼接比累加器慢」的倍数明显大于平衡树；
    另外用源码扫描确认 preorder 三处都是**累加器**版，没写成拼接版。

断言里的口径来自课件正文：嵌套列表 `[值, 左, 右]`、空树 `None`、
前序根在最前、层序用队列、树高=层数、链状不到一千层爆栈、平衡树约为 log2 n、
收集结果用累加器而不是拼接。

退出码：0 = 四个任务都通过；1 = 还有没通过的。
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMEOUT = 120

TODO_RE = re.compile(r'TODO\s+(\d+)')
FILE_LINE_RE = re.compile(r'File "([^"]*)", line (\d+)')

TASKS = [
    ('任务 1 · 四种遍历（三个递归版 + 一个队列版）', 'task1_traversal.py', None),
    ('任务 2 · 节点数、树高与对称性', 'task2_tree_stats.py', None),
    ('任务 3 · 形状与递归深度', 'task3_depth_shape.py', None),
    ('任务 4 · 拼接与累加器的代价', 'task4_concat_cost.py', None),
]

# 链状树的爆栈长度：本机（Python 3.14.7t，默认上限 1000）在主块里实测 999，
# 也就是 998 层的链还算得出。
CRASH_LENGTH = 999
# 「递归再深一层」是**贴着上限**的边界值，差一层就差在一两个栈帧上：
# 同一次运行里，主块顶层试出来的与函数里试出来的会差一层上下。
# 所以判分接受一个小波段，而不是钉死一个数（真正的判据是「它贴着上限、且在它那
# 个深度上 height 交回的树高等于深度本身」，见 check_task3 与探针）。
DEEP_LOW = CRASH_LENGTH - 4                    # 995
DEEP_HIGH = CRASH_LENGTH - 1                   # 998
EXPECT_DEEP = CRASH_LENGTH - 1                  # 参考解报出来的那一个（998）


# ══ 参照模型：判分自己的树与口径（期望值都从这里来，不抄）══════════════════

def N(v, l=None, r=None):
    return [v, l, r]


T_MODEL = N('A', N('B', N('D'), N('E')), N('C', None, N('F')))
CHAIN5_MODEL = N(1, N(2, N(3, N(4, N(5)))))
BAL5_MODEL = N(1,
               N(2, N(4, N(8), N(9)), N(5, N(10), N(11))),
               N(3, N(6, N(12), N(13)), N(7, N(14), N(15))))
S_MODEL = N('A', N('B', N('D')), N('B', None, N('D')))
M1_MODEL = N('A', N('B', N('D')), N('B', N('D')))
M2_MODEL = N('A', N('B', N('D')), N('B', N('E')))
ONE = N('A')


def model_pre(t, out=None):
    if out is None:
        out = []
    if t is None:
        return out
    out.append(t[0])
    model_pre(t[1], out)
    model_pre(t[2], out)
    return out


def model_in(t, out=None):
    if out is None:
        out = []
    if t is None:
        return out
    model_in(t[1], out)
    out.append(t[0])
    model_in(t[2], out)
    return out


def model_post(t, out=None):
    if out is None:
        out = []
    if t is None:
        return out
    model_post(t[1], out)
    model_post(t[2], out)
    out.append(t[0])
    return out


def model_level(t):
    if t is None:
        return []
    out = []
    q = [t]
    head = 0
    while head < len(q):
        x = q[head]
        head += 1
        out.append(x[0])
        if x[1] is not None:
            q.append(x[1])
        if x[2] is not None:
            q.append(x[2])
    return out


def model_count(t):
    if t is None:
        return 0
    return 1 + model_count(t[1]) + model_count(t[2])


def model_height(t):
    if t is None:
        return 0
    stack = [(t, 1)]
    best = 0
    while stack:
        x, d = stack.pop()
        if d > best:
            best = d
        if x[1] is not None:
            stack.append((x[1], d + 1))
        if x[2] is not None:
            stack.append((x[2], d + 1))
    return best


def model_values(t, out=None):
    """把树里全部结点的值收成一个列表（不考虑顺序）——用来验「每个结点正好走一次」。"""
    if out is None:
        out = []
    if t is None:
        return out
    out.append(t[0])
    model_values(t[1], out)
    model_values(t[2], out)
    return out


def model_mirror(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return a[0] == b[0] and model_mirror(a[1], b[2]) and model_mirror(a[2], b[1])


def model_symmetric(t):
    return t is None or model_mirror(t[1], t[2])


def model_balanced(n):
    """**判分自己**搭的那棵树：按下标摆满，与课件那张「平衡树约 log2 n」的形状一致。

    （学生交的 BAL5 不是这一棵：那是给好的 B15 那种「按层编号」的树，
    见 model_bfs_tree。两棵树的**形状**一样，值不一样——判分两处分开用。）
    """
    built = [N(i) for i in range(n)]
    for i in range(n):
        l, r = 2 * i + 1, 2 * i + 2
        if l < n:
            built[i][1] = built[l]
        if r < n:
            built[i][2] = built[r]
    return built[0]


def model_bfs_tree():
    """课件示例那种「按层从上到下、从左到右编号」的四层满二叉树（15 个结点）。"""
    return N(1,
             N(2, N(4, N(8), N(9)), N(5, N(10), N(11))),
             N(3, N(6, N(12), N(13)), N(7, N(14), N(15))))


def model_textbook_balanced(n):
    """课件那一版平衡树（build_balanced 的那个公式）：根是 k，左子树 k // 2 个结点。

    学生交的 build_balanced 就是它，判分拿这个公式复核（不看值、只看形状与高度）。
    """
    def rec(k):
        if k == 0:
            return None
        left = k // 2
        return N(k, rec(left), rec(k - 1 - left))

    return rec(n)


def model_chain(n):
    """链状树：每个结点只有左孩子，树高就是 n。"""
    t = None
    for i in range(n):
        t = N(i, t, None)
    return t


def same(got, want):
    """逐字一致：拖尾空格不算差别，其余（顺序、元素）都算。"""
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
            [sys.executable, str(path)],
            cwd=str(HERE), env=_env(), timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'out': '',
                'note': '跑了 ' + str(timeout) + ' 秒还没结束（死循环？或者树搭得太大）'}
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
    """取一行并按空格切词；没有那一行就交回 None。"""
    raw = get_line(out, prefix)
    return None if raw is None else raw.split()


def show(value, limit=80):
    text = repr(value)
    return text[:limit] + '…' if len(text) > limit else text


def unwrap(got):
    """探针里普遍写成 show(f(...)) → cases 里存的是 [值]；这里取回那个值。"""
    if isinstance(got, list) and len(got) == 1:
        return got[0]
    return got


VALUE_RE = re.compile(r'^-?\d+$')


def count_value(out, index):
    """取 `计数 NN 标签 值` 里的值（只按编号找）。

    标签本身是中文词，所以不能盲目取第一段或最后一段：值一定是
    「整数」或「True/False」这两种形状之一，从**后往前**找到第一个这样的段。
    任务 3 的值后面还跟着中文（「… 999 已爆栈」），这样也能取到。
    """
    for entry in get_lines(out, '计数 ' + index + ' '):
        parts = entry.split()
        for piece in reversed(parts):
            if VALUE_RE.match(piece) or piece in ('True', 'False'):
                return piece
    return None


def time_values(out, index):
    """取 `耗时 NN 标签 n=… 秒` 里的 (n, 秒数)；同一编号可能有多行。"""
    values = []
    for entry in get_lines(out, '耗时 ' + index + ' '):
        m = re.search(r'n=(\d+)\s+([\d.]+)', entry)
        if m:
            values.append((int(m.group(1)), float(m.group(2))))
    return values


def label_values(out, prefix):
    """取 `倍数 … 3.51` 这类行的最后一段，转成 float。"""
    values = []
    for entry in get_lines(out, prefix):
        parts = entry.split()
        if parts:
            try:
                values.append(float(parts[-1]))
            except ValueError:
                pass
    return values


def parse_list(text):
    """把 "['D', 'E']" / "[1, 2]" 解析成列表；解析不了或元素不是标量就交回 None。"""
    if text is None:
        return None
    try:
        value = ast.literal_eval(text.strip())
    except (ValueError, SyntaxError):
        return None
    if not isinstance(value, list):
        return None
    if any(isinstance(x, (list, tuple, dict, set)) for x in value):
        return None
    return value


# ══ 任务 1 · 四种遍历 ════════════════════════════════════════════════════

PROBE_TASK1 = '''
def isnone(v):
    return v is None

def show(v):
    if v is None:
        return None
    if not isinstance(v, list):
        return {'kind': type(v).__name__}
    out = []
    for x in v:
        if isinstance(x, list):
            out.append('[' + type(x).__name__ + ']')
        else:
            out.append(x)
    return out

cases = []
for name, tree in (('empty', None), ('one', [7, None, None]), ('T', m.T)):
    cases.append([name, show(m.preorder(tree)), show(m.inorder(tree)),
                  show(m.postorder(tree)), show(m.level_order(tree))])

# 判分自己搭的平衡树也用同一套口径：根是 k、左子树 k//2 个结点
def bal(k):
    if k == 0:
        return None
    left = k // 2
    return [k, bal(left), bal(k - 1 - left)]

b7 = bal(7)
cases.append(['bal7_pre', show(m.preorder(b7))])
cases.append(['bal7_level', show(m.level_order(b7))])

# 值有 0 的树：队列版不能写成 if x[1]（0 会被当成空）
zero = [0, [0, [1, None, None], None], [0, None, [2, None, None]]]
cases.append(['zero_pre', show(m.preorder(zero))])
cases.append(['zero_level', show(m.level_order(zero))])

# 累加器版的证据：给一个**现成的**列表，看它是不是接着往里收
leftover = [99]
got_pre = m.preorder([5, None, None], leftover)
cases.append(['acc_pre', show(got_pre), show(leftover), got_pre is leftover])
leftover2 = [99]
got_in = m.inorder([5, None, None], leftover2)
cases.append(['acc_in', show(got_in), show(leftover2), got_in is leftover2])

# 队列版的证据：20 个结点的树也要能走完
deep = None
for i in range(20):
    deep = [i, deep, [100 + i, None, None]]
cases.append(['deep_level', show(m.level_order(deep))])

# 注意：学生的函数可能是拼接版（签名叫 (t)），给两个参数会报 TypeError，
# 那也要让它变成一条结果，而不是把整个探针弄崩。
probe = {}
for label, call in (
        ('sig_pre', 'm.preorder(one0, [99])'),
        ('sig_in', 'm.inorder(one0, [99])'),
        ('sig_post', 'm.postorder(one0, [99])'),
        ('sig_level', 'm.level_order(one0)')):
    try:
        probe[label] = show(eval(call))
    except TypeError as exc:
        probe[label] = 'TypeError: ' + str(exc)

# 每个结点正好走一次：7 个结点、值互不相同时，四种遍历都该交出 7 个值，
# 而且排序之后与「树里所有值」完全一样（重复访问或多访问都会在这里露出来）
distinct = bal(7)
seen_level = show(m.level_order(distinct))
counts = []
for f in (m.preorder, m.inorder, m.postorder, m.level_order):
    try:
        v = f(distinct)
        counts.append(sorted(v) if isinstance(v, list) else {'kind': type(v).__name__})
    except TypeError as exc:
        counts.append('TypeError: ' + str(exc))
probe['counts'] = counts
probe['seen_level'] = seen_level
print('PROBE ' + json.dumps({'cases': cases, 'sig': probe, 'tree': distinct},
                            ensure_ascii=False))
'''.replace('one0', '[7, None, None]')


def check_task1():
    checks = []
    run = run_script('task1_traversal.py')
    if run['status'] != 'ok':
        return [(False, 'task1_traversal.py 没跑通：' + run['note'])]
    out = run['out']

    # ── 一、四种遍历 × 三棵树：与判分自己算的逐字对照 ──────────────
    want_shapes = [('示例树', T_MODEL), ('链状树', CHAIN5_MODEL), ('平衡树', BAL5_MODEL)]
    for name, tree in want_shapes:
        got = want_line(out, name + ' 前序')
        if got is None:
            checks.append((False, '没看到「' + name + ' 前序 …」这一行：带 print 的行别改、别删'))
        else:
            value = parse_list(' '.join(got))
            if same(value, model_pre(tree)):
                checks.append((True, name + ' 前序 ' + str(value) + ' 与判分算的一致'))
            else:
                checks.append((False, name + ' 前序 打出 ' + show(' '.join(got))
                               + '，期望 ' + str(model_pre(tree))
                               + '：TODO 1 的顺序是「先记根，再进左、再进右」'))
    for name, tree, todo, order in [('示例树', T_MODEL, 'TODO 2', '左 → 根 → 右'),
                                    ('链状树', CHAIN5_MODEL, 'TODO 2', '左 → 根 → 右'),
                                    ('平衡树', BAL5_MODEL, 'TODO 2', '左 → 根 → 右')]:
        got = want_line(out, name + ' 中序')
        if got is None:
            checks.append((False, '没看到「' + name + ' 中序 …」这一行'))
            continue
        value = parse_list(' '.join(got))
        if same(value, model_in(tree)):
            checks.append((True, name + ' 中序 ' + str(value) + ' 与判分算的一致'))
        else:
            checks.append((False, name + ' 中序 打出 ' + show(' '.join(got))
                           + '，期望 ' + str(model_in(tree))
                           + '：' + todo + ' 的 append 要夹在两个递归调用**中间**（' + order + '）'))
    for name, tree in [('示例树', T_MODEL), ('链状树', CHAIN5_MODEL), ('平衡树', BAL5_MODEL)]:
        got = want_line(out, name + ' 后序')
        if got is None:
            checks.append((False, '没看到「' + name + ' 后序 …」这一行'))
            continue
        value = parse_list(' '.join(got))
        if same(value, model_post(tree)):
            checks.append((True, name + ' 后序 ' + str(value) + ' 与判分算的一致'))
        else:
            checks.append((False, name + ' 后序 打出 ' + show(' '.join(got))
                           + '，期望 ' + str(model_post(tree))
                           + '：TODO 3 的 append 要放在两个递归调用**之后**（左 → 右 → 根）'))
    for name, tree in [('示例树', T_MODEL), ('链状树', CHAIN5_MODEL), ('平衡树', BAL5_MODEL)]:
        got = want_line(out, name + ' 层序')
        if got is None:
            checks.append((False, '没看到「' + name + ' 层序 …」这一行'))
            continue
        value = parse_list(' '.join(got))
        if same(value, model_level(tree)):
            checks.append((True, name + ' 层序 ' + str(value) + ' 与判分算的一致'))
        else:
            checks.append((False, name + ' 层序 打出 ' + show(' '.join(got))
                           + '，期望 ' + str(model_level(tree))
                           + '：TODO 4 要用 deque：popleft 取一个、把它的两个孩子从右边排进去'))

    # ── 二、课件那四行（逐字） ────────────────────────────────────
    courseware = [
        ('课件 前序', ['A', 'B', 'D', 'E', 'C', 'F']),
        ('课件 中序', ['D', 'B', 'E', 'A', 'C', 'F']),
        ('课件 后序', ['D', 'E', 'B', 'F', 'C', 'A']),
        ('课件 层序', ['A', 'B', 'C', 'D', 'E', 'F']),
    ]
    for prefix, expect in courseware:
        got = want_line(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif same(parse_list(' '.join(got)), expect):
            checks.append((True, prefix + ' ' + str(expect) + ' 与课件逐字一致'))
        else:
            checks.append((False, prefix + ' 打出 ' + show(' '.join(got)) + '，期望 ' + str(expect)))

    # ── 三、两棵自己搭的树 ───────────────────────────────────────
    chain = want_line(out, '链状树 前序')
    if chain is None:
        checks.append((False, '没看到「链状树 前序 …」这一行：TODO 5 的 CHAIN5 还没搭'))
    else:
        value = parse_list(' '.join(chain))
        if same(value, model_pre(CHAIN5_MODEL)):
            checks.append((True, 'CHAIN5 是只有左孩子、五层往下的链（前序 ' + str(value) + '）'))
        elif value in ([], None):
            checks.append((False, '链状树 前序 打出 ' + show(' '.join(chain))
                           + '：TODO 5 的 CHAIN5 还是 None，照 node(1, node(2, …)) 那串搭出来'))
        else:
            checks.append((False, '链状树 前序 打出 ' + show(' '.join(chain))
                           + '，期望 ' + str(model_pre(CHAIN5_MODEL))
                           + '：TODO 5 要的是「只有左孩子、值 1 2 3 4 5」的链'))
    bal = want_line(out, '平衡树 中序')
    if bal is None:
        checks.append((False, '没看到「平衡树 中序 …」这一行：TODO 6 的 BAL5 还没搭'))
    else:
        value = parse_list(' '.join(bal))
        if same(value, model_in(BAL5_MODEL)):
            checks.append((True, 'BAL5 是四层 15 个结点、每层挂满的平衡树（中序 ' + str(value) + '）'))
        elif value in ([], None):
            checks.append((False, '平衡树 中序 打出 ' + show(' '.join(bal))
                           + '：TODO 6 的 BAL5 还是 None，照给好的 B15 那串编号搭一棵'))
        else:
            checks.append((False, '平衡树 中序 打出 ' + show(' '.join(bal))
                           + '，期望 ' + str(model_in(BAL5_MODEL))
                           + '：TODO 6 要的是第 1 层 1、第 2 层 2 3、第 3 层 4..7、第 4 层 8..15'))

    # ── 四、基例：空树与单点 ─────────────────────────────────────
    empty = get_line(out, '空树 四种')
    if empty is None:
        checks.append((False, '没看到「空树 四种 …」这一行'))
    elif empty == '[] [] [] []':
        checks.append((True, '空树：四种遍历都交回 []（基例 `if t is None` 写对了）'))
    else:
        checks.append((False, '空树 四种 打出 ' + show(empty) + '，期望 [] [] [] []：'
                       '每个函数的第一句都该是 if t is None 那个基例'))
    sing = get_line(out, '单点 四种')
    if sing is None:
        checks.append((False, '没看到「单点 四种 …」这一行'))
    elif sing == "['A'] ['A'] ['A'] ['A']":
        checks.append((True, '单点树：四种遍历都交回 [\'A\']'))
    else:
        checks.append((False, '单点 四种 打出 ' + show(sing) + "，期望 ['A'] ['A'] ['A'] ['A']："
                       'TODO 1-4 的四个函数都要能走完一个结点（基例之外还要真的收值）'))

    for index, label in [('01', '示例树'), ('02', '链状树'), ('03', '平衡树')]:
        value = count_value(out, index)
        if value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        elif value == '6' and label == '示例树':
            checks.append((True, '计数 ' + index + '：示例树前序走完 6 个结点'))
        elif label == '链状树' and value == '5':
            checks.append((True, '计数 ' + index + '：链状树前序走完 5 个结点'))
        elif label == '平衡树' and value == '15':
            checks.append((True, '计数 ' + index + '：平衡树前序走完 15 个结点'))
        else:
            hint = {'示例树': '（课件那棵，一行一行照抄）',
                    '链状树': '（TODO 5：一层一个左孩子）',
                    '平衡树': '（TODO 6：一层填满，按层编号）'}[label]
            checks.append((False, '计数 ' + index + '（' + label + '）打出 ' + show(value)
                           + '，个数不对：先看那棵树搭对了没' + hint
                           + '，再看 TODO 1 的前序遍历有没有漏结点'))

    # ── 五、探针：import 学生的函数 ───────────────────────────────
    raw, err = run_probe('task1_traversal', PROBE_TASK1)
    if raw is None:
        checks.append((False, '任务 1 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)
    cases = {row[0]: row[1:] for row in data['cases']}

    broken = []
    for name, tree in [('empty', None), ('one', [7, None, None]), ('T', T_MODEL)]:
        got = cases.get(name)
        want = [model_pre(tree), model_in(tree), model_post(tree), model_level(tree)]
        if got is None or got != want:
            broken.append(name + ' 打出 ' + show(got) + '，期望 ' + show(want))
    if not broken:
        checks.append((True, '探针：空树 / 单点 / 判分自己搭的树三组上，四种遍历都与参照模型一致'))
    else:
        checks.append((False, '探针在 ' + str(len(broken)) + ' 组上对不上（TODO 1-4 还没写全）：'
                       + show('；'.join(broken))
                       + '：判分用的是它自己搭的树，别只对着课件那棵调'))

    # 累加器版的证据：函数要把传进去的列表接着用
    # 探针交回三段：返回值、传进去那个列表（调用后）、以及「返回值 is 那个列表」
    for label, note, todo in [('acc_pre', 'preorder', 'TODO 1'), ('acc_in', 'inorder', 'TODO 2')]:
        got = cases.get(label)
        if got is None or len(got) != 3:
            checks.append((False, '探针没给出 ' + label + ' 的完整结果：' + show(got)))
        elif got[1] == [99, 5] and got[0] == [99, 5] and got[2] is True:
            checks.append((True, '探针：' + note + ' 把值收进了**传进来**的列表里（[99] → [99, 5]），'
                                 '交回的正是它——累加器版'))
        elif got[1] == [99] and got[0] == [5]:
            checks.append((False, '探针：' + note + ' 把传进来的列表**丢掉**了（另开了一个）——'
                           '那是拼接版的形状。这一课要累加器版：out 不为 None 就接着用'))
        else:
            checks.append((False, '探针：' + note + ' 收到 (t, out) 之后打出 ' + show(got)
                           + '，期望 [\'[99, 5]\', \'[99, 5]\', True]'
                             '（值 append 进那个现成的列表，交回的还是它）：见 ' + todo))

    deep = cases.get('deep_level')
    tree = None
    for i in range(20):
        tree = [i, tree, [100 + i, None, None]]
    if deep == [model_level(tree)]:
        checks.append((True, '探针：层序在 20 层深的树上走完 40 个结点（队列版，不是递归）'))
    elif deep is None:
        pass
    else:
        checks.append((False, '探针：层序在 20 层深的树上打出 ' + show(deep)
                       + '，期望 ' + show([model_level(tree)]) + '：TODO 4 的队列里存的应当是**子树**'
                       + '（队列里别存值、存结点，取出时再取 x[0]）'))

    # 判分自己搭的平衡树（同一套口径：根是 k、左子树 k // 2 个结点）
    b7 = model_textbook_balanced(7)
    for label, want, note in [('bal7_pre', model_pre(b7), '前序'),
                              ('bal7_level', model_level(b7), '层序')]:
        got = cases.get(label)
        if got == [want]:
            checks.append((True, '探针：判分自己搭的 7 结点平衡树上，' + note + ' 与参照模型一致 ' + str(want)))
        else:
            checks.append((False, '探针：判分自己搭的 7 结点平衡树上，' + note + ' 打出 ' + show(got)
                           + '，期望 ' + show([want]) + '：TODO 1-4 走完这 7 个结点（树高 3；'
                             '前序是「根、整棵左、整棵右」，层序按层）'))

    # 值里带 0 的树：层序的队列版要比较 is not None，别写成 if x[1]
    zero = N(0, N(0, N(1), None), N(0, None, N(2)))
    for label, want, note in [('zero_pre', model_pre(zero), '前序'),
                              ('zero_level', model_level(zero), '层序')]:
        got = cases.get(label)
        if got == [want]:
            checks.append((True, '探针：值里带 0 的树上，' + note + ' 一个结点都没漏 ' + str(want)))
        else:
            checks.append((False, '探针：值里带 0 的树上，' + note + ' 打出 ' + show(got)
                           + '，期望 ' + show([want]) + '：TODO 4 入队前要比较 x[1] is not None——'
                             '写成 if x[1] 会把值为 0 的结点丢掉'))

    # 每个结点正好走一次：判分自己在探针里搭的那棵树，四种遍历都要走满 7 个结点
    probe_tree = data.get('tree')
    if probe_tree == model_textbook_balanced(7):
        want_seen = sorted(model_values(probe_tree))
        counts = data['sig'].get('counts')
        if counts == [want_seen] * 4:
            checks.append((True, '探针：7 个结点的树上四种遍历各走满 7 个值，'
                                 '排序后与「树里全部结点的值」逐项相同——每个结点正好访问一次'))
        else:
            checks.append((False, '探针：四种遍历交回的值排序后是 ' + show(counts)
                           + '，期望四份都等于 ' + show(want_seen)
                           + '：TODO 1-4 里每个结点都该正好访问一次'
                             '（层序的队列版最容易在值为 0 的结点上出错）'))
        if unwrap(data['sig'].get('seen_level')) == model_level(probe_tree):
            checks.append((True, '探针：层序在判分自己的树上与参照模型逐项一致'))
        else:
            checks.append((False, '探针：TODO 4 的层序打出 '
                       + show(unwrap(data['sig'].get('seen_level')))
                           + '，期望 ' + show(model_level(probe_tree))))
    else:
        checks.append((False, '探针：判分自己搭的树没被原样交回（' + show(probe_tree) + '）：'
                       '层序应当**只读不写**，别改动传进来的树'))

    sig = data['sig']
    # 探针调用时给的是一个现成的列表 [99]，所以前三行期望 [99, 7]（99 在前面、
    # 新值 append 在后面）；层序不吃第二个参数，期望 [7]。
    want_sig = {'sig_pre': [99, 7], 'sig_in': [99, 7], 'sig_post': [99, 7],
                'sig_level': model_level([7, None, None])}
    for label, note, todo in [('sig_pre', 'preorder', 'TODO 1'), ('sig_in', 'inorder', 'TODO 2'),
                              ('sig_post', 'postorder', 'TODO 3'), ('sig_level', 'level_order', 'TODO 4')]:
        got = sig.get(label)
        if got == want_sig[label]:
            extra = '（能接住第二个参数 out）' if label != 'sig_level' else ''
            checks.append((True, '探针：' + note + ' 在单点上给出 ' + show(got) + extra))
        elif isinstance(got, str) and got.startswith('TypeError'):
            checks.append((False, '探针：' + note + ' 接不住第二个参数——' + show(got)
                           + '：' + todo + ' 的签名要写成 (t, out=None)（累加器版），'
                             '现在多半是拼接版的 (t)'))
        else:
            checks.append((False, '探针：' + note + ' 打出 ' + show(got)
                           + '，期望 ' + show(want_sig[label]) + '：见 ' + todo))
    return checks


# ══ 任务 2 · 节点数、树高与对称性 ════════════════════════════════════════

PROBE_TASK2 = '''
one0 = [7, None, None]

def show(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v
    return {'kind': type(v).__name__}

cases = []
# 五种数据的四列，与脚本里那张表同一批
rows = [('empty', None), ('one', one0), ('S', m.S), ('T', m.T), ('M1', m.M1)]
for name, t in rows:
    cases.append([name, show(m.count(t)), show(m.height(t)), show(m.is_symmetric(t))])

# 镜像对的四个分支
pairs = [('both_none', None, None),
         ('a_none', None, [1, None, None]),
         ('b_none', [1, None, None], None),
         ('same_leaf', [1, None, None], [1, None, None]),
         ('mirror_ok', [1, [2, None, None], None], [1, None, [2, None, None]]),
         ('mirror_bad_val', [1, [2, None, None], None], [1, None, [3, None, None]]),
         ('same_shape', [1, [2, None, None], None], [1, [2, None, None], None])]
for name, a, b in pairs:
    cases.append(['mirror_' + name, show(m.is_mirror(a, b))])

# 树高必须是拿两个孩子交回的值算出来的：链状与平衡两种形状都要对
shapes = []
for n in (1, 2, 5, 17, 100):
    chain = None
    for i in range(n):
        chain = [i, chain, None]
    shapes.append(['chain' + str(n), show(m.height(chain)), show(m.count(chain))])
for n in (1, 2, 6, 15, 31):
    t = None
    k = 0
    level = [None]
    built = [[i, None, None] for i in range(n)]
    for i in range(n):
        l = 2 * i + 1
        r = 2 * i + 2
        if l < n:
            built[i][1] = built[l]
        if r < n:
            built[i][2] = built[r]
    shapes.append(['full' + str(n), show(m.height(built[0])), show(m.count(built[0]))])

# is_symmetric 在没写好的树上不能碰坏：拿一个空树与一个单点试
cases.append(['sym_none', show(m.is_symmetric(None))])
cases.append(['sym_one', show(m.is_symmetric(one0))])

print('PROBE ' + json.dumps({'cases': cases, 'shapes': shapes}, ensure_ascii=False))
'''


def check_task2():
    checks = []
    run = run_script('task2_tree_stats.py')
    if run['status'] != 'ok':
        return [(False, 'task2_tree_stats.py 没跑通：' + run['note'])]
    out = run['out']

    # ── 一、那张表：五行 × 三列 ──────────────────────────────────
    want_rows = [('空树', None), ('单点', ONE), ('对称树', S_MODEL),
                 ('示例树', T_MODEL), ('只差一个值', M1_MODEL)]
    if get_line(out, '数据 节点数 树高 对称') is None:
        checks.append((False, '没看到表头「数据 节点数 树高 对称」这一行：带 print 的行别改、别删'))
    for name, tree in want_rows:
        got = want_line(out, name + ' ')
        if got is None:
            checks.append((False, '没看到「' + name + ' 节点数 树高 对称」这一行'))
            continue
        want = [str(model_count(tree)), str(model_height(tree)), str(model_symmetric(tree))]
        if got == want:
            checks.append((True, name + '：节点数 ' + want[0] + '、树高 ' + want[1]
                           + '、对称 ' + want[2]))
        else:
            checks.append((False, name + ' 打出 ' + show(' '.join(got)) + '，期望 ' + ' '.join(want)
                           + '：TODO 1-4 还没写（三列分别对应 count / height / is_symmetric；'
                           + '空树的节点数与树高都是 0、单点高度是 1）'))

    # ── 二、直接问 is_mirror 的三行 ──────────────────────────────
    for prefix, want, todo, hint in [
        ('镜像对 是不是镜像', 'False', 'TODO 3',
         'M1 的右子树是 node(\'B\', node(\'D\'))，与左子树**一模一样**——那是「相同」不是「互为镜像」；'
         '最后一行递归要找右孩子的**左**孩子：is_mirror(a[2], b[1])'),
        ('镜像树 自己是自己的镜像', 'True', 'TODO 3', '对称树 S 的两棵子树互为镜像，这一行该是 True'),
        ('示例树 两棵子树是不是镜像', 'False', 'TODO 3', '示例树的左子树有 D、E，右子树只有 F，镜像对不上')]:
        value = get_line(out, prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == want:
            checks.append((True, prefix + ' ' + want))
        else:
            checks.append((False, prefix + ' 打出 ' + show(value) + '，期望 ' + want
                           + '：' + hint + '（' + todo + '）'))

    # ── 三、探针：五种数据 + 四个分支 + 两种形状 ─────────────────────
    raw, err = run_probe('task2_tree_stats', PROBE_TASK2)
    if raw is None:
        checks.append((False, '任务 2 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)
    cases = {row[0]: row[1:] for row in data['cases']}

    broken = []
    for name, tree in [('empty', None), ('one', ONE), ('S', S_MODEL), ('T', T_MODEL), ('M1', M1_MODEL)]:
        got = cases.get(name)
        want = [model_count(tree), model_height(tree), model_symmetric(tree)]
        if got != want:
            broken.append(name + ' 打出 ' + show(got) + '，期望 ' + show(want))
    if not broken:
        checks.append((True, '探针：五种数据上 count / height / is_symmetric 三项全对（判分用的是它自己搭的树）'))
    else:
        checks.append((False, '探针在 ' + str(len(broken)) + ' 组上对不上（TODO 1-4 还没写全）：'
                       + show('；'.join(broken))))

    mirror_broken = []
    for name, a, b in [('both_none', None, None), ('a_none', None, ONE), ('b_none', ONE, None),
                       ('same_leaf', ONE, ONE),
                       ('mirror_ok', N(1, N(2), None), N(1, None, N(2))),
                       ('mirror_bad_val', N(1, N(2), None), N(1, None, N(3))),
                       ('same_shape', N(1, N(2), None), N(1, N(2), None))]:
        got = cases.get('mirror_' + name)
        want = [model_mirror(a, b)]
        if got != want:
            mirror_broken.append(name + ' 打出 ' + show(got) + '，期望 ' + show(want))
    if not mirror_broken:
        checks.append((True, '探针：is_mirror 的四个分支都对（都空 True、只有一个空 False、'
                             '值不同 False、左对右才 True）——例子里那对「形状相同的树」判为 False'))
    else:
        checks.append((False, '探针：is_mirror 有 ' + str(len(mirror_broken)) + ' 组不对：'
                       + show('；'.join(mirror_broken))
                       + '：TODO 3 的四个分支按「都空 → 只有一个空 → 比值 + 左对右两个递归」写'))

    shape_broken = []
    for row in data['shapes']:
        name, h, c = row[0], row[1], row[2]
        if name.startswith('chain'):
            tree = model_chain(int(name[5:]))
        else:
            n = int(name[4:])
            built = [N(i) for i in range(n)]
            for i in range(n):
                l, r = 2 * i + 1, 2 * i + 2
                if l < n:
                    built[i][1] = built[l]
                if r < n:
                    built[i][2] = built[r]
            tree = built[0]
        if h != model_height(tree) or c != model_count(tree):
            shape_broken.append(name + ' 打出 ' + show([h, c])
                                + '，期望 ' + show([model_height(tree), model_count(tree)]))
    if not shape_broken:
        checks.append((True, '探针：链状（1/2/5/17/100）与满二叉（1/2/6/15/31）两种形状上，'
                             '树高与节点数都对——height 是拿两个孩子交回的值算的'))
    else:
        checks.append((False, '探针：两种形状上有 ' + str(len(shape_broken)) + ' 组不对：'
                       + show('；'.join(shape_broken))
                       + '：TODO 2 的 height 要写 1 + max(height(左), height(右))，单点的高度是 1'))
    return checks


# ══ 任务 3 · 形状与递归深度 ══════════════════════════════════════════════

PROBE_TASK3 = '''
def show(v):
    return v

def tryheight(t):
    try:
        return show(m.height(t))
    except RecursionError:
        return 'RecursionError'

out = {}
lines = [('balanced100', 100), ('balanced1000', 1000), ('balanced10000', 10000),
         ('chain100', 100), ('chain1000', 1000), ('chain10000', 10000)]
for name, n in lines:
    if name.startswith('balanced'):
        out[name] = tryheight(m.build_balanced(n))
    else:
        out[name] = tryheight(m.build_chain(n))

# 学生报的「递归再深一层」：树高等于它时跑得动，再深一层报 RecursionError。
# 这里在**模块顶层**直接试（不进任何函数），与脚本主块里试它的层数一样深。
deep = m.max_safe_depth()
out['deep'] = deep
out['deep_ok'] = 'no'
try:
    h = m.height(m.build_chain(deep))
    if h != deep:
        out['deep_ok'] = 'wrong-height:' + str(h)
    else:
        try:
            m.height(m.build_chain(deep + 1))
            out['deep_ok'] = 'no-recursion-error'
        except RecursionError:
            out['deep_ok'] = 'yes'
except RecursionError:
    out['deep_ok'] = 'crashed'

# 判分自己在**顶层**二分出那条线：height 还能走多深
lo, hi = 900, 1100
while lo < hi:
    mid = (lo + hi + 1) // 2
    try:
        m.height(m.build_chain(mid))
        lo = mid
    except RecursionError:
        hi = mid - 1
out['judge_lo'] = lo
out['judge_hi'] = lo + 1

out['recursion_after'] = __import__('sys').getrecursionlimit()
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task3():
    checks = []
    run = run_script('task3_depth_shape.py')
    if run['status'] != 'ok':
        return [(False, 'task3_depth_shape.py 没跑通：' + run['note'])]
    out = run['out']

    # ── 一、两种形状在三种规模上的树高 ───────────────────────────
    for shape, build, sizes in [('平衡', model_balanced, (100, 1000, 10000)),
                                ('链状', model_chain, (100, 1000, 10000))]:
        for n in sizes:
            prefix = '树高行 ' + shape + ' n=' + str(n)
            got = want_line(out, prefix)
            if got is None:
                checks.append((False, '没看到「' + prefix + ' …」这一行'))
                continue
            if shape == '链状' and n > CRASH_LENGTH:
                want = ['爆栈', '爆栈']
            else:
                want = [str(model_height(build(n))), '跑得动']
            if got == want:
                checks.append((True, prefix + ' → ' + ' '.join(want)))
            else:
                checks.append((False, prefix + ' 打出 ' + show(' '.join(got)) + '，期望 ' + ' '.join(want)
                               + '：要写的是 TODO 1/2 的 build_balanced / build_chain 与 TODO 3 的 height；'
                                  '树高等于递归深度，链状树超过递归上限就该在这一行看见爆栈'))
    got = count_value(out, '01')
    if got == '14':
        checks.append((True, '计数 01：平衡树 10000 个结点的树高是 14（约 log2 n）'))
    elif got is None:
        checks.append((False, '没看到「计数 01 平衡 n=10000 树高 …」这一行'))
    else:
        checks.append((False, '计数 01 打出 ' + show(got) + '，期望 14：'
                       '一万个结点的平衡树只走 14 层——TODO 3 的 height 一写出来就有这一行'
                             '（这就是「形状决定深度」）'))

    # ── 二、爆栈长度与「递归再深一层」 ───────────────────────────
    crash_at = CRASH_LENGTH
    crash = get_line(out, '链状 爆栈长度')
    if crash is None:
        checks.append((False, '没看到「链状 爆栈长度 …」这一行'))
    else:
        parts = crash.split()
        tail = parts[-1] if parts else ''
        if tail.isdigit():
            crash_at = int(tail)
        if tail == str(CRASH_LENGTH):
            checks.append((True, '链状树加到 ' + tail + ' 层就爆栈（' + str(CRASH_LENGTH - 1)
                                 + ' 层还跑得动）——与第 12 课那个上限是同一个'))
        elif tail == '0':
            checks.append((False, '链状 爆栈长度 打出 0：TODO 2 的 build_chain 还是占位的 None，'
                           '所以一直没爆栈。先让它搭出一条真的链'))
        else:
            checks.append((False, '链状 爆栈长度 打出 ' + show(crash) + '，期望 ' + str(CRASH_LENGTH)
                           + '：这一段是判分接口，别改；要从 990 往上试到第一条爆栈的链'))
    deep_line = get_line(out, '递归再深一层')
    deep = None
    if deep_line is None:
        checks.append((False, '没看到「递归再深一层 …」这一行'))
    else:
        text = deep_line.split()[0] if deep_line.split() else ''
        try:
            deep = int(text)
        except ValueError:
            deep = None
        if deep is None:
            checks.append((False, '递归再深一层 打出 ' + show(deep_line) + '，读不出整数：'
                           'TODO 4 的 max_safe_depth 还没写'))
        elif deep == 0:
            checks.append((False, '递归再深一层 打出 0：TODO 4 还是占位值。'
                           '它要交回「树高等于它时还跑得动、再深一层就报 RecursionError」的最大值'))
        elif not DEEP_LOW <= deep <= DEEP_HIGH:
            checks.append((False, '递归再深一层 打出 ' + str(deep) + '，期望在 '
                           + str(DEEP_LOW) + '-' + str(DEEP_HIGH) + ' 之间（贴着上限、'
                             '但比上限本身小几层）：从 limit - 5 开始试着往上加，'
                             '别直接交回 recursionlimit，也别差出一大截'))
        else:
            checks.append((True, '递归再深一层 ' + str(deep) + '（参考解 ' + str(EXPECT_DEEP)
                                 + '）：树高等于它时跑得动，再深一层就撞上限。'
                                   '这一行注定差得动一两层——差在哪几个栈帧上'))
        if deep is None or deep == 0:
            # 还没量出来（TODO 4 是占位的 0）：上一条已经点过 TODO 4 了，这里不重复
            pass
        elif deep > crash_at - 1:
            checks.append((False, '递归再深一层（' + str(deep) + '）大于爆栈长度减一（'
                           + str(crash_at - 1) + '）：主块顶层试出来 '
                           + str(crash_at - 1) + ' 层跑得动，你报的却更大——'
                             '这一行得在主块那种深度上能站得住'))
        else:
            checks.append((True, '递归再深一层不大于「爆栈长度减一」（' + str(crash_at - 1)
                                 + '）：与主块那条线对得上'))
    limit_text = get_line(out, '注释 递归上限')
    if limit_text is None:
        checks.append((False, '没看到「注释 递归上限 …」这一行'))
    else:
        try:
            limit = int(limit_text.split()[0])
        except (ValueError, IndexError):
            limit = None
        if limit is None:
            checks.append((False, '注释 递归上限 打出 ' + show(limit_text) + '，读不出整数'))
        elif deep is None or deep == 0:
            checks.append((False, '递归再深一层 还没量出来（' + show(deep) + '），'
                           '这一条先看不了：先写 TODO 4'))
        elif limit - deep < 1:
            checks.append((False, '递归上限（' + str(limit) + '）与递归再深一层（' + str(deep)
                           + '）之间没有余量：交回的不该是「贴着上限」的值，'
                             '要交回**跑得动**的最大值'))
        elif limit - deep > 6:
            checks.append((False, '递归上限（' + str(limit) + '）比递归再深一层（' + str(deep)
                           + '）多了 ' + str(limit - deep) + ' 层，期望 1-6 层：'
                             '交回的值太保守了——`height` 自己不需要多少余量，'
                             '它只比上限小几层固定开销（进入 height、递归里调用 max、'
                             '解释器自己占的那几层）；也别在函数里改递归上限'))
        else:
            checks.append((True, '递归上限 ' + str(limit) + ' 与递归再深一层 ' + str(deep)
                                 + ' 只差 ' + str(limit - deep)
                                 + ' 层固定开销（进 height、递归里调用 max、解释器自己那几层）'))
    for prefix, want, good in [
        ('递归深度比上限小几层', 'True', '递归深度比 sys.getrecursionlimit() 小几层'),
        ('固定开销的层数', None, '固定开销是几层（本机 2-3 层，差几层都算对，看的是它与上限的关系）')]:
        value = get_line(out, prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif want is None:
            # 「固定开销的层数」这一行：只看它是不是一个小整数，不核对具体值
            try:
                layers = int(value)
            except ValueError:
                layers = None
            if layers is None or not 0 <= layers <= 10:
                checks.append((False, prefix + ' 打出 ' + show(value)
                               + '，期望一个 10 以内的小整数：TODO 4 的 max_safe_depth 还没写出来'
                               + '（要是不对，说明 递归上限 与 '
                                 '递归再深一层 里有一个错了）'))
            else:
                checks.append((True, prefix + ' ' + str(layers) + '：' + good))
        elif value == want:
            checks.append((True, prefix + ' ' + want + '：' + good))
        else:
            checks.append((False, prefix + ' 打出 ' + show(value) + '，期望 ' + want))
    for index, expect, label in [('02', str(CRASH_LENGTH), '爆栈长度')]:
        value = count_value(out, index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' ' + label + ' 打出 ' + show(value)
                           + '，期望 ' + expect + '：TODO 2 的 build_chain 还搭不出链'))

    # ── 三、探针：判分自己复核那两条线 ───────────────────────────
    raw, err = run_probe('task3_depth_shape', PROBE_TASK3)
    if raw is None:
        checks.append((False, '任务 3 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)

    for name, build, n, want in [('balanced100', model_balanced, 100, 7),
                                 ('balanced1000', model_balanced, 1000, 10),
                                 ('balanced10000', model_balanced, 10000, 14),
                                 ('chain100', model_chain, 100, 100),
                                 ('chain1000', model_chain, 1000, 'RecursionError')]:
        got = data.get(name)
        if got == want:
            checks.append((True, '探针：' + name + ' → ' + str(got)))
        else:
            checks.append((False, '探针：' + name + ' 打出 ' + show(got) + '，期望 ' + show(want)
                           + '：先看 TODO 1/2 的 build_balanced / build_chain'
                           + ' 搭出来的是不是那棵树，再看 TODO 3 的 height'))
    # 判分自己的复核：探针在顶层自己二分出「height 还能走多深」，再看学生报的值对不对
    lo = data.get('judge_lo')
    hi = data.get('judge_hi')
    if lo is None:
        checks.append((False, '探针没给出它自己量到的边界'))
    else:
        checks.append((True, '探针：判分自己在顶层二分出这条线——' + str(lo) + ' 层的链算得出、'
                             + str(hi) + ' 层的链抛 RecursionError。'
                             '「递归深度等于树高」在链上就是这条线（差一两层是栈帧的事）'))
        d = data.get('deep')
        if not isinstance(d, int) or d == 0:
            checks.append((False, '探针：TODO 4 的 max_safe_depth 还是 ' + show(d) + '，没量出来'))
        elif d > lo:
            checks.append((False, '探针：max_safe_depth 交回 ' + str(d) + '，可判分自己量到 '
                           + str(lo) + ' 层就顶住了、再深一层（' + str(lo + 1)
                           + '）就报错：交回的值太大，那个深度站不住'))
        elif d < lo - 3:
            checks.append((False, '探针：max_safe_depth 交回 ' + str(d) + '，判分自己量到的是 '
                           + str(lo) + '：交回得太保守——它是「跑得动的最大值」，'
                             '要一直往上试到第一条爆栈的链'))
        else:
            checks.append((True, '探针：max_safe_depth 交回的 ' + str(d) + ' 与判分自己量到的 '
                                 + str(lo) + ' 对得上（函数里试会比顶层少一两层：'
                                   '多了一层 height 调用、build_chain 的那一层还没退掉）'))
    if data.get('deep_ok') == 'yes':
        checks.append((True, '探针：那个深度上 height 交回的树高等于深度本身——'
                             '「递归深度等于树高」在这份实现里是实打实成立的'))
    elif data.get('deep_ok') == 'crashed':
        checks.append((False, '探针：max_safe_depth 交回 ' + show(data.get('deep'))
                       + '，但那个深度上 height 自己就爆栈了：'
                         '交回的应当是**跑得动**的那个最大值，试太大时要退回上一次'))
    elif data.get('deep_ok') == 'no-recursion-error':
        # 边界上难免差一两层（函数里试比顶层多半层 height 调用）：
        # 上面已经确认它落在判分自己量到的那个值附近，这里不再要求它正好顶在边界上
        checks.append((True, '探针：max_safe_depth 交回的 ' + show(data.get('deep'))
                             + ' 比边界（' + show(lo) + '）保守一两层——'
                               '函数里试的身位与顶层不同，差一层属正常'))
    elif isinstance(data.get('deep_ok'), str) and data['deep_ok'].startswith('wrong-height'):
        checks.append((False, '探针：max_safe_depth 交回 ' + show(data.get('deep'))
                       + '，可那个深度上 height(chain) 交回的是 '
                       + show(data['deep_ok'].split(':', 1)[1])
                       + '（应当等于深度本身）：height 的公式不对'))
    else:
        checks.append((False, '探针：max_safe_depth 的结果有问题：deep=' + show(data.get('deep'))
                       + '、deep_ok=' + show(data.get('deep_ok'))))
    after = data.get('recursion_after')
    if after == 1000:
        checks.append((True, '探针：探查结束后递归上限仍然是 1000（TODO 4 把上限还原了）'))
    else:
        checks.append((False, '探针：探查结束后递归上限变成了 ' + show(after) + '，期望 1000：'
                       'TODO 4 收尾要把原值 setrecursionlimit 回去'))
    return checks


# ══ 任务 4 · 拼接与累加器的代价 ══════════════════════════════════════════

PROBE_TASK4 = '''
def show(v):
    return v

def tryit(f, t):
    try:
        v = show(f(t))
        if isinstance(v, list):
            return v[:6]
        return v
    except RecursionError:
        return 'RecursionError'

out = {}
out['chain50'] = tryit(m.preorder_concat, m.build_chain(50))
out['chain_n'] = show(m.build_chain(3))
out['empty_c'] = tryit(m.preorder_concat, None)
out['empty_a'] = tryit(m.preorder_acc, None)
b = m.build_balanced(7)
try:
    out['balanced_head'] = m.preorder_concat(b)
    out['balanced_count'] = len(out['balanced_head'])
except RecursionError:
    out['balanced_head'] = 'RecursionError'
    out['balanced_count'] = None

ones = [None] * 8
leftover = [99]
try:
    got = m.preorder_acc([5, None, None], leftover)
    out['acc_leftover'] = show(got)
    out['acc_after'] = show(leftover)
    out['acc_same'] = got is leftover
except TypeError as exc:
    out['acc_leftover'] = 'TypeError: ' + str(exc)

# best_of 真的取了最快的一次吗：拿一个恒定的函数试
calls = [0]
def fixed(t):
    calls[0] += 1
    return []
try:
    out['best_fixed'] = show(m.best_of(fixed, None, 7))
    out['best_calls'] = calls[0]
except TypeError as exc:
    out['best_fixed'] = 'TypeError: ' + str(exc)
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def scan_concat_version(checks):
    """源码扫描：前序遍历三处都必须是累加器版，不能出现拼接版。"""
    path = HERE / 'task1_traversal.py'
    path2 = HERE / 'task4_concat_cost.py'
    body = path.read_text(encoding='utf-8', errors='replace') if path.is_file() else ''
    body2 = path2.read_text(encoding='utf-8', errors='replace') if path2.is_file() else ''
    try:
        tree = ast.parse(body)
    except SyntaxError as exc:
        checks.append((False, 'task1_traversal.py 语法有问题：' + str(exc)))
        return
    bad = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(fn):
            if isinstance(node, ast.Return) and node.value is not None:
                calls = [n for n in ast.walk(node.value) if isinstance(n, ast.Call)
                         and isinstance(n.func, ast.Name) and n.func.id == fn.name]
                if calls and _has_add(node.value):
                    bad.append(fn.name)
    for name in sorted(set(bad)):
        checks.append((False, 'task1_traversal.py 的 ' + name + ' 被扫出**拼接版**的写法'
                       '（return 里出现了「函数自己调用自己」的结果相加）：'
                       '这一课要累加器版——把结果 append 进 out，别用 [] + [] 拼'))
    if not bad:
        checks.append((True, '源码扫描：task1_traversal.py 里三处递归遍历都没有拼接版的写法（都是累加器版）'))
    if 'preorder_concat' in body2 and _has_add_in_def(body2, 'preorder_concat'):
        checks.append((True, '源码扫描：task4 的 preorder_concat 是拼接版（这一份就是要它）'))
    else:
        checks.append((False, 'TODO 1 的 preorder_concat 没写成拼接版：'
                       '它要照课件那个形状写 return [t[0]] + preorder_concat(...) + preorder_concat(...)'))


def _has_add(node):
    for sub in ast.walk(node):
        if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Add):
            return True
    return False


def _has_add_in_def(source, name):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]:
        for node in ast.walk(fn):
            if isinstance(node, ast.Return) and node.value is not None and _has_add(node.value):
                return True
    return False


def check_task4():
    checks = []
    scan_concat_version(checks)

    run = run_script('task4_concat_cost.py')
    if run['status'] != 'ok':
        checks.append((False, 'task4_concat_cost.py 没跑通：' + run['note']))
        return checks
    out = run['out']

    for prefix, want, hint in [
        ('链状 200 两版答案一致', 'True', '两个版本在同一棵树上必须给出同一个列表'),
        ('空树 两版答案一致', 'True', '两版在空树上都该交回 []'),
        ('单点 两版答案一致', 'True', '两版在单点树上都该交回 [7]')]:
        value = get_line(out, prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value.startswith(want):
            checks.append((True, prefix + '：' + value.split()[0] + '——' + hint))
        else:
            checks.append((False, prefix + ' 打出 ' + show(value) + '，期望以 ' + want + ' 开头：' + hint))

    # ── 一、耗时真的量到了 ───────────────────────────────────────
    chain_c = time_values(out, '01')
    chain_a = time_values(out, '02')
    bal_c = time_values(out, '03')
    bal_a = time_values(out, '04')
    for name, values, index, todo in [('链状 拼接', chain_c, '01', 'TODO 1/3/5'),
                                      ('链状 累加器', chain_a, '02', 'TODO 2/3/5'),
                                      ('平衡 拼接', bal_c, '03', 'TODO 1/4/5'),
                                      ('平衡 累加器', bal_a, '04', 'TODO 2/4/5')]:
        if not values:
            checks.append((False, '没看到「耗时 ' + index + ' ' + name + ' n=… 秒」这一行：'
                           '带 print 的行别改、别删'))
        elif any(s <= 0 for _, s in values):
            checks.append((False, name + ' 有三行的秒数是 0.000000：' + todo
                           + ' 还没写出来（留白版三行都是 0）'))
        elif len(values) != 3:
            checks.append((False, name + ' 只读到 ' + str(len(values)) + ' 行（期望 3 行：三档规模）'))
        else:
            checks.append((True, name + '：三档耗时都量到了（' + ' / '.join(
                f'{s:.6f}' for _, s in values) + ' 秒）'))

    # ── 二、趋势：链状上拼接是平方级、累加器接近线性 ──────────────
    if len(chain_c) == 3 and len(chain_a) == 3 and all(s > 0 for _, s in chain_c + chain_a):
        c_small, c_mid, c_big = (x[1] for x in chain_c)
        a_small, a_mid, a_big = (x[1] for x in chain_a)
        c_grow = c_big / c_small              # 链长四倍，拼接涨多少倍
        c_last = c_big / c_mid
        a_grow = a_big / a_small
        # 三档里最小那一档最容易被「第一次跑」的噪声抬高，所以主判据用整段涨幅：
        # 链长翻四倍，线性的话是 4 倍，平方级接近 13-17 倍。
        if c_grow >= 8.0:
            checks.append((True, '链状 200→800（四倍长）：拼接涨 ' + f'{c_grow:.2f}'
                                 + ' 倍、最后一次翻倍涨 ' + f'{c_last:.2f}'
                                 + ' 倍——拼接版这一列不是线性的（线性该是 4 倍上下）'))
        else:
            checks.append((False, '链状 200→800（四倍长）拼接版只涨 ' + f'{c_grow:.2f}'
                           + ' 倍（最后一次翻倍 ' + f'{c_last:.2f}' + ' 倍），期望 8 倍以上：'
                             'TODO 1 要写成课件那个拼接形状（[t[0]] + 递归 + 递归），'
                             '而且链状树要经 build_chain 一路递归下去'))
        if a_grow <= 8.0:
            checks.append((True, '链状 200→800 累加器只涨 ' + f'{a_grow:.2f}'
                                 + ' 倍——接近线性，每个结点只被收一次'))
        else:
            checks.append((False, '链状 200→800 累加器涨了 ' + f'{a_grow:.2f}'
                           + ' 倍，期望 8 倍以内（线性该是 4 倍上下）：'
                             'TODO 2 要往传进来的 out 里 append，别另开列表、也别在返回时拼接'))
    else:
        checks.append((False, '链状那两列的秒数不全，趋势这一条先看不了：先把 TODO 1、2 写出来'))

    # ── 三、形状对照：链状上的倍数明显大于平衡树 ─────────────────
    ratios = label_values(out, '形状对照 ')
    if len(ratios) < 2:
        checks.append((False, '没读到「形状对照 链状倍数 …」「形状对照 平衡倍数 …」这两行'))
    else:
        chain_ratio, bal_ratio = ratios[0], ratios[1]
        if chain_ratio <= 1.0:
            checks.append((False, '形状对照 链状倍数（TODO 3/4 的造树 + TODO 5 的 best_of）打出 ' + f'{chain_ratio:.2f}'
                           + '，期望大于 1：链状 2000 个结点上拼接应当明显慢于累加器'))
        elif bal_ratio <= 1.0:
            checks.append((True, '形状对照：链状 ' + f'{chain_ratio:.2f}' + ' 倍、平衡 '
                                 + f'{bal_ratio:.2f}' + ' 倍——平衡树上两版差不多，'
                                   '链状树上拼接明显慢（平衡树上拼接要复制的量本来就少）'))
        elif chain_ratio >= 2.0 * bal_ratio:
            checks.append((True, '形状对照：链状上拼接慢 ' + f'{chain_ratio:.2f}' + ' 倍，平衡树上只慢 '
                                 + f'{bal_ratio:.2f}' + ' 倍——差距与**形状**有关，不只是与 n 有关'))
        else:
            checks.append((False, '形状对照：链状 ' + f'{chain_ratio:.2f}' + ' 倍、平衡 '
                           + f'{bal_ratio:.2f}' + ' 倍，两者太接近，期望链状那一列明显更大：'
                             '量性能不能只测一种形状——链状树上每层都要复制剩下那半条链'))
    value = get_line(out, '链状上的倍数更大')
    if value is None:
        checks.append((False, '没看到「链状上的倍数更大 …」这一行'))
    elif value == 'True':
        checks.append((True, '链状上的倍数更大 True'))
    else:
        checks.append((False, '链状上的倍数更大 打出 ' + show(value) + '，期望 True：'
                       'TODO 1 的拼接版与 TODO 2 的累加器版要在链状树上真的差出量级'))
    value = count_value(out, '01')
    if value == 'True':
        checks.append((True, '计数 01：2000 个结点的链上两版答案完全一致（慢不慢的先看对不对）'))
    elif value is None:
        checks.append((False, '没看到「计数 01 …」这一行'))
    else:
        checks.append((False, '计数 01 打出 ' + show(value) + '，期望 True：'
                       '两个版本在任何树上都必须给出同一个列表'))

    # ── 四、探针 ─────────────────────────────────────────────────
    raw, err = run_probe('task4_concat_cost', PROBE_TASK4)
    if raw is None:
        checks.append((False, '任务 4 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)
    want_head = model_pre(model_chain(50))[:6]
    if data.get('chain50') == want_head:
        checks.append((True, '探针：判分自己搭的 50 结点链上，拼接版给出 50 个值、前 6 个与模型一致 '
                             + str(want_head)))
    else:
        checks.append((False, '探针：判分自己搭的链上，拼接版前 6 个打出 ' + show(data.get('chain50'))
                       + '，期望 ' + show(want_head) + '：TODO 1 的递归要同时进左孩子与右孩子'))
    if data.get('chain_n') == model_chain(3):
        checks.append((True, '探针：build_chain(3) 是三层往左下的链 ' + str(data.get('chain_n'))))
    else:
        checks.append((False, '探针：build_chain(3) 搭出 ' + show(data.get('chain_n'))
                       + '，期望 ' + show(model_chain(3)) + '：TODO 3 的 build_chain 每个结点只有左孩子'))
    if data.get('empty_c') == [] and data.get('empty_a') == []:
        checks.append((True, '探针：两版在空树上都交回 []'))
    else:
        checks.append((False, '探针：空树上拼接版 ' + show(data.get('empty_c')) + '、累加器版 '
                       + show(data.get('empty_a')) + '，都该是 []'))
    want_full = model_pre(model_textbook_balanced(7))
    if data.get('balanced_head') == want_full and data.get('balanced_count') == 7:
        checks.append((True, '探针：build_balanced(7) 是 7 个结点的平衡树，前序 ' + str(want_full)))
    else:
        checks.append((False, '探针：build_balanced(7) 前序打出 ' + show(data.get('balanced_head'))
                       + '（' + show(data.get('balanced_count')) + ' 个值），期望 ' + str(want_full)
                       + '：TODO 4 照课件那几行写（left = k // 2）'))
    got_acc = data.get('acc_leftover')
    after = data.get('acc_after')
    if isinstance(got_acc, str) and got_acc.startswith('TypeError'):
        checks.append((False, '探针：preorder_acc 接不住第二个参数——' + show(got_acc)
                       + '：TODO 2 的签名要写成 (t, out=None)'))
    elif (got_acc == [99, 5] and after == [99, 5] and data.get('acc_same') is True):
        checks.append((True, '探针：累加器版接住了传进来的列表并往里 append'
                             '（[99] → [99, 5]，交回的正是它）'))
    else:
        checks.append((False, '探针：TODO 2 的累加器版收到现成列表时交出 ' + show(got_acc)
                       + '、那个列表变成 ' + show(after) + '，期望两者都是 [99, 5]'
                         '（值收进**传进来**的那个列表，交回的还是它）'))
    if data.get('best_fixed') == 0.0 and data.get('best_calls') == 7:
        checks.append((True, '探针：best_of 把函数跑了 7 次并交回最快那次的秒数'))
    elif isinstance(data.get('best_fixed'), str):
        checks.append((False, '探针：best_of 调不动——' + show(data.get('best_fixed'))
                       + '：它的签名是 (func, t, repeats)'))
    elif (isinstance(data.get('best_fixed'), (int, float))
          and data.get('best_calls') == 7):
        checks.append((True, '探针：best_of 跑了 7 次（每次都单独计时）、交回最快那次的 '
                             + f'{data["best_fixed"]:.6f}' + ' 秒'))
    else:
        checks.append((False, '探针：best_of 跑了 ' + show(data.get('best_calls')) + ' 次、交回 '
                       + show(data.get('best_fixed')) + '，期望跑 7 次并交回一个很小的秒数：TODO 5 的 best_of'
                       '要用 tools.timed 量每一次、取最小的一次'))
    return checks


CHECKERS = {
    'task1_traversal.py': check_task1,
    'task2_tree_stats.py': check_task2,
    'task3_depth_shape.py': check_task3,
    'task4_concat_cost.py': check_task4,
}


def main():
    print('StudyMate lab 0017 · 自动判分（树：会递归的结构）')
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
        print('四个任务都过了，再对照 ../solutions/0017-binary-tree-traversal/ 看参考解。')
        return 1
    print('四个任务都过了。现在去对照 ../solutions/0017-binary-tree-traversal/：')
    print('比一比你的写法与参考解，再用一句话回答「为什么收集结果要用累加器、'
          '而且测性能不能只测一种形状」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
