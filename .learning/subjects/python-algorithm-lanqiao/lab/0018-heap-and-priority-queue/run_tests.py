#!/usr/bin/env python3
"""lab 0018 · 自动判分：跑四个任务脚本，读它们打印的行，另起探针 import 学生代码。

用法（在 lab/0018-heap-and-priority-queue/ 目录里）：

    py run_tests.py

判法：
  - 四个任务各起一个进程跑，只读它们打印出来的固定格式行，不 import 学生代码；
  - 期望值不是抄来的：判分自己按课件的口径算——上一课那种「每轮取最轻的两堆合并」
    的和、第 k 大、数据流中位数、手写堆该弹出的升序序列——再与学生打印的行逐字对照；
  - 四个任务各另起**探针进程** import 学生的函数，拿判分自己造的数据去试：
    任务 1 试 `merge_list` / `merge_heap` / `merge_plan` 在随机小数据上对不对（这正是
    「两边结果一致」这句话的独立证据）；任务 2 试两种写法在各个 k 上是不是同一个值；
    任务 3 一步一步复核对顶堆的两条不变式；任务 4 逐步复核 `push` / `pop` / `_up` / `_down`；
  - 判分**看趋势不看常数**：秒数每次运行都会浮动（课件自己也写了第二次跑就不一样），
    所以合并果子那条只要求「列表版随规模涨得更快」、堆版在最大一档上更快。
    第 k 大那条只要求「k 很小时堆版更快」。

断言里的口径来自课件正文：堆只保证 `h[0]` 是最小值、其余位置没有顺序；
合并果子每轮取最轻的两堆、总代价是每轮代价之和；`heapify` 是 O(n)、`heappush`/`heappop`
是 O(log n)；第 k 大用大小为 k 的最小堆；对顶堆维持「lo 全不大于 hi」与「长度差不超过一」
两条不变式；插入是上浮、弹出是下沉。

退出码：0 = 四个任务都通过；1 = 还有没通过的。
"""

from __future__ import annotations

import ast
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMEOUT = 300

TODO_RE = re.compile(r'TODO\s+(\d+)')
FILE_LINE_RE = re.compile(r'File "([^"]*)", line (\d+)')

TASKS = [
    ('任务 1 · 合并果子两种写法（列表版每轮排序，堆版每轮弹两个压一个）', 'task1_merge_fruit.py', None),
    ('任务 2 · 前 k 大不必排全序（大小为 k 的最小堆）', 'task2_kth_largest.py', None),
    ('任务 3 · 数据流中位数（对顶堆）', 'task3_running_median.py', None),
    ('任务 4 · 手写一个最小堆（上浮与下沉）', 'task4_min_heap.py', None),
]

# 任务 1 的三档规模与任务 2 的规模：与任务文件里的常量一致（判分拿它们算趋势）
MERGE_SIZES = (1000, 2000, 4000)
MERGE_SEED = 11
KTH_N = 200000
KTH_SEED = 5
STREAM = (5, 15, 1, 8, 3, 8, 7, 9, 10, 6, 11, 4)      # 判分自己的流（与任务里那串不同）
HEAP_N = 1000
HEAP_SEED = 9


# ══ 参照模型：判分自己的口径（期望值都从这里来，不抄）══════════════════════

def model_merge_total(a):
    """合并果子：每轮取最轻的两堆合并，总代价是每轮代价之和（判分自己那一版）。"""
    b = sorted(a)
    total = 0
    while len(b) > 1:
        x = b.pop(0)
        y = b.pop(0)
        s = x + y
        total += s
        b.append(s)
        b.sort()
    return total


