#!/usr/bin/env python3
r"""lab 0015 · 自动判分（实验二：给解法装上对拍器）

用法（在 lab/0015-lab-02-verify-by-brute-force/ 目录里）：

    py run_tests.py

判法：**四层**，一层里几条检查各自给 PASS / FAIL。

    第 1 层 · 参照解对不对
        brute_find 在八组已知数据上给出正确的下标（空数组、单元素、重复值、
        目标不存在、答案在左端 / 右端都算在里面）。参照解是尺子，尺子不准，
        后面三层的结论全不算数。

    第 2 层 · stress 没自己骗自己
        拿**同一个函数**同时当候选与参照，跑 2000 次必须一次都抓不到（交回 None）。
        这一层专门抓「stress 根本没在比对」：漏了「两个答案不一样就报告」那一行、
        把两个答案写反、或者自己另造一组数据跟自己比就算过。
        另有一条对照：把候选换成「跟参照永远不一致」的一个函数，stress 必须立刻抓到——
        两条都对，才说明它真的在比两个答案。

    第 3 层 · 抓得住，而且抓得可复现
        两个造数据器交回的 a 必须升序、形状合法；再把候选换成两个「只在某种边界形态上
        出错」的假函数各对拍一次，两次都要被抓到——这是 gen_boundary 真的造了
        空数组 / 单元素 / 重复值这些形态的证据（造不出来就抓不到）。
        然后拿它对拍 buggy.py：必须抓到，而且同一个 seed 连着跑两次要抓到**同一组**数据。

    第 4 层 · 缩到最小，记录对得上
        shrink 的结果必须仍然让两边不一致、而且再删一个元素也删不动了；
        给它一组「前几个元素对暴露 bug 毫无贡献」的反例，它必须真的缩；
        把候选换成「答案永远错」的函数，它也必须照样缩。
        findings.md 里记的原始反例与最小反例，与判分自己算出来的对照——必须一致；
        出错的行号必须是 buggy.py 里那一行 `while lo < hi`（行号从 1 数起）。

判分不判的东西：造数据器够不够多样、记录写得清不清楚，由 lab/README.md 的自查清单
与课件那一节回答；这里只管能不能跑、比对有没有生效、反例能不能复现。

退出码：四层都过是 0；还有没过的（或跳过的）是 1。
"""

from __future__ import annotations

import importlib
import random
import re
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent

TRIALS = 2000
SEED = 20261115
LABEL = '第 {n} 次抓到：a={a} x={x} 候选={g} 参照={w}'

# 第 1 层：八组已知数据 → (a, x, 期望的下标)
BRUTE_CASES = [
    ([], 3, -1),
    ([7], 7, 0),
    ([7], 3, -1),
    ([4, 9], 9, 1),
    ([4, 9], 4, 0),
    ([1, 2, 3, 4, 5], 3, 2),
    ([5, 5, 5], 5, 0),
    ([1, 3, 5, 7, 9], 6, -1),
]


# ── 载入学生写的那个模块 ────────────────────────────────────────────────

class Loaded:
    """载入 stress.py → 记下它、载入时的异常、以及缺了哪些名字。"""

    def __init__(self):
        self.module = None
        self.tools = None
        self.buggy = None
        self.error = None
        self.missing = []
        sys.path.insert(0, str(HERE))
        try:
            import tools as tools_module
            self.tools = tools_module
            import buggy as buggy_module
            self.buggy = buggy_module
        except Exception:
            self.error = '给好的文件载入失败（tools.py / buggy.py 别改、别删）：\n' \
                         + traceback.format_exc()
            return
        try:
            import stress as student          # noqa: PLC0415  必须在 sys.path 改完再 import
            self.module = importlib.reload(student)
        except Exception:
            self.error = traceback.format_exc()
            return
        for name in ('brute_find', 'gen_wide', 'gen_boundary', 'stress', 'shrink'):
            if not callable(getattr(self.module, name, None)):
                self.missing.append(name)

    @property
    def ok(self):
        return self.error is None and not self.missing

    def why(self):
        if self.error is not None:
            tail = '\n'.join(self.error.strip().splitlines()[-6:])
            return 'stress.py 载入失败——它自己那几行就报错了：\n' + tail
        if self.missing:
            return ('stress.py 里找不到这些函数（函数名是判分接口，别改名、别删）：'
                    + '、'.join(self.missing))
        return ''

    def fn(self, name):
        return getattr(self.module, name, None)

    def cand(self, name='cand_find'):
        return getattr(self.buggy, name, None)

    def rows(self, candidate, reference, gen, trials=TRIALS, seed=SEED):
        """跑一次对拍 → (抓到的那几组, 报错文本)。"""
        return attempt(self.fn('stress'), candidate, reference, gen, trials, seed)

    def lists(self, candidate, reference, a, x):
        """跑一次两边 → (候选, 参照)。用给好的 tools.as_lists，口径与对拍一致。"""
        return self.tools.as_lists(candidate, reference, a, x)


