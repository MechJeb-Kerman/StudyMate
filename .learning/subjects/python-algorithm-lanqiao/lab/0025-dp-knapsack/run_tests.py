#!/usr/bin/env python3
"""lab 0025 · 自动判分：跑四个任务脚本，读它们打印的行，另起探针 import 学生代码。

用法（在 lab/0025-dp-knapsack/ 目录里，或 solutions/0025-dp-knapsack/ 目录里）：

    py run_tests.py

判法：

  - 四个任务各起一个进程跑，只读它们打印出来的固定格式行；
  - **数据是判分自己复现的**：任务脚本把每一批随机数据（种子、条数、取数上限）
    与每一条用例都打印出来，判分按**同一个种子、同一套上限**自己造一份，
    再拿判分自己那份参照实现（二维表 / 逆序一维 / 枚举 / 逐容量递推 / 分组枚举）
    重算期望值，与学生打印的那几列逐项对照——**答案对了才算过，不是「打印了就算过」**；
  - 四个任务另外各起**探针进程** import 学生的函数，拿判分**自己造的数据**去试：
    任务 1 试二维版与逆序一维版（判分自己造 15 组）；
    任务 2 试正序错版与完全背包（判分自己造 12 组）；
    任务 3 试「恰好装满」与「全 0 初始化」两版（判分自己造 12 组）；
    任务 4 试完全背包两版与分组背包（判分自己造 10 组 + 8 组）。
    探针的数据全在判分手里，所以「判分用一套数据、脚本用另一套」这个坑不存在。

判分口径全部来自课件第 25 课：

  - **0/1 背包内层必须逆序**：正序版的答案**总是偏大**，而且**恰好等于完全背包**
    （课件实测 400 组里正序错 297 组、逆序错 0 组，那一组反例是
     重量 [6, 9, 1, 8, 4]、价值 [2, 6, 4, 12, 16]、容量 8 → 逆序 20、正序 32、枚举 20）；
  - **完全背包内层正序就是对的**：与「逐容量从小到大推」那一版处处一致（300 组 0 组不一致）；
  - **「恰好装满」靠初始化区分**：只把 dp[0] 设 0、其余全设 −inf；
    写成全 0 会让它悄悄交回「不超过」的答案（重量 3/5/7 时容量 1、2、4、6、9、11、13 无解）；
  - **分组背包的循环顺序是「组在外、容量在中逆序、组内物品在最里」**。

秒数一律不判（本机实测、会浮动）；判的都是**确定值**：价值、偏大的数额、
-inf 的格、对拍的组数、反例那一组。

退出码：0 = 四个任务都通过；1 = 还有没通过的。
"""

from __future__ import annotations

import ast
import itertools
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMEOUT = 240

TODO_RE = re.compile(r'TODO\s+(\d+)')
FILE_LINE_RE = re.compile(r'File "([^"]*)", line (\d+)')

TASKS = [
    ('任务 1 · 0/1 背包的两版写法', 'task1_knap01.py', None),
    ('任务 2 · 内层循环的方向', 'task2_direction.py', None),
    ('任务 3 · 恰好装满与不超过', 'task3_exact.py', None),
    ('任务 4 · 完全背包与分组背包', 'task4_complete_group.py', None),
]

# 打印出来的「无解」那一档的两个写法（tools.fmt 打 '-inf' 之外也认 '无解'）
INF_TOKENS = ('无解', '-inf', 'None', 'none')

# ── 行格式（与任务文件里给好的 print 行逐字对应）─────────────────────────
RE_DATA_CASE = re.compile(r'^数据 \S+ (\{.*\})$')
RE_DATA_PLAIN = re.compile(r'^数据 \S+ (\{.*\})$')
# 标签里可能带空格（「方向 容量 6」「组一 容量 5」），所以标签那一段要吃任意字符
RE_LABEL_CASE = re.compile(r'^(?P<label>.+?) 重量 (?P<ws>\[.*?\]) 价值 (?P<vs>\[.*?\]) '
                           r'容量 (?P<c>-?\d+) 结果 (?P<res>.+)$')
RE_LABEL_GROUP = re.compile(r'^(?P<label>.+?) 组 (?P<groups>\[.*\]) 容量 (?P<c>-?\d+) '
                            r'结果 (?P<res>.+)$')
RE_COUNT_PAIR = re.compile(r'^(?P<label>.+?) (?P<a>-?\d+) (?P<b>-?\d+)$')
RE_COUNT_FOUR = re.compile(r'^(?P<label>.+?) (?P<a>-?\d+) (?P<b>-?\d+) (?P<c>-?\d+) (?P<d>-?\d+)$')
RE_TWO_VALUES = re.compile(r'^(-?\d+) (-?\d+)$')
# 「偏大 偏大的容量个数 与 试过的容量个数」这种标题里带数字，值得按 True/False 读
RE_DIGIT_BOOL = re.compile(r'^(?P<label>.*?)\s+(?P<ok>True|False)\s*$')


# ══ 参照模型：判分自己的数据与口径（期望值都从这里来，不抄任务脚本）══════

def rng(seed):
    import random
    return random.Random(seed)


def model_cases(seed, trials, n_hi, w_hi, v_hi, c_hi):
    """与 tools.make_cases 逐字同一套取数次序（换了个实现，不 import 学生那边）。"""
    import random
    r = random.Random(seed)
    out = []
    for _ in range(trials):
        n = r.randint(1, n_hi)
        ws = [r.randint(1, w_hi) for _ in range(n)]
        vs = [r.randint(1, v_hi) for _ in range(n)]
        out.append((ws, vs, r.randint(1, c_hi)))
    return out


def model_groups(seed, trials, g_hi, per_hi, w_hi, v_hi, c_hi):
    import random
    r = random.Random(seed)
    out = []
    for _ in range(trials):
        g = r.randint(1, g_hi)
        groups = []
        for _ in range(g):
            k = r.randint(1, per_hi)
            groups.append([(r.randint(1, w_hi), r.randint(1, v_hi)) for _ in range(k)])
        out.append((groups, r.randint(1, c_hi)))
    return out


def m_knap01_2d(w, v, C):
    n = len(w)
    dp = [[0] * (C + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for c in range(C + 1):
            dp[i][c] = dp[i - 1][c]
            if c >= w[i - 1]:
                dp[i][c] = max(dp[i][c], dp[i - 1][c - w[i - 1]] + v[i - 1])
    return dp[n][C]


def m_knap01_1d_rev(w, v, C):
    dp = [0] * (C + 1)
    for i in range(len(w)):
        for c in range(C, w[i] - 1, -1):
            dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]


def m_knap01_1d_fwd(w, v, C):
    dp = [0] * (C + 1)
    for i in range(len(w)):
        for c in range(w[i], C + 1):
            dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]


def m_knap_complete(w, v, C):
    dp = [0] * (C + 1)
    for i in range(len(w)):
        for c in range(w[i], C + 1):
            dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]


def m_brute_complete(w, v, C):
    """逐容量从小到大推（课件那一版完全背包的参照）。"""
    dp = [0] * (C + 1)
    for c in range(1, C + 1):
        for i in range(len(w)):
            if w[i] <= c:
                dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]


def m_brute01(w, v, C):
    best = 0
    n = len(w)
    for mask in range(1 << n):
        tw = tv = 0
        for i in range(n):
            if mask >> i & 1:
                tw += w[i]
                tv += v[i]
        if tw <= C and tv > best:
            best = tv
    return best


def m_brute_group(groups, C):
    best = 0
    for pick in itertools.product(*[range(-1, len(g)) for g in groups]):
        tw = tv = 0
        for i, j in enumerate(pick):
            if j >= 0:
                tw += groups[i][j][0]
                tv += groups[i][j][1]
        if tw <= C and tv > best:
            best = tv
    return best


NEG = float('-inf')


def m_exact(w, v, C):
    """恰好装满：只把 dp[0] 设 0，其余全是 -inf，内层容量**逆序**（对的）。

    逆序这一步是必须的：正序时算 dp[c] 读到的是本轮刚填上的 dp[c - w]，
    同一件被拿了第二次——重量 3/5/7 时容量 6（3+3）、9（3+3+3）、14（7+7）
    会被算成有解，「无解」那一档就漏报了。见 m_exact_rev。

    逐格复现课件那张表的确定值：无解的是 1、2、4、6、9、11、13、14。
    """
    dp = [NEG] * (C + 1)
    dp[0] = 0
    for i in range(len(w)):
        for c in range(C, w[i] - 1, -1):
            if dp[c - w[i]] != NEG:
                dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]


def m_exact_rev(w, v, C):
    """同一个初始化、内层正序（错的那一支：同一件会被拿第二次）。"""
    dp = [NEG] * (C + 1)
    dp[0] = 0
    for i in range(len(w)):
        for c in range(w[i], C + 1):
            if dp[c - w[i]] != NEG:
                dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]


def m_exact_badinit(w, v, C):
    """「恰好装满」但初始化照「不超过」那版写成全 0（交回另一个问题的答案）。"""
    dp = [0] * (C + 1)
    for i in range(len(w)):
        for c in range(C, w[i] - 1, -1):
            dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]


def m_group(groups, C):
    dp = [0] * (C + 1)
    for g in groups:
        for c in range(C, -1, -1):
            for gw, gv in g:
                if c >= gw:
                    dp[c] = max(dp[c], dp[c - gw] + gv)
    return dp[C]


# ══ 任务的给好数据（与任务文件里那些常量逐字相同）══════════════════════

# 任务 1
T1_BAG_W, T1_BAG_V, T1_BAG_C = [2, 3, 4, 5], [3, 4, 5, 6], 8
T1_ONE_W, T1_ONE_V = [7], [9]
T1_ONE_CAPS = (6, 7, 8)
T1_SEED, T1_TRIALS, T1_LIMITS = 2025, 12, (6, 9, 20, 22)
T1_CASES = model_cases(T1_SEED, T1_TRIALS, *T1_LIMITS)
T1_PROBE = (707, 15, (6, 9, 20, 22))
T1_PROBE_CASES = model_cases(T1_PROBE[0], T1_PROBE[1], *T1_PROBE[2])

# 任务 2
T2_DIR_W, T2_DIR_V = [2, 3, 4, 5], [3, 4, 5, 6]
T2_CAPS = (6, 8, 10, 12)
T2_SEED, T2_TRIALS, T2_LIMITS = 5, 400, (8, 9, 20, 20)
T2_CASES = model_cases(T2_SEED, T2_TRIALS, *T2_LIMITS)
T2_FIND = (5, 4000, 8, 9, 20, 20)   # 与课件那一段同一个种子（第一组就是课件里那个反例）
T2_PICK_W, T2_PICK_V = [3, 5, 2, 8], [7, 11, 4, 15]
T2_PICK_CAPS = (3, 5, 8, 11, 14, 20, 33, 50)
T2_PROBE = (1011, 12, (8, 9, 20, 20))

# 任务 3
T3_EX_W, T3_EX_V = [3, 5, 7], [3, 5, 7]
T3_CAPS = tuple(range(1, 16))
T3_UNREACHABLE = (1, 2, 4, 6, 9, 11, 13, 14)
T3_EX2_W, T3_EX2_V = [4, 6], [5, 8]
T3_EX2_CAPS = (4, 6, 8, 10, 12)
T3_EX3_W, T3_EX3_V = [1, 4, 9], [2, 5, 12]
T3_EX3_CAPS = tuple(range(1, 13))
T3_SEED, T3_TRIALS, T3_LIMITS = 31, 10, (5, 8, 15, 20)
T3_CASES = model_cases(T3_SEED, T3_TRIALS, *T3_LIMITS)
T3_PROBE = (99, 12, (5, 8, 15, 20))

