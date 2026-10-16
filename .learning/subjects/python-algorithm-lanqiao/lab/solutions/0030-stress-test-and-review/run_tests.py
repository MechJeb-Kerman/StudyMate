#!/usr/bin/env python3
r"""lab 0030 · 自动判分（交卷之前你要检查什么）

用法（在 lab/0030-stress-test-and-review/ 目录里）：

    py run_tests.py

判法：**五层**，一层里几条检查各自给 PASS / FAIL。每一条 FAIL 后面都点明
「这一条指哪个文件的哪个 TODO」，不用猜该补哪一段。

    第 1 层 · 对拍：两把尺子，同一批数据（task1_brute_ref.py）
        三个数一起看：同思路的「参考解」抓到 0 组（它是装饰品）、
        独立暴力抓到 58 组、独立分治也抓到 58 组；反向验证那一格必须回到 0 组
        （把 best 的初值改好之后还对不上，说明对拍器自己在乱报，那 58 组也就不算数）。
        第一个反例要连**组号**一起交：按种子 1 从头扫，它是第 23 组（组号从 0 起），
        数据恰好是 [-7]——「最小」那一类边界数据，n = 1 时循环体一次都不进。
        判分自己拿另一个种子（7 与 13）重造一批数据、另写三把尺子再算一遍，
        所以把 0 / 58 / 23 写死在这里是过不去的。

    第 2 层 · 生成器的范围要对（task2_generator.py）
        0 组 与 33 组这两个数是同一句话的两半：同一个 bug、同一个对拍器、同样 300 组，
        生成器多一句 max(a) > 0，抓到的组数就从 33 变成 0。
        run_pair 要在判分自己造的探针上算得对：种子在循环外面定一次、
        每组重抽 n（rng.randint(1, T1_N_HI)）、until_bad 为真时停在哪一组。
        把这几个数写死、或者把种子放进循环里，探针会当场抓住。

    第 3 层 · 多组数据要清空（task3_reset.py）
        [6, 36, 41] 与 [6, 30, 5] 摆在一起，重点在**第一组那个 6**——
        两种跑法的第一组都是 6，所以只拿样例的第一组试，什么都看不出来。
        判分换三组自己造的数据再跑一遍（第一组的答案刻意与后面某一组相等），
        并往 run_cases 里塞一个**自己的** Solver 类，看这条链通不通、
        看「忘了清空」那一版是不是真的一个 reset 都没调。

    第 4 层 · 取模：小数据上看不出来（task4_modulo.py）
        2090 位 与 2080 位这两个数是「小数据看不出」的量化说法；
        更要紧的是**第一个分家的 n = 45**：它不是背下来的，是 first_diff 循环比出来的
        （n = 44 两版还相等，n = 45 就不等了）。判分拿 44 / 45 / 46 三个点单独试一遍，
        再从 fib_nomod 上另算一次位数（tools.fib_count 是同一个口径的另一个写法）。
        这一层一个耗时都不量——本课全部是确定值。

    第 5 层 · 打印行、单跑、文件没被动过
        逐字读四个脚本打印出来的判分行（那些行就是接口，别改它们）；
        检查每个任务文件单跑退出码是 0、0 处 Traceback；
        再确认这个目录里的 tools.py 与发下来那一份**逐字节相同**——
        判分与课件那几组实测数字全靠它，自己改一个字，58 组 / 33 组 / 2090 位就对不上了。

判分不判的东西：注释写得多不多、清单的排版漂不漂亮、变量名起得好不好，
由 lab/README.md 的自查清单与课件那一节回答；这里只管能不能跑、口径对不对、
那四个现象是不是**算出来的**。

退出码：五层都过是 0；还有没过的（或跳过的）是 1。
"""

from __future__ import annotations

import hashlib
import importlib
import os
import random
import subprocess
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import tools as judge                                     # noqa: E402  给好的，别改
from tools import (CASES, EXPECT, MOD, T1_HI, T1_LO, T1_N_HI, T1_SEED, T1_TRIALS,  # noqa: E402
                   T2_SEED, T2_TRIALS, T4_BIG, T4_FIRST_N, T4_ROWS, T4_TAIL,
                   cand_buggy, cand_fixed, draw_case, fib_count, fib_mod, fib_nomod,
                   gen_any, gen_positive, ref_brute, ref_dc, ref_same_idea,
                   values_equal)

TASK_FILES = ['task1_brute_ref.py', 'task2_generator.py', 'task3_reset.py',
              'task4_modulo.py']

# ── 字符串片段：全角括号单独放成常量 ────────────────────────────────────
# 本文件里凡是「一句话的结尾是中文括号」的地方都写成 '……' + RP_CN 这种形状，
# 免得整段中文与括号挤在一起、读起来看不出括号是代码还是字符串的一部分。
RP_CN = chr(0xFF09)                 # 全角右括号
LP_CN = chr(0xFF08)                 # 全角左括号
TODO_MARK = '  → 这一条指 '

# 这一课一个耗时都不量：全部判据都是确定值（随机数一律固定种子）。
# 本文件出现过的最长反引号串是两个（用来讲拼接方式），源码里不许有连续三个。
FENCE = '`' * 3

# 发下来那一份 tools.py 的哈希（判分要确认学生没动过它：那几组实测数字全靠它）。
TOOLS_SHA256 = '83AB52926E501E6F'
TOOLS_CANON = None      # 第一次用到时才算，见 tools_same_as_handout()

# ── 判分自己造的那批数据（刻意换种子、换规模，与脚本用的那一批不同）─────────
PROBE1 = [(7, 400), (13, 120)]          # task1 的探针：(种子, 组数)
PROBE1_N_HI = 8
PROBE1_LO, PROBE1_HI = -9, 9

PROBE2 = [(11, 80), (5, 60), (23, 40)]  # task2 的探针：(种子, 组数)
PROBE2_N_HI = 6                         # 刻意与 T1_N_HI 不同：上限换了数就该跟着换

PROBE3_CASES = [[5, 5], [1], [2, 2]]    # task3 的探针：第一组 10，第三组恰好又是 10
PROBE3_EXPECT = [10, 1, 4]

PROBE4_TAILS = [44, 45, 46, 0, None]
PROBE4_DIGITS = [1, 10, 44, 45, 46, 50, 30]
PROBE4_RANDY = [(17, 120, 30, 90), (6, 40, 1, 25)]


# ── 载入学生写的四个文件 ────────────────────────────────────────────────

class Loaded:
    """逐个载入四个任务文件 → 记下模块、载入异常、以及缺了哪些名字。

    四道缝各自独立：某一个文件坏了，只有它负责的那一层会报载入失败。
    """

    REQUIRED = {
        'task1_brute_ref': ['run_trials', 'first_bad'],
        'task2_generator': ['run_pair'],
        'task3_reset': ['Solver', 'run_cases'],
        'task4_modulo': ['first_diff', 'tail14', 'sample_rows', 'big_digits',
                         'random_bad', 'random_first', 'gap_cell'],
    }

    def __init__(self):
        self.modules = {}
        self.errors = {}
        self.missing = {}
        for name, required in self.REQUIRED.items():
            try:
                module = importlib.import_module(name)
                importlib.reload(module)          # 判分在同一进程里跑多次时别拿旧对象
            except Exception:
                self.errors[name] = traceback.format_exc()
                continue
            self.modules[name] = module
            gone = [item for item in required
                    if getattr(module, item, None) is None]
            if module.__name__ == '__main__':
                gone.append('模块名变成了 __main__')
            if gone:
                self.missing[name] = gone

    def error_of(self, name):
        return self.errors.get(name)

    def gone(self, name):
        return self.missing.get(name, [])

    def ok(self, name):
        return name in self.modules and not self.missing.get(name)

    def fn(self, name, item):
        return getattr(self.modules[name], item, None)

    def why(self, label, name):
        """这一层为什么一开始就过不去——把该补的那一段名字点出来。"""
        if name in self.errors:
            tail = '\n'.join(self.errors[name].strip().splitlines()[-6:])
            return (label + '载入失败——文件自己那几行就报错了：\n' + tail
                    + '\n        ' + LP_CN + '判分是 import 你的文件的，'
                      '改完先单跑一次看它退出码是不是 0' + RP_CN)
        gone = self.gone(name)
        return (label + '里找不到这些名字：' + '、'.join(gone)
                + '\n        ' + LP_CN + '函数名与文件名都是判分接口，别改名、别删；'
                  '要写的是文件里标着 TODO 的那几段' + RP_CN)


# ── 调用学生函数的保险：报错就转成一句 FAIL，不让判分自己崩 ──────────────

def attempt(func, *args, **kwargs):
    """调一次 → (值, 错误文本)。抛异常时值是 None、错误文本是「类型: 说明」。"""
    if func is None:
        return None, '没有这个函数（判分接口的名字被改了或删了）'
    try:
        return func(*args, **kwargs), None
    except Exception as exc:
        return None, type(exc).__name__ + ': ' + str(exc)


def error_note(error):
    return '' if error is None else '（调用时抛出 ' + error + RP_CN


# 每个判分接口落在哪一段 TODO 上——FAIL 后面都带上它，学生不用猜该补哪一段。
TODO_OF = {
    ('task1_brute_ref', 'run_trials'): 'task1_brute_ref.py TODO 1',
    ('task1_brute_ref', 'first_bad'): 'task1_brute_ref.py TODO 2',
    ('task2_generator', 'run_pair'): 'task2_generator.py TODO（run_pair）',
    ('task3_reset', 'Solver'): 'task3_reset.py TODO 1（class Solver）',
    ('task3_reset', 'answer'): 'task3_reset.py TODO 1（class Solver）',
    ('task3_reset', 'reset'): 'task3_reset.py TODO 1（class Solver）',
    ('task3_reset', 'run_cases'): 'task3_reset.py TODO 2（run_cases）',
    ('task4_modulo', 'first_diff'): 'task4_modulo.py TODO 1（first_diff）',
    ('task4_modulo', 'tail14'): 'task4_modulo.py TODO 2（tail14）',
    ('task4_modulo', 'sample_rows'): 'task4_modulo.py TODO 3（sample_rows）',
    ('task4_modulo', 'big_digits'): 'task4_modulo.py TODO 4（big_digits）',
    ('task4_modulo', 'gap_cell'): 'task4_modulo.py TODO 4（big_digits）',
    ('task4_modulo', 'random_bad'): 'task4_modulo.py 给好的 random_bad',
    ('task4_modulo', 'random_first'): 'task4_modulo.py 给好的 random_first',
}


