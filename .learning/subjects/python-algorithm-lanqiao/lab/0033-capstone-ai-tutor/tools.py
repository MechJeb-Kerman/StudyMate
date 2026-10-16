"""tools.py · lab 0033 的公共工具（给好的，别改）

这一课要把五段拼成一条流水线：题目文本 → 提取题意 → 推荐算法 → 写解法 → 验证 → 出记录。
五个任务各自只管一段，但有几样东西**五段必须用同一个口径**，所以放在这里给好，别自己另写一份：

  1. TypeSpec / check_contract / contract_error
     契约检查的唯一口径。**每两段之间都要跑一次 check_contract**，位置是任务 5 的流水线。
     检查器要能说清是**哪一段的哪个字段**不对——这是差之毫厘的地方：
     passed 变成字符串 'False' 时不会抛任何异常，报告却会写「验证 通过」。

  2. ParseFailure / parse_json
     模型返回的是一段**文本**，不是结构化数据。三档解析器：裸 json.loads → 剥 Markdown
     围栏 → 提取首个括号平衡的 {...}。三档都吃不下的那一种（被截断）不是格式问题，
     是**内容不完整**——它只能靠「让模型少说点」与**重试**去救。
     失败一律交回 ParseFailure.reason（一段说明），不把 json 的异常抛给调用者。

  3. FENCE / make_fence() / fence_text()
     反引号围栏是三个反引号连在一起。**本 lab 的源码里不许出现连续三个反引号**
     （会打断阅卷工具链），所以统一用 make_fence() 造：它就是 '`' * 3。

  4. 四份预置输出 CLEAN / FENCED / PREFACED / TRUNCATED 与 pick_preset()
     判分与假模型共用这四份。**它们就是模型那四种真实输出**，别改一个字：
     判分逐条比对的期望值全部来自这里。

  5. 一份确定性的题目、样例与执行器 CANON_TEXT / CANON_CASES / canon_exec()
     第四段「自动验证」跑的就是这一份，期望值全部由 canon_exec 现算，没有一个是写死的。

判分不 replace 这份文件里的任何东西来「帮你过」：它做的是**另算一遍**——
拿自己的样本重新算期望值，再跟你的产物对上。所以「只写 print、不写实现」是过不去的。
"""

import copy
import re

# ── 0. TODO 名字（判分与脚本共用：每条 FAIL 后面都要点明是哪一段）──────────

TODO_NAMES = {
    1: 'contracts.py TODO 1（CONTRACTS 那张表）',
    2: 'contracts.py TODO 2（check_contract 检查器）',
    3: 'parse.py TODO 3（parse_json 三档解析）',
    4: 'parse.py TODO 4（parse_strip_fence 剥围栏）',
    5: 'parse.py TODO 5（parse_extract 提取首个括号平衡的对象）',
    6: 'pipeline.py TODO 6（extract_intent 第一段）',
    7: 'pipeline.py TODO 7（recommend 第二段）',
    8: 'pipeline.py TODO 8（run_cases 第四段）',
    9: 'pipeline.py TODO 9（make_record 第五段）',
    10: 'pipeline.py TODO 10（run_pipeline 把五段串起来）',
}

TODO_MARK = '  → 这一条指 '


def todo_mark(number):
    """一条 FAIL 的尾巴：『  → 这一条指 …TODO n（…）』。"""
    return TODO_MARK + TODO_NAMES[number]


# ── 1. 契约检查 ─────────────────────────────────────────────────────────

INT = ('int',)
STR = ('str',)
BOOL = ('bool',)
LIST_STR = ('list[str]',)
TEXT = ('str',)          # 一段文本：题目原文、解法源码、一段说明都是它


