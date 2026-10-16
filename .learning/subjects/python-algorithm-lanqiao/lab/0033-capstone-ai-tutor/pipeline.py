"""pipeline.py · 五段串起来：题目文本进，带证据的记录出（lab 0033 任务 5 · 参考解）

    ┌── 1 提取题意（调模型，带重试）──┐
    │  题目文本 ──▶ call_model ──▶ parse_json ──▶ {title, constraints, ask}
    └──────────── check_contract ────┘
                 ▼
    2 推荐候选算法 → {candidates, reasons, picked}
                 ▼
    3 写解法 → {code, entry, complexity}
                 ▼
    4 自动验证 → {passed, evidence, failing_case, cases, outputs, results, seed}
                 ▼
    5 出记录 → {problem, picked, passed, evidence, seed, rerun, failed_first, mode}

**`call_model` 是这一条链上唯一那道缝。** 默认接的是 fake_model（离线、四份预置输出），
接真 API 的时候只换这一处，其余四段一行都不用改。

三段各有各的要点，别混在一起查：

  · **第一段**：解析失败**不是**都由解析器负责。被截断那一档三档都救不回来
    （内容不完整，不是格式问题），它必须走**重试**——带着「上次输出被截断了」再问一次。
    重试还失败才交回占位，好让记录里留下「这一段是坏的」这个事实。
  · **第四段**：拿数据**真的跑一遍**解法，再跟期望输出比。evidence 里要留下**用到的数据本身**，
    不是「第 1 组过了」这种话。第一个反例要连组号、数据、算出来的、期望的**四样**一起交。
  · **第五段**：报告里的 passed 与验证那一段的 passed 必须是同一个结论。

判分接口（别改名字、别改那个 if __name__ 里的打印行）：

    extract_intent(text, model)             → 第 1 段的输出
    recommend(intent, model)                → 第 2 段的输出
    build_solution(rec)                     → 第 3 段的输出
    run_cases(solution, sandbox=None)       → 第 4 段的输出
    judge(record)                           → 一行结论（'验证 通过' / '验证 未过'）
    make_record(text, result, picked)       → 第 5 段的输出
    run_pipeline(text, model)               → 五段跑一遍的完整结果

跑： py pipeline.py
判： py run_tests.py
"""

import itertools
import json
import re

from contracts import CONTRACTS, STAGES, check_contract
from fake_model import advice, call_model
from parse import ParseFailure, parse_json
from tools import (CANON_TEXT, BUTTONS, TODO_NAMES, canon_cases, canon_exec, canon_seed,
                   clamp, contract_error, is_bool, normalize_value, show_banner, show_line,
                   todo_mark, TypeSpec)

# 第二段的那份预置推荐（模型建议的算法族）。
ADVICE_RAW = advice()

# 这一课要写的解法：拨钟问题——枚举每个按钮按 0..3 次，取总次数最小的那一个。
SOLUTION_CODE = '''def solve(text):
    """拨钟问题：枚举 9 个按钮各按 0..3 次（4^9 种），取总按键次数最小的一组。"""
    import itertools
    values = [int(x) for x in text.split()]
    if len(values) != 9:
        raise ValueError("输入要有 9 个整数")
    best = None
    for combo in itertools.product(range(4), repeat=9):
        state = [0] * 9
        total = 0
        for index, times in enumerate(combo):
            total += times
            if times:
                for clock in BUTTONS[index]:
                    state[clock] = (state[clock] + times) % 4
        if tuple(state) == tuple(values) and (best is None or total < best):
            best = total
    return "impossible" if best is None else str(best)
'''

# 第二段筛候选用的关键词表：模型会给出很自信但不沾边的族，拿它对一遍。
FAMILY_KEYS = {
    '图的搜索': ['最少步数', '最短步数', '最少按键次数', '走法', '状态空间', '扩散'],
    '动态规划': ['最优子结构', '转移方程', '每件最多选一次'],
    '二分答案': ['最大化最小值', '最小化最大值', '单调'],
    '枚举': ['枚举', '暴力', '4^9', '状态空间'],
}