def todo_of(module, item):
    return TODO_OF.get((module, item), item)


def with_todo(item, text):
    """在一条 FAIL 后面补上「这一段在哪个文件哪个 TODO」。"""
    return text + TODO_MARK + todo_of(*item)


def short(text, limit=60):
    text = '' if text is None else str(text)
    return text if len(text) <= limit else text[:limit] + '…'


def fresh_solver(solver):
    """每次要一个**新起的** Solver：类就现起一个，已经是实例就原样交回。

    留白版与参考解都把 Solver 写成一个类；这里顺带容忍「直接给了实例」的写法——
    判分不该因为这一点差别就说人家没写。
    """
    if callable(solver):
        return solver()          # 类（或者任何能无参造出实例的东西）
    return solver                # 已经是实例


# ── 判据小工具：值、布尔、组数、打印行逐字 ──────────────────────────────

def check_eq(actual, expected, good, bad):
    """值相等给 good，不等给 bad（bad 后面会补上「交回的是什么」）。"""
    if isinstance(expected, bool) or isinstance(actual, bool):
        same = actual is expected
    elif isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        same = list(actual) == list(expected)
    else:
        same = actual == expected
    if same:
        return True, good
    tail = ('（交回 ' + short(repr(actual), 56) + '，期望 '
            + short(repr(expected), 56) + RP_CN)
    return False, bad + tail


def check_count(actual, expected, todo, bad):
    """组数那一格：必须是 int，而且对得上（'58' / 58.0 / None 都不算）。"""
    if actual is None:
        return False, (bad + '（交回 None——这一格要真的**数**出来，'
                              '不是留着占位，也不是写死一个数' + TODO_MARK + todo)
    if isinstance(actual, bool) or not isinstance(actual, int):
        return False, (bad + '（交回 ' + short(repr(actual), 40) + '，类型是 '
                       + type(actual).__name__ + '——这一格要是一个整数'
                       + TODO_MARK + todo)
    if actual != expected:
        return False, (bad + '（交回 ' + str(actual) + '，期望 ' + str(expected)
                       + TODO_MARK + todo)
    return True, ''


def check_line(actual, tokens, good, bad, prefix=False):
    """打印行对得上吗：先按空白切、再一段段比，第一个不一样的地方点名。

    prefix=True 时只要求**以这几段开头**，后面还有别的也认。
    """
    got = str(actual).split()
    want = [str(token).split() for token in tokens]
    want = [piece for group in want for piece in group]
    if got == want or (prefix and got[:len(want)] == want):
        return True, good
    for i, piece in enumerate(want):
        if i >= len(got):
            head = '（这一行到第 ' + str(i + 1) + ' 段就没了，期望还有 '
            tail = repr(piece) + '；实际 ' + short(repr(actual), 56) + RP_CN
            return False, bad + head + tail
        if got[i] != piece:
            head = '（第 ' + str(i + 1) + ' 段是 ' + repr(got[i]) + '，期望 '
            tail = repr(piece) + '；整行 ' + short(repr(actual), 56) + RP_CN
            return False, bad + head + tail
    if prefix:
        return True, good
    return False, bad + '（后面还多出 ' + repr(' '.join(got[len(want):])) + RP_CN


def same_list(got, want):
    """两个表相等吗（JSON 往返会把 tuple 变成 list，所以一律先化成 list 再比）。"""
    if not isinstance(got, (list, tuple)):
        return False
    return list(got) == list(want)


def first_bad_place(got, want, label):
    """第一处不一样的位置交回一句人话（长度不同就说长度）。"""
    if not isinstance(got, (list, tuple)):
        return label + '交回的不是一个表：' + short(repr(got), 40)
    if len(got) != len(want):
        return label + '的条数是 ' + str(len(got)) + '，期望 ' + str(len(want))
    for i, (x, y) in enumerate(zip(got, want)):
        if not same_list(x, y):
            shown = tuple(x) if isinstance(x, tuple) else x
            return (label + '第 ' + str(i + 1) + ' 条是 ' + short(repr(shown), 44)
                    + '，期望 ' + short(repr(tuple(y)), 44))
    return label + '对不上'


# ── 判分自己的实现（独立证据：不吃 tools 里那几把尺子）──────────────────

def probe_brute(a):
    """照着定义自己再写一遍的暴力：枚举所有子段，一个不漏（与 tools.ref_brute 无关）。"""
    best = None
    for i in range(len(a)):
        s = 0
        for j in range(i, len(a)):
            s += a[j]
            if best is None or s > best:
                best = s
    return best


def probe_same_idea(a):
    """同一个错思路的另一份写法：cur 被按回 0，答案也截在 0 起步。"""
    cur = 0
    ans = 0
    for x in a:
        cur = cur + x
        if cur < 0:
            cur = 0
        if cur > ans:
            ans = cur
    return ans


def probe_dc(a):
    """分治版的最大子段和（判分自己的实现，用来与学生那一格「独立分治解」对照）。"""
    if not a:
        return None
    return _probe_dc(a, 0, len(a) - 1)


def _probe_dc(a, lo, hi):
    if lo == hi:
        return a[lo]
    mid = (lo + hi) // 2
    best_left = None
    s = 0
    for i in range(mid, lo - 1, -1):
        s += a[i]
        if best_left is None or s > best_left:
            best_left = s
    best_right = None
    s = 0
    for i in range(mid + 1, hi + 1):
        s += a[i]
        if best_right is None or s > best_right:
            best_right = s
    return max(_probe_dc(a, lo, mid), _probe_dc(a, mid + 1, hi), best_left + best_right)


def probe_fixed(a):
    """判分自己写的「修好初值」那一版：best 与 cur 都从头元素起步，空表交回 None。

    注意**不能**只把 best 改成 float('-inf')：`cur = max(0, cur + x)` 那一句
    照样把当前段的和按回 0，模型还是「子段可以空」，全负数据上仍然交回 0。
    """
    if not a:
        return None
    best = cur = a[0]
    for x in a[1:]:
        cur = x if cur < 0 else cur + x
        if cur > best:
            best = cur
    return best


def replay_trials(trials, seed, n_hi=None, lo=None, hi=None, ref=None):
    """判分自己的对拍器：拿自己另写的四把尺子数「各抓到几组不一致」。

    候选解用的是**给好的** cand_buggy（它是这一课的被测对象，不是学生写的），
    四把尺子全是判分自己另写的（probe_*）——所以这一格与学生那边独立。
    """
    n_hi = T1_N_HI if n_hi is None else n_hi
    lo = T1_LO if lo is None else lo
    hi = T1_HI if hi is None else hi
    ref = cand_buggy if ref is None else ref
    rng = random.Random(seed)
    counts = {('cand_buggy', 'same_idea'): 0, ('cand_buggy', 'brute'): 0,
              ('cand_buggy', 'dc'): 0, ('cand_fixed', 'brute'): 0}
    first = None
    for i in range(trials):
        a = draw_case(rng, n_hi, lo, hi)
        c = ref(a)
        if not values_equal(c, probe_same_idea(a)):
            counts[('cand_buggy', 'same_idea')] += 1
        if not values_equal(c, probe_brute(a)):
            counts[('cand_buggy', 'brute')] += 1
            if first is None:
                first = (i, a, c, probe_brute(a))
        if not values_equal(c, probe_dc(a)):
            counts[('cand_buggy', 'dc')] += 1
        if not values_equal(probe_fixed(a), probe_brute(a)):
            counts[('cand_fixed', 'brute')] += 1
    return counts, first


def probe_gen_positive(n, rng):
    """判分自己的「只造有正数」生成器（与 tools.gen_positive 同一个口径，另写一遍）。

    它抽的随机数个数与 gen_any 不同——「重抽到有正数为止」这件事会改变随机流，
    所以换个生成器、同一个种子，后面每一组数据都不一样。
    """
    while True:
        a = [rng.randint(T1_LO, T1_HI) for _ in range(n)]
        if max(a) > 0:
            return a


def probe_gen_any(n, rng):
    """判分自己的「照题面造」生成器：允许全负、允许全零。"""
    return [rng.randint(T1_LO, T1_HI) for _ in range(n)]


def probe_runner(gen, trials, seed, n_hi=None, until_bad=False):
    """判分自己数一遍：这批数据抓到几组、跑到第几组、第一组反例是什么。"""
    n_hi = T1_N_HI if n_hi is None else n_hi
    rng = random.Random(seed)
    caught = 0
    first = None
    groups = 0
    for i in range(trials):
        a = gen(rng.randint(1, n_hi), rng)
        groups += 1
        got, want = cand_buggy(a), probe_brute(a)
        if not values_equal(got, want):
            caught += 1
            if first is None:
                first = (i, a, got, want)
            if until_bad:
                break
    return {'caught': caught, 'groups': groups, 'first': first}


class ProbeSolver:
    """判分自己的 Solver：与任务里那个类同一个口径，另外**记下被调了几次**。

    run_cases 允许从外面传 solver 进来，塞的就是它——这样判分能看见
    「忘了清空」那一版是不是真的一组 reset 都没调（那样才对：bug 要复现得出来）。
    """

    def __init__(self):
        self.total = 0
        self.resets = 0
        self.answers = 0

    def reset(self):
        self.resets += 1
        self.total = 0

    def answer(self, a):
        self.answers += 1
        for x in a:
            self.total += x
        return self.total