class TypeSpec:
    """一份契约：{'字段名': 检查这个值的函数}。

    每个检查函数交回 **错误说明的列表**：空表 = 这一格合法；非空 = 每一句说清哪里不对。
    这样判分能精确到**字段级**地说出「字段 passed 应为 bool，实际是 str」，
    而不是一句笼统的「形状不对」。
    """

    def __init__(self, name, checks):
        self.name = name
        self.checks = dict(checks)

    def fields(self):
        """这份契约要求哪些字段（顺序就是 checks 的顺序）。"""
        return list(self.checks)

    def check(self, obj):
        """查一个值 → {字段名: 错误说明表}；一个字段一个键，全对就是空字典。"""
        if not isinstance(obj, dict):
            return {'(整体)': ['应该是 dict，实际是 ' + type(obj).__name__]}
        bad = {}
        for name, fn in self.checks.items():
            if name not in obj:
                bad[name] = ['缺字段 ' + name]
                continue
            wrong = fn(obj[name])
            if wrong:
                bad[name] = list(wrong)
        return bad

    def describe(self):
        """一句话说清这份契约：字段名与类型，用来印在那张表上。"""
        return '、'.join(self.fields())


def is_str(value):
    return [] if isinstance(value, str) else ['应为 str，实际是 ' + type(value).__name__]


def is_text(value):
    """一段非空文本（题目原文、源码、说明都走它）。"""
    if not isinstance(value, str):
        return ['应为 str，实际是 ' + type(value).__name__]
    if not value.strip():
        return ['是一段空文本']
    return []


def is_int(value):
    """真的是 int——bool 不算（isinstance(True, int) 在 Python 里是 True，这里要挡住）。"""
    if isinstance(value, bool) or not isinstance(value, int):
        return ['应为 int，实际是 ' + type(value).__name__]
    return []


def is_bool(value):
    """真的是 bool 本身——1 / 0 / 'True' / 'False' 都不算。"""
    if not isinstance(value, bool):
        return ['应为 bool，实际是 ' + type(value).__name__]
    return []


def is_list(value):
    return [] if isinstance(value, list) else ['应为 list，实际是 ' + type(value).__name__]


def is_list_str(value):
    """一串字符串：每个元素都要是 str。"""
    if not isinstance(value, list):
        return ['应为 list[str]，实际是 ' + type(value).__name__]
    wrong = [i for i, item in enumerate(value) if not isinstance(item, str)]
    if wrong:
        return ['list[str] 的第 ' + str(wrong[0]) + ' 个元素是 '
                + type(value[wrong[0]]).__name__ + '，不是 str']
    return []


def is_cases(value):
    """若干组测试数据：每组是 (输入, 期望输出) 两个字符串——存的是**数据本身**。"""
    if not isinstance(value, list):
        return ['应为 list，实际是 ' + type(value).__name__]
    for i, row in enumerate(value):
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            return ['第 ' + str(i) + ' 组不是 (输入, 期望输出) 两样']
        if not all(isinstance(item, str) for item in row):
            return ['第 ' + str(i) + ' 组里有不是 str 的元素——留证要留字符串']
    return []


def is_dict_str_int(value):
    """约束那一格：{n_max: int, value_max: int}。"""
    if not isinstance(value, dict):
        return ['应为 dict，实际是 ' + type(value).__name__]
    bad = []
    for key in ('n_max', 'value_max'):
        if key not in value:
            bad.append('里缺字段 ' + key)
        elif isinstance(value[key], bool) or not isinstance(value[key], int):
            bad.append('里的字段 ' + key + ' 应为 int，实际是 '
                       + type(value[key]).__name__)
    return bad


def contract_error(spec, obj):
    """跑一次契约检查 → 一句说清**哪一段的哪个字段**不对的说明；全对时交回空串。

    这就是「在边界就点名」的那句话。它必须同时说清三件事：
    是哪一段（spec.name）、是哪个字段、那个字段应该是什么类型。
    """
    bad = spec.check(obj)
    if not bad:
        return ''
    parts = []
    for name, notes in bad.items():
        parts.append(('整份 ' if name == '(整体)' else '字段 ' + name + ' ') + '；'.join(notes))
    return spec.name + ': ' + '，'.join(parts)


