#!/usr/bin/env python3
r"""lab 0029 · 自动判分（常数因子优化：先量再动）

用法（在 0029 这个任务目录里直接跑）：

    py run_tests.py

判法：**五层**，一层里几条检查各自给 PASS / FAIL。每一层都靠**两路证据**：

    第一路  跑四个脚本、读它们自己打印的那些行（那些行是接口）。
    第二路  另起一个进程 import 学生的函数，拿**判分自己的**数据试一遍。
            探针的数据与被测脚本里那份**刻意不同**（种子、规模都换过），
            所以「只写 print、不写实现」拿不到 PASS。

这一课的特殊之处：**量的是常数因子，最容易被耗时波动坑**（第 26 课就栽在这里，
留白版的分项计数在 32/88 与 31/89 之间抖）。所以本判分把判据分成两层，
权重完全不同：

    主判据（确定量）  「操作次数 / 循环次数 / 相等比较次数 / 读入调用次数 / 值访问次数」。
                      同一台机器上每次都是同一个整数，判分核的就是它。
    辅助量（参考量）  耗时。只留两处，而且一定带两层保护：
                      ① 噪声容差（>= 0.75 倍）；② 退化守卫（基线 < 1e-4 秒不判，
                      占位计时全是 0.000000 时直接 FAIL 而不是「0 跟 0 比」）。
                      见 tools.judge_guard。
    第三条路（不依赖时钟的因果证据）  同一件事跑若干遍，数一数优化版让**读入器被调了
                      几次**。次数差在那，快的过程就别指望时钟来证明——这一条不会被
                      机器快慢影响，也不会抖。

五层各验什么：

    第 1 层 · 分段计时与「不看形状，看次数」
        三段各多少次操作（判分拿**另两组规模**复算）、原以为最慢的与实测的不是同一段、
        `size()` 被调 n + 1 次而不是 n 次、两段在判分自己的数据上交回同一个命中数。
        再另起探针：拿判分自己的规模调一遍（写死的数在这里会露）。

    第 2 层 · 四招优化，每一招都留记录
        每一级四格**确定量**（循环次数、相等比较次数、读入次数、建集合次数）逐级对照；
        读入那一格还要核对**读入器的账目**（0-1 级逐行 size 次、2 级起整体读 1 次）；
        四级答案一致，而且要「一致地不等于 0」（把 0 写死也算一致，所以这一条也要核）。
        耗时只做两件事：退化守卫（四级全 0.000000 就 FAIL）+ 换容器那一处的噪声容差。

    第 3 层 · 和内置实现比，并说清差在哪一层
        五栏的答案两边一致、值访问次数按规模算对、layer_of 的关键词对得上；
        递归那两栏记住的是**机制**（边界那个 n 撑得住、再深一层就 RecursionError），
        不是一个写死的 998。

    第 4 层 · 故意写错一次：对拍抓不抓得住
        count_matches 在判分自己的五组数据上（含空数组、单元素）两版答案对得上；
        坏的那一版在 50 组固定数据上必须被抓到至少一组、而且带得出证据；
        改回来之后不一致组数是 0。判分自己另算一遍，不吃脚本里那个数。

    第 5 层 · 四个脚本能单独跑、打印行数与参考解一致、耗时不是占位值
        逐个单跑（退出码 0、0 处 Traceback），核对行数，再核对计时那几行
        至少有一格不是 0.000000。行数写死在这儿，是为了让「多打一行 / 少打一行」也报出来。

判分不判的东西：注释写得多不多、变量名叫得好不好、倍率好不好看，
由 lab/README.md 的自查清单与课件那一节回答；这里只管跑不跑得动、口径对不对、
结论是不是算出来的。

退出码：五层都过是 0；还有没过的（或跳过的）是 1。
"""

from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import tools as judge                                     # noqa: E402  给好的，别改
from tools import (DATA, FLOOR, JUDGE_DATA, JUDGE_SEG, LCG, LEVELS, NOISE,  # noqa: E402
                   PROBE_INTERFACE, PROBE_SENTINEL, SEG, SEGMENTS, TIERS,
                   WORK_REPEATS, WORK_SIZES, audit_cases, canonical_answer_of,
                   canonical_count, canonical_trace_table, input_text,
                   sample_data, segment_ops_canonical)

TASK_FILES = ['task1_bottleneck.py', 'task2_tuning.py', 'task3_builtin.py',
              'task4_break_it.py']

# 判分探针自己的那组规模与种子：与脚本里那份**刻意不同**（脚本用 SEG / DATA）。
PROBE_SEED = 2718281
PROBE_SIZES = {'size': 9000, 'keys': 120, 'seed': 2718281, 'n': 1234}

# 每个脚本该打几行——「多打一行 / 少打一行」也要报出来。
EXPECT_LINES = {
    'task1_bottleneck.py': 26,
    'task2_tuning.py': 34,
    'task3_builtin.py': 40,
    'task4_break_it.py': 22,
}

# 每个判分接口落在哪一段 TODO 上——每条 FAIL 后面都带上它。
TODO_OF = {
    ('task1_bottleneck', 'segment_ops'): 'task1_bottleneck.py TODO 1',
    ('task1_bottleneck', 'analyze_segments'): 'task1_bottleneck.py TODO 2',
    ('task1_bottleneck', 'segment_list_in'): 'task1_bottleneck.py TODO 3',
    ('task1_bottleneck', 'segment_set_in'): 'task1_bottleneck.py TODO 3',
    ('task1_bottleneck', 'count_size_calls'): 'task1_bottleneck.py TODO 4',
    ('task1_bottleneck', 'count_between'): 'task1_bottleneck.py TODO 5',
    ('task2_tuning', 'optimization_steps'): 'task2_tuning.py TODO 1',
    ('task2_tuning', 'tier_steps'): 'task2_tuning.py TODO 2',
    ('task2_tuning', 'solve_tier'): 'task2_tuning.py TODO 3',
    ('task2_tuning', 'tier_times'): 'task2_tuning.py TODO 4',
    ('task2_tuning', 'audit_answers'): 'task2_tuning.py TODO 5',
    ('task3_builtin', 'compare_with_builtin'): 'task3_builtin.py TODO 1',
    ('task3_builtin', 'compute_answer'): 'task3_builtin.py TODO 2',
    ('task3_builtin', 'work_of'): 'task3_builtin.py TODO 3',
    ('task3_builtin', 'recursion_ceiling'): 'task3_builtin.py TODO 4',
    ('task3_builtin', 'recursion_probe'): 'task3_builtin.py TODO 5',
    ('task3_builtin', 'distance'): 'task3_builtin.py TODO 6',
    ('task4_break_it', 'audit_broken_once'): 'task4_break_it.py TODO 1',
    ('task4_break_it', 'count_matches'): 'task4_break_it.py TODO 2',
    ('task4_break_it', 'audit'): 'task4_break_it.py TODO 3',
    ('task4_break_it', 'audit_after_fix'): 'task4_break_it.py TODO 4',
}


def todo_of(module, item):
    return TODO_OF.get((module, item), module + '.py 里那个名字')


def with_todo(item, text):
    return text + '  → 这一条指 ' + todo_of(*item)


def short(text, limit=60):
    text = '' if text is None else str(text)
    return text if len(text) <= limit else text[:limit] + '…'


# ── 载入学生写的四个文件 ────────────────────────────────────────────────

class Loaded:
    """逐个载入四个任务文件 → 记下模块、载入异常、以及缺了哪些名字。

    四道缝各自独立：某一个文件坏了，只有它负责的那一层会报载入失败。
    """

    REQUIRED = {
        'task1_bottleneck': ['segment_ops', 'analyze_segments', 'segment_list_in',
                             'segment_set_in', 'count_size_calls', 'count_between'],
        'task2_tuning': ['optimization_steps', 'tier_steps', 'solve_tier',
                         'tier_times', 'audit_answers'],
        'task3_builtin': ['compare_with_builtin', 'compute_answer', 'work_of',
                          'recursion_ceiling', 'recursion_probe', 'distance'],
        'task4_break_it': ['audit_broken_once', 'count_matches', 'audit',
                           'audit_after_fix'],
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
                    if not callable(getattr(module, item, None))]
            if module.__name__ == '__main__':
                gone.append('模块名变成了 __main__')
            if gone:
                self.missing[name] = gone

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
                    + '\n        （判分是 import 你的文件的，改完先单跑一次看它退出码是不是 0）')
        gone = self.gone(name)
        return (label + '里找不到这些名字：' + '、'.join(gone)
                + '\n        （函数名与文件名都是判分接口，别改名、别删；'
                  '要写的是文件里标着 TODO 的那几段）')


# ── 调用学生函数的保险：报错就转成一句 FAIL，不让判分自己崩 ──────────────