def probe_run_cases(cases, reset_per_case, solver):
    """判分自己的 run_cases：每组一个答案，reset 只在需要时调。"""
    out = []
    for a in cases:
        if reset_per_case:
            solver.reset()
        out.append(solver.answer(a))
    return out


def probe_random_bad(seed, trials, lo, hi):
    """判分自己数一遍：这批随机 n 里两版不相等的有几组。"""
    rng = random.Random(seed)
    bad = 0
    for _ in range(trials):
        n = rng.randint(lo, hi)
        if fib_nomod(n) != fib_mod(n):
            bad += 1
    return bad


def probe_random_first(seed, trials, lo, hi):
    """判分自己找一遍：这批随机 n 里第一个不相等的 n。"""
    rng = random.Random(seed)
    for _ in range(trials):
        n = rng.randint(lo, hi)
        if fib_nomod(n) != fib_mod(n):
            return n
    return None


def canonical_tail(x):
    """末 14 位那一格的标准写法（x 是 None 就还是 None）。"""
    if x is None:
        return None
    return str(x)[-T4_TAIL:]


def canonical_rows(ns):
    """判分自己造的那张表：每个 n 一行四格，格子口径与脚本那一列一样。"""
    rows = []
    for n in ns:
        x, y = fib_nomod(n), fib_mod(n)
        rows.append((n, canonical_tail(x), y, x == y))
    return rows


def row_text(row):
    """把一行四格按脚本那一行的形状拼出来——拼出来的字要能逐字对上脚本的打印。"""
    n, tail, value, same = row
    return ('   ' + str(n).rjust(5) + '      …' + str(tail).rjust(T4_TAIL)
            + '   ' + str(value).rjust(T4_TAIL) + '   ' + str(same))


# ── 第 1 层 · 对拍：两把尺子，同一批数据 ────────────────────────────────

def layer1(loaded):
    label = 'task1_brute_ref.py '
    if not loaded.ok('task1_brute_ref'):
        return [(False, loaded.why(label, 'task1_brute_ref'))]
    out = []
    counts, error = attempt(loaded.fn('task1_brute_ref', 'run_trials'))
    if error is not None:
        out.append((False, with_todo(('task1_brute_ref', 'run_trials'),
                                     'run_trials() 报错' + error_note(error))))
        return out
    if not isinstance(counts, dict):
        out.append((False, with_todo(('task1_brute_ref', 'run_trials'),
                                     'run_trials() 交回的不是字典：' + short(repr(counts), 40)
                                     + '——要交回 {(候选解, 尺子): 组数} 这么一张表')))
        return out

    facts = [
        (('cand_buggy', 'same_idea'), 0,
         '与「同一个思路的参考解」对拍抓到 0 组——它是装饰品，和候选解错在同一个地方；'
         '这一格要是非 0，说明两份代码并不是同一个思路',
         '与「同一个思路的参考解」对拍抓到'),
        (('cand_buggy', 'brute'), 58,
         '与「独立暴力解」对拍抓到 58 组——58 恰好是「全是负数」的那一类数据，'
         '这个 bug 的藏身处就只有那儿',
         '与「独立暴力解」对拍抓到'),
        (('cand_buggy', 'dc'), 58,
         '与「独立分治解」对拍也抓到 58 组——两把独立的尺子抓到的是同一批数据，'
         '它们与候选解的想法毫无关系',
         '与「独立分治解」对拍抓到'),
        (('cand_fixed', 'brute'), 0,
         '反向验证：把 best 的初值改好之后与独立暴力对拍 0 组不一致——'
         '对拍器是活的，前面那个 58 才作数',
         '修好初值之后与独立暴力对拍抓到'),
    ]
    for key, want, good, head in facts:
        if key not in counts:
            out.append((False, with_todo(('task1_brute_ref', 'run_trials'),
                                         'run_trials() 交回的表里没有这一格：' + repr(key)
                                         + '——四个键名都是判分接口，别改')))
            continue
        bad = head + ' ' + str(counts[key]) + ' 组，期望 ' + str(want) + ' 组'
        ok, note = check_count(counts[key], want,
                               todo_of('task1_brute_ref', 'run_trials'), bad)
        out.append((ok, good if ok else note))

    first, error = attempt(loaded.fn('task1_brute_ref', 'first_bad'))
    if error is not None:
        out.append((False, with_todo(('task1_brute_ref', 'first_bad'),
                                     'first_bad() 报错' + error_note(error))))
        return out
    if not (isinstance(first, (tuple, list)) and len(first) == 4):
        out.append((False, with_todo(('task1_brute_ref', 'first_bad'),
                                     'first_bad() 交回的不是四样：' + short(repr(first), 40)
                                     + '——要交回 (组号, 数据, 候选解给的, 独立暴力给的)')))
        return out
    idx, data, got, want_value = first
    problems = []
    if idx != 23:
        problems.append('组号是 ' + short(repr(idx), 20) + '，期望 23'
                        '（按种子 1 从头扫，这一组排在第 24 位，组号从 0 起）')
    if not same_list(data, [-7]):
        problems.append('数据是 ' + short(repr(data), 24) + '，期望 [-7]'
                        '——「最小」那一类：n = 1，循环体一次都不进')
    if got != 0:
        problems.append('「候选解给」是 ' + short(repr(got), 16) + '，期望 0')
    if want_value != -7:
        problems.append('「独立暴力给」是 ' + short(repr(want_value), 16) + '，期望 -7'
                        '——题目只保证子段非空，答案就是这个最大的负数')
    if problems:
        out.append((False, with_todo(('task1_brute_ref', 'first_bad'),
                                     'first_bad() 交回的第一个反例对不上：'
                                     + '；'.join(problems)
                                     + '。判据只能是 cand_buggy(a) 与 ref_brute(a) 比，'
                                       '不许用 ref_same_idea——拿同思路那把尺子找反例，'
                                       '永远找不到')))
    else:
        out.append((True, 'first_bad() 交回第 23 组、数据 [-7]、候选解给 0、独立暴力给 -7'
                          '——本课那个「最小」类边界就是它'))
    return out


def layer1b(loaded):
    """task1 的探针：判分换两个种子、另写三把尺子，看 run_trials 是算出来的还是写死的。"""
    label = 'task1_brute_ref.py '
    if not loaded.ok('task1_brute_ref'):
        return [(False, '探针这一组跳过：先让上面那一条过（' + label + '载入不完整' + RP_CN)]
    out = []
    for seed, trials in PROBE1:
        want, want_first = replay_trials(trials, seed)
        got, error = attempt(loaded.fn('task1_brute_ref', 'run_trials'), trials, seed)
        if error is not None:
            out.append((False, with_todo(('task1_brute_ref', 'run_trials'),
                                         'run_trials(trials=' + str(trials) + ', seed='
                                         + str(seed) + ') 报错' + error_note(error)
                                         + '——两个参数都要真的用上：种子换一个，'
                                           '抽出来的就是另一批数据')))
            continue
        rows = got if isinstance(got, dict) else {}
        diffs = []
        for key in (('cand_buggy', 'same_idea'), ('cand_buggy', 'brute'),
                    ('cand_buggy', 'dc'), ('cand_fixed', 'brute')):
            bad = ('种子 ' + str(seed) + ' 这一批里 ' + repr(key) + ' 这一格是 '
                   + str(rows.get(key)) + ' 组，期望 ' + str(want[key]) + ' 组')
            ok, note = check_count(rows.get(key), want[key],
                                   todo_of('task1_brute_ref', 'run_trials'), bad)
            if not ok:
                diffs.append(note)
        if diffs:
            out.append((False, '拿判分自己的数据（种子 ' + str(seed) + '、' + str(trials)
                               + ' 组）调 run_trials，四格里有对不上的：' + '；'.join(diffs)
                               + '——这几个数是从数据里数出来的，不是脚本里那批数据的数字；'
                                 '判分另写了一份同思路解、一份分治解、一份暴力解来对，'
                                 '只跑一半或者写死常数都会在这里露'))
        else:
            out.append((True, '种子 ' + str(seed) + '、' + str(trials) + ' 组'
                              '（判分自己造的数据）：同思路 0 组 / 暴力 '
                              + str(want[('cand_buggy', 'brute')]) + ' 组 / 分治 '
                              + str(want[('cand_buggy', 'dc')])
                              + ' 组 / 修好之后 0 组——四格与判分另算的一模一样'))
        probe_first, error = attempt(loaded.fn('task1_brute_ref', 'first_bad'),
                                     trials, seed)
        if error is not None:
            out.append((False, with_todo(('task1_brute_ref', 'first_bad'),
                                         'first_bad(trials=' + str(trials) + ', seed='
                                         + str(seed) + ') 报错' + error_note(error))))
        elif want_first is None:
            ok = same_list(probe_first, [None, None, None, None])
            out.append((ok, '这批数据里一个反例都没有，first_bad 照口径交回四个 None'
                        if ok else
                        '这批数据里一个反例都没有，first_bad 交回 '
                        + short(repr(probe_first), 30) + '，期望四个 None'
                        + TODO_MARK + todo_of('task1_brute_ref', 'first_bad')))
        else:
            same = (isinstance(probe_first, (tuple, list)) and len(probe_first) == 4
                    and probe_first[0] == want_first[0]
                    and same_list(probe_first[1], want_first[1])
                    and probe_first[2] == want_first[2]
                    and probe_first[3] == want_first[3])
            head = '第一个反例跟着数据走：第 ' + str(want_first[0]) + ' 组 ' + repr(want_first[1])
            tail = (head + ' 候选解给 ' + str(want_first[2]) + ' 暴力给 ' + str(want_first[3])
                    + '——与判分另扫一遍的一致')
            out.append((same, tail if same else
                        'first_bad(' + str(trials) + ', ' + str(seed) + ') 交回 '
                        + short(repr(probe_first), 46) + '，期望 '
                        + short(repr(want_first), 46) + TODO_MARK
                        + todo_of('task1_brute_ref', 'first_bad')))
    return out


# ── 第 2 层 · 生成器的范围要对 ──────────────────────────────────────────