def check_contract(spec, obj):
    """契约不对就**抛 TypeError**，并说清是哪个字段；对了就原样交回 obj。

    为什么抛而不是交回一个布尔：下游拿到的是「这一段能不能用」这个结论，
    一个 False 很容易被顺手 `if not x` 吃掉、然后接着往下算。
    抛出来是为了让错误停在**它发生的那一段**，而不是五层之外。
    """
    note = contract_error(spec, obj)
    if note:
        raise TypeError(note)
    return obj


# ── 2. 三档解析器 ───────────────────────────────────────────────────────

class ParseFailure(Exception):
    """解析失败——**它带着一段说明**，不是把 json 的异常原样抛出去。

    reason 是给人看的：说清「找不到 {」还是「括号不闭合」。后者才是被截断的样子。
    """

    def __init__(self, reason, raw=''):
        super().__init__(reason)
        self.reason = reason
        self.raw = raw


# 判定「被截断」的那句话：找得到 { 却找不到配对的 }。三段解析失败说明都带它。
TRUNCATED_NOTE = '括号不闭合（找得到 { 却找不到配对的 }）——这是**被截断**，不是格式问题'


def _raw_load(text):
    """最里面那一层：一次 json.loads，不成功就抛 ParseFailure。"""
    import json
    try:
        return json.loads(text)
    except Exception as exc:
        raise ParseFailure(type(exc).__name__ + ': ' + str(exc), text)


def _balanced_span(text):
    """从第一个 { 起找**第一个括号平衡**的 {...} → (起点, 终点)；找不到就抛。"""
    start = text.find('{')
    if start < 0:
        raise ParseFailure('没找到 {', text)
    depth = 0
    in_str = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return start, i + 1
    raise ParseFailure(TRUNCATED_NOTE, text)


def _strip_fence(text):
    """剥掉最外面那一层 Markdown 围栏（连 'json' 那个语言标记一起剥）。"""
    mark = make_fence()
    s = text.strip()
    if not s.startswith(mark):
        return s
    s = s[len(mark):]
    head, _, rest = s.partition('\n')
    if head.strip() == 'json':
        s = rest
    else:
        s = head + '\n' + rest if rest else head
    end = s.rfind(mark)
    if end >= 0:
        s = s[:end]
    return s.strip()


def parse_json(raw):
    """**三档解析**：裸 json.loads → 剥围栏 → 提取首个括号平衡的 {...}。

    成功交回解析出来的值（第 1 段要求它是个 dict，由契约去管）；
    三档都吃不下的（被截断）**抛 ParseFailure**，reason 里带着「被截断」这句判据。
    它不抛 json 的异常、也不交回 None——失败也要是一种说得清的值。
    """
    if not isinstance(raw, str):
        raise ParseFailure('解析器的输入应该是 str，实际是 ' + type(raw).__name__, raw)
    attempts = (
        lambda text: _raw_load(text.strip()),
        lambda text: _raw_load(_strip_fence(text)),
        lambda text: _raw_load(text[_balanced_span(text)[0]:_balanced_span(text)[1]]),
    )
    first = None
    for attempt in attempts:
        try:
            return attempt(raw)
        except ParseFailure as exc:
            # 「括号不闭合」这一句比「Expecting property name …」有信息量得多：
            # 它把「格式不对」与「内容被截断」分开——后者要走的不是解析器，是重试。
            if TRUNCATED_NOTE in exc.reason:
                raise ParseFailure(exc.reason, raw)
            if first is None:
                first = exc.reason
    raise ParseFailure(first, raw)


# ── 3. 围栏 ─────────────────────────────────────────────────────────────

def make_fence():
    """三个反引号连在一起（课件里写那三个反引号的地方）。"""
    return '`' * 3


FENCE = make_fence()


def fence_text(lang, body):
    """把一段文本包进围栏里，做成模型那种「带围栏」的输出。"""
    mark = make_fence()
    return mark + lang + '\n' + body + '\n' + mark


