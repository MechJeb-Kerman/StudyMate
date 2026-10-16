#!/usr/bin/env python3
r"""lab 0027 · 自动判分（实验三：让助手推荐并验证）

用法（在 lab/0027-lab-03-recommend-and-verify/ 目录里）：

    py run_tests.py

判法：**五层**，一层里几条检查各自给 PASS / FAIL。

    第 1 层 · 提示词的四样约束齐了吗
        格式固定 / 不许有别的文字 / 取值范围（八张族名表全列）/ 转义约定，
        逐条去认锚点；再核对题面原样出现在提示词里、提示词长什么样。
        最后一条是这一层的要害：`call_model` 必须是**唯一的联网点**，
        它得明确地抛 NotImplementedError——离线环境里它是那道缝，不是能跑通的请求。

    第 2 层 · 解析器六种形态过五种
        判分自己再造六种形态（用的就是课件那六段的原文），逐条跑你的两个解析器：
        朴素 json.loads 必须只过 1 种，加固版必须过 5 种，第六种两版都必须失败。
        失败的**方式**是本层的重点：必须交回一个明确的失败标记（字符串），
        不许抛异常、不许交回 None、不许交回半个字典。
        再加六组判分自己造的探针样本（与六种形态不重合）：K 组能解析、6-K 组不能，
        两边都要对上——表背下来了、解析器没写出来，这一条会露。

    第 3 层 · 关键词打分对六道题面
        拿 tools.canonical_classify 这个**另一个实现**逐道题面打分，跟你的候选列表对照。
        「合并果子」那一行必须有背包的并列（命中『重量』这个假阳性**要如实保留**），
        「岛屿数量」那一行图的搜索要排在并查集前面——表改窄、词表乱序，
        这两条就没了，判分会点名说哪一条对不上。

    第 4 层 · 端到端：同族两个实现结论不同
        用判分自己的样本调你的 run_trial：A（按开始时间排）选出 1 个、被否掉并附反例，
        B（按结束时间排）选出 6 个、通过，暴力最优 6 个，一整条链里 1 个通过。
        再换一组数据（区间数不是 6）跑一次，结论必须跟着数据变——
        把数字写死的会被抓住。然后把「两个实现都过」的情形交给 nothing_passed，
        它要认得出「这条链没验证出东西」；最后用带**没转义的引号**的假模型跑一遍，
        resolve 必须交回失败结论，而不是抛出来或者不声不响地当成通过。

    第 5 层 · 打印行逐字对得上、四个文件都能单独跑、离线可跑
        逐字读四个脚本打印出来的判分行（那些行就是接口，别改它们）；
        检查每个任务文件单跑退出码是 0、没有 Traceback；
        再把 socket.socket 掐掉跑一遍整条链——判分**绝不许联网**，
        断了网这条链还得给出同一个结论。顺便确认 call_model 真的会抛 NotImplementedError，
        fake_model 交回的是干净的一行 JSON。

判分不判的东西：提示词的文笔、注释写得多不多、候选实现写得漂不漂亮，由 lab/README.md
的自查清单与课件那一节回答；这里只管能不能跑、口径对不对、结论是不是算出来的。

退出码：五层都过是 0；还有没过的（或跳过的）是 1。
"""

from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import tools as judge                                     # noqa: E402  给好的，别改
from tools import (FENCE, PROBLEMS, PROBE_SAMPLES, PROMPT_REQUIRED, candidate_impl,  # noqa: E402
                   canonical_trial, case_intervals, classify_expected, naive_ok,
                   prompt_missing, robust_ok, sample_texts)

TASK_FILES = ['task1_prompt.py', 'task2_parse.py', 'task3_classify.py', 'task4_pipeline.py']

# 判分用的样本：区间数刻意不是 6，用来分开「算出来的」与「写死的」。
TRIAL_SAMPLES = [6, 3]

# 第六种形态样本在课件里的原文（判分自己写一遍，不从工具里抄）。
TRAP_TEXT = '{"family": "二分答案", "why": "题目说"最小化最大值""}'

# 六道题面在课件那一节里的**首选行**（逐字）。
EXPECT_EXPLAIN = {
    '木材加工': "题面「木材加工」首选 二分答案（命中 2 个：['最大化', '最长']）",
    '岛屿数量': "题面「岛屿数量」首选 图的搜索（命中 1 个：['网格']）",
    '合并果子': "题面「合并果子」首选 堆（命中 1 个：['每次取最小']）",
    '区间调度': "题面「区间调度」首选 贪心（命中 3 个：['区间', '不相交', '按结束时间']）",
    '第 k 大': "题面「第 k 大」首选 堆（命中 1 个：['第 k 大']）",
    '跳石头': "题面「跳石头」首选 二分答案（命中 1 个：['最短']）",
}


# ── 载入学生写的四个文件 ────────────────────────────────────────────────