def layer2(loaded):
    """run_pair 在**判分自己的探针**上算得对（数字写死的会被这一组抓住）。"""
    label = 'task2_generator.py '
    if not loaded.ok('task2_generator'):
        return [(False, loaded.why(label, 'task2_generator'))]
    out = []
    run_pair = loaded.fn('task2_generator', 'run_pair')
    for gen, gen_name in ((gen_any, '允许全负的'), (gen_positive, '只造有正数的')):
        want = probe_runner(gen, T2_TRIALS, T2_SEED)
        got, error = attempt(run_pair, gen)
        if error is not None:
            out.append((False, with_todo(('task2_generator', 'run_pair'),
                                         'run_pair(' + gen_name + ' 那个生成器) 报错'
                                         + error_note(error))))
            continue
        if not isinstance(got, dict):
            out.append((False, with_todo(('task2_generator', 'run_pair'),
                                         'run_pair 交回的不是字典：' + short(repr(got), 40)
                                         + '——要交回 {"caught":…, "groups":…, "first":…}')))
            continue
        problems = []
        bad = (gen_name + '这一批里「抓到 bug 的组数」是 ' + str(got.get('caught'))
               + '，期望 ' + str(want['caught']))
        ok, note = check_count(got.get('caught'), want['caught'],
                               todo_of('task2_generator', 'run_pair'), bad)
        if not ok:
            problems.append(note)
        bad = (gen_name + '这一批里「跑完的组数」是 ' + str(got.get('groups'))
               + '，期望 ' + str(want['groups']))
        ok, note = check_count(got.get('groups'), want['groups'],
                               todo_of('task2_generator', 'run_pair'), bad)
        if not ok:
            problems.append(note)
        first = got.get('first')
        want_first = want['first']
        if want_first is None:
            if first is not None:
                problems.append('这一批一个反例都没有，first 该是 None，交回的是 '
                                + short(repr(first), 30))
        elif not (isinstance(first, (tuple, list)) and len(first) == 4
                  and first[0] == want_first[0] and same_list(first[1], want_first[1])
                  and first[2] == want_first[2] and first[3] == want_first[3]):
            problems.append('first 是 ' + short(repr(first), 40) + '，期望 '
                            + short(repr(want_first), 40))
        if problems:
            out.append((False, '拿 ' + gen_name + '那个生成器（种子 ' + str(T2_SEED)
                               + '、' + str(T2_TRIALS) + ' 组）调 run_pair：'
                               + '；'.join(problems) + TODO_MARK
                               + todo_of('task2_generator', 'run_pair')))
        else:
            extra = ('（第一组就是反例，第 ' + str(want_first[0]) + ' 组）'
                     if want_first else '（一个反例都没有）')
            out.append((True, gen_name + '：run_pair 交出 跑完 ' + str(want['groups'])
                              + ' 组、抓到 ' + str(want['caught']) + ' 组' + extra
                              + '——与判分另数一遍的一致'))
    return out


def layer2b(loaded):
    """探针：换种子、换规模、试 until_bad，看 run_pair 的参数是不是真的在用。"""
    label = 'task2_generator.py '
    if not loaded.ok('task2_generator'):
        return [(False, '探针这一组跳过：先让上面那一条过（' + label + '载入不完整' + RP_CN)]
    out = []
    run_pair = loaded.fn('task2_generator', 'run_pair')

    for seed, trials in PROBE2:
        want = probe_runner(probe_gen_any, trials, seed, n_hi=PROBE2_N_HI)
        # n 的上限是判分接口（脚本里写死的是 rng.randint(1, T1_N_HI)），所以这里
        # 把它当关键字递进去；万一这份实现只肯接四个参数，就退回默认上限再试一次。
        got, error = attempt(run_pair, probe_gen_any, trials, seed, False,
                             n_hi=PROBE2_N_HI)
        probe_note = 'n 上限 ' + str(PROBE2_N_HI)
        if error is not None and 'n_hi' in error:
            want = probe_runner(probe_gen_any, trials, seed, n_hi=T1_N_HI)
            got, error = attempt(run_pair, probe_gen_any, trials, seed, False)
            probe_note = '默认上限 ' + str(T1_N_HI)
        if error is not None:
            out.append((False, with_todo(('task2_generator', 'run_pair'),
                                         'run_pair(gen, trials=' + str(trials) + ', seed='
                                         + str(seed) + ', until_bad=False) 报错'
                                         + error_note(error)
                                         + '——run_pair 的四个参数都要接得住：'
                                           'until_bad 与 n 的上限都是判分接口')))
            continue
        rows = got if isinstance(got, dict) else {}
        bad = ('种子 ' + str(seed) + '、' + probe_note + '、' + str(trials)
               + ' 组里抓到 ' + str(rows.get('caught')) + ' 组，期望 '
               + str(want['caught']) + ' 组')
        ok_caught, note_caught = check_count(rows.get('caught'), want['caught'],
                                            todo_of('task2_generator', 'run_pair'), bad)
        bad = ('这批数据的「跑完的组数」是 ' + str(rows.get('groups')) + '，期望 '
               + str(want['groups']))
        ok_groups, note_groups = check_count(rows.get('groups'), want['groups'],
                                            todo_of('task2_generator', 'run_pair'), bad)
        if ok_caught and ok_groups:
            out.append((True, '判分自己的生成器 + 种子 ' + str(seed) + ' + ' + probe_note
                              + ' + ' + str(trials) + ' 组：抓到 ' + str(want['caught'])
                              + ' 组、跑完 ' + str(want['groups'])
                              + ' 组——数与判分另数一遍的对上，说明 n 的上限与种子'
                                '都在真的用，不是写死的'))
        else:
            out.append((False, (note_caught or note_groups)
                               + '——判分这里的生成器、种子与 n 的上限都与脚本里那一批'
                                 '不同，照抄 33 会在这里露'))

    want_stop = probe_runner(gen_any, T2_TRIALS, T2_SEED, until_bad=True)
    got, error = attempt(run_pair, gen_any, T2_TRIALS, T2_SEED, True)
    if error is not None:
        out.append((False, with_todo(('task2_generator', 'run_pair'),
                                     'run_pair(gen_any, until_bad=True) 报错'
                                     + error_note(error))))
    elif not isinstance(got, dict):
        out.append((False, with_todo(('task2_generator', 'run_pair'),
                                     'run_pair(gen_any, until_bad=True) 交回的不是字典：'
                                     + short(repr(got), 40))))
    else:
        bad = ('until_bad=True 时「抓到几组」是 ' + str(got.get('caught'))
               + '，期望 ' + str(want_stop['caught']))
        ok_caught, note = check_count(got.get('caught'), want_stop['caught'],
                                      todo_of('task2_generator', 'run_pair'), bad)
        bad = ('until_bad=True 时「跑完几组」是 ' + str(got.get('groups'))
               + '，期望 ' + str(want_stop['groups'])
               + '（抓到第一组就该停在第 ' + str(want_stop['groups']) + ' 组）')
        ok_groups, note2 = check_count(got.get('groups'), want_stop['groups'],
                                       todo_of('task2_generator', 'run_pair'), bad)
        if ok_caught and ok_groups:
            out.append((True, 'until_bad=True：跑到第 ' + str(want_stop['groups'])
                              + ' 组就停了，抓到 ' + str(want_stop['caught'])
                              + ' 组——「抓到一个就收工」这一条也是算出来的'))
        else:
            out.append((False, (note or note2)
                               + '——until_bad 为真时要立刻停：换成「if first is not None: '
                                 'break」或者「跑到最后再回头找」都会在这里露'))
    return out


# ── 第 3 层 · 多组数据要清空 ────────────────────────────────────────────