# ── 调用学生函数的保险：报错就转成一句 FAIL，不让判分自己崩 ──────────────

def attempt(func, *args, **kwargs):
    """调一次 → (值, 错误文本)。抛异常时值是 None、错误文本是「类型: 说明」。"""
    try:
        return func(*args, **kwargs), None
    except Exception as exc:
        return None, type(exc).__name__ + ': ' + str(exc)


def error_note(error):
    return '' if error is None else '（调用时抛出 ' + error + '）'


# ── 形状判据 ────────────────────────────────────────────────────────────

def shape_of(seed, trials, maker):
    """连造 trials 组数据 → 数一数每组算哪种形态、数组升不升序、x 在不在表里。

    形态口径（数组不是升序时只记 asc，不归类）：
        空数组 / 单元素 / 全相同（长度 ≥ 2 且只有一个不同的值）/ 答案在左端 /
        答案在右端（两种端点形态都要求 x 真的在数组里）/ 其余算「一般数据」。
    交回 dict；中途造出的东西形状不合法时交回 {'bad': 那一组}。
    """
    random.seed(seed)
    shapes = {'空数组': 0, '单元素': 0, '全相同': 0, '答案在左端': 0,
              '答案在右端': 0, '一般数据': 0}
    asc = 0
    inside = 0
    for _ in range(trials):
        made = maker()
        if not (isinstance(made, tuple) and len(made) == 2):
            return {'bad': '交回的不是 (a, x) 两个：' + repr(made)}
        a, x = made
        if not isinstance(a, list) or not all(isinstance(v, int) and not isinstance(v, bool)
                                              for v in a):
            return {'bad': 'a 不是一张整数表：' + repr(a)}
        if isinstance(x, bool) or not isinstance(x, int):
            return {'bad': 'x 不是整数：' + repr(x)}
        if not all(a[i] <= a[i + 1] for i in range(len(a) - 1)):
            continue
        asc += 1
        if x in a:
            inside += 1
        if len(a) == 0:
            shapes['空数组'] += 1
        elif len(a) == 1:
            shapes['单元素'] += 1
            if x == a[0]:
                shapes['答案在左端'] += 1
                shapes['答案在右端'] += 1
        elif len(set(a)) == 1:
            shapes['全相同'] += 1
        elif x == a[0]:
            shapes['答案在左端'] += 1
        elif x == a[-1]:
            shapes['答案在右端'] += 1
        else:
            shapes['一般数据'] += 1
    return {'shapes': shapes, 'asc': asc, 'inside': inside, 'trials': trials}


def is_one_row(row):
    return (isinstance(row, tuple) and len(row) == 5
            and isinstance(row[1], list) and isinstance(row[2], int))


def found_rows(result):
    """把 stress 的返回值归成「抓到的那几组数据」这张表。

    交回 None → []（一次都没抓到）；交回一组或一组组、形状都对 → 那张表；
    形状不认识 → None（由调用处报 FAIL）。
    """
    if result is None:
        return []
    if is_one_row(result):
        return [result]
    if isinstance(result, list) and all(is_one_row(item) for item in result):
        return list(result)
    return None


def describe(row):
    return LABEL.format(n=row[0], a=list(row[1]), x=row[2], g=row[3], w=row[4])


def short(text, limit=64):
    text = '' if text is None else str(text)
    return text if len(text) <= limit else text[:limit] + '…'


# ── 三个「假候选」：专门试学生的对拍器有没有真的在比、造数据器有没有覆盖边界 ──

def cand_always_zero(a, x):
    """答案永远是 0。与参照解比对时几乎每次都报不一致。"""
    return 0


def cand_empty_crash(a, x):
    """只在空数组上错：别的输入与参照解完全一致。"""
    if len(a) == 0:
        return 0
    for i in range(len(a)):
        if a[i] == x:
            return i
    return -1


