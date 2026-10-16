#!/usr/bin/env python3
"""lab 0026 · 自动判分：跑四个任务脚本，读它们打印的行，另起探针 import 学生代码。

用法（在 lab/0026-dp-sequence-interval/ 目录里）：

    py run_tests.py

判法：
  - 四个任务各起一个进程跑，只读它们打印出来的固定格式行，不 import 学生代码；
  - 期望值不是抄来的：判分自己另有一份参照实现，把同一道口径重算一遍再与学生打印的
    行逐字对照——LIS 的长度/tails/恢复出的子序列、LCS 的整张状态表、最长回文子序列的
    长度、石子合并的最小总代价（含**长度从大到小**那一版的错答案）；
  - 四个任务各另起**探针进程** import 学生的函数，拿判分自己造的数据去试：
    任务 1 在判分自己造的 200+200 组随机数据上核两版长度与「恢复出的序列是原序列的
    合法子序列且严格递增且长度等于 LIS 长度」；任务 2 核每一格的整张表；
    任务 3 与判分自己的暴力版对拍；任务 4 在判分自己的数据上核从小到大、并核
    「从大到小给的是偏小的错答案」。
  - 判分**看趋势不看常数**：秒数每次运行都会浮动（课件自己也写了第二次跑就不一样），
    所以耗时那一列只要求「二分版每一档都比 DP 版快」「规模翻四倍时 DP 版涨得更多」
    「二分版在最大一档更快」，以及几处 25% 噪声带内的比较，绝不核对具体秒数。

断言里的口径来自课件正文：LIS 的答案是 max(dp) 而不是 dp[n-1]；tails[k] 是「所有长度
为 k+1 的递增子序列里结尾最小的值」，**它本身不是一条递增子序列**（实测 [2, 3, 7, 18]
对 [2, 5, 7, 101]）；严格递增用 bisect_left；LCS 的第一行第一列全是 0、每一格只依赖
左/上/左上；区间 DP 按区间长度从小到大枚举；石子合并的转移枚举断点、末尾加区间和；
长度从大到小枚举时短区间还没算过、代价被漏掉，答案**偏小**。

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
VALUE_RE = re.compile(r'^-?\d+$')

TASKS = [
    ('任务 1 · LIS 两版与「那条子序列本身」（DP 版 / 二分版 / 从 dp 回溯）',
     'task1_lis.py', None),
    ('任务 2 · 最长公共子序列：把状态表打印出来（第一行第一列全是 0）',
     'task2_lcs.py', None),
    ('任务 3 · 最长回文子序列：区间 DP，必须先算短区间', 'task3_palindrome.py', None),
    ('任务 4 · 石子合并：断点枚举，以及长度枚举写反的后果', 'task4_stone.py', None),
]

# ── 与任务文件里的常量对齐（判分靠它们造出**同一批**数据）──────────────────
A_COURSE = [10, 9, 2, 5, 3, 7, 101, 18]        # 课件那组数据
DUP_COURSE = [5, 5, 5, 5]                      # 全相同元素
LIS_TRIALS = 500
LIS_SEED_A = 11                                # 脚本第四节：两版长度对拍
LIS_SEED_B = 12                                # 脚本第五节：恢复出的序列
LIS_SEED_C = 13                                # 脚本第六节：耗时那批
LIS_SIZES = (400, 800, 1600)

LCS_S1, LCS_S2 = 'ABCBDAB', 'BDCABA'
LCS_CASES = (('AGGTAB', 'GXTXAYB'), ('abcde', 'ace'), ('aaa', 'aa'),
             ('', 'ABC'), ('XYZ', 'PQR'))

LPS_CASES = ('character', 'abba', 'abcda', 'aaaa')
LPS_TRIALS = 200
LPS_SEED_A = 7                                 # 脚本第四节：与暴力对拍
LPS_SEED_B = 8                                 # 脚本第五节：耗时那串
LPS_SIZES = (100, 200, 400)
PAL_SHORT = ('a', 'ab', 'aa', 'abc', 'aab', 'racecar', 'abcba')

STONE_CASES = ([4, 1, 2, 3], [3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6])
STONE_TRIALS = 200
STONE_SEED_A = 9                               # 脚本第四节：与暴力对拍（课件就是 seed(9)）
STONE_SIZES = (60, 120, 240)

# ── 判分**自己**造数据用的种子（与脚本那几批刻意不同，是独立证据）──────────
JUDGE_LIS_SEED = 1011                          # 任务 1 探针：两版长度
JUDGE_LIS_REC_SEED = 2027                      # 任务 1 探针：恢复出的子序列
JUDGE_PAL_SEED = 3031                          # 任务 3 探针：与暴力对拍
JUDGE_STONE_SEED = 4099                        # 任务 4 探针：与暴力对拍
JUDGE_TRIALS = 200                             # 探针那几批的组数


# ══ 参照模型：判分自己的口径（期望值都从这里来，不抄）══════════════════════

def model_lis_dp(a):
    """LIS 的 O(n^2) 版：交回 (最长长度, dp 数组)。"""
    n = len(a)
    if n == 0:
        return 0, []
    dp = [1] * n
    for i in range(1, n):
        for j in range(i):
            if a[j] < a[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
    return max(dp), dp


def model_lis_bisect(a):
    """LIS 的二分版：交回 (长度, tails 数组)。严格递增用 bisect_left。"""
    import bisect
    tails = []
    for x in a:
        k = bisect.bisect_left(tails, x)
        if k == len(tails):
            tails.append(x)
        else:
            tails[k] = x
    return len(tails), tails


def model_lis_sequence(a):
    """判分自己从 dp 加 prev 回溯出一条真正的最长递增子序列。"""
    n = len(a)
    if n == 0:
        return []
    dp = [1] * n
    prev = [-1] * n
    for i in range(1, n):
        for j in range(i):
            if a[j] < a[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j
    best = max(range(n), key=lambda i: dp[i])
    out = []
    while best != -1:
        out.append(a[best])
        best = prev[best]
    return out[::-1]


def model_is_subsequence(seq, a):
    """判分自己判「seq 是不是 a 的子序列」（贪心匹配）。"""
    pos = 0
    for x in a:
        if pos < len(seq) and seq[pos] == x:
            pos += 1
    return pos == len(seq)


def model_lcs(s, t):
    """LCS：交回 (长度, 整张状态表)。"""
    n, m = len(s), len(t)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m], dp


def model_edge_zeros(table):
    """判分自己数「第一行 + 第一列」上的 0（左上角只数一次）。"""
    if not table:
        return 0
    first_row = table[0]
    first_col = [row[0] for row in table]
    return (sum(1 for v in first_row if v == 0) + sum(1 for v in first_col if v == 0)
            - (1 if first_row and first_col and first_row[0] == 0 else 0))


def model_lps(s):
    """最长回文子序列：区间 DP，长度从小到大。"""
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1
    for length in range(2, n + 1):
        for i in range(0, n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]


def model_lps_brute(s):
    """判分自己的暴力版：枚举全部子序列，取最长的回文。"""
    seqs = ['']
    for ch in s:
        seqs = seqs + [x + ch for x in seqs]
    best = 0
    for x in seqs:
        if x == x[::-1] and len(x) > best:
            best = len(x)
    return best


def model_stone(a, order='asc'):
    """石子合并：区间 DP。order='desc' 是**故意写反**的那一版。"""
    n = len(a)
    if n < 2:
        return 0
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] + a[i]
    dp = [[0] * n for _ in range(n)]
    big = float('inf')
    lengths = range(2, n + 1) if order == 'asc' else range(n, 1, -1)
    for length in lengths:
        for i in range(0, n - length + 1):
            j = i + length - 1
            best = big
            for k in range(i, j):
                cand = dp[i][k] + dp[k + 1][j]
                if cand < best:
                    best = cand
            dp[i][j] = best + pre[j + 1] - pre[i]
    return dp[0][n - 1]


def model_stone_brute(a):
    """判分自己的暴力版：递归枚举每一次合并的是相邻哪两堆。"""
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def go(t):
        if len(t) == 1:
            return 0
        best = float('inf')
        for k in range(len(t) - 1):
            cost = t[k] + t[k + 1]
            nxt = t[:k] + (cost,) + t[k + 2:]
            best = min(best, cost + go(nxt))
        return best

    return go(tuple(a))


# ── 判分自己造的几批数据（探针用；与脚本那几批不是同一批）────────────────

def judge_lis_data(seed, trials, max_n=40, hi=30):
    """判分自己的 LIS 数据：[随机长度 0~max_n、元素 1~hi] 的 trials 组。"""
    random.seed(seed)
    return [[random.randint(1, hi) for _ in range(random.randint(0, max_n))]
            for _ in range(trials)]


def judge_pal_data(seed, trials):
    """判分自己的回文数据：随机长度 0~12、字母表 'abc'。"""
    random.seed(seed)
    return [''.join(random.choice('abc') for _ in range(random.randint(0, 12)))
            for _ in range(trials)]


def judge_stone_data(seed, trials):
    """判分自己的石子数据：随机 1~7 堆、每堆 1~20。"""
    random.seed(seed)
    return [[random.randint(1, 20) for _ in range(random.randint(1, 7))]
            for _ in range(trials)]


LIS_POOL = judge_lis_data(JUDGE_LIS_SEED, JUDGE_TRIALS)                   # 核两版长度
LIS_REC_POOL = judge_lis_data(JUDGE_LIS_REC_SEED, JUDGE_TRIALS, max_n=30)  # 核回溯出的序列
PAL_POOL = (['', 'z', 'zz', 'zy', 'aaaaaaaa'] + list(PAL_SHORT)
            + judge_pal_data(JUDGE_PAL_SEED, JUDGE_TRIALS))
STONE_POOL = ([[7], [3, 5], [5, 5, 5, 5], [9, 9, 9], [1, 2], [1, 2, 3]]
              + [list(c) for c in STONE_CASES]
              + judge_stone_data(JUDGE_STONE_SEED, 100))


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


def count_by_label(lines, label):
    """按**标签**取 `计数 NN 标签 值` 那一行的值——判分读的是学生脚本自己打印的行。

    比按编号取安全得多：编号只是行号，标签才是那一行在说什么。标签里的
    `n=` / `k=` 这类后缀（例如 `第k大 k=10`）算作标签的一部分。
    值的形状一定是「整数」或 `True/False`：从后往前找到第一个这样的段。
    """
    if isinstance(lines, str):
        lines = lines.splitlines()
    for entry in lines:
        if not entry.startswith('计数 '):
            continue
        body = entry[len('计数 '):].strip()
        head = body.split(None, 1)
        if len(head) < 2 or head[1] != label and not head[1].startswith(label + ' '):
            continue
        for piece in reversed(head[1].split()):
            if VALUE_RE.match(piece) or piece in ('True', 'False'):
                return piece
    return None


def counted(out, label, want, note, todo):
    """一条「计数 NN 标签 值」的断言：读标签、与 want 比，并给出指名的失败理由。"""
    got = count_by_label(out, label)
    if got is None:
        return (False, '没看到「计数 … ' + label + ' …」这一行：'
                       '带 show_count 的那几行是判分接口，别改、别删')
    if got == want:
        return (True, '计数 ' + label + ' ' + note + '：' + got)
    return (False, '计数 ' + label + ' 打出 ' + show(got) + '，期望 ' + want + '：' + todo)


def label_value(out, label):
    """取 `标签 值` 那一行里剩下的内容；没有这一行交回 None。"""
    return get_line(out, label + ' ')


def label_bool(out, label):
    """取 `标签 True/False` 那一行，交回 True / False / None。"""
    value = label_value(out, label)
    if value is None:
        return None
    head = value.split()
    if not head:
        return None
    if head[0] == 'True':
        return True
    if head[0] == 'False':
        return False
    return None


def time_values(out, index):
    """取 `耗时 NN 标签 n=… 0.000000 秒` 里的 (规模, 秒数)；同一编号可能有多行。"""
    values = []
    for entry in get_lines(out, '耗时 ' + index + ' '):
        parts = entry.split()
        if len(parts) < 2 or parts[-1] != '秒':
            continue
        try:
            seconds = float(parts[-2])
        except ValueError:
            continue
        m = re.search(r'n=(\d+)', entry)
        values.append((int(m.group(1)) if m else None, seconds))
    return values


def parse_list(text):
    """把 "['D', 'E']" / "[1, 2]" / "[(1, 7, 0)]" 解析成列表；解析不了交回 None。"""
    if text is None:
        return None
    try:
        value = ast.literal_eval(text.strip())
    except (ValueError, SyntaxError):
        return None
    return value if isinstance(value, list) else None


def parse_ints(text):
    """把 "[0, 1, 2]" 解析成整数列表；解析不了交回 None。"""
    value = parse_list(text)
    if value is None:
        return None
    return value if all(isinstance(v, int) for v in value) else None


def to_lists(value):
    """元组经 json.dumps 会变成列表；比较前统一转成 list（这是判分自己的锅）。"""
    if isinstance(value, tuple):
        return [to_lists(v) for v in value]
    if isinstance(value, list):
        return [to_lists(v) for v in value]
    return value


def show(value, limit=110):
    text = repr(value)
    return text[:limit] + '…' if len(text) > limit else text


def tbl(seq):
    """把 [(n, 秒数), …] 只留秒数。"""
    return [s for _, s in seq]


def table_rows(out):
    """把脚本打印出来的整张 dp 表读成二维整数列表。

    表体那几行的形状是固定的三种：
        '     ""  B  D  C  A  B  A'              表头：t 的字符，认出 '""' 这一格
        '     "   0   0   0   0   0   0   0'     第 0 行（全 0）
        '     A   0   0   0   0   1   1   1'     第 i 行，第一个词是 s[i-1]
    只认「第一个词是引号那两格、或单个字符，且后面全是整数」的行——
    表体下面那些凑巧也全是数字的输出行不会被误认（第一格不是单字符）。
    """
    rows = []
    started = False
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        tag = parts[0]
        if not (tag in ('"', "''", '""') or len(tag) == 1):
            if started:
                break
            continue
        if not all(VALUE_RE.match(p) for p in parts[1:]):
            if started:
                break
            continue
        rows.append([int(p) for p in parts[1:]])
        started = True
    return rows


# ══ 任务 1 · LIS 两版与「那条子序列本身」════════════════════════════════

PROBE_TASK1 = '''
import random

def call(f, *args):
    try:
        return f(*args)
    except Exception as exc:
        return type(exc).__name__ + ': ' + str(exc)

# 必须与判分器的两批数据同一造法（同 seed、同 randint 范围），
# 否则探针算的是另一批数，期望值永远对不上。
random.seed(1011)
POOL = [[random.randint(1, 30) for _ in range(random.randint(0, 40))] for _ in range(200)]
random.seed(2027)
REC = [[random.randint(1, 30) for _ in range(random.randint(0, 30))] for _ in range(200)]

out = {}
out['len'] = [[call(m.lis_dp, list(a)), call(m.lis_bisect, list(a))] for a in POOL]
out['rec'] = [call(m.lis_recover, list(a)) for a in REC]
out['fixed'] = {
    'course_dp': call(m.lis_dp, [10, 9, 2, 5, 3, 7, 101, 18]),
    'course_bi': call(m.lis_bisect, [10, 9, 2, 5, 3, 7, 101, 18]),
    'course_rec': call(m.lis_recover, [10, 9, 2, 5, 3, 7, 101, 18]),
    'dup_dp': call(m.lis_dp, [5, 5, 5, 5]),
    'dup_bi': call(m.lis_bisect, [5, 5, 5, 5]),
    'dup_rec': call(m.lis_recover, [5, 5, 5, 5]),
    'empty_dp': call(m.lis_dp, []),
    'empty_bi': call(m.lis_bisect, []),
    'empty_rec': call(m.lis_recover, []),
    'one_rec': call(m.lis_recover, [7]),
    'dec_dp': call(m.lis_dp, [9, 8, 7, 6]),
    'inc_dp': call(m.lis_dp, [1, 2, 3, 4, 5]),
}
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task1():
    checks = []
    run = run_script('task1_lis.py')
    if run['status'] != 'ok':
        return [(False, 'task1_lis.py 没跑通：' + run['note'])]
    out = run['out']

    want_len, want_dp = model_lis_dp(A_COURSE)
    _, want_tails = model_lis_bisect(A_COURSE)
    want_rec = model_lis_sequence(A_COURSE)

    # ── 一、课件那组数据：长度、tails、恢复出的子序列 ──────────────
    checks.append(counted(out, 'LIS 长度', str(want_len),
                          '两版长度都该是 4', 'TODO 1 的 lis_dp 还没写对'))
    checks.append(counted(out, '恢复出的长度', str(len(want_rec)),
                          '恢复出的也是 4 个', 'TODO 3 的 lis_recover 还没写对'))

    got = parse_ints(label_value(out, 'tails 数组'))
    if got is None:
        checks.append((False, '没看到「tails 数组 […]」这一行'))
    elif got == want_tails:
        checks.append((True, 'tails 数组 ' + show(got) + ' 与判分自己按「长度 k+1 的最小结尾」'
                             '维护出来的逐项一致——**它不是一条递增子序列**，只是记账数组'))
    else:
        checks.append((False, 'tails 数组 打出 ' + show(got) + '，期望 ' + show(want_tails)
                              + '：看 TODO 2 的 lis_bisect（严格递增要用 bisect_left，'
                                '遇到相等的值替换、不追加）'))

    got = parse_ints(label_value(out, '恢复出的子序列'))
    if got is None:
        checks.append((False, '没看到「恢复出的子序列 […]」这一行'))
    elif (got == want_rec and model_is_subsequence(got, A_COURSE)
          and all(got[i] < got[i + 1] for i in range(len(got) - 1))):
        checks.append((True, '恢复出的子序列 ' + show(got)
                             + '：是原序列的子序列、严格递增、长度 ' + str(len(got))
                             + ' 等于 LIS 长度（判分自己回溯出的也是这条）'))
    else:
        checks.append((False, '恢复出的子序列 打出 ' + show(got) + '，期望 ' + show(want_rec)
                              + '（判分自己回溯出来的那条）：看 TODO 3 的 lis_recover——'
                                '转移时要把 prev[i] = j 记下来，再从 max(dp) 那个下标一路回溯'))

    for prefix, want, todo in [
            ('LIS 两版长度一致', True, 'TODO 1 与 TODO 2 都要写出来'),
            ('tails 与恢复出的子序列相同吗', False,
             '这一行期望 False：tails 与真正的那条子序列元素完全对不上——'
             'TODO 3 的 lis_recover 还没写、它交回跟 tails 一样的空表时这一行才会打出 True'),
            ('恢复出的就是判分要的那一条', True,
             '要交的是从 dp 加 prev 回溯出来的那条（这里就是 [2, 5, 7, 101]）；'
             '打出 False 多半是 TODO 3 还没写（或者把 tails 交回来了）'),
            ('恢复出的是原序列的子序列吗', True, 'TODO 3 要真的从原序列里挑'),
            ('恢复出的严格递增', True, 'TODO 3 回溯出来的序列必须严格递增'),
            ('恢复出的长度等于 LIS 长度', True, 'TODO 1 与 TODO 3 的长度要对上')]:
        got = label_bool(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' True/False」这一行'))
        elif got is want:
            checks.append((True, prefix + ' ' + str(got) + '（期望值）'))
        else:
            checks.append((False, prefix + ' 打出 ' + str(got) + '，期望 ' + str(want)
                                  + '：' + todo))

    # ── 二、全相同元素 ───────────────────────────────────────────
    got = label_value(out, '全相同元素 两版长度')
    if got is None:
        checks.append((False, '没看到「全相同元素 两版长度 1 1」这一行'))
    elif got.split()[:2] == ['1', '1']:
        checks.append((True, '全相同元素 [5, 5, 5, 5] 两版长度 1 1'
                             '——严格递增，相等的接不上（bisect_left 是替换不是追加）'))
    else:
        checks.append((False, '全相同元素 两版长度 打出 ' + show(got) + '，期望 1 1：'
                              'TODO 2 要是 bisect_left；用 bisect_right 会得到 4'))
    for prefix, want, todo in [
            ('全相同元素 长度都是1', True, 'TODO 1 的 lis_dp 与 TODO 2 的 lis_bisect 在重复值上都要给 1'),
            ('空序列 两版都是0', True, 'TODO 1 与 TODO 2 在空序列上都要直接交回 0'),
            ('空序列 恢复出空表', True, 'TODO 3 的 lis_recover 在空序列上要交回空表'),
            ('单个元素 长度1', True, 'TODO 1 的 lis_dp 在 [7] 上要交回长度 1'),
            ('单个元素 恢复出它自己', True, 'TODO 3 的 lis_recover 在 [7] 上要交回 [7]'),
            ('严格递减 长度1', True, 'TODO 1 的 lis_dp 在 [9, 8, 7, 6] 上要交回 1（每个元素都接不上别人）'),
            ('严格递增 全长', True, 'TODO 1 的 lis_dp 在 [1, 2, 3, 4, 5] 上要交回 5')]:
        got = label_bool(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif got is want:
            checks.append((True, prefix + ' ' + str(got) + '（期望值）'))
        else:
            checks.append((False, prefix + ' 打出 ' + str(got) + '，期望 ' + str(want)
                                  + '：' + todo))
    checks.append(counted(out, '全相同元素 两版都给', '1',
                          '两版在 [5, 5, 5, 5] 上给同一个长度',
                          '两版在 [5, 5, 5, 5] 上给的不是同一个长度（这一行刻意写成了 -1）：'
                          'TODO 2 要用 bisect_left，用 bisect_right 会得到 4'))

    # ── 三、500 组随机数据：判分自己复算一遍 ─────────────────────
    for prefix, want, todo in [
            ('随机对拍 组数', str(LIS_TRIALS), '这一行是给好的，别删'),
            ('随机对拍 两版长度不一致组数', '0',
             'TODO 1 与 TODO 2 在 500 组（长度 0~40、元素 1~30）上必须给出同一个长度')]:
        got = label_value(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif got == want:
            checks.append((True, prefix + ' ' + got))
        else:
            checks.append((False, prefix + ' 打出 ' + show(got) + '，期望 ' + want + '：' + todo))
    checks.append(counted(out, '随机对拍 不一致组数', '0',
                          '500 组上两版长度从不打架',
                          '两版长度从不出错——混用出的错一定出在「你问的是长度还是序列」'))

    # 判分自己按同一种造法造 500 组、用自己的参照实现算一遍，再核对那两行
    bad_model = 0
    random.seed(LIS_SEED_A)
    for _ in range(LIS_TRIALS):
        n = random.randint(0, 40)
        row = [random.randint(1, 30) for _ in range(n)]
        if model_lis_dp(row)[0] != model_lis_bisect(row)[0]:
            bad_model += 1
    printed = label_value(out, '随机对拍 两版长度不一致组数')
    if bad_model == 0 and printed == '0':
        checks.append((True, '判分自己按同一造法（random.seed(' + str(LIS_SEED_A)
                             + ')、randint(1, 30)、长度 0~40）造 500 组、用自己的两版实现算出'
                             '不一致 ' + str(bad_model) + ' 组——脚本那一行的 0 对得上'))
    else:
        checks.append((False, '判分自己按同一种造法造出来的 500 组上不一致 ' + str(bad_model)
                              + ' 组、脚本打印的是 ' + show(printed)
                              + '：先怀疑判分器的造法与脚本不一致（那是判分自己的锅），'
                                '再怀疑 TODO 1/2'))

    # ── 四、恢复出的那条子序列：判分另造一批自查 ────────────────
    for prefix, want, todo in [
            ('恢复出的 不是子序列的组数', '0', 'TODO 3 交回的必须真是原序列的子序列'),
            ('恢复出的 不是严格递增的组数', '0', 'TODO 3 交回的必须严格递增'),
            ('恢复出的 长度不对的组数', '0', 'TODO 3 的长度要等于 TODO 1 的 LIS 长度'),
            ('恢复出的一条都没错', 'True', '上三条都是 0 时这一行才是 True')]:
        got = label_value(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif got == want:
            checks.append((True, prefix + ' ' + got))
        else:
            checks.append((False, prefix + ' 打出 ' + show(got) + '，期望 ' + want + '：' + todo))

    # ── 五、耗时趋势 ─────────────────────────────────────────────
    t_dp = time_values(out, '01')
    t_bi = time_values(out, '02')
    for name, values, todo in [('DP 版', t_dp, 'TODO 1 的 lis_dp'),
                               ('二分版', t_bi, 'TODO 2 的 lis_bisect')]:
        if not values:
            checks.append((False, '没看到「耗时 01/02 LIS ' + name + ' n=… 秒」这一行：'
                                  '带 print 的行别改、别删'))
        elif [n for n, _ in values] != list(LIS_SIZES):
            checks.append((False, name + ' 读到的规模是 ' + show([n for n, _ in values])
                                  + '，期望 ' + show(list(LIS_SIZES)) + '：三档规模都要量一次'))
        elif any(s <= 0 for _, s in values):
            checks.append((False, name + ' 有三行的秒数是 0.000000：' + todo
                                  + ' 还没写出来（留白版三行都是 0）'))
        else:
            checks.append((True, name + '：三档耗时都量到了（'
                                  + ' / '.join(f'{s:.6f}' for _, s in values) + ' 秒）'))
    ds, bs = tbl(t_dp), tbl(t_bi)
    if len(ds) == 3 and len(bs) == 3 and all(s > 0 for s in ds + bs):
        ratio = ds[-1] / max(bs[-1], 1e-9)
        if ratio > 1.0:
            checks.append((True, '最大一档（n=1600）上二分版比 DP 版快 ' + f'{ratio:.2f}'
                                 + ' 倍——O(n log n) 对 O(n^2)'))
        else:
            checks.append((False, '最大一档上二分版只比 DP 版快 ' + f'{ratio:.2f}'
                                  + ' 倍，期望明显更快：TODO 2 要真的用 bisect 维护 tails'
                                    '（别在里面套一层 O(n) 的扫描）'))
        d_grow = ds[-1] / ds[0]
        b_grow = bs[-1] / max(bs[0], 1e-9)
        if d_grow > b_grow * 0.75:
            checks.append((True, '规模翻四倍（400→1600）：DP 版涨 ' + f'{d_grow:.2f}'
                                 + ' 倍、二分版涨 ' + f'{b_grow:.2f}'
                                 + ' 倍——DP 版该涨得更凶（平方级对线性对数级，'
                                   '两个倍数靠得近时允许 25% 的计时噪声）'))
        else:
            checks.append((False, '规模翻四倍：DP 版涨 ' + f'{d_grow:.2f}' + ' 倍、二分版涨 '
                                  + f'{b_grow:.2f}' + ' 倍，期望 DP 版涨得更多：'
                                    '两个 TODO 是不是互换了？DP 版是双重循环、'
                                    '二分版每步只做一次 bisect'))
    else:
        checks.append((False, '耗时那两列的秒数不全（有 0.000000），趋势这一条先看不了：'
                              '先把 TODO 1、TODO 2 写出来'))
    for prefix, todo in [('二分版每一档都更快', 'TODO 1 的 lis_dp 与 TODO 2 的 lis_bisect 都还没写，'
                                               '两边的秒数都是 0.000000，比不出快慢'),
                         ('规模翻四倍时 DP 版涨得更多', 'TODO 1 与 TODO 2 都还没写，'
                                                       '两边的秒数都不随规模增长')]:
        got = label_bool(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' True/False」这一行'))
        elif got is True:
            checks.append((True, prefix + ' True'))
        else:
            checks.append((False, prefix + ' 打出 ' + str(got) + '，期望 True：' + todo))
    if len(ds) == 3 and len(bs) == 3 and all(s > 0 for s in ds + bs):
        checks.append(counted(out, '二分版在最大一档更快', 'True',
                              '最大一档上二分版更快', 'TODO 2 还没写对'))
    else:
        checks.append((False, '计数 二分版在最大一档更快 这一条先看不了：两边的秒数里有 '
                              '0.000000（TODO 1、TODO 2 还没写出来），0 跟 0 比不出快慢。'
                              '先把它写出来再回来看这条'))

    # ── 六、探针：判分自己造的两批数据 ──────────────────────────
    raw, err = run_probe('task1_lis', PROBE_TASK1)
    if raw is None:
        checks.append((False, '任务 1 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)

    bad = []
    for a, row in zip(LIS_POOL, data['len']):
        got_dp, got_bi = row[0], row[1]
        want_d, want_dp_arr = model_lis_dp(a)
        want_b, want_t = model_lis_bisect(a)
        if not (isinstance(got_dp, list) and len(got_dp) == 2 and got_dp[0] == want_d
                and to_lists(got_dp[1]) == want_dp_arr
                and isinstance(got_bi, list) and len(got_bi) == 2 and got_bi[0] == want_b
                and to_lists(got_bi[1]) == want_t):
            bad.append('a=' + show(a, 40) + ' 打出 dp ' + show(got_dp) + ' / 二分 '
                       + show(got_bi) + '，期望 (' + str(want_d) + ', ' + show(want_dp_arr)
                       + ') 与 (' + str(want_b) + ', ' + show(want_t) + ')')
    if not bad:
        checks.append((True, '探针：判分自己造的 ' + str(len(LIS_POOL)) + ' 组随机数据'
                             '（长度 0~40、元素 1~30）上，lis_dp 交回的**长度与整个 dp 数组**、'
                             'lis_bisect 交回的**长度与整个 tails 数组**都与判分自己的实现逐项一致'))
    else:
        checks.append((False, '探针有 ' + str(len(bad)) + ' 组对不上（TODO 1/2 还没写全）：'
                              + show('；'.join(bad[:2]))))

    bad_rec = []
    for a, got in zip(LIS_REC_POOL, data['rec']):
        want = model_lis_sequence(a)
        if not isinstance(got, list):
            bad_rec.append('a=' + show(a, 40) + ' 交回的不是列表：' + show(got))
            continue
        if (got != want or not model_is_subsequence(got, a)
                or (len(got) > 1 and not all(got[i] < got[i + 1] for i in range(len(got) - 1)))):
            bad_rec.append('a=' + show(a, 40) + ' 打出 ' + show(got) + '，期望 ' + show(want))
    if not bad_rec:
        checks.append((True, '探针：判分自己另造的一批随机数据上，lis_recover 交回的序列'
                             '**是原序列的子序列、严格递增、长度等于 LIS 长度**，'
                             '且与判分自己回溯出来的那条逐项相同'))
    else:
        checks.append((False, '探针有 ' + str(len(bad_rec)) + ' 组恢复出的序列不对：'
                              + show('；'.join(bad_rec[:2]))
                              + '：TODO 3 要真的回溯（prev 数组），别把 tails 交回来'))

    fixed = data.get('fixed') or {}
    want_fixed = {
        'course_dp': [want_len, want_dp],
        'course_bi': [len(want_tails), want_tails],
        'course_rec': want_rec,
        'dup_dp': [1, [1, 1, 1, 1]],
        'dup_bi': [1, [5]],
        'dup_rec': [5],
        'empty_dp': [0, []],
        'empty_bi': [0, []],
        'empty_rec': [],
        'one_rec': [7],
        'dec_dp': [1, [1, 1, 1, 1]],
        'inc_dp': [5, [1, 2, 3, 4, 5]],
    }
    bad_fixed = []
    for key, want in want_fixed.items():
        got = to_lists(fixed.get(key))
        if got != want:
            bad_fixed.append(key + ' 打出 ' + show(got) + '，期望 ' + show(want))
    if not bad_fixed:
        checks.append((True, '探针：课件那组 / 全相同 [5, 5, 5, 5] / 空序列 / 单个元素 / '
                             '严格递减 / 严格递增 六类固定输入上，三个函数的返回值都逐项正确'
                             '（全相同那组两版都是 1、tails 只剩 [5]）'))
    else:
        checks.append((False, '探针在固定输入上有 ' + str(len(bad_fixed)) + ' 处不对：'
                              + show('；'.join(bad_fixed[:3]))
                              + '：TODO 1/2/3 的边界都要看'))
    return checks


# ══ 任务 2 · 最长公共子序列 ═════════════════════════════════════════════

PROBE_TASK2 = '''
def call(f, *args):
    try:
        return f(*args)
    except Exception as exc:
        return type(exc).__name__ + ': ' + str(exc)

CASES = [('ABCBDAB', 'BDCABA'), ('AGGTAB', 'GXTXAYB'), ('abcde', 'ace'),
         ('aaa', 'aa'), ('', 'ABC'), ('XYZ', 'PQR'), ('', ''), ('a', 'a'),
         ('abcd', 'dcba'), ('aaaa', 'aa')]
out = {}
out['lcs'] = [list(call(m.lcs, s, t)) for s, t in CASES]
out['shape'] = [list(call(m.table_shape, call(m.lcs, s, t)[1], s, t)) for s, t in CASES]
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task2():
    checks = []
    run = run_script('task2_lcs.py')
    if run['status'] != 'ok':
        return [(False, 'task2_lcs.py 没跑通：' + run['note'])]
    out = run['out']

    want_len, want_table = model_lcs(LCS_S1, LCS_S2)

    checks.append(counted(out, 'LCS 长度', str(want_len), '8×7 的表右下角是 4',
                          'TODO 1 的 lcs 还没写对'))
    checks.append(counted(out, 'dp 表 行数', str(len(want_table)),
                          '= len(s) + 1', 'TODO 1 的表该建 len(s)+1 行'))
    checks.append(counted(out, 'dp 表 列数', str(len(want_table[0])),
                          '= len(t) + 1', 'TODO 1 的表该建 len(t)+1 列'))

    # ── 打印出来的整张表逐格核 ──────────────────────────────────
    got_table = table_rows(out)
    if not got_table:
        checks.append((False, '没读到打印出来的 dp 表：TODO 1 交回的表还是空的'
                              '（那几行 print 是分表头与表体两段打的，别删）'))
    elif got_table == want_table:
        checks.append((True, '打印出来的整张 ' + str(len(want_table)) + '×'
                             + str(len(want_table[0])) + ' 状态表与判分自己算的**逐格相同**'
                             '（第一行第一列全是 0，右下角是 ' + str(want_len) + '）'))
    else:
        diff = None
        for i in range(min(len(got_table), len(want_table))):
            if got_table[i] != want_table[i]:
                diff = ('第 ' + str(i) + ' 行打出 ' + show(got_table[i]) + '，期望 '
                        + show(want_table[i]))
                break
        checks.append((False, '打印出来的状态表与判分自己算的对不上'
                              + ('：' + diff if diff else '（行数 ' + str(len(got_table))
                                 + '，期望 ' + str(len(want_table)) + '）')
                              + '：TODO 1 里 s[i-1] == t[j-1] 那一支取 dp[i-1][j-1] + 1、'
                                '另一支取 max(dp[i-1][j], dp[i][j-1])'))

    # ── 第一行第一列 ────────────────────────────────────────────
    for prefix, want, todo in [
            ('第一行', [0] * (len(LCS_S2) + 1), 'TODO 1 的表宽该是 len(t)+1，第 0 行全是 0'),
            ('第一列', [0] * (len(LCS_S1) + 1), 'TODO 1 的表高该是 len(s)+1，第 0 列全是 0')]:
        got = parse_ints(label_value(out, prefix))
        if got is None:
            checks.append((False, '没看到「' + prefix + ' […]」这一行'))
        elif got == want:
            checks.append((True, prefix + ' ' + show(got) + ' 全是 0'
                                 + '（空串配任何串，公共子序列长度都是 0）'))
        else:
            checks.append((False, prefix + ' 打出 ' + show(got) + '，期望 ' + show(want)
                                  + '：' + todo))
    got = label_bool(out, '第一行第一列 全是0')
    if got is None:
        checks.append((False, '没看到「第一行第一列 全是0 …」这一行'))
    elif got is True:
        checks.append((True, '第一行第一列 全是0 True'))
    else:
        checks.append((False, '第一行第一列 全是0 打出 ' + str(got) + '，期望 True：'
                              'TODO 1 要建 (n+1) × (m+1) 的表，多出来的那一圈就是这些 0'))
    got = label_value(out, '第一行的0个数与第一列的0个数')
    want_pair = str(len(want_table[0])) + ' ' + str(len(want_table))
    if got is None:
        checks.append((False, '没看到「第一行的0个数与第一列的0个数 …」这一行'))
    elif got.split()[:2] == want_pair.split():
        checks.append((True, '第一行的0个数与第一列的0个数 ' + got
                             + '（列数 ' + str(len(want_table[0])) + '、行数 '
                             + str(len(want_table)) + '）'))
    else:
        checks.append((False, '第一行的0个数与第一列的0个数 打出 ' + show(got) + '，期望 '
                              + want_pair + '：TODO 1 的表形状不对'))
    want_edge = str(model_edge_zeros(want_table))
    checks.append(counted(out, '两条边上的0共', want_edge,
                          '（判分自己数出来也是 ' + want_edge + '）',
                          'TODO 1 的表形状不对（第一行 + 第一列都是 0，共 '
                          + want_edge + ' 个）'))

    # ── table_shape 与右下角 ────────────────────────────────────
    got = label_value(out, '表的行数列数')
    want_rows_cols = str(len(want_table)) + ' ' + str(len(want_table[0]))
    if got is None:
        checks.append((False, '没看到「表的行数列数 …」这一行'))
    elif got.split()[:2] == want_rows_cols.split():
        checks.append((True, '表的行数列数 ' + got + '（= len(s)+1 与 len(t)+1）'))
    else:
        checks.append((False, '表的行数列数 打出 ' + show(got) + '，期望 ' + want_rows_cols
                              + '：TODO 2 的 table_shape 要交回 (行数, 列数, 边上的0个数)'))
    got = label_value(out, '两条边上的0（由 table_shape 算）')
    if got == want_edge:
        checks.append((True, '两条边上的0（由 table_shape 算）' + got
                             + '：与上面那一行独立算出来的相同'))
    elif got is None:
        checks.append((False, '没看到「两条边上的0（由 table_shape 算） …」这一行'))
    else:
        checks.append((False, '两条边上的0（由 table_shape 算）打出 ' + show(got)
                              + '，期望 ' + want_edge
                              + '：TODO 2 的第三个值 = 第一行的 0 数 + 第一列的 0 数 - 1'))
    checks.append(counted(out, '右下角', str(want_len), '= LCS 长度',
                          '答案在表的右下角——TODO 1 的 lcs 还没交回整张表（打出的 -1 是占位值）'))
    got = label_bool(out, '右下角等于长度')
    if got is None:
        checks.append((False, '没看到「右下角等于长度 …」这一行'))
    elif got is True:
        checks.append((True, '右下角等于长度 True'))
    else:
        checks.append((False, '右下角等于长度 打出 ' + str(got) + '，期望 True：'
                              'TODO 1 交回的长度该取 dp[n][m]'))

    # ── 几组小数据 ──────────────────────────────────────────────
    bad_small = []
    for left, right in LCS_CASES:
        want_v, want_tb = model_lcs(left, right)
        got_v = label_value(out, 'LCS ' + left + ' ' + right)
        got_shape = label_value(out, '表形状 ' + left + ' ' + right)
        want_shape = str((len(want_tb), len(want_tb[0])))
        if got_v is None or got_shape is None:
            bad_small.append(str((left, right)) + ' 那两行没看到')
            continue
        if got_v.split()[:1] != [str(want_v)] or got_shape != want_shape:
            bad_small.append(str((left, right)) + ' 打出 ' + show(got_v) + ' / '
                             + show(got_shape) + '，期望 ' + str(want_v) + ' / ' + want_shape)
    if not bad_small:
        checks.append((True, '五组小数据（AGGTAB/GXTXAYB、abcde/ace、aaa/aa、空串、'
                             '没有公共字符）的长度与表形状都与判分自己算的一致'))
    else:
        checks.append((False, '五组小数据里有 ' + str(len(bad_small)) + ' 组不对：'
                              + show('；'.join(bad_small[:2]))
                              + '：TODO 1 的边界（空串、重复字符）最容易错'))
    for prefix, want, todo in [
            ('空串那组是0', True, 'TODO 1 的 lcs 在空串上要交回 0（表里只剩那一行/一列的 0）'),
            ('没有公共字符那组是0', True, 'TODO 1 的 lcs 在 XYZ/PQR 上要交回 0——一个字符都不共有'),
            ('aaa 与 aa 是2', True, 'TODO 1 的 lcs 要能把重复字符配上两个，答案是 2')]:
        got = label_bool(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif got is want:
            checks.append((True, prefix + ' ' + str(got) + '（期望值）'))
        else:
            checks.append((False, prefix + ' 打出 ' + str(got) + '，期望 ' + str(want)
                                  + '：' + todo))
    for left, right in [('AGGTAB', 'GXTXAYB'), ('abcde', 'ace')]:
        want = str(model_lcs(left, right)[0])
        checks.append(counted(out, left + ' 与 ' + right, want,
                              '判分自己算的也是 ' + want, 'TODO 1 还没算对'))

    # ── 探针：判分自己那批字符串上逐格核表 ──────────────────────
    raw, err = run_probe('task2_lcs', PROBE_TASK2)
    if raw is None:
        checks.append((False, '任务 2 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)

    probe_cases = [('ABCBDAB', 'BDCABA'), ('AGGTAB', 'GXTXAYB'), ('abcde', 'ace'),
                   ('aaa', 'aa'), ('', 'ABC'), ('XYZ', 'PQR'), ('', ''), ('a', 'a'),
                   ('abcd', 'dcba'), ('aaaa', 'aa')]
    bad = []
    for (left, right), got in zip(probe_cases, data['lcs']):
        want_v, want_tb = model_lcs(left, right)
        if not (isinstance(got, list) and len(got) == 2 and got[0] == want_v
                and to_lists(got[1]) == want_tb):
            bad.append(str((left, right)) + ' 打出 ' + show(got, 60) + '，期望 ('
                       + str(want_v) + ', 整张 ' + str(len(want_tb)) + '×'
                       + str(len(want_tb[0])) + ' 表)')
    if not bad:
        checks.append((True, '探针：判分自己那 10 组字符串（含空串、单字符、倒序、重复字符）上，'
                             'lcs 交回的**长度与整张表**都与判分自己的实现逐格一致'))
    else:
        checks.append((False, '探针有 ' + str(len(bad)) + ' 组对不上：' + show('；'.join(bad[:2]))
                              + '：TODO 1 的表要连第一行第一列一起建出来'))
    bad_shape = []
    for (left, right), got in zip(probe_cases, data['shape']):
        want_v, want_tb = model_lcs(left, right)
        want = [len(want_tb), len(want_tb[0]), model_edge_zeros(want_tb)]
        if to_lists(got) != want:
            bad_shape.append(str((left, right)) + ' 打出 ' + show(got) + '，期望 ' + show(want))
    if not bad_shape:
        checks.append((True, '探针：table_shape 在那 10 组上交回的 (行数, 列数, 边上的0个数)'
                             '都与判分自己数出来的一致'))
    else:
        checks.append((False, '探针：table_shape 有 ' + str(len(bad_shape)) + ' 组不对：'
                              + show('；'.join(bad_shape[:2]))
                              + '：TODO 2 的 table_shape 在空表上要交回 (0, 0, 0)，'
                                '非空表按 len(s)+1 / len(t)+1 算'))
    return checks


# ══ 任务 3 · 最长回文子序列 ═════════════════════════════════════════════

PROBE_TASK3 = '''
def call(f, *args):
    try:
        return f(*args)
    except Exception as exc:
        return type(exc).__name__ + ': ' + str(exc)

CASES = ['', 'z', 'zz', 'zy', 'aaaaaaaa', 'a', 'ab', 'aa', 'abc', 'aab',
         'racecar', 'abcba', 'character', 'abba', 'abcda', 'aaaa']
out = {}
out['lps'] = [call(m.lps, s) for s in CASES]
out['brute'] = [call(m.lps_brute, s) for s in CASES]
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''


def check_task3():
    checks = []
    run = run_script('task3_palindrome.py')
    if run['status'] != 'ok':
        return [(False, 'task3_palindrome.py 没跑通：' + run['note'])]
    out = run['out']

    # ── 一、课件那四组 ──────────────────────────────────────────
    for s in LPS_CASES:
        want = str(model_lps(s))
        checks.append(counted(out, s, want,
                              '判分自己算的也是 ' + want,
                              'TODO 1 的 lps 要在**长度从小到大**的枚举下填表'
                              '（写反了短区间还是 0，答案会偏小）'))
    got = label_value(out, 'LPS ' + LPS_CASES[0])
    if got is not None and got.split()[:1] == [str(model_lps(LPS_CASES[0]))]:
        checks.append((True, '「LPS character ' + got + '」这一行也对上了'))
    elif got is None:
        checks.append((False, '没看到「LPS character …」这一行'))
    else:
        checks.append((False, '「LPS character」打出 ' + show(got) + '，期望 '
                              + str(model_lps(LPS_CASES[0])) + '：TODO 1 的 lps 还没写对'))
    for prefix, s in [('character 是5', 'character'), ('abba 是4', 'abba'),
                      ('abcda 是3', 'abcda'), ('aaaa 是4', 'aaaa')]:
        got = label_bool(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif got is True:
            checks.append((True, prefix + ' True（判分自己算的也是 '
                                 + str(model_lps(s)) + '）'))
        else:
            checks.append((False, prefix + ' 打出 ' + str(got) + '，期望 True：'
                                  'TODO 1 还没算对'))

    # ── 二、与暴力版对拍 ────────────────────────────────────────
    bad_pairs = []
    for s in PAL_SHORT:
        got = label_value(out, '暴力对照 ' + s)
        want = str(model_lps(s))
        if got is None:
            bad_pairs.append(s + ' 那一行没看到')
            continue
        if got.split()[:2] != [want, want]:
            bad_pairs.append(s + ' 打出 ' + show(got) + '，期望 ' + want + ' ' + want)
    if not bad_pairs:
        checks.append((True, '七组短串上「区间 DP / 暴力」两列都等于判分自己算的长度'
                             '（暴力版枚举全部子序列，是独立答案）'))
    else:
        checks.append((False, '短串对拍有 ' + str(len(bad_pairs)) + ' 处不对：'
                              + show('；'.join(bad_pairs[:2]))
                              + '：TODO 1 与 TODO 2 都要写出来才会两列相同'))
    got = label_bool(out, '短串上两版都对')
    if got is None:
        checks.append((False, '没看到「短串上两版都对 …」这一行'))
    elif got is True:
        checks.append((True, '短串上两版都对 True'))
    else:
        checks.append((False, '短串上两版都对 打出 ' + str(got) + '，期望 True：'
                              'TODO 2 的 lps_brute 要么还没写、要么枚举漏了子序列'))
    checks.append(counted(out, 'racecar 两版都给', str(model_lps('racecar')),
                          '整个串本身就是回文', 'TODO 1/2 在 racecar 上还没对上'))

    # ── 三、边界 ────────────────────────────────────────────────
    for prefix, s, want, todo in [
            ('空串 0', '', 0, 'TODO 1 的 lps 在空串上直接交回 0（那个 length 循环一次都不进）'),
            ('单字符 1', 'z', 1, 'TODO 1 的单格区间要先各自填 1'),
            ('两个相同 2', 'zz', 2, 'TODO 1 两头相同就配上：dp[i+1][j-1] + 2'),
            ('两个不同 1', 'zy', 1, 'TODO 1 不同就丢一头：max(dp[i+1][j], dp[i][j-1])'),
            ('全相同 等于长度', 'aaaaaaaa', 8, 'TODO 1 在整条都是回文时要给长度 8'),
            ('与倒序串的 LCS 一致', 'character', 5, 'TODO 1 还没算对（回文子序列 = 与倒序串的 LCS）')]:
        got = label_bool(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif got is True:
            checks.append((True, prefix + ' True（判分自己的长度是 ' + str(model_lps(s)) + '）'))
        else:
            checks.append((False, prefix + ' 打出 ' + str(got) + '，期望 True：' + todo))

    # ── 四、200 组随机小串 ──────────────────────────────────────
    got = label_value(out, '随机对拍 与暴力不一致组数')
    if got == '0':
        checks.append((True, '随机对拍 与暴力不一致组数 0'))
    elif got is None:
        checks.append((False, '没看到「随机对拍 与暴力不一致组数 …」这一行'))
    else:
        checks.append((False, '随机对拍 与暴力不一致组数 打出 ' + show(got) + '，期望 0：'
                              'TODO 1 与 TODO 2 在 200 组（长度 0~12、字母表 abc）上要一致'))
    checks.append(counted(out, '随机对拍 不一致组数', '0',
                          '200 组上与暴力版从不打架', 'TODO 1/2 还没写全'))

    # 判分自己按同一造法造 200 组、用自己的参照实现算一遍
    bad_model = 0
    random.seed(LPS_SEED_A)
    for _ in range(LPS_TRIALS):
        n = random.randint(0, 12)
        s = ''.join(random.choice('abc') for _ in range(n))
        if model_lps(s) != model_lps_brute(s):
            bad_model += 1
    if bad_model == 0:
        checks.append((True, '判分自己按同一造法（random.seed(' + str(LPS_SEED_A)
                             + ')、长度 0~12、字母表 abc）造 200 组，用**判分自己的**区间 DP '
                             '与暴力版算出不一致 ' + str(bad_model) + ' 组——脚本那一行的 0 对得上'))
    else:
        checks.append((False, '判分自己的参照实现在这 200 组上不一致 ' + str(bad_model)
                              + ' 组（这是判分自己的问题，请报给教练）'))

    # ── 五、耗时趋势 ────────────────────────────────────────────
    t_lps = time_values(out, '01')
    if not t_lps:
        checks.append((False, '没看到「耗时 01 LPS 区间DP n=… 秒」这一行：'
                              '带 print 的行别改、别删'))
    elif [n for n, _ in t_lps] != list(LPS_SIZES):
        checks.append((False, '读到的规模是 ' + show([n for n, _ in t_lps]) + '，期望 '
                              + show(list(LPS_SIZES)) + '：三档规模都要量一次'))
    elif any(s <= 0 for _, s in t_lps):
        checks.append((False, '有三行的秒数是 0.000000：TODO 1 还没写出来（留白版三行都是 0）'))
    else:
        checks.append((True, 'LPS 三档耗时都量到了（'
                             + ' / '.join(f'{s:.6f}' for _, s in t_lps) + ' 秒）'))
        values = tbl(t_lps)
        grow = values[-1] / max(values[0], 1e-9)
        if grow >= 3.0:
            checks.append((True, '规模翻四倍（100→400）耗时涨 ' + f'{grow:.2f}'
                                 + ' 倍——区间 DP 是 O(n^2)，翻四倍规模该涨十几倍'
                                   '（这里只要求涨 3 倍以上，留足计时噪声）'))
        else:
            checks.append((False, '规模翻四倍耗时只涨 ' + f'{grow:.2f}'
                                  + ' 倍，期望明显更慢：TODO 1 的 lps 要真的建 n×n 的表'
                                    '并两层循环填（别在里面提前交回）'))
    lps_timed = bool(t_lps) and all(s > 0 for _, s in t_lps)
    if lps_timed:
        for prefix, todo in [('规模大的一档更慢', 'TODO 1 的 lps 还没写，三档秒数都是 0.000000'),
                             ('耗时没有一行是0', 'TODO 1 的 lps 还没写（留白版三行都是 0.000000）')]:
            got = label_bool(out, prefix)
            if got is None:
                checks.append((False, '没看到「' + prefix + ' …」这一行'))
            elif got is True:
                checks.append((True, prefix + ' True'))
            else:
                checks.append((False, prefix + ' 打出 ' + str(got) + '，期望 True：' + todo))
    else:
        for prefix in ('规模大的一档更慢', '耗时没有一行是0'):
            checks.append((False, prefix + ' 这一条先看不了：三档秒数里有 0.000000'
                                  '（TODO 1 的 lps 还没写出来），比不出快慢。'
                                  '先把它写出来再回来看这条'))
    checks.append(counted(out, '最大一档长度', str(LPS_SIZES[-1]),
                          '量耗时的那一档串长', '这几行 print 是给好的，别改'))

    # ── 六、探针：判分自己那批字符串 ────────────────────────────
    raw, err = run_probe('task3_palindrome', PROBE_TASK3)
    if raw is None:
        checks.append((False, '任务 3 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)

    probe_cases = ['', 'z', 'zz', 'zy', 'aaaaaaaa', 'a', 'ab', 'aa', 'abc', 'aab',
                   'racecar', 'abcba', 'character', 'abba', 'abcda', 'aaaa']
    bad = []
    for s, got in zip(probe_cases, data['lps']):
        want = model_lps(s)
        if got != want:
            bad.append(repr(s) + ' 打出 ' + show(got) + '，期望 ' + str(want))
    if not bad:
        checks.append((True, '探针：判分自己那 ' + str(len(probe_cases)) + ' 组字符串'
                             '（含空串、单字符、全相同、课件那四组）上，lps 与判分自己的'
                             '区间 DP 逐组相同'))
    else:
        checks.append((False, '探针有 ' + str(len(bad)) + ' 组不对：' + show('；'.join(bad[:3]))
                              + '：TODO 1 在「两头相同 + 长度差一」这类区间上最容易错'))
    bad_b = []
    for s, got in zip(probe_cases, data['brute']):
        want = model_lps_brute(s)
        if got != want:
            bad_b.append(repr(s) + ' 打出 ' + show(got) + '，期望 ' + str(want))
    if not bad_b:
        checks.append((True, '探针：lps_brute 在那 ' + str(len(probe_cases))
                             + ' 组上也与判分自己的暴力版（枚举全部子序列）逐组相同'))
    else:
        checks.append((False, '探针：lps_brute 有 ' + str(len(bad_b)) + ' 组不对：'
                              + show('；'.join(bad_b[:3]))
                              + '：TODO 2 要「每个已有子序列各接上这个字符」，'
                                '别漏掉不接的那些'))
    return checks


# ══ 任务 4 · 石子合并 ═══════════════════════════════════════════════════

PROBE_TASK4 = '''
def call(f, *args):
    try:
        return f(*args)
    except Exception as exc:
        return type(exc).__name__ + ': ' + str(exc)

CASES = [[], [7], [3, 5], [5, 5, 5, 5], [9, 9, 9], [1, 2], [1, 2, 3],
         [4, 1, 2, 3], [3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6]]
out = {}
out['asc'] = [call(m.stone_dp, list(a)) for a in CASES]
out['desc'] = [call(m.stone_desc, list(a)) for a in CASES]
out['brute'] = [call(m.stone_brute, list(a)) for a in CASES]
print('PROBE ' + json.dumps(out, ensure_ascii=False))
'''

PROBE_STONE_CASES = [[], [7], [3, 5], [5, 5, 5, 5], [9, 9, 9], [1, 2], [1, 2, 3],
                     [4, 1, 2, 3], [3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6]]


def stone_lit_cases():
    """脚本第四节那 200 组（random.seed(9)、1~7 堆、每堆 1~20）——与任务文件同一造法。"""
    return judge_stone_data(STONE_SEED_A, STONE_TRIALS)


def check_task4():
    checks = []
    run = run_script('task4_stone.py')
    if run['status'] != 'ok':
        return [(False, 'task4_stone.py 没跑通：' + run['note'])]
    out = run['out']

    want_asc = [model_stone(a) for a in STONE_CASES]
    want_desc = [model_stone(a, 'desc') for a in STONE_CASES]
    want_brute = [model_stone_brute(a) for a in STONE_CASES]

    # ── 一、课件那三组：从小到大 / 从大到小 / 暴力 ───────────────
    # 判分按**标签**读（不按编号）：标签里写了是这一组、是哪个方向。
    for i, st in enumerate(STONE_CASES):
        checks.append(counted(out, '石子' + str(st) + ' 从小到大', str(want_asc[i]),
                              '判分自己算的也是 ' + str(want_asc[i]),
                              'TODO 1 要按**长度从小到大**枚举，末尾再加上区间和'
                              '（pre[j+1] - pre[i]）'))
    for i, st in enumerate(STONE_CASES):
        checks.append(counted(out, '石子' + str(st) + ' 从大到小', str(want_desc[i]),
                              '判分自己按同一处写反算出来也是 ' + str(want_desc[i])
                              + '，**偏小**',
                              'TODO 2 的 stone_desc 就是把 lengths 反过来'
                              '（range(n, 1, -1)），短区间还没算过、代价被漏掉'))
    checks.append(counted(out, '暴力[4, 1, 2, 3]', str(want_brute[0]),
                          '判分自己的暴力版也是 ' + str(want_brute[0]),
                          'TODO 3 的 stone_brute 要枚举「这次合哪两堆」，'
                          '并把结果记在元组上（列表不能当字典的键）'))
    for prefix, want, todo in [
            ('[4, 1, 2, 3] 从小到大是19', True, 'TODO 1 还没算对'),
            ('[4, 1, 2, 3] 从大到小更小', True,
             'TODO 2 给的是偏小的错答案——这一行就是在确认那件事'),
            ('[3, 4, 5, 6, 7] 从小到大是57', True, 'TODO 1 还没算对'),
            ('[1, 2, 3, 4, 5, 6] 从小到大是51', True, 'TODO 1 还没算对')]:
        got = label_bool(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif got is want:
            checks.append((True, prefix + ' ' + str(got) + '（期望值）'))
        else:
            checks.append((False, prefix + ' 打出 ' + str(got) + '，期望 ' + str(want)
                                  + '：' + todo))

    # ── 二、与暴力逐一对上 ──────────────────────────────────────
    got = label_bool(out, '从小到大 三组都与暴力一致')
    if got is None:
        checks.append((False, '没看到「从小到大 三组都与暴力一致 …」这一行'))
    elif got is True:
        checks.append((True, '从小到大 三组都与暴力一致 True（判分自己的暴力版给出 '
                             + show(want_brute) + '）'))
    else:
        checks.append((False, '从小到大 三组都与暴力一致 打出 ' + str(got) + '，期望 True：'
                              'TODO 1 或 TODO 3 有一个不对'))
    got = label_bool(out, '从大到小 三组都与暴力一致')
    if got is None:
        checks.append((False, '没看到「从大到小 三组都与暴力一致 …」这一行'))
    elif got is False:
        checks.append((True, '从大到小 三组都与暴力一致 False——**这一行要的就是 False**：'
                             '长度枚举写反了，三组都与暴力版对不上'))
    else:
        checks.append((False, '从大到小 三组都与暴力一致 打出 ' + str(got) + '，期望 False：'
                              '要是 True，说明 TODO 2 其实没把顺序写反'
                              '（或者 TODO 3 的暴力版跟着一起错了）'))
    checks.append(counted(out, '从小到大 与暴力一致', 'True',
                          '三组都对上', 'TODO 1/3 还没写对'))

    # ── 三、边界 ────────────────────────────────────────────────
    for prefix, arr, want, todo in [
            ('单堆 0', [7], 0, 'TODO 1 的 stone_dp 在只剩一堆时直接交回 0，不用再合并'),
            ('两堆 是它们的和', [3, 5], 8, 'TODO 1 在 [3, 5] 上要交回 8（两堆合并一次）'),
            ('全相同 四个5是40', [5, 5, 5, 5], 40,
             'TODO 1 在 [5, 5, 5, 5] 上要交回 40：先合成两个 10（代价 10 + 10）、'
             '再合成 20（代价 20）'),
            ('三个9是45', [9, 9, 9], 45,
             'TODO 1 在 [9, 9, 9] 上要交回 45：合并两次，18 与 27'),
            ('单堆 暴力也是0', [7], 0, 'TODO 3 的 stone_brute 在单堆上也要交回 0'),
            ('空排 0', [], 0, 'TODO 1 的 stone_dp 在空排上要交回 0')]:
        got = label_bool(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif got is True:
            checks.append((True, prefix + ' True（判分自己的暴力版给出 ' + str(want) + '）'))
        else:
            checks.append((False, prefix + ' 打出 ' + str(got) + '，期望 True：' + todo
                                  + '（判分自己算出的是 ' + str(want) + '）'))
    for label, arr, note, todo in [
            ('两堆 3与5', [3, 5], '两堆合并一次，代价是它们的和', 'TODO 1 还没算对'),
            ('全相同四个5', [5, 5, 5, 5],
             '先合成两个 10 再合成 20，一共 40',
             'TODO 1 的 stone_dp 在全相同时要交回 40：先合成两个 10、再合成 20')]:
        checks.append(counted(out, label, str(model_stone(arr)), note, todo))

    # ── 四、200 组随机对拍 ──────────────────────────────────────
    lit = stone_lit_cases()
    expect_asc = expect_desc = 0
    for a in lit:
        want = model_stone_brute(a)
        if model_stone(a) != want:
            expect_asc += 1
        if model_stone(a, 'desc') != want:
            expect_desc += 1
    for prefix, want, todo in [
            ('随机对拍 组数', str(STONE_TRIALS), '这一行是给好的，别删'),
            ('从小到大 与暴力不一致组数', str(expect_asc),
             'TODO 1 在 200 组（1~7 堆、每堆 1~20）上必须全对'),
            ('从大到小 与暴力不一致组数', str(expect_desc),
             'TODO 2 写反之后该错很多组——这一行正是这一课要看的现象')]:
        got = label_value(out, prefix)
        if got is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif got == want:
            checks.append((True, prefix + ' ' + got))
        else:
            checks.append((False, prefix + ' 打出 ' + show(got) + '，期望 ' + want
                                  + '（判分自己按同一造法复算出来的）：' + todo))
    got = label_bool(out, '顺序写反是错的一版')
    if got is None:
        checks.append((False, '没看到「顺序写反是错的一版 …」这一行'))
    elif got is True:
        checks.append((True, '顺序写反是错的一版 True：从小到大 0 组错、从大到小错很多组'))
    else:
        checks.append((False, '顺序写反是错的一版 打出 ' + str(got) + '，期望 True：'
                              'TODO 1 与 TODO 2 必须给出**不同**的结果才算把顺序写反了'))
    if expect_asc == 0 and expect_desc > 0:
        checks.append((True, '判分自己按同一造法（random.seed(' + str(STONE_SEED_A)
                             + ')、1~7 堆、每堆 1~20）造 200 组，用自己的暴力版与两个方向的'
                             '区间 DP 算出：从小到大错 ' + str(expect_asc) + ' 组、从大到小错 '
                             + str(expect_desc) + ' 组——脚本那两行的数字对得上'))
    else:
        checks.append((False, '判分自己复算这批数据得到「从小到大错 ' + str(expect_asc)
                              + ' 组、从大到小错 ' + str(expect_desc)
                              + ' 组」，没复现出「写反 = 错一大片」：'
                                '这是判分自己的问题，请报给教练'))
    checks.append(counted(out, '从小到大 不一致组数', str(expect_asc),
                          '判分自己算出来也是 ' + str(expect_asc) + ' 组', 'TODO 1 还没算对'))
    checks.append(counted(out, '从大到小 不一致组数', str(expect_desc),
                          '判分自己算出来也是 ' + str(expect_desc)
                          + ' 组——写反之后该错一大片',
                          'TODO 2 要严格照「同一个循环、lengths 反过来」写；'
                          '打出 0 说明还没把顺序写反'))

    # ── 五、耗时趋势 ────────────────────────────────────────────
    t_asc = time_values(out, '01')
    if not t_asc:
        checks.append((False, '没看到「耗时 01 石子合并 区间DP n=… 秒」这一行：'
                              '带 print 的行别改、别删'))
    elif [n for n, _ in t_asc] != list(STONE_SIZES):
        checks.append((False, '读到的规模是 ' + show([n for n, _ in t_asc]) + '，期望 '
                              + show(list(STONE_SIZES)) + '：三档规模都要量一次'))
    elif any(s <= 0 for _, s in t_asc):
        checks.append((False, '有三行的秒数是 0.000000：TODO 1 还没写出来（留白版三行都是 0）'))
    else:
        checks.append((True, '石子合并三档耗时都量到了（'
                             + ' / '.join(f'{s:.6f}' for _, s in t_asc) + ' 秒）'))
    if t_asc and all(s > 0 for _, s in t_asc):
        got = label_bool(out, '耗时没有一行是0')
        if got is None:
            checks.append((False, '没看到「耗时没有一行是0 …」这一行'))
        elif got is True:
            checks.append((True, '耗时没有一行是0 True'))
        else:
            checks.append((False, '耗时没有一行是0 打出 ' + str(got) + '，期望 True：'
                                  'TODO 1 的 stone_dp 还没写（留白版三行都是 0.000000）'))
    else:
        checks.append((False, '耗时没有一行是0 这一条先看不了：三档秒数里有 0.000000'
                              '（TODO 1 的 stone_dp 还没写出来）。'
                              '先把它写出来再回来看这条'))
    checks.append(counted(out, '最大一档堆数', str(STONE_SIZES[-1]),
                          '量耗时的那一档堆数', '这几行 print 是给好的，别改'))

    # ── 六、探针：判分自己那批石子 ──────────────────────────────
    raw, err = run_probe('task4_stone', PROBE_TASK4)
    if raw is None:
        checks.append((False, '任务 4 的探针没跑成：' + err))
        return checks
    data = json.loads(raw)

    bad = []
    for a, got in zip(PROBE_STONE_CASES, data['asc']):
        want = model_stone(a)
        if got != want:
            bad.append(str(a) + ' 打出 ' + show(got) + '，期望 ' + str(want))
    if not bad:
        checks.append((True, '探针：判分自己那 ' + str(len(PROBE_STONE_CASES)) + ' 组石子上，'
                             'stone_dp 从小到大给出 '
                             + show([model_stone(a) for a in PROBE_STONE_CASES])
                             + '，与判分自己的区间 DP 逐组相同'))
    else:
        checks.append((False, '探针有 ' + str(len(bad)) + ' 组不对：' + show('；'.join(bad[:3]))
                              + '：TODO 1 的断点范围是 range(i, j)、末尾别忘了区间和'))
    bad_d = []
    for a, got in zip(PROBE_STONE_CASES, data['desc']):
        want = model_stone(a, 'desc')
        if got != want:
            bad_d.append(str(a) + ' 打出 ' + show(got) + '，期望 ' + str(want))
    if not bad_d:
        checks.append((True, '探针：stone_desc 在每一组上给出 '
                             + show([model_stone(a, 'desc') for a in PROBE_STONE_CASES])
                             + '——与判分自己把 lengths 反过来算的完全一致'
                               '（[4, 1, 2, 3] 该是 10 而不是 19，**偏小**）'))
    else:
        checks.append((False, '探针：stone_desc 有 ' + str(len(bad_d)) + ' 组不对：'
                              + show('；'.join(bad_d[:3]))
                              + '：TODO 2 只该改 lengths 那一行，别的字一个都别动'))
    bad_b = []
    for a, got in zip(PROBE_STONE_CASES, data['brute']):
        want = model_stone_brute(a)
        if got != want:
            bad_b.append(str(a) + ' 打出 ' + show(got) + '，期望 ' + str(want))
    if not bad_b:
        checks.append((True, '探针：stone_brute 在那 ' + str(len(PROBE_STONE_CASES))
                             + ' 组（含空排、单堆、全相同）上也与判分自己的暴力版逐组相同'))
    else:
        checks.append((False, '探针：stone_brute 有 ' + str(len(bad_b)) + ' 组不对：'
                              + show('；'.join(bad_b[:3]))
                              + '：TODO 3 的递归要在 len(t) == 1 时交回 0，'
                                '元组拼法是 t[:k] + (cost,) + t[k + 2:]'))

    # ── 七、判分自己用**判分自己的**数据再核一遍「写反 = 偏小」────────
    worse = better = same = 0
    for a in STONE_POOL:
        want = model_stone_brute(a)
        asc, desc = model_stone(a), model_stone(a, 'desc')
        if asc != want:
            worse += 1                       # 判分自己的从小到大都不对，那是判分自己的问题
        if desc < want:
            better += 1
        elif desc == want:
            same += 1
    if worse == 0 and better > 0:
        checks.append((True, '判分自己在**自己造的** ' + str(len(STONE_POOL)) + ' 组数据上复核：'
                             '从小到大 0 组错；从大到小有 ' + str(better) + ' 组给出**偏小**的'
                             '答案（另有 ' + str(same) + ' 组恰好一样）——'
                             '「枚举顺序写反 = 答案偏小」这条结论是判分自己算出来的'))
    else:
        checks.append((False, '判分自己的参照实现在这批数据上没复现出「写反 = 偏小」'
                              '（从小到大错 ' + str(worse) + ' 组、偏小 ' + str(better)
                              + ' 组）：这是判分自己的问题，请报给教练'))
    return checks


CHECKERS = {
    'task1_lis.py': check_task1,
    'task2_lcs.py': check_task2,
    'task3_palindrome.py': check_task3,
    'task4_stone.py': check_task4,
}


def main():
    print('StudyMate lab 0026 · 自动判分（先写状态，再写代码：序列与区间的状态设计）')
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
        print('四个任务都过了，再对照 ../solutions/0026-dp-sequence-interval/ 看参考解。')
        return 1
    print('四个任务都过了。现在去对照 ../solutions/0026-dp-sequence-interval/：')
    print('比一比你的写法与参考解，再用一句话回答「为什么 tails 不是一条递增子序列」'
          '与「为什么区间 DP 必须先算短区间」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