def model_median(stream):
    """数据流中位数：每来一个数，把当前所有数排一次序取中位数。"""
    out = []
    seen = []
    for v in stream:
        seen.append(v)
        seen.sort()
        n = len(seen)
        if n % 2 == 1:
            out.append(seen[n // 2])
        else:
            out.append((seen[n // 2 - 1] + seen[n // 2]) / 2)
    return out


def model_state(stream):
    """判分自己按课件的三步维持两个堆，交出每一步之后的 (lo 数, lo 顶, hi 数, hi 顶)。

    lo 存负数（最大堆），hi 是最小堆。这一步一步算出来的东西就是「不变式」的样子。
    """
    import heapq
    lo = []
    hi = []
    out = []
    for v in stream:
        heapq.heappush(lo, -v)
        heapq.heappush(hi, -heapq.heappop(lo))
        if len(hi) > len(lo):
            heapq.heappush(lo, -heapq.heappop(hi))
        out.append((len(lo), -lo[0], len(hi), hi[0] if hi else None))
    return out


def model_state_is_invariant(states, stream):
    """按判分自己的 state 复核两条不变式（长度差不超过一；lo 顶不大于 hi 顶）。"""
    ok_len = all(abs(row[0] - row[2]) <= 1 for row in states)
    ok_top = all(row[3] is None or row[1] <= row[3] for row in states)
    return ok_len, ok_top, len(states) == len(stream)


def show(value, limit=90):
    text = repr(value)
    return text[:limit] + '…' if len(text) > limit else text


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
                'note': '跑了 ' + str(timeout) + ' 秒还没结束（死循环？或者数据造得太大）'}
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-5:])
        return {'status': 'crash', 'out': done.stdout or '', 'err': done.stderr or '',
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


def count_value(lines, index):
    """从 `计数 NN 标签 值` 那几行里取值（只按编号找）。

    标签本身是中文词，所以不能盲目取第一段或最后一段：值一定是
    「整数」或「True/False」这两种形状之一，从**后往前**找到第一个这样的段。
    """
    if isinstance(lines, str):
        lines = lines.splitlines()
    for entry in lines:
        if not entry.startswith('计数 ' + index + ' '):
            continue
        body = entry[len('计数 ' + index + ' '):]
        for piece in reversed(body.split()):
            if VALUE_RE.match(piece) or piece in ('True', 'False'):
                return piece
    return None


def value_of(out, index):
    return count_value(out.splitlines(), index)


VALUE_RE = re.compile(r'^-?\d+$')
FLOAT_RE = re.compile(r'^-?\d+\.\d+$')


def time_values(out, index):
    """取 `耗时 NN 标签 n=… 0.000000 秒` 里的 (规模, 秒数)；同一编号可能有多行。

    规模写在整行里（有的任务写 `n=1000`、有的写 `k=10`），所以从整行里找；
    秒数固定是整行里倒数第二个词（紧接着那个「秒」字）。
    """
    values = []
    for entry in get_lines(out, '耗时 ' + index + ' '):
        parts = entry.split()
        if len(parts) < 2 or parts[-1] != '秒':
            continue
        try:
            seconds = float(parts[-2])
        except ValueError:
            continue
        m = re.search(r'[nk]=(\d+)', entry)
        values.append((int(m.group(1)) if m else None, seconds))
    return values


def parse_list(text):
    """把 "['D', 'E']" / "[1, 2]" / "[(1, 7, 0, None)]" 解析成列表；解析不了交回 None。"""
    if text is None:
        return None
    try:
        value = ast.literal_eval(text.strip())
    except (ValueError, SyntaxError):
        return None
    return value if isinstance(value, list) else None


def floats(seq):
    """把 [(n, 秒数), …] 只留秒数。"""
    return [s for _, s in seq]


def norm_state(seq):
    """探针的输出走 JSON，元组一律变成列表；比较前统一转回元组。

    不转的话 [[1, 7, 0, None]] 永远不等于 [(1, 7, 0, None)]，
    那是判分自己的锅，不能算学生错。
    """
    if not isinstance(seq, list):
        return seq
    return [tuple(item) if isinstance(item, list) else item for item in seq]


# ══ 任务 1 · 合并果子两种写法 ════════════════════════════════════════════

PROBE_TASK1 = '''
def show(v):
    return v

def total_of(f, a):
    try:
        v = f(list(a))
        return v if isinstance(v, int) else {'kind': type(v).__name__}
    except Exception as exc:
        return type(exc).__name__ + ': ' + str(exc)

def plan_of(a):
    try:
        p = m.merge_plan(list(a))
        return [len(p), sorted(p)]
    except Exception as exc:
        return type(exc).__name__ + ': ' + str(exc)

import random
# 必须与判分器的 JUDGE_DATA 同一造法（random.seed(MERGE_SEED + 1000) 且 randint(1, 1000)），
# 否则探针算的是另一批数，期望值永远对不上。
random.seed(11 + 1000)
POOL = [random.randint(1, 1000) for _ in range(200)]
out = {'cases': []}
for n in (2, 3, 5, 20, 200):
    data = POOL[:n]
    out['cases'].append([n, total_of(m.merge_list, data), total_of(m.merge_heap, data)])
out['fixed'] = [[len(a), total_of(m.merge_list, a), total_of(m.merge_heap, a)]
                for a in ([], [4], [3, 5], [1, 1, 1, 1], [5, 5, 5],
                          [9, 9, 1, 1], list(range(50, 0, -1)))]
out['plan20'] = plan_of(POOL[:20])
out['plan_fixed'] = plan_of([1, 1, 1, 1])
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''

# 判分自己的合并果子数据（与任务文件同一种造法，判分自己算参照值）
random.seed(MERGE_SEED + 1000)
JUDGE_DATA = [random.randint(1, 1000) for _ in range(MERGE_SIZES[-1])]

# 任务脚本那一份数据：脚本里写的是 random.seed(MERGE_SEED)，它打印出来的总和就是按这份算的。
# 读打印行时必须拿这一份去核对；JUDGE_DATA（换了种子）只留给探针用。
random.seed(MERGE_SEED)
SCRIPT_DATA = [random.randint(1, 1000) for _ in range(MERGE_SIZES[-1])]


def check_task1():
    checks = []
    run = run_script('task1_merge_fruit.py')
    if run['status'] != 'ok':
        return [(False, 'task1_merge_fruit.py 没跑通：' + run['note'])]
    out = run['out']

    # ── 一、两边答案一致、且等于判分自己算的值 ────────────────────
    small = SCRIPT_DATA[:MERGE_SIZES[0]]
    want_total = model_merge_total(small)
    list_total = get_line(out, 'n=1000 列表版总和')
    heap_total = get_line(out, 'n=1000 堆版总和')
    for name, got, hint in [('列表版', list_total, 'TODO 1 的 merge_list'),
                            ('堆版', heap_total, 'TODO 2 的 merge_heap')]:
        if got is None:
            checks.append((False, '没看到「n=1000 ' + name + '总和 …」这一行：'
                                  '带 print 的行别改、别删'))
        elif got == str(want_total):
            checks.append((True, 'n=1000 ' + name + '总和 ' + got
                                 + '，与判分自己按「每轮取最轻的两堆」算的一致'))
        else:
            checks.append((False, 'n=1000 ' + name + '总和打出 ' + show(got) + '，期望 '
                                  + str(want_total) + '：看 ' + hint
                                  + '（每轮取最小的两个、把和放回去；列表版每轮末尾要再排一次序）'))
    value = get_line(out, '两版答案一致')
    if value is None:
        checks.append((False, '没看到「两版答案一致 …」这一行'))
    elif value.startswith('True') and list_total == heap_total and list_total == str(want_total):
        checks.append((True, '两版答案一致，而且与判分算的 ' + str(want_total) + ' 相同'
                             '——这不是「谁算得对」的区别，是代价的区别'))
    else:
        checks.append((False, '两版答案一致 打出 ' + show(value) + '，而两行总和是 '
                              + show(list_total) + ' / ' + show(heap_total)
                              + '，期望两边都等于判分算的 ' + str(want_total)
                              + '：TODO 1、TODO 2 有一个算错了'))
    cons = get_line(out, '合并果子 两版答案一致')
    if cons is not None and cons == 'True' and list_total == str(want_total):
        checks.append((True, '计数 01：合并果子 两版答案一致 True'))
    elif cons is None:
        checks.append((False, '没看到「合并果子 两版答案一致 …」这一行'))
    else:
        checks.append((False, '合并果子 两版答案一致 打出 ' + show(cons) + '（标签行打出 '
                              + show(value) + '），期望 True：两版必须给出同一个和'
                              '——把 TODO 1 与 TODO 2 都写出来，再做这一步核对'))
    got = value_of(out, '01')
    if got == str(want_total):
        checks.append((True, '计数 01 合并果子 堆版总和 ' + got))
    elif got is None:
        checks.append((False, '没看到「计数 01 合并果子 堆版总和 …」这一行'))
    else:
        checks.append((False, '计数 01 打出 ' + show(got) + '，期望 ' + str(want_total)
                              + '：TODO 2 的 merge_heap 还没算对'))

    # ── 二、合并的顺序 ─────────────────────────────────────────
    rounds = get_line(out, '合并过程 轮数')
    if rounds is None:
        checks.append((False, '没看到「合并过程 轮数 …」这一行'))
    else:
        parts = rounds.split()
        if parts and parts[0] == str(len(small) - 1):
            checks.append((True, '合并过程 轮数 ' + parts[0]
                                 + '：n 堆合并成一堆正好 n-1 轮'))
        else:
            checks.append((False, '合并过程 轮数 打出 ' + show(rounds) + '，期望 '
                                  + str(len(small) - 1) + '：TODO 3 的 merge_plan 每一轮 append '
                                  '一个三元组，最后一轮之后堆里只剩一堆'))
    head = parse_list(get_line(out, '合并过程 前三轮'))
    if head is None:
        checks.append((False, '没看到「合并过程 前三轮 …」这一行'))
    elif not head:
        checks.append((False, '合并过程 前三轮 打出 []：TODO 3 的 merge_plan 还是交回空表'))
    else:
        want_pairs = sorted((pair[0], pair[1]) for pair in head[:3])
        want_small = sorted(small)[:2]
        ok_shape = all(isinstance(p, (list, tuple)) and len(p) == 3 for p in head[:3])
        if ok_shape and want_pairs[0] == tuple(want_small):
            checks.append((True, '合并过程 前三轮 ' + show(head[:3])
                                 + '：第一轮挑的正是最小的两个 ' + show(want_small)
                                 + '（每轮取最轻的两堆）'))
        else:
            checks.append((False, '合并过程 前三轮 打出 ' + show(head[:3]) + '，期望每项都是 '
                                  '(x, y, x + y)、且第一轮的两个数是最小的两个 '
                                  + show(want_small) + '：TODO 3 要把每轮挑出的两个与它们的和记下来'))
    last = parse_list(get_line(out, '合并过程 末轮总和'))
    if last is None:
        checks.append((False, '没看到「合并过程 末轮总和 …」这一行'))
    elif len(last) == 1 and len(last[0]) == 3 and last[0][2] == sum(small):
        checks.append((True, '合并过程 末轮总和 ' + show(last)
                             + '：最后一轮合出来的那一堆，重量正好是所有堆的总和 '
                             + str(sum(small)) + '（注意它不是总代价，总代价是 '
                             + str(want_total) + '）'))
    else:
        checks.append((False, '合并过程 末轮总和 打出 ' + show(last) + '，期望最后一项的和等于 '
                              + str(sum(small)) + '——那是所有堆的重量之和（最后一轮把仅剩的两堆'
                              '并成一堆）；总代价 ' + str(want_total) + ' 是每一轮代价的累计，'
                              '两者不是一回事。TODO 3 记的第三个值是 x + y'))

    # ── 三、三档耗时与趋势 ─────────────────────────────────────
    t_list = time_values(out, '01')
    t_heap = time_values(out, '02')
    for name, values, todo in [('列表版', t_list, 'TODO 1'), ('堆版', t_heap, 'TODO 2')]:
        if not values:
            checks.append((False, '没看到「耗时 01/02 合并果子 ' + name + ' n=… 秒」这一行：'
                                  '带 print 的行别改、别删'))
        elif [n for n, _ in values] != list(MERGE_SIZES):
            checks.append((False, name + ' 读到的规模是 ' + show([n for n, _ in values])
                                  + '，期望 ' + show(list(MERGE_SIZES))
                                  + '：三档规模都要量一次'))
        elif any(s <= 0 for _, s in values):
            checks.append((False, name + ' 有三行的秒数是 0.000000：' + todo
                                  + ' 还没写出来（留白版三行都是 0）'))
        else:
            checks.append((True, name + '：三档耗时都量到了（'
                                  + ' / '.join(f'{s:.6f}' for _, s in values) + ' 秒）'))
    ls, hs = floats(t_list), floats(t_heap)
    if len(ls) == 3 and len(hs) == 3 and all(s > 0 for s in ls + hs):
        l_grow = ls[-1] / ls[0]
        h_grow = hs[-1] / hs[0]
        if h_grow < l_grow:
            checks.append((True, '规模翻四倍（1000→4000）：列表版涨 ' + f'{l_grow:.2f}'
                                 + ' 倍、堆版只涨 ' + f'{h_grow:.2f}'
                                 + ' 倍——堆版每一步是对数时间，列表版每轮都要重排整个列表'))
        else:
            checks.append((False, '规模翻四倍：列表版涨 ' + f'{l_grow:.2f}' + ' 倍、堆版涨 '
                                  + f'{h_grow:.2f}' + ' 倍，期望列表版涨得更多：'
                                    'TODO 1 要是**每轮排序**那一版（末尾 a.sort() 别漏）、'
                                    'TODO 2 要是 heappop 两次 + heappush 一次'))
        ratio = ls[-1] / max(hs[-1], 1e-9)
        if ratio > 1.0:
            checks.append((True, '最大一档（n=4000）上列表版比堆版慢 ' + f'{ratio:.2f}' + ' 倍'))
        else:
            checks.append((False, '最大一档上列表版只比堆版慢 ' + f'{ratio:.2f}'
                                  + ' 倍，期望明显更慢（课件实测 n=4000 时约 8.8 倍）：'
                                    '两个函数都检查一遍——列表版要真排序，堆版要先 heapify'))
    else:
        checks.append((False, '耗时那两列的秒数不全，趋势这一条先看不了：先把 TODO 1、TODO 2 写出来'))

    # ── 四、边界 ───────────────────────────────────────────────
    for prefix, want, hint in [
        ('空列表 两版都是 0', 'True', '空列表上两边都该直接交回 0（while len(a) > 1 一进去就不成立）'),
        ('单堆 两版都是 0', 'True', '只剩一堆时不用再合并，两边都该交回 0'),
        ('两堆 两版都是和', 'True', '两堆 3 与 5 合并一次，代价 8')]:
        value = get_line(out, prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value.startswith(want):
            checks.append((True, prefix + '：' + value.split()[0] + '——' + hint))
        else:
            checks.append((False, prefix + ' 打出 ' + show(value) + '，期望以 ' + want
                                  + ' 开头：' + hint + '（TODO 1 与 TODO 2 都要写出来才会是 True；'
                                    '另一个常见错：堆版的循环写成 while a，空列表上 '
                                    'heappop 会报 IndexError）'))
    got = value_of(out, '03')
    if got == '8':
        checks.append((True, '计数 03 两堆 堆版 8：两个数合并一次，代价是它们的和'))
    elif got is None:
        checks.append((False, '没看到「计数 03 两堆 堆版 …」这一行'))
    else:
        checks.append((False, '计数 03 两堆 堆版 打出 ' + show(got) + '，期望 8：'
                              'TODO 2 的 merge_heap 在 [3, 5] 上要先 heapify 再弹两个'))

    # ── 五、探针：拿判分自己造的数据试三个函数 ───────────────────
    raw, err = run_probe('task1_merge_fruit', PROBE_TASK1)
    if raw is None:
        checks.append((False, '任务 1 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)

    broken = []
    for row in data['cases']:
        n, got_list, got_heap = row[0], row[1], row[2]
        want = model_merge_total(JUDGE_DATA[:n])
        if got_list != want or got_heap != want:
            broken.append('n=' + str(n) + ' 列表版 ' + show(got_list) + '、堆版 ' + show(got_heap)
                          + '，期望都是 ' + str(want))
    if not broken:
        checks.append((True, '探针：判分自己造的 5 组随机数据（2/3/5/20/200 堆）上，'
                             'merge_list 与 merge_heap 都等于判分自己算的总代价'))
    else:
        checks.append((False, '探针在 ' + str(len(broken)) + ' 组上对不上（TODO 1/2 还没写全）：'
                              + show('；'.join(broken))))

    fixed_broken = []
    for n, got_list, got_heap in data['fixed']:
        if got_list != got_heap or not isinstance(got_list, int):
            fixed_broken.append('n=' + str(n) + ' 列表版 ' + show(got_list)
                                + '、堆版 ' + show(got_heap) + '（两边必须一致）')
    if not fixed_broken:
        checks.append((True, '探针：空列表 / 单堆 / 两堆 / 全相等（四个 1）等 7 组边界上，'
                             '两个版本给出的值完全一致'))
    else:
        checks.append((False, '探针：边界上有 ' + str(len(fixed_broken)) + ' 组两个版本不一致：'
                              + show('；'.join(fixed_broken))
                              + '：TODO 1/2 在「只剩一堆」「两堆」这些地方要给出同一个数'))

    plan = data.get('plan20')
    if isinstance(plan, list) and len(plan) == 2:
        rounds, triples = plan
        # 两个不同的量，别混：末轮合出来的那一堆重 = 所有堆的重量之和；
        # 而各轮 (x+y) 加起来才是题目的答案（累计代价）。
        want_last = sum(JUDGE_DATA[:20])
        want_cost = model_merge_total(JUDGE_DATA[:20])
        ok_shape = all(isinstance(t, (list, tuple)) and len(t) == 3 and t[2] == t[0] + t[1]
                       for t in triples)
        plan_cost = sum(t[2] for t in triples) if ok_shape and triples else None
        if (rounds == 19 and ok_shape and triples
                and triples[-1][2] == want_last and plan_cost == want_cost):
            checks.append((True, '探针：merge_plan 在 20 堆上给出 19 轮、每项都是 (x, y, x+y)；'
                                 '末轮合出的那一堆重 ' + str(triples[-1][2])
                                 + '（等于所有堆重量之和），各轮之和 ' + str(plan_cost)
                                 + ' 等于总代价'))
        else:
            checks.append((False, '探针：merge_plan 在 20 堆上给出 ' + show(plan)
                                  + '，期望 19 轮、每项 (x, y, x+y)、末轮合出的那一堆重 '
                                  + str(want_last) + '、各轮之和等于总代价 ' + str(want_cost)
                                  + '：TODO 3 别只记两个数，第三个是 x + y（末轮的和是最后一堆的重量，'
                                    '不等于累计代价）'))
    else:
        checks.append((False, '探针：merge_plan 调不动或交回的不是列表：' + show(plan)))
    return checks


# ══ 任务 2 · 前 k 大不必排全序 ═══════════════════════════════════════════

PROBE_TASK2 = '''
def show(v):
    return v

def call(f, *args):
    try:
        v = f(*args)
        if isinstance(v, list):
            return v[:5]
        return v
    except Exception as exc:
        return type(exc).__name__ + ': ' + str(exc)

import random
random.seed(23)
data = [random.randrange(10 ** 9) for _ in range(500)]
n = len(data)
out = {'pairs': []}
for k in (1, 2, 3, 10, 250, 499, 500):
    out['pairs'].append([k, call(m.kth_by_sort, data, k), call(m.kth_by_minheap, data, k)])
out['top'] = [[k, call(m.topk_by_heap, data, k), sorted(data, reverse=True)[:k][:5]]
              for k in (1, 3, 10)]
out['best'] = [call(m.smaller_heap_better, [(10, 8.0), (250, 1.2), (499, 0.9)]),
               call(m.smaller_heap_better, [(10, 0.5), (250, 1.2), (499, 3.0)])]
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task2():
    checks = []
    run = run_script('task2_kth_largest.py')
    if run['status'] != 'ok':
        return [(False, 'task2_kth_largest.py 没跑通：' + run['note'])]
    out = run['out']

    # ── 一、两种写法在每个 k 上给出同一个值 ─────────────────────
    random.seed(KTH_SEED)
    judge = [random.randrange(10 ** 9) for _ in range(KTH_N)]
    judge_sorted = sorted(judge, reverse=True)
    mismatched = []
    for k in (1, 2, 3, 10, KTH_N // 2, KTH_N - 1, KTH_N):
        line = get_line(out, 'k=' + str(k) + ' 排序版')
        if line is None:
            mismatched.append('k=' + str(k) + ' 那一行没看到')
            continue
        parts = line.split()
        if len(parts) < 3:
            mismatched.append('k=' + str(k) + ' 那一行读不出两个值：' + show(line))
            continue
        got_sort, got_heap = parts[0], parts[2]
        want = judge_sorted[k - 1]
        if got_sort == str(want) and got_heap == str(want):
            continue
        mismatched.append('k=' + str(k) + ' 排序版 ' + show(got_sort) + '、堆版 ' + show(got_heap)
                          + '，期望都是 ' + str(want))
    if not mismatched:
        checks.append((True, '七个 k（1 / 2 / 3 / 10 / 10 万 / 199999 / 20 万）上，'
                             '排序版与堆版都与判分自己排序取出的值一致'))
    else:
        checks.append((False, '有 ' + str(len(mismatched)) + ' 个 k 对不上：'
                              + show('；'.join(mismatched))
                              + '：TODO 1 取的是降序表的第 k-1 项、TODO 2 的堆里是最大的 k 个'
                                '（h[0] 是这 k 个里最小的，也就是第 k 大）'))

    for k, label in ((10, 'k=10'), (KTH_N, 'k=200000')):
        got = get_line(out, '第k大 ' + label + ' 一致')
        if got is None:
            checks.append((False, '没看到「第k大 ' + label + ' 一致 …」这一行'))
        elif got == 'True':
            checks.append((True, '第k大 ' + label + ' 一致 True'))
        else:
            checks.append((False, '第k大 ' + label + ' 一致 打出 ' + show(got)
                                  + '，期望 True：两种写法必须交出同一个值'))
    for index, k, hint in (('01', '10', 'TODO 2 的堆版'), ('02', str(KTH_N), 'TODO 1 与 TODO 2')):
        got = value_of(out, index)
        want = str(judge_sorted[int(k) - 1])
        if got == want:
            checks.append((True, '计数 ' + index + ' 第 k 大（k=' + k + '）' + got))
        elif got is None:
            checks.append((False, '没看到「计数 ' + index + ' 第k大 …」这一行'))
        else:
            checks.append((False, '计数 ' + index + '（k=' + k + '）打出 ' + show(got) + '，期望 '
                                  + want + '：看 ' + hint))

    # ── 二、前 k 大：自己写的堆要和 nlargest 一致 ────────────────
    a = sorted(judge, reverse=True)[:10]
    b = __import__('heapq').nlargest(10, judge)
    value = get_line(out, '前10大 两版一致')
    if value is None:
        checks.append((False, '没看到「前10大 两版一致 …」这一行'))
    elif value == 'True' and a == b:
        checks.append((True, '前10大 两版一致 True（排序取前 10 与 nlargest 恒等）'))
    else:
        checks.append((False, '前10大 两版一致 打出 ' + show(value) + '，期望 True'))
    value = get_line(out, '前10大 前三个')
    if value is None:
        checks.append((False, '没看到「前10大 前三个 …」这一行'))
    elif parse_list(value) == b[:3]:
        checks.append((True, '前10大 前三个 ' + value + '（20 万个数里最大的三个）'))
    else:
        checks.append((False, '前10大 前三个 打出 ' + show(value) + '，期望 ' + show(b[:3])))
    value = get_line(out, '自己写的堆 前10大 与 nlargest 一致')
    if value is None:
        checks.append((False, '没看到「自己写的堆 前10大 与 nlargest 一致 …」这一行'))
    elif value == 'True':
        checks.append((True, '自己写的堆 前10大 与 nlargest 一致 True'
                             '——大小 k 的最小堆能取出前 k 大，交回的顺序也对'))
    else:
        checks.append((False, '自己写的堆 前10大 与 nlargest 一致 打出 ' + show(value)
                              + '，期望 True：TODO 3 最后要把堆**逐个 heappop** 出来再反向'
                                '（堆只保证 h[0] 最小，其余位置没有顺序）'))
    value = get_line(out, '自己写的堆 前10大 前三个')
    if value is None:
        checks.append((False, '没看到「自己写的堆 前10大 前三个 …」这一行'))
    elif parse_list(value) == b[:3]:
        checks.append((True, '自己写的堆 前10大 前三个 ' + value + ' 与 nlargest 一致'))
    else:
        checks.append((False, '自己写的堆 前10大 前三个 打出 ' + show(value) + '，期望 '
                              + show(b[:3]) + '：TODO 3 的 topk_by_heap 还没交回东西'))

    # ── 三、k 从小到大：差距怎么变 ─────────────────────────────
    t_sort = time_values(out, '01')
    t_heap = time_values(out, '02')
    want_ks = [10, KTH_N // 2, KTH_N - 1]
    for name, values, todo in [('排序版', t_sort, 'TODO 1'), ('堆版', t_heap, 'TODO 2')]:
        if not values:
            checks.append((False, '没看到「耗时 01/02 第k大 ' + name + ' k=… 秒」这一行：'
                                  '带 print 的行别改、别删'))
        elif [n for n, _ in values] != want_ks:
            checks.append((False, name + ' 读到的规模是 ' + show([n for n, _ in values])
                                  + '，期望 ' + show(want_ks) + '：三档 k 都要量一次'))
        elif any(s <= 0 for _, s in values):
            checks.append((False, name + ' 有三行的秒数是 0.000000：' + todo
                                  + ' 还没写出来（留白版三行都是 0）'))
        else:
            checks.append((True, name + '：k=' + '/'.join(str(n) for n, _ in values)
                                  + ' 三档耗时都量到了（'
                                  + ' / '.join(f'{s:.6f}' for _, s in values) + ' 秒）'))
    ratios = [get_line(out, '倍数 k=' + str(k) + ' 排序比堆')
              for k in (10, KTH_N // 2, KTH_N - 1)]
    got_ratios = []
    for entry in ratios:
        try:
            got_ratios.append(float(entry))
        except (TypeError, ValueError):
            got_ratios.append(None)
    if all(r is not None for r in got_ratios):
        if got_ratios[0] > 1.0:
            checks.append((True, 'k=10 时排序版比堆版慢 ' + f'{got_ratios[0]:.2f}'
                                 + ' 倍——k 远小于 n 时不必排全序'))
        else:
            checks.append((False, 'k=10 时排序版比堆版慢 ' + f'{got_ratios[0]:.2f}'
                                  + ' 倍，期望大于 1：TODO 2 的堆版在 k 很小的时候应当明显更快'
                                    '（大小为 k 的堆只维护 k 个数）'))
        # 这一条是本机实测的倍数趋势，两个倍数差得不远（典型 8% 上下），
        # 单纯比大小会被计时噪声翻过来，所以留 25% 的噪声带。
        if got_ratios[0] >= got_ratios[-1] * 0.75:
            checks.append((True, 'k=10 的倍数（' + f'{got_ratios[0]:.2f}' + '）不小于 k=199999 的倍数（'
                                 + f'{got_ratios[-1]:.2f}' + '）——k 越大，堆省下的活越少'
                                 '（两个倍数靠得近，允许 25% 的计时噪声）'))
        else:
            checks.append((False, 'k=10 的倍数 ' + f'{got_ratios[0]:.2f}' + ' 明显小于 k=199999 的 '
                                  + f'{got_ratios[-1]:.2f}' + '（差距超出计时噪声）：两个 TODO 是不是互换了？'
                                    '堆版应当随 k 变大而越来越不占便宜'))
    else:
        checks.append((False, '没读到「倍数 k=… 排序比堆 …」这三行：'
                              + show(ratios) + '（带 print 的行别改）'))
    value = get_line(out, 'k 小的时候堆更划算')
    near_tie = (all(r is not None for r in got_ratios)
                and got_ratios[0] >= got_ratios[-1] * 0.75)
    if value is None:
        checks.append((False, '没看到「k 小的时候堆更划算 …」这一行'))
    elif value == 'True':
        checks.append((True, 'k 小的时候堆更划算 True'))
    elif value == 'False' and near_tie:
        checks.append((True, 'k 小的时候堆更划算 打出 False，但本机两个倍数只差 '
                             + f'{got_ratios[0]:.2f}' + ' 与 ' + f'{got_ratios[-1]:.2f}'
                             + '——落在计时噪声带里，True/False 都算对，这一条不扣'))
    else:
        checks.append((False, 'k 小的时候堆更划算 打出 ' + show(value) + '，期望 True：'
                              'TODO 4 的 smaller_heap_better 拿 k 最小那一项与 k 最大那一项比倍数'))
    got = value_of(out, '03')
    if got == 'True':
        checks.append((True, '计数 03 k小的时候堆更划算 True'))
    elif got is None:
        checks.append((False, '没看到「计数 03 k小的时候堆更划算 …」这一行'))
    elif got == 'False' and near_tie:
        checks.append((True, '计数 03 k小的时候堆更划算 打出 False——同上，落在计时噪声带里，不扣'))
    else:
        checks.append((False, '计数 03 k小的时候堆更划算 打出 ' + show(got) + '，期望 True：'
                              'TODO 4 还没写对'))

    # ── 四、探针 ───────────────────────────────────────────────
    raw, err = run_probe('task2_kth_largest', PROBE_TASK2)
    if raw is None:
        checks.append((False, '任务 2 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)
    random.seed(23)
    pool = [random.randrange(10 ** 9) for _ in range(500)]
    pool_sorted = sorted(pool, reverse=True)
    broken = []
    for row in data['pairs']:
        k, got_sort, got_heap = row[0], row[1], row[2]
        want = pool_sorted[k - 1]
        if got_sort != want or got_heap != want:
            broken.append('k=' + str(k) + ' 排序版 ' + show(got_sort) + '、堆版 ' + show(got_heap)
                          + '，期望都是 ' + str(want))
    if not broken:
        checks.append((True, '探针：判分自己造的 500 个数上，k=1/2/3/10/250/499/500 七个值'
                             '两种写法都对（这是「两边结果一致」的独立证据）'))
    else:
        checks.append((False, '探针有 ' + str(len(broken)) + ' 处对不上：' + show('；'.join(broken))
                              + '：TODO 1 与 TODO 2 的边界都要看——k=1 是最大值、k=n 是最小值'))
    top_broken = []
    for k, got, want in data['top']:
        if got != want:
            top_broken.append('k=' + str(k) + ' 打出 ' + show(got) + '，期望 ' + show(want))
    if not top_broken:
        checks.append((True, '探针：topk_by_heap 在 k=1/3/10 上给的是降序的前 k 大'
                             '（与 sorted 取前 k 一致）'))
    else:
        checks.append((False, '探针：topk_by_heap 有 ' + str(len(top_broken)) + ' 处不对：'
                              + show('；'.join(top_broken))
                              + '：TODO 3 要逐个 heappop 再反向，不能直接把内部数组交回'))
    best = data.get('best')
    if isinstance(best, list) and len(best) == 2 and best[0] is True and best[1] is False:
        checks.append((True, '探针：smaller_heap_better 两条都判对'
                             '——k 小的那组倍数更大（8.0 对 0.9）时 True，'
                             '反过来的那组（0.5 对 3.0）False'))
    elif best == [False, False] or best == [True, True]:
        checks.append((False, '探针：smaller_heap_better 两次都交回 ' + show(best[0])
                              + '——它是个常数，没在看传进来的 ratios：'
                                'TODO 4 要拿 k 最小那一项与 k 最大那一项的倍数比一比'))
    else:
        checks.append((False, '探针：smaller_heap_better 交出 ' + show(best)
                              + '，期望 [True, False]：TODO 4 要用首尾两项的倍数比，'
                                '首项大于末项才是 True（k 小的时候倍数更大，说明堆更划算）'))
    return checks


# ══ 任务 3 · 数据流中位数（对顶堆）═══════════════════════════════════════

PROBE_TASK3 = '''
def show(v):
    return v

def call(f, *args):
    try:
        v = f(*args)
        if isinstance(v, list):
            return v          # 不能截断：最长那条流有 11 步，截掉就跟期望对不上了
        return v
    except Exception as exc:
        return type(exc).__name__ + ': ' + str(exc)

out = {}
streams = [[], [7], [4, 9], [1, 2, 3, 4], [5, 15, 1, 3, 8, 7, 9, 10, 6, 11, 4],
           [2, 2, 2, 2, 2], [10, 1, 9, 2, 8, 3, 7, 4, 6, 5]]
out['med'] = [call(m.running_median, s) for s in streams]
out['state'] = [call(m.median_state, s) for s in streams]
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''

PROBE_STREAM = (5, 15, 1, 3, 8, 7, 9, 10, 6, 11, 4)


def check_task3():
    checks = []
    run = run_script('task3_running_median.py')
    if run['status'] != 'ok':
        return [(False, 'task3_running_median.py 没跑通：' + run['note'])]
    out = run['out']

    want_med = model_median(PROBE_STREAM)
    want_show = [int(m) if m == int(m) else m for m in want_med]

    # ── 一、中位数序列 ─────────────────────────────────────────
    got = get_line(out, '数据流')
    if got is None:
        checks.append((False, '没看到「数据流 …」这一行'))
    elif parse_list(got) == list(PROBE_STREAM):
        checks.append((True, '数据流就是课件那 11 个数 ' + show(list(PROBE_STREAM))))
    else:
        checks.append((False, '数据流 打出 ' + show(got) + '，期望 ' + show(list(PROBE_STREAM))))
    got = get_line(out, '中位数')
    if got is None:
        checks.append((False, '没看到「中位数 …」这一行'))
    else:
        value = parse_list(got)
        if value == want_show:
            checks.append((True, '中位数 ' + show(value) + ' 与课件逐字一致'
                                 '（每一步都是当前所有数的中位数）'))
        elif value == []:
            checks.append((False, '中位数 打出 []：TODO 1 的 running_median 还是交回空表'))
        else:
            checks.append((False, '中位数 打出 ' + show(value) + '，期望 ' + show(want_show)
                                  + '：TODO 1 照课件那段写（先无条件进 lo、把 lo 顶挪到 hi、'
                                    'hi 更长就挪回来；奇数取 -lo[0]、偶数取两个堆顶平均）'))
    got = get_line(out, '中位数 个数')
    if got == str(len(PROBE_STREAM)):
        checks.append((True, '中位数 个数 ' + got + '：一个数交回一个中位数'))
    elif got is None:
        checks.append((False, '没看到「中位数 个数 …」这一行'))
    else:
        checks.append((False, '中位数 个数 打出 ' + show(got) + '，期望 ' + str(len(PROBE_STREAM))
                              + '：TODO 1 要交回**每一步**的中位数序列，不是最后一个'))
    got = get_line(out, '中位数 是每一步的序列')
    if got is None:
        checks.append((False, '没看到「中位数 是每一步的序列 …」这一行'))
    elif got == 'True':
        checks.append((True, '中位数 是每一步的序列 True：交回的是序列，不是单个值'))
    else:
        checks.append((False, '中位数 是每一步的序列 打出 ' + show(got) + '，期望 True：'
                              'TODO 1 的 out 要在循环里每来一个数就 append 一个中位数'))

    # ── 二、每一步之后两个堆的长度与堆顶 ────────────────────────
    step_lines = []
    for i in range(1, len(PROBE_STREAM) + 1):
        line = get_line(out, '第' + str(i) + ' 步 ')
        if line is not None:
            step_lines.append((i, line))
    if len(step_lines) < len(PROBE_STREAM):
        checks.append((False, '「第 N 步 …」只找到 ' + str(len(step_lines)) + ' 行，期望 '
                              + str(len(PROBE_STREAM)) + ' 行：TODO 2 的 median_state 每一步都要 '
                                'append 一个四元组 (len(lo), -lo[0], len(hi), hi[0] if hi else None)'))
    else:
        want_states = model_state(PROBE_STREAM)
        bad = []
        for i, line in step_lines[:len(PROBE_STREAM)]:
            parts = line.split()
            if len(parts) < 4:
                bad.append('第 ' + str(i) + ' 步读不出四个数：' + show(line))
                continue
            lo_n, lo_top, hi_n = int(parts[0]), int(parts[1]), int(parts[2])
            hi_top = None if parts[3] == 'None' else int(parts[3])
            want = want_states[i - 1]
            if (lo_n, lo_top, hi_n, hi_top) != want:
                bad.append('第 ' + str(i) + ' 步打出 ' + show((lo_n, lo_top, hi_n, hi_top))
                           + '，期望 ' + show(want))
        if not bad:
            checks.append((True, '每一步之后两个堆的长度与堆顶都与判分自己维持的那两个堆一致'
                                 '（第一步 lo 1 个、hi 空着）'))
        else:
            checks.append((False, '逐步那一列有 ' + str(len(bad)) + ' 处对不上：' + show('；'.join(bad[:3]))
                                  + '：TODO 2 的 lo 存负数（堆顶要转回正数）、hi 为空时写 None'))
    for index, label, want in (('01', '长度差不超过一', True), ('02', 'lo 顶不大于 hi 顶', True)):
        got = value_of(out, index)
        if got == str(want):
            checks.append((True, '计数 ' + index + ' 不变式 ' + label + ' True'
                                 + '（这两条不变式立住，中位数才只能在两个堆顶上）'))
        elif got is None:
            checks.append((False, '没看到「计数 ' + index + ' 不变式 ' + label + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 不变式 ' + label + ' 打出 ' + show(got)
                                  + '，期望 True：TODO 1/TODO 2 的三步要一步不少'
                                    '（少了「把 lo 顶挪到 hi」这一步，lo 里就会有比 hi 大的数）'))

    # ── 三、边界 ───────────────────────────────────────────────
    for prefix, want, hint in [
        ('空流 中位数', '[]', '一个数都没有时交回空表（循环一次都不进）'),
        ('一个数 中位数', '[7]', '总数为奇数，中位数是 lo 顶上的那个数本身'),
        ('两个数 中位数', '[4, 6.5]', '偶数个取两个堆顶的平均：(4 + 9) / 2 = 6.5')]:
        got = get_line(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        else:
            value = parse_list(got)
            try:
                want_value = ast.literal_eval(want)
            except (ValueError, SyntaxError):
                want_value = None
            if value == want_value:
                checks.append((True, prefix + ' ' + got + '——' + hint))
            else:
                checks.append((False, prefix + ' 打出 ' + show(got) + '，期望 ' + want
                                      + '：' + hint + '（TODO 1 还没写对）'))
    got = get_line(out, '第一个数的状态')
    want_first = [(1, 7, 0, None)]
    if got is None:
        checks.append((False, '没看到「第一个数的状态 …」这一行'))
    elif parse_list(got) == want_first or ast.literal_eval(got) == want_first:
        checks.append((True, '第一个数的状态 ' + got + '：lo 有一个数、hi 还空着（None）'))
    else:
        checks.append((False, '第一个数的状态 打出 ' + show(got) + '，期望 ' + show(want_first)
                              + '：TODO 2 里 hi 为空时要写 hi[0] if hi else None，'
                                '写成 hi[0] 会在单个数上就报 IndexError'))

    # ── 四、探针：七条流上逐步复核 ──────────────────────────────
    raw, err = run_probe('task3_running_median', PROBE_TASK3)
    if raw is None:
        checks.append((False, '任务 3 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)
    streams = [[], [7], [4, 9], [1, 2, 3, 4], list(PROBE_STREAM),
               [2, 2, 2, 2, 2], [10, 1, 9, 2, 8, 3, 7, 4, 6, 5]]
    bad_med = []
    for stream, got in zip(streams, data['med']):
        want = model_median(stream)
        if got != want:
            bad_med.append('流 ' + show(stream) + ' 打出 ' + show(got) + '，期望 ' + show(want))
    if not bad_med:
        checks.append((True, '探针：七条流（空 / 单个 / 两个 / 递增 / 课件那串 / 全相同 / 一升一降）'
                             '上，每一步的中位数都与判分自己排序取的中位数一致'))
    else:
        checks.append((False, '探针：有 ' + str(len(bad_med)) + ' 条流的中位数不对：'
                              + show('；'.join(bad_med[:3]))
                              + '：TODO 1 在「总数为偶数」与「重复值」两类上最容易错'))

    bad_state = []
    for stream, raw_state in zip(streams, data['state']):
        want = model_state(stream)
        got = norm_state(raw_state)
        if got == want:
            continue
        if got == [] and want != []:
            bad_state.append('流 ' + show(stream) + ' 交回空表（TODO 2 还是占位值）')
        elif isinstance(got, str):
            bad_state.append('流 ' + show(stream) + ' 报错：' + got)
        else:
            bad_state.append('流 ' + show(stream) + ' 打出 ' + show(got) + '，期望 ' + show(want))
    if not bad_state:
        checks.append((True, '探针：七条流上每一步的 (lo 数, lo 顶, hi 数, hi 顶) 四元组'
                             '都与判分自己按那三步维持出来的完全一致——两条不变式是实打实维持住的'))
    else:
        checks.append((False, '探针：逐步状态有 ' + str(len(bad_state)) + ' 条流不对：'
                              + show('；'.join(bad_state[:2]))
                              + '：TODO 2 的每一步都要先 heappush(lo, -v)、再把 lo 顶挪进 hi、'
                                'hi 更长就挪回来；lo 的堆顶是 -lo[0]'))

    # 判分自己复核那两条不变式（拿判分自己的状态算，不依赖学生交回的东西）
    states = model_state(PROBE_STREAM)
    ok_len, ok_top, ok_count = model_state_is_invariant(states, PROBE_STREAM)
    if ok_len and ok_top and ok_count:
        checks.append((True, '判分自己按课件那三步维持的两个堆上，两条不变式也成立'
                             '（长度差不超过一、lo 顶不大于 hi 顶）——留白版那两行 True 是'
                             '空表上「什么都没检查」的假成立，这里由判分自己给出真结论'))
    else:
        checks.append((False, '判分自己的参照实现没能维持不变式（这是判分自己的问题，请报给教练）：'
                              + show((ok_len, ok_top, ok_count))))
    return checks


# ══ 任务 4 · 手写一个最小堆 ═════════════════════════════════════════════

PROBE_TASK4 = '''
def show(v):
    return v

def ok_of(h):
    """判分自己的堆序性质检查（不用学生交回的那个，免得被学生自己的检查糊弄过去）。"""
    a = h.a
    n = len(a)
    for i in range(n):
        l, r = 2 * i + 1, 2 * i + 2
        if l < n and a[i] > a[l]:
            return False
        if r < n and a[i] > a[r]:
            return False
    return True

def asc(vals):
    h = m.MinHeap()
    for v in vals:
        h.push(v)
    return [h.pop() for _ in range(len(vals))]

def tryit(f):
    try:
        return show(f())
    except IndexError:
        return 'IndexError'
    except Exception as exc:
        return type(exc).__name__ + ': ' + str(exc)

out = {}
import heapq as _h
vals = [50, 20, 70, 10, 40, 60, 90, 30, 80, 5]
out['seq'] = asc(vals)
theirs = list(vals)
_h.heapify(theirs)
out['heapq_seq'] = [_h.heappop(theirs) for _ in range(len(theirs))]

# 1) 每推一个数：元素个数跟着长、堆序性质成立
h = m.MinHeap()
grow, okp = True, True
for i, v in enumerate(vals, 1):
    h.push(v)
    if len(h.a) != i:
        grow = False
    if not ok_of(h):
        okp = False
out['push_grow'] = grow
out['push_ok'] = okp
out['push_size'] = len(h.a)

# 2) 每弹一个数：元素个数跟着减、堆序性质成立、弹出来的是升序
seq, shrunk, okq = [], True, True
for i in range(len(vals) - 1, -1, -1):
    seq.append(tryit(h.pop))
    if len(h.a) != i:
        shrunk = False
    if not ok_of(h):
        okq = False
out['pop_seq'] = seq
out['pop_shrink'] = shrunk
out['pop_ok'] = okq
out['pop_size'] = len(h.a)

# 3) 穿插 push / pop：弹出的值必须每次都是当前最小值
h2 = m.MinHeap()
mirror = []
mix_ok, mix_len = True, 0
for v in vals:
    h2.push(v)
    mirror.append(v)
    if len(h2.a) != len(mirror) or not ok_of(h2):
        mix_ok = False
    got = tryit(h2.pop)
    want = min(mirror)
    mirror.remove(want)
    if got != want or len(h2.a) != len(mirror) or not ok_of(h2):
        mix_ok = False
out['mix_ok'] = mix_ok
out['mix_len'] = len(h2.a)

# 4) 重复值、已升序、已降序
dups = [7] * 6
out['dups'] = {k: tryit(v) for k, v in (('seq', lambda: asc(dups)),)}['seq']
ups = list(range(1, 9))
downs = list(range(8, 0, -1))
def asc_ok(vals):
    try:
        return asc(vals) == sorted(vals)
    except Exception as exc:
        return type(exc).__name__ + ': ' + str(exc)
out['ups_ok'] = asc_ok(ups)
out['downs_ok'] = asc_ok(downs)
out['downs_seq'] = tryit(lambda: asc(downs))
out['ups_seq'] = tryit(lambda: asc(ups))

# 5) 直接调 _up / _down（它们就是要写的两个动作）
h3 = m.MinHeap()
h3.a = [1, 5, 3, 9, 8, 2]        # 只有一个位置违反堆序：下标 5 的 2 应当上浮
tryit(lambda: h3._up(5))
out['up_array'] = list(h3.a)
out['up_ok'] = ok_of(h3)
out['up_top'] = h3.a[0] if h3.a else None

h4 = m.MinHeap()
h4.a = [9, 1, 2, 3, 5, 4]        # 只有根违反堆序：它该往下沉
tryit(lambda: h4._down(0))
out['down_array'] = list(h4.a)
out['down_ok'] = ok_of(h4)
out['down_top'] = h4.a[0] if h4.a else None

# 6) 边界：空堆弹出、单元素弹出、单元素 push 后顶上就是它
out['empty_pop'] = tryit(lambda: m.MinHeap().pop())
h5 = m.MinHeap()
h5.push(42)
out['one_top'] = h5.a[0] if h5.a else None
out['one_pop'] = tryit(h5.pop)
out['one_size'] = len(h5.a)

# 7) 1000 个数上（与脚本主块同一批数据的独立复核）
import random
random.seed(9)
big = [random.randrange(1000) for _ in range(1000)]
out['big_ok'] = asc_ok(big)

print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task4():
    checks = []
    run = run_script('task4_min_heap.py')
    if run['status'] != 'ok':
        return [(False, 'task4_min_heap.py 没跑通：' + run['note'])]
    out = run['out']

    random.seed(HEAP_SEED)
    vals = [random.randrange(1000) for _ in range(HEAP_N)]
    want_head = sorted(vals)[:8]

    # ── 一、与 heapq 对照弹出序列 ───────────────────────────────
    got = get_line(out, '手写堆 与 heapq 一致')
    cross = get_line(out, '手写堆弹出序列与 heapq 一致')
    if cross is None:
        checks.append((False, '没看到「手写堆弹出序列与 heapq 一致 …」这一行'))
    elif cross.startswith('True') and got == 'True':
        checks.append((True, '手写堆弹出序列与 heapq 一致 True'
                             '——1000 个随机数的弹出顺序逐项相同'))
    else:
        checks.append((False, '手写堆弹出序列与 heapq 一致 打出 ' + show(cross)
                              + '（标签行 ' + show(got) + '），期望 True：'
                                'TODO 1-4 还没写全（push 上浮、pop 下沉、_up 与 _down 的下标判断）'))
    got = get_line(out, '与原数组排序一致')
    if got is None:
        checks.append((False, '没看到「与原数组排序一致 …」这一行'))
    elif got.startswith('True'):
        checks.append((True, '与原数组排序一致 True：弹出序列就是升序'))
    else:
        checks.append((False, '与原数组排序一致 打出 ' + show(got) + '，期望 True：'
                              'TODO 1-4 都要写对——升序弹出要求 push 上浮、pop 下沉两条路都对'))
    got = parse_list(get_line(out, '手写堆 前 8 个弹出'))
    if got is None:
        checks.append((False, '没看到「手写堆 前 8 个弹出 …」这一行'))
    elif got == want_head:
        checks.append((True, '手写堆 前 8 个弹出 ' + show(got) + ' 与判分自己排序取出的前 8 小一致'))
    else:
        checks.append((False, '手写堆 前 8 个弹出 打出 ' + show(got) + '，期望 ' + show(want_head)
                              + '：判分拿的是同一种造法（random.seed(9)）造出来的那 1000 个数，'
                                '弹出来的必须是最小的八个（TODO 1-4 还没写全）'))
    for prefix, want, note in [('每推一个数之后 堆序性质都成立', 'True', '每一步之后每个结点都不大于它的两个孩子'),
                               ('每弹一个数之后 堆序性质都成立', 'True', '弹完也一样成立'),
                               ('穿插 push/pop 之后 弹出值都对', 'True', '每弹一次都要是当前最小值')]:
        got = get_line(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif got.startswith(want):
            checks.append((True, prefix + ' ' + got.split()[0] + '——' + note))
        else:
            checks.append((False, prefix + ' 打出 ' + show(got) + '，期望 True：'
                                  'TODO 1-4 里还有没写对的（先单独跑一遍 py task4_min_heap.py 看它是哪一步坏的）'))
    got = value_of(out, '01')
    if got == '50':
        checks.append((True, '计数 01 推完 50 个数之后 元素个数 50：push 真的把数放进去了'))
    elif got is None:
        checks.append((False, '没看到「计数 01 推完 50 个数之后 元素个数 …」这一行'))
    else:
        checks.append((False, '计数 01 推出 ' + show(got) + '，期望 50：TODO 1 的 push 要 append 进 self.a'))

    # ── 二、耗时：都给出来了 ───────────────────────────────────
    t_mine = time_values(out, '01')
    t_theirs = time_values(out, '02')
    for name, values, todo in [('手写堆', t_mine, 'TODO 1-4'),
                               ('heapq', t_theirs, '（这一列是给好的，不该是 0）')]:
        if not values:
            checks.append((False, '没看到「耗时 01/02 推 1000 个数 ' + name + ' n=… 秒」这一行'))
        elif any(s <= 0 for _, s in values):
            checks.append((False, '耗时 ' + name + ' 打出 0.000000：' + todo
                                  + ' 还没写出来（留白版的 push 一进去就交回，量到的只是空跑）'))
        else:
            checks.append((True, '耗时 ' + name + '：' + f'{values[-1][1]:.6f}' + ' 秒（1000 次 push）'))
    got = get_line(out, '耗时对照 手写堆比heapq慢')
    if got is None:
        checks.append((False, '没看到「耗时对照 手写堆比heapq慢 …」这一行'))
    elif not t_mine or not t_theirs or t_mine[0][1] <= 0 or t_theirs[0][1] <= 0:
        checks.append((False, '耗时 01/02 里还有 0.000000，这一行的倍数没有意义：'
                              '先把 TODO 1-4 写出来（留白版的 push 一进去就交回）'))
    else:
        try:
            ratio = float(got)
        except ValueError:
            ratio = None
        if ratio is None:
            checks.append((False, '耗时对照 手写堆比heapq慢 打出 ' + show(got) + '，读不出数字'))
        elif 0.1 <= ratio <= 100:
            checks.append((True, '耗时对照 手写堆比heapq慢 ' + got
                                 + ' 倍——同一量级（手写版每层多一次 Python 层的函数调用，'
                                   'heapq 是 C 实现，差不了一两个数量级）'))
        else:
            checks.append((False, '耗时对照 手写堆比heapq慢 打出 ' + got
                                  + ' 倍，不像是「同一量级」：先确认 push 里真的做了上浮'
                                    '（而不是只 append），再确认两边规模一样'))
    got = value_of(out, '02')
    if got is not None:
        checks.append((True, '计数 02 穿插之后 剩下元素个数 ' + got))
    else:
        checks.append((False, '没看到「计数 02 穿插之后 剩下元素个数 …」这一行'))

    # ── 三、边界 ───────────────────────────────────────────────
    got = get_line(out, '单元素弹出')
    if got is None:
        checks.append((False, '没看到「单元素弹出 …」这一行'))
    elif got.split()[:1] == ['5'] and '剩下 0' in got:
        checks.append((True, '单元素弹出 5 剩下 0：pop 里那三步的顺序写对了'
                             '（先记根、再取末尾、剩下的非空才放回去下沉）'))
    else:
        checks.append((False, '单元素弹出 打出 ' + show(got) + '，期望「5 剩下 0」：'
                              'TODO 2 的 pop 要把根记下来交回，并把末尾元素取出来'))
    got = get_line(out, '空堆弹出报错')
    err_value = get_line(out, '空堆弹出报错类型')
    if got is None:
        checks.append((False, '没看到「空堆弹出报错 …」这一行'))
    elif got.startswith('IndexError'):
        checks.append((True, '空堆弹出报错 IndexError：空堆上 pop 去取 a[0]，'
                             '报的正是这个（有些写法会报 TypeError 或干脆交回垃圾值）'))
    elif got == '没有报错':
        checks.append((False, '空堆弹出 打出「没有报错」：TODO 2 在空堆上没走到取 a[0] 那一步'
                              '——空堆应当报 IndexError: list index out of range'))
    else:
        checks.append((False, '空堆弹出报错 打出 ' + show(got) + '，期望 IndexError 开头'))
    if err_value == 'IndexError':
        checks.append((True, '空堆弹出报错类型 IndexError'))
    elif err_value is None:
        checks.append((False, '没看到「空堆弹出报错类型 …」这一行'))

    # ── 四、探针：独立复核每一步 ───────────────────────────────
    raw, err = run_probe('task4_min_heap', PROBE_TASK4)
    if raw is None:
        checks.append((False, '任务 4 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)
    probe_vals = [50, 20, 70, 10, 40, 60, 90, 30, 80, 5]
    want_seq = sorted(probe_vals)

    if data.get('seq') == want_seq and data.get('heapq_seq') == want_seq:
        checks.append((True, '探针：判分自己那 10 个数上，手写堆弹出 ' + show(data['seq'])
                             + '，与 heapq 逐项一致'))
    else:
        checks.append((False, '探针：判分自己那 10 个数上手写堆弹出 ' + show(data.get('seq'))
                              + '，期望 ' + show(want_seq) + '（heapq 那一列是 '
                              + show(data.get('heapq_seq')) + '）：TODO 1-4 还没写全'))

    for key, note, todo in [('push_grow', '每推一个数元素个数跟着长', 'TODO 1 的 push 要 append'),
                            ('push_ok', '每推一个数之后堆序性质都成立', 'TODO 3 的 _up 要一路与父结点比上去'),
                            ('pop_shrink', '每弹一个数元素个数跟着减', 'TODO 2 的 pop 要真的取走末尾'),
                            ('pop_ok', '每弹一个数之后堆序性质都成立', 'TODO 4 的 _down 要与较小的那个孩子比')]:
        if data.get(key) is True:
            checks.append((True, '探针：' + note))
        else:
            checks.append((False, '探针：' + note + ' 这一条没过（打出 ' + show(data.get(key))
                                  + '）：' + todo))
    if data.get('push_size') == len(probe_vals):
        checks.append((True, '探针：推完 10 个数之后堆里有 ' + str(data['push_size']) + ' 个元素'))
    else:
        checks.append((False, '探针：推完 10 个数之后堆里有 ' + show(data.get('push_size'))
                              + ' 个，期望 10：TODO 1 的 push 没把数放进去'))
    if data.get('pop_seq') == want_seq and data.get('pop_size') == 0:
        checks.append((True, '探针：全部弹出的顺序 ' + show(data['pop_seq']) + ' 是升序，弹空后堆里 0 个'))
    else:
        checks.append((False, '探针：全部弹出的顺序打出 ' + show(data.get('pop_seq'))
                              + '（弹空后剩 ' + show(data.get('pop_size')) + ' 个），期望 '
                              + show(want_seq) + ' 与 0 个：TODO 2 的 pop 交回的要一直是当前最小值'))
    if data.get('mix_ok') is True and data.get('mix_len') == 0:
        checks.append((True, '探针：穿插 push / pop 十次，每次都弹出当时的最小值、堆始终合法'))
    else:
        checks.append((False, '探针：穿插 push / pop 打出 mix_ok=' + show(data.get('mix_ok'))
                              + '、剩下 ' + show(data.get('mix_len')) + ' 个，期望 True 与 0：'
                                'TODO 1-4 里还有没写对的（每一项 push 之后最小值都要在顶上）'))

    if data.get('dups') == [7] * 6:
        checks.append((True, '探针：六个相同的数（全是 7）弹出 ' + show(data['dups'])
                             + '——重复值不会把堆弄坏'))
    else:
        checks.append((False, '探针：六个相同的数弹出 ' + show(data.get('dups')) + '，期望 '
                              + show([7] * 6) + '：TODO 3/4 的比较要用 <= / <，别写成互不相等才算停'))
    if data.get('ups_ok') is True and data.get('downs_ok') is True:
        checks.append((True, '探针：已经升序（1..8）与已经降序（8..1）的输入都弹成升序 '
                             + show(data.get('downs_seq'))))
    else:
        checks.append((False, '探针：升序输入 ' + show(data.get('ups_seq')) + '（对？'
                              + show(data.get('ups_ok')) + '）、降序输入 ' + show(data.get('downs_seq'))
                              + '（对？' + show(data.get('downs_ok')) + '），两份都该弹成升序：'
                                '降序输入最考验 TODO 3 的 _up（每个新元素都要一路上浮到顶）'))

    up_ok = (data.get('up_ok') is True and data.get('up_top') == 1
             and norm_state([data.get('up_array')]) == [(1, 5, 2, 9, 8, 3)])
    if up_ok:
        checks.append((True, '探针：直接调 _up(5)：[1, 5, 3, 9, 8, 2] → ' + show(data['up_array'])
                             + '，堆序性质恢复、顶上还是 1'))
    else:
        checks.append((False, '探针：直接调 _up(5) 之后数组是 ' + show(data.get('up_array'))
                              + '、顶上 ' + show(data.get('up_top'))
                              + '，期望 [1, 5, 2, 9, 8, 3] 与 1：'
                                '上浮是「与父结点比、比父结点小就换上去」'
                                '（TODO 3 里的 p = (i - 1) // 2；注意别写成 1 起编号的 i // 2）'))
    down_ok = (data.get('down_ok') is True and data.get('down_top') == 1)
    if down_ok:
        checks.append((True, '探针：直接调 _down(0)：[9, 1, 2, 3, 5, 4] → ' + show(data['down_array'])
                             + '，堆序性质恢复、顶上变成 1'))
    else:
        checks.append((False, '探针：直接调 _down(0) 之后数组是 ' + show(data.get('down_array'))
                              + '、顶上 ' + show(data.get('down_top')) + '，期望顶上变成 1 且堆合法：'
                                '下沉是「与较小的那个孩子比、比孩子大就换下去」'
                                '（TODO 4 里先比左孩子、再比右孩子）'))

    if data.get('empty_pop') == 'IndexError':
        checks.append((True, '探针：空堆上 pop 报 IndexError（判分自己接住的）'))
    else:
        checks.append((False, '探针：空堆上 pop 打出 ' + show(data.get('empty_pop'))
                              + '，期望 IndexError：TODO 2 在空堆上应当走到取 a[0] 那一步'))
    if data.get('one_top') == 42 and data.get('one_pop') == 42 and data.get('one_size') == 0:
        checks.append((True, '探针：push(42) 之后 a[0] 是 42，pop 交回 42 且堆空'))
    else:
        checks.append((False, '探针：push(42) 之后 a[0]=' + show(data.get('one_top')) + '、pop='
                              + show(data.get('one_pop')) + '、剩下 ' + show(data.get('one_size'))
                              + '，期望 42 / 42 / 0：TODO 1 的 push 要把数放进去、'
                                'TODO 2 的 pop 要把唯一的那个元素取出来（单元素时 _up 与 '
                                '_down 一次都不该走）'))
    if data.get('big_ok') is True:
        checks.append((True, '探针：判分自己造的 1000 个随机数上，弹出序列与排序一致'))
    else:
        checks.append((False, '探针：1000 个随机数上弹出序列与排序不一致（'
                              + show(data.get('big_ok')) + '）：TODO 4 的 _down 里两个孩子的'
                                '下标判断最容易在大规模上露出来'))
    return checks


# ══ 源码扫描：写法边界 ══════════════════════════════════════════════════

def scan_sources(checks):
    """扫任务 2 的源码：不许出现「排序后按下标取第 k 大」当堆版、
    也不许把 nlargest 直接当自己写的堆。"""
    path = HERE / 'task2_kth_largest.py'
    body = path.read_text(encoding='utf-8', errors='replace') if path.is_file() else ''
    try:
        tree = ast.parse(body)
    except SyntaxError as exc:
        checks.append((False, 'task2_kth_largest.py 语法有问题：' + str(exc)))
        return

    def calls_in(name):
        found = []
        for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]:
            for node in ast.walk(fn):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    found.append(node.func.id)
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and isinstance(node.func.value, ast.Name)):
                    found.append(node.func.value.id + '.' + node.func.attr)
        return found

    heap_calls = calls_in('kth_by_minheap')
    if not heap_calls:
        checks.append((False, '源码扫描：kth_by_minheap 里一个函数都没调用——TODO 2 还是占位值'
                              '（它要用 heapq.heapify / heapreplace）'))
    elif any(c.startswith('heapq.heap') or c == 'heapq.heapreplace' for c in heap_calls):
        checks.append((True, '源码扫描：kth_by_minheap 用的是 heapq 的堆操作（'
                             + show(sorted(set(heap_calls))) + '）——大小为 k 的最小堆'))
    else:
        checks.append((False, '源码扫描：kth_by_minheap 里没看到 heapq 的堆操作（只有 '
                              + show(sorted(set(heap_calls))) + '），它应当用 heapq.heapify 建堆、'
                                'heapq.heapreplace 顶掉堆顶（或 heappop + heappush）'))
    sort_calls = calls_in('topk_by_heap')
    if 'heapq.nlargest' in sort_calls or 'heapq.nsmallest' in sort_calls:
        checks.append((False, '源码扫描：topk_by_heap 直接调了 nlargest ——这一份要的是**自己**'
                              '拿大小为 k 的最小堆取出来（nlargest 那一行是给好的对照）'))
    elif 'sorted' in sort_calls:
        checks.append((False, '源码扫描：topk_by_heap 里调了 sorted ——那就又排了全序，'
                              '这一份要的是「不必排全序」的那一版'))
    else:
        checks.append((True, '源码扫描：topk_by_heap 没有偷用 sorted / nlargest'))


CHECKERS = {
    'task1_merge_fruit.py': check_task1,
    'task2_kth_largest.py': check_task2,
    'task3_running_median.py': check_task3,
    'task4_min_heap.py': check_task4,
}


def main():
    print('StudyMate lab 0018 · 自动判分（每次都要最小的那个：堆与优先队列）')
    print('目录：' + str(HERE))
    print()
    failed = []
    total_pass = 0
    total_fail = 0
    for title, filename, _ in TASKS:
        print(title + '（' + filename + '）')
        if not (HERE / filename).is_file():
            print('  FAIL  还没建这个文件：' + filename)
            print()
            failed.append(filename)
            total_fail += 1
            continue
        checks = CHECKERS[filename]()
        if filename == 'task2_kth_largest.py':
            scan_sources(checks)
        all_ok = True
        for ok, message in checks:
            print('  ' + ('PASS' if ok else 'FAIL') + '  ' + message)
            if ok:
                total_pass += 1
            else:
                all_ok = False
                total_fail += 1
        if all_ok:
            print('  → 这个任务过了')
        else:
            failed.append(filename)
        print()

    print('─' * 60)
    print(str(total_pass) + ' 条 PASS，' + str(total_fail) + ' 条 FAIL')
    print('4 个任务：' + str(4 - len(failed)) + ' 个通过，' + str(len(failed)) + ' 个还没通过')
    if failed:
        print('没过的：' + '、'.join(failed))
        print('卡住了先读 ../README.md 的「卡壳顺序」：读错误信息 → 自己跑一遍 → 看 FAIL 行 → 再对线索。')
        print('四个任务都过了，再对照 ../solutions/0018-heap-and-priority-queue/ 看参考解。')
        return 1
    print('四个任务都过了。现在去对照 ../solutions/0018-heap-and-priority-queue/：')
    print('比一比你的写法与参考解，再用一句话回答「堆为什么能在对数时间取到最小」'
          '与「为什么 k 远小于 n 时不必排全序」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
