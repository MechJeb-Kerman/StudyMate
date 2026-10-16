#!/usr/bin/env python3
r"""lab 0033 · 自动判分（综合实战：把刷题助手做完）

用法（在 lab/0033-capstone-ai-tutor/ 或 lab/solutions/0033-capstone-ai-tutor/ 里）：

    py run_tests.py

判法：**五层**，一层里几条检查各自给 PASS / FAIL。每一条 FAIL 后面都点明
「这一条指哪个文件的哪个 TODO」，不用猜该补哪一段。

    第 1 层 · 五段的契约表与检查器（contracts.py）
        那张表要五行齐全、顺序对、段号 1..5，每段的**输出契约**里关键字段都点到；
        CONTRACTS 要五段都有，而且**第 4 段的 passed 必须是 bool 口径**——
        这一格是整课的要害：'False' 是非空字符串，在布尔语境里是 True，
        报告会**静默地**写成「验证 通过」而正确答案是「未过」。
        检查器那一层另拿两份记录试：一份合格的、一份 passed 被改成字符串 'False' 的，
        它必须放过前者、拦住后者，并且**说清是哪个字段**（点名字段名与类型名）。

    第 2 层 · 三档解析（parse.py）
        四份预置输出逐档过：干净那份三档都吃得下、带围栏那份从第二档起、
        带前言那份只有第三档能吃下、**被截断那份三档都不行**。
        最后一档是本层的重点：它必须交出「括号不闭合（找得到 { 却找不到配对的 }）」
        这句判据——找得到 { 找不到配对的 }，坏的不是格式，是内容不完整。
        再拿判分自己造的四段文本试第三档（嵌套对象、字符串里带花括号、没有 {、括号不闭合）。

    第 3 层 · 五段各自的产物（pipeline.py）
        先独立试四段（不等整条链跑通）：第一段的三个字段是不是从**预置输出**里来的；
        第二段的候选经过关键词筛之后还剩什么；第四段在**判分自己的沙箱**上算得对不对
        （换一个全错的沙箱进去，那一格必须跟着变成「没过」——数字写死的会被抓住）；
        judge 那一行要跟着 passed 变（换一份合格记录进去，「通过」与「未过」都要出得来）。
        再把五段串起来：能跑完、五段之间都过了契约、两遍结论一致；
        最后注入一个**类型漂移**（passed → 'False'）与一个**字段漂移**（title → name），
        看错误是不是停在**出错的那一段**，而不是五层之外。

    第 4 层 · 记录里有证据、结论能重放（pipeline.py 的第五段）
        记录里必须有**用到的数据本身**（五组输入与期望、五组算出来的值），不能只有 seed；
        第一个反例要连组号、数据、算出来的、期望的一起交；
        两次完整流程的记录要能对比出「结论一致」；
        再单独喂一组**全过**的数据，确认 failing_case 是 None、
        failed_first 写成「没有反例」，而不是一句笼统的「通过」。

    第 5 层 · 打印行、单跑、工具没被动过
        逐字读五个脚本打印出来的行（那些行就是接口，别改它们）；
        检查每个任务文件单跑退出码 0、0 处 Traceback；
        再确认 tools.py 与 fake_model.py 与发下来那一份**逐字节相同**——
        判分与四份预置输出全靠它们，自己改一个字，四种模型输出就对不上了。

判分不判的东西：说明的文笔、注释写得多不多、目录结构漂不漂亮，
由 lab/README.md 的自查清单与课件那一节回答；这里只管能不能跑、口径对不对、
那六件事是不是**真的做出来了**。

一个耗时都不量：四份预置输出与那几组数据全是确定值。

退出码：五层都过是 0；还有没过的（或跳过的）是 1。
"""

from __future__ import annotations

import hashlib
import importlib
import os
import subprocess
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def task_dir():
    """学生的任务目录（`answer.md` / `record.md` 就在那里）。

    判分放在 `solutions/` 里也照样跑，所以那两个文件不在这里时往上找一层
    （`solutions/xxx/` → `lab/` 那一层，参考解与留白版的文档是同一份）。
    """
    for place in (HERE, HERE.parent, HERE.parent.parent):
        if (place / 'answer.md').exists() and (place / 'record.md').exists():
            return place
    return HERE


TASK_DIR = task_dir()

import tools as judge                                     # noqa: E402  给好的，别改
from tools import (CANON_CASES, CANON_FAILING, CANON_TEXT, CLEAN, FENCED, PRESETS,  # noqa: E402
                   PREFACED, TRUNCATED, TODO_MARK, TRUNCATED_NOTE, canon_cases,
                   canon_exec, canon_seed, fence_line_count, make_fence,
                   normalize_value, parse_json)

TASK_FILES = ['contracts.py', 'parse.py', 'fake_model.py', 'pipeline.py']
STAGES = ['1 提取题意', '2 推荐算法', '3 写解法', '4 验证', '5 出记录']

# 每个段名 → 那张「输出契约」里必须点到的关键字段。
STAGE_FIELDS = {
    STAGES[0]: ['title', 'constraints', 'ask'],
    STAGES[1]: ['candidates', 'reasons', 'picked'],
    STAGES[2]: ['code', 'entry', 'complexity'],
    STAGES[3]: ['passed', 'evidence', 'failing_case'],
    STAGES[4]: ['problem', 'picked', 'passed', 'evidence', 'seed', 'rerun'],
}

# 契约合格的那一组：五段各自的代表产物（判分自己造的，与流水线无关）。
GOOD = {
    STAGES[0]: {'title': '拨钟问题', 'constraints': {'n_max': 9, 'value_max': 27},
                'ask': '最少按键次数'},
    STAGES[1]: {'candidates': ['图的搜索', '枚举'], 'reasons': ['最少按键次数'],
                'picked': '图的搜索'},
    STAGES[2]: {'code': 'def solve(text):\n    return "0"\n', 'entry': 'solve(text)',
                'complexity': 'O(4^n · n)'},
    STAGES[3]: {'passed': True, 'evidence': ['第 0 组: 0 算出来 0 / 期望 0 → 过'],
                'failing_case': None, 'cases': [['0 0 0\n0 0 0\n0 0 0\n', '0']],
                'outputs': ['0'], 'results': [True], 'seed': canon_seed(), 'mode': '对拍'},
    STAGES[4]: {'problem': '拨钟问题', 'picked': '图的搜索', 'passed': True,
                'evidence': ['第 0 组: 0 算出来 0 / 期望 0 → 过'], 'seed': canon_seed(),
                'rerun': '数据在 cases 里（不看 seed 也能重放）',
                'failed_first': '（没有反例：全部组都过了）', 'mode': '对拍'},
}

# 判分自己造的那几段文本：用来分开「背下了四份预置输出」与「解析器真写出来了」。
PROBE_NESTED = '{"a": {"b": {"c": 1}}, "d": 2}'
PROBE_BRACES_IN_STR = '先看这个 {"note": "这里有个 } 和一个 { 在字符串里", "k": 3} 就这样。'
PROBE_NO_BRACE = '这道题我建议用枚举加剪枝，先按 4^9 种组合试一遍。'

# 发下来那一份的哈希（判分要确认学生没动过这两个文件）。
SEALED_SHA256 = {
    'tools.py': '5E047339463A67BF47AB5D83E6096E611A206462938FA44B674A4BB2B96C9740',
    'fake_model.py': 'B76CE3586F34AACC8B51AF3EFF9EFFD87FF6283440D78023B4AB688FA1E1A288',
}


# ── 载入学生写的文件 ────────────────────────────────────────────────────

