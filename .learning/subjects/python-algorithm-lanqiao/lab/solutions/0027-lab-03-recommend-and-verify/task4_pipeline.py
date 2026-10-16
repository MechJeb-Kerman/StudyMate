"""任务 4 · 端到端：题面进，候选实现 + 验证结论出（lab 0027）· 参考解

前面三段给出的是**候选**。最后这一段决定要不要信它。

拿「区间调度」当例子：推荐给出「贪心」，然后写两个实现——**都叫贪心，只是排序关键字不同**：

    实现 A  按开始时间排（tools.greedy_by_start）——很自然，但在区间调度上错；
    实现 B  按结束时间排（tools.greedy_by_end）——对。

课件那一组数据（tools.case_intervals(6)）上：A 选出 1 个，B 选出 6 个，暴力最优 6 个。

**推荐给出的名字是对的，两个实现却一个好一个坏。** 所以验证环节要验的是**具体实现**，
不是算法名——名字下面可以挂无数种写法，其中大部分是错的。

整条链的结论也不该是「推荐用贪心」，而该是「推荐贪心 → A 被否掉（附反例）→ B 通过」。
有反例的否掉，比没有反例的通过更有价值：前者告诉你这条路走不通，而且给了你能复现的证据。

跑： py task4_pipeline.py
判： py run_tests.py
"""

import json

from task1_prompt import build_prompt, fake_model
from task3_classify import classify
from tools import (PROBLEMS, brute_best, candidate_impl, case_intervals, clamp,
                   show_banner, show_line)

# 两个候选实现的名单：名字 + 「怎么排的」；函数用 tools.candidate_impl 取。
CANDIDATES = [
    ('A', '按开始时间排'),
    ('B', '按结束时间排'),
]


def resolve(raw):
    """把模型返回的那段文本变成本课能用的推荐结论。

    三种结局三种形状：{'ok': True, family/confidence/why}、
    {'ok': False, 'reason': '<异常类名>'}、{'ok': False, 'reason': '不是字典'}。
    第六种形态（引号没转义）落到第二支：交回**一个结论**，而不是把异常放出去。
    """
    try:
        value = json.loads(raw)
    except Exception as exc:
        return {'ok': False, 'reason': '<' + type(exc).__name__ + '>'}
    if not isinstance(value, dict):
        return {'ok': False, 'reason': '不是字典'}
    for key in ('family', 'confidence', 'why'):
        if key not in value:
            return {'ok': False, 'reason': '不是字典'}
    return {'ok': True, 'family': value['family'],
            'confidence': value['confidence'], 'why': value['why']}


def run_trial(family, intervals):
    """同一个算法族下的每个候选实现各跑一遍，跟暴力比 → (verdicts, want)。

    每个实现都把它实际选出来的那张表交回来：没通过的那一张就是**反例**，
    通过的那一张让判分核对「选出几个」不是写死的。两个实现都跑，不短路。
    """
    want = brute_best(intervals)
    verdicts = []
    for name, how in CANDIDATES:
        picked = list(candidate_impl(name)(intervals))
        passed = len(picked) == want
        verdicts.append((name, how, len(picked), passed, picked))
    return verdicts, want


def nothing_passed(verdicts):
    """这条链有没有验证出可用结论？一个都没通过 → True；有任何一个通过 → False。"""
    any_pass = any(row[3] for row in (verdicts or []))
    return not any_pass


def as_result(value):
    """把 resolve 交回的东西归成能取键的字典（交回别的就归成空字典）。"""
    return value if isinstance(value, dict) else {}


if __name__ == '__main__':
    CASE = case_intervals(6)

    show_banner('0027 端到端：题面进，推荐出')
    problem = PROBLEMS['区间调度']
    prompt = build_prompt(problem)
    raw = fake_model(prompt)
    rec = as_result(resolve(raw))
    show_line('模型给的原文', clamp(raw, 72))
    show_line('推荐的算法族', rec.get('family') if rec.get('ok')
              else rec.get('reason', '（还没接上）'))

    show_banner('0027 同族两个实现，结论不同')
    trial = run_trial('贪心', CASE)
    if isinstance(trial, tuple) and len(trial) == 2:
        verdicts, want = trial
    else:
        verdicts, want = [], 0
    lengths = []
    for name, how in CANDIDATES:
        row = None
        for item in (verdicts or []):
            if isinstance(item, tuple) and len(item) == 5 and item[0] == name:
                row = item
                break
        picked, passed, counter = (row[2], row[3], row[4]) if row is not None else (0, False, None)
        lengths.append(str(picked))
        show_line('实现 ' + name + '（' + how + '）选出', str(picked) + ' 个: ' + str(counter))
        show_line('实现 ' + name + ' 通过吗', passed)
        show_line('实现 ' + name + ' 反例', '' if counter is None else str(counter))
    show_line('暴力验证给出的最优', str(want) + ' 个')
    show_line('两个实现选出的个数', ' '.join(lengths))

    show_banner('0027 结论行')
    ok_count = sum(1 for item in (verdicts or [])
                   if isinstance(item, tuple) and len(item) == 5 and item[3])
    show_line('实现数', len(lengths))
    show_line('通过的实现数', ok_count)
    show_line('这条链没验证出东西', nothing_passed(verdicts))

    show_banner('0027 第六种形态：解析坏了也要给结论')
    bad = as_result(resolve('{"family": "二分答案", "why": "题目说"最小化最大值""}'))
    show_line('解析坏掉时的 ok', bad.get('ok', '（还没接上）'))
    show_line('解析坏掉时的 reason', bad.get('reason', '（还没接上）'))

    show_banner('0027 关键词表怎么交叉检查模型')
    top = classify(problem)
    top = top if isinstance(top, list) else []
    show_line('题面首选', top[0][1] if top else '（一个都没命中）')
    show_line('模型推荐', rec.get('family') if rec.get('ok') else '（解析失败）')
    show_line('首选与模型一致', bool(top) and top[0][1] == rec.get('family'))