# 任务 4
T4_SM_W, T4_SM_V = [2, 3, 4], [3, 4, 5]
T4_SM_CAPS = (4, 6, 8, 10, 12)
T4_CG_SEED, T4_CG_TRIALS, T4_CG_LIMITS = 11, 300, (5, 8, 15, 25)
T4_CG_CASES = model_cases(T4_CG_SEED, T4_CG_TRIALS, *T4_CG_LIMITS)
T4_GRP1 = [[(2, 3), (3, 4)], [(4, 5), (5, 6)], [(1, 8)]]
T4_GRP1_CAPS = tuple(range(1, 13))
T4_GRP2 = [[(1, 4)], [(3, 7), (4, 9)], [(2, 3), (5, 10), (6, 11)]]
T4_GRP2_CAPS = tuple(range(1, 15))
T4_GRP_SEED, T4_GRP_TRIALS, T4_GRP_LIMITS = 23, 60, (3, 3, 7, 12, 18)
T4_GRP_CASES = model_groups(T4_GRP_SEED, T4_GRP_TRIALS, *T4_GRP_LIMITS)
T4_CG_PROBE = (404, 10, (5, 8, 15, 25))
T4_GRP_PROBE = (505, 8, (3, 3, 7, 12, 18))

# 课件里的两个**确定值**（第 25 课「完全背包：正序就是答案」与「小数据对拍」两节）
DIRECTION_BAD = 297          # 400 组里正序与枚举不一致的组数
COMPLETE_BAD = 0             # 300 组里完全背包两版与参照不一致的组数
FIRST_BAD_CASE = ([6, 9, 1, 8, 4], [2, 6, 4, 12, 16], 8, 20, 32)   # 重量 价值 容量 枚举 正序


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
                'note': '跑了 ' + str(timeout) + ' 秒还没结束（是不是哪里死循环了）'}
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-5:])
        return {'status': 'crash', 'out': done.stdout or '', 'err': done.stderr or '',
                'note': ('脚本报错退出（退出码 ' + str(done.returncode) + '）'
                         + todo_hint(name, done.stderr or '') + '：\n' + tail)}
    return {'status': 'ok', 'out': done.stdout or '', 'err': '', 'note': ''}


def run_probe(module, code, timeout=TIMEOUT):
    """另起一个进程 import 学生的某个任务文件，跑一小段探针代码。"""
    header = ('import json\n'
              'import sys\n'
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

def lines_of(out):
    return out.splitlines()


def get_line(out, prefix):
    for line in out.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def label_value(out, label):
    """标题为 label、后面跟一串东西的那一行 → 那一串（原样）。

    **按标签整段比**，不做前缀匹配：`例子` 不能读到 `例子 二维 与 一维逆序 10 10`
    那种另一个标题的行；`例子` 自己那一行也可能只写了标签、后面什么都没有。
    """
    for line in out.splitlines():
        if line == label:
            return ''
        if line.startswith(label + ' '):
            return line[len(label) + 1:].strip()
    return None


def label_value_exact(out, label):
    """同 label_value，但要求标签后面**正好一个**空白分隔的字段。"""
    raw = label_value(out, label)
    if raw is None:
        return None
    parts = raw.split()
    if len(parts) != 1:
        return None
    return parts[0]


def label_int(out, label):
    raw = label_value(out, label)
    if raw is None:
        return None
    parts = raw.split()
    if not parts or not re.fullmatch(r'-?\d+', parts[0]):
        return None
    return int(parts[0])


def first_tokens(out, prefix):
    """找以 `prefix` 开头的行（**整段标签**：后面只能是空白或没有），
    交回那一行里**第一个 True/False**——用来读一条判定。

    按标签整段比，别的标题里凑巧含同一段字也不会串行；
    取行里第一个 True/False 而不是最后一个词，是因为判定行后面可能还跟着说明。
    """
    for line in out.splitlines():
        if line == prefix or line.startswith(prefix + ' '):
            for token in line.split():
                if token in ('True', 'False'):
                    return token
    return None


def prefix_bool(out, prefix):
    """以 prefix 开头的那一行交回的 True/False；读不出就 None。"""
    token = first_tokens(out, prefix)
    if token in ('True', 'False'):
        return token == 'True'
    return None


def count_pair(out, label):
    """标题带「与」的那种行：`<标签> <a> <b>` → (a, b)；读不出就 None。

    取回的是**整行**（不是切掉标签之后的余下部分），因为那两个正则自己带了
    `^(?P<label>…)` 那一段。标签后面必须正好两个整数、再没有别的东西，
    所以「<标签> <个数>」那种只有一个数的行不会被误读成一对。
    """
    for line in out.splitlines():
        if line == label or line.startswith(label + ' '):
            m = RE_COUNT_PAIR.match(line)
            if m:
                return int(m.group('a')), int(m.group('b'))
            return None
    return None


def count_four(out, label):
    for line in out.splitlines():
        if line == label or line.startswith(label + ' '):
            m = RE_COUNT_FOUR.match(line)
            if m:
                return (int(m.group('a')), int(m.group('b')),
                        int(m.group('c')), int(m.group('d')))
            return None
    return None


def two_values(out, label):
    """`<标签> <a> <b>` 两个整数（原样字符串也行：None 也算一个值）。"""
    raw = label_value(out, label)
    if raw is None:
        return None
    parts = raw.split()
    if len(parts) != 2:
        return None
    return parts[0], parts[1]


def parse_data(out, label):
    """`数据 <标签> <一行 JSON>` → dict；没打到或 JSON 坏了就 None。"""
    raw = label_value(out, '数据 ' + label)
    if raw is None:
        return None
    try:
        obj = json.loads(raw)
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


def parse_int(token):
    """打印出来的一个值 → int 或 float('-inf')；读不出就 None。"""
    token = token.strip()
    if token in INF_TOKENS:
        return NEG
    if re.fullmatch(r'-?\d+', token):
        return int(token)
    try:
        return float(token)
    except ValueError:
        return None


def same_num(a, b):
    """两个值算不算同一个答案：都是 -inf（或一个 -inf 一个 None）算同一个。"""
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, float) and a == NEG:
        return (isinstance(b, float) and b == NEG) or b is None
    if isinstance(b, float) and b == NEG:
        return (isinstance(a, float) and a == NEG) or a is None
    if isinstance(a, float) or isinstance(b, float):
        return float(a) == float(b)
    return a == b


def tokens_of(res):
    return [t for t in res.split() if t != '']


def show(value, limit=90):
    text = repr(value)
    return text[:limit] + '…' if len(text) > limit else text


def verdict(checks, ok, good, bad, dep_ok=True, dep_note=''):
    """一条检查的结论：ok 为真才算数；dep_ok 是「它依赖的那几条过了吗」。

    依赖没过的时候即使 ok 为真也只写 FAIL——两个 None 相等这种事不算答案对。
    """
    if ok and dep_ok:
        checks.append((True, good))
    else:
        checks.append((False, bad + ('' if dep_ok else '（依赖的那几条还没过：' + dep_note + '）')))


def label_cases(out):
    """所有「<标签> 重量 [...] 价值 [...] 容量 N 结果 …」行 → [(标签, ws, vs, C, [值…]), …]。"""
    found = []
    for line in lines_of(out):
        m = RE_LABEL_CASE.match(line)
        if not m:
            continue
        try:
            ws = ast.literal_eval(m.group('ws'))
            vs = ast.literal_eval(m.group('vs'))
        except (ValueError, SyntaxError):
            continue
        found.append((m.group('label'), list(ws), list(vs), int(m.group('c')),
                      tokens_of(m.group('res'))))
    return found


def match_case(out, label_re):
    """按标签（正则）找回那一行 → (标签, ws, vs, C, [值…])；没有就 None。"""
    for entry in label_cases(out):
        if re.fullmatch(label_re, entry[0]):
            return entry
    return None


def label_group_cases(out):
    """所有「<标签> 组 [...] 容量 N 结果 …」行。"""
    found = []
    for line in lines_of(out):
        m = RE_LABEL_GROUP.match(line)
        if not m:
            continue
        try:
            groups = ast.literal_eval(m.group('groups'))
        except (ValueError, SyntaxError):
            continue
        found.append((m.group('label'), [list(g) for g in groups], int(m.group('c')),
                      tokens_of(m.group('res'))))
    return found


def match_group_case(out, label_re):
    for entry in label_group_cases(out):
        if re.fullmatch(label_re, entry[0]):
            return entry
    return None


def as_json_list(value):
    """把模型里的元组结构规整成 JSON 读回来那种「列表的列表」。

    脚本是 show_json 打出来的，读回来每层都是 list；判分这边的模型用的是元组。
    判分自己造的数据与脚本打印时用的数据是同源的，比的时候只看值，
    不能因为一层元组一层列表就判成「不一样」——所以两边都过这一道。
    """
    if isinstance(value, (list, tuple)):
        return [as_json_list(x) for x in value]
    return value


def data_cases(obj):
    """从「数据 …」那一行里读回这批用例，规整成 [[ws, vs, C], …]；读不出就 None。"""
    if not obj or not isinstance(obj.get('cases'), list):
        return None
    out = []
    for item in obj['cases']:
        if not isinstance(item, (list, tuple)) or len(item) != 3:
            return None
        ws, vs, cc = item
        if not isinstance(ws, list) or not isinstance(vs, list) or not isinstance(cc, int):
            return None
        out.append([[int(x) for x in ws], [int(x) for x in vs], int(cc)])
    return out


def data_group_cases(obj):
    """分组背包那批 → [[组表, 容量], …]，组表里是 [[重量, 价值], …]。"""
    if not obj or not isinstance(obj.get('cases'), list):
        return None
    out = []
    for item in obj['cases']:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return None
        groups, cc = item
        if not isinstance(groups, list) or not isinstance(cc, int):
            return None
        gs = []
        for g in groups:
            if not isinstance(g, list):
                return None
            gs.append([[int(a), int(b)] for a, b in g])
        out.append([gs, int(cc)])
    return out


def verify_batch(out, data_label, model_cases_, per_case_check, reader=None):
    """核对一批随机数据：先比数据本身，再逐组比答案。→ (checks, 全部对上了吗)"""
    checks = []
    obj = parse_data(out, data_label)
    if obj is None:
        checks.append((False, '没看到「数据 ' + data_label + ' …」这一行（带 print 的行别改、别删）'))
        return checks, False
    got_cases = (reader or data_cases)(obj)
    if got_cases is None:
        checks.append((False, '「数据 ' + data_label + '」那一行的 JSON 读不出 cases'))
        return checks, False
    if len(got_cases) != len(model_cases_):
        checks.append((False, '「数据 ' + data_label + '」里有 ' + str(len(got_cases))
                       + ' 组数据，期望 ' + str(len(model_cases_)) + ' 组'))
        return checks, False
    if got_cases != as_json_list(model_cases_):
        want_cases = as_json_list(model_cases_)
        for i, (got, want) in enumerate(zip(got_cases, want_cases), 1):
            if got != want:
                checks.append((False, '「数据 ' + data_label + '」第 ' + str(i)
                               + ' 组与判分自己按同一个种子复现出来的不一样：打出 '
                               + show(got) + '，期望 ' + show(want)
                               + '——种子与取数次序都是判分接口，别改'))
                break
        return checks, False
    all_ok = True
    bad = 0
    for i, case in enumerate(model_cases_, 1):
        row = per_case_check(i, case)
        if row is None:
            bad += 1
            if bad <= 3:
                checks.append((False, '「数据 ' + data_label + '」第 ' + str(i) + ' 组没有对应的结果行'))
            all_ok = False
    return checks, all_ok