# 「验证那一段该长什么样」那一份契约：judge 用它做边界检查（给好的，别改）。
VERDICT_SPEC = CONTRACTS.get(STAGES[3], TypeSpec(STAGES[3], {'passed': is_bool}))


# ══ TODO 6 ═════════════════════════════════════════════════
# 第一段：题目文本 → 题意（**要调模型，而且带重试**）。
#
# 做三件事：
#   1) 拼提示词：要让模型交回 title / constraints / ask 三样，其中 constraints 是
#      {n_max, value_max} 两个整数。
#   2) 调模型 + 解析：第一次 call_model(prompt)；解析失败就**带着坏消息再问一次**——
#      重试的提示词里要出现「截断」两个字（假模型按它给干净的那一份），
#      这一句就是「把上一轮失败的样子告诉模型」：call_model(prompt + 一句坏消息, retry=True)。
#      **必须传 retry=True**：不传的话假模型照样交回半截，重试等于没做。
#   3) 两次都失败：交回一个**说得清**的占位值（title 写成「（提取失败：括号不闭合…）」），
#      不要交回 None、也不要抛异常——整条链要带着「这一段坏了」这个事实继续走，
#      记录里才有东西可写。契约里 title 是 str，占位值也是 str，所以契约仍然过。
#
# 交回 {'title': str, 'constraints': {'n_max': int, 'value_max': int}, 'ask': str}。
def extract_intent(text, model=None):
    return {'title': '（还没接上）', 'constraints': {'n_max': 0, 'value_max': 0},
    'ask': '（还没接上）'}


# ══ TODO 7 ═════════════════════════════════════════════════
# 第二段：第 1 段的 dict → 候选算法（**也要调模型**，但这一段的输入是上一段的产物）。
#
# 交回 {'candidates': [str], 'reasons': [str], 'picked': str}。
#
# 模型给的那一份预置推荐（ADVICE_RAW）里有 candidates / reasons / picked 三样，
# 解析出来照抄即可；要点是**交叉检查**：拿本文件那张 FAMILY_KEYS 去对一遍，
# 把一条关键词都没命中的候选从 candidates 里筛掉——模型会给出很自信但不沾边的族，
# 筛掉之后 picked 也要跟着落到第一个还剩下来的候选上。
#
# 这一段的调用**不重试**（重试是第一段的事）：解析失败就交回空表 + picked 写成一句说明，
# 让下游的契约检查去喊——别在这里静默地猜一个算法族出来。
def recommend(intent, model=None):
    return {'candidates': [], 'reasons': [], 'picked': '（还没接上）'}


# ══ TODO 8 ═════════════════════════════════════════════════
# 第四段：第 3 段的 dict + 数据 → 验证结论（**这一课最要紧的一段**）。
#
# 拿 canon_cases() 那几组数据，**真的跑一遍**解法（第三段产物里的那个 entry 函数），
# 再跟每一组的期望输出比。交回八个键：
#
#   cases        [ [输入, 期望输出], … ]     用到的**数据本身**（不是只留一个 seed）
#   outputs      [ 算出来的, … ]             每组跑出来的实际值
#   results      [ bool, … ]                 每组过没过，**真的布尔值**
#   passed       bool                        **全部**过了才是 True
#   evidence     [str, … ]                   每组一行：组号 + 数据 + 算出来 + 期望 + 过没过
#   failing_case 第一个反例 → {'index': int, 'case': [输入, 期望], 'got': 算出来的}；
#                            一组都没失败时是 **None**
#   seed         int                         canon_seed()（方便重跑用）
#   mode         str                         '对拍'（这一份数据是固定的一组）
#
# 三个必须做对的地方：
#   · `results` / `passed` 要交**真布尔值**（True / False 本身）——写字符串是这一课最大的坑：
#     'False' 是非空字符串，在布尔语境里是 True，报告会静默地写「验证 通过」；
#   · 每组都要跑，**别短路**（别「一失败就 break」）：记录里要能看到「5 组里过了 4 组」；
#   · 比之前先 tools.normalize_value 归一化：JSON 往返会把 tuple 变成 list，
#     不然「同一份数据」在两边看起来是不相等的。
def run_cases(solution, sandbox=None):
    return {'cases': [], 'outputs': [], 'results': [], 'passed': False,
    'evidence': [], 'failing_case': None, 'seed': canon_seed(),
    'mode': '（还没接上）'}


