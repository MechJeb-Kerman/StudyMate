"""tools.py · lab 0027 的公共工具（给好的，别改）

这一课要把三段拼成一条链：提示词 → 解析 → 关键词打分 → 验证。四个任务各自只管一段，
但有几样东西**四段必须用同一个口径**，所以放在这里给好，别自己另写一份：

  1. FENCE / make_fence()
     反引号围栏是三个反引号连在一起。**这个 lab 的源码里不许出现连续三个反引号**
     （会打断阅卷工具链），所以统一用 make_fence() 造：它就是 '`' * 3。
     课件里出现 `` `{3} `` 的地方，在这里一律写成 re 的 {3} 量词。

  2. trim(text) / clamp(text, n)
     归一与截断。要打印一段文本时先过 trim（去掉首尾空白），太长时过 clamp
     （沿用课件那种「超出部分写成 …」的口径）。

  3. safe_load(text)
     一次 json.loads，失败交回异常对象（不抛出来）。两个解析器都靠它。

  4. ESCAPE_TRAP
     课件第六种形态样本的**归一文本**：字符串里的引号没有转义，
     `题目说"最小化最大值"` 那一处在 JSON 里就是语法错误。两个括号是配平的，
     所以任何「找大括号」的招数都救不了它——它只能由提示词与接口参数去修。

  5. FAMILIES / canonical_scores(text) / canonical_classify(text)
     八张算法族关键词表与它们打分的**唯一口径**。
     任务 3 的表必须与 FAMILIES 逐字一致——判分拿两边分别打分再对照，
     表改窄了「合并果子」那一行的并列背包就没了，那是把现象藏起来。
     canonical_classify 交回 [(命中数, 族名, 命中词表)]，已按 (-命中数, 族名) 排好。

  6. 六个样例题面 PROBLEMS 与 case_intervals / greedy_by_start / greedy_by_end /
     brute_intervals / brute_best
     任务 3 打分要用的六道题面，以及任务 4 的验证段要用的那套对拍：
     造数据的样本、两个候选实现、暴力最优。

判分不 replace 这份文件里的任何东西来「帮你过」：它做的是**另算一遍**——
拿自己的样本重新算期望值，再跟你的脚本打印出来的行对上。所以只写 print、
不写实现是过不去的：打印行由你，期望值由判分自己算。
"""

import json
import re


# ── 1. 围栏 ──────────────────────────────────────────────────────────────

def make_fence():
    """三个反引号连在一起（课件里写 `` `{3} `` 的那串东西）。"""
    return '`' * 3


FENCE = make_fence()


# ── 2. 归一与截断 ────────────────────────────────────────────────────────

def trim(text):
    """去掉首尾空白。判分对提示词、对解析器的输入都先过这一道。"""
    return text.strip()


def clamp(text, limit=48):
    """太长就截断（沿用课件那种「超出部分写成 …」的口径）。"""
    text = '' if text is None else str(text)
    return text if len(text) <= limit else text[:limit] + '…'


# ── 3. 安全解析 ──────────────────────────────────────────────────────────

def safe_load(text):
    """跑一次 json.loads，交回 (值, 异常对象)。失败时值是 None、异常对象不是 None。"""
    try:
        return json.loads(text), None
    except Exception as exc:
        return None, exc


# ── 4. 第六种形态样本 ────────────────────────────────────────────────────

# 课件第六种：`题目说"最小化最大值"` 里的那对引号**没有转义**（下面字符串里那两处引号是
# 原样的中文引号内嵌，源码看上去像 Python 的引号错误，其实那正是这一段要示意的坏内容）。
ESCAPE_TRAP = '{"family": "二分答案", "why": "题目说"最小化最大值""}'