def cand_dup_crash(a, x):
    """只在「单元素」与「有重复值」上错：这两种形态造不出来，就抓不到它。"""
    if len(a) >= 2 and len(set(a)) == 1:
        return len(a) - 1
    if len(a) == 1:
        return -1
    for i in range(len(a)):
        if a[i] == x:
            return i
    return -1


# ── 第 1 层 · 参照解对不对 ──────────────────────────────────────────────

def layer1(loaded):
    if not loaded.ok:
        return [(False, loaded.why())]
    _, error = attempt(loaded.fn('brute_find'), [1], 1)
    if error is not None:
        return [(False, 'brute_find([1], 1) 就报错了' + error_note(error))]
    out = []
    bad = []
    for a, x, want in BRUTE_CASES:
        got, error = attempt(loaded.fn('brute_find'), list(a), x)
        if error is not None:
            bad.append('a=' + repr(a) + ' x=' + repr(x) + ' 报错')
        elif got != want:
            bad.append('a=' + repr(a) + ' x=' + repr(x) + ' → ' + short(repr(got))
                       + '（期望 ' + repr(want) + '）')
    if not bad:
        out.append((True, '八组已知数据全部对上：空数组与「目标不存在」都交回 -1，'
                          '重复值 [5, 5, 5] 交回第一处的 0，答案在右端的 [4, 9] x=9 交回 1'))
    else:
        out.append((False, 'brute_find 有 ' + str(len(bad)) + ' 组不对：' + short('；'.join(bad))
                    + '——参照解是尺子，先让它在手算的小数据上对，再拿它对拍'))
        return out

    source = Path(loaded.module.__file__).read_text(encoding='utf-8')
    if 'random' in source:
        out.append((True, 'stress.py 里用到了 random（造数据器与固定种子都要它）'))
    else:
        out.append((False, 'stress.py 里没有 random——造数据器与固定种子都要用到它，'
                           '在文件开头写 import random'))
    return out


# ── 第 2 层 · stress 没自己骗自己 ───────────────────────────────────────

def layer2(loaded):
    if not loaded.ok:
        return [(False, '第 2 层跳过：' + short(loaded.why(), 80))]
    brute = loaded.fn('brute_find')
    gen = loaded.fn('gen_boundary')
    sample, gen_error = attempt(gen)
    if gen_error is not None or not (isinstance(sample, tuple) and len(sample) == 2):
        return [(False, 'gen_boundary() 交回的不是 (a, x) 两个：' + short(repr(sample))
                        + error_note(gen_error) + '——这一层要拿它造数据，先把 TODO 2 写上')]

    # 2a：同一个函数同时当候选与参照，2000 次必须一次都抓不到
    same, error = loaded.rows(brute, brute, gen)
    if error is not None:
        return [(False, 'stress(brute_find, brute_find, gen_boundary, ' + str(TRIALS)
                        + ', seed=…) 报错' + error_note(error)
                        + '——先看那个函数的返回值：函数还空着时它交回 None，'
                          '对拍器拿 None 去取下标就会抛 TypeError')]
    rows = found_rows(same)
    if rows is None:
        return [(False, 'stress 的返回值形状不对：' + short(repr(same))
                        + '——要么交回 None（一次都没抓到），要么交回 '
                          '(第几次, a, x, 候选答案, 参照答案) 这五样')]
    if rows:
        return [(False, '同一个函数同时当候选与参照，居然报了 ' + str(len(rows)) + ' 组不一致：'
                        + short(describe(rows[0]))
                        + '——同一个函数跟自己比永远该一致。三个地方各看一遍：'
                          '比对那一行是不是写着「两个答案不一样就报告」（写反了只会在一致时报）、'
                          '交回的五样里候选与参照是不是调了个位置、'
                          '以及循环里有没有另造一组数据在跟自己比')]
    out = [(True, '同一个函数同时当候选与参照，' + str(TRIALS)
                  + ' 次一次都没抓到（交回 None）——这个对拍器没有自己骗自己')]

    # 2b：候选换成「永远不一致」的函数，必须立刻抓到
    zero, error = loaded.rows(cand_always_zero, brute, gen)
    if error is not None:
        out.append((False, '把候选换成「答案永远是 0」的函数之后，stress 报错'
                           + error_note(error)))
        return out
    caught = found_rows(zero)
    if caught:
        out.append((True, '候选换成「答案永远是 0」的函数立刻被抓到（' + describe(caught[0])
                          + '）——它真的在比两个答案'))
    elif caught == []:
        out.append((False, '候选换成「答案永远是 0」的函数，' + str(TRIALS)
                           + ' 次一次都没抓到——这说明它没有在比两个答案：'
                             '比对那一行漏了，或者比的是别的东西'))
    else:
        out.append((False, 'stress 的返回值形状不对：' + short(repr(zero))))
    return out