def attempt(func, *args, **kwargs):
    """调一次 → (值, 错误文本)。抛异常时值是 None、错误文本是「类型: 说明」。"""
    try:
        return func(*args, **kwargs), None
    except Exception as exc:
        return None, type(exc).__name__ + ': ' + str(exc)


def error_note(error):
    return '' if error is None else '（调用时抛出 ' + error + '）'


# ── 跑脚本、另起探针（两路证据）────────────────────────────────────────

def run_script(filename, timeout=600):
    """在任务目录里单跑一个脚本 → (退出码, 完整输出, 输出里的 Traceback 数)。"""
    path = HERE / filename
    if not path.exists():
        return None, '', 0
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    try:
        done = subprocess.run(
            [sys.executable, '-X', 'utf8', '-B', '-u', filename],
            cwd=str(HERE), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, '（单跑超过 ' + str(timeout) + ' 秒还没结束）', 0
    except Exception as exc:
        return None, '（起不了进程：' + type(exc).__name__ + ' ' + str(exc) + '）', 0
    out = done.stdout.decode('utf-8', 'replace')
    err = done.stderr.decode('utf-8', 'replace')
    return done.returncode, out, err.count('Traceback (most recent call last)')


def run_probe(module, sizes=None, seed=None, timeout=600):
    """另起一个进程 import 学生的函数，拿判分自己的数据试 → 交回那行 JSON。

    这就是第二路证据：判分**不读学生脚本自己打印的行**也能下结论。
    探针脚本用 tools.probe_module_source 现生成，与被测数据刻意不同。
    """
    if not (HERE / (module + '.py')).exists():
        return None
    source = judge.probe_module_source(module, sizes or PROBE_SIZES,
                                       PROBE_SEED if seed is None else seed)
    with tempfile.TemporaryDirectory(prefix='probe0029-') as work:
        workdir = Path(work)
        for name in TASK_FILES + ['tools.py']:
            src = HERE / name
            if src.exists():
                (workdir / name).write_bytes(src.read_bytes())
        (workdir / 'probe_run.py').write_bytes(source.encode('utf-8'))
        env = dict(os.environ)
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        try:
            done = subprocess.run(
                [sys.executable, '-X', 'utf8', '-B', '-u', 'probe_run.py',
                 str(workdir)],
                cwd=str(workdir), env=env, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None
        for line in reversed(done.stdout.decode('utf-8', 'replace').splitlines()):
            if line.startswith(PROBE_SENTINEL):
                try:
                    return json.loads(line[len(PROBE_SENTINEL):])
                except Exception:
                    return None
    return None


def probe_error(record, keys, item, label):
    """探针没跑起来 / 这一格是 'ERR …' → 一条 FAIL（点名哪一段 TODO）。"""
    if record is None:
        return [(False, with_todo(item, label + '：探针都没跑起来——'
                                  '先确认这个文件能单独跑（退出码 0）'))]
    if 'error' in record:
        return [(False, with_todo(item, label + '：探针里这个文件一进门就报错了：'
                                  + short(str(record.get('error')), 200)))]
    if record.get('missing'):
        return [(False, with_todo(item, label + '：探针在 ' + str(record.get('module'))
                                  + '.py 里找不到这些名字：'
                                  + '、'.join(record['missing'])
                                  + '——函数名是判分接口，别改名、别删'))]
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.startswith('ERR '):
            return [(False, with_todo(item, label + '：' + value))]
    return []


def parse_lines(text):
    """把脚本打印的行收成 {标签: 值}（判分按标签取，不按编号）。"""
    out = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('=='):
            continue
        for split in (stripped.find(' '), stripped.find('：')):
            if split <= 0:
                continue
            out.setdefault(stripped[:split], stripped[split + 1:].strip())
            break
    return out


def line_count(text):
    return len(text.splitlines())


# ── 判据小工具 ──────────────────────────────────────────────────────────

def chk(condition, good, bad):
    """一条检查 → (过没过, 那句话)。**坏话用函数包着**，只在 FAIL 时才拼。

    这样「每条 FAIL 后面都点名是哪个文件的哪个 TODO」只在真失败时才发生——
    提前拼出来的话，每条 PASS 也会顺手造一个用不上的三元组。
    """
    if condition:
        return True, good
    return False, bad() if callable(bad) else bad


def chk_eq(actual, expected, good, bad):
    """值相等给 good；不等时再拼坏话（坏话可以是一个函数）。"""
    if isinstance(expected, bool) or isinstance(actual, bool):
        same = actual is expected
    elif isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        same = list(actual) == list(expected)
    else:
        same = actual == expected
    if same:
        return True, good
    tail = bad() if callable(bad) else bad
    return False, (tail + '（交回 ' + short(repr(actual), 56) + '，期望 '
                   + short(repr(expected), 56) + '）')


def chk(condition, good, bad):
    """一条检查 → (过没过, 那句话)。**坏话用 lambda 包着**，只在 FAIL 时才拼。

    这样「每条 FAIL 后面都点名是哪个文件的哪个 TODO」只在真失败时才发生——
    提前拼出来的话每条 PASS 也会顺手造一个用不上的三元组，主循环解包就崩。
    """
    if condition:
        return True, good
    return False, bad() if callable(bad) else bad


def check_eq(actual, expected, good, bad):
    if isinstance(expected, bool) or isinstance(actual, bool):
        same = actual is expected
    elif isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        same = list(actual) == list(expected)
    else:
        same = actual == expected
    if same:
        return True, good
    return False, (bad + '（交回 ' + short(repr(actual), 56) + '，期望 '
                   + short(repr(expected), 56) + '）')


def depth_note(probe):
    """递归边界那一格 → (机制对不对, 那个 n, 一句人话)。

    判分**只认机制**：三格的表，第二个是真、第三个是假——
    也就是「边界那个 n 撑得住、再深一层就 RecursionError」。
    那个具体的 n 会随调用深度浮动（判分自己量是 994，学生在自己的调用深度上量是 992），
    所以它只当参考，不当判据。
    """
    if not isinstance(probe, (list, tuple)) or len(probe) != 3:
        return False, 0, '交回的不是一个三格的表：' + short(repr(probe), 40)
    edge = probe[0]
    ok = (isinstance(edge, int) and not isinstance(edge, bool)
          and probe[1] is True and probe[2] is False)
    return ok, edge if isinstance(edge, int) else 0, ''


def normalize(value, depth=0):
    """JSON 往返会把 tuple 变成 list——比较前先归一化，不然「其实一样」会被判成不一样。"""
    if depth > 8:
        return value
    if isinstance(value, dict):
        return dict((key, normalize(item, depth + 1)) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return [normalize(item, depth + 1) for item in value]
    return value


def same_answer(got, expected):
    """两边交回的答案是不是同一个（先归一化，再逐格比）。"""
    return normalize(got) == normalize(expected)


def numbers(value):
    """把探针交回的一串计数归成整数元组；不是数字就交回 None。"""
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        return None
    out = []
    for cell in value:
        if isinstance(cell, bool) or not isinstance(cell, (int, float)):
            return None
        out.append(int(cell))
    return tuple(out)


def real_times(values):
    """一串耗时里有几格「不是占位值」（> 守卫的地板）→ 退化守卫用它。"""
    count = 0
    for value in values:
        if isinstance(value, (int, float)) and float(value) > FLOOR:
            count += 1
    return count


# ── 第 1 层 · 分段计时与「不看形状，看次数」────────────────────────────

def layer1(loaded):
    label = 'task1_bottleneck.py '
    if not loaded.ok('task1_bottleneck'):
        return [(False, loaded.why(label, 'task1_bottleneck'))]
    out = []

    # 1) 三段各多少次操作——判分拿**另外两组规模**复算（写死的会立刻露）。
    for size, keys in ((SEG['size'], SEG['keys']),
                       (PROBE_SIZES['size'], PROBE_SIZES['keys']),
                       (JUDGE_SEG['size'], JUDGE_SEG['keys'])):
        got, error = attempt(loaded.fn('task1_bottleneck', 'segment_ops'), size, keys)
        expect = segment_ops_canonical(size, keys)
        out.append(check_eq(
            normalize(got), normalize(expect),
            '规模 (' + str(size) + ', ' + str(keys) + ') 上三段的操作次数算对了：'
            'C_in 是 A_set 的 ' + str(expect['C_in'] // expect['A_set']) + ' 倍'
            '——不看代码形状，看每段各执行多少次操作',
            with_todo(('task1_bottleneck', 'segment_ops'),
                      '规模 (' + str(size) + ', ' + str(keys) + ') 上三段的操作次数对不上'
                      + error_note(error)
                      + '（A 段一个元素一次、B 段 nlogn 量级、C 段 keys * size）')))

    # 2) 原以为最慢的 vs 实测最慢：**实测那一段必须是判分给的那一段**。
    for slow in ('C_in', 'A_set'):
        times = dict((name, 0.0) for name in SEGMENTS)
        times[slow] = 0.25                    # 判分自己给的实测值：让最慢的那段是它
        found, error = attempt(loaded.fn('task1_bottleneck', 'analyze_segments'), times)
        if error is not None or not isinstance(found, dict):
            out.append((False, with_todo(('task1_bottleneck', 'analyze_segments'),
                                         'analyze_segments(三段耗时) 交回的不是字典：'
                                         + short(repr(found), 40) + error_note(error))))
            continue
        out.append(check_eq(
            found.get('slower_true'), slow,
            '把一段「只有 ' + slow + ' 是 0.25 秒、另两段 0」的实测值交给它，'
            '实测最慢的判成 ' + slow + '——这一条不能看代码形状，要看**传进来的实测值**'
            '（判分两次给的实测值不一样，写死的会露）',
            with_todo(('task1_bottleneck', 'analyze_segments'),
                      'slower_true 不是传进来的实测值里最慢的那一段（这次最慢的是 '
                      + slow + '）')))
    found, _error = attempt(loaded.fn('task1_bottleneck', 'analyze_segments'),
                            dict((name, 0.0) for name in SEGMENTS))
    out.append(check_eq(
        found.get('slower_guess') if isinstance(found, dict) else None, 'A_set',
        '原以为最慢的是 A_set（看着最重的那个）——两个答案不一样才算做了这一步',
        with_todo(('task1_bottleneck', 'analyze_segments'),
                  'slower_guess 不是「凭形状猜的那一段」（期望 A_set）')))

    # 3) size() 被调了几次：n + 1 与 1（判分换三个规模各数一遍）。
    for limit in (1000, PROBE_SIZES['n'], 17):
        got, error = attempt(loaded.fn('task1_bottleneck', 'count_size_calls'), limit)
        expect = (limit + 1, 1)
        got_tuple = numbers(got)
        out.append(check_eq(
            got_tuple, expect,
            'n = ' + str(limit) + ' 时 size() 被调了 ' + str(expect[0])
            + ' 次、提到外面之后 1 次——写在条件里是 n + 1 次，不是 n 次，'
            '最后那次失败的比较最容易漏算',
            with_todo(('task1_bottleneck', 'count_size_calls'),
                      'n = ' + str(limit) + ' 时 size() 的调用次数对不上（期望 '
                      + str(expect) + '）' + error_note(error))))

    # 4) 三段里的两段：同一批数据、只换容器，答案必须一样。
    arr, wanted = sample_data(PROBE_SIZES['seed'], PROBE_SIZES['size'],
                              PROBE_SIZES['keys'])
    hits_list, error_a = attempt(loaded.fn('task1_bottleneck', 'segment_list_in'),
                                 arr, wanted)
    hits_set, error_b = attempt(loaded.fn('task1_bottleneck', 'segment_set_in'),
                                arr, wanted)
    expect_hits = sum(1 for key in wanted if key in set(arr))
    out.append(check_eq(
        hits_list, expect_hits,
        '判分自己造的数据上，「列表 in」找到 ' + str(expect_hits) + ' 个——'
        '换成判分的数据也数得对，不是把脚本里那个数写死的',
        with_todo(('task1_bottleneck', 'segment_list_in'),
                  '判分的数据上「列表 in」找到的个数对不上' + error_note(error_a))))
    out.append(check_eq(
        hits_set, expect_hits,
        '同一批数据换成集合，找到的还是 ' + str(expect_hits) + ' 个——'
        '换容器省的是两个数量级的操作，不是答案',
        with_todo(('task1_bottleneck', 'segment_set_in'),
                  '同一批数据换成集合之后找到的个数对不上' + error_note(error_b))))
    out.append(check_eq(
        hits_list == hits_set, True,
        '两个容器给出同一个答案——这就是「换容器不许改答案」在代码里的样子',
        with_todo(('task1_bottleneck', 'segment_set_in'),
                  '列表版与集合版的答案不一样，说明这两个函数有一边数错了')))

    # 5) 一个干活的循环：数 [0, limit) 里能被 7 整除的数（判分换规模再算）。
    for limit in (1000, PROBE_SIZES['n'], JUDGE_SEG['keys']):
        got, error = attempt(loaded.fn('task1_bottleneck', 'count_between'), limit)
        expect = sum(1 for value in range(limit) if value % 7 == 0)
        out.append(check_eq(
            got, expect,
            'n = ' + str(limit) + ' 时数出 ' + str(expect) + ' 个能被 7 整除的数'
            '——这一格是「一个最小的干活循环」，判分换了规模也数得对',
            with_todo(('task1_bottleneck', 'count_between'),
                      'n = ' + str(limit) + ' 时能被 7 整除的个数对不上'
                      + error_note(error))))
    return out


def layer1b(loaded):
    """探针那一路：拿判分自己的规模调函数，核对每一格。"""
    if not loaded.ok('task1_bottleneck'):
        return [(False, '探针这一组跳过：先让上面那一条过（task1_bottleneck.py 载入不完整）')]
    record = run_probe('task1_bottleneck')
    out = probe_error(record, ['seg_ops', 'analyze', 'size_calls', 'between'],
                        ('task1_bottleneck', 'segment_ops'),
                        '探针里那几格')
    if out:
        return out

    seg_ops = record.get('seg_ops')
    expect = segment_ops_canonical(PROBE_SIZES['size'], PROBE_SIZES['keys'])
    gone = [name for name in SEGMENTS
            if not isinstance(seg_ops, dict) or seg_ops.get(name) != expect[name]]
    if gone:
        out.append((False, with_todo(('task1_bottleneck', 'segment_ops'),
                                     '探针（规模 ' + str(PROBE_SIZES['size']) + ' / 键 '
                                     + str(PROBE_SIZES['keys']) + '）里这几段对不上：'
                                     + '、'.join(gone) + '（交回 ' + short(repr(seg_ops), 50)
                                     + '，期望 ' + short(repr(expect), 50) + '）')))
    else:
        out.append((True, '探针里三段的操作次数与判分另算一遍的逐格一致'
                          '（A ' + str(expect['A_set']) + ' / B ' + str(expect['B_sort'])
                          + ' / C ' + str(expect['C_in'])
                          + '）——脚本里那份是算出来的，不是写死的'))

    analyze = record.get('analyze') if isinstance(record.get('analyze'), dict) else {}
    out.append(check_eq(
        analyze.get('slower_true'), 'C_in',
        '探针单独调 analyze_segments（判分给的三段耗时里 C 最慢）也判成 C_in'
        '——这一条不吃脚本里打印出来的那一行',
        with_todo(('task1_bottleneck', 'analyze_segments'),
                  '探针里 slower_true 不是 C_in（交回 '
                  + short(repr(analyze.get('slower_true')), 30) + '）')))

    want_calls = (PROBE_SIZES['n'] + 1, 1)
    out.append(check_eq(
        numbers(record.get('size_calls')), want_calls,
        '探针拿 n = ' + str(PROBE_SIZES['n']) + ' 再数一遍 size()：'
        + str(want_calls[0]) + ' 次与 1 次——这一格是**数出来的**，不是「看着像对」',
        with_todo(('task1_bottleneck', 'count_size_calls'),
                  '探针的规模上 size() 的调用次数对不上（期望 ' + str(want_calls) + '）')))

    want_between = sum(1 for value in range(PROBE_SIZES['n']) if value % 7 == 0)
    out.append(check_eq(
        record.get('between'), want_between,
        '探针拿 n = ' + str(PROBE_SIZES['n']) + ' 再数一遍能被 7 整除的：'
        + str(want_between) + ' 个',
        with_todo(('task1_bottleneck', 'count_between'),
                  '探针的规模上能被 7 整除的个数对不上（期望 ' + str(want_between) + '）')))

    seg_times = record.get('seg_times') if isinstance(record.get('seg_times'), dict) else {}
    hits = (seg_times.get('hit_list'), seg_times.get('hit_set'))
    out.append(chk(hits[0] is not None and hits[0] == hits[1], '探针里两个容器在同一批数据上交回同一个命中数（' + str(hits[0]) + '）——'
        '换容器不许改答案，这一步在探针里也核了一遍', lambda: with_todo(('task1_bottleneck', 'segment_set_in'),
                  '探针里列表版与集合版的命中数不一样：' + short(repr(hits), 30))))
    out.append(chk(isinstance(seg_times.get('list'), (int, float))
        and isinstance(seg_times.get('set'), (int, float)), '探针顺手量了一次容器对照：列表 ' + judge.fmt_seconds(seg_times.get('list'))
        + ' 秒 vs 集合 ' + judge.fmt_seconds(seg_times.get('set'))
        + ' 秒（这一格只当参考，判死的是上面那些次数）', lambda: with_todo(('task1_bottleneck', 'segment_list_in'),
                  '探针里两段的耗时没量出来：' + short(repr(seg_times), 40))))
    return out


# ── 第 2 层 · 四招优化，每一招都留记录 ──────────────────────────────────

def layer2(loaded):
    label = 'task2_tuning.py '
    if not loaded.ok('task2_tuning'):
        return [(False, loaded.why(label, 'task2_tuning'))]
    out = []

    # 1) 四招的名字（判分逐条核对，顺序也是接口）。
    got, error = attempt(loaded.fn('task2_tuning', 'optimization_steps'))
    rows = []
    if isinstance(got, (list, tuple)):
        for item in got:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                rows.append((item[0], item[1]))
    out.append(check_eq(
        rows, list(TIERS),
        '四招的名字与顺序逐条对上：' + ' → '.join(name for _level, name in TIERS),
        with_todo(('task2_tuning', 'optimization_steps'),
                  '交回的四招列表与 tools.TIERS 对不上' + error_note(error))))

    # 2) 每一级四格**确定量**——判分拿自己的规模复算。
    size, keys, seed = PROBE_SIZES['size'], PROBE_SIZES['keys'], PROBE_SIZES['seed']
    canonical = canonical_trace_table(size, keys, seed)
    bad_levels = []
    for level in LEVELS:
        reader = judge.ReadCounter().load('0\n')
        got, error = attempt(loaded.fn('task2_tuning', 'tier_steps'),
                             level, size, keys, seed, reader)
        want = canonical[level]
        got_nums = numbers(got)
        if got_nums is None or got_nums[:3] != want:
            bad_levels.append(level)
            out.append((False, with_todo(('task2_tuning', 'tier_steps'),
                                         '第 ' + str(level) + ' 级的前三格计数对不上：交回 '
                                         + short(repr(got_nums), 40)
                                         + '，期望循环 / 相等比较 / 读入 = ' + str(want)
                                         + error_note(error))))
    if not bad_levels:
        out.append((True, '四级的前三格计数（循环 / 相等比较 / 读入）在判分自己的规模上与'
                          '另算一遍的逐级一致：'
                          + ' → '.join(str(canonical[level]) for level in LEVELS)))
        # 读入那一格是真调出来的：判分再数一遍读入器自己的账。
        for level in LEVELS:
            reader = judge.ReadCounter().load('0\n')
            attempt(loaded.fn('task2_tuning', 'tier_steps'), level, size, keys, seed,
                    reader)
            want_all = 1 if level >= 2 else 0
            want_line = 0 if level >= 2 else size
            ok = (reader.calls.get('all') == want_all
                  and reader.calls.get('line') == want_line)
            good = ('第 ' + str(level) + ' 级的读入器账目对得上：'
                    + ('一次整体读（read_all 1 次、逐行 0 次）' if level >= 2 else
                       '逐行读 ' + str(size) + ' 次（read_all 0 次）')
                    + '——这一格是数出来的，不是写出来的')
            bad = ('第 ' + str(level) + ' 级'
                   + ('该走**整体读入**（read_all 一次）' if level >= 2 else
                      '该走**逐行读入**（每行一次）')
                   + '，实际账目是 ' + short(repr(reader.calls), 40)
                   + '——第 ' + str(level) + ' 级要改的正是读入这一处')
            out.append((ok, good if ok else with_todo(('task2_tuning', 'tier_steps'), bad)))

    # 3) 四级答案一致（判分自己的数据），而且要有**其实在干活**的证据。
    arr = LCG(PROBE_SEED + 1).make(400, 0, 50)
    wanted = LCG(PROBE_SEED + 2).make(60, 0, 50)
    text = input_text(arr)
    expect_answer = canonical_count(arr, wanted)
    answers = {}
    for level in LEVELS:
        reader = judge.ReadCounter().load(text)
        got, _error = attempt(loaded.fn('task2_tuning', 'solve_tier'),
                              level, 400, 60, PROBE_SEED + 2, text, reader)
        answers[level] = got
    out.append(check_eq(
        len(set(short(repr(value), 30) for value in answers.values())) == 1
        and answers.get(4) == expect_answer, True,
        '四级答案都是 ' + str(expect_answer) + '（判分自己造的 400 个值 / 60 个键上）'
        '——每上一招都回验一次，四招上完答案没变，这就是「优化不许改答案」',
        with_todo(('task2_tuning', 'solve_tier'),
                  '四级答案不一致，或者与判分另算一遍的 ' + str(expect_answer) + ' 对不上：'
                  + '、'.join('第 ' + str(level) + ' 级 '
                              + short(repr(answers.get(level)), 20)
                              for level in LEVELS))))
    out.append(chk(expect_answer > 0, '这一组数据上真的有命中（' + str(expect_answer) + ' 个）——'
        '四级都交回 0 这种「一致」不算对：一致的前提是四级都在干活', lambda: with_todo(('task2_tuning', 'solve_tier'),
                  '判分的数据上有 ' + str(expect_answer) + ' 个命中，四级却都交回 '
                  + short(repr(answers.get(4)), 20) + '——把 0 写死也算「一致」，所以要核')))

    # 4) 耗时那几格：先过退化守卫，再过噪声容差（本课最容易抖的就是这里）。
    times, error = attempt(loaded.fn('task2_tuning', 'tier_times'))
    table = {}
    if isinstance(times, dict):
        for level in LEVELS:
            value = times.get(level, times.get(str(level)))
            if isinstance(value, (int, float)):
                table[level] = float(value)
    real = real_times(table.values())
    if error is not None:
        out.append((False, with_todo(('task2_tuning', 'tier_times'),
                                     'tier_times() 报错：' + error)))
    elif real == 0:
        out.append((False, with_todo(('task2_tuning', 'tier_times'),
                                     '四级耗时全是占位值（' + short(repr(table), 44) + '）——'
                                     '「0 跟 0 比」是掷硬币，不是证据。这一条是**退化守卫**：'
                                     '耗时可以抖动，但不能一格都没量')))
    else:
        out.append((True, '四级耗时里有 ' + str(real) + ' 格是真量出来的（不是 0.000000），'
                          '退化守卫过了——留白版的四格全 0 就栽在这一条'))
    t0, t1 = table.get(0), table.get(1)
    guard_on, can_set, guard_note = judge.judge_guard(t1, t0)
    prefix = ('换容器那一处：' if guard_on else
              '换容器那一处（退化守卫：基线太小，这一条只当参考）：')
    out.append(chk((not guard_on) or can_set, prefix + guard_note + '——耗时只当辅助证据，判死的是上面那四行次数', lambda: with_todo(('task2_tuning', 'tier_times'),
                  '换容器那一处的耗时没通过噪声容差：第 0 级 '
                  + judge.fmt_seconds(t0) + ' 秒 / 第 1 级 ' + judge.fmt_seconds(t1)
                  + ' 秒（期望 <= ' + str(NOISE) + ' 倍）')))

    # 5) 一条**不依赖时钟**的因果证据：同一件事跑 16 遍，优化版让读入器被调的次数
    #    远小于基线。这才是「换容器省的是操作次数」这件事的硬证据。
    box = {'loops': 0}

    class CountingReader(judge.ReadCounter):
        def next_number(self):
            box['loops'] += 1
            return judge.ReadCounter.next_number(self)

    def spend(level, reps):
        for _ in range(reps):
            reader = CountingReader().load(text)
            attempt(loaded.fn('task2_tuning', 'solve_tier'), level, 400, 60,
                    PROBE_SEED + 2, text, reader)

    box['loops'] = 0
    spend(4, 16)
    loops_optimized = box['loops']
    box['loops'] = 0
    spend(0, 1)
    loops_baseline = box['loops']
    out.append(chk(loops_baseline > 0 and loops_optimized * 4 < loops_baseline, '不靠时钟的因果证据：第 4 级跑 16 遍只让读入器被调 ' + str(loops_optimized)
        + ' 次，第 0 级跑 1 遍就要 ' + str(loops_baseline) + ' 次——'
        '优化掉的是**操作次数**，这一条不会被机器快慢影响', lambda: with_todo(('task2_tuning', 'solve_tier'),
                  '第 4 级跑 16 遍让读入器被调 ' + str(loops_optimized) + ' 次，'
                  '第 0 级跑 1 遍是 ' + str(loops_baseline) + ' 次——'
                  '第 4 级该走整体读入（16 次调用），第 0 级该逐行读（每遍 400 次）')))

    # 6) 改正之后对拍一次：不一致 0 组（确定量，判分自己另算）。
    got, error = attempt(loaded.fn('task2_tuning', 'audit_answers'),
                         JUDGE_DATA['size'], JUDGE_DATA['keys'], JUDGE_DATA['seed'])
    want = canonical_answer_of(JUDGE_DATA['size'], JUDGE_DATA['keys'],
                               JUDGE_DATA['seed'])
    out.append(check_eq(
        numbers(got) if numbers(got) is not None else got, (0, len(LEVELS)),
        '判分自己造的那组数据（规模 ' + str(JUDGE_DATA['size']) + ' / 键 '
        + str(JUDGE_DATA['keys']) + '）上，四招上完答案一致：'
        + str(want[0]) + ' 个命中的标准答案，不一致 0 级',
        with_todo(('task2_tuning', 'audit_answers'),
                  'audit_answers() 交回的 (不一致级数, 级数) 对不上' + error_note(error))))

    # 7) 主块打印的那几行：四级答案与标准答案逐级对上。
    #    **额外一条**：全 0 也算「一致」，所以判分自己把标准答案另算一遍来对账——
    #    只靠 audit_answers() 那一格的话，「四级都交回 0」也能拿到 (0, 5)。
    rows, error = attempt(loaded.fn('task2_tuning', 'audit_tiers'),
                          JUDGE_DATA['size'], JUDGE_DATA['keys'], JUDGE_DATA['seed'])
    if error is not None or not isinstance(rows, (list, tuple)) or len(rows) != 2:
        out.append((False, with_todo(('task2_tuning', 'solve_tier'),
                                     'audit_tiers() 交回的不是 (四级答案, 标准答案)：'
                                     + short(repr(rows), 40) + error_note(error))))
    else:
        got_answers, got_standard = numbers(rows[0]), rows[1]
        want_standard = want[0]
        out.append(chk(
            got_standard == want_standard and got_answers is not None
            and len(set(got_answers)) == 1 and got_answers[0] == want_standard,
            '四级答案逐级都是 ' + str(want_standard) + '（判分自己另算的标准答案）'
            '——「四级都交回同一个数」不算对：那个数还得是**对的那个数**',
            lambda: with_todo(('task2_tuning', 'solve_tier'),
                              '四级答案与判分另算的标准答案（' + str(want_standard)
                              + '）对不上：交回 ' + short(repr(rows[0]), 40)
                              + '、标准答案交回 ' + short(repr(got_standard), 20)
                              + error_note(error))))
    return out


def layer2b(loaded):
    """探针那一路：四招的名字、四级计数、四级答案、收尾那一格，全由判分另算。"""
    if not loaded.ok('task2_tuning'):
        return [(False, '探针这一组跳过：先让上面那一条过（task2_tuning.py 载入不完整）')]
    record = run_probe('task2_tuning')
    out = probe_error(record, ['steps', 'counts', 'answers', 'times',
                                 'audit_answers'],
                        ('task2_tuning', 'tier_steps'), '探针里那几格')
    if out:
        return out

    steps = record.get('steps')
    rows = []
    if isinstance(steps, list):
        for item in steps:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                rows.append((item[0], item[1]))
    out.append(check_eq(
        rows, list(TIERS),
        '探针里四招的名字与顺序也对得上（名字在函数交回的东西里，不是从打印行里读的）',
        with_todo(('task2_tuning', 'optimization_steps'),
                  '探针里交回的四招列表对不上：' + short(repr(steps), 50))))

    size, keys, seed = PROBE_SIZES['size'], PROBE_SIZES['keys'], PROBE_SIZES['seed']
    canonical = canonical_trace_table(size, keys, seed)
    counts = record.get('counts') if isinstance(record.get('counts'), dict) else {}
    reads = record.get('reads') if isinstance(record.get('reads'), dict) else {}
    bad = []
    for level in LEVELS:
        got = numbers(counts.get(str(level)))
        if got is None or got[:3] != canonical[level]:
            bad.append('第 ' + str(level) + ' 级（' + short(repr(got), 24) + '）')
            continue
        want_reads = {'all': 1, 'line': 0} if level >= 2 else {'all': 0, 'line': size}
        got_reads = reads.get(str(level)) or {}
        if (got_reads.get('all') != want_reads['all']
                or got_reads.get('line') != want_reads['line']):
            bad.append('第 ' + str(level) + ' 级的读入账目（' + short(repr(got_reads), 22)
                       + '）')
    if bad:
        out.append((False, with_todo(('task2_tuning', 'tier_steps'),
                                     '探针里这几级对不上：' + '、'.join(bad))))
    else:
        out.append((True, '探针里四级的前三格计数与读入账目逐级对上：'
                          + ' → '.join(str(canonical[level]) for level in LEVELS)
                          + '，读入 9000/9000/1/1/1——'
                          '这是判分拿**自己的**规模另算一遍的结果'))

    answers = record.get('answers') if isinstance(record.get('answers'), dict) else {}
    want_answer = record.get('canonical_answer')
    distinct = set(short(repr(answers.get(str(level))), 30) for level in LEVELS)
    out.append(chk(len(distinct) == 1 and answers.get('4') == want_answer, '探针自己造的数据上四级答案一致，都是 ' + str(want_answer)
        + '（由 tools.canonical_count 另算一遍）', lambda: with_todo(('task2_tuning', 'solve_tier'),
                  '探针里四级答案对不上判分另算的 ' + str(want_answer) + '：'
                  + short(repr(answers), 50))))

    audit = numbers(record.get('audit_answers'))
    out.append(chk(audit == (0, len(LEVELS)), '探针里 audit_answers 也交回 ' + str((0, len(LEVELS)))
        + '——四招上完，不一致必须是 0 级', lambda: with_todo(('task2_tuning', 'audit_answers'),
                  '探针里 audit_answers 交回 ' + short(repr(record.get('audit_answers')), 30))))

    times = record.get('times')
    ok_times = isinstance(times, dict) and real_times(
        [value for value in times.values() if isinstance(value, (int, float))]) > 0
    out.append(chk(ok_times, '探针里 tier_times 也真量出了秒数（' + short(repr(times), 60)
        + '）——耗时当参考，但一格都不能是 0', lambda: with_todo(('task2_tuning', 'tier_times'),
                  '探针里 tier_times 交回的全是占位值：' + short(repr(times), 40))))
    return out


# ── 第 3 层 · 和内置实现比，并说清差在哪一层 ────────────────────────────

JOBS = ('contain', 'sort', 'sum', 'min', 'role')

LAYER_KEYWORDS = {
    'contain': ['查找'],
    'sort': ['复杂度'],
    'sum': ['循环'],
    'min': ['堆', '每轮', '一遍'],
    'role': ['分支', '查表'],
}


def layer3(loaded):
    label = 'task3_builtin.py '
    if not loaded.ok('task3_builtin'):
        return [(False, loaded.why(label, 'task3_builtin'))]
    out = []

    for job in JOBS:
        row, error = attempt(loaded.fn('task3_builtin', 'compare_with_builtin'),
                             job, PROBE_SEED)
        if error is not None or not isinstance(row, dict):
            out.append((False, with_todo(('task3_builtin', 'compare_with_builtin'),
                                         'compare_with_builtin(' + repr(job) + ') '
                                         '交回的不是字典：' + short(repr(row), 40)
                                         + error_note(error))))
            continue
        expect = judge.expect_answer(job, PROBE_SEED, WORK_SIZES[job])
        hand, builtin = row.get('hand'), row.get('builtin')
        out.append(chk(same_answer(hand, builtin), job + ' 栏两边答案一致（' + short(repr(expect), 30) + '）——'
            '两个版本除了要比的那一点，别的地方必须严格一样，'
            '否则量出来的倍率没有意义（课件那个「查表反而慢 12%」就是这么写错的）', lambda: with_todo(('task3_builtin', 'compare_with_builtin'),
                      job + ' 栏手写版与内置版交回的答案不一样：'
                      + short(repr(hand), 30) + ' vs ' + short(repr(builtin), 30))))
        out.append(chk(same_answer(hand, expect), job + ' 栏的答案与「按判分自己的种子单独算一遍」一致——'
            '答案是从数据里算出来的，不是脚本里那个数', lambda: with_todo(('task3_builtin', 'compare_with_builtin'),
                      job + ' 栏的答案与判分另算一遍的对不上：交回 ' + short(repr(hand), 30)
                      + '，期望 ' + short(repr(expect), 30))))

        expect_hand, expect_builtin = judge.expect_times(
            job, PROBE_SEED, WORK_SIZES[job], WORK_REPEATS[job])
        got_hand, error_a = attempt(loaded.fn('task3_builtin', 'work_of'),
                                    job, PROBE_SEED, WORK_SIZES[job], 'hand')
        got_builtin, error_b = attempt(loaded.fn('task3_builtin', 'work_of'),
                                       job, PROBE_SEED, WORK_SIZES[job], 'builtin')
        out.append(chk(got_hand == expect_hand, job + ' 栏手写版的「值访问次数」= ' + str(expect_hand)
            + '（按规模算出来的确定量，判分也是这么算的）', lambda: with_todo(('task3_builtin', 'work_of'),
                      '手写版的值访问次数对不上：交回 ' + short(repr(got_hand), 30)
                      + '，期望 ' + str(expect_hand) + error_note(error_a))))
        out.append(chk(got_builtin == expect_builtin, job + ' 栏内置版的「值访问次数」= ' + str(expect_builtin)
            + '——差在哪一层，看的就是这两个数（倍率只是参考）', lambda: with_todo(('task3_builtin', 'work_of'),
                      '内置版的值访问次数对不上：交回 ' + short(repr(got_builtin), 30)
                      + '，期望 ' + str(expect_builtin) + error_note(error_b))))

        layer, error = attempt(loaded.fn('task3_builtin', 'layer_of'), job)
        text = '' if error is not None else str(layer)
        hit = [word for word in LAYER_KEYWORDS[job] if word in text]
        out.append(chk(bool(hit), job + ' 栏「差在哪一层」点到了 ' + '、'.join(hit) + '：' + short(text, 56), lambda: with_todo(('task3_builtin', 'compare_with_builtin'),
                      job + ' 栏 layer_of 交回的话里没有 '
                      + '、'.join(LAYER_KEYWORDS[job]) + ' 里的任何一个词（交回 '
                      + short(repr(layer), 30) + '）')))

    # 递归那两栏：记的是**机制**，不是一个写死的边界。
    for n in (200, 400, 700):
        got, error = attempt(loaded.fn('task3_builtin', 'recursion_ceiling'), n)
        want = judge.expect_recursion_ceiling(n)
        out.append(chk(same_answer(got, want), 'n = ' + str(n) + ' 递归求和：'
            + ('撑得住' if want is not None else 'RecursionError')
            + '（判分自己在**同一个位置上**又试了一遍）', lambda: with_todo(('task3_builtin', 'recursion_ceiling'),
                      'n = ' + str(n) + ' 时递归那一条与判分另试一遍的不一样：交回 '
                      + short(repr(got), 30) + '，期望 ' + short(repr(want), 30)
                      + error_note(error))))
    probe, error = attempt(loaded.fn('task3_builtin', 'recursion_probe'))
    edge = judge.recursion_edge()
    ok_depth, got_edge, note = depth_note(probe)
    out.append(chk(
        ok_depth,
        '递归的边界在 n = ' + str(got_edge) + '：这个 n 撑得住、n = '
        + str(got_edge + 1) + ' 就 RecursionError——判分核的是这个**机制**，'
        '不是一个写死的 998（判分自己量出来是 ' + str(edge)
        + '，差几层是调用深度不同，不算错）',
        lambda: with_todo(('task3_builtin', 'recursion_probe'),
                          '递归边界的机制没对上：' + (note or short(repr(probe), 40))
                          + '，期望 [边界 n, True, False]' + error_note(error))))
    out.append(chk(
        abs(got_edge - edge) <= 4,
        '这个 n 与判分在同一种位置量出来的 ' + str(edge) + ' 差 '
        + str(abs(got_edge - edge)) + ' 层——判据只认机制，这一条是核对量法一致',
        lambda: with_todo(('task3_builtin', 'recursion_probe'),
                          '边界那个 n 与判分量出来的 ' + str(edge) + ' 差得太多（交回 '
                          + str(got_edge) + ' 层）：先看 recursion_ceiling 是不是'
                          '「撑得住交回和、撑不住交回 None」这个口径')))

    for hand, builtin, want in ((5, 5, 0), (5, 7, 2), ('a', 'a', 0), (None, 3, 1)):
        got, error = attempt(loaded.fn('task3_builtin', 'distance'), hand, builtin)
        out.append(check_eq(
            got, want,
            'distance(' + repr(hand) + ', ' + repr(builtin) + ') = ' + str(want)
            + '——「优化不许改答案」在代码里就是这一句',
            with_todo(('task3_builtin', 'distance'),
                      'distance(' + repr(hand) + ', ' + repr(builtin) + ') 对不上'
                      + error_note(error))))
    return out


def layer3b(loaded):
    """探针那一路：五栏 + 递归，判分自己另算一遍。"""
    if not loaded.ok('task3_builtin'):
        return [(False, '探针这一组跳过：先让上面那一条过（task3_builtin.py 载入不完整）')]
    record = run_probe('task3_builtin')
    out = probe_error(record, ['compare', 'layers', 'ceiling', 'depth'],
                        ('task3_builtin', 'compare_with_builtin'), '探针里那几格')
    if out:
        return out

    table = record.get('compare') if isinstance(record.get('compare'), dict) else {}
    bad = []
    good_rows = []
    for job in JOBS:
        row = table.get(job)
        if not isinstance(row, dict):
            bad.append(job + '（' + short(repr(row), 24) + '）')
            continue
        expect = judge.expect_answer(job, PROBE_SEED, WORK_SIZES[job])
        if not same_answer(row.get('answer'), row.get('builtin')):
            bad.append(job + '（两边答案不一致）')
        elif not same_answer(row.get('answer'), expect):
            bad.append(job + '（答案不是算出来的：' + short(repr(row.get('answer')), 24)
                       + '）')
        else:
            good_rows.append(job + ' ' + short(repr(expect), 20))
    if bad:
        out.append((False, with_todo(('task3_builtin', 'compare_with_builtin'),
                                     '探针里这几栏与判分另算一遍的对不上：' + '、'.join(bad)
                                     + '——换一个种子答案就变，写死的数在这里会露')))
    else:
        out.append((True, '探针（判分自己的种子 ' + str(PROBE_SEED) + '）里五栏答案'
                          '两边一致、而且与另算一遍的逐栏对上：' + '；'.join(good_rows)))

    layers = record.get('layers') if isinstance(record.get('layers'), dict) else {}
    missed = []
    for job in JOBS:
        text = str(layers.get(job, ''))
        if not [word for word in LAYER_KEYWORDS[job] if word in text]:
            missed.append(job)
    out.append(chk(not missed, '五栏「差在哪一层」都被判分从**函数交回的东西**里认了出来'
        '——不是靠读脚本打印的那一行', lambda: with_todo(('task3_builtin', 'compare_with_builtin'),
                  '探针里这几栏的 layer_of 点不到该点的关键词：' + '、'.join(missed))))

    ceiling = record.get('ceiling')
    want_ceiling = [judge.expect_recursion_ceiling(n) for n in (200, 400, 700)]
    out.append(check_eq(
        normalize(ceiling), want_ceiling,
        '探针里 n = 200 / 400 / 700 三个点上的递归结果与判分自己再试一遍的一致'
        '（' + '、'.join('n = ' + str(n) + ' '
                        + ('撑得住' if want is not None else 'RecursionError')
                        for n, want in zip((200, 400, 700), want_ceiling)) + '）',
        with_todo(('task3_builtin', 'recursion_ceiling'),
                  '探针里这三个 n 上的递归结果对不上（交回 '
                  + short(repr(ceiling), 40) + '）')))

    depth = record.get('depth')
    edge = judge.recursion_edge()
    ok_depth, got_edge, note = depth_note(depth)
    out.append(chk(
        ok_depth and abs(got_edge - edge) <= 4,
        '探针在它自己的调用深度上找出来的边界是 n = ' + str(got_edge)
        + '，而且「边界撑得住、再深一层就 RecursionError」——'
        '判分核的是这个机制，不是一个固定的数（判分自己量是 ' + str(edge) + '）',
        lambda: with_todo(('task3_builtin', 'recursion_probe'),
                          '探针里 recursion_probe 交回 ' + (note or short(repr(depth), 40))
                          + '，期望 [边界 n, True, False]，且边界与判分的 ' + str(edge)
                          + ' 只差几层')))
    return out


# ── 第 4 层 · 故意写错一次：对拍抓不抓得住 ──────────────────────────────

PROBES_4 = [([1, 2, 3], 0, 3), ([], 0, 3), ([2], 0, 3),
            ([0, 1, 2, 3, 4, 5], 3, 6), ([3], 3, 3)]


def layer4(loaded):
    label = 'task4_break_it.py '
    if not loaded.ok('task4_break_it'):
        return [(False, loaded.why(label, 'task4_break_it'))]
    out = []

    # 1) 判分自己的五组数据（含空数组、单元素）：两版答案都要与判分另算的一致。
    for values, lo, hi in PROBES_4:
        want_right = judge.count_matches(values, lo, hi, False)
        want_wrong = judge.count_matches(values, lo, hi, True)
        got_right, error_a = attempt(loaded.fn('task4_break_it', 'count_matches'),
                                     values, lo, hi, False)
        got_wrong, error_b = attempt(loaded.fn('task4_break_it', 'count_matches'),
                                     values, lo, hi, True)
        out.append(chk(got_right == want_right and got_wrong == want_wrong, '对拍器在 ' + repr(values)[:32] + '（[lo, hi] = [' + str(lo) + ', '
            + str(hi) + ']）上：对的那版 ' + str(want_right) + '、坏的那版 '
            + str(want_wrong) + '——空数组与单元素这两组都要对', lambda: with_todo(('task4_break_it', 'count_matches'),
                      '在 ' + repr(values)[:32] + ' 上两版答案与判分另算的不一样：交回 '
                      + short(repr((got_right, got_wrong)), 30) + '，期望 '
                      + short(repr((want_right, want_wrong)), 30)
                      + error_note(error_a) + error_note(error_b))))

    # 2) 把错写进去一次：50 组固定数据上必须被抓到，而且带得出证据。
    got, error = attempt(loaded.fn('task4_break_it', 'audit_broken_once'))
    if error is not None or not isinstance(got, dict):
        out.append((False, with_todo(('task4_break_it', 'audit_broken_once'),
                                     'audit_broken_once() 交回的不是字典：'
                                     + short(repr(got), 40) + error_note(error))))
    else:
        rows = audit_cases(judge.AUDIT['cases'], judge.AUDIT['size'],
                           judge.AUDIT['value_hi'], judge.AUDIT['seed'])
        right, wrong, misses, evidence = judge.audit_run(
            rows, judge.AUDIT['low'], judge.AUDIT['high'], True)
        out.append(check_eq(
            got.get('cases'), int(judge.AUDIT['cases']),
            '对拍跑了 ' + str(judge.AUDIT['cases']) + ' 组固定数据'
            '（种子钉死 → 每次都一样）',
            with_todo(('task4_break_it', 'audit_broken_once'), '对拍的组数对不上')))
        out.append(check_eq(
            (got.get('right'), got.get('wrong')), (right, wrong),
            '50 组数据上两版各自加起来是 ' + str(right) + ' / ' + str(wrong)
            + '（判分自己另算一遍）',
            with_todo(('task4_break_it', 'audit_broken_once'),
                      '两版各自加起来对不上')))
        out.append(chk(got.get('misses') == int(misses) and int(misses) > 0, '坏的那一版在 ' + str(misses) + ' 组上露了——'
            '把 `i < n` 写成 `i < n - 1`，最后一个元素就不看了。'
            '这一条证明**对拍真的有效**，不是摆设；'
            '一组都没抓到的话，对拍每轮都会说「没事」', lambda: with_todo(('task4_break_it', 'audit_broken_once'),
                      '坏的那一版对不上的组数不是 ' + str(misses)
                      + '（交回 ' + short(repr(got.get('misses')), 20) + '）')))
        proof = got.get('evidence')
        ok_proof = (isinstance(proof, (list, tuple)) and len(proof) == 3
                    and list(proof[0]) == list(evidence[0])
                    and proof[1] == evidence[1] and proof[2] == evidence[2])
        out.append(chk(ok_proof, '证据那一格是**最早对不上的那组数据**本身：'
            + short(repr(evidence), 50) + '——有反例的对拍才能复现', lambda: with_todo(('task4_break_it', 'audit_broken_once'),
                      '证据那一格不是最早对不上的那组数据：交回 '
                      + short(repr(proof), 44) + '，期望 ' + short(repr(evidence), 44))))

    # 3) 一次都没抓到 → 单独点出来（这是这一步最要命的错法）。
    single = [2]
    right = judge.count_matches(single, 0, 3, False)
    wrong = judge.count_matches(single, 0, 3, True)
    got_right, _e1 = attempt(loaded.fn('task4_break_it', 'count_matches'),
                             single, 0, 3, False)
    got_wrong, _e2 = attempt(loaded.fn('task4_break_it', 'count_matches'),
                             single, 0, 3, True)
    out.append(chk(got_right == right and got_wrong == wrong and right != wrong, '只有一个元素的数组上：对的版 ' + str(right) + '、坏的版 ' + str(wrong)
        + '——答案直接变成 0，错得不多，但已经错了', lambda: with_todo(('task4_break_it', 'count_matches'),
                  '单元素数组上两版答案与判分另算的对不上：交回 '
                  + short(repr((got_right, got_wrong)), 30) + '，期望 '
                  + str((right, wrong)))))

    # 4) 改回来之后再对拍一次：不一致 0 组（确定量）。
    got, error = attempt(loaded.fn('task4_break_it', 'audit_after_fix'))
    expect = judge.audit_fixed()
    out.append(check_eq(
        numbers(got) if numbers(got) is not None else got, expect,
        '改回来之后再对拍：' + str(expect[1]) + ' 组里不一致 ' + str(expect[0])
        + ' 组——修好之后这一格必须回到 0',
        with_todo(('task4_break_it', 'audit_after_fix'),
                  'audit_after_fix() 交回的 (不一致组数, 总组数) 对不上：交回 '
                  + short(repr(got), 30) + '，期望 ' + str(expect) + error_note(error))))
    return out


def layer4b(loaded):
    """探针那一路：对拍与「改回来」都由判分自己造数据复算。"""
    if not loaded.ok('task4_break_it'):
        return [(False, '探针这一组跳过：先让上面那一条过（task4_break_it.py 载入不完整）')]
    record = run_probe('task4_break_it')
    out = probe_error(record, ['audit', 'probe_count', 'audit_probe',
                                 'after_fix'],
                        ('task4_break_it', 'count_matches'), '探针里那几格')
    if out:
        return out

    audit = record.get('audit') if isinstance(record.get('audit'), dict) else {}
    rows = audit_cases(judge.AUDIT['cases'], judge.AUDIT['size'],
                       judge.AUDIT['value_hi'], judge.AUDIT['seed'])
    _right, _wrong, misses, evidence = judge.audit_run(
        rows, judge.AUDIT['low'], judge.AUDIT['high'], True)
    out.append(chk(audit.get('misses') == int(misses) and int(misses) > 0, '探针里 audit_broken_once() 也抓到 ' + str(misses) + ' 组，'
        '与判分另算一遍的一致——抓得到错的对拍器才是有效的', lambda: with_todo(('task4_break_it', 'audit_broken_once'),
                  '探针里 audit_broken_once() 的结论与判分另算的对不上：交回 '
                  + short(repr(audit.get('misses')), 20) + '，期望 ' + str(misses))))
    proof = audit.get('evidence')
    ok_proof = (isinstance(proof, (list, tuple)) and len(proof) == 3
                and list(proof[0]) == list(evidence[0]) and proof[1] == evidence[1]
                and proof[2] == evidence[2])
    out.append(chk(ok_proof, '探针里证据那一格也是最早对不上的那组数据：' + short(repr(evidence), 44), lambda: with_todo(('task4_break_it', 'audit_broken_once'),
                  '探针里证据那一格不对：交回 ' + short(repr(proof), 40))))

    cases = audit_cases(9, 12, 6, PROBE_SEED)
    want_break = judge.audit_pair(cases, 3, 6, True)
    want_fixed = judge.audit_pair(cases, 3, 6, False)
    got_break = record.get('audit_probe')
    got_fixed = record.get('audit_probe_fixed')
    if not isinstance(got_break, dict) or not isinstance(got_fixed, dict):
        out.append((False, with_todo(('task4_break_it', 'count_matches'),
                                     '探针里 count_matches 报错，对拍那两组没跑起来')))
        return out
    out.append(chk((got_break.get('misses') == want_break['misses']
         and got_break.get('right') == want_break['right']
         and got_break.get('wrong') == want_break['wrong']), '判分自己造的 9 组数据（种子 ' + str(PROBE_SEED) + '，规模也不是脚本里那个）上：'
        '坏版对不上 ' + str(want_break['misses']) + ' 组、两版各自加起来 '
        + str(want_break['right']) + ' / ' + str(want_break['wrong'])
        + '——与判分另算一遍的逐格一致', lambda: with_todo(('task4_break_it', 'count_matches'),
                  '判分自己造的数据上对拍结果对不上：交回 '
                  + short(repr((got_break.get('right'), got_break.get('wrong'),
                                got_break.get('misses'))), 44)
                  + '，期望 ' + str((want_break['right'], want_break['wrong'],
                                      want_break['misses'])))))
    out.append(chk(got_fixed.get('same') is True and got_fixed.get('misses') == 0, '同一批数据上「对的那一版」自己跟自己比：不一致 0 组——'
        '对拍器的两边不能同时错，这一条就是那个对照', lambda: with_todo(('task4_break_it', 'count_matches'),
                  '对的那一版自己跟自己比居然有 ' + str(got_fixed.get('misses'))
                  + ' 组不一致：说明计数的口径本身就不稳定')))

    after = record.get('after_fix')
    out.append(check_eq(
        normalize(after), list(judge.audit_fixed()),
        '探针里 audit_after_fix() 交回 ' + str(list(judge.audit_fixed()))
        + '（不一致 0 组）——修好之后这一格必须回到 0',
        with_todo(('task4_break_it', 'audit_after_fix'),
                  '探针里 audit_after_fix() 对不上：交回 ' + short(repr(after), 30))))

    probe_count = record.get('probe_count')
    bad = []
    if isinstance(probe_count, dict):
        for index, (values, lo, hi) in enumerate(PROBES_4):
            row = probe_count.get(str(index))
            want = (judge.count_matches(values, lo, hi, False),
                    judge.count_matches(values, lo, hi, True))
            if not isinstance(row, dict) or (row.get('right'), row.get('wrong')) != want:
                bad.append(repr(values)[:22])
        out.append(chk(not bad, '探针里 5 组数据（含空数组、单元素）的四格计数与判分另算的逐格一致', lambda: with_todo(('task4_break_it', 'count_matches'),
                      '探针里这几组对不上：' + '、'.join(bad))))
    else:
        out.append((False, with_todo(('task4_break_it', 'count_matches'),
                                     '探针里 count_matches 没被调起来')))
    return out


# ── 第 5 层 · 脚本单跑、行数、耗时不是占位值 ────────────────────────────

def layer5(loaded, runs):
    """四个脚本逐个单跑：退出码 0、0 处 Traceback、行数对得上。

    这一层读的就是脚本自己打印的行——**打印行是判分接口**，多一行少一行也报出来。
    """
    out = []
    for name in TASK_FILES:
        code, text, tracebacks = runs.get(name, (None, '', 0))
        item = ('task1_bottleneck' if name.startswith('task1') else
                'task2_tuning' if name.startswith('task2') else
                'task3_builtin' if name.startswith('task3') else 'task4_break_it')
        if code is None:
            out.append((False, name + ' 没跑起来：' + short(text, 60)))
            continue
        out.append(check_eq(
            code, 0,
            name + ' 单独跑退出码 0',
            name + ' 单独跑退出码是 ' + str(code)
            + '——把它单跑一次，看最后几行（判分要读的就是它打印的行）：\n'
            + '\n'.join(text.strip().splitlines()[-8:])))
        out.append(chk(tracebacks == 0, name + ' 单独跑 0 处 Traceback', lambda: name + ' 单独跑出现了 ' + str(tracebacks) + ' 处 Traceback'
                    + '——先把这个脚本单跑修到退出码 0，再谈别的  → 这一条指 '
                    + todo_of(item, loaded.REQUIRED[item][0])))
        want_lines = EXPECT_LINES[name]
        out.append(check_eq(
            line_count(text), want_lines,
            name + ' 打印了 ' + str(want_lines) + ' 行——与参考解逐行数一致',
            name + ' 打印了 ' + str(line_count(text)) + ' 行，期望 ' + str(want_lines)
            + ' 行——脚本的判分行是接口，别删；没有实现时也要把全部判分行打出来'
              '（值可以是占位值），但行数不能变'))
    return out


def layer5b(loaded, runs):
    """计时那几行必须真量出来：全部 0.000000 就是占位值（退化守卫的最后一关）。"""
    out = []
    text = runs.get('task2_tuning.py', (None, '', 0))[1]
    values = re.findall(r'第\s*\d+\s*级耗时\s+([0-9.]+)\s*秒', text)
    seconds = []
    for item in values:
        try:
            seconds.append(float(item))
        except ValueError:
            continue
    if not values:
        out.append((False, with_todo(('task2_tuning', 'tier_times'),
                                     'task2 打印的行里一行「第 N 级耗时 … 秒」都没有'
                                     '——那几行是判分接口，别改')))
    elif real_times(seconds) == 0:
        out.append((False, with_todo(('task2_tuning', 'tier_times'),
                                     '四级耗时全是 0.000000——这是**占位值**。'
                                     '耗时可以抖动、可以慢，但不能一格都没量：'
                                     '「0 跟 0 比」是掷硬币，不是证据'
                                     '（第 26 课就是在这里栽的）')))
    else:
        out.append((True, '四级耗时里 ' + str(real_times(seconds))
                          + ' 格不是 0.000000：'
                          + '、'.join(judge.fmt_seconds(item) for item in seconds)
                          + '——退化守卫过了（判分只在不是占位值时才拿耗时当辅助证据）'))

    text1 = runs.get('task1_bottleneck.py', (None, '', 0))[1]
    seg = re.findall(r'实测\s+([A-Za-z_]+)\s+([0-9.]+)\s+秒', text1)
    seg_seconds = []
    for _name, item in seg:
        try:
            seg_seconds.append(float(item))
        except ValueError:
            continue
    if not seg:
        out.append((False, with_todo(('task1_bottleneck', 'analyze_segments'),
                                     'task1 打印的行里一行「实测 段名 秒数 秒」都没有')))
    elif real_times(seg_seconds) == 0:
        out.append((False, with_todo(('task1_bottleneck', 'analyze_segments'),
                                     '三段的实测耗时全是 0.000000（占位值）——'
                                     '分段的钱要真花一次，不然「哪一段慢」无从谈起')))
    else:
        out.append((True, '三段里 ' + str(real_times(seg_seconds))
                          + ' 段的耗时不是 0.000000：'
                          + '、'.join(name + ' ' + judge.fmt_seconds(value)
                                      for (name, _old), value in zip(seg, seg_seconds))
                          + '——中位数口径，单次抖动不参与'))
    return out


# ── 主流程 ──────────────────────────────────────────────────────────────

LAYERS = [
    ('第 1 层 · 先量出瓶颈：三段各多少次操作、size() 被调几次',
     [layer1, layer1b],
     'task1_bottleneck.py 的 TODO 1 到 TODO 5（segment_ops、analyze_segments、'
     'segment_list_in / segment_set_in、count_size_calls、count_between）'),
    ('第 2 层 · 四招优化，每一招都留记录（判死的是次数，不是秒数）',
     [layer2, layer2b],
     'task2_tuning.py 的 TODO 1 到 TODO 5（optimization_steps、tier_steps、solve_tier、'
     'tier_times、audit_answers）'),
    ('第 3 层 · 和内置实现比，并说清差在哪一层',
     [layer3, layer3b],
     'task3_builtin.py 的 TODO 1 到 TODO 6（compare_with_builtin、compute_answer、'
     'work_of、recursion_ceiling、recursion_probe、distance）'),
    ('第 4 层 · 故意写错一次：对拍抓不抓得住',
     [layer4, layer4b],
     'task4_break_it.py 的 TODO 1 到 TODO 4（audit_broken_once、count_matches、'
     'audit、audit_after_fix）'),
    ('第 5 层 · 四个脚本单跑、行数、耗时不是占位值',
     [layer5, layer5b],
     '四个脚本里的判分行与那几处计时（打印行是接口，别改；TODO 补齐后这些值自然就对了）'),
]


def collect_runs():
    """四个脚本各单跑一次（两路证据里的第一路）。"""
    runs = {}
    for name in TASK_FILES:
        runs[name] = run_script(name)
    return runs


def main():
    print('StudyMate lab 0029 · 自动判分（常数因子优化：先量再动）')
    print('目录：' + str(HERE))
    print('判据分层：次数（操作 / 循环 / 比较 / 读入 / 值访问）是**确定量**，判死的就是它；')
    print('          耗时只当辅助证据，一律带噪声容差 ' + str(NOISE)
          + ' 与退化守卫（基线 < ' + judge.fmt_seconds(FLOOR) + ' 秒不判）。')
    print()
    loaded = Loaded()
    runs = collect_runs()
    passed = 0
    failed = 0
    layers_ok = 0
    for title, checks, todo_scope in LAYERS:
        print(title)
        layer_ok = True
        for check in checks:
            try:
                if check in (layer5, layer5b):
                    results = check(loaded, runs)
                else:
                    results = check(loaded)
            except Exception:                             # 判分自己也不许崩
                results = [(False, '判分自己这一组抛了异常，把下面这段贴给教练：\n'
                                   + traceback.format_exc())]
            for ok, message in results:
                if not ok and '这一条指' not in message:
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
    print('五层：' + str(layers_ok) + ' 层通过、' + str(len(LAYERS) - layers_ok)
          + ' 层还没过（共 ' + str(passed) + ' 条 PASS、' + str(failed) + ' 条 FAIL）')
    if failed == 0:
        print('五层全过。现在去对照 ../solutions/0029-constant-factor-tuning/：')
        print('比一比四招各是怎么落的、对拍的数据是按什么量级造的，'
              '再用一句话回答「你凭什么相信优化之后答案还是对的」。')
        return 0
    print('卡住了先读 ../README.md 的「卡壳顺序」，再看每条 FAIL 后面点出的那一段 TODO。')
    print('判分读的就是四个脚本打印出来的行，也别改那些 print。')
    print('全部过了再对照 ../solutions/0029-constant-factor-tuning/。')
    return 1


if __name__ == '__main__':
    sys.exit(main())