# ══ 任务 1 · 0/1 背包的两版写法 ══════════════════════════════════════════

PROBE_TASK1 = '''
def num(x):
    if x is None:
        return 'None'
    if isinstance(x, float) and x == float('-inf'):
        return '无解'
    return x

out = {}
cases = m.CASES_DP
out['cases_replay'] = [[list(ws), list(vs), cc] for ws, vs, cc in cases]
out['on_script_cases'] = [[num(m.knap01_2d(ws, vs, cc)), num(m.knap01_1d_rev(ws, vs, cc))]
                          for ws, vs, cc in cases]

# 判分自己造的一批（种子与上限都在判分手里，学生脚本不知道）
import random
r = random.Random(707)
probe = []
for _ in range(15):
    n = r.randint(1, 6)
    ws = [r.randint(1, 9) for _ in range(n)]
    vs = [r.randint(1, 20) for _ in range(n)]
    probe.append((ws, vs, r.randint(1, 22)))
out['probe'] = [[list(ws), list(vs), cc] for ws, vs, cc in probe]
out['probe_2d'] = [num(m.knap01_2d(ws, vs, cc)) for ws, vs, cc in probe]
out['probe_1d'] = [num(m.knap01_1d_rev(ws, vs, cc)) for ws, vs, cc in probe]

# 边界：一件都没有 / 容量 0 / 一件都装不下 / 刚好装上
out['empty'] = num(m.knap01_2d([], [], 7))
out['empty_1d'] = num(m.knap01_1d_rev([], [], 7))
out['zero'] = [num(m.knap01_2d(m.BAG_W, m.BAG_V, 0)), num(m.knap01_1d_rev(m.BAG_W, m.BAG_V, 0))]
out['fit'] = [num(m.knap01_1d_rev([4], [9], 4)), num(m.knap01_1d_rev([4], [9], 3))]
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task1():
    checks = []
    run = run_script('task1_knap01.py')
    if run['status'] != 'ok':
        return [(False, 'task1_knap01.py 没跑通：' + run['note'])]
    out = run['out']

    # ── 一、第一个例子（课件那个 10）────────────────────────────
    want2, want1 = m_knap01_2d(T1_BAG_W, T1_BAG_V, T1_BAG_C), m_knap01_1d_rev(T1_BAG_W, T1_BAG_V, T1_BAG_C)
    pair = two_values(out, '例子 二维 与 一维逆序')
    if pair is None:
        checks.append((False, '没看到「例子 二维 与 一维逆序 …」这一行：带 print 的行别改、别删'))
    else:
        for got, want, which, todo in ((pair[0], want2, '二维', 'TODO 1'), (pair[1], want1, '一维逆序', 'TODO 2')):
            if parse_int(got) is not None and same_num(parse_int(got), want):
                checks.append((True, '例子 二维 与 一维逆序：' + which + ' 交回 ' + str(got)
                                     + '（判分自己算也是 ' + str(want) + '）'))
            else:
                checks.append((False, '例子 二维 与 一维逆序：' + which + ' 打出 ' + show(got)
                               + '，期望 ' + str(want) + '：' + todo
                               + '（这一组重量 ' + str(T1_BAG_W) + '、容量 ' + str(T1_BAG_C)
                               + '，答案是拿重量 3 与 5 那两件）'))
    value = prefix_bool(out, '例子 与枚举一致')
    if value is None:
        checks.append((False, '没看到「例子 与枚举一致 …」这一行'))
    elif value:
        checks.append((True, '例子 与枚举一致 True（两版都等于枚举出来的 ' + str(m_brute01(T1_BAG_W, T1_BAG_V, T1_BAG_C)) + '）'))
    else:
        checks.append((False, '例子 与枚举一致 打出 False：TODO 1 与 TODO 2 都该等于枚举出来的 '
                       + str(m_brute01(T1_BAG_W, T1_BAG_V, T1_BAG_C))))
    check_row(checks, out, '例子', T1_BAG_W, T1_BAG_V, T1_BAG_C,
              [want2, want1, m_brute01(T1_BAG_W, T1_BAG_V, T1_BAG_C)],
              'TODO 1 / TODO 2 的两版答案与枚举（' + str(m_brute01(T1_BAG_W, T1_BAG_V, T1_BAG_C)) + '）')

    # ── 二、单件物品那一档 ───────────────────────────────────────
    for cap in T1_ONE_CAPS:
        check_row(checks, out, '单件 容量 ' + str(cap), T1_ONE_W, T1_ONE_V, cap,
                  [m_knap01_2d(T1_ONE_W, T1_ONE_V, cap), m_knap01_1d_rev(T1_ONE_W, T1_ONE_V, cap),
                   m_brute01(T1_ONE_W, T1_ONE_V, cap)],
                  '容量 ' + str(cap) + ' 时装不下就交回 0、装得上就交回 9（TODO 1 / TODO 2）')

    # ── 三、对拍那一批 12 组（逐组比三个值）─────────────────────
    batch, batch_dep = verify_batch(out, '二维', T1_CASES, lambda i, case: check_row(
        checks, out, str(i), case[0], case[1], case[2],
        [m_knap01_2d(*case), m_knap01_1d_rev(*case), m_brute01(*case)],
        'TODO 1 与 TODO 2 都要给出枚举出来那个数（' + str(m_brute01(*case)) + '）'))
    checks.extend(batch)

    pair = count_pair(out, '对拍 两版一致且都给出答案的组数 与 总组数')
    if pair is None:
        checks.append((False, '没看到「对拍 两版一致且都给出答案的组数 与 总组数 …」这一行'))
    elif pair == (len(T1_CASES), len(T1_CASES)):
        checks.append((True, '对拍：' + str(pair[0]) + '/' + str(pair[1])
                             + ' 组两版都给出了答案且一致'))
    else:
        checks.append((False, '对拍 两版一致且都给出答案的组数 打出 ' + str(pair[0]) + '/' + str(pair[1])
                       + '，期望 ' + str(len(T1_CASES)) + '/' + str(len(T1_CASES))
                       + '：TODO 1 与 TODO 2 回答的是同一个问题，处处都该一致（两个都没交回不算一致）'))
    value = prefix_bool(out, '对拍 两版处处一致')
    if value is None:
        checks.append((False, '没看到「对拍 两版处处一致 …」这一行'))
    elif value:
        checks.append((True, '对拍 两版处处一致 True'))
    else:
        checks.append((False, '对拍 两版处处一致 打出 False：12 组数据上两版必须处处一致'))
    pair = count_pair(out, '对拍 两版都对上枚举的组数 与 总组数')
    if pair is None:
        checks.append((False, '没看到「对拍 两版都对上枚举的组数 与 总组数 …」这一行'))
    elif pair == (len(T1_CASES), len(T1_CASES)):
        checks.append((True, '对拍：' + str(pair[0]) + '/' + str(pair[1])
                             + ' 组两版都与枚举一致（枚举是这一课的裁判）'))
    else:
        checks.append((False, '对拍 两版都对上枚举的组数 打出 ' + str(pair[0]) + '/' + str(pair[1])
                       + '，期望 ' + str(len(T1_CASES)) + '/' + str(len(T1_CASES))
                       + '：TODO 1 的二维版与 TODO 2 的逆序版都该等于枚举出来的答案'))

    # ── 四、不变式 ──────────────────────────────────────────────
    value = prefix_bool(out, '不变式 答案在 0 与总价值之间')
    if value is None:
        checks.append((False, '没看到「不变式 答案在 0 与总价值之间 …」这一行'))
    elif value:
        checks.append((True, '不变式 答案在 0 与总价值之间 True：12 组里两版的答案都没越界'))
    else:
        checks.append((False, '不变式 答案在 0 与总价值之间 打出 False：答案不该是负数、'
                              '也不该超过「所有物品都拿」的总价值（TODO 1 / TODO 2）'))
    values = two_values(out, '不变式 容量为 0 时两版都交回 0')
    if values is None:
        checks.append((False, '没看到「不变式 容量为 0 时两版都交回 0 …」这一行'))
    elif values == ('0', '0') and zero_pair_ok(out):
        checks.append((True, '不变式：容量为 0 时两版都交回 0'))
    else:
        checks.append((False, '不变式 容量为 0 时两版打出 ' + show(list(values))
                       + '，期望 0 0：容量是 0 就一件都装不下，价值是 0'
                       + '（这一行是被 TODO 1 与 TODO 2 算出来的，不是写死的 0）'))
    value = prefix_bool(out, '不变式 容量为 0 时两版是 0')
    if value is not None:
        verdict(checks, value, '不变式 容量为 0 时两版是 0 True',
                '不变式 容量为 0 时两版是 0 打出 False：'
                'TODO 1 与 TODO 2 在容量 0 上都该交回 0')

    # ── 五、探针 ────────────────────────────────────────────────
    raw, err = run_probe('task1_knap01', PROBE_TASK1)
    if raw is None:
        checks.append((False, '任务 1 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)

    got_replay = data.get('cases_replay')
    want_replay = [[list(ws), list(vs), cc] for ws, vs, cc in T1_CASES]
    probe_answers_ok = True
    for key, func in (('probe_2d', m_knap01_2d), ('probe_1d', m_knap01_1d_rev)):
        got = data.get(key)
        if not isinstance(got, list) or len(got) != len(T1_PROBE_CASES):
            probe_answers_ok = False
            continue
        for case, token in zip(T1_PROBE_CASES, got):
            if not same_num(parse_int(str(token)), func(*case)):
                probe_answers_ok = False
    if got_replay == want_replay:
        verdict(checks, True, '探针：import 你的任务文件时读到的 CASES_DP 与判分自己'
                              '复现的 12 组逐组相同',
                '', dep_ok=probe_answers_ok,
                dep_note='探针里两版在判分自己造的数据上还没组组对上')
    else:
        checks.append((False, '探针：读到的 CASES_DP 与判分复现的不一样（第 1 组打出 '
                       + show((got_replay or [[]])[0]) + '，期望 ' + show(want_replay[0]) + '）'))

    for key, func, todo in (('probe_2d', m_knap01_2d, 'TODO 1'), ('probe_1d', m_knap01_1d_rev, 'TODO 2')):
        got = data.get(key)
        if not isinstance(got, list) or len(got) != len(T1_PROBE_CASES):
            checks.append((False, '探针：' + key + ' 交回的不是 ' + str(len(T1_PROBE_CASES))
                           + ' 个值：' + show(got)))
            continue
        bad = 0
        first = None
        for case, token in zip(T1_PROBE_CASES, got):
            want = func(*case)
            if not same_num(parse_int(str(token)), want):
                bad += 1
                if first is None:
                    first = (case, token, want)
        if bad == 0:
            checks.append((True, '探针：判分自己造的 15 组数据上，' + key + ' 组组都对'
                                 '（' + todo + ' 的写法不是只对着给好的那 12 组调出来的）'))
        else:
            case, token, want = first
            checks.append((False, '探针：' + key + ' 在判分自己造的数据上错了 ' + str(bad)
                           + '/' + str(len(T1_PROBE_CASES)) + ' 组；第一组是重量 ' + show(case[0])
                           + '、容量 ' + str(case[2]) + '，打出 ' + show(token)
                           + '，期望 ' + str(want) + '：见 ' + todo))
    if parse_int(str(data.get('empty'))) == 0 and parse_int(str(data.get('empty_1d'))) == 0:
        checks.append((True, '探针：一件物品都没有时两版都交回 0'))
    else:
        checks.append((False, '探针：一件物品都没有时打出 ' + show(data.get('empty')) + ' 与 '
                       + show(data.get('empty_1d')) + '，期望都是 0'))
    if data.get('zero') == [0, 0]:
        checks.append((True, '探针：容量 0 时两版都交回 0'))
    else:
        checks.append((False, '探针：容量 0 时打出 ' + show(data.get('zero')) + '，期望 [0, 0]'))
    if data.get('fit') == [9, 0]:
        checks.append((True, '探针：单个物品重量 4 价值 9——容量 4 交回 9、容量 3 交回 0'))
    else:
        checks.append((False, '探针：单件物品那两档打出 ' + show(data.get('fit'))
                       + '，期望 [9, 0]：刚好装上交回 9、装不下交回 0（TODO 2）'))
    return checks


def zero_pair_ok(out):
    """「容量为 0 时两版都交回 0」那一行：两版都得真的给出 0（占位值不算）。"""
    return two_values(out, '不变式 容量为 0 时两版都交回 0') == ('0', '0') \
        and prefix_bool(out, '不变式 容量为 0 时两版是 0') is True


def check_row(checks, out, label, ws, vs, C, wants, todo_note, tail=None):
    """核对一行用例：wants 是这一行该打出的那几个数值；tail 是后面另跟的说明词。

    对不上就往 checks 里写一条 FAIL，并交回 True/False。
    """
    entry = match_case(out, re.escape(label))
    if entry is None:
        checks.append((False, '没看到「' + label + ' 重量 … 价值 … 容量 … 结果 …」这一行'))
        return False
    gws, gvs, gc, toks = entry[1], entry[2], entry[3], entry[4]
    if gws != list(ws) or gvs != list(vs) or gc != C:
        checks.append((False, '「' + label + '」那一行的数据是 重量 ' + show(gws) + ' 价值 '
                       + show(gvs) + ' 容量 ' + str(gc) + '，期望 重量 ' + show(list(ws))
                       + ' 价值 ' + show(list(vs)) + ' 容量 ' + str(C)))
        return False
    want_toks = len(wants) + (1 if tail is not None else 0)
    if len(toks) != want_toks:
        checks.append((False, '「' + label + '」那一行有 ' + str(len(toks)) + ' 个结果，期望 '
                       + str(want_toks) + ' 个'))
        return False
    ok = True
    for i, (token, want) in enumerate(zip(toks, wants)):
        got = parse_int(token)
        if got is not None and same_num(got, want):
            continue
        ok = False
        checks.append((False, '「' + label + '」第 ' + str(i + 1) + ' 个结果打出 ' + show(token)
                       + '，期望 ' + (str(want) if isinstance(want, int) else '无解')
                       + '：' + todo_note))
    if tail is not None and toks[-1] != tail:
        ok = False
        checks.append((False, '「' + label + '」后面那个说明词打出 ' + show(toks[-1])
                       + '，期望 ' + show(tail) + '：' + todo_note))
    if ok:
        checks.append((True, '「' + label + '」那一行整行都对上：'
                             + ' '.join(str(w) if isinstance(w, int) else '无解' for w in wants)
                             + ('' if tail is None else ' ' + tail)))
    return ok


# ══ 任务 2 · 内层循环的方向 ══════════════════════════════════════════════

PROBE_TASK2 = '''
def num(x):
    if x is None:
        return 'None'
    if isinstance(x, float) and x == float('-inf'):
        return '无解'
    return x