# ── 第 3 层 · 抓得住，而且抓得可复现 ────────────────────────────────────

def layer3(loaded):
    if not loaded.ok:
        return [(False, '第 3 层跳过：' + short(loaded.why(), 80))]
    brute = loaded.fn('brute_find')
    cand = loaded.cand()
    if cand is None:
        return [(False, 'buggy.py 里没有 cand_find——这个文件是给好的，别改、别删')]
    out = []

    # 3a：两个造数据器的形状与升序
    for name in ('gen_wide', 'gen_boundary'):
        report, error = attempt(shape_of, SEED, 40, loaded.fn(name))
        if error is not None:
            out.append((False, name + ' 连造 40 组就报错' + error_note(error)))
            continue
        if 'bad' in report:
            out.append((False, name + ' 造出来的东西形状不对：' + short(report['bad'])
                        + '——每次要交回 (a, x)：a 是一张**整数表**、x 是一个整数'))
            continue
        if report['asc'] < report['trials']:
            out.append((False, name + ' 连造 40 组里有 ' + str(report['trials'] - report['asc'])
                        + ' 组的 a 不是升序：候选解是二分，无序的数据会让它给出没意义的答案，'
                          '对拍报出来的东西也就不算证据'
                          '（生成器里排一次序，或者用 sorted(...) 包一层）'))
            continue
        if name == 'gen_wide':
            out.append((True, 'gen_wide 连造 40 组：数组都是升序的、形状合法（其中 '
                              + str(report['inside']) + ' 组的 x 落在数组里）'))
        else:
            out.append((True, 'gen_boundary 连造 40 组的形态分布：'
                              + '、'.join(k + ' ' + str(v) for k, v in report['shapes'].items())))

    # 3b：边界形态真的覆盖到了——用两个「只在某种形态上错」的假候选反过来试它
    gen = loaded.fn('gen_boundary')
    for what, fake in (('空数组', cand_empty_crash),
                       ('单元素或重复值', cand_dup_crash)):
        result, error = loaded.rows(fake, brute, gen)
        rows = found_rows(result)
        if error is not None:
            out.append((False, '拿「只在' + what + '上出错」的假候选对拍时 stress 报错'
                               + error_note(error)))
        elif not rows:
            out.append((False, '拿一个「只在' + what + '上出错」的假候选对拍 ' + str(TRIALS)
                               + ' 次，一次都没抓到——gen_boundary 还没造出这种形态。'
                                 '这一支要专门写出来，不能等随机去撞：' + what))
        else:
            out.append((True, '「只在' + what + '上出错」的假候选被抓到了（'
                              + describe(rows[0]) + '）——gen_boundary 确实造了这种形态'))

    # 3c：对拍 buggy.py 必须抓到
    first, error = loaded.rows(cand, brute, gen)
    rows = found_rows(first)
    if error is not None:
        out.append((False, 'stress(cand_find, brute_find, gen_boundary, ' + str(TRIALS)
                           + ', seed=…) 报错' + error_note(error)))
        return out
    if rows is None:
        out.append((False, 'stress 的返回值形状不对：' + short(repr(first))))
        return out
    if not rows:
        out.append((False, '拿 ' + str(TRIALS) + ' 次预算对拍 buggy.py，一次都没抓到——'
                           'buggy.py 里的 cand_find 确实有 bug，抓不到是造数据器没踩中触发条件：'
                           '它只在「x 真的在数组里」而且「答案恰好是最后剩下的那一格」时才露出来，'
                           '让 gen_boundary 主动把单元素、全相同、答案在两端这些形态造出来'))
        return out
    out.append((True, '对拍 buggy.py 第 ' + str(rows[0][0]) + ' 次就抓到了：' + describe(rows[0])
                      + '——候选交回 ' + repr(rows[0][3]) + '，参照交回 ' + repr(rows[0][4])))

    # 3d：同一个 seed 连着跑两次，抓到同一组
    second, error = loaded.rows(cand, brute, gen)
    rows2 = found_rows(second)
    if error is not None:
        out.append((False, '第二次用同一个 seed 跑时 stress 报错' + error_note(error)))
    elif not rows2:
        out.append((False, '第一次抓到了，第二次用同一个 seed 却一次都没抓到——'
                           '说明种子没固定：random.seed(seed) 要在**循环外面**设一次，'
                           '而且只在 seed 不是 None 时设'))
    elif (rows2[0][0], list(rows2[0][1]), rows2[0][2]) != (rows[0][0], list(rows[0][1]), rows[0][2]):
        out.append((False, '同一个 seed 两次抓到的不一样：第一次 ' + short(describe(rows[0]), 46)
                           + '，第二次 ' + short(describe(rows2[0]), 46)
                           + '——反例要能复现才当得了证据（种子设在了循环里面，或者压根没设）'))
    else:
        out.append((True, '同一个 seed 连着跑两次，抓到的是同一组数据（第 ' + str(rows[0][0])
                          + ' 次：a=' + repr(list(rows[0][1])) + ' x=' + repr(rows[0][2])
                          + '）——这组反例是可复现的证据'))
    return out