def layer3(loaded):
    """换三组判分自己的数据跑一遍：重点看「第一组对不对」与「有没有真的清」。"""
    label = 'task3_reset.py '
    if not loaded.ok('task3_reset'):
        return [(False, loaded.why(label, 'task3_reset'))]
    out = []
    run_cases = loaded.fn('task3_reset', 'run_cases')

    want_leaky = probe_run_cases(PROBE3_CASES, False, ProbeSolver())
    want_clean = probe_run_cases(PROBE3_CASES, True, ProbeSolver())
    got_leaky, error_a = attempt(run_cases, PROBE3_CASES, False)
    got_clean, error_b = attempt(run_cases, PROBE3_CASES, True)
    if error_a is not None or error_b is not None:
        out.append((False, with_todo(('task3_reset', 'run_cases'),
                                     'run_cases(判分自己的三组数据, 清不清) 报错'
                                     + error_note(error_a) + error_note(error_b))))
    else:
        for got, want, flag, words in ((got_leaky, want_leaky, False, '一组都不清'),
                                       (got_clean, want_clean, True, '每问都清空')):
            if same_list(got, want):
                extra = ('（第一组也在里头：两种跑法的第一组相同）' if flag else '')
                out.append((True, words + '：判分自己造的三组数据交出 ' + str(list(want))
                                  + '——与判分另算一遍的一致' + extra))
            else:
                out.append((False, with_todo(('task3_reset', 'run_cases'),
                                             words + '时交回 ' + short(repr(got), 46)
                                             + '，期望 ' + str(list(want))
                                             + '。判分这三组是按「第一组的答案与后面某一组相等」'
                                               '挑的：' + str(PROBE3_CASES)
                                             + '——「忘了清空」得真的在叠，'
                                               '「每问都清空」得真的每问都调 reset')))
        shape_ok = (isinstance(got_leaky, (list, tuple)) and isinstance(got_clean, (list, tuple))
                    and len(got_leaky) == len(PROBE3_CASES)
                    and len(got_clean) == len(PROBE3_CASES))
        first_seen = (list(got_leaky)[:1] if shape_ok else got_leaky)
        second_seen = (list(got_clean)[:1] if shape_ok else got_clean)
        ok_first = shape_ok and got_leaky[0] == got_clean[0] == want_leaky[0]
        out.append((ok_first,
                    '两种跑法的第 1 组都是 ' + str(want_leaky[0])
                    + '，答案相同——**本课那句「第一组往往是对的」就是这一格**；'
                      '第 2 组起才开始分家（' + str(list(want_leaky)) + ' / '
                    + str(list(want_clean)) + '）'
                    if ok_first else
                    with_todo(('task3_reset', 'run_cases'),
                              '两种跑法的第 1 组没对上：忘了清空给 '
                              + short(repr(first_seen), 20) + '、每问清空给 '
                              + short(repr(second_seen), 20) + '，都该是 '
                              + str(want_leaky[0])
                              + '——第一组对不上说明连累加本身都不对；'
                                '第一组对而后面错，才是这一课那个 bug 的样子')))

    probe_solver = ProbeSolver()
    got, error = attempt(run_cases, PROBE3_CASES, False, probe_solver)
    want_mine = probe_run_cases(PROBE3_CASES, False, ProbeSolver())
    if error is not None:
        out.append((False, with_todo(('task3_reset', 'run_cases'),
                                     'run_cases(cases, False, 判分自己的 Solver) 报错'
                                     + error_note(error)
                                     + '——solver 这个参数要真的用上（别写成 '
                                       'def run_cases(cases, reset_per_case, solver=Solver())：'
                                       '那样缝就堵上了）')))
    else:
        ok = same_list(got, want_mine) and probe_solver.resets == 0
        out.append((ok,
                    '塞给 run_cases 一个判分自己的 Solver：它被问了 '
                    + str(probe_solver.answers) + ' 次、被 reset 了 '
                    + str(probe_solver.resets) + ' 次，交出 ' + short(repr(got), 36)
                    + '——「忘了清空」那一版**一次 reset 都不许有**，'
                      '而且在循环外面补一次 reset 也会在这里露'
                    if ok else
                    with_todo(('task3_reset', 'run_cases'),
                              '塞判分自己的 Solver 进去之后：被问 '
                              + str(probe_solver.answers) + ' 次、被 reset '
                              + str(probe_solver.resets) + ' 次，交出 ' + short(repr(got), 36)
                              + '，期望 ' + str(list(want_mine))
                              + ' 且一次 reset 都没有。reset_per_case 为假时一组都不许清'
                                '（在循环外面补一次也会让「忘了清空」变对，'
                                '这一节的现象就没了）')))

    cases_kept = [list(a) for a in PROBE3_CASES]
    attempt(run_cases, PROBE3_CASES, True)
    out.append((PROBE3_CASES == cases_kept,
                'run_cases 没有改动传进来的那个 cases（交回的是新表）'
                if PROBE3_CASES == cases_kept else
                with_todo(('task3_reset', 'run_cases'),
                          'run_cases 把传进来的 cases 改掉了：现在是 ' + str(PROBE3_CASES)
                          + '，原来是 ' + str(cases_kept) + '——交回的要是一张新 list')))
    return out


def layer3b(loaded):
    """Solver 这个类本身：reset 真的清、answer 真的累加、且不偷偷自己清。"""
    label = 'task3_reset.py '
    if not loaded.ok('task3_reset'):
        return [(False, 'Solver 这一组跳过：先让上面那一条过（' + label + '载入不完整' + RP_CN)]
    out = []
    solver = loaded.fn('task3_reset', 'Solver')
    if solver is None:
        out.append((False, with_todo(('task3_reset', 'Solver'),
                                     '这个文件里没有 Solver 这个名字——它是判分接口，别改名')))
        return out
    try:
        probe_inst = fresh_solver(solver)
    except Exception as exc:
        out.append((False, with_todo(('task3_reset', 'Solver'),
                                     'Solver 起不来：' + type(exc).__name__ + ': ' + str(exc))))
        return out
    if not hasattr(probe_inst, 'answer') or not hasattr(probe_inst, 'reset'):
        out.append((False, with_todo(('task3_reset', 'Solver'),
                                     'Solver 起出来的东西没有 answer / reset 这两个方法——'
                                     '任务 3 要的就是这两个方法加一个 self.total')))
        return out

    def ask(values):
        """起一个**新的** Solver 问一组数据（每次都从头起，免得上一次的状态混进来）。"""
        return lambda: fresh_solver(solver).answer(values)

    def twice():
        s = fresh_solver(solver)
        s.answer([5, 5])
        return s.answer([1])

    def after_reset():
        s = fresh_solver(solver)
        s.answer([5, 5])
        s.reset()
        return s.answer([1])

    first, error = attempt(ask([5, 5]))
    if error is not None:
        out.append((False, with_todo(('task3_reset', 'answer'),
                                     'answer([5, 5]) 报错' + error_note(error))))
    else:
        out.append(check_eq(first, 10, '新起的 Solver 问第一组 [5, 5] 交出 10',
                            with_todo(('task3_reset', 'answer'),
                                      'answer([5, 5]) 交回的数不对')))
    second, error = attempt(twice)
    if error is not None:
        out.append((False, with_todo(('task3_reset', 'answer'),
                                     '连着问两组时报错' + error_note(error))))
    else:
        out.append(check_eq(second, 11,
                            '没人调 reset 时第二组是 11（10 + 1）——状态真的留在外面了，'
                            '这个 bug 才复现得出来',
                            with_todo(('task3_reset', 'answer'),
                                      '没人调 reset 时第二组交回的数不对——answer 里'
                                      '不许自己偷偷把 total 归零，那样「忘了清空」'
                                      '这个 bug 就复现不出来了')))
    third, error = attempt(after_reset)
    if error is not None:
        out.append((False, with_todo(('task3_reset', 'reset'),
                                     '调过 reset 之后 answer 报错' + error_note(error))))
    else:
        out.append(check_eq(third, 1, '调一次 reset 之后再问，交出 1——reset 真的把它清掉了',
                            with_todo(('task3_reset', 'reset'),
                                      '调过 reset 之后 answer 交回的数不对')))
    return out


# ── 第 4 层 · 取模：小数据上看不出来 ────────────────────────────────────

def layer4(loaded):
    """确定值：45 这个分家点、末 14 位那一列、位数 2090、差了 2080 位。"""
    label = 'task4_modulo.py '
    if not loaded.ok('task4_modulo'):
        return [(False, loaded.why(label, 'task4_modulo'))]
    out = []

    got, error = attempt(loaded.fn('task4_modulo', 'first_diff'))
    if error is not None:
        out.append((False, with_todo(('task4_modulo', 'first_diff'),
                                     'first_diff() 报错' + error_note(error))))
    else:
        out.append(check_eq(got, T4_FIRST_N,
                            '第一个分家的 n 是 ' + str(T4_FIRST_N) + '——它是循环比出来的'
                            '（n = 44 两版还相等，n = 45 就不等了）',
                            with_todo(('task4_modulo', 'first_diff'),
                                      'first_diff() 交回的 n 不对')))

    got, error = attempt(loaded.fn('task4_modulo', 'sample_rows'))
    if error is not None:
        out.append((False, with_todo(('task4_modulo', 'sample_rows'),
                                     'sample_rows() 报错' + error_note(error))))
    else:
        want = canonical_rows(T4_ROWS)
        if not isinstance(got, list):
            out.append((False, with_todo(('task4_modulo', 'sample_rows'),
                                         'sample_rows() 交回的不是表：' + short(repr(got), 40))))
        elif len(got) != len(want):
            out.append((False, with_todo(('task4_modulo', 'sample_rows'),
                                         'sample_rows() 交回 ' + str(len(got)) + ' 行，期望 '
                                         + str(len(want)) + ' 行——一个 n 一行')))
        else:
            bad_rows = [i for i, (row, exp) in enumerate(zip(got, want))
                        if not same_list(row, exp)]
            bad_types = [i for i, row in enumerate(got)
                         if isinstance(row, (list, tuple)) and len(row) == 4
                         and not isinstance(row[3], bool)]
            if bad_rows:
                i = bad_rows[0]
                shown = tuple(got[i]) if isinstance(got[i], tuple) else got[i]
                out.append((False, with_todo(('task4_modulo', 'sample_rows'),
                                             'sample_rows() 第 ' + str(i + 1) + ' 行对不上：交回 '
                                             + short(repr(shown), 50) + '，期望 '
                                             + short(repr(want[i]), 50))))
            else:
                out.append((True, '六行都在：n=' + '、'.join(str(n) for n in T4_ROWS)
                                  + '，各自的末 14 位、取模值、两版相等吗都与判分另算一遍的'
                                    '一致（n ≤ 30 那两行是 True，n ≥ 50 起是 False）'))
            if bad_types:
                i = bad_types[0]
                row = got[i]
                out.append((False, with_todo(('task4_modulo', 'sample_rows'),
                                             'sample_rows() 第 ' + str(i + 1) + ' 行第四格是 '
                                             + repr(row[3]) + '（' + type(row[3]).__name__
                                             + '）——「两者相等吗」这一格要是 True / False 本身，'
                                               '不是 1 / 0、也不是字符串')))
            elif not bad_rows:
                out.append((True, '第四格都是真的布尔值——这一列就是这一节的全部信息量'))

    got, error = attempt(loaded.fn('task4_modulo', 'big_digits'))
    if error is not None:
        out.append((False, with_todo(('task4_modulo', 'big_digits'),
                                     'big_digits() 报错' + error_note(error))))
    else:
        want_bits = fib_count(T4_BIG)
        bad = ('big_digits() 交回 ' + str(got) + ' 位，期望 ' + str(want_bits)
               + ' 位（不取模那一版的位数，别写成 len(str(fib_mod(n)))）')
        ok, note = check_count(got, want_bits,
                               todo_of('task4_modulo', 'big_digits'), bad)
        out.append((ok, '不取模在 n = ' + str(T4_BIG) + ' 时是 ' + str(want_bits)
                        + ' 位——与 tools.fib_count 这个另一个写法一致')
                   if ok else (False, note))
        out.append(check_eq(got, 2090, '2090 位这个数也对上了课件那张表',
                            with_todo(('task4_modulo', 'big_digits'),
                                      '位数与课件那张表的 2090 不一致')))

    got, error = attempt(loaded.fn('task4_modulo', 'gap_cell'))
    if error is not None:
        out.append((False, with_todo(('task4_modulo', 'gap_cell'),
                                     'gap_cell() 报错' + error_note(error))))
    else:
        out.append(check_eq(got, 2080,
                            '「两版差了 2080 位」——2090 减掉取模之后最多可能的 10 位；'
                            '同一条口径在大表上是 10 位以内，在 n = 30 上却逐字相同',
                            with_todo(('task4_modulo', 'gap_cell'),
                                      'gap_cell() 交回的数不对')))

    checks = [('random_bad', '两版不相等的组数', 3, 300, 21, 120),
              ('random_first', '第一组不相等的 n', 3, 300, 21, 120)]
    for func_name, words, seed, trials, lo, hi in checks:
        got, error = attempt(loaded.fn('task4_modulo', func_name))
        if error is not None:
            out.append((False, with_todo(('task4_modulo', func_name),
                                         func_name + '() 报错' + error_note(error))))
            continue
        if func_name == 'random_bad':
            want_value = probe_random_bad(seed, trials, lo, hi)
            good = ('种子 ' + str(seed) + '、' + str(trials) + ' 组、n 在 ' + str(lo)
                    + '..' + str(hi) + '：两版不相等的有 ' + str(want_value)
                    + ' 组——与判分另数一遍的一致')
        else:
            want_value = probe_random_first(seed, trials, lo, hi)
            good = '同一批 n 里第一个不相等的 n 是 ' + str(want_value)
        ok, note = check_eq(got, want_value, good,
                            with_todo(('task4_modulo', func_name),
                                      func_name + '() 交回的' + words + '不对'))
        out.append((ok, good if ok else note))
    return out