class Loaded:
    """逐个载入四个任务文件 → 记下模块、载入异常、以及缺了哪些名字。

    四道缝各自独立：某一个文件坏了，只有它负责的那一层会报载入失败。
    """

    REQUIRED = {
        'task1_prompt': ['build_prompt', 'call_model', 'fake_model'],
        'task2_parse': ['parse_naive', 'parse_robust', 'explain_samples'],
        'task3_classify': ['classify', 'explain_problems'],
        'task4_pipeline': ['resolve', 'run_trial', 'nothing_passed'],
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


# 每个判分接口落在哪一段 TODO 上——FAIL 后面都带上它，学生不用猜该补哪一段。
TODO_OF = {
    ('task1_prompt', 'build_prompt'): 'task1_prompt.py TODO 1',
    ('task1_prompt', 'call_model'): 'task1_prompt.py TODO 2',
    ('task1_prompt', 'fake_model'): 'task1_prompt.py TODO 3',
    ('task1_prompt', 'recommend'): 'task1_prompt.py TODO 4',
    ('task2_parse', 'parse_naive'): 'task2_parse.py TODO 1',
    ('task2_parse', 'parse_robust'): 'task2_parse.py TODO 2',
    ('task2_parse', 'explain_samples'): 'task2_parse.py TODO 3',
    ('task3_classify', 'classify'): 'task3_classify.py TODO 1',
    ('task3_classify', 'explain_problems'): 'task3_classify.py TODO 2',
    ('task4_pipeline', 'resolve'): 'task4_pipeline.py TODO 1',
    ('task4_pipeline', 'run_trial'): 'task4_pipeline.py TODO 2',
    ('task4_pipeline', 'nothing_passed'): 'task4_pipeline.py TODO 3',
}


def todo_of(module, item):
    return TODO_OF.get((module, item), item)


def with_todo(item, text):
    """在一条 FAIL 后面补上「这一段在哪个文件哪个 TODO」。"""
    return text + '  → 这一条指 ' + todo_of(*item)


def short(text, limit=60):
    text = '' if text is None else str(text)
    return text if len(text) <= limit else text[:limit] + '…'


# ── 判据小工具：Python 值、布尔、打印行逐字、标记字符串 ─────────────────

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
    return False, bad + '（交回 ' + short(repr(actual), 56) + '，期望 ' + short(repr(expected), 56) + '）'


def check_bool(actual, expected, good, bad):
    """要求的这一格必须是 True / False 本身，不是 1 / 0 / 'True'。"""
    if actual is expected:
        return True, good
    if isinstance(actual, bool):
        return False, bad + '（交回 ' + repr(actual) + '，期望 ' + repr(expected) + '）'
    return False, (bad + '（交回 ' + short(repr(actual), 40) + '——这一格要是 True / False 本身，'
                   '不是 ' + type(actual).__name__ + '）')


def check_line(actual, tokens, good, bad, prefix=False):
    """打印行对得上吗：先按空白切、再一段段比，第一个不一样的地方点名。

    prefix=True 时只要求**以这几段开头**，后面还有别的也认——
    用在「一行里带着整张表」的场合（比如「可选算法族共 8 个: 二分答案、…」）。
    """
    got = str(actual).split()
    want = [str(token).split() for token in tokens]
    want = [piece for group in want for piece in group]
    if got == want or (prefix and got[:len(want)] == want):
        return True, good
    for i, piece in enumerate(want):
        if i >= len(got):
            return False, (bad + '（这一行到第 ' + str(i + 1) + ' 段就没了，期望还有 '
                           + repr(piece) + '；实际 ' + short(repr(actual), 56) + '）')
        if got[i] != piece:
            return False, (bad + '（第 ' + str(i + 1) + ' 段是 ' + repr(got[i])
                           + '，期望 ' + repr(piece) + '；整行 ' + short(repr(actual), 56) + '）')
    if prefix:
        return True, good
    return False, bad + '（后面还多出 ' + repr(' '.join(got[len(want):])) + '）'


def is_marker(value):
    """失败标记的形状：一头一尾都是尖括号的字符串。"""
    return isinstance(value, str) and value.startswith('<') and value.endswith('>')


def as_dict(got):
    """交回的东西是个字典吗（判分读 resolve / explain 的返回值时用）。"""
    return got if isinstance(got, dict) else None


def same_table(got, expected):
    """候选列表对不对得上：命中数、族名、命中词表三格逐格比。"""
    if not isinstance(got, list) or len(got) != len(expected):
        return False
    for row, want in zip(got, expected):
        if not (isinstance(row, (list, tuple)) and len(row) == 3):
            return False
        if tuple(row) != tuple(want):
            return False
    return True


def first_bad_row(got, expected):
    """第一处不一样的候选，交回一句人话。"""
    for i in range(min(len(got), len(expected))):
        if tuple(got[i]) != tuple(expected[i]):
            return ('第 ' + str(i + 1) + ' 个候选是 ' + short(repr(tuple(got[i])), 48)
                    + '，期望 ' + short(repr(expected[i]), 48))
    return '长度不一样：交回 ' + str(len(got)) + ' 个候选，期望 ' + str(len(expected)) + ' 个'


# ── 第 1 层 · 提示词的四样约束齐了吗 ────────────────────────────────────

def layer1(loaded):
    label = 'task1_prompt.py '
    if not loaded.ok('task1_prompt'):
        return [(False, loaded.why(label, 'task1_prompt'))]

    problem = PROBLEMS['区间调度']
    prompt, error = attempt(loaded.fn('task1_prompt', 'build_prompt'), problem)
    if error is not None:
        return [(False, with_todo(('task1_prompt', 'build_prompt'),
                                  'build_prompt(题面) 报错' + error_note(error)))]
    if not isinstance(prompt, str) or not prompt.strip():
        return [(False, with_todo(('task1_prompt', 'build_prompt'),
                                  'build_prompt 交回的不是一段非空文本：' + short(repr(prompt))
                                  + '——留白版交回的是一段空字符串'))]
    out = []
    missing = prompt_missing(prompt, problem)
    if missing:
        names = '、'.join(dict.fromkeys(missing))
        out.append((False, with_todo(('task1_prompt', 'build_prompt'),
                                     '提示词里缺这几样：' + names
                                     + '。四样约束缺一样后面就会在哪一段出问题：'
                                       '格式不钉死 → 解析器不知道有哪些键；'
                                       '不说「不要围栏」→ 六种形态里立刻有四种解析不了；'
                                       '不限定取值范围 → 模型给出项目里没有对应实现的名字；'
                                       '不约定转义 → 第六种那种内容不合法谁也救不了')))
    else:
        out.append((True, '四样约束齐全（' + '、'.join(name for name, _ in PROMPT_REQUIRED)
                          + '），八张族名表全列上了（' + judge.FAMILY_LIST_MARK + '），'
                            '题面也原样在里面'))
    return out


def layer1b(loaded):
    """提示词的形状与那两行的逐字对照（单独的几条，FAIL 时好指到具体哪一行）。"""
    label = 'task1_prompt.py '
    if not loaded.ok('task1_prompt'):
        return [(False, '提示词形状这一组跳过：先让上面那一条过（' + label + '载入不完整）')]
    problem = PROBLEMS['区间调度']
    out = []
    source = Path(loaded.modules['task1_prompt'].__file__).read_text(encoding='utf-8')

    head, error = attempt(loaded.fn('task1_prompt', 'build_prompt'), '  设备夹紧力计算问题  ')
    ok_probe = (isinstance(head, str) and head.strip() and '设备夹紧力计算问题' in head)
    out.append((bool(ok_probe) and error is None,
                ('拿一段带首尾空白的题面试 build_prompt：题面原样进去了，'
                 '说明你用的是 problem.strip()，没把空白也裹进去')
                if ok_probe and error is None else
                with_todo(('task1_prompt', 'build_prompt'),
                          '拿一段带首尾空白的题面试 build_prompt 没通过对上：' + short(repr(head))
                          + error_note(error) + '——题面要 problem.strip() 之后原样进去')))

    fence_hits = sum(line.count(FENCE) for line in str(head).splitlines())
    if fence_hits:
        out.append((False, with_todo(('task1_prompt', 'build_prompt'),
                                     '提示词里出现了 ' + str(fence_hits) + ' 处围栏标记——要写的是'
                                     '「不要用代码块围栏」这句话，别把围栏本身塞进去')))
    else:
        out.append((True, '提示词里没有围栏标记，只有「不要用代码块围栏」那句话——'
                          '第一步就是把这种形态挡在门外'))

    if FENCE in source:
        out.append((False, 'task1_prompt.py 的源码里出现了连续三个反引号——'
                           '本 lab 的源码里不许有它（会打断阅卷与工具链）。'
                           '要拼围栏就写 FENCE，或者用 ' + repr('`') + ' * 3'))
    else:
        out.append((True, '源码里没有连续三个反引号（要拼就用 '
                          + 'tools.make_fence()，别手写）'))

    text = loaded.fn('task1_prompt', 'build_prompt')(problem)
    out.append(check_line(text.splitlines()[0] if isinstance(text, str) and text.splitlines()
                          else '',
                          ['你是一个算法助教。读下面的题目，判断它最像哪一类算法。'],
                          '提示词第一行与课件逐字一致',
                          with_todo(('task1_prompt', 'build_prompt'),
                                    '提示词第一行的形状与课件不一样')))
    return [item for item in out if item is not None]


# ── 第 2 层 · 解析器六种形态过五种 ──────────────────────────────────────

def layer2(loaded):
    label = 'task2_parse.py '
    if not loaded.ok('task2_parse'):
        return [(False, loaded.why(label, 'task2_parse'))]
    out = []
    samples = sample_texts()
    count_naive = 0
    count_robust = 0
    for name, raw in samples.items():
        expect_naive = naive_ok(raw)
        expect_robust = robust_ok(raw)
        got_naive, err_a = attempt(loaded.fn('task2_parse', 'parse_naive'), raw)
        got_robust, err_b = attempt(loaded.fn('task2_parse', 'parse_robust'), raw)
        if err_a is not None or err_b is not None:
            out.append((False, '「' + name + '」这一条样本把解析器弄崩了'
                               + (error_note(err_a) if err_a else '')
                               + (error_note(err_b) if err_b else '')
                               + '——解析失败要交回失败标记，不许抛异常  → 这一条指 '
                               + todo_of('task2_parse', 'parse_naive') + ' 与 '
                               + todo_of('task2_parse', 'parse_robust')))
            continue
        count_naive += 1 if (isinstance(got_naive, dict) and 'family' in got_naive) else 0
        count_robust += 1 if (isinstance(got_robust, dict) and 'family' in got_robust) else 0
        if expect_naive and not expect_robust:
            out.append((False, '判分自己的两个口径就不一致，「' + name + '」这一条跳过'))
            continue
        ok_shape = True
        if not isinstance(got_naive, dict):
            ok_shape = isinstance(got_naive, str)
        if not isinstance(got_robust, dict):
            ok_shape = ok_shape and isinstance(got_robust, str)
        if not ok_shape:
            out.append((False, '「' + name + '」解析失败时交回的不是失败标记而是 '
                               + type(got_naive if not isinstance(got_naive, dict) else got_robust).__name__
                               + '（' + short(repr(got_naive if not isinstance(got_naive, dict)
                                                  else got_robust), 40)
                               + '）——失败也要是一种值：'
                                 "交回 '<' + 异常类名 + '>' 这样的字符串标记  → 这一条指 "
                               + todo_of('task2_parse', 'parse_naive') + ' 与 '
                               + todo_of('task2_parse', 'parse_robust')))
            continue
        if expect_naive:
            ok = isinstance(got_naive, dict) and got_naive.get('family') == '二分答案'
            out.append((ok, "「" + name + "」朴素版过（拿到 family 二分答案）" if ok else
                        "「" + name + "」朴素版没过：" + short(repr(got_naive), 40)
                        + '——这一种本该直接 json.loads 就拿下的  → 这一条指 '
                        + todo_of('task2_parse', 'parse_naive')))
        else:
            ok = isinstance(got_naive, str)
            out.append((ok, "「" + name + "」朴素版失败并交回标记 " + repr(got_naive) if ok else
                        "「" + name + "」朴素版交回的是 " + short(repr(got_naive), 40)
                        + '——这一种本该失败  → 这一条指 '
                        + todo_of('task2_parse', 'parse_naive')))
        if expect_robust:
            ok = isinstance(got_robust, dict) and got_robust.get('family') == '二分答案'
            out.append((ok, "「" + name + "」加固版过（剥围栏/取大括号之后拿到了 family）" if ok else
                        "「" + name + "」加固版没过：" + short(repr(got_robust), 40)
                        + '——这一种该被加固版拿下来：'
                          '先剥围栏、再取第一个 { 到最后一个 }，正则别忘了 re.S  → 这一条指 '
                        + todo_of('task2_parse', 'parse_robust')))
        else:
            ok = isinstance(got_robust, str)
            out.append((ok, "「" + name + "」加固版也失败并交回标记 " + repr(got_robust) if ok else
                        "「" + name + "」加固版交回的是 " + short(repr(got_robust), 40)
                        + '——这一种**两版都救不了**，它得交回失败标记  → 这一条指 '
                        + todo_of('task2_parse', 'parse_robust')))
    out.append(check_eq(count_naive, 1,
                        '六种形态里朴素版过了 1 种（只认干净 JSON）——与课件一致',
                        '六种形态里朴素版过了 ' + str(count_naive) + ' 种，期望 1 种  → 这一条指 '
                        + todo_of('task2_parse', 'parse_naive')))
    out.append(check_eq(count_robust, 5,
                        '六种形态里加固版过了 5 种（比朴素多认下四种格式浮动）',
                        '六种形态里加固版过了 ' + str(count_robust) + ' 种，期望 5 种  → 这一条指 '
                        + todo_of('task2_parse', 'parse_robust')))
    return out


def probe_oracle_naive(raw):
    """判分的朴素口径，**照着描述自己写一遍**：直接 json.loads，不成功就交回标记。

    这段是**独立证据**：它不吃 tools.safe_load / tools.naive_ok，只用 json 库自己再读一遍。
    两边口径一致时，本层那些探针才算数——只在一边对一个口径上对得上的解析器会被抓住。
    """
    try:
        value = json.loads(raw.strip())
    except Exception as exc:
        return '<' + type(exc).__name__ + '>'
    if isinstance(value, dict) and 'family' in value:
        return value
    return '<不是字典>'


def probe_oracle_robust(raw):
    """判分的加固口径，**照着描述自己写一遍**：剥一层围栏 → 取首尾大括号 → json.loads。"""
    text = raw.strip()
    if text.startswith(FENCE):
        text = text[len(FENCE):]
        first, _, rest = text.partition('\n')
        if first.strip() == 'json':
            text = rest
        else:
            text = first + '\n' + rest if rest else first
        end = text.rfind(FENCE)
        if end != -1:
            text = text[:end]
    text = text.strip()
    lo, hi = text.find('{'), text.rfind('}')
    if lo == -1 or hi == -1 or hi < lo:
        return '<没有找到 JSON 对象>'
    try:
        value = json.loads(text[lo:hi + 1])
    except Exception as exc:
        return '<' + type(exc).__name__ + '>'
    if isinstance(value, dict) and 'family' in value:
        return value
    return '<不是字典>'


def shape_mismatch(got, should_pass):
    """交回的东西形状对不对：该拿下就要是字典，该失败就要是字符串标记。

    对不上时交回一句**说清了实际交回什么**的话（None 就是 None，不是「字典」）；
    形状没问题就交回空串。探针那两组共用它，免得再写两遍同样的判断。
    """
    if should_pass:
        if isinstance(got, dict):
            return ''
        return '本该拿下（交回字典），实际交回 ' + short(repr(got), 30)
    if isinstance(got, str):
        return ''
    return '本该交回失败标记，实际交回 ' + type(got).__name__ + '（' + short(repr(got), 30) + '）'


def layer2b(loaded):
    """探针样本 + 第六种形态 + 打印行（判分自己的样本，用来分开「背表」与「写出来」）。"""
    label = 'task2_parse.py '
    if not loaded.ok('task2_parse'):
        return [(False, '探针这一组跳过：先让上面那一条过（' + label + '载入不完整）')]
    parse_robust = loaded.fn('task2_parse', 'parse_robust')
    parse_naive = loaded.fn('task2_parse', 'parse_naive')
    out = []

    # 判分自己另算一遍的两个口径（probe_oracle_*，不吃 tools 的现成口径），
    # 期望值取自**样本自己的标签**（干净的一段该过、有格式浮动的一层剥完该过、内容不合法的两版都不过）。
    # 两边不一致的那一组跳过：那说明样本本身有歧义，不该算到学生头上。
    rows = []
    skipped = []
    for name, (raw, wanted) in PROBE_SAMPLES.items():
        want_naive = wanted == '朴素也过'
        want_robust = wanted in ('朴素也过', '只有加固过')
        got_naive = probe_oracle_naive(raw)
        got_robust = probe_oracle_robust(raw)
        ok_naive = isinstance(got_naive, dict)
        ok_robust = isinstance(got_robust, dict)
        if ok_naive != want_naive or ok_robust != want_robust:
            skipped.append(name)
            continue
        rows.append((name, raw, want_naive, want_robust))
    if skipped:
        out.append((True, '这几组探针在判分的两个读数口径下不一致，本层跳过它们：'
                          + '、'.join(skipped) + '（它们不是课件那六种形态，不影响成绩）'))

    bad_probes = []
    for name, raw, expect_naive, expect_robust in rows:
        got, error = attempt(parse_robust, raw)
        note = shape_mismatch(got, expect_robust) if error is None else ''
        if error is not None:
            bad_probes.append(name + '（抛出 ' + error + '）')
        elif note:
            bad_probes.append(name + '（' + note + '）')
        else:
            out.append((True, '探针「' + name + '」：加固版'
                              + ('拿下了（' if expect_robust else '交回失败标记（')
                              + short(repr(got), 34) + '）——与判分自己另算一遍的结果一致'))
    if bad_probes:
        out.append((False, '加固版在判分的 ' + str(len(rows)) + ' 组探针样本上有 '
                           + str(len(bad_probes)) + ' 组不对：' + '；'.join(bad_probes)
                           + '——六种形态是表，探针是另一批数据：'
                             '解析器真写出来了，两边才会同时对得上  → 这一条指 '
                           + todo_of('task2_parse', 'parse_robust')))
    else:
        out.append((True, '加固版在判分自己造的 ' + str(len(rows)) + ' 组探针样本上全部符合期望'
                          + '（' + str(sum(1 for _, _, _, flag in rows if flag)) + ' 组能拿下、'
                          + str(sum(1 for _, _, _, flag in rows if not flag)) + ' 组该失败）'))

    bad_naive = []
    for name, raw, expect_naive, expect_robust in rows:
        got, error = attempt(parse_naive, raw)
        note = shape_mismatch(got, expect_naive) if error is None else ''
        if error is not None:
            bad_naive.append(name + '（抛出 ' + error + '）')
        elif note:
            bad_naive.append(name + '（' + note + '）')
    out.append((not bad_naive,
                '朴素版在探针样本上全对：干净的那一组能过，带围栏/带解释的都交回标记'
                if not bad_naive else
                '朴素版在探针样本上有 ' + str(len(bad_naive)) + ' 组不对：' + '；'.join(bad_naive)
                + '——朴素写法就是直接 json.loads，别在它里面也加剥围栏的活  → 这一条指 '
                + todo_of('task2_parse', 'parse_naive')))

    for func_name in ('parse_naive', 'parse_robust'):
        got, error = attempt(loaded.fn('task2_parse', func_name), TRAP_TEXT)
        todo = todo_of('task2_parse', func_name)
        if error is not None:
            out.append((False, func_name + ' 吃到第六种形态（引号没转义）时抛出了 ' + error
                               + '——这一条正是本层的重点：它必须**交回一个失败标记**，'
                                 '让整条链带着「这一段失败了」继续往下走  → 这一条指 ' + todo))
        elif not is_marker(got):
            out.append((False, func_name + ' 吃到第六种形态时交回的是 ' + short(repr(got), 40)
                               + '——它必须交回一个明确的失败标记（两头尖括号的字符串），'
                                 '不是 None、不是半个字典  → 这一条指 ' + todo))
        else:
            out.append((True, func_name + ' 吃到第六种形态交回 ' + repr(got)
                              + '——是个明确的失败标记，整条链能带着它继续走'))

    explained, error = attempt(loaded.fn('task2_parse', 'explain_samples'))
    if error is not None:
        out.append((False, 'explain_samples() 报错' + error_note(error)
                           + '——要把六种形态逐条打印出来，交回两个整数  → 这一条指 '
                           + todo_of('task2_parse', 'explain_samples')))
        return out
    if not (isinstance(explained, (tuple, list)) and len(explained) == 2):
        out.append((False, 'explain_samples() 交回的不是两个整数：' + short(repr(explained), 40)
                           + '——交回 (朴素过的种数, 加固过的种数)  → 这一条指 '
                           + todo_of('task2_parse', 'explain_samples')))
        return out
    out.append(check_eq(list(explained), [1, 5],
                        'explain_samples() 交回的 (朴素, 加固) 是 (1, 5)',
                        'explain_samples() 交回的 (朴素, 加固) 对不上'))
    return out


# ── 第 3 层 · 关键词打分对六道题面 ──────────────────────────────────────

def layer3(loaded):
    label = 'task3_classify.py '
    if not loaded.ok('task3_classify'):
        return [(False, loaded.why(label, 'task3_classify'))]
    out = []

    def fail3(message):
        return (False, with_todo(('task3_classify', 'classify'), message))

    for title, text in PROBLEMS.items():
        expected = classify_expected(text)
        got, error = attempt(loaded.fn('task3_classify', 'classify'), text)
        if error is not None:
            out.append(fail3('classify(题面「' + title + '」) 报错' + error_note(error)))
            continue
        if not isinstance(got, list):
            out.append(fail3('题面「' + title + '」交回的不是一张候选表：' + short(repr(got), 40)
                             + '——形状是 [(命中数, 族名, 命中词表), ...]，空表也要是 []'))
            continue
        if same_table(got, expected):
            out.append((True, '题面「' + title + '」的候选列表与另一个实现逐格对上（首选 '
                              + got[0][1] + '，命中 ' + str(got[0][0]) + ' 个：'
                              + repr(got[0][2]) + '）'))
        else:
            out.append(fail3('题面「' + title + '」的候选列表对不上：'
                             + first_bad_row(got, expected)
                             + '——表就是 tools.FAMILIES，逐字用它；'
                               '排序是先按命中数降序、再按族名字典序升序'))
    empty, error = attempt(loaded.fn('task3_classify', 'classify'), '完全无关的一段话')
    ok_empty = error is None and isinstance(empty, list) and empty == []
    out.append((ok_empty, '没命中任何关键词时交回空表 []' if ok_empty else
                fail3('拿一段毫不相关的话试 classify，交回的是 ' + short(repr(empty), 40)
                      + error_note(error) + '——一个都没命中的族不该放进候选表')))
    return out


def layer3b(loaded):
    """六道题面的首选行逐字 + 合并果子的并列背包（假阳性要如实保留）。"""
    label = 'task3_classify.py '
    if not loaded.ok('task3_classify'):
        return [(False, '打印行这一组跳过：先让上面那一条过（' + label + '载入不完整）')]
    out = []
    got, error = attempt(loaded.fn('task3_classify', 'explain_problems'))
    if error is not None:
        out.append((False, with_todo(('task3_classify', 'explain_problems'),
                                     'explain_problems() 报错' + error_note(error))))
        return out
    rows = as_dict(got)
    if rows is None:
        out.append((False, with_todo(('task3_classify', 'explain_problems'),
                                     'explain_problems() 交回的不是字典：' + short(repr(got), 40)
                                     + '——交回 {题面名: 候选列表}')))
        return out
    for title in PROBLEMS:
        if title not in rows:
            out.append((False, with_todo(('task3_classify', 'explain_problems'),
                                         'explain_problems() 交回的表里没有题面「' + title + '」')))
            continue
        expected = classify_expected(PROBLEMS[title])
        if same_table(rows[title], expected):
            out.append((True, '题面「' + title + '」那一行与课件逐字一致：' + EXPECT_EXPLAIN[title]))
        else:
            out.append((False, with_todo(('task3_classify', 'explain_problems'),
                                         '题面「' + title + '」那一行对不上：'
                                         + first_bad_row(rows[title], expected)
                                         + '；课件那一行是 ' + EXPECT_EXPLAIN[title])))

    merge = rows.get('合并果子')
    tied = []
    if isinstance(merge, list) and merge and len(merge) > 1:
        top = merge[0][0] if isinstance(merge[0], (list, tuple)) and merge[0] else None
        tied = [row for row in merge[1:]
                if isinstance(row, (list, tuple)) and row and row[0] == top]
    tied_names = [row[1] for row in tied]
    if merge == classify_expected(PROBLEMS['合并果子']) and len(merge) == 2:
        out.append((True, '「合并果子」那一行是 堆（命中 1 个）并列 背包（命中 1 个：'
                          + repr(tied[0][2]) + '）——关键词的假阳性如实保留了，这是要看的现象'))
    elif merge == classify_expected(PROBLEMS['合并果子']):
        out.append((False, '「合并果子」的候选表与另一个实现对上了，但候选数是 ' + str(len(merge))
                           + '，期望 2 —— 判分自己的口径这边也应当是 2 个'))
    else:
        out.append((False, with_todo(('task3_classify', 'classify'),
                                     '「合并果子」那一行没有背包的并列（并列的有：'
                                     + ('、'.join(tied_names) if tied_names else '（没有并列）') + '）。'
                                     + '题面里有「重量」两个字，背包就该以 1 个命中并列出现——'
                                       '这是关键词匹配的假阳性，**要如实报告，不许把表改窄**。'
                                       '正确的那一行是：' + EXPECT_EXPLAIN['合并果子'])))
    return out


# ── 第 4 层 · 端到端：同族两个实现结论不同 ──────────────────────────────

def make_recording(json_text):
    """造一个会记账的假模型：它记下每次收到的提示词，交回给好的那段文本。

    这就是那道**缝**：真模型（要联网）与假模型（离线）是同一个位置上的两个函数，
    换了它，链路上其余部分一行都不用改。
    """
    calls = []

    def recorder(prompt):
        calls.append(prompt)
        return json_text

    return recorder, calls


def probe_resolve(loaded, raw, label):
    """用一段文本探你的 resolve：交回符合统一的 (结果, 检查项) 两样。"""
    got, error = attempt(loaded.fn('task4_pipeline', 'resolve'), raw)
    if error is not None:
        return None, 'resolve(' + label + ') 抛出了 ' + error + '——解析失败也要交回一个**结论**' \
                     '（{"ok": False, "reason": ...}），不许把异常放出去把整条链打断'
    if not isinstance(got, dict):
        return None, 'resolve(' + label + ') 交回的不是字典：' + short(repr(got), 40)
    if got.get('ok') is not True:
        return None, ('resolve(' + label + ') 说没解析成功：' + short(repr(got), 60)
                      + '——这一段是干净的 JSON，短样板该吃得下')
    bad = []
    for key, want in (('family', '贪心'), ('confidence', '中'), ('why', '没认出来，先猜一个')):
        if got.get(key) != want:
            bad.append(key + ' 是 ' + short(repr(got.get(key)), 24) + '，期望 ' + repr(want))
    if bad:
        return None, 'resolve(' + label + ') 交回的结论里 ' + '；'.join(bad)
    return got, ''


def unpack_row(row):
    """一条结论 → (名字, 怎么排的, 选出个数, 通过吗, 反例)。canonical_trial 交回的是四格。"""
    if isinstance(row, tuple) and len(row) == 4:
        name, picked, passed, counter = row
        return name, judge.candidate_how(name), picked, passed, counter
    return None


def layer4(loaded):
    label = 'task4_pipeline.py '
    if not loaded.ok('task4_pipeline'):
        return [(False, loaded.why(label, 'task4_pipeline'))]
    out = []
    raw_clean = ('{"family": "贪心", "confidence": "中", "why": "没认出来，先猜一个"}')
    rec_fn, calls = make_recording(raw_clean)

    recommend = loaded.fn('task1_prompt', 'recommend') if loaded.ok('task1_prompt') else None
    if callable(recommend):
        problem = PROBLEMS['区间调度']
        argued, error = attempt(recommend, problem, rec_fn)
        if error is None and calls and isinstance(argued, str) and argued.strip():
            out.append((True, '链路第一段接上了：recommend(题面, 假模型) 把提示词交给了那道缝，'
                              '假模型交回 ' + short(argued, 44) + '——模型调用是换得掉的一个函数'))
        elif error is not None:
            out.append((False, 'recommend(题面, 假模型) 报错' + error_note(error)))
        else:
            out.append((False, 'recommend(题面, 假模型) 没有把提示词交给传进来的那个模型函数'
                               '——它得走 model(build_prompt(problem)) 这条缝'))
    else:
        out.append((False, 'task1_prompt.py 里没有 recommend 可以让判分拿假模型试——'
                           '这一段是链路的接缝（题面 → 提示词 → 模型），别删它'))

    resolved, note = probe_resolve(loaded, raw_clean, '干净 JSON')
    out.append((resolved is not None, 'resolve() 吃得下干净 JSON，交回 family=贪心、confidence=中'
                if resolved is not None else note))

    trap, error = attempt(loaded.fn('task4_pipeline', 'resolve'), TRAP_TEXT)
    if error is not None:
        out.append((False, 'resolve(第六种形态) 抛出了 ' + error
                           + '——第六种（引号没转义）必须交回失败结论'))
    elif not isinstance(trap, dict) or trap.get('ok') is not False:
        out.append((False, 'resolve(第六种形态) 交回 ' + short(repr(trap), 50)
                           + '——它该交回 {"ok": False, "reason": ...}：'
                             '解析器的能力有边界，但**结论的形状**不能变'))
    elif not is_marker(trap.get('reason')):
        out.append((False, 'resolve(第六种形态) 的 reason 是 ' + short(repr(trap.get('reason')), 40)
                           + '——reason 要带引原文并点名异常类型，'
                             "形状是 '<' + 异常类名 + '>'"))
    else:
        out.append((True, 'resolve(第六种形态) 交回失败结论，reason ' + repr(trap.get('reason'))
                          + '——它没有抛异常，也没有交回半个字典'))
    return out


def layer4b(loaded):
    """run_trial 在**判分自己的样本**上算得对不对（数字写死的会被这一组抓住）。"""
    label = 'task4_pipeline.py '
    if not loaded.ok('task4_pipeline'):
        return [(False, '端到端这一组跳过：先让上面那一条过（' + label + '载入不完整）')]
    out = []
    run_trial = loaded.fn('task4_pipeline', 'run_trial')
    for size in TRIAL_SAMPLES:
        intervals = case_intervals(size)
        expected_rows, expected_want = canonical_trial(intervals)
        got, error = attempt(run_trial, '贪心', intervals)
        if error is not None:
            out.append((False, 'run_trial(贪心, 区间数 ' + str(size) + ') 报错' + error_note(error)))
            continue
        if not (isinstance(got, tuple) and len(got) == 2):
            out.append((False, 'run_trial(贪心, 区间数 ' + str(size) + ') 交回的不是两样：'
                               + short(repr(got), 40) + '——交回 (verdicts, want)'))
            continue
        verdicts, want = got
        if not isinstance(verdicts, (list, tuple)) or len(verdicts) != len(expected_rows):
            out.append((False, 'run_trial(贪心, 区间数 ' + str(size) + ') 交回的结论条数是 '
                               + str(len(verdicts) if isinstance(verdicts, (list, tuple)) else '?')
                               + '，期望 ' + str(len(expected_rows)) + ' 条（每个候选实现一条，'
                                 '两个都跑，别短路）'))
            continue
        desc = []
        ok_all = True
        for row, expected in zip(verdicts, expected_rows):
            if not (isinstance(row, tuple) and len(row) == 5):
                out.append((False, 'run_trial 交回的结论形状不对：' + short(repr(row), 46)
                                   + '——一条是 (名字, 怎么排的, 选出个数, 通过吗, 选出那张表)'))
                ok_all = False
                break
            name, how, picked, passed, table = row
            exp_name, exp_picked, exp_passed, exp_table = expected
            if name != exp_name or how != judge.candidate_how(exp_name):
                out.append((False, '结论里的名字/叫法对不上：交回 '
                                   + short(repr((name, how)), 40) + '，期望 '
                                   + short(repr((exp_name, judge.candidate_how(exp_name))), 40)))
                ok_all = False
                break
            if picked != exp_picked:
                out.append((False, '实现 ' + name + ' 在区间数 ' + str(size) + ' 的样本上'
                                   + '「选出个数」是 ' + repr(picked) + '，期望 ' + repr(exp_picked)
                                   + '——这个数要从 len(函数(数据)) 来，不能写死'))
                ok_all = False
                break
            if passed is not exp_passed:
                out.append((False, '实现 ' + name + ' 在区间数 ' + str(size) + ' 的样本上'
                                   + '「通过吗」是 ' + short(repr(passed), 20) + '，期望 '
                                   + repr(exp_passed) + '——通过与否是「选出个数 == 暴力最优」算出来的，'
                                     '要交回 True / False 本身'))
                ok_all = False
                break
            if not (isinstance(table, (list, tuple)) and list(table) == list(exp_table)):
                out.append((False, '实现 ' + name + ' 交回的「选出那张表」是 ' + short(repr(table), 40)
                                   + '，期望 ' + short(repr(list(exp_table)), 40)
                                   + '——每个实现都把它实际选出来的那张表交回来：'
                                     '没通过的那一张就是**反例**，通过的判分用它核对个数'))
                ok_all = False
                break
            desc.append(name + ' 选出 ' + str(picked) + ' 个'
                        + ('（被否掉，反例 ' + short(repr(list(table)), 30) + '）' if not passed
                           else '（通过）'))
        if ok_all:
            out.append(check_eq(want, expected_want,
                                '区间数 ' + str(size) + ' 这一组：' + '；'.join(desc)
                                + '，暴力最优 ' + str(expected_want) + ' 个——与另算一遍的对上',
                                '区间数 ' + str(size) + ' 这一组的「暴力最优」对不上'))
    return out


def layer4c(loaded):
    """结论行 + nothing_passed + 关键词交叉检查。"""
    label = 'task4_pipeline.py '
    if not loaded.ok('task4_pipeline'):
        return [(False, '结论行这一组跳过：先让上面那一条过（' + label + '载入不完整）')]
    out = []
    verdicts, want = canonical_trial(case_intervals(6))
    own_rows = [unpack_row(row) for row in verdicts]
    got, error = attempt(loaded.fn('task4_pipeline', 'run_trial'), '贪心', case_intervals(6))

    def nothing(items, label_want):
        value, err = attempt(loaded.fn('task4_pipeline', 'nothing_passed'), items)
        return value, err

    empty_value, empty_err = nothing([], '空表')
    out.append((empty_err is None and empty_value is True,
                '交一张空结论表给 nothing_passed：交回 True（什么都没跑，等于什么都没验出来）'
                if empty_err is None and empty_value is True else
                'nothing_passed([]) 交回 ' + short(repr(empty_value), 20) + error_note(empty_err)
                + '——空表要交回 True'))

    fail_rows = [(name, how, picked, False, table)
                 for name, how, picked, _passed, table in own_rows]
    pass_rows = [(name, how, picked, True, table)
                 for name, how, picked, _passed, table in own_rows]
    for rows, expected, words in ((fail_rows, True, '两个实现都被否掉'),
                                  (pass_rows, False, '两个实现都通过'),
                                  (verdicts, False, 'A 被否掉、B 通过')):
        value, err = nothing(rows, words)
        ok = err is None and value is expected
        out.append((ok, words + '时交回 ' + repr(expected) + '：'
                    + ('用 not any 判「一个都没通过」，不是 not all' if ok else
                       '交回的是 ' + short(repr(value), 20) + error_note(err)
                       + '——写成 not all 的话「全过」和「全不过」都会交回 True')))

    if error is not None:
        out.append((False, 'run_trial(贪心, 课件那一组数据) 报错' + error_note(error)))
    elif isinstance(got, tuple) and len(got) == 2:
        rows = got[0]
        if isinstance(rows, (list, tuple)) and len(rows) == 2:
            passed = [row[3] for row in rows if isinstance(row, tuple) and len(row) == 5]
            out.append(check_eq(passed, [False, True],
                                '课件那一组数据上：实现 A 被否掉、实现 B 通过——'
                                '同一个算法族下的两个实现结论不同，这一课最要紧的一句话就在这',
                                '课件那一组数据上两个实现的通过情况对不上'))
        else:
            out.append((False, 'run_trial(贪心, 课件那一组数据) 交回的结论条数是 '
                               + short(repr(len(rows)), 8) + '，期望 2'))

    hint, error = attempt(loaded.fn('task3_classify', 'classify'), PROBLEMS['区间调度'])
    top = None
    if error is None and isinstance(hint, list) and hint:
        top = hint[0][1]
    out.append((top == '贪心',
                '关键词表交叉检查：题面「区间调度」的首选是 贪心，与模型给的一致——'
                '模型选了 A 而关键词表一条都不支持 A，才值得多看一眼'
                if top == '贪心' else
                '关键词表对「区间调度」的首选是 ' + short(repr(top), 20) + '，期望 贪心'
                '——交叉检查这一段要用它'))
    return out


# ── 第 5 层 · 打印行、单跑、离线 ────────────────────────────────────────

def run_script(path):
    """起一个子进程跑一个任务脚本 → (退出码, stdout, stderr)。"""
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    try:
        done = subprocess.run([sys.executable, str(path)], cwd=str(path.parent),
                              capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=90, env=env)
    except Exception as exc:
        return None, '', '起不了子进程：' + type(exc).__name__ + ': ' + str(exc)
    return done.returncode, done.stdout or '', done.stderr or ''


def parse_shown(text):
    """把「标签 值」的行读成 {标签: 值}（值原样保留内部空白）。

    标签后面那一个分隔符是空格还是冒号都认（脚本里有几行照课件带了冒号）。
    同名标签取**最后一次**出现的那一行：脚本里「朴素 / 加固」在六种形态那一组里各出现过一次，
    末尾那一组（第六种形态那两行）才是判分要核对的那一次。
    """
    rows = {}
    for line in text.splitlines():
        line = line.strip()
        for label in SHOWN_LABELS:
            head = label + ' '
            if line.startswith(head):
                rows[label] = line[len(head):]
                break
            head = label + ': '
            if line.startswith(head):
                rows[label] = line[len(head):]
                break
    return rows


SHOWN_LABELS = sorted([
    '模型给的原文', '推荐的算法族',
    '实现 A（按开始时间排）选出', '实现 A 通过吗', '实现 A 反例',
    '实现 B（按结束时间排）选出', '实现 B 通过吗', '实现 B 反例',
    '暴力验证给出的最优', '两个实现选出的个数',
    '实现数', '通过的实现数', '这条链没验证出东西',
    '解析坏掉时的 ok', '解析坏掉时的 reason',
    '题面首选', '模型推荐', '首选与模型一致',
    '假模型返回', '可选算法族共', '围栏那一串的长度', '提示词里的围栏行',
    '朴素过的种数', '加固过的种数', '朴素', '加固', '大括号配平吗',
    '朴素交回的是标记吗', '加固交回的是标记吗', '加固版认下来', '朴素版认下来',
    '首选', '首选命中数', '并列的族', '并列族 背包 命中', '候选数',
    '族名表大小', '木材加工候选数', '区间调度候选数', '岛屿数量首选',
], key=len, reverse=True)


def layer5(loaded):
    runs = [run_script(HERE / name) for name in TASK_FILES]

    # 5a · 四个脚本各自单跑：退出码 0、没有 Traceback
    out = []
    for name, (code, text, err) in zip(TASK_FILES, runs):
        if code is None:
            out.append((False, name + ' 起不了子进程：' + short(err, 80)))
        elif 'Traceback' in err or 'Traceback' in text:
            tail = (err or text).strip().splitlines()
            out.append((False, name + ' 单跑时抛了异常，最后一行是 ' + short(tail[-1], 70)
                               + '——每个任务文件都要能**单独跑通**（退出码 0、0 处 Traceback），'
                                 '判分也是按文件 import 的'))
        elif code != 0:
            out.append((False, name + ' 单跑的退出码是 ' + str(code) + '，期望 0'))
        else:
            out.append((True, name + ' 单跑退出码 0、没有 Traceback'
                              + ('（' + str(len(text.splitlines())) + ' 行输出）' if text else '')))

    # 5b · 逐字读四个脚本打印出来的行
    t1 = parse_shown(runs[0][1])
    t2 = parse_shown(runs[1][1])
    t3 = parse_shown(runs[2][1])
    t4 = parse_shown(runs[3][1])

    if '假模型返回' in t1:
        out.append(check_line(t1['假模型返回'],
                              ['{"family": "二分答案", "confidence": "高", '
                               '"why": "要让最小长度最大化"}'],
                              'task1 的「假模型返回」是干净的一行 JSON（与课件逐字一致）',
                              'task1 的「假模型返回」这一行对不上'))
    else:
        out.append((False, 'task1 的输出里没有「假模型返回」这一行——打印行是判分接口，别改'))
    prompt_lines = [line.strip() for line in runs[0][1].splitlines() if line.strip()]
    prompt_head = [line for line in prompt_lines if line.startswith('|')]
    if prompt_head:
        out.append(check_line(prompt_head[0],
                              ['|', '你是一个算法助教。读下面的题目，判断它最像哪一类算法。'],
                              'task1 打出来的提示词第一行与课件逐字一致（连前面的竖线都在）',
                              'task1 打出来的提示词第一行对不上'))
    else:
        out.append((False, 'task1 没打出带竖线的提示词行（' + str(len(prompt_lines))
                           + ' 行非空输出）——提示词要逐行打印出来自己读一遍，'
                             '判分就按这些行核对'))
    out.append(check_line(t1.get('可选算法族共', ''), ['8'],
                          'task1 打印的族名表是 8 个（取值范围这一段全列上了）',
                          'task1 的「可选算法族共」这一行对不上', prefix=True))
    if t1.get('围栏那一串的长度') != '3 个反引号':
        out.append((False, 'task1 的「围栏那一串的长度」是 '
                           + short(repr(t1.get('围栏那一串的长度')), 24)
                           + '，期望「3 个反引号」——别手写那一串，用 tools.make_fence()'))
    else:
        out.append((True, 'task1 确认围栏那一串是 3 个反引号，而源码里一个都没出现'))
    out.append(check_line(t1.get('提示词里的围栏行', ''), ['0'],
                          '提示词里一行围栏都没有（0 行开头是三个反引号）——'
                          '「不要用代码块围栏」是写给模型看的话，不是让你真加围栏',
                          'task1 的「提示词里的围栏行」这一行对不上'))

    out.append(check_line(t2.get('朴素过的种数', ''),
                          ['1'], 'task2 打印的朴素成绩是 1 种',
                          'task2 的「朴素过的种数」对不上'))
    out.append(check_line(t2.get('加固过的种数', ''),
                          ['5'], 'task2 打印的加固成绩是 5 种',
                          'task2 的「加固过的种数」对不上'))
    for want, row, good, bad in (
            ('<JSONDecodeError>', t2.get('朴素', ''),
             'task2 的「朴素」吃到第六种形态交回 <JSONDecodeError>',
             'task2 的「朴素」那一行对不上'),
            ('<JSONDecodeError>', t2.get('加固', ''),
             'task2 的「加固」吃到第六种形态也交回 <JSONDecodeError>',
             'task2 的「加固」那一行对不上'),
            ('True', t2.get('大括号配平吗', ''),
             'task2 确认第六种的括号是配平的——坏的是字符串内容本身',
             'task2 的「大括号配平吗」那一行对不上'),
            ('<JSONDecodeError>', t2.get('朴素交回的是标记吗', ''),
             'task2 的「朴素交回的是标记吗」是 <JSONDecodeError>——失败是一种值',
             'task2 的「朴素交回的是标记吗」那一行对不上'),
            ('<JSONDecodeError>', t2.get('加固交回的是标记吗', ''),
             'task2 的「加固交回的是标记吗」是 <JSONDecodeError>——失败是一种值',
             'task2 的「加固交回的是标记吗」那一行对不上'),
            ('5', t2.get('加固版认下来', ''),
             'task2 的「加固版认下来」是 5——六种形态里比朴素多认下四种',
             'task2 的「加固版认下来」那一行对不上'),
            ('1', t2.get('朴素版认下来', ''),
             'task2 的「朴素版认下来」是 1',
             'task2 的「朴素版认下来」那一行对不上')):
        out.append(check_line(row, [want], good, bad))

    exact3 = {
        '首选': '堆', '首选命中数': '1', '并列的族': '背包',
        '并列族 背包 命中': '重量', '族名表大小': '8',
        '木材加工候选数': '1', '区间调度候选数': '1', '岛屿数量首选': '图的搜索',
        '候选数': '2',
    }
    for key, want in exact3.items():
        if key not in t3:
            out.append((False, 'task3 的输出里没有「' + key + '」这一行——打印行是判分接口，别改'))
        else:
            out.append(check_line(t3[key], [want],
                                  'task3 的「' + key + '」是 ' + want + '（与课件一致）',
                                  'task3 的「' + key + '」对不上'))

    exact4 = {
        '推荐的算法族': '贪心',
        '实现 A（按开始时间排）选出': '1 个: [(0, 60)]',
        '实现 A 通过吗': 'False',
        '实现 A 反例': '[(0, 60)]',
        '实现 B（按结束时间排）选出': '6 个: [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12)]',
        '实现 B 通过吗': 'True',
        '实现 B 反例': '[(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12)]',
        '暴力验证给出的最优': '6 个',
        '两个实现选出的个数': '1 6',
        '实现数': '2',
        '通过的实现数': '1',
        '这条链没验证出东西': 'False',
        '解析坏掉时的 ok': 'False',
        '解析坏掉时的 reason': '<JSONDecodeError>',
        '题面首选': '贪心',
        '模型推荐': '贪心',
        '首选与模型一致': 'True',
    }
    for key, want in exact4.items():
        if key not in t4:
            out.append((False, 'task4 的输出里没有「' + key + '」这一行——打印行是判分接口，别改'))
            continue
        out.append(check_line(t4[key], [want],
                              'task4 的「' + key + '」逐字对上：' + want,
                              'task4 的「' + key + '」对不上'))
    # 课件那一组数据的两个实现选出来的是哪两批区间，单独再核一遍（顺序也要对）
    out.append(check_line(t4.get('实现 A（按开始时间排）选出', ''),
                          ['1', '个:', '[(0, 60)]'],
                          '实现 A 在课件那一组数据上只选出 1 个（就是 (0, 60) 那一段）',
                          '实现 A 选出的那一批区间对不上'))
    out.append(check_line(t4.get('实现 B（按结束时间排）选出', ''),
                          ['6', '个:', '[(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12)]'],
                          '实现 B 在课件那一组数据上把 6 个小区间全收了——'
                          '同一个「贪心」名下两个实现结论不同',
                          '实现 B 选出的那一批区间对不上'))
    return out


def block_network():
    """把 socket.socket 掐掉，交回一个还原用的函数。判分层里模拟「断网」。"""
    import socket

    original = socket.socket
    calls = []

    def refusal(*args, **kwargs):
        calls.append(args)
        raise RuntimeError('判分环境不许联网')

    socket.socket = refusal

    def restore():
        socket.socket = original

    return restore, calls


def layer5b(loaded):
    """离线可跑：判分**绝不许联网**，模型调用必须走那道缝。"""
    out = []
    if not loaded.ok('task1_prompt'):
        return [(False, '离线这一组跳过：task1_prompt.py 载入不完整')]

    call_model = loaded.fn('task1_prompt', 'call_model')
    raw, error = attempt(call_model, '随便一段提示词')
    if error is None:
        out.append((False, 'call_model 直接交回了 ' + short(repr(raw), 40)
                           + '——离线环境里它是唯一的联网点，得明确地抛 NotImplementedError：'
                             '测试时换掉它、其余部分一行不改，这就是那道缝'))
    elif not error.startswith('NotImplementedError'):
        out.append((False, 'call_model 抛出的是 ' + error + '，不是 NotImplementedError'
                           + '——这一条要说清「离线环境不联网，测试时请换掉这个函数」'))
    else:
        out.append((True, 'call_model 会明确地抛 NotImplementedError——'
                          '它是整条链上唯一的联网点，也就是那道缝'))

    fake, error = attempt(loaded.fn('task1_prompt', 'fake_model'), '题目里有木头两个字')
    if error is not None:
        out.append((False, 'fake_model 报错' + error_note(error)))
    elif not isinstance(fake, str) or not fake.strip():
        out.append((False, 'fake_model 交回的不是一段非空文本：' + short(repr(fake), 40)))
    else:
        verdict, load_error = judge.safe_load(fake.strip())
        ok = isinstance(verdict, dict) and 'family' in verdict
        out.append((ok, 'fake_model 交回干净的一行 JSON，family=' + str(verdict.get('family'))
                    if ok else 'fake_model 交回的不是干净 JSON：' + short(repr(fake), 40)
                    + '——这一段试的是「缝」通不通，不是解析器的抗噪能力'))

    restore, calls = block_network()
    try:
        problem = PROBLEMS['区间调度']
        prompt = loaded.fn('task1_prompt', 'build_prompt')(problem)
        offline_value, offline_error = attempt(loaded.fn('task1_prompt', 'fake_model'), prompt)
        offline_resolve, resolve_error = attempt(loaded.fn('task4_pipeline', 'resolve')
                                                if loaded.ok('task4_pipeline') else (lambda: None),
                                                offline_value if isinstance(offline_value, str) else '')
        offline_trial, trial_error = attempt(loaded.fn('task4_pipeline', 'run_trial')
                                             if loaded.ok('task4_pipeline') else (lambda: None),
                                             '贪心', case_intervals(6))
    finally:
        restore()

    if calls:
        out.append((False, '判分把 socket 掐掉之后，有 ' + str(len(calls)) + ' 次建连接的尝试'
                           + '——判分**绝不许联网**，模型调用必须走传进来的那个函数'))
    else:
        out.append((True, '掐掉 socket 之后整条链照跑：一次建连接的尝试都没有'
                          '——离线可跑这条要求是真的验过的'))

    ok_offline = (resolve_error is None and isinstance(offline_resolve, dict)
                  and offline_resolve.get('ok') is True
                  and trial_error is None and isinstance(offline_trial, tuple)
                  and len(offline_trial) == 2)
    expected_rows, expected_want = canonical_trial(case_intervals(6))
    if ok_offline:
        rows = offline_trial[0]
        the_same = (isinstance(rows, (list, tuple)) and len(rows) == len(expected_rows)
                    and all(isinstance(row, tuple) and len(row) == 5
                            and row[2] == expected[1] and row[3] is expected[2]
                            and list(row[4]) == list(expected[3])
                            for row, expected in zip(rows, expected_rows)))
        out.append((the_same, '断网状态下 run_trial 给出的结论与另算一遍的完全一致'
                              '（A 被否掉、B 通过）——结论不是从网络来的'
                    if the_same else '断网状态下 run_trial 的结论与另算一遍的不一致：交回 '
                    + short(repr(rows), 60)))
    else:
        out.append((False, '断网状态下跑这条链没跑通：'
                           + short(repr(offline_resolve), 30) + ' / '
                           + short(repr(offline_trial), 30)
                           + error_note(resolve_error) + error_note(trial_error)))
    return out


# ── 主流程 ──────────────────────────────────────────────────────────────

LAYERS = [
    ('第 1 层 · 提示词的四样约束', [layer1, layer1b],
     'task1_prompt.py 的四个 TODO（提示词的四样约束、call_model、fake_model、recommend）'),
    ('第 2 层 · 六种形态过五种', [layer2, layer2b],
     'task2_parse.py 的 TODO 1 / 2 / 3（parse_naive、parse_robust、explain_samples）'),
    ('第 3 层 · 关键词打分对六道题面', [layer3, layer3b],
     'task3_classify.py 的 TODO 1 / 2（classify、explain_problems）'),
    ('第 4 层 · 端到端：同族两个实现结论不同', [layer4, layer4b, layer4c],
     'task4_pipeline.py 的 TODO 1 / 2 / 3（resolve、run_trial、nothing_passed）'),
    ('第 5 层 · 打印行、单跑、离线', [layer5, layer5b],
     '四个脚本里的 TODO——这一层读的是它们打印出来的行，所以那些 print 别改'),
]


def main():
    print('StudyMate lab 0027 · 自动判分（让助手推荐并验证）')
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
    print('五层：' + str(layers_ok) + ' 层通过、' + str(len(LAYERS) - layers_ok) + ' 层还没过'
          + '（共 ' + str(passed) + ' 条 PASS、' + str(failed) + ' 条 FAIL）')
    if failed == 0:
        print('五层全过。现在去对照 ../solutions/0027-lab-03-recommend-and-verify/：')
        print('比一比提示词里那四样约束怎么落地、解析器的失败标记怎么设计，'
              '再用一句话回答「这个助手给出的结论，凭什么值得相信」。')
        return 0
    print('卡住了先读 ../README.md 的「卡壳顺序」，再看每条 FAIL 后面点出的那一段 TODO。')
    print('判分读的就是四个脚本打印出来的行，也别改那些 print。')
    print('全部过了再对照 ../solutions/0027-lab-03-recommend-and-verify/。')
    return 1


if __name__ == '__main__':
    sys.exit(main())