# ── 第 4 层 · 缩到最小，记录对得上 ──────────────────────────────────────

def can_still_shrink(loaded, candidate, a, x):
    """a 还能再删一个元素而两边仍不一致吗？交回 False（缩不动）/ 更小的那张表 / None（算不出来）。"""
    reference = loaded.fn('brute_find')
    for i in range(len(a)):
        smaller = a[:i] + a[i + 1:]
        got_want, error = attempt(loaded.lists, candidate, reference, smaller, x)
        if error is not None:
            return None
        got, want = got_want
        if got != want:
            return smaller
    return False


def check_findings(loaded, small, raw_x):
    """findings.md 的三样东西：原始反例、最小反例、出错的行号。"""
    path = HERE / 'findings.md'
    if not path.is_file():
        return [(False, '还没有 findings.md——任务 5 的两样产物之一就是它：'
                        '原始反例、最小反例、出错的那一行，三样都写进去')]
    text = path.read_text(encoding='utf-8')
    if 'TBD' in text:
        return [(False, 'findings.md 里还留着 TBD 这个记号——'
                        '照着 py stress.py 打出来的那几行把三样东西填进去')]
    out = []

    source = (HERE / 'buggy.py').read_text(encoding='utf-8').splitlines()
    culprit = None
    for number, row in enumerate(source, 1):
        if row.strip().startswith('while lo < hi'):
            culprit = number
            break
    if culprit is None:
        return [(False, 'buggy.py 里找不到那一行 `while lo < hi`——这个文件是给好的，别改')]

    found = re.search(r'第\s*(\d+)\s*行', text)
    if not found:
        out.append((False, 'findings.md 里没有写出错的行号——'
                           '照 py stress.py 最后打出的那一行写「buggy.py 第 N 行」'))
    elif int(found.group(1)) != culprit:
        out.append((False, 'findings.md 里写的是第 ' + found.group(1) + ' 行，'
                           'buggy.py 里出错的那一行是第 ' + str(culprit) + ' 行（'
                           + repr(source[culprit - 1].strip()) + '，行号从 1 数起）'))
    else:
        out.append((True, 'findings.md 指出的是 buggy.py 第 ' + str(culprit) + ' 行（'
                          + repr(source[culprit - 1].strip()) + '）——'
                          '闭区间配上这个循环条件，最后剩下的那一格从没被检查过'))

    minimal = re.search(r'最小反例[^\n]*?a\s*=\s*(\[[^\]\n]*\])', text)
    if not minimal:
        out.append((False, 'findings.md 里没找到「最小反例: a = [...]」这一行——'
                           '照 py stress.py 第 5 步打出的那一行抄'))
    elif minimal.group(1).replace(' ', '') == repr(list(small)).replace(' ', ''):
        out.append((True, 'findings.md 记的最小反例 ' + minimal.group(1)
                          + ' 与判分自己缩出来的那一组一致'))
    else:
        out.append((False, 'findings.md 记的最小反例是 ' + minimal.group(1)
                           + '，判分自己缩出来的是 ' + repr(list(small))
                           + '——两边必须一致（记录照 shrink 的结果抄，别手写）'))

    original = re.search(r'原始反例[^\n]*?a\s*=\s*(\[[^\]\n]*\])\s*,?\s*x\s*=\s*(-?\d+)', text)
    if not original:
        out.append((False, 'findings.md 里没找到「原始反例: a = [...], x = ...」这一行——'
                           '照 py stress.py 第 4 步抓到的那一组抄'))
    else:
        listed_a = None
        try:
            listed_a = eval(original.group(1), {'__builtins__': {}}, {})   # noqa: S307 只解析整数表
        except Exception:
            listed_a = None
        if not isinstance(listed_a, list):
            out.append((False, 'findings.md 里的原始反例读不出来：' + original.group(1)))
        else:
            got_want, error = attempt(loaded.lists, loaded.cand(), loaded.fn('brute_find'),
                                      listed_a, int(original.group(2)))
            if error is not None:
                out.append((False, '拿 findings.md 里那组原始反例跑两边时报错'
                                   + error_note(error)))
            else:
                got, want = got_want
                if got != want:
                    out.append((True, 'findings.md 记的原始反例 ' + original.group(1)
                                      + ' x=' + original.group(2) + ' 确实是反例（候选 '
                                      + repr(got) + ' / 参照 ' + repr(want) + '）'))
                else:
                    out.append((False, 'findings.md 记的原始反例 ' + original.group(1)
                                       + ' x=' + original.group(2) + ' 两边是一致的（都交回 '
                                       + repr(got) + '）——那不是一组反例，照抓到的那一组抄'))
    return out