out = {}
# 判分自己造的一批 0/1 数据（n 的上限与 T2_PROBE 那套 limits 的第一个数一致）
import random
r = random.Random(1011)
probe = []
for _ in range(12):
    n = r.randint(1, 8)
    ws = [r.randint(1, 9) for _ in range(n)]
    vs = [r.randint(1, 20) for _ in range(n)]
    probe.append((ws, vs, r.randint(1, 20)))
out['probe'] = [[list(ws), list(vs), cc] for ws, vs, cc in probe]
out['fwd_01'] = [num(m.knap01_1d_fwd(ws, vs, cc)) for ws, vs, cc in probe]
out['complete_01'] = [num(m.knap_complete(ws, vs, cc)) for ws, vs, cc in probe]
out['first_wrong'] = [list(x) if x is not None else None
                      for x in (m.first_wrong(ws, vs, cc) for ws, vs, cc in probe)]

# 课件那个例子（W=[2,3,4,5]、V=[3,4,5,6]）上的四行
out['dir_rows'] = [[num(m.knap01_1d_fwd(m.DIR_W, m.DIR_V, c)),
                    num(m.knap_complete(m.DIR_W, m.DIR_V, c))]
                   for c in (6, 8, 10, 12)]

# 一个装不满的容量：正序与完全背包仍然一致
out['edge'] = [num(m.knap01_1d_fwd([5], [7], 3)), num(m.knap_complete([5], [7], 3))]
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task2():
    checks = []
    run = run_script('task2_direction.py')
    if run['status'] != 'ok':
        return [(False, 'task2_direction.py 没跑通：' + run['note'])]
    out = run['out']

    # ── 一、方向那四行 ─────────────────────────────────────────
    dir_ok = True
    for cap in T2_CAPS:
        want = [m_knap01_1d_rev(T2_DIR_W, T2_DIR_V, cap), m_knap01_1d_fwd(T2_DIR_W, T2_DIR_V, cap),
                m_brute01(T2_DIR_W, T2_DIR_V, cap), m_knap_complete(T2_DIR_W, T2_DIR_V, cap)]
        got = check_row(checks, out, '方向 容量 ' + str(cap), T2_DIR_W, T2_DIR_V, cap, want,
                        '四个值依次是 逆序（对）、正序（错）、枚举（裁判）、完全背包；'
                        '容量 ' + str(cap) + ' 上正序该给 ' + str(want[1])
                        + '、枚举给 ' + str(want[2]))
        dir_ok = dir_ok and got
        for label, expect, note, todo in (
                ('方向 容量 ' + str(cap) + ' 正序等于完全背包', True,
                 '正序那一段与完全背包是同一段代码，答案处处一样', 'TODO 1 与 TODO 2'),
                ('方向 容量 ' + str(cap) + ' 正序比正确答案大', True,
                 '偏大就是铁证：同一件物品被拿了多次', 'TODO 1')):
            value = prefix_bool(out, label)
            if value is None:
                checks.append((False, '没看到「' + label + ' …」这一行'))
            else:
                verdict(checks, value == expect, label + ' ' + str(value) + '：' + note,
                        label + ' 打出 ' + str(value) + '，期望 ' + str(expect) + '：' + note
                        + '（见 ' + todo + '）',
                        dep_ok=dir_ok,
                        dep_note='这一档四个值还没对上')

    # ── 二、对拍 400 组 ────────────────────────────────────────
    batch_ok = True
    obj = parse_data(out, '方向对拍')
    if obj is None:
        checks.append((False, '没看到「数据 方向对拍 …」这一行'))
        batch_ok = False
    else:
        got_cases = data_cases(obj)
        if got_cases != [[list(ws), list(vs), cc] for ws, vs, cc in T2_CASES]:
            checks.append((False, '「数据 方向对拍」里那 400 组与判分按种子 ' + str(T2_SEED)
                           + ' 复现出来的不一样——种子与取数次序是判分接口，别改'))
            batch_ok = False
        else:
            checks.append((True, '数据 方向对拍：' + str(len(T2_CASES))
                                 + ' 组与判分自己复现的逐组相同'))
            pair = count_pair(out, '对拍 逆序与枚举不一致的组数 与 总组数')
            want_bad_rev = sum(1 for case in T2_CASES
                               if m_knap01_1d_rev(*case) != m_brute01(*case))
            if pair is None:
                checks.append((False, '没看到「对拍 逆序与枚举不一致的组数 与 总组数 …」这一行'))
            elif pair == (want_bad_rev, len(T2_CASES)):
                checks.append((True, '对拍：逆序与枚举不一致的有 ' + str(pair[0]) + '/' + str(pair[1])
                                     + ' 组（判分自己数也是 ' + str(want_bad_rev) + '）——逆序是对的'))
            else:
                checks.append((False, '对拍 逆序与枚举不一致的组数 打出 ' + str(pair[0]) + '/' + str(pair[1])
                               + '，期望 ' + str(want_bad_rev) + '/' + str(len(T2_CASES))
                               + '：逆序版不该错（它查的是还没被本轮更新的 dp[c-w]）'))
            pair = count_pair(out, '对拍 正序与枚举不一致的组数 与 总组数')
            want_bad_fwd = sum(1 for case in T2_CASES
                               if m_knap01_1d_fwd(*case) != m_brute01(*case))
            if pair is None:
                checks.append((False, '没看到「对拍 正序与枚举不一致的组数 与 总组数 …」这一行'))
            elif pair == (want_bad_fwd, len(T2_CASES)):
                checks.append((True, '对拍：正序与枚举不一致的有 ' + str(pair[0]) + '/' + str(pair[1])
                                     + ' 组（判分自己数也是 ' + str(want_bad_fwd)
                                     + '，正好是课件那个确定值）——正序错得很厉害'))
            else:
                checks.append((False, '对拍 正序与枚举不一致的组数 打出 ' + str(pair[0]) + '/' + str(pair[1])
                               + '，期望 ' + str(want_bad_fwd) + '/' + str(len(T2_CASES))
                               + '：判分按同一个种子自己数出来的（正序版偏大，'
                                 '错的那些组数就是这个值）'))
            for label, note, todo in (
                    ('对拍 不一致的那些组里正序总是偏大',
                     '偏大意味着用掉了你其实没有的资源（同一件物品被拿了多次）', 'TODO 1'),
                    ('对拍 不一致的那些组里正序都等于完全背包',
                     '两段代码一样、问题不一样，所以错的这一版恰好给出完全背包的答案', 'TODO 1 / TODO 2')):
                value = prefix_bool(out, label)
                if value is None:
                    checks.append((False, '没看到「' + label + ' …」这一行'))
                elif value:
                    checks.append((True, label + ' True：' + note))
                else:
                    checks.append((False, label + ' 打出 False，期望 True：' + note
                                   + '（见 ' + todo + '）'))
    # ── 三、揪出一组 ───────────────────────────────────────────
    obj = parse_data(out, '揪出一组')
    if obj is None:
        checks.append((False, '没看到「数据 揪出一组 …」这一行'))
    else:
        seed, trials, n_hi = obj.get('seed'), obj.get('trials'), obj.get('n_hi')
        limits = obj.get('limits')
        if (seed, trials, n_hi) != (T2_FIND[0], T2_FIND[1], T2_FIND[2]) \
                or list(limits or []) != [T2_FIND[3], T2_FIND[4], T2_FIND[5]]:
            checks.append((False, '「数据 揪出一组」写的参数是 seed=' + str(seed) + '、trials='
                           + str(trials) + '、n_hi=' + str(n_hi) + '、limits=' + show(limits)
                           + '，期望 seed=' + str(T2_FIND[0]) + '、trials=' + str(T2_FIND[1])
                           + '、n_hi=' + str(T2_FIND[2]) + '、limits=' + show(list(T2_FIND[3:]))
                           + '——这一段是判分接口，别改种子与范围'))
        else:
            checks.append((True, '数据 揪出一组：参数与判分接口一致（种子 ' + str(seed)
                                 + '、' + str(trials) + ' 组）'))
    entry = match_case(out, r'揪出')
    if entry is None:
        checks.append((False, '没看到「揪出 重量 … 价值 … 容量 … 结果 …」这一行：'
                              'TODO 1 还没写出能用的答案（正序与枚举永远相同就没得揪）'))
    else:
        ws, vs, cc, toks = entry[1], entry[2], entry[3], entry[4]
        want_ws, want_vs, want_cc, want_enum, want_fwd = FIRST_BAD_CASE
        if [ws, vs, cc] != [want_ws, want_vs, want_cc]:
            checks.append((False, '「揪出」那一组是 重量 ' + show(ws) + ' 价值 ' + show(vs)
                           + ' 容量 ' + str(cc) + '，期望重量 ' + show(want_ws) + ' 价值 '
                           + show(want_vs) + ' 容量 ' + str(want_cc)
                           + '：判分按同一个种子从头找，第一组就是它（找法：'
                             '先算正序、再算枚举、不同就收下并 break）'))
        elif [parse_int(t) for t in toks[:3]] != [want_fwd, want_enum, m_knap_complete(want_ws, want_vs, want_cc)]:
            checks.append((False, '「揪出」那一行的三个结果是 ' + show(toks[:3])
                           + '，期望 [' + str(want_fwd) + ', ' + str(want_enum) + ', '
                           + str(m_knap_complete(want_ws, want_vs, want_cc))
                           + ']（正序、枚举、完全背包）：这一组正是课件里那个反例'))
        else:
            checks.append((True, '揪出：第一组就是重量 ' + show(want_ws) + '、容量 ' + str(want_cc)
                                 + '（逆序 ' + str(want_enum) + '、正序 ' + str(want_fwd)
                                 + '、完全背包 ' + str(m_knap_complete(want_ws, want_vs, want_cc))
                                 + '）——与课件逐字一致'))

    # ── 四、偏大那一列 ─────────────────────────────────────────
    obj = parse_data(out, '偏大')
    if obj is None:
        checks.append((False, '没看到「数据 偏大 …」这一行'))
    elif list(obj.get('caps') or []) != list(T2_PICK_CAPS) \
            or [int(x) for x in (obj.get('w') or [])] != T2_PICK_W \
            or [int(x) for x in (obj.get('v') or [])] != T2_PICK_V:
        checks.append((False, '「数据 偏大」写的 caps/w/v 与判分接口不一致：' + show(obj)))
    else:
        checks.append((True, '数据 偏大：八个容量与那批物品都对上判分接口'))
    bigger = 0
    rows_ok = True
    for cap in T2_PICK_CAPS:
        want = [m_brute01(T2_PICK_W, T2_PICK_V, cap), m_knap01_1d_fwd(T2_PICK_W, T2_PICK_V, cap),
                m_knap_complete(T2_PICK_W, T2_PICK_V, cap)]
        # 说明词只有三个词：大了写「偏大」、小了写「偏小」、一样写「对得上」。
        # 正序这一版只会偏大，所以这里该出现的就是「偏大」与「对得上」两种。
        if want[1] > want[0]:
            note = '偏大'
        elif want[1] < want[0]:
            note = '偏小'
        else:
            note = '对得上'
        if want[1] > want[0]:
            bigger += 1
        rows_ok = check_row(checks, out, '偏大 容量 ' + str(cap), T2_PICK_W, T2_PICK_V, cap,
                            want, '这一行是「枚举 / 正序 / 完全背包」三个数再加一个说明词；'
                                  '容量 ' + str(cap) + ' 上正序给 ' + str(want[1])
                                  + '、枚举给 ' + str(want[0]) + '（' + note + '）',
                            tail=note) and rows_ok
        for label, expect, note2 in (
                ('偏大 容量 ' + str(cap) + ' 正序不小于正确答案', True,
                 '正序那一版只会偏大、不会偏小'),
                ('偏大 容量 ' + str(cap) + ' 对不上就是偏大', True,
                 '「对不上」与「偏大」是同一件事：偏大就是铁证')):
            value = prefix_bool(out, label)
            if value is None:
                checks.append((False, '没看到「' + label + ' …」这一行'))
            else:
                verdict(checks, value == expect, label + ' ' + str(value) + '：' + note2,
                        label + ' 打出 ' + str(value) + '，期望 ' + str(expect) + '：' + note2,
                        dep_ok=rows_ok, dep_note='这一档三个数还没对上')
    raw = label_value(out, '偏大 偏大的容量个数')
    if raw is None:
        checks.append((False, '没看到「偏大 偏大的容量个数 …」这一行'))
    elif raw.strip() == str(bigger):
        checks.append((True, '偏大：' + str(bigger) + '/' + str(len(T2_PICK_CAPS))
                             + ' 个容量上正序都比正确答案大（判分自己数也是 ' + str(bigger) + '）'))
    else:
        checks.append((False, '偏大 偏大的容量个数 打出 ' + show(raw) + '，期望 ' + str(bigger)
                       + '：同一批物品换容量，正序在能重复拿的容量上都偏大'
                         '（容量 3、5、8 上那四件刚好各拿一件，正序也就对得上）'))

    # ── 五、探针 ───────────────────────────────────────────────
    raw, err = run_probe('task2_direction', PROBE_TASK2)
    if raw is None:
        checks.append((False, '任务 2 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)
    want_probe = model_cases(T2_PROBE[0], T2_PROBE[1], *T2_PROBE[2])
    got_cases = [(tuple(ws), tuple(vs), cc) for ws, vs, cc in data.get('probe', [])]
    if got_cases != [(tuple(ws), tuple(vs), cc) for ws, vs, cc in want_probe]:
        checks.append((False, '探针：判分自己造的那批数据没读回来：' + show(data.get('probe'))))
    for key, func, todo, note in (
            ('fwd_01', m_knap01_1d_fwd, 'TODO 1', '正序（错的那一版）'),
            ('complete_01', m_knap_complete, 'TODO 2', '完全背包')):
        got = data.get(key)
        if not isinstance(got, list) or len(got) != len(want_probe):
            checks.append((False, '探针：' + key + ' 交回的不是 ' + str(len(want_probe)) + ' 个值'))
            continue
        bad = 0
        first = None
        for case, token in zip(want_probe, got):
            want = func(*case)
            if not same_num(parse_int(str(token)), want):
                bad += 1
                if first is None:
                    first = (case, token, want)
        if bad == 0:
            checks.append((True, '探针：判分自己造的 ' + str(len(want_probe)) + ' 组数据上，'
                                 + note + ' 组组都对（' + todo + '）'))
        else:
            case, token, want = first
            checks.append((False, '探针：' + note + ' 在判分自己造的数据上错了 ' + str(bad) + '/'
                           + str(len(want_probe)) + ' 组；第一组是重量 ' + show(case[0])
                           + '、容量 ' + str(case[2]) + '，打出 ' + show(token)
                           + '，期望 ' + str(want) + '：见 ' + todo))
    got = data.get('first_wrong')
    if isinstance(got, list) and len(got) == len(want_probe):
        bad = 0
        for case, item in zip(want_probe, got):
            fwd, want = m_knap01_1d_fwd(*case), m_brute01(*case)
            expect = [case[2], want, fwd] if fwd != want else None
            if item is None and expect is None:
                continue
            if item is not None and expect is not None and [int(x) for x in item] == expect:
                continue
            bad += 1
        if bad == 0:
            checks.append((True, '探针：first_wrong 在判分自己造的 ' + str(len(want_probe))
                                 + ' 组上组组都对（对不上就交回 (容量, 枚举, 正序)，'
                                   '对得上就交回 None）'))
        else:
            checks.append((False, '探针：first_wrong 有 ' + str(bad) + ' 组不对（TODO 3）：'
                           '它该交回 (容量, 枚举的答案, 正序的答案)，对得上时交回 None'))
    else:
        checks.append((False, '探针：first_wrong 交回的不是 ' + str(len(want_probe)) + ' 个值：'
                       + show(got)))
    rows = data.get('dir_rows')
    want_rows = [[m_knap01_1d_fwd(T2_DIR_W, T2_DIR_V, c), m_knap_complete(T2_DIR_W, T2_DIR_V, c)]
                 for c in (6, 8, 10, 12)]
    if rows == [[str(x) for x in row] for row in want_rows] or \
            rows == [[x for x in row] for row in want_rows]:
        checks.append((True, '探针：课件那四个容量上（6/8/10/12）正序与完全背包逐格相同：'
                             + show([r[0] for r in want_rows])))
    else:
        checks.append((False, '探针：课件那四个容量上两组值打出 ' + show(rows)
                       + '，期望 ' + show(want_rows)))
    if data.get('edge') == [0, 0]:
        checks.append((True, '探针：一件物品都装不下时正序与完全背包都是 0'))
    else:
        checks.append((False, '探针：装不下那一档打出 ' + show(data.get('edge')) + '，期望 [0, 0]'))
    return checks


# ══ 任务 3 · 恰好装满与不超过 ════════════════════════════════════════════

PROBE_TASK3 = '''
def num(x):
    if x is None:
        return 'None'
    if isinstance(x, float) and x == float('-inf'):
        return '无解'
    return x

out = {}
import random
r = random.Random(99)
probe = []
for _ in range(12):
    n = r.randint(1, 5)
    ws = [r.randint(1, 8) for _ in range(n)]
    vs = [r.randint(1, 15) for _ in range(n)]
    probe.append((ws, vs, r.randint(1, 20)))
out['probe'] = [[list(ws), list(vs), cc] for ws, vs, cc in probe]
out['exact'] = [num(m.knap01_exact(ws, vs, cc)) for ws, vs, cc in probe]
out['probe_exact'] = [num(m.probe_exact(ws, vs, cc)) for ws, vs, cc in probe]
out['rev'] = [num(m.knap01_exact_rev(ws, vs, cc)) for ws, vs, cc in probe]
out['first_short'] = [list(x) if x is not None else None
                      for x in (m.first_short(ws, vs, cc) for ws, vs, cc in probe)]
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task3():
    checks = []
    run = run_script('task3_exact.py')
    if run['status'] != 'ok':
        return [(False, 'task3_exact.py 没跑通：' + run['note'])]
    out = run['out']

    # ── 一、第一个例子：容量 1..15 ─────────────────────────────
    # 这一段的标签是「例一 容量 N」——第 6 段那批对拍用的是纯编号（1、2、…），
    # 判分按标签整段找行，两个段落的标签不能撞。
    vals_ok = True
    for cap in T3_CAPS:
        want = [m_exact(T3_EX_W, T3_EX_V, cap), m_exact_rev(T3_EX_W, T3_EX_V, cap),
                m_exact(T3_EX_W, T3_EX_V, cap), m_brute01(T3_EX_W, T3_EX_V, cap)]
        vals_ok = check_row(checks, out, '例一 容量 ' + str(cap), T3_EX_W, T3_EX_V, cap, want,
                            '四个值依次是 恰好装满、正序（错）、probe_exact、不超过；'
                            '容量 ' + str(cap) + ' 上恰好装满该是 '
                            + ('无解' if want[0] == NEG else str(want[0]))
                            + '、正序那版给 '
                            + ('无解' if want[1] == NEG else str(want[1]))
                            + '、不超过是 ' + str(want[3])) and vals_ok
    pair = count_pair(out, '例子 无解的容量个数 与 容量个数')
    want_unreach = sum(1 for c in T3_CAPS if m_exact(T3_EX_W, T3_EX_V, c) == NEG)
    if pair is None:
        checks.append((False, '没看到「例子 无解的容量个数 与 容量个数 …」这一行'))
    else:
        verdict(checks, pair == (want_unreach, len(T3_CAPS)),
                '例子：' + str(pair[0]) + '/' + str(pair[1])
                + ' 个容量凑不出来（判分自己数也是 ' + str(want_unreach)
                + '）——重量 3/5/7 凑得出的只有 3、5、7、8、10、12、15',
                '例子 无解的容量个数 打出 ' + str(pair[0]) + '/' + str(pair[1])
                + '，期望 ' + str(want_unreach) + '/' + str(len(T3_CAPS))
                + '：非法状态要设成负无穷；并且内层要**逆序**'
                  '（正序会连容量 6 = 3+3 这种都当成凑得出，个数会偏少）',
                dep_ok=vals_ok, dep_note='那 15 行四个值还没对上')
    value = prefix_bool(out, '例子 无解的容量正好是 1 2 4 6 9 11 13')
    if value is None:
        checks.append((False, '没看到「例子 无解的容量正好是 1 2 4 6 9 11 13 …」这一行'))
    else:
        verdict(checks, value,
                '例子：无解的那几个容量与课件逐字一致',
                '例子 无解的容量正好是 1 2 4 6 9 11 13 打出 False：'
                '重量 3、5、7 每一件只用一次时，凑不出的容量与课件列的那几个对不上（TODO 1）',
                dep_ok=vals_ok, dep_note='那 15 行四个值还没对上')
    value = prefix_bool(out, '例子 恰好装满不超过不超过那一问')
    if value is not None and not value:
        checks.append((False, '例子 恰好装满不超过不超过那一问 打出 False：'
                              '凑得出来时「恰好装满」的价值不会超过「不超过」的价值（TODO 1）'))
    elif value:
        checks.append((True, '例子：恰好装满的答案处处不超过不超过那一问的答案'))

    # ── 二、两种方向的差别 ─────────────────────────────────────
    want_short = sum(1 for c in T3_CAPS
                     if m_exact(T3_EX_W, T3_EX_V, c) != m_exact_rev(T3_EX_W, T3_EX_V, c))
    pair = count_pair(out, '差别 方向不同的容量个数 与 容量个数')
    if pair is None:
        checks.append((False, '没看到「差别 方向不同的容量个数 与 容量个数 …」这一行'))
    else:
        verdict(checks, pair == (want_short, len(T3_CAPS)),
                '差别：' + str(pair[0]) + '/' + str(pair[1])
                + ' 个容量上恰好装满与正序那一版给出不同答案（判分自己数也是 '
                + str(want_short) + '）',
                '差别 方向不同的容量个数 打出 ' + str(pair[0]) + '/' + str(pair[1])
                + '，期望 ' + str(want_short) + '/' + str(len(T3_CAPS))
                + '：TODO 1 逆序、TODO 2 正序，两者差在「本轮刚更新的格够不够得着」',
                dep_ok=vals_ok, dep_note='那 15 行四个值还没对上')
    for label, note, todo in (
            ('差别 正序多算的都是要重复用同一件的容量',
             '容量 6 = 3+3、9 = 3+3+3、14 = 7+7 这些格子，正序时读到的是本轮刚填上的 dp[c-w]，'
             '于是同一件被拿了第二次，被算成「凑得出」', 'TODO 1 / TODO 2'),
            ('差别 全 0 初始化的那一版给出的是不超过那一问的答案',
             '全 0 初始化把「凑不出来」当成 0 价值，交回的数正常、合法，'
             '但回答的不是你问的那个问题', '给好的 brute01，以及任选一版恰好装满')):
        value = prefix_bool(out, label)
        if value is None:
            checks.append((False, '没看到「' + label + ' …」这一行'))
        elif value:
            checks.append((True, label + ' True：' + note))
        else:
            checks.append((False, label + ' 打出 False，期望 True：' + note
                           + '（见 ' + todo + '）'))

    # ── 三、第二个例子 ─────────────────────────────────────────
    # 重量 4/6：每件只用一次时只有 4、6、10（4+6）凑得出，
    # 容量 8（要靠 4+4）与 12（要靠 4+4+4）都凑不出来——正序那一支会算成 10、16。
    ex2_ok = True
    for cap in T3_EX2_CAPS:
        ex2_ok = check_row(checks, out, '例二 容量 ' + str(cap), T3_EX2_W, T3_EX2_V, cap,
                           [m_exact(T3_EX2_W, T3_EX2_V, cap),
                            m_exact_rev(T3_EX2_W, T3_EX2_V, cap),
                            m_exact(T3_EX2_W, T3_EX2_V, cap)],
                           '容量 ' + str(cap) + ' 上恰好装满该是 '
                           + ('无解' if m_exact(T3_EX2_W, T3_EX2_V, cap) == NEG
                              else str(m_exact(T3_EX2_W, T3_EX2_V, cap)))
                           + '（正序那一支会靠 4+4 把它算成有解）') and ex2_ok

    # ── 四、第三个例子 ─────────────────────────────────────────
    # 重量 1/4/9：1..12 里 1、4、5、9、10 这些凑得出，2、3、6、7、8、11、12
    # 要同一件拿两次以上，凑不出来
    ex3_ok = True
    for cap in T3_EX3_CAPS:
        ex3_ok = check_row(checks, out, '例三 容量 ' + str(cap), T3_EX3_W, T3_EX3_V, cap,
                           [m_exact(T3_EX3_W, T3_EX3_V, cap),
                            m_exact_rev(T3_EX3_W, T3_EX3_V, cap),
                            m_exact(T3_EX3_W, T3_EX3_V, cap)],
                           '容量 ' + str(cap) + ' 上恰好装满该是 '
                           + ('无解' if m_exact(T3_EX3_W, T3_EX3_V, cap) == NEG
                              else str(m_exact(T3_EX3_W, T3_EX3_V, cap)))) and ex3_ok
    value = prefix_bool(out, '例三 每个容量都装得满')
    if value is None:
        checks.append((False, '没看到「例三 每个容量都装得满 …」这一行'))
    else:
        verdict(checks, value,
                '例三：有一件 1 重（价值 2）的物品，1..12 每个容量都装得满',
                '例三 每个容量都装得满 打出 False：'
                '重量 1 那件能把 1..12 每个容量都补齐（凑不出来那一档的原样是负无穷，'
                '别把它当成 0 或 None）（TODO 1）',
                dep_ok=ex3_ok, dep_note='例三那 12 行还没对上')

    # ── 五、对拍那一批 10 组 ───────────────────────────────────
    obj = parse_data(out, '恰好装满对拍')
    if obj is None:
        checks.append((False, '没看到「数据 恰好装满对拍 …」这一行'))
    else:
        got_cases = data_cases(obj)
        if got_cases != [[list(ws), list(vs), cc] for ws, vs, cc in T3_CASES]:
            checks.append((False, '「数据 恰好装满对拍」那 10 组与判分按种子 ' + str(T3_SEED)
                           + ' 复现出来的不一样——种子与取数次序是判分接口，别改'))
        else:
            checks.append((True, '数据 恰好装满对拍：10 组与判分自己复现的逐组相同'))
            rows_ok = True
            for i, case in enumerate(T3_CASES, 1):
                rows_ok = check_row(checks, out, str(i), case[0], case[1], case[2],
                                    [m_exact(*case), m_exact_rev(*case),
                                     m_exact(*case), m_brute01(*case)],
                                    '第 ' + str(i) + ' 组（重量 ' + show(case[0]) + '、容量 '
                                    + str(case[2]) + '）上恰好装满该是 '
                                    + ('无解' if m_exact(*case) == NEG else str(m_exact(*case)))
                                    + '、不超过是 ' + str(m_brute01(*case))
                                    + '；TODO 3 的 probe_exact 必须与 TODO 1 给出同一个值'
                                    ) and rows_ok
            pair = count_pair(out, '对拍 两版一致且都给出答案的组数 与 总组数')
            if pair is None:
                checks.append((False, '没看到「对拍 两版一致且都给出答案的组数 与 总组数 …」这一行'))
            else:
                verdict(checks, pair == (len(T3_CASES), len(T3_CASES)),
                        '对拍：' + str(pair[0]) + '/' + str(pair[1])
                        + ' 组两版都给出了答案且一致',
                        '对拍 两版一致且都给出答案的组数 打出 ' + str(pair[0]) + '/'
                        + str(pair[1]) + '，期望 ' + str(len(T3_CASES)) + '/'
                        + str(len(T3_CASES)) + '：TODO 1 与 TODO 3 是同一个问题的两遍，'
                          '处处都该一致（两个都没交回不算一致）',
                        dep_ok=rows_ok, dep_note='那 10 行还没对上')
            pair = count_pair(out, '对拍 正序多算而逆序填不上的组数 与 总组数')
            want_short_groups = sum(1 for case in T3_CASES
                                    if m_exact_rev(*case) != NEG and m_exact(*case) == NEG)
            if pair is None:
                checks.append((False, '没看到「对拍 正序多算而逆序填不上的组数 与 总组数 …」这一行'))
            else:
                verdict(checks, pair == (want_short_groups, len(T3_CASES)),
                        '对拍：正序多算、而逆序填不上的有 ' + str(pair[0]) + '/' + str(pair[1])
                        + ' 组（判分自己数也是 ' + str(want_short_groups) + '）',
                        '对拍 正序多算而逆序填不上的组数 打出 ' + str(pair[0]) + '/'
                        + str(pair[1]) + '，期望 ' + str(want_short_groups) + '/'
                        + str(len(T3_CASES)) + '：那些组正是「要重复用同一件」的容量',
                        dep_ok=rows_ok, dep_note='那 10 行还没对上')
            value = prefix_bool(out, '对拍 两版处处一致')
            if value is None:
                checks.append((False, '没看到「对拍 两版处处一致 …」这一行'))
            else:
                verdict(checks, value, '对拍 两版处处一致 True',
                        '对拍 两版处处一致 打出 False：10 组上 TODO 1 与 TODO 3 必须处处一致',
                        dep_ok=rows_ok, dep_note='那 10 行还没对上')
    four = count_four(out, '收尾 无解的组数 有解的组数 一致的组数 总组数')
    if four is None:
        checks.append((False, '没看到「收尾 无解的组数 有解的组数 一致的组数 总组数 …」这一行'))
    else:
        want_four = (sum(1 for case in T3_CASES if m_exact(*case) == NEG),
                     sum(1 for case in T3_CASES if m_exact(*case) != NEG),
                     len(T3_CASES), len(T3_CASES))
        if four == want_four:
            checks.append((True, '收尾：10 组里无解 ' + str(four[0]) + ' 组、有解 ' + str(four[1])
                                 + ' 组、两版一致 ' + str(four[2]) + ' 组'))
        else:
            checks.append((False, '收尾那一行打出 ' + show(list(four)) + '，期望 ' + show(list(want_four))
                           + '（无解 / 有解 / 一致 / 总组数）：见 TODO 1 与 TODO 3'))

    # ── 六、探针 ───────────────────────────────────────────────
    raw, err = run_probe('task3_exact', PROBE_TASK3)
    if raw is None:
        checks.append((False, '任务 3 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)
    want_probe = model_cases(T3_PROBE[0], T3_PROBE[1], *T3_PROBE[2])
    got_cases = [(tuple(ws), tuple(vs), cc) for ws, vs, cc in data.get('probe', [])]
    if got_cases != [(tuple(ws), tuple(vs), cc) for ws, vs, cc in want_probe]:
        checks.append((False, '探针：判分自己造的那批数据没读回来（判分那份是 '
                       + str(len(want_probe)) + ' 组）'))
    for key, func, todo, note in (
            ('exact', m_exact, 'TODO 1', '恰好装满（逆序 + 负无穷）'),
            ('probe_exact', m_exact, 'TODO 3', 'probe_exact'),
            ('rev', m_exact_rev, 'TODO 2', '正序那一版（故意写错的那一支）')):
        got = data.get(key)
        if not isinstance(got, list) or len(got) != len(want_probe):
            checks.append((False, '探针：' + key + ' 交回的不是 ' + str(len(want_probe)) + ' 个值'))
            continue
        bad = 0
        first = None
        for case, token in zip(want_probe, got):
            want = func(*case)
            if not same_num(parse_int(str(token)), want):
                bad += 1
                if first is None:
                    first = (case, token, want)
        if bad == 0:
            checks.append((True, '探针：判分自己造的 ' + str(len(want_probe)) + ' 组数据上，'
                                 + note + ' 组组都对（' + todo + '）'))
        else:
            case, token, want = first
            checks.append((False, '探针：' + note + ' 在判分自己造的数据上错了 ' + str(bad) + '/'
                           + str(len(want_probe)) + ' 组；第一组是重量 ' + show(case[0])
                           + '、容量 ' + str(case[2]) + '，打出 ' + show(token)
                           + '，期望 ' + (str(want) if want != NEG else '无解')
                           + '：见 ' + todo))
    got = data.get('first_short')
    if isinstance(got, list) and len(got) == len(want_probe):
        bad = 0
        for case, item in zip(want_probe, got):
            ex, fwd_wrong = m_exact(*case), m_exact_rev(*case)
            # 「无解」在这一路上有两种原样：脚本里是负无穷（json 出去变成 -Infinity），
            # 判分这边把它写成 None。两者是同一件事，用 same_num 比。
            expect = [case[2], ex, fwd_wrong] if ex != fwd_wrong else None
            if item is None and expect is None:
                continue
            if item is not None and expect is not None and len(item) == 3:
                if int(item[0]) == expect[0] \
                        and same_num(parse_int(str(item[1])), expect[1]) \
                        and same_num(parse_int(str(item[2])), expect[2]):
                    continue
            bad += 1
        if bad == 0:
            checks.append((True, '探针：first_short 在判分自己造的 ' + str(len(want_probe))
                                 + ' 组上组组都对（不同就交回 (容量, 恰好装满, 正序)，一样交回 None；'
                                   '「无解」写成负无穷或 None 都认）'))
        else:
            checks.append((False, '探针：first_short 有 ' + str(bad) + ' 组不对（TODO 4）：'
                           '它该交回 (容量, 正序的答案, 逆序的答案)，一样时交回 None'))
    else:
        checks.append((False, '探针：first_short 交回的不是 ' + str(len(want_probe)) + ' 个值：'
                       + show(got)))
    return checks


PROBE_TASK4 = '''
def num(x):
    if x is None:
        return 'None'
    if isinstance(x, float) and x == float('-inf'):
        return '无解'
    return x

out = {}
import random
r = random.Random(404)
cg = []
for _ in range(10):
    n = r.randint(1, 5)
    ws = [r.randint(1, 8) for _ in range(n)]
    vs = [r.randint(1, 15) for _ in range(n)]
    cg.append((ws, vs, r.randint(1, 25)))
out['cg'] = [[list(ws), list(vs), cc] for ws, vs, cc in cg]
out['cg_item_outer'] = [num(m.knap_complete2(ws, vs, cc)) for ws, vs, cc in cg]
out['cg_cap_outer'] = [num(m.knap_complete_cap(ws, vs, cc)) for ws, vs, cc in cg]

r2 = random.Random(505)
grp = []
for _ in range(8):
    g = r2.randint(1, 3)
    groups = []
    for _ in range(g):
        k = r2.randint(1, 3)
        groups.append([(r2.randint(1, 7), r2.randint(1, 12)) for _ in range(k)])
    grp.append((groups, r2.randint(1, 18)))
out['grp'] = [[[list(p) for p in groups], cc] for groups, cc in grp]
out['grp_ans'] = [num(m.knap_group(groups, cc)) for groups, cc in grp]

# 边界：只有一组 / 一件物品比容量还重 / 空组表
out['one_group'] = num(m.knap_group([[(2, 5), (3, 9)]], 3))
out['too_heavy'] = num(m.knap_group([[(9, 9)], [(8, 8)]], 5))
out['empty_groups'] = num(m.knap_group([], 7))
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task4():
    checks = []
    run = run_script('task4_complete_group.py')
    if run['status'] != 'ok':
        return [(False, 'task4_complete_group.py 没跑通：' + run['note'])]
    out = run['out']

    # ── 一、小例子 ─────────────────────────────────────────────
    small_ok = True
    for cap in T4_SM_CAPS:
        want = [m_knap_complete(T4_SM_W, T4_SM_V, cap), m_brute_complete(T4_SM_W, T4_SM_V, cap),
                m_brute01(T4_SM_W, T4_SM_V, cap), m_brute_complete(T4_SM_W, T4_SM_V, cap)]
        got = check_row(checks, out, '小例 容量 ' + str(cap), T4_SM_W, T4_SM_V, cap, want,
                        '四个值依次是 物品在外那版、课件那版、0/1 枚举、逐容量参照；容量 '
                        + str(cap) + ' 上完全背包该给 ' + str(want[0])
                        + '、0/1 背包只给 ' + str(want[2]))
        small_ok = small_ok and got
    for cap in T4_SM_CAPS:
        value = prefix_bool(out, '小例 容量 ' + str(cap) + ' 两版一致')
        if value is None:
            checks.append((False, '没看到「小例 容量 ' + str(cap) + ' 两版一致 …」这一行'))
        else:
            verdict(checks, value,
                    '小例 容量 ' + str(cap) + ' 两版一致 True',
                    '小例 容量 ' + str(cap) + ' 两版一致 打出 False：'
                    'TODO 1 与 TODO 2 是同一个问题的两种循环次序，答案必须一样',
                    dep_ok=small_ok, dep_note='这一档四个值还没对上')

    # ── 二、完全背包对拍 300 组 ────────────────────────────────
    obj = parse_data(out, '完全背包对拍')
    if obj is None:
        checks.append((False, '没看到「数据 完全背包对拍 …」这一行'))
    else:
        got_cases = data_cases(obj)
        if got_cases != [[list(ws), list(vs), cc] for ws, vs, cc in T4_CG_CASES]:
            checks.append((False, '「数据 完全背包对拍」那 300 组与判分按种子 ' + str(T4_CG_SEED)
                           + ' 复现出来的不一样——种子与取数次序是判分接口，别改'))
        else:
            checks.append((True, '数据 完全背包对拍：300 组与判分自己复现的逐组相同'))
            bad_a = bad_b = 0
            first_bad = None
            for i, case in enumerate(T4_CG_CASES, 1):
                row = match_case(out, re.escape(str(i)))
                want = [m_knap_complete(*case), m_brute_complete(*case),
                        m_brute_complete(*case), m_brute01(*case)]
                if row is None:
                    continue
                toks = row[4]
                if len(toks) != 4:
                    continue
                got_a, got_b = parse_int(toks[0]), parse_int(toks[1])
                if not same_num(got_a, want[0]):
                    bad_a += 1
                    if first_bad is None:
                        first_bad = (i, case, toks[0], want[0])
                if not same_num(got_b, want[1]):
                    bad_b += 1
            for label, want_count, which, todo in (
                    ('对拍 物品在外那版对不上参照的组数 与 总组数', bad_a,
                     '物品在外那版（TODO 1）', 'TODO 1'),
                    ('对拍 课件那版对不上参照的组数 与 总组数', bad_b,
                     '课件那一版（TODO 2）', 'TODO 2')):
                pair = count_pair(out, label)
                if pair is None:
                    checks.append((False, '没看到「' + label + ' …」这一行'))
                elif pair == (want_count, len(T4_CG_CASES)):
                    checks.append((True, '对拍：' + which + ' 与参照不一致的有 ' + str(pair[0]) + '/'
                                         + str(pair[1]) + ' 组（判分自己数也是 ' + str(want_count)
                                         + '）'))
                else:
                    checks.append((False, label + ' 打出 ' + str(pair[0]) + '/' + str(pair[1])
                                   + '，期望 ' + str(want_count) + '/' + str(len(T4_CG_CASES))
                                   + '：' + which + ' 处处都该等于「逐容量从小到大推」的参照'))
            pair = count_pair(out, '对拍 完全背包两版一致的组数 与 总组数')
            if pair is None:
                checks.append((False, '没看到「对拍 完全背包两版一致的组数 与 总组数 …」这一行'))
            elif pair == (len(T4_CG_CASES), len(T4_CG_CASES)):
                checks.append((True, '对拍：两版 300/300 组一致（谁在外层不影响答案）'))
            else:
                checks.append((False, '对拍 完全背包两版一致的组数 打出 ' + str(pair[0]) + '/'
                               + str(pair[1]) + '，期望 ' + str(len(T4_CG_CASES)) + '/'
                               + str(len(T4_CG_CASES)) + '：TODO 1 与 TODO 2 是同一个问题的'
                                 '两种循环次序'))
            for label, note, todo in (
                    ('对拍 两版一致', '两种循环次序给出同一个答案', 'TODO 1 / TODO 2'),
                    ('对拍 两版都等于参照实现', '两版都要等于「逐容量从小到大推」那一版',
                     'TODO 1 / TODO 2'),
                    ('对拍 完全背包答案都不小于 0/1 背包',
                     '可选的方案多了（允许重复拿），最大值只会更大或不变', 'TODO 1 / TODO 2')):
                value = prefix_bool(out, label)
                if value is None:
                    checks.append((False, '没看到「' + label + ' …」这一行'))
                elif value:
                    checks.append((True, label + ' True：' + note))
                else:
                    checks.append((False, label + ' 打出 False，期望 True：' + note
                                   + '（见 ' + todo + '）'))

    # ── 三、分组背包例一 ───────────────────────────────────────
    for cap in T4_GRP1_CAPS:
        entry = match_group_case(out, re.escape('组一 容量 ' + str(cap)))
        want = m_brute_group(T4_GRP1, cap)
        if entry is None:
            checks.append((False, '没看到「组一 容量 ' + str(cap) + ' 组 … 容量 … 结果 …」这一行'))
            continue
        if entry[1] != [list(g) for g in T4_GRP1] or entry[2] != cap:
            checks.append((False, '「组一 容量 ' + str(cap) + '」那一行的组表或容量与判分接口不一致'))
            continue
        toks = entry[3]
        got = parse_int(toks[0]) if toks else None
        if got is not None and same_num(got, want):
            checks.append((True, '组一 容量 ' + str(cap) + '：分组背包 ' + str(got)
                                 + '，枚举也是 ' + str(want)))
        else:
            checks.append((False, '组一 容量 ' + str(cap) + ' 的答案是 ' + show(toks[:1])
                           + '，期望 ' + str(want) + '：TODO 3 的循环是「组在外、'
                             '容量在中逆序、组内物品在最里」'))
        value = prefix_bool(out, '组一 容量 ' + str(cap) + ' 与枚举一致')
        if value is None:
            checks.append((False, '没看到「组一 容量 ' + str(cap) + ' 与枚举一致 …」这一行'))
        elif not value:
            checks.append((False, '组一 容量 ' + str(cap) + ' 与枚举一致 打出 False：'
                                  '分组背包该与枚举每组取法的答案一样'))

    # ── 四、分组背包例二 ───────────────────────────────────────
    ok2 = 0
    for cap in T4_GRP2_CAPS:
        entry = match_group_case(out, re.escape('组二 容量 ' + str(cap)))
        want = m_brute_group(T4_GRP2, cap)
        if entry is None:
            checks.append((False, '没看到「组二 容量 ' + str(cap) + ' …」这一行'))
            continue
        toks = entry[3]
        got = parse_int(toks[0]) if toks else None
        if got is not None and same_num(got, want):
            ok2 += 1
    pair = count_pair(out, '组二 与枚举一致的容量个数 与 容量个数')
    if pair is None:
        checks.append((False, '没看到「组二 与枚举一致的容量个数 与 容量个数 …」这一行'))
    elif pair == (len(T4_GRP2_CAPS), len(T4_GRP2_CAPS)) and ok2 == len(T4_GRP2_CAPS):
        checks.append((True, '组二：1..14 每个容量上都与枚举一致（组里件数不齐也一样）'))
    else:
        checks.append((False, '组二 与枚举一致的容量个数 打出 ' + str(pair[0]) + '/' + str(pair[1])
                       + '（判分自己在打印出来的行里数出 ' + str(ok2) + ' 个），期望 '
                       + str(len(T4_GRP2_CAPS)) + '/' + str(len(T4_GRP2_CAPS))
                       + '：见 TODO 3'))

    # ── 五、分组背包对拍 60 组 ─────────────────────────────────
    obj = parse_data(out, '分组背包对拍')
    if obj is None:
        checks.append((False, '没看到「数据 分组背包对拍 …」这一行'))
    else:
        got_cases = data_group_cases(obj)
        if got_cases != as_json_list(T4_GRP_CASES):
            checks.append((False, '「数据 分组背包对拍」那 60 组与判分按种子 ' + str(T4_GRP_SEED)
                           + ' 复现出来的不一样——种子与取数次序是判分接口，别改'))
        else:
            bad = 0
            first_bad = None
            for i, (groups, cc) in enumerate(T4_GRP_CASES, 1):
                entry = match_group_case(out, re.escape(str(i)))
                want = m_brute_group(groups, cc)
                if entry is None or not entry[3]:
                    bad += 1
                    if first_bad is None:
                        first_bad = (i, groups, cc, None, want)
                    continue
                got = parse_int(entry[3][0])
                if not same_num(got, want):
                    bad += 1
                    if first_bad is None:
                        first_bad = (i, groups, cc, entry[3][0], want)
            pair = count_pair(out, '对拍 分组背包与枚举一致的组数 与 总组数')
            if pair is None:
                checks.append((False, '没看到「对拍 分组背包与枚举一致的组数 与 总组数 …」这一行'))
            else:
                want_agree = len(T4_GRP_CASES) - bad
                if pair == (len(T4_GRP_CASES), len(T4_GRP_CASES)) and bad == 0:
                    checks.append((True, '对拍：分组背包 60/60 组与枚举一致'))
                else:
                    checks.append((False, '对拍 分组背包与枚举一致的组数 打出 ' + str(pair[0]) + '/'
                                   + str(pair[1]) + '（判分自己在打印出来的行里数出 ' + str(want_agree)
                                   + ' 组一致），期望 ' + str(len(T4_GRP_CASES)) + '/'
                                   + str(len(T4_GRP_CASES)) + '：见 TODO 3'
                                   + ('' if first_bad is None else
                                      '；第一组不一致的是第 ' + str(first_bad[0]) + ' 组，容量 '
                                      + str(first_bad[2]) + '，打出 ' + show(first_bad[3])
                                      + '、期望 ' + str(first_bad[4]))))
            value = prefix_bool(out, '对拍 分组背包处处与枚举一致')
            if value is not None and not value:
                checks.append((False, '对拍 分组背包处处与枚举一致 打出 False：'
                                      '60 组都该与枚举一致（TODO 3）'))

    # ── 六、探针 ───────────────────────────────────────────────
    raw, err = run_probe('task4_complete_group', PROBE_TASK4)
    if raw is None:
        checks.append((False, '任务 4 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)
    want_cg = model_cases(T4_CG_PROBE[0], T4_CG_PROBE[1], *T4_CG_PROBE[2])
    for key, func, todo, note in (
            ('cg_item_outer', m_knap_complete, 'TODO 1', '完全背包 · 物品在外那版'),
            ('cg_cap_outer', m_brute_complete, 'TODO 2', '完全背包 · 课件那版')):
        got = data.get(key)
        if not isinstance(got, list) or len(got) != len(want_cg):
            checks.append((False, '探针：' + key + ' 交回的不是 ' + str(len(want_cg)) + ' 个值'))
            continue
        bad = 0
        first = None
        for case, token in zip(want_cg, got):
            want = func(*case)
            if not same_num(parse_int(str(token)), want):
                bad += 1
                if first is None:
                    first = (case, token, want)
        if bad == 0:
            checks.append((True, '探针：判分自己造的 ' + str(len(want_cg)) + ' 组数据上，'
                                 + note + ' 组组都对（' + todo + '）'))
        else:
            case, token, want = first
            checks.append((False, '探针：' + note + ' 在判分自己造的数据上错了 ' + str(bad) + '/'
                           + str(len(want_cg)) + ' 组；第一组是重量 ' + show(case[0])
                           + '、容量 ' + str(case[2]) + '，打出 ' + show(token)
                           + '，期望 ' + str(want) + '：见 ' + todo))
    want_grp = model_groups(T4_GRP_PROBE[0], T4_GRP_PROBE[1], *T4_GRP_PROBE[2])
    got = data.get('grp_ans')
    if not isinstance(got, list) or len(got) != len(want_grp):
        checks.append((False, '探针：分组背包交回的不是 ' + str(len(want_grp)) + ' 个值'))
    else:
        bad = 0
        first = None
        for (groups, cc), token in zip(want_grp, got):
            want = m_brute_group(groups, cc)
            if not same_num(parse_int(str(token)), want):
                bad += 1
                if first is None:
                    first = (groups, cc, token, want)
        if bad == 0:
            checks.append((True, '探针：判分自己造的 ' + str(len(want_grp)) + ' 组分组数据上，'
                                 '分组背包组组都对（TODO 3）'))
        else:
            groups, cc, token, want = first
            checks.append((False, '探针：分组背包在判分自己造的数据上错了 ' + str(bad) + '/'
                           + str(len(want_grp)) + ' 组；第一组是 ' + show(groups) + ' 容量 '
                           + str(cc) + '，打出 ' + show(token) + '，期望 ' + str(want)
                           + '：见 TODO 3'))
    for key, want, note in (('one_group', 9, '只有一组时，容量 3 装得下 (2,5) 或 (3,9)，取大的 9'),
                            ('too_heavy', 0, '每件都比容量重时交回 0'),
                            ('empty_groups', 0, '一组都没有时交回 0')):
        got = parse_int(str(data.get(key)))
        if got is not None and same_num(got, want):
            checks.append((True, '探针：' + note))
        else:
            checks.append((False, '探针：' + note + '，但打出 ' + show(data.get(key))
                           + '，期望 ' + str(want)))
    return checks


# ══ 空模板识别：让每一条 FAIL 都点名是哪个 TODO 没写 ═════════════════════

# 空模板里这些函数体还是 `return None`。判分**不 cache、不猜**：
# 起一次探针，看这些函数交回来的值是不是清一色的 None，是就认定「这一段还没写」。
STUB_FUNCS = {
    'task1_knap01.py': (('knap01_2d', 'TODO 1'), ('knap01_1d_rev', 'TODO 2')),
    'task2_direction.py': (('knap01_1d_fwd', 'TODO 1'), ('knap_complete', 'TODO 2'),
                           ('first_wrong', 'TODO 3')),
    'task3_exact.py': (('knap01_exact', 'TODO 1'), ('knap01_exact_rev', 'TODO 2'),
                       ('probe_exact', 'TODO 3'), ('first_short', 'TODO 4')),
    'task4_complete_group.py': (('knap_complete2', 'TODO 1'), ('knap_complete_cap', 'TODO 2'),
                                ('knap_group', 'TODO 3')),
}

STUB_PROBE = '''
import json
import random
out = {}
r = random.Random(20250101)
probe = []
for _ in range(6):
    n = r.randint(1, 4)
    probe.append(([r.randint(1, 6) for _ in range(n)],
                  [r.randint(1, 9) for _ in range(n)], r.randint(1, 12)))
out['cases'] = [[list(a), list(b), c] for a, b, c in probe]
# 分组背包那一段的参数是 (组表, 容量)，别的都是 (重量表, 价值表, 容量)
groups = [[[(1, 1)], [(2, 2)]] for _ in probe]
res = {}
for name in __STUB_FUNCS__:
    vals = []
    for i, (a, b, c) in enumerate(probe):
        fn = getattr(m, name, None)
        if fn is None:
            vals.append('__missing__')
            continue
        try:
            vals.append(fn(groups[i], c) if name == 'knap_group' else fn(a, b, c))
        except Exception:
            vals.append('__raised__')
    res[name] = vals
out['res'] = res
print('PROBE ' + json.dumps(out, ensure_ascii=False, default=str))
'''


def detect_stubs(task_name):
    """空模板里哪几段还是 `return None` → ['TODO 1', …]（判分自己起探针看的）。"""
    pairs = STUB_FUNCS.get(task_name)
    if not pairs:
        return []
    names = [n for n, _ in pairs]
    probe = STUB_PROBE.replace('__STUB_FUNCS__', repr(names))
    raw, _err = run_probe(task_name[:-3], probe)
    if raw is None:
        return []
    try:
        res = json.loads(raw).get('res') or {}
    except ValueError:
        return []
    missing = []
    for name, todo in pairs:
        vals = res.get(name)
        if not isinstance(vals, list) or not vals:
            continue
        # 空模板的占位实现交回负无穷（tools.NEG，json 出去是 '-Infinity'）或 None；
        # 两者都算「这一段还没写」。
        hit = True
        for v in vals:
            if v is None or v == 'None':
                continue
            try:
                if float(v) == float('-inf'):
                    continue
            except (TypeError, ValueError):
                pass
            hit = False
        if hit:
            missing.append(todo)
    return missing


def tag_missing(checks, missing):
    """一段都没写时，把「没写」这件事补进每一条还没点名的 FAIL 里。"""
    if not missing:
        return checks
    names = '、'.join(missing)
    out = []
    for ok, note in checks:
        if not ok and 'TODO' not in note:
            note = note + '（这一条要 ' + names + ' 写出来才可能过：那一段还是占位的）'
        out.append((ok, note))
    return out


# ══ 主流程 ═══════════════════════════════════════════════════════════════

CHECKERS = {
    'task1_knap01.py': check_task1,
    'task2_direction.py': check_task2,
    'task3_exact.py': check_task3,
    'task4_complete_group.py': check_task4,
}


def main():
    total = passed = 0
    failed_tasks = []
    for title, name, _ in TASKS:
        print('=' * 72)
        print(title + '（' + name + '）')
        print('=' * 72)
        checks = CHECKERS[name]()
        checks = tag_missing(checks, detect_stubs(name))
        ok_here = sum(1 for ok, _ in checks if ok)
        total += len(checks)
        passed += ok_here
        for ok, note in checks:
            print(('PASS ' if ok else 'FAIL ') + note)
        print('-- ' + title + '：' + str(ok_here) + ' PASS / '
              + str(len(checks) - ok_here) + ' FAIL')
        if ok_here != len(checks):
            failed_tasks.append(name)
        print()
    print('=' * 72)
    print('总共 ' + str(passed) + ' PASS / ' + str(total - passed) + ' FAIL')
    if failed_tasks:
        print('还差这几个任务：' + '、'.join(failed_tasks))
        return 1
    print('四个任务全过。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