# 任务 2 要用的六种形态样本，键就是课件那一节的六行名字。
def sample_texts():
    """交回课件那六种形态样本：{名字: 原文}。顺序就是课件打印的顺序。"""
    return {
        '干净 JSON': '{"family": "二分答案", "confidence": "高"}',
        '套了 json 围栏': (FENCE + 'json\n{"family": "二分答案", "confidence": "高"}\n'
                           + FENCE),
        '围栏 + 前面一段话': ('根据题意，答案具有单调性。\n\n' + FENCE + 'json\n'
                             '{"family": "二分答案", "confidence": "高"}\n' + FENCE),
        '围栏 + 后面一段话': (FENCE + 'json\n{"family": "二分答案", "confidence": "高"}\n'
                             + FENCE + '\n\n希望有帮助，有疑问可以继续追问。'),
        '没有围栏，但有前后解释': ('这道题我建议用二分答案。\n'
                                  '{"family": "二分答案", "confidence": "高"}\n'
                                  '理由如上。'),
        '内容本身不是合法 JSON': ESCAPE_TRAP,
    }


# ── 5. 八张关键词表与打分口径 ────────────────────────────────────────────

FAMILIES = [
    ('二分答案', ['最大化', '最小化', '最小值的最大', '最大值的最小', '单调',
                  '猜一个', '判定一个值行不行', '最长', '最短']),
    ('并查集', ['连通块', '属于同一组', '合并集合', '是否连通', '朋友的朋友']),
    ('堆', ['前 k 大', '前 k 小', '第 k 大', '中位数', '每次取最小', '每次取最大']),
    ('图的搜索', ['最短步数', '最少几步', '网格', '迷宫', '走法', '扩散', '可达']),
    ('背包', ['容量', '重量', '价值', '装下', '每件最多选一次', '选与不选']),
    ('贪心', ['区间', '不相交', '最多能选几个活动', '按结束时间']),
    ('前缀和', ['区间和', '连续子数组的和', '多次询问', '子矩阵']),
    ('双指针', ['有序数组', '两数之和', '左右两个指针', '原地去重']),
]


def canonical_scores(text):
    """按 FAMILIES 给每个族打分，交回 [(命中数, 族名, 命中词表)]，**没命中的族不在里面**。"""
    scores = []
    for family, keys in FAMILIES:
        hit = [k for k in keys if k in text]
        if hit:
            scores.append((len(hit), family, hit))
    return scores


def canonical_classify(text):
    """打分 + 排序，交回 [(命中数, 族名, 命中词表)]：先按命中数降序，再按族名字典序升序。"""
    return sorted(canonical_scores(text), key=lambda row: (-row[0], row[1]))


# ── 6. 六道样例题面 ──────────────────────────────────────────────────────

PROBLEMS = {
    '木材加工': '有 n 根木头，要切成 k 段等长的小段。求每小段最长的长度，即让最小长度最大化。',
    '岛屿数量': '一个由 0 和 1 组成的网格，1 表示陆地。求有多少个连通块。',
    '合并果子': '每次把两堆合并，代价是重量之和。求最小总代价，每次取最小的两堆。',
    '区间调度': '给出若干个区间，选出最多几个互不相交的区间，按结束时间排。',
    '第 k 大': '在一个数据流里随时回答第 k 大是多少。',
    '跳石头': '一条河里有若干块石头，最多移走 M 块，求最短跳跃距离的最大值。',
}


# ── 7. 验证段要用的那套对拍 ──────────────────────────────────────────────

def case_intervals(n):
    """造一组能分开两个贪心实现的数据：(0, n*10) 那一大段，加上 1..n 每隔一格一段。

    课件用的是 n = 6 那一组。按开始时间排的实现会先吃掉 (0, n*10)，
    从此每个小区间都塞不进去；按结束时间排的那一版能把 n 个小区间全收了。
    """
    return [(0, n * 10)] + [(2 * i + 1, 2 * i + 2) for i in range(n)]


def greedy_by_start(intervals):
    """按开始时间排的贪心——很自然，但在区间调度上错。"""
    picked = []
    last_end = -1
    for s, e in sorted(intervals):
        if s >= last_end:
            picked.append((s, e))
            last_end = e
    return picked


def greedy_by_end(intervals):
    """按结束时间排的贪心——对。"""
    picked = []
    last_end = -1
    for s, e in sorted(intervals, key=lambda pair: pair[1]):
        if s >= last_end:
            picked.append((s, e))
            last_end = e
    return picked