def layer4b(loaded):
    """探针：判分自己选的 n 与末 14 位（44 / 45 / 46 那三个点单独试）。"""
    label = 'task4_modulo.py '
    if not loaded.ok('task4_modulo'):
        return [(False, '探针这一组跳过：先让上面那一条过（' + label + '载入不完整' + RP_CN)]
    out = []

    got, error = attempt(loaded.fn('task4_modulo', 'first_diff'), 41, 60)
    if error is not None:
        out.append((False, with_todo(('task4_modulo', 'first_diff'),
                                     'first_diff(41, 60) 报错' + error_note(error))))
    else:
        out.append(check_eq(got, T4_FIRST_N,
                            'first_diff(41, 60) 交出 45——把区间挪到 45 附近它照样找得到'
                            '（44 还相等、45 就不等）',
                            with_todo(('task4_modulo', 'first_diff'),
                                      'first_diff(41, 60) 交回的不对——循环要从 lo 走到 hi'
                                      '（含 hi），不能写死 45')))
        start, error = attempt(loaded.fn('task4_modulo', 'first_diff'), 45, 60)
        out.append((error is None and start == 45,
                    'first_diff(45, 60) 交出 45——区间左端正好落在分家点上也没问题'
                    if error is None and start == 45 else
                    with_todo(('task4_modulo', 'first_diff'),
                              'first_diff(45, 60) 交回 ' + short(repr(start), 20)
                              + '，期望 45（区间两端都要算进去）' + error_note(error))))
        none_case, error = attempt(loaded.fn('task4_modulo', 'first_diff'), 1, 44)
        out.append((error is None and none_case is None,
                    'first_diff(1, 44) 交出 None——这一段里一个分家的 n 都没有，'
                    '要按口径交回 None，不是 0、也不是报错'
                    if error is None and none_case is None else
                    with_todo(('task4_modulo', 'first_diff'),
                              'first_diff(1, 44) 交回 ' + short(repr(none_case), 20)
                              + '，期望 None（这一段里两版一直相等）' + error_note(error))))

    for x in PROBE4_TAILS:
        value = None if x is None else fib_nomod(x)
        got, error = attempt(loaded.fn('task4_modulo', 'tail14'), value)
        want = canonical_tail(value)
        why = ('x 是 None 时要原样交回 None，别去 str(None)' if x is None else
               'n = 44 时两版还相等，这一格也一样' if x == 44 else
               'n = 45 起两版就分家了，这一格正是「末几位还一样、整体已经不一样」'
               if x == 45 else
               '末 14 位就是从整个数上切尾巴——不用先算取模再来切')
        out.append((error is None and got == want,
                    'tail14(' + short(repr(value), 20) + ') 交出 ' + repr(want) + '——' + why
                    if error is None and got == want else
                    with_todo(('task4_modulo', 'tail14'),
                              'tail14(' + short(repr(value), 20) + ') 交回 '
                              + short(repr(got), 30) + '，期望 ' + repr(want)
                              + error_note(error))))

    rows, error = attempt(loaded.fn('task4_modulo', 'sample_rows'), PROBE4_DIGITS)
    if error is not None:
        out.append((False, with_todo(('task4_modulo', 'sample_rows'),
                                     'sample_rows(判分自己那组 n) 报错' + error_note(error))))
    else:
        want = canonical_rows(PROBE4_DIGITS)
        if not same_list(rows, want):
            out.append((False, with_todo(('task4_modulo', 'sample_rows'),
                                         first_bad_place(rows, want, 'sample_rows(判分那组 n)')
                                         + '——判分这组 n 里有 44 / 45 / 46 三个贴着分家点的，'
                                           '与脚本那六档都不一样')))
        else:
            out.append((True, '拿判分自己选的 ' + str(list(PROBE4_DIGITS))
                              + ' 调 sample_rows：每一行的四格都对上了，'
                                '其中 n = 44 是 True、n = 45 与 46 是 False'
                              + '——分家点就在这两行之间'))

    for n in PROBE4_DIGITS:
        got, error = attempt(loaded.fn('task4_modulo', 'big_digits'), n)
        want = fib_count(n)
        out.append((error is None and got == want,
                    'big_digits(n=' + str(n) + ') 交出 ' + str(want)
                    + ' 位——与「一边递推一边数位数」那个写法一致'
                    if error is None and got == want else
                    with_todo(('task4_modulo', 'big_digits'),
                              'big_digits(n=' + str(n) + ') 交回 ' + short(repr(got), 20)
                              + '，期望 ' + str(want) + ' 位' + error_note(error))))

    got, error = attempt(loaded.fn('task4_modulo', 'sample_rows'), [])
    out.append((error is None and same_list(got, []),
                '样本表那一格：sample_rows([]) 交出空表（没让判分崩）'
                if error is None and same_list(got, []) else
                with_todo(('task4_modulo', 'sample_rows'),
                          'sample_rows([]) 交回 ' + short(repr(got), 30)
                          + '，期望 []' + error_note(error))))

    for seed, trials, lo, hi in PROBE4_RANDY:
        got_bad, error_a = attempt(loaded.fn('task4_modulo', 'random_bad'),
                                   seed, trials, lo, hi)
        got_first, error_b = attempt(loaded.fn('task4_modulo', 'random_first'),
                                     seed, trials, lo, hi)
        want_bad = probe_random_bad(seed, trials, lo, hi)
        want_first = probe_random_first(seed, trials, lo, hi)
        ok = (error_a is None and error_b is None and got_bad == want_bad
              and got_first == want_first)
        head = ('种子 ' + str(seed) + '、' + str(trials) + ' 组、n 在 ' + str(lo)
                + '..' + str(hi) + '：')
        out.append((ok, head + '不相等 ' + str(want_bad) + ' 组、第一个是 n = '
                        + repr(want_first) + '——两个函数都把参数真的用上了'
                  if ok else
                  with_todo(('task4_modulo', 'random_bad'),
                            head + '交回 ' + short(repr(got_bad), 16) + ' 组 / 第一个 '
                            + short(repr(got_first), 16) + '，期望 ' + str(want_bad)
                            + ' 组 / ' + repr(want_first) + error_note(error_a)
                            + error_note(error_b)
                            + '——seed / trials / lo / hi 四个参数都要接住')))
    return out


# ── 第 5 层 · 打印行、单跑、文件没被动过 ────────────────────────────────

def run_script(path):
    """起一个子进程跑一个任务脚本 → (退出码, stdout, stderr)。"""
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    try:
        done = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(path)],
                              cwd=str(path.parent), capture_output=True, text=True,
                              encoding='utf-8', errors='replace', timeout=180, env=env)
    except Exception as exc:
        return None, '', '起不了子进程：' + type(exc).__name__ + ': ' + str(exc)
    return done.returncode, done.stdout or '', done.stderr or ''


def parse_rows(text):
    """把四个脚本的输出读成 [(原行, 去掉行首空白与「→」), …]。小节标题行不要。

    四个脚本都用「→」标出「这一行是结论」，它顶在行首、不是标签的一部分，
    所以先摘掉——不摘的话按标签前缀比对时会被它挡住（「→ 与「独立暴力解」…」
    并不以「与「独立暴力解」…」开头）。
    """
    rows = []
    for raw in text.splitlines():
        head = raw.strip()
        if head.startswith('→'):
            head = head[1:].strip()
        if not head or head.startswith('=='):
            continue                                   # 小节标题不是「标签 值」
        rows.append((raw, head))
    return rows


def pick_count(line):
    """「… 300 组里抓到 bug 的有 0 组」这种句子里的那个数——取末尾的「N 组」。

    句子里还有一个 300，所以不能取第一个数；末尾的「N 组」才是「抓到几组」。
    """
    pieces = line.split()
    for i in range(len(pieces) - 1, 0, -1):
        if pieces[i] == '组' and pieces[i - 1].isdigit():
            return pieces[i - 1]
    return None


def norm_label(text):
    """把标签末尾的冒号去掉，用来比较。"""
    text = text.strip()
    return text[:-1] if text.endswith(':') else text