# ══ TODO 9 ═════════════════════════════════════════════════
# 第五段：第 4 段的 dict → 带证据的记录。
#
# 交回八个键（前六个照抄课件的契约，后两个是模板要的两行）：
#
#   problem       题目文本（一段**改短过**的说明即可，别把整篇题目抄进来）
#   picked        这一次选了哪个算法族
#   passed        **与验证那一段同一个结论**（不是重新猜一遍）
#   evidence      一行行的证据（照抄验证那一段的，别自己重写一份）
#   seed          第 4 段的 seed
#   rerun         怎么重跑这一份：「数据在 cases 里，不看 seed」这类话说清楚
#   failed_first  第一个反例写成一行；**一个反例都没有时**写 '（没有反例：全部组都过了）'
#   mode          照抄第 4 段的 mode
#
# 记录的价值在**数据本身**：seed 只保证「同一个环境下能复现」，换了 Python 版本、
# 改了随机调用的顺序，同一个种子的含义就变了。所以 cases 与 outputs 必须原样在记录里。
def make_record(text, result, picked):
    return {'problem': '（还没接上）', 'picked': picked, 'passed': False,
    'evidence': [], 'seed': 0, 'rerun': '（还没接上）',
    'failed_first': '（还没接上）', 'mode': '（还没接上）'}


# ══ TODO 10 ═════════════════════════════════════════════════
# 把五段串起来：**每两段之间都要 check_contract**。
#
# 顺序（一步都不能省——省掉的那一步就是「错误在下游深处才崩」）：
#
#   intent = extract_intent(text, model)     → check_contract(CONTRACTS['1 提取题意'], intent)
#   advice = recommend(intent, model)        → check_contract(CONTRACTS['2 推荐算法'], advice)
#   solution = build_solution(advice)        → check_contract(CONTRACTS['3 写解法'], solution)
#   result = run_cases(solution)             → check_contract(CONTRACTS['4 验证'], result)
#   record = make_record(text, result, advice['picked'])
#                                            → check_contract(CONTRACTS['5 出记录'], record)
#
# 交回七样：{'intent', 'advice', 'solution', 'result', 'record', 'done', 'stopped'}。
# 契约不对时 check_contract 会抛 TypeError，**错误就停在那一段**——
# 别用 try 把它吞掉：那正是这一课要防的静默错误。
#
# 交回里的 done 是「五段都过了契约吗」（bool），stopped 是「停在哪一段」：
# 全过时是空串，被契约拦住时是**那一段的段名**——记录里因此留着「坏在哪一段」这个事实，
# 而不是一句笼统的「跑失败了」。
def run_pipeline(text, model=None):
    return {'intent': {}, 'advice': {}, 'solution': {}, 'result': {},
    'record': {}, 'done': False, 'stopped': '（还没接上）'}


# ── 给好的几个：第三段、以及「差不多」的那种写法与结论那一行 ────────────────

def build_solution(rec):
    """第三段：把选定的算法族落成一份能跑的源码（给好的，别改）。"""
    return {
        'code': SOLUTION_CODE,
        'entry': 'solve(text) —— 输入 9 个整数的那段文本，输出最少按键次数或 impossible',
        'complexity': 'O(4^n · n)：n = 9 时 262144 种组合，每个组合走一遍 n 个按钮',
    }