def fence_line_count(text):
    """这段文本里有几行是围栏行（一行开头就是三个反引号）。"""
    return sum(1 for line in str(text).splitlines() if line.startswith(FENCE))


# ── 4. 四份预置输出（假模型交回的就是这四份）────────────────────────────

CLEAN = ('{"title": "拨钟问题", "constraints": {"n_max": 9, "value_max": 27}, '
         '"ask": "求把所有钟拨到 12 点的最少按键次数"}')
FENCED = fence_text('json', CLEAN)
PREFACED = ('好的，我先把题意理一遍：这道题问的是最少按几下。\n\n' + CLEAN
            + '\n\n希望这个理解对你有帮助。')
# 被截断：一段**开头对、结尾断在半截**的文本。括号根本没闭合，任何解析器都救不回来。
TRUNCATED = CLEAN[:64]

PRESETS = {
    '干净 JSON': CLEAN,
    '带围栏': FENCED,
    '带前言': PREFACED,
    '被截断': TRUNCATED,
}

# 模型建议的算法族——第二段的预置推荐就是从这段文本里解析出来的。
MODEL_ADVICE = ('{"candidates": ["图的搜索"], "reasons": ["求最少按键次数，是网格上的'
                '最短步数", "状态可以编码成一个整数", "复杂度能压到 O(4^n·n)"], '
                '"picked": "图的搜索"}')


def pick_preset(prompt, retry=False):
    """按**提示词的内容**挑一份预置输出：这就是假模型的全部逻辑。

    四条规则，顺序不能换（换一个字，重试那一条路就永远走不到）：

      1. retry=True → 干净的那一份。**重试必须有机会成功**，不然「重试」这件事没法收尾；
      2. 提示词里出现「截断」→ 第一次就给**被截断**的那一份。
         所以第一段的第一次提示词里**不能**带这两个字，重试那一句必须带；
      3. 提示词里提到「候选」（第二段问的是候选算法族）→ 给那份推荐；
      4. 出现「围栏」「前言」这些词 → 给对应的一份（用来试另外两档解析）；
      5. 都不沾边 → 题意那一份。
    """
    text = prompt if isinstance(prompt, str) else str(prompt)
    lowered = text.lower()
    if retry:
        return CLEAN
    if '截断' in lowered or 'truncat' in lowered:
        return TRUNCATED
    if '候选' in lowered or 'candidates' in lowered:
        return MODEL_ADVICE
    if '围栏' in lowered or 'fence' in lowered:
        return FENCED
    if '前言' in lowered or '开头' in lowered or 'preface' in lowered:
        return PREFACED
    return CLEAN


def is_truncated_preset(raw):
    """这一段文本是不是「被截断」那一份：**是从头开始的那 64 个字符**，而且括号不闭合。

    不是靠长度比出来的：判分比对的是「与预置输出逐字相同的开头」+「缺一对括号」。
    """
    if not isinstance(raw, str):
        return False
    if raw == TRUNCATED:
        return True
    if not TRUNCATED.startswith(raw):
        return False
    return raw.count('{') != raw.count('}')


def same_value(a, b):
    """两个值是不是同一个东西——**JSON 往返会把 tuple 变成 list**，所以先归一化再比。"""
    return normalize_value(a) == normalize_value(b)


def normalize_value(value):
    """把值归一成「能与 JSON 往返之后相比」的形状：tuple → list，dict 逐键往下走。"""
    if isinstance(value, dict):
        return {k: normalize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_value(v) for v in value]
    return value


# ── 5. 一份确定性的题目、样例与执行器（第四段跑的就是这一份）────────────

CANON_TEXT = ('【拨钟问题】有 9 个钟，排成 3×3。每个钟的指针只可能指向 12、3、6、9 点，'
              '分别记作 0、1、2、3。9 个按钮各拨动一组钟，每按一次，那一组钟都前进 3 小时'
              '（3 变成 6，9 变成 12）。同一个按钮按 4 次回到原样，所以每个按钮最多按 3 次。'
              '给定 9 个钟的初始状态，求把所有钟都拨到 12 点的最少按键次数。'
              '如果拨不到，输出 impossible。输入 3 行，每行 3 个整数。')