def label_of(head, labels):
    """这一行是不是以 labels 里的某一个开头 → 命中的标签写法（原样），否则 None。

    长标签优先：task3 里「忘了清空对吗:」必须比「忘了清空」先命中。
    末尾冒号可有可无（脚本里一列一列那几行的冒号是右对齐垫出来的，
    task3 / task4 的冒号则贴着标签），所以两边的冒号都去掉再比。
    """
    hit = None
    for label in labels:
        if norm_label(head).startswith(norm_label(label)):
            if hit is None or len(label) > len(hit):
                hit = label
    return hit


def take_after(line, label):
    """标签之后剩下的那一段：跳掉对齐空白与可能出现的冒号 / 等号，再去掉两端空白。

    「在第 23 组」→ label「在第」→「23 组」
    「三组数据      : [[1, 2, 3], …]」→ label「三组数据」→「[[1, 2, 3], …]」
    「不一致的        : 58 组」→ label「不一致的」→「58 组」
        注意标签与冒号之间垫着对齐空白：先跳空白、再跳冒号，顺序反了会留下「: …」。
    「MOD = 1,000,000,007」→ label「MOD」→「1,000,000,007」
    「忘了清空对吗: False    每问清空对吗: True」→ label →「False …」
    「→ 两组各自的第 1 组: 忘了清空 6 / …」→ label 带着「→」→「忘了清空 6 / …」
    """
    rest = line[len(label):].lstrip()
    for _ in range(2):
        # 先跳空白（上面已做过），再跳一个冒号 / 等号；对齐用的空白可能反复出现
        if rest[:1] in (':', '=') and not rest[1:2].isdigit():
            rest = rest[1:]
        rest = rest.lstrip()
    return rest.strip()


def looks_like_detail(head):
    """这一行是不是「第 N 组 …」那种逐组明细行。

    明细行形如「第 2 组 n=7 数据 [3, 7, …] 候选解给 32 暴力解给 32 一致吗 True」，
    里面重名地带了「数据 / 候选解给」这些与真标签一样的词；task2 那几行前面
    还挂着一个生成器名字（「只造有正数的 第 2 组 …」）。所以判据是
    「这一行里有没有『第 + 数字 + 组』这个连着的形状」——有就是明细行，
    真正的标签行不会有它（「在第 23 组」里的「第 23 组」中间隔着空格，
    连着切不出「第」「23」「组」三段，所以不受影响）。
    """
    pieces = head.split()
    for i in range(len(pieces) - 2):
        if pieces[i] == '第' and pieces[i + 1].isdigit() and pieces[i + 2] == '组':
            return True
    return False


# 取值方式一：标签之后那一段有东西可取（task1 的几行结论、task3 / task4 的那些行）。
# 次序不要紧（label_of 自己会挑最长的那一个），但都写全：
#   · task1 的「与…对拍，不一致的」那四行是右对齐的，标签与冒号之间垫着空白；
#   · task3 的「忘了清空对吗:」必须比「忘了清空」长，label_of 靠长度挑，不会切错。
VALUE_LABELS = ('两组各自的第 1 组:',
                '与「同一个思路的参考解」对拍，不一致的',
                '修好初值（best 从 -inf 起步）之后，与独立暴力对拍不一致的',
                '与「独立暴力解」对拍，不一致的',
                '与「独立分治解」对拍，不一致的',
                '第一个分家的 n（两版从这里开始不等）',
                '不取模在 n = 10000 时的位数:',
                '其中两版不相等的组数:',
                '第一组不相等的 n:',
                '忘了清空对吗:',
                'MOD',
                '三组数据', '忘了清空', '每问都清空', '正确答案',
                '在第', '出现在第', '数据', '候选解给', '独立暴力给')

# 取值方式二：标签之后剩的是「内容 + 标签」那种句子里的**数**（值在标签前面）。
# 判据是「标签 + 空格 + 内容 + 空格 + 数字 + 空格 + 组」——明细行也会命中这个形状，
# 所以取值之前先把明细行挡掉（见 looks_like_detail）。
COUNT_LABELS = ('只造有正数的', '允许全负的')

# 取值方式三：标签只是一段开头，值就是标签之后**整段**（task4 最后一行）。
PREFIX_LABELS = ('取模后的值最多 10 位——两版差了',)


def parse_shown(text):
    """把四个脚本的打印行读成 {标签: 值}。

    四个文件里的行有四种形状，取值的方式各不相同：

      · 一列一列、值在行末（task1 与 task4 那几行是右对齐的）：
            与「独立暴力解」对拍，不一致的        : 58 组      → '58 组'
            第一个分家的 n（两版从这里开始不等）: 45          → '45'
        标签与冒号之间垫着对齐空白，所以按「行末那一段」取——但「组数」那种值
        末尾可能带单位，于是取「最后一个数字 + 后面跟着的词」。

      · 一列一列、值就在标签后面（task3 / task4 那几行）：
            在第 23 组                                       → '23 组'
            三组数据      : [[1, 2, 3], [10, 20], [5]]       → '[[1, 2, 3], …]'
            MOD = 1,000,000,007                              → '1,000,000,007'

      · 值在标签**前面**（task2 的两行摘要）：
            只造有正数的 300 组里抓到 bug 的有 0 组          → '0 组'
            允许全负的 300 组里抓到 bug 的有 33 组           → '33 组'
        句子中间还有另一个数（300），所以要取**末尾**那个「N 组」。

      · 标签只是一段开头、值在后面跟着（task4 最后一行）：
            取模后的值最多 10 位——两版差了 2080 位，在 n = 30 上却逐字相同
                                                            → '2080 位，在 n = 30 上却逐字相同'

    两处容易踩空的坑：
      · 四个脚本里都有「第 N 组 …」这种**逐组明细**行（「只造有正数的 第 2 组
        n=7 数据 …」）。它不是「标签 值」，取值之前先按「第 数字 组」这个形状摘掉，
        否则明细行会把真正那一行的值覆盖掉。
      · task3 里「忘了清空」与「忘了清空对吗:」是一对前缀，长标签必须先生效
        （所以按标签长度从长到短试）。
    """
    rows = {}
    for raw, head in parse_rows(text):
        if looks_like_detail(head):
            continue                       # 「第 N 组 …」明细行，不是「标签 值」
        norm = norm_label(head)
        # 第三种形状：值在标签前面
        for label in COUNT_LABELS:
            if head.startswith(label + ' '):
                value = pick_count(head)
                if value is not None:
                    rows[label] = value + ' 组'
        # 第二种形状：标签只是一段开头，值就是后面整段
        for label in PREFIX_LABELS:
            if head.startswith(label + ' '):
                rows[label] = take_after(head, label)
        # 第一种形状：标签之后紧跟着值
        hit = label_of(head, VALUE_LABELS)
        if hit is not None:
            rows[hit] = take_after(head, hit)
    return rows


def tools_same_as_handout():
    """这个目录里的 tools.py 与发下来那一份逐字节相同吗 → (一样吗, 说明)。"""
    global TOOLS_CANON
    path = HERE / 'tools.py'
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return False, '读不了 tools.py：' + str(exc)
    digest = hashlib.sha256(raw).hexdigest().upper()
    text = raw.decode('utf-8', errors='replace')
    if TOOLS_CANON is None:
        TOOLS_CANON = {'sha': digest, 'len': len(raw)}
    if digest.startswith(TOOLS_SHA256):
        return True, ('tools.py 与发下来那一份逐字节相同（' + str(TOOLS_CANON['len'])
                      + ' 字节、SHA256 ' + digest[:16] + '…）——本课那几组实测数字全靠它')
    if FENCE in text:
        return False, ('tools.py 里出现了连续三个反引号——本 lab 的源码里不许有它'
                       '（会打断阅卷与工具链）。要说明拼接方式就用 ' + repr('`') + ' * 3')
    return False, ('tools.py 已经被改过了（现在是 ' + str(len(raw)) + ' 字节、SHA256 '
                   + digest[:16] + '…，发下来那一份是 ' + str(TOOLS_CANON['len'])
                   + ' 字节、' + TOOLS_SHA256 + '…）。它是**给好的公共工具**：'
                     '候选解、两把独立的尺子、随机口径、MOD 与那几档 n 都在里面，'
                     '改一个字，58 组 / 33 组 / 2090 位就对不上了。改回来再跑：'
                     '从任务目录外拿一份原始的 tools.py 覆盖掉它')