def as_bool(value):
    """这一格「差不多是不是真的」——**给好的，但别用它做判定**。

    它就是那个陷阱的写法：'False' 是非空字符串，在布尔语境里是 True。
    本课保留它是为了让你**看见**这一条路有多顺：报告里会静默地写出「验证 通过」。
    """
    return bool(value)


def verdict_of(record):
    """按验证结论交回一行话（给好的，别改）。

    它**先跑第 4 段的契约检查**，所以 passed 是 'False' 这种字符串时它会当场抛出来，
    而不是静默地写出「验证 通过」——这就是契约检查放在边界上的价值。
    """
    check_contract(VERDICT_SPEC, record)
    return '验证 ' + ('通过' if record.get('passed') is True else '未过')


def judge(record):
    """verdict_of 的另一个名字（判分按 judge 这个名字调，别改）。"""
    return verdict_of(record)


def show_verdict(record):
    """打印用：契约不对（或那一段还没接上）就打印一句话（不抛），对了就打印结论。"""
    note = contract_error(VERDICT_SPEC, record)
    if note:
        return '（契约拦住了：' + note + '）'
    try:
        return verdict_of(record)
    except NotImplementedError:
        return '（检查器那一段还没接上）'


# ── 内部小工具（给好的，别改）───────────────────────────────────────────

def _ask_and_parse(model, prompt, retry):
    """问一次模型并解析；解析失败交回 None（由调用处决定要不要重试）。"""
    try:
        raw = model(prompt, retry=retry)
    except TypeError:              # 传进来的模型函数只吃一个参数
        raw = model(prompt)
    try:
        value = parse_json(raw)
    except ParseFailure:
        return None
    return value if isinstance(value, dict) else None


def _as_int(value):
    """整数那一格：不是 int 就试着转，转不了就退回 0（那一格是 int，别交字符串）。"""
    if isinstance(value, bool) or not isinstance(value, int):
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return 0
    return value


def _as_intent(value):
    """把解析出来的字典归成第一段的契约形状（缺的字段补成说得清的占位）。"""
    limits = value.get('constraints') if isinstance(value.get('constraints'), dict) else {}
    return {
        'title': str(value.get('title') or '（题目没给名字）'),
        'constraints': {
            'n_max': _as_int(limits.get('n_max')),
            'value_max': _as_int(limits.get('value_max')),
        },
        'ask': str(value.get('ask') or '（没提取到要求）'),
    }


def _entry_name(entry):
    """从 'solve(text) —— …' 里把函数名抠出来（'solve'）。"""
    if not isinstance(entry, str):
        return ''
    match = re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)', entry)
    return match.group(1) if match else ''


def _load_entry(code, name):
    """把一段源码执行一遍，取里面的 name 那个函数。

    命名空间里预置了 BUTTONS 与 itertools：这一段代码是「解法」，
    它要能拿到题目给的那张按钮表。
    """
    space = {'BUTTONS': BUTTONS, 'itertools': itertools}
    try:
        exec(compile(code, '<solution>', 'exec'), space)      # noqa: S102
    except Exception:
        return None
    return space.get(name)


def _make_runner(solution, sandbox):
    """要一个「输入文本 → 算出来的文本」的函数。

    几种情形都堵住，免得调用处拿 None 去跑：
      · sandbox 是可调用的 → 就用它（判分塞自己的探针就走这一支）；
      · solution 里带着 code（第三段的产物）→ 把那段 code 里的 entry 函数取出来
        （这一支才是**真的在跑解法**，不是拿期望值糊过去）；
      · solution 自己就是可调用的 → 用它；
      · 别的（solution 是 None、是不带 code 的 dict）→ 退回 tools.canon_exec。
    """
    if callable(sandbox):
        return lambda text: sandbox(text)
    entry = 'solve'
    if isinstance(solution, dict):
        entry = str(solution.get('entry_name') or _entry_name(solution.get('entry')) or 'solve')
        code = solution.get('code')
        if isinstance(code, str) and code.strip():
            fn = _load_entry(code, entry)
            if callable(fn):
                return lambda text: fn(text)
    if callable(solution):
        return lambda text: solution(text)
    return lambda text: canon_exec(text)


