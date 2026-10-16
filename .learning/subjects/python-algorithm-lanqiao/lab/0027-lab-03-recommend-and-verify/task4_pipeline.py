"""任务 4 · 端到端：题面进，候选实现 + 验证结论出（lab 0027）

前面三段给出的是**候选**。最后这一段决定要不要信它。

拿「区间调度」当例子：推荐给出「贪心」，然后写两个实现——**都叫贪心，只是排序关键字不同**：

    实现 A  按开始时间排（tools.greedy_by_start）——很自然，但在区间调度上错；
    实现 B  按结束时间排（tools.greedy_by_end）——对。

课件那一组数据（tools.case_intervals(6)）上：A 选出 1 个，B 选出 6 个，暴力最优 6 个。

    实现 A（按开始时间排）选出 1 个: [(0, 60)]
    实现 B（按结束时间排）选出 6 个: [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12)]
    暴力验证给出的最优: 6 个
    A 通过吗: False    B 通过吗: True

**推荐给出的名字是对的，两个实现却一个好一个坏。** 所以验证环节要验的是**具体实现**，
不是算法名——名字下面可以挂无数种写法，其中大部分是错的。

整条链的结论也不该是「推荐用贪心」，而该是「推荐贪心 → A 被否掉（附反例）→ B 通过」。
有反例的否掉，比没有反例的通过更有价值：前者告诉你这条路走不通，而且给了你能复现的证据。

判分在这一层做四件事，都是**另算一遍**：
  · 拿它自己的样本调你的 run_trial，看结论是不是真的从计算里出来的；
  · 换一组数据（区间数不是 6），看你的结论跟着数据变——把「A 1 个 / B 6 个」写死的会被抓住；
  · 把「两个实现都过」的情形交给你的 nothing_passed，看它认不认得出「这条链没验证出东西」；
  · 用带**没转义的引号**的假模型跑一遍，看你的 resolve 交回的是失败结论，还是不声不响地当成通过。

接口：文件名、函数名、CANDIDATES 那张名单、带 print 的行都是判分接口，别改；
要写的是三个 TODO。

跑： py task4_pipeline.py
判： py run_tests.py
"""

import json

from task1_prompt import build_prompt, fake_model
from task3_classify import classify
from tools import (PROBLEMS, brute_best, candidate_impl, case_intervals, clamp,
                   show_banner, show_line)

# 两个候选实现的名单：名字（判分按它取结论，别改名）+ 「怎么排的」那一格的叫法。
# 函数用 tools.candidate_impl(名字) 取，别自己另写一份排序——判分核的就是这两个。
CANDIDATES = [
    ('A', '按开始时间排'),
    ('B', '按结束时间排'),
]


# ══ TODO 1 ═════════════════════════════════════════════════
# resolve(raw)：把模型返回的那段**文本**变成本课能用的推荐结论，交回一个字典。
#
# 三种结局，三种形状（这里是判分接口，键名别改）：
#
#   解析成功 → {'ok': True, 'family': 族名, 'confidence': 置信度, 'why': 理由}
#   文本坏掉 → {'ok': False, 'reason': '<异常类名>'}        ← 第六种形态走这一支
#   解析出来不是字典 → {'ok': False, 'reason': '不是字典'}
#
# 要点：
#   · 用 json.loads 直接吃这段文本（这一段是**带噪声的文本**，不是已经解析好的字典——
#     真模型返回的就是一段文本，哪怕提示词里写了「不要围栏」）；
#   · 抛异常不许跑出去：用 try / except Exception 接住，reason 写 '<' + 异常类名 + '>'。
#     第六种形态（引号没转义）落到的就是这一支，它必须交回**一个结论**，
#     而不是抛出来把整条链打断；
#   · 解析成功但不是字典（比如模型返回了一个数组）→ reason 写 '不是字典'；
#   · family / confidence / why 三个键都取出来放进结论里；缺一个也算「不是字典」那一支。
def resolve(raw):
    return None