# 题目里那 9 个按钮各拨动哪几个钟（经典拨钟问题的那张表）。
BUTTONS = [
    (0, 1, 3, 4),
    (0, 1, 2),
    (1, 2, 4, 5),
    (0, 3, 6),
    (1, 3, 4, 5, 7),
    (2, 5, 8),
    (3, 4, 6, 7),
    (6, 7, 8),
    (4, 5, 7, 8),
]

# 四组样例：每一组都是 (输入文本, 期望输出文本)。期望值是 canon_exec **现算**出来的，
# 不是写死的——判分也是拿它当期望值，所以两边永远对得上。
CANON_CASES = [
    ('0 0 0\n0 0 0\n0 0 0\n', '0'),
    ('0 0 1\n0 0 1\n0 0 1\n', '1'),
    ('0 1 2\n3 0 1\n2 3 0\n', '8'),
    ('1 2 3\n0 1 2\n3 0 1\n', '13'),
]
# 第五组是**故意对不上**的：期望值写的是 4，而真值是 18。
# 它的用途是让「不合格时的第一个反例」这一格有东西可写——
# 记录里说「5 组里过了 4 组、第 4 组反例是 …」比一个光秃秃的「通过」有信息量得多。
CANON_FAILING = ('2 1 0\n3 2 1\n0 3 2\n', '4')


def _states(text):
    """把一段输入解析成 9 个钟的状态（0/1/2/3）→ 一个长度 9 的 list。"""
    numbers = [int(x) for x in re.findall(r'-?\d+', text)]
    if len(numbers) != 9:
        raise ValueError('输入要有 9 个整数，实际读到 ' + str(len(numbers)) + ' 个')
    return numbers


def _button_presses():
    """枚举每个按钮按 0..3 次的所有组合（4^9 = 262144 种），交回 {状态: 最少按键次数}。

    为什么这就够了：状态空间只有 4^9 个，把每个组合的结果算出来再取最小，
    得到的就是**真值**——这一课要的是确定值，不是「大概对」。
    """
    import itertools
    best = {}
    for combo in itertools.product(range(4), repeat=len(BUTTONS)):
        state = [0] * 9
        total = 0
        for index, times in enumerate(combo):
            total += times
            if times:
                for clock in BUTTONS[index]:
                    state[clock] = (state[clock] + times) % 4
        key = tuple(state)
        if total < best.get(key, 99):
            best[key] = total
    return best


def canon_exec(text):
    """这一课的**唯一执行器**：输入文本进、输出文本出。期望值全部由它现算。

    找得到就交回最少按键次数，找不到就交回 'impossible'——
    不可能这件事要有一个**说得出的输出**，不能交回 None 让上游去猜。
    """
    state = tuple(value % 4 for value in _states(text))
    total = _button_presses().get(state)
    return 'impossible' if total is None else str(total)


def canon_cases():
    """四组样例 + 一组**故意对不上**的数据（留着看「第一个反例」长什么样）。"""
    return copy.deepcopy(CANON_CASES + [CANON_FAILING])


def canon_seed():
    """留证那一格要的种子：这一课的数据是确定性的，种子只是一个方便重跑的手段。"""
    return 20260301


# ── 6. 打印统一走这里 ───────────────────────────────────────────────────

def show_banner(title):
    """打印一行小节标题，五个任务的脚本都用它开头。"""
    print('== ' + title + ' ==')


def show_line(label, value):
    """打印一行「标签 值」，判分按标签取（顺序也按行读，所以别改这些行）。"""
    print('  ' + label + ': ' + str(value))


def clamp(text, limit=72):
    """太长就截断（超出部分写成 …），打印时用。"""
    text = '' if text is None else str(text)
    return text if len(text) <= limit else text[:limit] + '…'