def _brief(text):
    """证据行里那一段数据：换成一行、太长就截断（数据本身要留，但别把记录撑爆）。"""
    return clamp(' '.join(str(text).split()), 40)


if __name__ == '__main__':                      # 别改：判分读的就是下面这几行
    show_banner('0033 最简一条线：题目文本进，记录出')
    pipeline = run_pipeline(CANON_TEXT, call_model)
    intent = pipeline['intent']
    advice_out = pipeline['advice']
    solution = pipeline['solution']
    result = pipeline['result']
    record = pipeline['record']
    show_line('提取出来的标题', intent.get('title') if isinstance(intent, dict)
              else '（还没接上）')
    show_line('推荐算法', advice_out.get('picked') if isinstance(advice_out, dict)
              else '（还没接上）')
    show_line('解法入口', solution.get('entry') if isinstance(solution, dict)
              else '（还没接上）')
    show_line('验证结论', result.get('passed') if isinstance(result, dict)
              else '（还没接上）')
    show_line('记录里的结论', show_verdict(result) if isinstance(result, dict) and result
              else '（还没接上）')
    show_line('记录的 seed', record.get('seed') if isinstance(record, dict)
              else '（还没接上）')
    show_line('记录里的证据条数', len(record.get('evidence') or [])
              if isinstance(record, dict) else '（还没接上）')
    show_line('第一个反例', record.get('failed_first') if isinstance(record, dict)
              else '（还没接上）')
    show_line('这一遍拿到几条证据', len(result.get('evidence') or [])
              if isinstance(result, dict) else '（还没接上）')
    show_line('五段都过了契约吗', pipeline.get('done'))
    show_line('停在哪一段', pipeline.get('stopped') or '（没有停，五段都过了）')

    show_banner('0033 跑两遍：结论一致吗')
    again = run_pipeline(CANON_TEXT, call_model)
    show_line('两遍的记录一样吗', again['record'] == record)
    show_line('两遍的结论一样吗',
              (again['result'].get('passed') is result.get('passed')))

    show_banner('0033 被截断那一档：必须走重试，不许静默吞掉')
    import fake_model
    fake_model.reset()
    intent2 = extract_intent(CANON_TEXT, fake_model.call_model)
    calls = fake_model.CALLS
    show_line('第一段调用了几次模型', len(calls))
    show_line('第二次的 retry 标记', calls[1][1] if len(calls) > 1 else '（没有第二次）')
    show_line('两次拿到的输出一样吗',
              bool(len(calls) > 1) and calls[0][2] == calls[1][2])
    show_line('第一次那一份是截断的吗',
              bool(calls) and fake_model.looks_truncated(calls[0][2]))
    show_line('重试之后的标题', intent2.get('title') if isinstance(intent2, dict)
              else '（还没接上）')

    show_banner('0033 注入一个类型漂移：passed 变成字符串')
    real = result if isinstance(result, dict) and result else {'passed': True}
    drift = dict(real, passed='False')          # 只改这一格：True → 字符串 'False'
    show_line('契约检查放过了它吗',
              contract_error(VERDICT_SPEC, drift) == '')
    show_line('契约检查怎么说漂移后那一格', contract_error(VERDICT_SPEC, drift)
              or '（契约放过了它）')
    show_line('漂移之后输出里写的结论',
              '验证 ' + ('通过' if as_bool(drift.get('passed')) else '未过'))
    show_line('正确答案', '验证 ' + ('通过' if drift.get('passed') is True else '未过'))
    show_line('静默地当成「通过」了吗', as_bool(drift.get('passed')) is True)
    show_line('不查契约时报告会写错吗',
              '验证 ' + ('通过' if as_bool(drift.get('passed')) else '未过') != '验证 未过')
    show_line('judge 吃这一份会怎样',
              contract_error(VERDICT_SPEC, drift) or show_verdict(drift))
    show_line('同一份合格记录上 judge 交回', show_verdict(real))