def layer4(loaded):
    if not loaded.ok:
        return [(False, '第 4 层跳过：' + short(loaded.why(), 80))]
    brute = loaded.fn('brute_find')
    cand = loaded.cand()
    if cand is None:
        return [(False, 'buggy.py 里没有 cand_find——这个文件是给好的，别改、别删')]
    out = []

    # 4a：自己找一组反例（不复用第 3 层的结果：这一层单独也要说得通）
    hit, error = loaded.rows(cand, brute, loaded.fn('gen_boundary'))
    rows = found_rows(hit)
    if error is not None or not rows:
        return [(False, '这一层要一组反例来缩，但 stress 没抓到（'
                        + ('报错' + error_note(error) if error else '一次都没抓到')
                        + '）——先让第 3 层过')]
    _, raw_a, raw_x, _, _ = rows[0]

    # 4b：缩出来的东西形状要对
    small, error = attempt(loaded.fn('shrink'), cand, brute, raw_a, raw_x)
    if error is not None:
        return [(False, 'shrink(cand_find, brute_find, ' + repr(raw_a) + ', ' + repr(raw_x)
                        + ') 报错' + error_note(error)
                        + '——注意它要交回**一张表**（不是 (a, x) 两个）')]
    if not isinstance(small, list) or not all(isinstance(v, int) and not isinstance(v, bool)
                                              for v in small):
        return [(False, 'shrink 交回的不是一张整数表：' + short(repr(small))
                        + '——x 从头到尾不变，最小化的是那张表，所以只交回表')]

    # 4c：还是真的反例吗
    got_want, error = attempt(loaded.lists, cand, brute, small, raw_x)
    if error is not None:
        return [(False, '拿 shrink 的结果跑两边时报错' + error_note(error))]
    got, want = got_want
    if got == want:
        return [(False, 'shrink 交回的 ' + repr(small) + ' x=' + repr(raw_x)
                        + ' 两边一致了（都交回 ' + repr(got) + '）——'
                          '它接受了一个让两边重新一致的版本：每次接受更小的版本**之前**要再比一次')]
    out.append((True, 'shrink 的结果 ' + repr(small) + ' x=' + repr(raw_x) + ' 仍然不一致（候选 '
                      + repr(got) + ' / 参照 ' + repr(want) + '）'))

    # 4d：缩到底了吗
    further = can_still_shrink(loaded, cand, small, raw_x)
    if further is None:
        out.append((False, '拿 shrink 的结果再删一个元素时报错，没法判断它缩到底没有'))
        return out
    if further is False:
        out.append((True, '再删掉一个元素就抓不到这个 bug 了——' + repr(small)
                          + ' 已经缩到底（' + str(len(small)) + ' 个元素）'))
    else:
        out.append((False, 'shrink 的结果 ' + repr(small) + ' 还能再缩：删掉一个元素得到 '
                           + repr(further) + '，两边依然不一致——'
                             '要反复试到再也删不动为止（一轮下来一个都删不掉才跳出循环）'))
        return out

    # 4e：给它一组「能缩」的反例，它必须真的缩
    reducible = [10, 20, 63, 97]
    small2, error2 = attempt(loaded.fn('shrink'), cand, brute, list(reducible), 97)
    if error2 is not None:
        out.append((False, 'shrink(cand_find, brute_find, ' + repr(reducible) + ', 97) 报错'
                           + error_note(error2)))
    elif not isinstance(small2, list) or len(small2) >= len(reducible):
        out.append((False, '给它 ' + repr(reducible) + ' x=97 这一组（前两个元素对暴露 bug '
                           '毫无贡献），shrink 交回 ' + short(repr(small2))
                           + '——大小没减下来，说明它没有真的在缩'))
    else:
        out.append((True, '给它 ' + repr(reducible) + ' x=97 这一组，缩成了 ' + repr(small2)
                          + '——真的在缩，不是原样交回'))

    # 4f：候选换成「答案永远错」的函数，缩的能力不依赖那一个 bug
    small3, error3 = attempt(loaded.fn('shrink'), cand_always_zero, brute, list(reducible), 97)
    if error3 is not None:
        out.append((False, '把候选换成「答案永远是 0」的函数之后 shrink 报错' + error_note(error3)))
    elif not isinstance(small3, list) or len(small3) >= len(reducible):
        out.append((False, '把候选换成「答案永远是 0」的函数，给它 ' + repr(reducible)
                           + ' 缩出来的是 ' + short(repr(small3))
                           + '——shrink 不该只对某一个 bug 有效：它比的是传进来的那两个函数'))
    else:
        out.append((True, '换一个候选函数照样缩（' + repr(reducible) + ' → ' + repr(small3)
                          + '）——shrink 用的是传进来的那两个函数，不是写死的那一对'))

    # 4g：findings.md 的三样东西
    out += check_findings(loaded, small, raw_x)
    return out