# ══ TODO 2 ═════════════════════════════════════════════════
# run_trial(family, intervals)：对同一个算法族下的每个候选实现各跑一遍，跟暴力比。
#
# 交回 (verdicts, want) 两样：
#
#   verdicts = [ (名字, '怎么排的', 选出的个数, 通过吗(True/False), 选出那张表), ... ]
#   want     = 暴力最优的个数
#
# 第五格那张表是什么：**每一个**实现都把它实际选出来的那些区间交回来。
# 没通过的那一个，这张表就是**复现得了的反例**；通过的那一个也交，
# 判分用它核对「选出 1 个」这个数不是写死的。
# 「选出 1 个、最优 6 个」这种结论没有证据价值，带着那张表才有。
#
# 要点：
#   · want = brute_best(intervals)（暴力是尺子，先让它算）；
#   · 对 CANDIDATES 里每一对 (名字, 怎么排的)：函数用 tools.candidate_impl(名字) 取，
#     picked = list(那个函数(intervals))，选出个数 = len(picked)，
#     通过当且仅当 选出个数 == want，第五格就交 picked 那张表；
#   · 交回的表里顺序就是 CANDIDATES 的顺序，**两个实现都跑**，
#     不能谁先通过就短路——这一层要看的正是「同族两个实现结论不同」。
#   · 通过与否要交回**真布尔值**。
#   · 形状必须是 **(结论表, want) 两样**：只交回结论表的话，调用处解包会崩。
def run_trial(family, intervals):
    return ([], 0)


# ══ TODO 3 ═════════════════════════════════════════════════
# nothing_passed(verdicts)：这条链有没有验证出可用结论？
#
#   · 一个都没通过 → 交回 True（要用 not any(...)，不是 not all(...)——
#     写成 not all 的话「全过」和「全不过」都会交回 True）；
#   · 有任何一个通过 → 交回 False；
#   · 空表 → 交回 True（什么都没跑，等于什么都没验出来）；
#   · 交回**真布尔值**（True / False 本身），别交回 1 / 0 / 字符串。
def nothing_passed(verdicts):
    return None


def as_result(value):
    """把 resolve 交回的东西归成能取键的字典；交回别的（None / 字符串）就归成空字典。

    这是**给好的**：TODO 1 还没写时脚本照样能跑完、把所有判分行打出来，
    打印出来的那一格会是「（还没接上）」。
    """
    return value if isinstance(value, dict) else {}


if __name__ == '__main__':                      # 别改：判分读的就是下面这几行
    CASE = case_intervals(6)                    # 别改：课件那一组数据

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
    # 每一行都从 verdicts 里**查**出来，查不到就打占位值——这样留白版也打印得出全部判分行，
    # 而每一行的数字都来自 run_trial 交回的那张表。
    for name, how in CANDIDATES:
        row = None
        for item in (verdicts or []):
            if isinstance(item, tuple) and len(item) == 5 and item[0] == name:
                row = item
                break
        picked, passed, counter = (row[2], row[3], row[4]) if row is not None else (0, False, None)
        lengths.append(str(picked))
        show_line('实现 ' + name + '（' + how + '）选出',
                  str(picked) + ' 个: ' + str(counter))     # 别改：判分逐字读
        show_line('实现 ' + name + ' 通过吗', passed)         # 别改
        show_line('实现 ' + name + ' 反例', '' if counter is None else str(counter))   # 别改
    show_line('暴力验证给出的最优', str(want) + ' 个')         # 别改：期望 6 个
    show_line('两个实现选出的个数', ' '.join(lengths))         # 别改：期望 1 6

    show_banner('0027 结论行')
    ok_count = sum(1 for item in (verdicts or [])
                   if isinstance(item, tuple) and len(item) == 5 and item[3])
    show_line('实现数', len(lengths))                          # 别改：期望 2
    show_line('通过的实现数', ok_count)                        # 别改：期望 1
    show_line('这条链没验证出东西', nothing_passed(verdicts))   # 别改：期望 False

    show_banner('0027 第六种形态：解析坏了也要给结论')
    bad = as_result(resolve('{"family": "二分答案", "why": "题目说"最小化最大值""}'))
    show_line('解析坏掉时的 ok', bad.get('ok', '（还没接上）'))      # 别改：期望 False
    show_line('解析坏掉时的 reason', bad.get('reason', '（还没接上）'))  # 别改：期望 <JSONDecodeError>

    show_banner('0027 关键词表怎么交叉检查模型')
    top = classify(problem)
    top = top if isinstance(top, list) else []
    show_line('题面首选', top[0][1] if top else '（一个都没命中）')
    show_line('模型推荐', rec.get('family') if rec.get('ok') else '（解析失败）')
    show_line('首选与模型一致', bool(top) and top[0][1] == rec.get('family'))   # 别改：期望 True