def layer5(loaded):
    runs = [run_script(HERE / name) for name in TASK_FILES]
    out = []

    # 5a · 四个脚本各自单跑：退出码 0、没有 Traceback
    for name, (code, text, err) in zip(TASK_FILES, runs):
        if code is None:
            out.append((False, name + ' 起不了子进程：' + short(err, 80) + TODO_MARK
                               + name + ' 里还没补的那一段 TODO'))
        elif 'Traceback' in err or 'Traceback' in text:
            tail = (err or text).strip().splitlines()
            out.append((False, name + ' 单跑时抛了异常，最后一行是 ' + short(tail[-1], 70)
                               + '——每个任务文件都要能**单独跑通**'
                                 '（退出码 0、0 处 Traceback），判分也是按文件 import 的'
                               + TODO_MARK + name + ' 里还没补的那一段 TODO'))
        elif code != 0:
            out.append((False, name + ' 单跑的退出码是 ' + str(code) + '，期望 0'
                               + TODO_MARK + name + ' 里还没补的那一段 TODO'))
        else:
            extra = ('（' + str(len(text.splitlines())) + ' 行输出）' if text else '')
            out.append((True, name + ' 单跑退出码 0、0 处 Traceback' + extra))

    # 5b · 这个目录里的 tools.py 与发下来那一份逐字节相同吗
    same_tools, note_tools = tools_same_as_handout()
    out.append((same_tools, note_tools))

    # 5c · 逐字读四个脚本打印出来的行
    t1 = parse_shown(runs[0][1])
    t2 = parse_shown(runs[1][1])
    t3 = parse_shown(runs[2][1])
    t4 = parse_shown(runs[3][1])

    def shown(rows, wanted):
        """按标签取值，容忍两种写法上的差别：

          · 末尾那个冒号有也行、没有也行——task1 / task4 的标签与冒号之间垫着
            对齐空白，那个冒号是「一列一列对齐」用的，不算标签的一部分；
          · 「→」有也行、没有也行——脚本用它在行首标出「这一行是结论」，
            parse_rows 已经把它摘掉了，这里再兜一层。
        """
        def bare(text):
            return norm_label(text).lstrip('→ ').strip()

        want = bare(wanted)
        for label, value in rows.items():
            if bare(label) == want:
                return value
        return None

    # 每一行的标签（不带末尾冒号）→ 期望的值
    exact1 = [
        ('与「同一个思路的参考解」对拍，不一致的', '0 组', 'run_trials'),
        ('与「独立暴力解」对拍，不一致的', '58 组', 'run_trials'),
        ('与「独立分治解」对拍，不一致的', '58 组', 'run_trials'),
        ('修好初值（best 从 -inf 起步）之后，与独立暴力对拍不一致的', '0 组', 'run_trials'),
        ('在第', '23 组', 'first_bad'),
        ('数据', '[-7]', 'first_bad'),
        ('候选解给', '0', 'first_bad'),
        ('独立暴力给', '-7', 'first_bad'),
    ]
    for key, want, owner in exact1:
        todo = todo_of('task1_brute_ref', owner)
        got = shown(t1, key)
        if got is None:
            out.append((False, 'task1 的输出里没有「' + key + '」这一行——'
                               '打印行是判分接口，别改它们' + TODO_MARK + todo))
            continue
        bad = ('task1 的「' + key + '」是 ' + short(repr(got), 30) + '，期望 ' + want
               + TODO_MARK + todo)
        out.append(check_line(got, [want],
                              'task1 的「' + key + '」是 ' + want + '（与课件那一组实测一致）',
                              bad))

    for key, want in (('只造有正数的', '0 组'), ('允许全负的', '33 组')):
        todo = todo_of('task2_generator', 'run_pair')
        got = shown(t2, key)
        if got is None:
            out.append((False, 'task2 的输出里没有「' + key + '」这一行——'
                               '打印行是判分接口，别改' + TODO_MARK + todo))
            continue
        out.append(check_line(got, [want],
                              'task2 的「' + key + '」那一行是 ' + want
                              + '——同一个 bug、同一个对拍器、同样 300 组，'
                                '只换了生成器的范围',
                              'task2 的「' + key + '」那一行对不上' + TODO_MARK + todo))

    exact3 = [
        ('三组数据', '[[1, 2, 3], [10, 20], [5]]'),
        ('忘了清空', '[6, 36, 41]'),
        ('每问都清空', '[6, 30, 5]'),
        ('正确答案', '[6, 30, 5]'),
        ('忘了清空对吗:', 'False    每问清空对吗: True'),
        ('两组各自的第 1 组:', '忘了清空 6 / 每问清空 6 / 期望 6'),
    ]
    for key, want in exact3:
        todo = todo_of('task3_reset', 'run_cases')
        got = shown(t3, key)
        if got is None:
            out.append((False, 'task3 的输出里没有「' + key + '」这一行——'
                               '打印行是判分接口，别改' + TODO_MARK + todo))
            continue
        out.append(check_line(got, [want],
                              'task3 的「' + key + '」逐字对上：' + want,
                              'task3 的「' + key + '」对不上' + TODO_MARK + todo))

    exact4 = [
        ('MOD', '1,000,000,007'),
        ('第一个分家的 n（两版从这里开始不等）', '45'),
        ('其中两版不相等的组数', '239'),
        ('第一组不相等的 n', '51'),
        ('不取模在 n = 10000 时的位数', '2090 位'),
        ('取模后的值最多 10 位——两版差了', '2080 位，在 n = 30 上却逐字相同'),
    ]
    for key, want in exact4:
        todo = todo_of('task4_modulo', 'big_digits')
        got = shown(t4, key)
        if got is None:
            out.append((False, 'task4 的输出里没有「' + key + '」这一行——'
                               '打印行是判分接口，别改' + TODO_MARK + todo))
            continue
        bad = ('task4 的「' + key + '」是 ' + short(repr(got), 30) + '，期望 ' + want
               + TODO_MARK + todo)
        out.append(check_line(got, [want],
                              'task4 的「' + key + '」逐字对上：' + want, bad))

    # 那张六行的表要逐字对上（判分拿同一批 n 把每一行重拼一遍）
    body = [line for line in runs[3][1].splitlines()
            if line.startswith('   ') and '…' in line]
    want_lines = [row_text(row) for row in canonical_rows(T4_ROWS)]
    todo = todo_of('task4_modulo', 'sample_rows')
    if len(body) != len(want_lines):
        out.append((False, 'task4 那张表的行数是 ' + str(len(body)) + '，期望 '
                           + str(len(want_lines)) + ' 行（一个 n 一行）' + TODO_MARK + todo))
    else:
        bad_rows = [i for i, (got, want) in enumerate(zip(body, want_lines))
                    if got != want]
        if bad_rows:
            i = bad_rows[0]
            out.append((False, 'task4 那张表第 ' + str(i + 1) + ' 行对不上：'
                               + repr(body[i]) + '，期望 ' + repr(want_lines[i])
                               + '——四格的顺序是「n、末 14 位、取模值、相等吗」，'
                                 '末 14 位那一列前面有一个省略号' + TODO_MARK + todo))
        else:
            out.append((True, 'task4 那张表六行逐字对上（连省略号与对齐都在）：n ∈ '
                              + '、'.join(str(n) for n in T4_ROWS)
                              + '——n ≤ 30 两版相等，n ≥ 50 起不等'))
    return out


def layer5b(loaded):
    """**源码**里不许有连续三个反引号（本目录的 .py 扫一遍），四个任务文件也不许是空的。

    只扫 .py：README.md 是讲这一课的文档，里面的代码块本来就要用围栏（本课
    与其他几课的 README 都这么写）；这条规矩管的是**源码**——围栏出现在 .py 里
    会打断阅卷与工具链。要拼围栏就用 FENCE = '`' * 3 这种写法，或者用字符串拼接。
    """
    out = []
    hits = []
    for path in sorted(HERE.glob('*.py')):
        text = path.read_text(encoding='utf-8')
        if FENCE in text:
            hits.append(path.name)
    out.append((not hits,
                '这个目录里的 .py 源码一个连续三个反引号都没有（README 那种文档不算）'
                if not hits else
                '这几个 .py 源码里出现了连续三个反引号：' + '、'.join(hits)
                + '——本 lab 的源码里不许有它（会打断阅卷与工具链）。'
                  '要拼围栏就写 ' + repr('`') + ' * 3 或者用字符串拼接'))

    empty = []
    for name in TASK_FILES:
        module = loaded.modules.get(name[:-3])
        if module is None:
            continue
        source = Path(module.__file__).read_text(encoding='utf-8')
        if not source.strip():
            empty.append(name)
    out.append((not empty,
                '四个任务文件都不是空文件' if not empty else
                '这几个任务文件是空的：' + '、'.join(empty)))
    return out


# ── 主流程 ──────────────────────────────────────────────────────────────

LAYERS = [
    ('第 1 层 · 对拍：两把尺子，同一批数据', [layer1, layer1b],
     'task1_brute_ref.py 的 TODO 1（run_trials）与 TODO 2（first_bad）'),
    ('第 2 层 · 生成器的范围要对', [layer2, layer2b],
     'task2_generator.py 的 TODO（run_pair）'),
    ('第 3 层 · 多组数据要清空', [layer3, layer3b],
     'task3_reset.py 的 TODO 1（class Solver）与 TODO 2（run_cases）'),
    ('第 4 层 · 取模：小数据上看不出来', [layer4, layer4b],
     'task4_modulo.py 的 TODO 1 / 2 / 3 / 4'
     '（first_diff、tail14、sample_rows、big_digits）'),
    ('第 5 层 · 打印行、单跑、文件没被动过', [layer5, layer5b],
     '四个脚本里的 TODO——这一层读的是它们打印出来的行，所以那些 print 别改'),
]


def main():
    print('StudyMate lab 0030 · 自动判分（交卷之前你要检查什么）')
    print('目录：' + str(HERE))
    print()
    loaded = Loaded()
    passed = 0
    failed = 0
    layers_ok = 0
    for title, checks, todo_scope in LAYERS:
        print(title)
        layer_ok = True
        for check in checks:
            try:
                results = check(loaded)
            except Exception:                             # 判分自己也不许崩
                results = [(False, '判分自己这一组抛了异常，把下面这段贴给教练：\n'
                                   + traceback.format_exc())]
            for ok, message in results:
                if not ok and TODO_MARK not in message:
                    message = message + '  → 这一层要补的是 ' + todo_scope
                print('  ' + ('PASS' if ok else 'FAIL') + '  ' + message)
                if ok:
                    passed += 1
                else:
                    layer_ok = False
                    failed += 1
        if layer_ok:
            layers_ok += 1
        print('  → 这一层' + ('过了' if layer_ok else '还没过'))
        print()

    print('─' * 60)
    print('五层：' + str(layers_ok) + ' 层通过、' + str(len(LAYERS) - layers_ok) + ' 层还没过'
          + '（共 ' + str(passed) + ' 条 PASS、' + str(failed) + ' 条 FAIL）')
    if failed == 0:
        print('五层全过。现在去对照 ../solutions/0030-stress-test-and-review/：')
        print('比一比四个现象各自是怎么被量出来的，再拿课件那份八条的清单回查三道做错的题。')
        return 0
    print('卡住了先读 ../README.md 的自查清单，再看每条 FAIL 后面点出的那一段 TODO。')
    print('判分读的就是四个脚本打印出来的行，也别改那些 print；tools.py 是给好的，别改。')
    print('全部过了再对照 ../solutions/0030-stress-test-and-review/。')
    return 1


if __name__ == '__main__':
    sys.exit(main())