# ── 主流程 ──────────────────────────────────────────────────────────────

LAYERS = [
    ('第 1 层 · 参照解对不对', layer1),
    ('第 2 层 · stress 没自己骗自己', layer2),
    ('第 3 层 · 抓得住，而且抓得可复现', layer3),
    ('第 4 层 · 缩到最小，记录对得上', layer4),
]


def main():
    print('StudyMate lab 0015 · 自动判分（给解法装上对拍器）')
    print('目录：' + str(HERE))
    print()
    loaded = Loaded()
    passed = 0
    failed = 0
    layers_done = 0
    layers_ok = 0
    for index, (title, check) in enumerate(LAYERS, 1):
        print(title)
        if index == 1 and not loaded.ok:
            print('  FAIL  ' + loaded.why().replace('\n', '\n        '))
            print('        （后面三层跳过：参照解与对拍循环都没接上，它们的信息没有参考价值）')
            print()
            failed += 1
            break
        try:
            checks = check(loaded)
        except Exception:                                   # 判分自己也不许崩
            checks = [(False, '判分自己在这一层抛了异常，把下面这段贴给教练：\n'
                              + traceback.format_exc())]
        layers_done += 1
        layer_ok = True
        for ok, message in checks:
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
    print('四层：' + str(layers_ok) + ' 层通过、' + str(layers_done - layers_ok) + ' 层还没过'
          + '（共 ' + str(passed) + ' 条 PASS、' + str(failed) + ' 条 FAIL）')
    if failed == 0:
        print('四层全过。现在去对照 ../solutions/0015-lab-02-verify-by-brute-force/：')
        print('比一比造数据器覆盖了哪些形态、stress 的返回值怎么设计，'
              '再用一句话回答「是哪一个数据形态让 buggy.py 暴露出来的」。')
        return 0
    if layers_done < len(LAYERS):
        print('第 1 层就没过，后面三层的信息没有参考价值，所以跳过了。')
        print('先单独跑 py stress.py 看它在哪一行停下（函数还空着时会抛 TypeError）。')
    else:
        print('卡住了先读 ../README.md 的「卡壳顺序」：读错误信息 → 自己跑一遍 → 看 FAIL 行 → 再对线索。')
    print('全部过了再对照 ../solutions/0015-lab-02-verify-by-brute-force/。')
    return 1


if __name__ == '__main__':
    sys.exit(main())