class Loaded:
    """逐个载入四个文件 → 记下模块、载入异常、以及缺了哪些名字。

    四道缝各自独立：某一个文件坏了，只有它负责的那一层会报载入失败。
    """

    REQUIRED = {
        'contracts': ['CONTRACTS', 'TABLE_ROWS', 'contract_table', 'check_contract',
                      'contract_error'],
        'parse': ['parse_naive', 'parse_strip_fence', 'parse_extract', 'parse_json',
                  'explain_samples'],
        'fake_model': ['call_model', 'reset', 'samples', 'advice', 'looks_truncated',
                       'preset_names'],
        'pipeline': ['extract_intent', 'recommend', 'build_solution', 'run_cases',
                     'make_record', 'run_pipeline', 'judge'],
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

    def gone(self, name):
        return self.missing.get(name, [])

    def ok(self, name):
        return name in self.modules and not self.missing.get(name)

    def fn(self, name, item):
        return getattr(self.modules[name], item, None)

    def why(self, label, name):
        """这一层为什么一开始就过不去——把该补的那一段点出来。"""
        if name in self.errors:
            tail = '\n'.join(self.errors[name].strip().splitlines()[-6:])
            return (label + '载入失败——文件自己那几行就报错了：\n' + tail
                    + '\n        （判分是 import 你的文件的，'
                      '改完先单跑一次看它退出码是不是 0）')
        gone = self.gone(name)
        return (label + '里找不到这些名字：' + '、'.join(gone)
                + '。函数名、变量名、文件名都是判分接口，别改名、别删；'
                  '要写的是文件里标着 TODO 的那几段')


# ── 调用学生函数的保险：报错就转成一句 FAIL，不让判分自己崩 ──────────────

def attempt(func, *args, **kwargs):
    """调一次 → (值, 错误文本)。抛异常时值是 None、错误文本是「类型: 说明」。"""
    if func is None:
        return None, '没有这个函数（判分接口的名字被改了或删了）'
    try:
        return func(*args, **kwargs), None
    except Exception as exc:
        return None, type(exc).__name__ + ': ' + str(exc)


def is_parse_failure(error):
    """这一条错误是解析器**如实交回失败**（抛 ParseFailure），还是它真崩了？

    两者要分开：解析器吃不下某一份预置输出是**正常**的（被截断那一档本来就吃不下去），
    而 AttributeError / TypeError / KeyError 那几种才是「拿了个坏对象去用」。
    """
    if not error:
        return False
    head = error.split(':', 1)[0].strip()
    return head.endswith('ParseFailure')


def error_note(error):
    return '' if error is None else '（调用时抛出 ' + error + '）'


def short(text, limit=60):
    text = '' if text is None else str(text)
    return text if len(text) <= limit else text[:limit] + '…'


def text_of(value):
    """交回的东西是不是一段用得上文字（给「契约那几格是不是字符串」这类判断用）。"""
    return value if isinstance(value, str) else ''


def spec_text(spec):
    """把一份契约写成一段文本（字段名按顺序排开），关键词检查走它。"""
    fields = getattr(spec, 'fields', None)
    if not callable(fields):
        return ''
    try:
        return '、'.join(str(item) for item in fields())
    except Exception:
        return ''


def check_eq(actual, expected, good, bad):
    """值相等给 good，不等给 bad（bad 后面会补上「交回的是什么」）。"""
    if isinstance(expected, bool) or isinstance(actual, bool):
        same = actual is expected
    elif isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        same = normalize_value(actual) == normalize_value(expected)
    else:
        same = normalize_value(actual) == normalize_value(expected)
    if same:
        return True, good
    return False, (bad + '（交回 ' + short(repr(actual), 56) + '，期望 '
                   + short(repr(expected), 56) + '）')


def check_line(actual, tokens, good, bad, prefix=False):
    """打印行对得上吗：先按空白切、再一段段比，第一个不一样的地方点名。"""
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


def parse_shown(text):
    """把「标签: 值」的行读成 {标签: 值}（值原样保留内部空白）。

    标签后面那一个分隔符是空格还是冒号都认（scripts 里有几行照课件带了冒号；
    `show_line` 打的是「标签: 值」，而 contracts.py 的表头打的是「契约表 5 行」）。
    """
    rows = {}
    for line in str(text).splitlines():
        line = line.strip()
        if line.startswith('==') or not line:
            continue
        for sep in (': ', ' '):
            label, found, value = line.partition(sep)
            if found:
                rows[label.strip()] = value.strip()
                break
    return rows


def shown(rows, label):
    return rows.get(str(label).strip())


# ── 第 1 层 · 契约表与检查器 ────────────────────────────────────────────

def layer1a(loaded):
    label = 'contracts.py '
    if not loaded.ok('contracts'):
        return [(False, loaded.why(label, 'contracts'))]
    out = []
    table, error = attempt(loaded.fn('contracts', 'contract_table'))
    if error is not None:
        return [(False, 'contract_table() 报错' + error_note(error)
                       + TODO_MARK + judge.TODO_NAMES[3])]
    rows = list(table) if isinstance(table, (list, tuple)) else []
    if len(rows) != 5:
        return [(False, '契约表有 ' + str(len(rows)) + ' 行，期望 5 行（五段各一行）'
                       + TODO_MARK + judge.TODO_NAMES[1])]
    numbers = []
    for index, row in enumerate(rows):
        if not isinstance(row, (list, tuple)) or len(row) != 3:
            out.append((False, '契约表第 ' + str(index + 1) + ' 行的形状是 '
                               + short(repr(row), 40) + '，期望 (段号, 输入, 输出契约) 三格'
                               + TODO_MARK + judge.TODO_NAMES[3]))
            continue
        number, takes, gives = row
        numbers.append(number)
        if not isinstance(number, int) or isinstance(number, bool) or number != index + 1:
            out.append((False, '契约表第 ' + str(index + 1) + ' 行的段号是 ' + repr(number)
                               + '，期望 ' + str(index + 1) + '（顺序就是流水线的顺序）'
                               + TODO_MARK + judge.TODO_NAMES[3]))
        if not text_of(takes).strip():
            out.append((False, '契约表第 ' + str(index + 1) + ' 行的「输入」那一格是空的'
                               + TODO_MARK + judge.TODO_NAMES[3]))
        body = text_of(gives)
        stage = STAGES[index]
        missing = [field for field in STAGE_FIELDS[stage] if field not in body]
        if missing:
            out.append((False, '契约表里「' + stage + '」那一行的输出契约没点到这几个字段：'
                               + '、'.join(missing) + '（那一格现在写着 '
                               + short(repr(body), 40) + '）' + TODO_MARK + judge.TODO_NAMES[3]))
        else:
            out.append((True, '契约表「' + stage + '」那一行点到了 '
                              + '、'.join(STAGE_FIELDS[stage]) + '——五段的输出契约都写下来了'))
    if numbers == [1, 2, 3, 4, 5]:
        out.append((True, '五行的段号是 1..5、顺序与流水线一致（提取题意 → 推荐算法 → '
                          '写解法 → 验证 → 出记录）'))
    return out


def layer1b(loaded):
    label = 'contracts.py '
    if not loaded.ok('contracts'):
        return [(False, '契约这一组跳过：先让上面那一条过（' + label + '载入不完整）')]
    out = []
    contracts = loaded.fn('contracts', 'CONTRACTS')
    if not isinstance(contracts, dict):
        return [(False, 'CONTRACTS 不是字典（实际是 ' + type(contracts).__name__
                       + '）' + TODO_MARK + judge.TODO_NAMES[1])]
    missing = [stage for stage in STAGES if stage not in contracts]
    if missing:
        return [(False, 'CONTRACTS 里缺这几段的契约：' + '、'.join(missing)
                       + '（段名要逐字是 ' + '、'.join(STAGES) + '）'
                       + TODO_MARK + judge.TODO_NAMES[1])]
    out.append((True, 'CONTRACTS 五段的契约都有：' + '、'.join(STAGES)))
    bad_shape = [stage for stage in STAGES
                 if not callable(getattr(contracts[stage], 'check', None))]
    out.append((not bad_shape,
                '五份契约都是 TypeSpec（能 check）'
                if not bad_shape else
                '这几段的契约不是 TypeSpec（没有 check）：' + '、'.join(bad_shape)
                + '——用 TypeSpec(段名, {字段名: 检查函数}) 造' + TODO_MARK + judge.TODO_NAMES[1]))
    stage4 = spec_text(contracts[STAGES[3]])
    for field in STAGE_FIELDS[STAGES[3]]:
        if field not in stage4:
            out.append((False, '第 4 段的契约里没有字段 ' + field + '——它是判分与记录都要用的'
                               + TODO_MARK + judge.TODO_NAMES[1]))
    passed_back = attempt(loaded.fn('contracts', 'contract_error'),
                          contracts[STAGES[3]], dict(GOOD[STAGES[3]], passed='False'))
    drift_note, drift_error = passed_back
    drift_type = isinstance(drift_note, str) and bool(drift_note.strip())
    if drift_type:
        out.append((True, '第 4 段的契约拦住了 passed 是字符串的记录，并给出了一句说明（'
                          + short(drift_note, 50) + '）——这一格是全课要害：'
                          '不拦它，报告就会静默地写「验证 通过」'))
    else:
        out.append((False, '第 4 段的契约**放过了** passed 是字符串的那种记录'
                           + ('' if drift_error is None
                              else '（试的时候抛了 ' + short(str(drift_error), 50) + '）')
                           + '。这一格必须是 bool 口径：\'False\' 是非空字符串，'
                             '在布尔语境里是 True，报告会静默地写成「验证 通过」'
                           + TODO_MARK + judge.TODO_NAMES[2]))
    return out


def layer1c(loaded):
    label = 'contracts.py '
    if not loaded.ok('contracts'):
        return [(False, '检查器这一组跳过：先让上面那一条过（' + label + '载入不完整）')]
    out = []
    check = loaded.fn('contracts', 'check_contract')
    contracts = loaded.fn('contracts', 'CONTRACTS')
    gone = [stage for stage in STAGES if stage not in contracts]
    if gone:
        return [(False, '检查器拿不到这几段的契约，试不了：' + '、'.join(gone)
                       + '——先照课件那张五行表把 CONTRACTS 写出来'
                       + TODO_MARK + judge.TODO_NAMES[1])]
    for stage in STAGES:
        spec = contracts[stage]
        value, error = attempt(check, spec, GOOD[stage])
        out.append((error is None and isinstance(value, dict),
                    '拿一份合格的「' + stage + '」产物试 check_contract：原样交回，没冤枉它'
                    if error is None else
                    '拿一份合格的「' + stage + '」产物试 check_contract，它却抛了 '
                    + str(error) + '——合格的产物不该被拦住' + TODO_MARK + judge.TODO_NAMES[2]))
    # 类型漂移：passed 从 True 变成字符串 'False'——**必须是这一条被抓住**。
    spec4 = contracts[STAGES[3]]
    drift = dict(GOOD[STAGES[3]], passed='False')
    _, error = attempt(check, spec4, drift)
    if error is None:
        out.append((False, 'passed 变成字符串 \'False\' 之后 check_contract **没吭声**——'
                           '这一条正是本课最该抓住的坑：报告写着「验证 通过」，'
                           '而正确答案是「未过」' + TODO_MARK + judge.TODO_NAMES[2]))
    else:
        note = str(error)
        named = ('passed' in note and 'bool' in note and 'str' in note
                 and STAGES[3] in note)
        out.append((named,
                    '漂移那一条被当场拦住，而且说清了是哪一段的哪个字段：' + short(note, 80)
                    if named else
                    '漂移那一条拦住了，但没说清「哪一段的哪个字段、该是什么类型」：'
                    + short(note, 80) + '——要能一次说清三段信息：段名、字段名、'
                      '字段应该是什么类型（判分读的就是这三样）' + TODO_MARK + judge.TODO_NAMES[2]))
    # 字段漂移：title 少一个字母 → 必须说「缺字段 name」。
    wrong_field = dict(GOOD[STAGES[0]])
    wrong_field['name'] = wrong_field.pop('title')
    _, error = attempt(check, contracts[STAGES[0]], wrong_field)
    text = '' if error is None else str(error)
    out.append((error is not None and 'title' in text and STAGES[0] in text,
                '字段名漂移（title → name）也被点名了：' + short(text, 70)
                if error is not None and 'title' in text else
                '字段名漂移那一组没被说清（交回的是 ' + short(text, 60) + '）——'
                '检查器要能说出**缺了哪个字段**，错误才会停在出错的那一段'
                + TODO_MARK + judge.TODO_NAMES[2]))
    # 检查器的返回值：对了就该原样交回，别交回 True / None。
    value, _ = attempt(check, contracts[STAGES[2]], GOOD[STAGES[2]])
    out.append((isinstance(value, dict) and value.get('entry') == GOOD[STAGES[2]]['entry'],
                '契约对了的时候原样交回那个对象（不是交回 True）'
                if isinstance(value, dict) else
                '契约对了的时候交回的是 ' + short(repr(value), 30)
                + '——要原样交回传进来的那个对象' + TODO_MARK + judge.TODO_NAMES[2]))
    return out


# ── 第 2 层 · 三档解析 ─────────────────────────────────────────────────

def layer2a(loaded):
    label = 'parse.py '
    if not loaded.ok('parse'):
        return [(False, loaded.why(label, 'parse'))]
    out = []
    expect = [
        ('干净 JSON', True, True, True),
        ('带围栏', False, True, True),
        ('带前言', False, False, True),
        ('被截断', False, False, False),
    ]
    rows = [(name, PREFACED if name == '带前言' else PRESETS[name]) for name, _, _, _ in expect]
    for (name, want_naive, want_fence, want_extract), (_, raw) in zip(expect, rows):
        for want, func in ((want_naive, 'parse_naive'), (want_fence, 'parse_strip_fence'),
                           (want_extract, 'parse_extract')):
            value, error = attempt(loaded.fn('parse', func), raw)
            if error is not None and not is_parse_failure(error):
                # 真崩了：这不是「吃不下」，是拿了个坏对象去用。
                out.append((False, '「' + name + '」这一份把 ' + func + ' 弄崩了：'
                                   + error + '——解析器要么拿下一个对象、'
                                     '要么抛 ParseFailure（带一段说明），'
                                     '别崩在别的地方' + TODO_MARK + judge.TODO_NAMES[4]))
                continue
            got = error is None and isinstance(value, dict)
            if want and not got:
                detail = ('（交回 ' + short(repr(value), 40) + '）' if error is None
                          else '（抛了 ' + short(error, 60) + '）')
                out.append((False, '「' + name + '」这一份 ' + func + ' 没拿下' + detail
                                   + '——这一份本该被它吃下' + TODO_MARK + judge.TODO_NAMES[4]))
            elif not want and got:
                out.append((False, '「' + name + '」这一份 ' + func + ' 竟然拿下了'
                                   + '——这一档不该救得了它（被截断那一份的括号根本没闭合）'
                                   + TODO_MARK + judge.TODO_NAMES[5]))
            else:
                out.append((True, '「' + name + '」 ' + func
                                  + ('拿下' if want else '如实交回失败（抛 ParseFailure）')))
    return out


def layer2b(loaded):
    label = 'parse.py '
    if not loaded.ok('parse'):
        return [(False, '解析细节这一组跳过：先让上面那一条过（' + label + '载入不完整）')]
    out = []
    parse_json_fn = loaded.fn('parse', 'parse_json')
    # 被截断那一份：reason 里必须带「括号不闭合」这句判据。
    _, error = attempt(parse_json_fn, TRUNCATED)
    note = '' if error is None else str(error)
    out.append((error is not None and '括号不闭合' in note and '没找到' not in note,
                '被截断那一份交回的说明是「' + short(note, 70) + '」——'
                '这正是它该说的话：找得到 { 找不到配对的 }，坏的不是格式，是内容不完整'
                if error is not None and '括号不闭合' in note else
                '被截断那一份交回的说明对不上（' + short(note, 80) + '）——'
                '它要交出「' + TRUNCATED_NOTE + '」这句判据，好让上游知道'
                '该走的是**重试**，不是再换个解析器' + TODO_MARK + judge.TODO_NAMES[5]))
    # 判分自己造的四段文本。
    probes = [
        ('嵌套对象', PROBE_NESTED, True),
        ('字符串里带花括号', PROBE_BRACES_IN_STR, True),
        ('根本没有花括号', PROBE_NO_BRACE, False),
        ('括号不闭合', '{"title": "拨钟问题", "constraints": {', False),
    ]
    for name, raw, want in probes:
        value, error = attempt(loaded.fn('parse', 'parse_extract'), raw)
        if error is not None and not is_parse_failure(error) and want:
            out.append((False, '判分的探针「' + name + '」把 parse_extract 弄崩了：'
                               + error + TODO_MARK + judge.TODO_NAMES[5]))
            continue
        if want:
            ok = error is None and isinstance(value, dict)
            out.append((ok, '探针「' + name + '」拿下了：' + short(repr(value), 46)
                        if ok else
                        '探针「' + name + '」没拿下（' + short(error or repr(value), 50)
                        + '）——深度计数要跳过字符串里的花括号'
                        + TODO_MARK + judge.TODO_NAMES[5]))
        else:
            ok = error is not None
            out.append((ok, '探针「' + name + '」如实失败：' + short(error, 60)
                        if ok else
                        '探针「' + name + '」竟然拿下了（交回 ' + short(repr(value), 40)
                        + '）——这一份不该有结果' + TODO_MARK + judge.TODO_NAMES[5]))
    # 两种失败要说得不一样：「没找到 {」与「括号不闭合」是两句不同的话。
    _, e1 = attempt(parse_json_fn, PROBE_NO_BRACE)
    _, e2 = attempt(parse_json_fn, '{"title": "拨钟问题", "constraints": {')
    out.append((e1 is not None and e2 is not None and str(e1) != str(e2),
                '没有花括号与括号不闭合交回的是两句**不同**的话（'
                + short(str(e1), 30) + ' / ' + short(str(e2), 30) + '）——'
                '上游靠这个区分「只能重试」与「提示词要改」'
                if e1 is not None and e2 is not None and str(e1) != str(e2) else
                '两种失败没能分开（' + short(str(e1), 40) + ' / ' + short(str(e2), 40)
                + '）——「没找到 {」与「括号不闭合」要各说各的'
                + TODO_MARK + judge.TODO_NAMES[5]))
    # explain_samples：四行，且被截断那一行是「三档都不行」。
    rows, error = attempt(loaded.fn('parse', 'explain_samples'))
    if error is not None:
        out.append((False, 'explain_samples() 报错' + error_note(error)
                           + TODO_MARK + judge.TODO_NAMES[4]))
    elif not isinstance(rows, (list, tuple)) or len(rows) != 4:
        out.append((False, 'explain_samples() 交回的不是四行：' + short(repr(rows), 40)
                           + TODO_MARK + judge.TODO_NAMES[4]))
    else:
        last = rows[-1]
        ok = (isinstance(last, (list, tuple)) and len(last) >= 2
              and '不行' in str(last[1]))
        out.append((ok, 'explain_samples() 四行都对上：最后一行「' + str(rows[-1][0])
                        + '」是「三档都不行」——这一课最要紧的那一格'
                    if ok else
                    'explain_samples() 最后一行（被截断那一份）写的是 '
                    + short(repr(last), 50) + '，期望「三档都不行」'
                    + TODO_MARK + judge.TODO_NAMES[4]))
    return out


def layer2c(loaded):
    """假模型那份（两侧相同）：四份预置输出与重试那一条路。"""
    label = 'fake_model.py '
    if not loaded.ok('fake_model'):
        return [(False, loaded.why(label, 'fake_model'))]
    out = []
    samples, error = attempt(loaded.fn('fake_model', 'samples'))
    if error is not None or not isinstance(samples, dict):
        return [(False, 'fake_model.samples() 交回的不是四份预置输出：'
                       + short(repr(samples), 40) + error_note(error))]
    names = loaded.fn('fake_model', 'preset_names')()
    out.append((check_eq(list(names), ['干净 JSON', '带围栏', '带前言', '被截断'],
                         '四份预置输出的名字与顺序都对：干净 JSON、带围栏、带前言、被截断',
                         '四份预置输出的名字或顺序对不上')[0],
                '四份预置输出的名字与顺序逐字对上'
                if list(names) == ['干净 JSON', '带围栏', '带前言', '被截断'] else
                '四份预置输出的名字/顺序是 ' + short(repr(list(names)), 50)))
    for name, want in (('干净 JSON', CLEAN), ('带围栏', FENCED), ('带前言', PREFACED),
                       ('被截断', TRUNCATED)):
        got = samples.get(name)
        out.append(check_eq(got, want,
                            '预置的「' + name + '」与 tools 里那一份逐字相同'
                            + ('（这一份就是被截断的：'
                               + str(len(want)) + ' 个字符、括号不闭合）'
                               if name == '被截断' else ''),
                            '预置的「' + name + '」被改过了'))
    out.append((fence_line_count(FENCED) == 2,
                '「带围栏」那一份正好有两行围栏行——第一档解析器就该在它上面失败'))
    # 重试那一条路：第一次给被截断的，retry=True 给干净的。
    call = loaded.fn('fake_model', 'call_model')
    loaded.fn('fake_model', 'reset')()
    first, error = attempt(call, '题目：' + CANON_TEXT[:12] + '截断的', retry=False)
    second, _ = attempt(call, '上一次被截断了，重来一次', retry=True)
    out.append((error is None and loaded.fn('fake_model', 'looks_truncated')(first)
                and not loaded.fn('fake_model', 'looks_truncated')(second),
                '假模型的两条路都在：提示词里出现「截断」时给被截断的那一份，'
                'retry=True 时给干净的那一份——**重试必须有机会成功**'
                if error is None and loaded.fn('fake_model', 'looks_truncated')(first)
                else '假模型的重试那条路不对：第一次交回 ' + short(repr(first), 40)
                     + '、第二次交回 ' + short(repr(second), 40)))
    # 交回的是副本：改坏了也不该动到预置的那一份。
    loaded.fn('fake_model', 'reset')()
    value = call('随便一句没有任何关键词的话')
    if isinstance(value, str):
        value = value + '（被调用处就地改了）'
    out.append((samples.get('干净 JSON') == CLEAN and judge.CLEAN == CLEAN,
                'call_model 交回的是副本：调用处就地改它不会把预置的那一份带坏'))
    loaded.fn('fake_model', 'reset')()
    return out


# ── 第 3 层 · 五段各自的产物 ────────────────────────────────────────────

def layer3a(loaded):
    label = 'pipeline.py '
    if not loaded.ok('pipeline'):
        return [(False, loaded.why(label, 'pipeline'))]
    out = []
    # 第一段：三个字段都要从预置输出里来。
    loaded.fn('fake_model', 'reset')()
    intent, error = attempt(loaded.fn('pipeline', 'extract_intent'), CANON_TEXT,
                           loaded.fn('fake_model', 'call_model'))
    calls = list(loaded.modules['fake_model'].CALLS)
    if error is not None:
        return [(False, 'extract_intent(题目文本, 假模型) 报错' + error_note(error)
                       + TODO_MARK + judge.TODO_NAMES[6])]
    if not isinstance(intent, dict):
        return [(False, 'extract_intent 交回的不是字典：' + short(repr(intent), 40)
                       + TODO_MARK + judge.TODO_NAMES[6])]
    out.append((check_eq(intent.get('title'), '拨钟问题',
                         '第一段把标题提取出来了：拨钟问题',
                         '第一段的 title 对不上（预置输出里写的正是「拨钟问题」）')[0],
                '第一段把标题提取出来了：' + short(repr(intent.get('title')), 24)))
    out.append((check_eq(intent.get('constraints'), {'n_max': 9, 'value_max': 27},
                         '第一段的 constraints 两个整数都对：n_max 9 / value_max 27',
                         '第一段的 constraints 对不上')[0],
                '第一段的 constraints 是 ' + short(repr(intent.get('constraints')), 40)))
    ask = str(intent.get('ask') or '')
    out.append((('最少按键次数' in ask) and len(calls) == 2,
                '第一段调用模型 2 次：第一次拿到被截断的那一份（解析失败），'
                '重试才拿到干净的——**被截断走的是重试，不是静默吞掉**'
                if len(calls) == 2 else
                '第一段调用模型 ' + str(len(calls)) + ' 次，期望 2 次'
                '（第一次被截断 → 带着坏消息再问一次）。只调一次就说明重试没做，'
                '那半截输出被静默吞掉了' + TODO_MARK + judge.TODO_NAMES[6]))
    if len(calls) >= 2:
        out.append((calls[0][1] is False and calls[1][1] is True
                    and loaded.fn('fake_model', 'looks_truncated')(calls[0][2])
                    and not loaded.fn('fake_model', 'looks_truncated')(calls[1][2]),
                    '两次调用的样子都对：第一次 retry=False 且拿到被截断的一份，'
                    '第二次 retry=True 且拿到干净的一份'
                    if calls[1][1] is True else
                    '第二次调用没有带 retry=True——不传它，假模型照样交回半截，'
                    '重试等于没做' + TODO_MARK + judge.TODO_NAMES[6]))
    # 第二段：候选要被关键词筛过。
    loaded.fn('fake_model', 'reset')()
    advice, error = attempt(loaded.fn('pipeline', 'recommend'), intent,
                            loaded.fn('fake_model', 'call_model'))
    if error is not None:
        out.append((False, 'recommend(第 1 段的产物, 假模型) 报错' + error_note(error)
                           + TODO_MARK + judge.TODO_NAMES[7]))
    elif not isinstance(advice, dict):
        out.append((False, 'recommend 交回的不是字典：' + short(repr(advice), 40)
                           + TODO_MARK + judge.TODO_NAMES[7]))
    else:
        out.append((check_eq(advice.get('candidates'), ['图的搜索'],
                             '第二段筛完候选还剩「图的搜索」——预置推荐里带的族，'
                             '而且关键词命中了（最少按键次数/最短步数）',
                             '第二段的 candidates 对不上')[0],
                    '第二段的候选是 ' + short(repr(advice.get('candidates')), 40)))
        out.append((check_eq(advice.get('picked'), '图的搜索',
                             'picked 与候选对得上（不是模型随口说的那个）',
                             '第二段的 picked 对不上')[0],
                    '第二段的 picked 是 ' + short(repr(advice.get('picked')), 30)))
        reasons = advice.get('reasons')
        out.append((isinstance(reasons, list) and len(reasons) >= 1
                    and all(isinstance(x, str) for x in reasons),
                    '理由那一格是「一串字符串」，长度 ' + str(len(reasons or []))
                    if isinstance(reasons, list) else
                    'reasons 不是一串字符串：' + short(repr(reasons), 40)
                    + TODO_MARK + judge.TODO_NAMES[7]))
        out.append((advice.get('picked') in (advice.get('candidates') or []),
                    'picked 落在 candidates 里——第二段的结论与候选一致'
                    if advice.get('picked') in (advice.get('candidates') or []) else
                    'picked（' + short(repr(advice.get('picked')), 20) + '）不在 candidates（'
                    + short(repr(advice.get('candidates')), 30) + '）里'
                    + TODO_MARK + judge.TODO_NAMES[7]))
    return out


def layer3b(loaded):
    """第四段：判分塞自己的沙箱进去，看结论跟不跟着数据变。"""
    label = 'pipeline.py '
    if not loaded.ok('pipeline'):
        return [(False, '验证这一组跳过：先让上面那一条过（' + label + '载入不完整）')]
    out = []
    run_cases = loaded.fn('pipeline', 'run_cases')
    solution, error = attempt(loaded.fn('pipeline', 'build_solution'),
                             {'picked': '图的搜索'})
    if error is not None or not isinstance(solution, dict):
        return [(False, 'build_solution 交回的不是第 3 段的产物：'
                       + short(repr(solution), 40) + error_note(error))]
    result, error = attempt(run_cases, solution)
    if error is not None:
        return [(False, 'run_cases(第 3 段的产物) 报错' + error_note(error)
                       + TODO_MARK + judge.TODO_NAMES[8])]
    if not isinstance(result, dict):
        return [(False, 'run_cases 交回的不是字典：' + short(repr(result), 40)
                       + TODO_MARK + judge.TODO_NAMES[8])]
    cases = result.get('cases')
    want_cases = [[text, want] for text, want in canon_cases()]
    out.append((normalize_value(cases) == want_cases,
                '第四段留下的**是用到的数据本身**：' + str(len(want_cases)) + ' 组输入与期望'
                '（不是只留一个 seed）'
                if normalize_value(cases) == want_cases else
                '第四段留下的数据对不上（交回 ' + short(repr(cases), 50)
                + '）——记录里要留下用到的数据本身，不是只留一个 seed'
                + TODO_MARK + judge.TODO_NAMES[8]))
    outputs = result.get('outputs')
    want_outputs = [canon_exec(text) for text, _ in canon_cases()]
    out.append((isinstance(outputs, list) and normalize_value(outputs) == want_outputs,
                '算出来的五个值都对：' + short(repr(outputs), 50)
                + '——这一组是从**第 3 段的解法**跑出来的，不是拿期望值凑的'
                if normalize_value(outputs) == want_outputs else
                '算出来的值对不上（交回 ' + short(repr(outputs), 50) + '，期望 '
                + short(repr(want_outputs), 50) + '）' + TODO_MARK + judge.TODO_NAMES[8]))
    results = result.get('results')
    want_results = [True, True, True, True, False]
    out.append((isinstance(results, list) and normalize_value(results) == want_results
                and all(isinstance(x, bool) for x in (results or [])),
                '五组的通过情况是 [True, True, True, True, False]，'
                '而且每一格都是**真的布尔值**（不是 1 / 0 / 字符串）'
                if normalize_value(results) == want_results else
                '五组的通过情况对不上：' + short(repr(results), 50)
                + '，期望 [True, True, True, True, False]；每一格都要是 True / False 本身'
                + TODO_MARK + judge.TODO_NAMES[8]))
    out.append((result.get('passed') is False,
                'passed 是 False（第五组故意对不上）——它是 all(results) 算出来的，'
                '不是写死的'
                if result.get('passed') is False else
                'passed 交回的是 ' + short(repr(result.get('passed')), 20)
                + '，期望 False（而且是布尔值本身）' + TODO_MARK + judge.TODO_NAMES[8]))
    failed = result.get('failing_case')
    if not isinstance(failed, dict):
        out.append((False, 'failing_case 交回的是 ' + short(repr(failed), 30)
                           + '，期望第一个反例 {index, case, got}'
                           + TODO_MARK + judge.TODO_NAMES[8]))
    else:
        ok = (failed.get('index') == 4
              and normalize_value(failed.get('case')) == normalize_value(list(CANON_FAILING))
              and failed.get('got') == '18')
        out.append((ok, '第一个反例说清了四样：第 4 组、数据 ' + short(repr(CANON_FAILING[0]), 24)
                        + '、算出来 ' + short(repr(failed.get('got')), 8)
                        + '、期望 ' + short(repr(CANON_FAILING[1]), 6)
                    if ok else
                    '第一个反例的四样里有对不上的：' + short(repr(failed), 60)
                    + '，期望 index 4、数据 '
                    + short(repr(CANON_FAILING[0]), 24) + '、算出来 18'
                    + TODO_MARK + judge.TODO_NAMES[8]))
    out.append((result.get('seed') == canon_seed(),
                'seed 那一格是 ' + str(canon_seed()) + '（用 canon_seed()，别写别的数）'
                if result.get('seed') == canon_seed() else
                'seed 交回的是 ' + short(repr(result.get('seed')), 20) + '，期望 '
                + str(canon_seed()) + TODO_MARK + judge.TODO_NAMES[8]))
    # 换一个**全错**的沙箱进去：结论必须跟着变——数字写死的会被这一条抓住。
    probe, error = attempt(run_cases, solution, lambda text: '全是错的')
    if error is not None:
        out.append((False, '把判分自己的沙箱塞进 run_cases 时它报错了：' + error
                           + '——sandbox 那一道缝要能用' + TODO_MARK + judge.TODO_NAMES[8]))
    else:
        flags = probe.get('results') if isinstance(probe, dict) else None
        ok = (isinstance(flags, list) and flags == [False] * 5
              and probe.get('passed') is False
              and isinstance(probe.get('failing_case'), dict)
              and probe['failing_case'].get('index') == 0)
        out.append((ok, '换一个全错的沙箱进去：五组全没过、passed 是 False、'
                        '第一个反例落在第 0 组——结论是**跑出来的**，不是写死的'
                    if ok else
                    '换全错的沙箱之后结论没跟着变（交回 ' + short(repr(flags), 40)
                    + '）——「通过吗」必须是算出来的' + TODO_MARK + judge.TODO_NAMES[8]))
    return out


def layer3c(loaded):
    """judge 那一行 + 整条链跑通 + 注入漂移。"""
    label = 'pipeline.py '
    if not loaded.ok('pipeline'):
        return [(False, '端到端这一组跳过：先让上面那一条过（' + label + '载入不完整）')]
    out = []
    judge_fn = loaded.fn('pipeline', 'judge')
    solution, _ = attempt(loaded.fn('pipeline', 'build_solution'), {'picked': '图的搜索'})
    result, _ = attempt(loaded.fn('pipeline', 'run_cases'), solution)
    if isinstance(result, dict) and result:
        got, error = attempt(judge_fn, result)
        out.append((error is None and got == '验证 未过',
                    'judge(验证那一段的产物) 交回「验证 未过」——四组过、第五组没过，'
                    '结论就是「未过」'
                    if error is None and got == '验证 未过' else
                    'judge 交回的是 ' + short(repr(got), 30) + error_note(error)
                    + '，期望「验证 未过」'))
        green = {key: value for key, value in result.items()}
        green['passed'] = True
        green['results'] = [True] * len(result.get('results') or [])
        green['failing_case'] = None
        got2, error2 = attempt(judge_fn, green)
        out.append((error2 is None and got2 == '验证 通过',
                    '把 passed 换成 True 之后 judge 交回「验证 通过」——'
                    '那一行是跟着结论走的'
                    if error2 is None and got2 == '验证 通过' else
                    'passed 换成 True 之后 judge 交回 ' + short(repr(got2), 30)
                    + error_note(error2) + '，期望「验证 通过」'))
    # 整条链。
    loaded.fn('fake_model', 'reset')()
    pipeline_out, error = attempt(loaded.fn('pipeline', 'run_pipeline'), CANON_TEXT,
                                 loaded.fn('fake_model', 'call_model'))
    if error is not None:
        out.append((False, 'run_pipeline(题目文本, 假模型) 报错' + error_note(error)
                           + TODO_MARK + judge.TODO_NAMES[10]))
        return out
    if not isinstance(pipeline_out, dict) or 'record' not in pipeline_out:
        out.append((False, 'run_pipeline 交回的不是五样：' + short(repr(pipeline_out), 50)
                           + TODO_MARK + judge.TODO_NAMES[10]))
        return out
    out.append((pipeline_out.get('done') is True,
                '五段一路跑完，**每两段之间的契约都过了**——记录出得来'
                if pipeline_out.get('done') is True else
                '这条链没跑完，停在了「' + str(pipeline_out.get('stopped'))
                + '」：' + short(str(pipeline_out.get('error')), 60)
                + TODO_MARK + judge.TODO_NAMES[10]))
    record = pipeline_out.get('record')
    out.append((isinstance(record, dict) and record.get('passed') is False,
                '记录的结论与验证那一段一致（passed 是 False：第五组故意对不上）'
                if isinstance(record, dict) and record.get('passed') is False else
                '记录里的 passed 是 ' + short(repr((record or {}).get('passed')), 20)
                + '，期望 False（与验证那一段同一个结论）' + TODO_MARK + judge.TODO_NAMES[9]))
    # 串起来的时候，每两段之间都要真的查一遍：拿一个坏掉的第一段进去。
    before = loaded.fn('contracts', 'check_contract')

    def count_calls(spec, obj):
        count_calls.seen.append(spec)
        return before(spec, obj)

    count_calls.seen = []
    module = loaded.modules['pipeline']
    module.check_contract = count_calls
    try:
        attempt(loaded.fn('pipeline', 'run_pipeline'), CANON_TEXT,
                loaded.fn('fake_model', 'call_model'))
    finally:
        module.check_contract = before
    stages_seen = [spec_text(spec) for spec in count_calls.seen]
    covered = [stage for stage in STAGES
               if any(all(field in text for field in STAGE_FIELDS[stage])
                      for text in stages_seen)]
    out.append((len(covered) == 5,
                '整条链上 check_contract 被调了 ' + str(len(count_calls.seen))
                + ' 次，五段的契约都查过——省掉哪一段，错误就会掉到下游深处去'
                if len(covered) == 5 else
                '这条链只在 ' + str(len(covered)) + ' 段上查了契约（缺 '
                + '、'.join(stage for stage in STAGES if stage not in covered)
                + '）——每两段之间都要查' + TODO_MARK + judge.TODO_NAMES[10]))
    # 类型漂移：passed → 'False'，报错要停在「4 验证」。
    drift = dict(result) if isinstance(result, dict) and result else dict(GOOD[STAGES[3]])
    drift['passed'] = 'False'
    _, error = attempt(judge_fn, drift)
    note = '' if error is None else str(error)
    out.append((error is not None and 'passed' in note and 'bool' in note
                and STAGES[3] in note,
                '把 passed 改成字符串 \'False\' 再交给 judge：当场拦住，'
                '而且点名了「第 4 段的 passed」——错误停在出错的那一段'
                if error is not None and 'passed' in note else
                '类型漂移没被拦住，或者没点名字段（交回 ' + short(note or repr(got), 70)
                + '）——这一条是本课最该抓住的坑：报告会静默地写「验证 通过」，'
                '而正确答案是「未过」'))
    # 字段漂移：让第一段交出 name 而不是 title，报错要停在「1 提取题意」。
    module = loaded.modules['pipeline']
    before_intent = module.extract_intent

    def broken_intent(text, model=None):
        value = dict(before_intent(text, model))
        value['name'] = value.pop('title')
        return value

    module.extract_intent = broken_intent
    try:
        broken, error = attempt(loaded.fn('pipeline', 'run_pipeline'), CANON_TEXT,
                                loaded.fn('fake_model', 'call_model'))
    finally:
        module.extract_intent = before_intent
    stopped = broken.get('stopped') if isinstance(broken, dict) else ''
    out.append((stopped == STAGES[0],
                '把第一段的 title 改成 name：错误停在「' + str(stopped) + '」，'
                '不是五层之外——这就是契约放在边界上的价值'
                if stopped == STAGES[0] else
                '字段漂移之后停在的是「' + str(stopped) + '」，期望「' + STAGES[0]
                + '」——契约检查要在**出错的那一段**就点名，别让错误掉到下游'
                + TODO_MARK + judge.TODO_NAMES[10]))
    return out


# ── 第 4 层 · 记录里的证据与可重放 ──────────────────────────────────────

def layer4a(loaded):
    label = 'pipeline.py '
    if not loaded.ok('pipeline'):
        return [(False, '记录这一组跳过：先让上面那一条过（' + label + '载入不完整）')]
    loaded.fn('fake_model', 'reset')()
    run, error = attempt(loaded.fn('pipeline', 'run_pipeline'), CANON_TEXT,
                        loaded.fn('fake_model', 'call_model'))
    if error is not None or not isinstance(run, dict):
        return [(False, 'run_pipeline 还跑不起来（' + short(str(error), 60) + '）'
                       + TODO_MARK + judge.TODO_NAMES[10])]
    record = run.get('record')
    if not isinstance(record, dict) or not record:
        return [(False, '记录那一格是空的' + TODO_MARK + judge.TODO_NAMES[9])]
    out = []
    evidence = record.get('evidence')
    out.append((isinstance(evidence, list) and len(evidence) == 5
                and all(isinstance(row, str) for row in evidence),
                '记录里有 5 条证据（一组一行）' if isinstance(evidence, list)
                and len(evidence) == 5 else
                '记录里的证据不是 5 条：' + short(repr(evidence), 50)
                + TODO_MARK + judge.TODO_NAMES[9]))
    result = run.get('result') if isinstance(run.get('result'), dict) else {}
    cases = result.get('cases')
    joined = ' '.join(str(row) for row in (evidence or []))
    data_inside = ('0 0 0' in joined and '0 0 1' in joined and '2 1 0' in joined
                   and isinstance(cases, list) and len(cases) == 5)
    out.append((data_inside,
                '证据里带着**数据本身**：那几组输入的原文（0 0 0 / 0 0 1 / 2 1 0 …）'
                '都在，不是「第 1 组过了」这种话'
                if data_inside else
                '证据里看不到数据本身（现在写着 ' + short(repr(joined), 60) + '）——'
                '记录里要留下实际用到的那几组输入与期望：只记 seed 是不够的，'
                '换了 Python 版本，同一个种子的含义就变了' + TODO_MARK + judge.TODO_NAMES[9]))
    first = str(record.get('failed_first') or '')
    out.append((('2 1 0' in first) and ('18' in first) and ('4' in first),
                '记录里有「不合格时的第一个反例」：' + short(first, 60)
                if '2 1 0' in first else
                '记录里的第一个反例对不上（' + short(first, 60) + '）——它要说清组号、'
                '数据、算出来的、期望的四样' + TODO_MARK + judge.TODO_NAMES[9]))
    out.append((record.get('seed') == canon_seed() and isinstance(record.get('rerun'), str)
                and len(str(record.get('rerun'))) > 8,
                '记录里 seed 与「怎么重跑」两格都在（seed 方便、数据可靠，两个都留）'
                if record.get('seed') == canon_seed() else
                '记录里的 seed 是 ' + short(repr(record.get('seed')), 20) + '，期望 '
                + str(canon_seed()) + '；rerun 那一格是 '
                + short(repr(record.get('rerun')), 30) + TODO_MARK + judge.TODO_NAMES[9]))
    out.append((record.get('passed') is run.get('result', {}).get('passed'),
                '报告里的 passed 与验证那一段是同一个结论（不是重新猜一遍）'
                if record.get('passed') is run.get('result', {}).get('passed') else
                '报告里的 passed（' + short(repr(record.get('passed')), 12)
                + '）与验证那一段（' + short(repr(run.get('result', {}).get('passed')), 12)
                + '）不是一个结论' + TODO_MARK + judge.TODO_NAMES[9]))
    return out


def layer4b(loaded):
    label = 'pipeline.py '
    if not loaded.ok('pipeline'):
        return [(False, '两遍这一组跳过：先让上面那一条过（' + label + '载入不完整）')]
    out = []
    loaded.fn('fake_model', 'reset')()
    first, error = attempt(loaded.fn('pipeline', 'run_pipeline'), CANON_TEXT,
                          loaded.fn('fake_model', 'call_model'))
    loaded.fn('fake_model', 'reset')()
    second, _ = attempt(loaded.fn('pipeline', 'run_pipeline'), CANON_TEXT,
                       loaded.fn('fake_model', 'call_model'))
    if error is not None or not isinstance(first, dict) or not isinstance(second, dict):
        return [(False, '跑两遍这一组还没法试（' + short(str(error), 50) + '）'
                       + TODO_MARK + judge.TODO_NAMES[10])]
    one, two = first.get('record'), second.get('record')
    out.append((normalize_value(one) == normalize_value(two) and one is not None,
                '两遍完整流程的记录逐字相同——同一份数据、同一个结论，'
                '重放得出来'
                if normalize_value(one) == normalize_value(two) else
                '两遍的记录不一样（第一遍 ' + short(repr(one), 40) + ' / 第二遍 '
                + short(repr(two), 40) + '）——这一课的数据是确定的，两遍必须同结论'
                + TODO_MARK + judge.TODO_NAMES[9]))
    r1, r2 = first.get('result', {}), second.get('result', {})
    out.append((r1.get('passed') is r2.get('passed')
                and normalize_value(r1.get('outputs')) == normalize_value(r2.get('outputs')),
                '两遍算出来的五个值与结论都一样（'
                + short(repr(r1.get('outputs')), 40) + '）——证据是可以拿去重放的'
                if normalize_value(r1.get('outputs')) == normalize_value(r2.get('outputs'))
                else '两遍算出来的值不一样：' + short(repr(r1.get('outputs')), 40) + ' / '
                     + short(repr(r2.get('outputs')), 40) + TODO_MARK + judge.TODO_NAMES[8]))
    # 全过的那一组：failing_case 是 **None**，failed_first 写「没有反例」。
    # 判分自己造这一份（把期望值换成真值），不靠 run_cases ——
    # 判分留下的那五组里，第五组的期望值是**故意写错的**，那一组永远过不了。
    good_cases = [[text, canon_exec(text)] for text, _ in canon_cases()]
    good_outputs = [canon_exec(text) for text, _ in canon_cases()]
    solution, _ = attempt(loaded.fn('pipeline', 'build_solution'), {'picked': '图的搜索'})
    green = {'cases': good_cases, 'outputs': good_outputs,
             'results': [True] * len(good_cases), 'passed': True,
             'evidence': ['第 ' + str(i) + ' 组: ' + str(text.splitlines()[0])
                          + ' 算出来 ' + got + ' / 期望 ' + got + ' → 过'
                          for i, ((text, _), got) in enumerate(zip(canon_cases(), good_outputs))],
             'failing_case': None, 'seed': canon_seed(), 'mode': '对拍'}
    record, error = attempt(loaded.fn('pipeline', 'make_record'), CANON_TEXT, green,
                           '图的搜索')
    if error is not None or not isinstance(record, dict):
        out.append((False, 'make_record(全过的那一组) 报错' + error_note(error)
                           + TODO_MARK + judge.TODO_NAMES[9]))
    else:
        first_bad = str(record.get('failed_first') or '')
        out.append((record.get('passed') is True and '没有反例' in first_bad,
                    '全过的那一组（failing_case 是 None）：报告里 passed 是 True、'
                    'failed_first 写的是「' + short(first_bad, 30) + '」——'
                    '不是一句光秃秃的「通过」'
                    if record.get('passed') is True and '没有反例' in first_bad else
                    '全过的那一组不对：passed ' + short(repr(record.get('passed')), 10)
                    + '、failed_first ' + short(first_bad, 40)
                    + '——要说清「没有反例：全部组都过了」，别写成空字符串或 None'
                    + TODO_MARK + judge.TODO_NAMES[9]))
    return out


# ── 第 5 层 · 打印行、单跑、文件没被动过 ────────────────────────────────

def run_script(path):
    """起一个子进程跑一个脚本 → (退出码, stdout, stderr)。"""
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    try:
        done = subprocess.run([sys.executable, str(path)], cwd=str(path.parent),
                              capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=180, env=env)
    except Exception as exc:
        return None, '', '起不了子进程：' + type(exc).__name__ + ': ' + str(exc)
    return done.returncode, done.stdout or '', done.stderr or ''


def layer5a(loaded):
    out = []
    runs = [run_script(HERE / name) for name in TASK_FILES]
    for name, (code, text, err) in zip(TASK_FILES, runs):
        if code is None:
            out.append((False, name + ' 起不了子进程：' + short(err, 80)))
        elif 'Traceback' in (err or '') or 'Traceback' in (text or ''):
            tail = (err or text).strip().splitlines()
            out.append((False, name + ' 单跑时抛了异常，最后一行是 ' + short(tail[-1], 70)
                               + '——每个 .py 都要能**单独跑通**（退出码 0、0 处 Traceback），'
                                 '还没接上的那一段打占位、不崩'
                               + TODO_MARK + judge.TODO_NAMES[4]))
        elif code != 0:
            out.append((False, name + ' 单跑的退出码是 ' + str(code) + '，期望 0'
                               + TODO_MARK + judge.TODO_NAMES[4]))
        else:
            out.append((True, name + ' 单跑退出码 0、0 处 Traceback（'
                              + str(len((text or '').splitlines())) + ' 行输出）'))
    return out, runs


def layer5b(loaded, runs):
    out = []
    shown_ok = {
        # 表头那一行打的是「契约表 5 行」——判分的标签读法是「第一个空格前面是标签」，
        # 所以这里的标签就是「契约表」，值是「5 行」。
        'contracts.py': [('契约表', '5 行')],
        'parse.py': [('干净 JSON', '拿下'), ('带围栏', '拿下'), ('带前言', '拿下'),
                     ('三档串起来吃下', '3/4 种')],        'pipeline.py': [('提取出来的标题', '拨钟问题'), ('推荐算法', '图的搜索'),
                        ('验证结论', 'False'), ('记录的 seed', str(canon_seed())),
                        ('记录里的证据条数', '5'), ('五段都过了契约吗', 'True'),
                        ('停在哪一段', '（没有停，五段都过了）'),
                        ('两遍的记录一样吗', 'True')],
    }
    owners = {'contracts.py': judge.TODO_NAMES[1], 'parse.py': judge.TODO_NAMES[4],
              'pipeline.py': judge.TODO_NAMES[10]}
    for name, pairs in shown_ok.items():
        index = TASK_FILES.index(name)
        rows = parse_shown(runs[index][1])
        for label, want in pairs:
            got = shown(rows, label)
            if got is None:
                out.append((False, name + ' 的输出里没有「' + label + '」这一行——'
                                   '打印行是判分接口，别改它们' + TODO_MARK + owners[name]))
                continue
            out.append(check_line(got, [want],
                                  name + ' 的「' + label + '」逐字对上：' + want,
                                  name + ' 的「' + label + '」对不上' + TODO_MARK + owners[name]))
    # 被截断那一组：两次调用、第二次带 retry。
    index = TASK_FILES.index('pipeline.py')
    rows = parse_shown(runs[index][1])
    for label, want, owner in (('第一段调用了几次模型', '2', judge.TODO_NAMES[6]),
                               ('第二次的 retry 标记', 'True', judge.TODO_NAMES[6]),
                               ('第一次那一份是截断的吗', 'True', judge.TODO_NAMES[6]),
                               ('漂移之后输出里写的结论', '验证 通过', judge.TODO_NAMES[2]),
                               ('正确答案', '验证 未过', judge.TODO_NAMES[2]),
                               ('契约检查放过了它吗', 'False', judge.TODO_NAMES[2])):
        got = shown(rows, label)
        if got is None:
            out.append((False, 'pipeline.py 的输出里没有「' + label + '」这一行'
                               + TODO_MARK + owner))
            continue
        out.append(check_line(got, [want],
                              'pipeline.py 的「' + label + '」逐字对上：' + want,
                              'pipeline.py 的「' + label + '」对不上' + TODO_MARK + owner))
    return out


def layer5c(loaded):
    """tools.py 与 fake_model.py 逐字节相同吗、源码里有没有连续三个反引号。"""
    out = []
    fence = make_fence()
    for name in ('tools.py', 'fake_model.py'):
        raw = (HERE / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest().upper()
        want = SEALED_SHA256[name]
        if want.startswith('PLACEHOLDER'):
            out.append((False, name + ' 的期望哈希没填（判分自己没装好）'))
        elif digest == want:
            out.append((True, name + ' 与发下来那一份逐字节相同（SHA-256 '
                              + digest[:8] + '）——四份预置输出与那几组数据全靠它'))
        else:
            out.append((False, name + ' 被改过了（SHA-256 是 ' + digest[:8] + '，期望 '
                               + want[:8] + '）——这两个文件是给好的：判分与课件那几组'
                               '实测数字全靠它们。从任务目录外拿一份原始的覆盖回来'))
    hits = []
    for path in sorted(HERE.glob('*.py')):
        if fence in path.read_bytes().decode('utf-8'):
            hits.append(path.name)
    out.append((not hits,
                '这个目录的 .py 源码里一个连续三个反引号都没有（README.md 那种文档不算）'
                if not hits else
                '这几个 .py 源码里出现了连续三个反引号：' + '、'.join(hits)
                + '——本 lab 的源码里不许有它（会打断阅卷与工具链）。'
                  '要拼围栏就用 tools.make_fence()'))
    empty = []
    for name in TASK_FILES:
        if not (HERE / name).read_text(encoding='utf-8').strip():
            empty.append(name)
    out.append((not empty, '四个任务文件都不是空文件' if not empty else
                '这几个任务文件是空的：' + '、'.join(empty)))
    return out


def layer5d(loaded):
    """说明与记录那两份文档：至少要有这几段（判分只读它们的标题与几个哨兵词）。"""
    out = []
    answer = TASK_DIR / 'answer.md'
    if not answer.exists():
        out.append((False, 'answer.md 不在 ' + str(TASK_DIR) + '（说明要跟着 lab 一起交）'))
    else:
        text = answer.read_text(encoding='utf-8')
        if '我不放心的地方' not in text:
            out.append((False, 'answer.md 里没有「我不放心的地方」这一节——'
                               '**这一条是硬要求**：一份没有「不确定」的说明，'
                               '说明你没真正检查过自己的东西。另外写清每一处的**触发条件**'))
        else:
            ok = ('触发条件' in text) and ('如果' in text or '当' in text)
            out.append((ok, 'answer.md 里有「我不放心的地方」，而且每一条都带了触发条件'
                        if ok else
                        'answer.md 的「我不放心的地方」里没有写清**触发条件**'
                        '（要有「如果…就会…」这类条件句，不能只说「这里可能有问题」）'))
        for mark in ('五段', '契约', '重试', 'seed'):
            if mark not in text:
                out.append((False, 'answer.md 里没讲到「' + mark + '」——'
                                   '说明要讲清五个环节各自为什么这么设计'))
    record = TASK_DIR / 'record.md'
    if not record.exists():
        out.append((False, 'record.md 不在 ' + str(TASK_DIR) + '（记录模板要跟着 lab 一起交）'))
    else:
        text = record.read_text(encoding='utf-8')
        marks = {'数据本身': '数据本身', '反例': '反例', 'seed': 'seed'}
        missing = [name for name, mark in marks.items() if mark not in text]
        out.append((not missing,
                    'record.md 里该有的几样都在：数据本身、第一个反例、seed'
                    if not missing else
                    'record.md 里缺这几样：' + '、'.join(missing)
                    + '——光写一个「通过」不算记录'))
    return out


# ── 主流程 ──────────────────────────────────────────────────────────────

LAYERS = [
    ('第 1 层 · 五段的契约表与检查器', [layer1a, layer1b, layer1c],
     'contracts.py 的 TODO 1（五段契约）/ 2（检查器）/ 3（那张表）'),
    ('第 2 层 · 三档解析（含被截断那一档）', [layer2a, layer2b, layer2c],
     'parse.py 的 TODO 3 / 4 / 5（三档解析器）'),
    ('第 3 层 · 五段各自的产物与整条链', [layer3a, layer3b, layer3c],
     'pipeline.py 的 TODO 6（第一段）/ 7（第二段）/ 8（第四段）/ 10（串起来）'),
    ('第 4 层 · 记录里的证据与可重放', [layer4a, layer4b],
     'pipeline.py 的 TODO 9（第五段 make_record）'),
    ('第 5 层 · 打印行、单跑、文件没被动过', [],
     '五个脚本里的 TODO——这一层读的是它们打印出来的行，所以那些 print 别改'),
]


def main():
    print('StudyMate lab 0033 · 自动判分（综合实战：把刷题助手做完）')
    print('目录：' + str(HERE))
    print()
    loaded = Loaded()
    passed = 0
    failed = 0
    layers_ok = 0
    runs = [None] * len(TASK_FILES)
    for title, checks, todo_scope in LAYERS:
        print(title)
        layer_ok = True
        results = []
        crash = ('判分这一组自己抛了异常（多半是任务文件里交回的东西形状太出乎意料）。'
                 '把下面这段贴给教练' + TODO_MARK + todo_scope + '：\n')
        for check in checks:
            try:
                results.extend(check(loaded))
            except Exception:                             # 判分自己也不许崩
                results.append((False, crash + traceback.format_exc()))
        if title.startswith('第 5 层'):
            try:
                one, runs = layer5a(loaded)
            except Exception:
                one = [(False, crash + traceback.format_exc())]
            results.extend(one)
            try:
                results.extend(layer5b(loaded, runs))
            except Exception:
                results.append((False, crash + traceback.format_exc()))
            try:
                results.extend(layer5c(loaded))
            except Exception:
                results.append((False, crash + traceback.format_exc()))
            try:
                results.extend(layer5d(loaded))
            except Exception:
                results.append((False, crash + traceback.format_exc()))
        for ok, message in results:
            if not ok and TODO_MARK not in message:
                message = message + '  → 要补的是 ' + todo_scope
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
        print('五层全过。现在去对照 ../solutions/0033-capstone-ai-tutor/：')
        print('比一比那六步各自是怎么被做出来的，再翻回课件自检清单最后两条。')
        return 0
    print('卡住了先读 ../README.md 的自查清单，再看每条 FAIL 后面点出的那一段 TODO。')
    print('判分读的就是五个脚本打印出来的行，也别改那些 print；tools.py 与 fake_model.py')
    print('是给好的，别改。全部过了再对照 ../solutions/0033-capstone-ai-tutor/。')
    return 1


if __name__ == '__main__':
    sys.exit(main())