def brute_intervals(intervals):
    """枚举所有子集，找两两不相交的最大个数。慢，但当尺子用。"""
    best = 0
    n = len(intervals)
    for mask in range(1 << n):
        chosen = sorted(intervals[i] for i in range(n) if mask >> i & 1)
        if all(chosen[i][1] <= chosen[i + 1][0] for i in range(len(chosen) - 1)):
            best = max(best, len(chosen))
    return best


def brute_best(intervals):
    """暴力最优的个数（brute_intervals 的值那一半，单列一个名字给判分用）。"""
    return brute_intervals(intervals)


# 两个候选实现的名单：名字 → 函数。任务 4 的 CANDIDATES 用的就是这两个名字。
def candidate_name(family):
    """这个算法族下有几个可执行实现。这一课只有「贪心」这一族有。"""
    if family == '贪心':
        return ['A', 'B']
    return []


def candidate_impl(name):
    """按名字取候选实现：'A' 是按开始时间排的那一版，'B' 是按结束时间排的那一版。"""
    if name == 'A':
        return greedy_by_start
    if name == 'B':
        return greedy_by_end
    return None


def candidate_how(name):
    """按名字取「怎么排的」那一格叫法：'A' → 按开始时间排，'B' → 按结束时间排。"""
    if name == 'A':
        return '按开始时间排'
    if name == 'B':
        return '按结束时间排'
    return ''


def canonical_trial(intervals):
    """验证段的**唯一口径**：交回 [(名字, 选出个数, 通过吗, 选出那张表)], 暴力最优个数。

    判分拿它当期望值——它就是「另算一遍」的那一遍。它与任务 4 的 run_trial
    必须给出同一个结论；不一样就说明你的验证段跟数据对不上（或者数字是写死的）。
    第四格一律是**那个实现实际选出来的表**（通过的那一个也交）：
    没通过时它是反例，通过时判分用它核对「选出几个」不是写死的。
    """
    want = brute_best(intervals)
    rows = []
    for name in candidate_name('贪心'):
        picked = list(candidate_impl(name)(intervals))
        passed = len(picked) == want
        rows.append((name, len(picked), passed, picked))
    return rows, want


# ── 8. 判分与脚本共用的两套期望值 ────────────────────────────────────────
#
# 下面这些是「另算一遍」的那一遍：run_tests.py 用它算期望值，任务脚本用它打印判分要读的行。
# 两边**共用同一份口径**，所以脚本打印出来的东西与判分算出来的东西永远可以对上；
# 对不上就一定是实现里的问题，不是口径问题。

# task1：提示词里的四样约束各要认得出来的锚点（都是**小写之后**再比对）。
# 说明：约束 2（不许有别的文字）在这四句里同时被「只输出…不要…」认下来；
# 「不要用代码块围栏」不单独作为一条判据——本 lab 的源码里不许出现连续三个反引号。
PROMPT_REQUIRED = [
    ('(1) 输出格式', ['格式固定']),
    ('(2) 不许有别的文字', ['只输出', '不要']),
    ('(3) 取值范围', ['可选的算法族']),
    ('(4) 转义约定', ['转义', '\\"']),
]

# 判分额外认的几条：约束 (3) 要求八张族名表全列上；(4) 要求提示词里真的出现转义写法。
FAMILY_LIST_MARK = '、'.join(name for name, _ in FAMILIES)
ESCAPE_MARK = '\\"'


def prompt_missing(prompt, problem):
    """逐条核对四样约束，交回**缺哪些**的标签表（都齐了就交回空表）。

    比对小写之后的文本：提示词里写大写 JSON 也算写明了格式。
    """
    lowered = prompt.lower()
    missing = []
    for label, anchors in PROMPT_REQUIRED:
        for anchor in anchors:
            if anchor.lower() not in lowered:
                missing.append(label)
                break
    if FAMILY_LIST_MARK not in prompt:
        missing.append('(3) 取值范围里的八张族名表不齐')
    if ESCAPE_MARK not in prompt and '\\' not in prompt:
        missing.append('(4) 转义约定里没有反斜杠配引号的写法')
    if trim(problem) not in prompt:
        missing.append('题面没有原样出现在提示词里（problem.strip() 之后的那份）')
    return missing


