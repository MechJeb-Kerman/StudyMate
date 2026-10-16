#!/usr/bin/env python3
r"""lab 0031 · 流程自检（实验四：一次完整的赛前模拟）

用法（在 lab/0031-lab-04-spaced-repetition-drill/ 目录里）：

    py check_timeline.py

这一课要判的**不是代码**，是决策与表述。所以这个脚本一行业都不跑你的答案，
只读两份自己填的材料：

    timeline.md   限时解题记录（五道题各一格：读题用时 / 定的算法 / 写完时刻 /
                  自检 / 得分 / 丢分点；放弃的那道还要写依据）
    explain.md    讲解稿（每题四段：解决什么问题 / 为什么正确 / 复杂度怎么推 /
                  **多大的规模会把它淘汰**）

它检查六件事，每件事给 PASS / FAIL：

    1 · 五道题都有记录
    2 · 每格的算法理由都提到了数据范围
    3 · 放弃的题写了依据（时间预算 + 具体数字）
    4 · 讲解稿四段齐全
    5 · 「什么规模会淘汰它」那一段带了具体数字
    6 · 两份材料里没有还留着的 TODO

退出码：六件事都过是 0，还有没过的（或有空文件）是 1。

只读 `timeline.md` 与 `explain.md` 两个文件；改文件名就找不到。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

TIMELINE = HERE / 'timeline.md'
EXPLAIN = HERE / 'explain.md'

# 五道题的编号：与 problems/p1 … problems/p5 对齐。
PROBLEMS = ['p1', 'p2', 'p3', 'p4', 'p5']

# 每题要有的域（键名就是模板里的行首标签，别改；冒号是半角或全角都认）。
FIELDS = ['读题用时', '定下的算法', '写完时刻', '自检做了什么', '得分', '丢分丢在哪']

# 放弃声明：写在 timeline 的任意位置都行，只要提到 pN 与「放弃」。
GIVE_UP_WORDS = ['放弃', '跳过', '不做这道', '果断跳']

# 「依据」里要能看出是在算时间预算，并且带数字。
BUDGET_WORDS = ['预算', '剩余', '总时长', '4 小时', '4小时', '两百四', '240',
                '做不完', '超预算', '来不及', '预计耗时', '估时']

# 讲解稿四段（模板里的四个二级标题，别改）。
SECTIONS = ['解决什么问题', '为什么正确', '复杂度怎么推', '多大的规模会淘汰它']

# 第 4 段要出现的「具体数字」形状：n ≤ 10^6 / 10^5 / 一百万 / 2 秒 / 1e6 之类。
SCALE_PATTERNS = [
    re.compile(r'\d\s*[×x*]\s*10\s*\^?\s*\d+'),      # 2×10^5
    re.compile(r'10\s*\^\s*\d+'),                      # 10^6
    re.compile(r'\b\d+(?:\.\d+)?\s*e\s*[+-]?\d+\b', re.I),  # 1e6
    re.compile(r'\d+(?:\.\d+)?\s*(?:万|亿|千|百)'),     # 五十万 / 100 万
    re.compile(r'\d+(?:\.\d+)?\s*(?:秒|分钟|毫秒)'),    # 2 秒 / 15 分钟
    re.compile(r'\b\d{4,}\b'),                         # 100000
]

# 中文数字（够用就行：只用来认「四小时」这类写法）。
CN_DIGITS = {'零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5,
             '六': 6, '七': 7, '八': 8, '九': 9}

# 一段内容至少要有几个非空白字符才算「写了」（防呆：写个「有」就想蒙过去）。
MIN_BODY = 12

# 占位符：一格（或一段）里只写了这些词，等于没写。
# 留白版给的就是带占位符的模板，所以这一条必须认得出占位符——
# 不然「还没做」会被当成「做完了」。
PLACEHOLDER_WORDS = [
    '待填', '待补', 'TODO', 'todo', 'Todo',
    '略', '无', '空', '没填', '未填', '还没写', '未写', '待写', '未做', '还没做',
    '不知道', '不确定', '空着', '待定', '看情况', '随便', '待想',
    'xxx', 'XXX', '...', '……', '——', '??', '？？', '?', '？',
    '分钟', '小时', '秒', '分', '钟',
]

# 一格的样子：`- 读题用时：8 分钟` / `- **定下的算法（为什么，要说数据范围）**：**二分**`
# 标签里不许出现冒号（要说明的括注写在括号里），否则没法切开。
FIELD_LINE = re.compile(
    r'^\s*(?:[-*+]\s*)?(?:#+\s*)?'          # 列表符号与井号
    r'(?:\*\*\s*)?'                          # 标签前面的 **
    r'(?P<key>[^：:*\n]+?)'                  # 标签本身：冒号与星号都不吃
    r'\s*(?:\*\*\s*)?'                       # 标签后面的 **
    r'[:：]\s*'                              # 分隔用的冒号（半角全角都认）
    r'(?P<value>.*)$'                        # 内容
)


def parse_field(line):
    """把一行读成 (标签, 内容)；不是「标签: 内容」的形状就交回 None。

    标签里可能带反引号（模板里写成 `` `### 多大的规模会淘汰它` ``），读之前剥掉。
    """
    match = FIELD_LINE.match(line)
    if not match:
        return None
    key = match.group('key').strip().strip('`').strip()
    value = match.group('value').strip().strip('`').strip()
    return (key, value) if key else None


def read_text(path):
    """读一份材料；文件不在就交回 None（调用处去报「文件不在」）。"""
    if not path.is_file():
        return None
    return path.read_text(encoding='utf-8', errors='replace')


def has_number(text):
    """这一段里有没有数字（半角或中文数字都算）。"""
    if re.search(r'\d', text):
        return True
    return any(char in CN_DIGITS for char in text)


def cn_number_in(text):
    """段里出现的最大中文数字（只处理个位/十位这种简单写法），没有就是 0。"""
    best = 0
    for match in re.finditer(r'[零一二两三四五六七八九十]+', text):
        word = match.group(0)
        value = 0
        if '十' in word:
            head, _, tail = word.partition('十')
            value = (CN_DIGITS.get(head, 1) if head else 1) * 10
            value += CN_DIGITS.get(tail, 0) if tail else 0
        else:
            value = CN_DIGITS.get(word[0], 0)
        best = max(best, value)
    return best


def has_scale_number(text):
    """有没有「具体规模」的数字：10^5、2×10^5、五十万、1e6、2 秒、100000 都算。"""
    for pattern in SCALE_PATTERNS:
        if pattern.search(text):
            return True
    return False


def short(text, limit=64):
    text = '' if text is None else str(text)
    text = ' '.join(text.split())
    return text if len(text) <= limit else text[:limit] + '…'


class Timeline:
    """把 timeline.md 切成五段：每段的标题里带 pN，段里的「标签: 内容」收进字典。"""

    HEAD = re.compile(r'^#{1,6}\s*(.*)$')

    def __init__(self, text):
        self.sections = {pid: {} for pid in PROBLEMS}
        self.texts = {pid: [] for pid in PROBLEMS}
        self.extra = []            # 不属于任何一题的行（定顺序那一段等）
        current = None
        for line in text.splitlines():
            head = self.HEAD.match(line)
            if head:
                found = self._problem_in(head.group(1))
                current = found
                if found:
                    self.texts[found].append(line)
                else:
                    self.extra.append(line)
                continue
            if current is None:
                self.extra.append(line)
                continue
            self.texts[current].append(line)
            field = parse_field(line)
            if field:
                key, value = field
                # 同一格写了两遍就合并，别丢信息。
                if key in self.sections[current] and self.sections[current][key]:
                    self.sections[current][key] += ' ' + value
                else:
                    self.sections[current][key] = value

    @staticmethod
    def _problem_in(head):
        """标题里认 p1 … p5（也认「第 1 题」「P1」「第1题」这些写法）。"""
        low = head.lower().replace(' ', '')
        for pid in PROBLEMS:
            if pid in low:
                return pid
        match = re.search(r'第\s*([1-5])\s*题', head)
        if match:
            return 'p' + match.group(1)
        return None

    def body(self, pid):
        """这一段里所有「标签: 内容」之外的内容，连带标签行一起去掉空白后拼起来。"""
        rows = []
        for line in self.texts[pid]:
            if parse_field(line):
                continue
            rows.append(line)
        return '\n'.join(rows).strip()

    def text(self, pid):
        return '\n'.join(self.texts[pid])

    def field(self, pid, key):
        """按标签取值；找不到就交回 None。标签允许写成「读题用时」或「1 读题用时」。"""
        rows = self.sections[pid]
        if key in rows:
            return rows[key]
        for name, value in rows.items():
            if key in name:
                return value
        return None


class Explain:
    """把 explain.md 按题切开，再把每题按四个二级标题切成四段。"""

    def __init__(self, text):
        self.parts = {pid: {} for pid in PROBLEMS}
        self.chunks = {pid: {name: [] for name in SECTIONS} for pid in PROBLEMS}
        current_pid = None
        current_sec = None
        for line in text.splitlines():
            head = re.match(r'^(#{1,6})\s*(.*)$', line)
            if head:
                level = len(head.group(1))
                title = head.group(2).strip()
                pid = Timeline._problem_in(title)
                if level <= 2 and pid:
                    current_pid = pid
                    current_sec = None
                    continue
                section = self._section_in(title)
                if section is not None:
                    if current_pid is not None:
                        current_sec = section
                        self.parts[current_pid].setdefault(section, [])
                    continue
                # 别的三级标题：不切换段落，但也不当内容
                continue
            if current_pid is not None and current_sec is not None:
                self.chunks[current_pid][current_sec].append(line)

    @staticmethod
    def _section_in(title):
        for name in SECTIONS:
            if name in title:
                return name
        return None

    def section(self, pid, name):
        rows = [line for line in self.chunks[pid][name]
                if not re.match(r'^\s*(?:[-*+]\s*)?(?:#+\s*)?\*\*?[^：:*]*\*\*?\s*[:：]', line)]
        return '\n'.join(rows).strip()

    def text(self, pid):
        rows = []
        for name in SECTIONS:
            rows.extend(self.chunks[pid][name])
        return '\n'.join(rows).strip()


def fail(message):
    return (False, message)


def who(pid, label):
    """FAIL 行的开头要带上是哪份材料、哪一题——一眼看出该改哪个文件。"""
    return label + ' ' + pid


def is_blank(value):
    """这一格是不是「还空着」：没有、或者只写了占位符。

    只写「待填」「TODO」「略」「无」这类词，等于没写——这一条的判定要挡住它，
    不然留白版里那五格占位符会被当成填好的。
    """
    text = re.sub(r'\s', '', value or '')
    if not text:
        return True
    # 剥掉占位词之后还剩什么？什么都不剩就是空着。
    residue = text
    for word in PLACEHOLDER_WORDS:
        residue = residue.replace(word, '')
    return not residue


def check_records(timeline):
    """第 1 条 · 五道题都有记录，每格的域齐全、而且不是占位符。"""
    out = []
    for pid in PROBLEMS:
        if not timeline.text(pid).strip():
            out.append(fail('FAIL ' + who(pid, '记录') + '：timeline.md 里没有这一题的记录'
                            '（记录模板里每一题都有一个二级标题，别删）'))
            continue
        gone = [key for key in FIELDS if is_blank(timeline.field(pid, key))]
        if gone:
            out.append(fail('FAIL ' + who(pid, '记录') + '：这几格空着没填——' + '、'.join(gone)
                            + '。没做出来的题**也要**填：卡在哪、什么时候决定放弃'))
        else:
            out.append((True, 'PASS ' + pid + '：六格都填了（读题用时 / 定的算法 / 写完时刻 / '
                              '自检做了什么 / 得分 / 丢分丢在哪）'))
    return out


def check_algorithm(timeline):
    """第 2 条 · 每格的算法理由要提到数据范围（不是只写个算法名）。"""
    out = []
    for pid in PROBLEMS:
        value = (timeline.field(pid, '定下的算法') or '').strip()
        if is_blank(value):
            out.append(fail('FAIL ' + who(pid, '记录') + '：没有「定下的算法」这一格'
                            '（或者只写了占位符）'))
            continue
        if has_number(value):
            out.append((True, 'PASS ' + pid + '：算法那一格提到了数据范围——'
                              + short(value)))
        else:
            out.append(fail('FAIL ' + who(pid, '记录') + '：算法那一格只有名字、没有数据范围（'
                            + short(value) + '）。第 28 课那套：先说 n 有多大，'
                            '再说这个规模容得下几阶复杂度'))
    return out


def check_give_up(timeline):
    """第 3 条 · 「放弃得对」：至少要有一题写了放弃，并且依据是时间预算 + 数字。"""
    out = []
    gave_up = []
    for pid in PROBLEMS:
        whole = timeline.text(pid)
        field_text = ' '.join(v for v in timeline.sections[pid].values())
        hit = any(word in whole for word in GIVE_UP_WORDS)
        if not hit:
            continue
        gave_up.append(pid)
        if not has_number(field_text):
            out.append(fail('FAIL ' + who(pid, '记录') + '：写了放弃，但依据里没有一个数字'
                            '（要能看出是在算时间预算：预计还要多少分钟、剩多少分钟）'))
        elif not any(word in whole for word in BUDGET_WORDS):
            out.append(fail('FAIL ' + who(pid, '记录') + '：写了放弃，但看不出依据是**时间预算**'
                            '（说明「预计耗时超过剩余预算」这类话，别只写「太难了」）'))
        else:
            out.append((True, 'PASS ' + pid + '：放弃的依据写清了（提到了时间预算，也带了数字）'))
    if not gave_up:
        out.append(fail('FAIL 记录 p1…p5：没有任何一题的「定下的算法」与「丢分丢在哪」'
                        '写了放弃。这一条是判断你会不会选题的直接证据：'
                        '五道题里有一道是 4 小时做不完的，把它标出来并写清依据'
                        '（预计耗时与剩余预算各是多少分钟）'))
    else:
        out.append((True, 'PASS 记录里能看出放弃的决定，涉及：' + '、'.join(gave_up)))
    return out


def check_explain_sections(explain):
    """第 4 条 · 讲解稿四段齐全，而且每段真写了东西。"""
    out = []
    for pid in PROBLEMS:
        missing = []
        thin = []
        for name in SECTIONS:
            body = explain.section(pid, name)
            if name not in explain.parts[pid]:
                missing.append(name)
            elif len(re.sub(r'\s', '', body)) < MIN_BODY:
                thin.append(name)
        if missing:
            out.append(fail('FAIL ' + who(pid, '讲解稿') + '：讲解稿缺这几段——' + '、'.join(missing)
                            + '（四段的标题就是模板里那四个，别改名）'))
        elif thin:
            out.append(fail('FAIL ' + who(pid, '讲解稿') + '：这几段几乎是空的（不足 ' + str(MIN_BODY)
                            + ' 个字）——' + '、'.join(thin)))
        else:
            out.append((True, 'PASS ' + pid + '：讲解稿四段齐全（解决什么问题 / 为什么正确 / '
                              '复杂度怎么推 / 多大的规模会淘汰它）'))
    return out


def check_scale(explain):
    """第 5 条 · 「多大的规模会淘汰它」那一段必须带具体数字——这一课的重点。"""
    out = []
    for pid in PROBLEMS:
        body = explain.section(pid, '多大的规模会淘汰它')
        if not body:
            out.append(fail('FAIL ' + who(pid, '讲解稿') + '：「多大的规模会淘汰它」这一段是空的'
                            '——说不出这条，说明你只是记住了这道题'))
            continue
        if not has_scale_number(body):
            out.append(fail('FAIL ' + who(pid, '讲解稿') + '：「多大的规模会淘汰它」这一段没有具体数字（'
                            + short(body) + '）。要写成「n 到 2×10^5 就超时」'
                            '「50 万个数要 2 秒」这样能对上的量'))
        else:
            out.append((True, 'PASS ' + pid + '：淘汰规模写成了具体数字——' + short(body, 72)))
    return out


def check_todo(timeline_text, explain_text):
    """第 6 条 · 两份材料里没有还留着的 TODO。"""
    out = []
    for name, text in (('timeline.md', timeline_text), ('explain.md', explain_text)):
        hits = [line.strip() for line in text.splitlines() if 'TODO' in line]
        if hits:
            out.append(fail('FAIL ' + name + ' 里还有 ' + str(len(hits))
                            + ' 处没换掉的 TODO（例如「' + short(hits[0], 40) + '」）'))
        else:
            out.append((True, 'PASS ' + name + ' 里的 TODO 都换成了自己的内容'))
    return out


def main():
    lab = HERE.name
    print('═' * 72)
    print('lab 0031 · 流程自检（限时解题记录 + 讲解稿）')
    print('═' * 72)

    results = []
    for path in (TIMELINE, EXPLAIN):
        if not path.is_file():
            print('FAIL 找不到 ' + path.name + '——这一课要交的就是这两份材料'
                  '（模板就在 lab 目录里，拷过来填）')
            print('')
            print('结论：0 条 PASS、1 条 FAIL  →  还没做完')
            return 1

    timeline_text = read_text(TIMELINE)
    explain_text = read_text(EXPLAIN)
    timeline = Timeline(timeline_text)
    explain = Explain(explain_text)

    groups = [
        ('1 · 五道题都有记录', check_records(timeline)),
        ('2 · 算法理由提到了数据范围', check_algorithm(timeline)),
        ('3 · 放弃的题写了依据', check_give_up(timeline)),
        ('4 · 讲解稿四段齐全', check_explain_sections(explain)),
        ('5 · 淘汰规模带了具体数字', check_scale(explain)),
        ('6 · 没有留着的 TODO', check_todo(timeline_text, explain_text)),
    ]

    passed = failed = 0
    for title, rows in groups:
        print('')
        print('── ' + title + ' ' + '─' * max(0, 66 - len(title)))
        for ok, message in rows:
            print('  ' + message)
            if ok:
                passed += 1
            else:
                failed += 1
        results.append(rows)

    print('')
    print('═' * 72)
    print('目录：' + lab)
    print('共 ' + str(passed) + ' 条 PASS、' + str(failed) + ' 条 FAIL')
    if failed:
        print('结论：还没做完。这一课判的是决策与表述：'
              '五道题都要有记录、放弃要有依据、讲解稿四段齐全、'
              '「多大的规模会淘汰它」要带数字')
        return 1
    print('结论：两份材料都齐了。带着这份数据去第 33 课')
    return 0


if __name__ == '__main__':
    sys.exit(main())