# task2：6 组判分自己造的探针样本，分三类。键名 → (原文, 谁该吃得下)
#   '朴素也过'   干净的一段，直接 json.loads 就拿下了；
#   '只有加固过' 有格式浮动（围栏、前后解释），剥一层才拿得下；
#   '两版都不过' 内容本身不合法（压根没有大括号、只有一个半截的、引号没转义的）。
# 期望值由判分自己按这两条口径**算**出来，不靠这里的标签：标签只是给人看的。
PROBE_SAMPLES = {
    '干净 JSON 没有解释': ('{"family": "前缀和", "confidence": "高"}', '朴素也过'),
    '围栏没有语言标记': (FENCE + '\n{"family": "贪心", "confidence": "低"}\n' + FENCE,
                        '只有加固过'),
    '前后都有解释': ('先看题意。\n{"family": "图的搜索", "confidence": "中"}\n'
                     '以上就是我的判断，供你参考。', '只有加固过'),
    '根本没有大括号': ('这道题用贪心就行，按结束时间排。', '两版都不过'),
    '半截 JSON': ('{"family": "二分答案"', '两版都不过'),
    '引号没转义': (ESCAPE_TRAP, '两版都不过'),
}


def naive_ok(raw):
    """朴素 json.loads 能不能吃下这一段（判分自己的口径）。"""
    value, _ = safe_load(trim(raw))
    return isinstance(value, dict) and 'family' in value


def robust_ok(raw):
    """剥围栏 + 取首尾大括号之后能不能吃下这一段（判分自己的口径）。"""
    text = trim(raw)
    lo_mark, hi_mark = make_fence(), make_fence()
    start, end = text.find(lo_mark), text.rfind(hi_mark)
    if start != -1 and end > start + len(lo_mark):
        inner = text[start + len(lo_mark):end]
        if inner.startswith('json'):
            inner = inner[4:]
        text = trim(inner)
    lo, hi = text.find('{'), text.rfind('}')
    if lo == -1 or hi == -1 or hi < lo:
        return False
    value, _ = safe_load(text[lo:hi + 1])
    return isinstance(value, dict) and 'family' in value


def classify_expected(text):
    """按 FAMILIES 算期望的候选列表（就是 canonical_classify，另起一个名字给判分读）。"""
    return canonical_classify(text)


# ── 8b. 失败标记与「剥围栏」的读数口径（判分与脚本共用）────────────────────
#
# 解析器的失败标记是**两头尖括号的字符串**，比如 '<JSONDecodeError>'。
# 打印那一格时不要直接打印解析器交回来的值（它会带花括号、引号，判分读起来要猜），
# 统一过一道这两个函数。

def basic_marker(value):
    """是不是一个「基本形态」的失败标记：'<异常类名>'（里面全是字母数字）。"""
    if not isinstance(value, str) or not (value.startswith('<') and value.endswith('>')):
        return False
    return value[1:-1].isalnum()


def marker_cell(value):
    """打印那一格：基本形态的失败标记原样，别的（字典、其它字符串、None）都写成 '非标记'。

    「非标记」这四个字就是判分要读的东西：它不是标记，说明解析**没有失败**。
    """
    if basic_marker(value):
        return value
    return '非标记'


def fence_line_count(text):
    """这一段文本里有几行是围栏行：一行开头就是三个反引号。"""
    head = FENCE
    return sum(1 for line in str(text).splitlines() if line.startswith(head))


# ── 9. 打印统一走这里 ────────────────────────────────────────────────────

def show_banner(title):
    """打印一行小节标题，四个任务的脚本都用它开头。"""
    print('== ' + title + ' ==')


def show_line(label, value):
    """打印一行「标签 值」，判分按标签取。"""
    print(label + ' ' + str(value))
