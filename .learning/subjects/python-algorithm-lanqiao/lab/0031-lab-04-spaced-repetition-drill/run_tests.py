#!/usr/bin/env python3
r"""lab 0031 · 自动判分（实验四：一次完整的赛前模拟）

用法（在 lab/0031-lab-04-spaced-repetition-drill/ 目录里，或 solutions 里同一份）：

    py run_tests.py            # 判分，逐条给 PASS / FAIL
    py run_tests.py --quick    # 跳过「重跑全部测试数据」那两条（快一点）

这一课跟前面几课不一样：**lab 本身就是考核**，判的不是某道填空题，
而是一整套赛前模拟的脚手架能不能用、以及要交的两份材料是不是真的做了决策。
所以判分读的是这些东西（七层，一层里几条检查各自给 PASS / FAIL）：

    第 1 层 · 脚手架齐不齐
        check_timeline.py 与 score.py 在 lab 与 solutions 两侧**逐字节相同**；
        两个脚本单独跑退出码是 0、没有 Traceback；两个脚本里都不许出现连续三个反引号；
        manifest.json 的五题分值加起来等于总分；五道题的题面与样例都在，
        题面里写到了数据范围 / 输入格式 / 输出格式。

    第 2 层 · 判分数据能现算、且每次一样
        拿判分自己内嵌的 generate_cases() 生成几组最要紧的数据，
        与 test_data.generate() 逐字节对一遍；再生成两遍看是不是同一批。

    第 3 层 · 参考解真的都对吗（两组）
        在 solutions 一侧，对每组数据跑 reference/pN.py，要求退出码 0；
        再拿参考解现跑的结果与 problems/pN/cases 里的期望输出逐字比——
        期望输出不是写死的常数，而是**同一组数据现跑的参考解输出**。
        （留白版这一侧**故意不带 reference/**，这两层按「查不到」跳过。）

    第 4 层 · score.py 抓不抓得住写错的答案
        拿参考解当答案跑：退出码 0、总分 360 = 30 + 60 + 90 + 100 + 80；
        再把 p3 换成「每个询问都交回 0」：退出码非 0、总分 270
        （那 90 分被扣掉），并且输出里点出了 FAIL。

    第 5 层 · check_timeline.py 抓不抓得住写坏的材料
        拿**填好的**那份记录与讲解稿跑，必须 0 条 FAIL；
        再拿故意写坏的七份材料（缺一题的记录 / 算法没写数据范围 / 放弃没写依据 /
        还有 TODO / 讲解稿缺一段 / 淘汰规模没有数字 / 讲解稿还有 TODO）逐份跑，
        每份都必须退出码非 0，并且第一条 FAIL 点名到是哪个文件哪一条。

    第 6 层 · 留白版留下的是不是「还没做的痕迹」
        answers/p1.py … p5.py 都要在，而且不能有写好的答案（不许 import 参考解、
        不许从 solutions / reference 目录读文件）；
        这一侧**不许出现 reference/**——参考解只在 solutions 那一侧。

    第 7 层 · 这一课要交的两份材料
        timeline.md 与 explain.md 要在，而且里面要留着待填的 TODO
        （这一课要交的是「你填的」记录，不是抄来的示例）；
        solutions 一侧则必须已经填好，并且 check_timeline.py 认它。

退出码：七层都过是 0（solutions 一侧、参考解与两份材料都齐）；
留白版（lab 一侧，answers/ 还是空的、材料还是模板）是 1，
每一条 FAIL 都点名是哪个文件缺什么。
"""

from __future__ import annotations

import hashlib
import importlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import traceback
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

FENCE = '`' * 3                      # 连续三个反引号，本 lab 的 .py 里不许有

PROBLEM_IDS = ['p1', 'p2', 'p3', 'p4', 'p5']
TIMEOUT_QUICK = 90                   # 单组数据跑参考解的上限（秒）
DEFAULT_TIMEOUT = 15.0

# 参考解与留白答案各有多少个文件（留白版这一侧由 answers/ 决定）
REF_FILES = ['p1.py', 'p2.py', 'p3.py', 'p4.py', 'p5.py']
PURE_SCRIPTS = ['check_timeline.py', 'score.py']

# 留白版那五份答案骨架里留的占位词：有它 = 这题还没写。
DEFERRED = '待填'

# 学号式文件名：留白版这一侧只有 answers/ 这一个目录要交代码
ANSWER_DIR = HERE / 'answers'
PROBLEMS = HERE / 'problems'

# 同一份判分脚本两侧都用，所以「参考解那一侧在哪」要自己认出来：
#   lab 那一侧 → 子目录 solutions/<本目录名>/
#   solutions 那一侧 → 就是自己
if HERE.parent.name == 'solutions':
    SOLUTIONS = HERE
else:
    SOLUTIONS = HERE.parent / 'solutions' / HERE.name

# 这一份判分脚本两侧都用，所以先认清楚自己在哪一侧：
#   留白版（学生做的）  = lab/0031-…      → 答案该是骨架、材料该是模板、**不该有**参考解
#   solutions（参考答案）= lab/solutions/0031-…
# 认法就看上一级目录叫什么：进 solutions 只有这一条路。
IS_SOLUTIONS_SIDE = HERE.parent.name == 'solutions'
IS_STARTER = not IS_SOLUTIONS_SIDE

# 参考解装在哪：solutions 那一侧是 reference/；留白版这一侧应该没有。
REFERENCE_DIR = SOLUTIONS / 'reference'


# ── 判分自己内嵌的数据生成：用来核 test_data.py 有没有被改过 ──────────
#
# 这一段**照抄思路、另写一遍**：它不吃 test_data.py，用的是同一批种子。
# 两边逐字节一致，才算「数据是现算的、没有被写死在文件里」。

def gen_case_1():
    import random as _r
    rng = _r.Random(3101)
    out = []
    for _ in range(2000):
        out.append(rng.randint(1, 10000))
    return out


def gen_case_2():
    import random as _r
    rng = _r.Random(3201)
    out = []
    for _ in range(41):
        out.append(rng.randint(1, 10 ** 9))
    return out


def gen_case_3():
    import random as _r
    rng = _r.Random(3303)
    out = []
    for _ in range(200000):
        out.append(rng.randint(1, 300))
    return out


def gen_case_4():
    import random as _r
    rng = _r.Random(3501)
    rows = [''.join(rng.choice('.bb') for _ in range(60)) for _ in range(60)]
    rows[0] = '.' + rows[0][1:]
    rows[-1] = rows[-1][:-1] + '.'
    return rows


def generate_cases():
    """判分自己那一份「现算数据」（只取各组里最要紧的那几组）。"""
    return {
        'p1_case05_a': ' '.join(str(v) for v in gen_case_1()),
        'p2_case05_a': ' '.join(str(v) for v in gen_case_2()),
        'p3_case05_a': ' '.join(str(v) for v in gen_case_3()),
        'p5_case05_grid': '\n'.join(gen_case_4()),
    }


# ── 小工具 ────────────────────────────────────────────────────────────

def read_text(path):
    return path.read_text(encoding='utf-8', errors='replace') if path.is_file() else None


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def short(text, limit=88):
    text = '' if text is None else ' '.join(str(text).split())
    return text if len(text) <= limit else text[:limit] + '…'


def run_python(path, args=(), cwd=None, stdin_text=None, timeout=120):
    """起一个子进程跑一个 .py → (退出码, stdout, stderr)。"""
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    try:
        done = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-u', str(path), *args],
                              cwd=str(cwd or path.parent), input=stdin_text,
                              capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return None, '', '超时（超过 ' + str(timeout) + ' 秒）'
    except Exception as exc:
        return None, '', '起不了子进程：' + type(exc).__name__ + ': ' + str(exc)
    return done.returncode, done.stdout or '', done.stderr or ''


def load_module(path, name):
    """按文件路径载入一个模块（不吃 import 缓存），交回 (模块, 错误文本)。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        return None, name + ' 载入不了'
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None, traceback.format_exc().strip().splitlines()[-1]
    return module, ''


def visible_lines(text):
    rows = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    return [row.rstrip() for row in rows]


def same_output(got, want):
    rows_got = visible_lines(got)
    rows_want = visible_lines(want)
    while rows_got and not rows_got[-1]:
        rows_got.pop()
    while rows_want and not rows_want[-1]:
        rows_want.pop()
    return rows_got == rows_want


def first_difference(got, want):
    rows_got = visible_lines(got)
    rows_want = visible_lines(want)
    for i in range(max(len(rows_got), len(rows_want))):
        a = rows_got[i] if i < len(rows_got) else '（没有这一行）'
        b = rows_want[i] if i < len(rows_want) else '（多出这一行）'
        if a != b:
            return '第 ' + str(i + 1) + ' 行：交回 ' + repr(a[:30]) + '，期望 ' + repr(b[:30])
    return '对的'


def named_fails(stdout, pid, label):
    """FAIL 行里点到这一份材料（`记录` / `讲解稿`）的都算。

    check_timeline.py 的 FAIL 行开头是「记录 p3」/「讲解稿 p3」。
    """
    del pid        # 只看到「哪份材料」就够；题号在消息里已经带了
    head = 'FAIL ' + label
    return [line.strip() for line in stdout.splitlines()
            if line.strip().startswith(head)]


def first_fail(stdout):
    """从一份自检输出里挑出第一条 FAIL（判分用它点名到哪一条丢分）。"""
    for line in stdout.splitlines():
        if line.strip().startswith('FAIL'):
            return line.strip()
    return ''


class Report:
    """把 PASS / FAIL 收起来，最后一起打印。"""

    def __init__(self):
        self.layers = []

    def layer(self, title):
        self.layers.append((title, []))

    def add(self, ok, message):
        self.layers[-1][1].append((bool(ok), message))
        return bool(ok)

    def counts(self):
        rows = [row for _, items in self.layers for row in items]
        return sum(1 for ok, _ in rows if ok), sum(1 for ok, _ in rows if not ok)

    def print(self):
        for title, items in self.layers:
            print('')
            print('── ' + title + ' ' + '─' * max(0, 66 - len(title)))
            for ok, message in items:
                print('  ' + ('PASS ' if ok else 'FAIL ') + message)


# ── 第 1 层 · 流程自检器真的在自检吗 ──────────────────────────────────

def layer1(rep):
    rep.layer('1 · 流程自检器真的在自检吗（check_timeline.py / score.py）')

    for name in PURE_SCRIPTS:
        here = HERE / name
        there = SOLUTIONS / name
        text = read_text(here)
        if text is None:
            rep.add(False, '这一侧少了 ' + name + '——留白版与参考解都要有它')
            continue
        rep.add(FENCE not in text,
                name + ' 的源码里没有连续三个反引号' if FENCE not in text else
                name + ' 的源码里出现了连续三个反引号——会打断阅卷与工具链')
        if there.is_file():
            same = sha256(here) == sha256(there)
            rep.add(same,
                    name + ' 与 solutions 一侧逐字节相同（sha256 ' + str(sha256(here))[:12] + '…）'
                    if same else
                    name + ' 与 solutions 一侧**不一样**：这一份是流程自检器，'
                    '两侧必须同一份（改一份就要同步另一份）')
        # 单跑一次：退出码要有、不许有 Traceback
        code, out, err = run_python(here, cwd=HERE, timeout=120)
        has_traceback = 'Traceback' in (err or '') or 'Traceback' in (out or '')
        rep.add(code is not None and not has_traceback,
                name + ' 单跑没有 Traceback（退出码 ' + str(code) + '）'
                if code is not None and not has_traceback else
                name + ' 单跑出了问题' + ('（超时）' if code is None else '（退出码 ' + str(code) + '）')
                + '：' + short((err or out).strip().splitlines()[-1] if (err or out).strip() else ''))

    data = HERE / 'test_data.py'
    rep.add(data.is_file(), 'test_data.py 在（判分数据由它现算）' if data.is_file()
            else 'test_data.py 不在——没有它就没有判分数据')

    manifest = PROBLEMS / 'manifest.json'
    info = None
    if manifest.is_file():
        try:
            info = json.loads(manifest.read_text(encoding='utf-8'))
        except Exception as exc:
            rep.add(False, 'problems/manifest.json 读不动：' + str(exc))
    else:
        rep.add(False, 'problems/manifest.json 不在——题面与测试数据都要有它')
    if info is not None:
        missing = [pid for pid in PROBLEM_IDS if pid not in info.get('problems', {})]
        rep.add(not missing,
                'manifest.json 里五道题的点数与时限都在（'
                + '、'.join(pid + ' ' + str(info['problems'][pid]['points']) + ' 分'
                           for pid in PROBLEM_IDS if pid in info.get('problems', {})) + '）'
                if not missing else 'manifest.json 里缺这几题：' + '、'.join(missing))
        total = sum(info['problems'][pid]['points'] for pid in PROBLEM_IDS
                    if pid in info.get('problems', {}))
        rep.add(total == info.get('total_points'),
                '五题分值加起来等于 manifest 里的总分 ' + str(total)
                if total == info.get('total_points') else
                '五题分值加起来是 ' + str(total) + '，manifest 写的总分是 '
                + str(info.get('total_points')))
    for pid in PROBLEM_IDS:
        statement = PROBLEMS / pid / 'statement.md'
        sample_in = PROBLEMS / pid / 'samples' / 'sample1.in'
        sample_out = PROBLEMS / pid / 'samples' / 'sample1.out'
        rep.add(statement.is_file() and sample_in.is_file() and sample_out.is_file(),
                pid + ' 的题面与样例齐全（statement.md + samples/sample1.in/out）'
                if statement.is_file() and sample_in.is_file() and sample_out.is_file() else
                pid + ' 少了 ' + '、'.join(name for name, ok in
                                       (('statement.md', statement.is_file()),
                                        ('samples/sample1.in', sample_in.is_file()),
                                        ('samples/sample1.out', sample_out.is_file()))
                                       if not ok))
    for pid in PROBLEM_IDS:
        text = read_text(PROBLEMS / pid / 'statement.md') or ''
        hit = ('数据范围' in text) and ('输入格式' in text) and ('输出格式' in text)
        rep.add(hit, pid + ' 的题面里写到了数据范围、输入格式、输出格式'
                if hit else pid + ' 的题面少了这几样之一：数据范围 / 输入格式 / 输出格式')


# ── 第 2 层 · 判分数据能现算、且每次一样 ─────────────────────────────

def layer2(rep):
    rep.layer('2 · 判分数据能现算、且每次一样')
    path = HERE / 'test_data.py'
    module, error = load_module(path, 'lab31_test_data')
    if module is None:
        rep.add(False, 'test_data.py 载入失败：' + error)
        return None

    try:
        first = module.generate()
    except Exception:
        rep.add(False, 'test_data.generate() 报错：'
                       + short(traceback.format_exc().strip().splitlines()[-1]))
        return None

    shape_ok = set(first.keys()) == set(PROBLEM_IDS)
    rep.add(shape_ok, 'generate() 交回五道题的数据（'
                      + '、'.join(pid + ' ' + str(len(first[pid])) + ' 组'
                                 for pid in PROBLEM_IDS if pid in first) + '）'
            if shape_ok else 'generate() 交回的题号不对：' + '、'.join(sorted(first.keys())))

    second = module.generate()
    same = all(first[pid] == second[pid] for pid in first)
    rep.add(same, '同一份生成器跑两遍交回**同一批**数据（种子固定，判分才可复现）'
            if same else '同一份生成器跑两遍交回的数据不一样——种子里混进了时间或随机源')

    # 判分自己内嵌的那一份，用来分开「现算」与「写死」
    mine = generate_cases()
    got = {}
    for pid, cases in first.items():
        for name, text, _what, _how in cases:
            if pid == 'p1' and name == 'case05':
                got['p1_case05_a'] = text.split('\n')[1]
            if pid == 'p2' and name == 'case05':
                got['p2_case05_a'] = text.split('\n')[1]
            if pid == 'p3' and name == 'case05':
                got['p3_case05_a'] = text.split('\n')[1]
            if pid == 'p5' and name == 'case05':
                got['p5_case05_grid'] = '\n'.join(text.split('\n')[1:61])
    for key in sorted(mine):
        same = got.get(key) == mine[key]
        rep.add(same, key + ' 与判分自己另算一遍的完全一致（' + str(len(mine[key])) + ' 个字符）'
                if same else key + ' 与判分自己另算一遍的对不上——'
                '数据要么被改过、要么种子变了')

    # 每组数据都得有「考什么」这一栏，题面才讲得清
    thin = []
    for pid, cases in first.items():
        for name, text, what, how in cases:
            if len(what) < 6 or not text.strip():
                thin.append(pid + '/' + name)
    rep.add(not thin, '每组数据都写了「这一组在考什么」'
            if not thin else '这几组没写清在考什么：' + '、'.join(thin))
    return first


# ── 第 3 层 · 参考解真的都对吗 ───────────────────────────────────────

def layer3(rep, cases):
    rep.layer('3 · 参考解真的都对吗（每组数据现跑一遍逐字比）')
    ref_dir = REFERENCE_DIR
    if not ref_dir.is_dir():
        # 留白版这一侧**故意不装参考解**：学生先自己写，赛后再看那边。
        rep.add(True, '这一侧没有 reference/（参考解只在 solutions 那一侧），'
                      '这一层按「查不到参考解」跳过——这是留白版正常的样子')
        return None
    if cases is None:
        rep.add(False, '上一层没交出数据，这一层没法判')
        return None

    expected = {}
    for pid in PROBLEM_IDS:
        script = ref_dir / (pid + '.py')
        if not script.is_file():
            rep.add(False, 'reference/' + pid + '.py 不在')
            continue
        info = json.loads((PROBLEMS / 'manifest.json').read_text(encoding='utf-8'))
        timeout = float(info['problems'][pid].get('timeout_seconds', DEFAULT_TIMEOUT))
        rows = cases.get(pid, [])
        bad = []
        for name, text, _what, _how in rows:
            code, out, err = run_python(script, cwd=ref_dir, stdin_text=text,
                                        timeout=max(TIMEOUT_QUICK, timeout))
            if code != 0:
                bad.append(name + '（退出码 ' + str(code) + '：'
                           + short((err or '').strip().splitlines()[-1:] or '', 50) + '）')
                continue
            expected[(pid, name)] = out
        if bad:
            rep.add(False, '参考解 reference/' + pid + '.py 有 ' + str(len(bad))
                           + ' 组没过：' + '；'.join(bad))
        else:
            rep.add(True, '参考解 reference/' + pid + '.py 在全部 ' + str(len(rows))
                          + ' 组数据上都跑通、退出码 0')
    return expected


def layer3b(rep, cases, expected):
    """参考解的输出与 problems/pN/cases 里的期望文件逐字比（判分实际读的就是后者）。"""
    rep.layer('3b · 期望输出文件与参考解现跑的结果一致')
    if cases is None:
        rep.add(False, '上面那层没交出数据，这一层跳过')
        return
    if expected is None:
        rep.add(True, '这一侧没有参考解，这一层按「没法对」跳过'
                      '（solutions 那一侧会真跑一遍）')
        return
    for pid in PROBLEM_IDS:
        folder = PROBLEMS / pid / 'cases'
        if not folder.is_dir():
            rep.add(False, 'problems/' + pid + '/cases 不在（判分数据目录）')
            continue
        rows = cases.get(pid, [])
        bad = []
        for name, text, _what, _how in rows:
            inp = folder / (name + '.in')
            out = folder / (name + '.out')
            if not inp.is_file() or not out.is_file():
                bad.append(name + ' 少了 .in 或 .out')
                continue
            if inp.read_text(encoding='utf-8', errors='replace') != text:
                bad.append(name + '.in 与现算数据不一致')
                continue
            want = out.read_text(encoding='utf-8', errors='replace')
            got = expected.get((pid, name))
            if got is None or not same_output(got, want):
                bad.append(name + ('.out 与参考解现跑的结果不一致：'
                                   + first_difference(got or '', want)))
        rep.add(not bad, 'problems/' + pid + '/cases 里 ' + str(len(rows))
                         + ' 组数据与期望输出都和参考解现跑的一致'
                if not bad else 'problems/' + pid + '/cases 有问题：' + '；'.join(bad[:4]))


# ── 第 4 层 · 判分器与流程自检器抓不抓得住问题 ────────────────────────

def layer4(rep):
    """拿「故意写错的答案」试 score.py：它必须交回非零退出码，而不是一律 PASS。"""
    rep.layer('4 · score.py 抓不抓得住写错的答案')
    script = HERE / 'score.py'
    if not script.is_file():
        rep.add(False, 'score.py 不在')
        return
    ref_dir = REFERENCE_DIR
    if not ref_dir.is_dir():
        rep.add(True, '这一侧没有 reference/，没法试「正确答案应当满分」这一条——跳过')
        return

    # 工作目录自己建、自己删：**不用** TemporaryDirectory 链一个符号链接进去，
    # 免得清理时把 lab 自己的 problems/ 一起删掉。
    work = Path(tempfile.mkdtemp(prefix='lab31_score_'))
    try:
        # score.py 是按**自己所在的目录**找 answers/ 与 problems/ 的，
        # 所以要把它也复制一份到工作目录里跑；直接跑原文件会去判 lab 真正的 answers/。
        (work / 'score.py').write_text(script.read_text(encoding='utf-8'), encoding='utf-8')
        _link_or_copy_tree(PROBLEMS, work / 'problems')
        (work / 'answers').mkdir(exist_ok=True)
        for name in REF_FILES:
            source = ref_dir / name
            if source.is_file():
                (work / 'answers' / name).write_text(
                    source.read_text(encoding='utf-8'), encoding='utf-8')
        code, out, err = run_python(work / 'score.py', cwd=work, timeout=600)
        got_total = _total_of(out)
        rep.add(code == 0 and got_total == 360,
                '拿参考解当答案跑 score.py：退出码 0、总分 ' + str(got_total)
                + ' / 360（30 + 60 + 90 + 100 + 80）'
                if code == 0 and got_total == 360 else
                '拿参考解当答案跑 score.py：退出码 ' + str(code) + '、总分 ' + str(got_total)
                + '（期望 0 与 360）：' + short((err or out).strip().splitlines()[-1:] or ''))

        # 故意写错一道：把 p3 的答案换成「每个询问都交回 0」
        wrong = ('import sys\n'
                 'data = sys.stdin.buffer.read().split()\n'
                 'q = int(data[1])\n'
                 'sys.stdout.write("\\n".join("0" for _ in range(q)) + "\\n")\n')
        (work / 'answers' / 'p3.py').write_text(wrong, encoding='utf-8')
        code2, out2, err2 = run_python(work / 'score.py', cwd=work, timeout=600)
        total2 = _total_of(out2)
        rep.add(code2 not in (0, None) and total2 == 270,
                '把 p3 换成「每个询问都交回 0」：score.py 交出退出码 ' + str(code2)
                + '、总分 ' + str(total2) + '（p3 那 90 分被扣掉，只剩 270）'
                if code2 not in (0, None) and total2 == 270 else
                '把 p3 换成错答案之后，score.py 交出退出码 ' + str(code2) + '、总分 '
                + str(total2) + '（期望非 0 与 270）—— 它必须把错的扣掉')
        rep.add('FAIL' in out2, 'score.py 的输出里点出了 FAIL 的那一组'
                if 'FAIL' in out2 else 'score.py 扣了分，但输出里一条 FAIL 都没有')
    finally:
        import shutil
        # 只删自己建在系统临时目录下的那一个（确认路径真的是临时目录再删）。
        if str(work).startswith(tempfile.gettempdir()):
            shutil.rmtree(work, ignore_errors=True)
        else:
            rep.add(False, '工作目录 ' + str(work) + ' 不在临时目录里，没敢删')


def _copy_tree(source, target):
    import shutil
    shutil.copytree(source, target, dirs_exist_ok=True)


def _link_or_copy_tree(source, target):
    """problems/ 只读，尽量用符号链接（省掉每次 15 MB 的复制）；链不了就复制。"""
    if target.exists():
        return
    try:
        target.symlink_to(source.resolve(), target_is_directory=True)
        return
    except Exception:
        pass
    _copy_tree(source, target)


def _total_of(stdout):
    match = re.search(r'总分：\s*(\d+)\s*/\s*(\d+)', stdout or '')
    return int(match.group(1)) if match else -1


# 故意写坏的材料：check_timeline.py 必须点名到具体哪一条
BAD_TIMELINE = {
    '缺一题的记录': """# 限时解题记录

## p1 · 舞台高度
- 读题用时：8 分钟
- 定下的算法：二分答案，n ≤ 2×10^5、a_i ≤ 10^9，只能 O(n log V)
- 写完时刻：40 分钟
- 自检做了什么：拿样例和 n=1 的边界各试了一遍
- 得分：30 / 30
- 丢分丢在哪：没丢分

## p2 · 四边形合并
- 读题用时：10 分钟
- 定下的算法：区间 DP，n ≤ 300，O(n^3) 装得下
- 写完时刻：110 分钟
- 自检做了什么：拿 n=1、n 为偶数两组边界试过
- 得分：60 / 60
- 丢分丢在哪：没丢分

## p3 · 数颜色
- 读题用时：8 分钟
- 定下的算法：离线 + 树状数组，n、q ≤ 2×10^5
- 写完时刻：205 分钟
- 自检做了什么：只跑了样例
- 得分：0 / 90
- 丢分丢在哪：时间不够，最后没写完

## p5 · 雨天迷宫
- 读题用时：7 分钟
- 定下的算法：0-1 BFS，600×600 = 36 万格，O(N)
- 写完时刻：175 分钟
- 自检做了什么：拿样例 3 试了不可达那一档
- 得分：80 / 80
- 丢分丢在哪：没丢分
""",
    '算法没写数据范围': """# 限时解题记录

## p1 · 舞台高度
- 读题用时：8 分钟
- 定下的算法：二分答案
- 写完时刻：40 分钟
- 自检做了什么：拿样例和 n=1 的边界各试了一遍
- 得分：30 / 30
- 丢分丢在哪：没丢分

## p2 · 四边形合并
- 读题用时：10 分钟
- 定下的算法：区间 DP，n ≤ 300，O(n^3) 装得下
- 写完时刻：110 分钟
- 自检做了什么：拿 n=1、n 为偶数两组边界试过
- 得分：60 / 60
- 丢分丢在哪：没丢分

## p3 · 数颜色
- 读题用时：8 分钟
- 定下的算法：离线 + 树状数组，n、q ≤ 2×10^5
- 写完时刻：205 分钟
- 自检做了什么：只跑了样例
- 得分：0 / 90
- 丢分丢在哪：时间不够，最后没写完

## p4 · 最长公共子串
- 读题用时：6 分钟
- 定下的算法：放弃
- 写完时刻：没写
- 自检做了什么：没有
- 得分：0 / 100
- 丢分丢在哪：预计还要三个多小时，而剩不到一小时，果断跳

## p5 · 雨天迷宫
- 读题用时：7 分钟
- 定下的算法：0-1 BFS，600×600 = 36 万格，O(N)
- 写完时刻：175 分钟
- 自检做了什么：拿样例 3 试了不可达那一档
- 得分：80 / 80
- 丢分丢在哪：没丢分
""",
    '放弃的那题没写依据': """# 限时解题记录

## p1 · 舞台高度
- 读题用时：8 分钟
- 定下的算法：二分答案，n ≤ 2×10^5、a_i ≤ 10^9，只能 O(n log V)
- 写完时刻：40 分钟
- 自检做了什么：拿样例和 n=1 的边界各试了一遍
- 得分：30 / 30
- 丢分丢在哪：没丢分

## p2 · 四边形合并
- 读题用时：10 分钟
- 定下的算法：区间 DP，n ≤ 300，O(n^3) 装得下
- 写完时刻：110 分钟
- 自检做了什么：拿 n=1、n 为偶数两组边界试过
- 得分：60 / 60
- 丢分丢在哪：没丢分

## p3 · 数颜色
- 读题用时：8 分钟
- 定下的算法：离线 + 树状数组，n、q ≤ 2×10^5
- 写完时刻：205 分钟
- 自检做了什么：只跑了样例
- 得分：0 / 90
- 丢分丢在哪：时间不够，最后没写完

## p4 · 最长公共子串
- 读题用时：6 分钟
- 定下的算法：太难了，放弃
- 写完时刻：没写
- 自检做了什么：没有
- 得分：0 / 100
- 丢分丢在哪：这道题做不出来

## p5 · 雨天迷宫
- 读题用时：7 分钟
- 定下的算法：0-1 BFS，600×600 = 36 万格，O(N)
- 写完时刻：175 分钟
- 自检做了什么：拿样例 3 试了不可达那一档
- 得分：80 / 80
- 丢分丢在哪：没丢分
""",
    '还有 TODO 没换': """# 限时解题记录

## p1 · 舞台高度
- 读题用时：TODO
- 定下的算法：二分答案，n ≤ 2×10^5、a_i ≤ 10^9，只能 O(n log V)
- 写完时刻：40 分钟
- 自检做了什么：拿样例和 n=1 的边界各试了一遍
- 得分：30 / 30
- 丢分丢在哪：没丢分

## p2 · 四边形合并
- 读题用时：10 分钟
- 定下的算法：区间 DP，n ≤ 300，O(n^3) 装得下
- 写完时刻：110 分钟
- 自检做了什么：拿 n=1、n 为偶数两组边界试过
- 得分：60 / 60
- 丢分丢在哪：没丢分

## p3 · 数颜色
- 读题用时：8 分钟
- 定下的算法：离线 + 树状数组，n、q ≤ 2×10^5
- 写完时刻：205 分钟
- 自检做了什么：只跑了样例
- 得分：0 / 90
- 丢分丢在哪：时间不够，最后没写完

## p4 · 最长公共子串
- 读题用时：6 分钟
- 定下的算法：放弃
- 写完时刻：没写
- 自检做了什么：没有
- 得分：0 / 100
- 丢分丢在哪：预计还要 3 小时，剩余预算只有 60 分钟，果断跳

## p5 · 雨天迷宫
- 读题用时：7 分钟
- 定下的算法：0-1 BFS，600×600 = 36 万格，O(N)
- 写完时刻：175 分钟
- 自检做了什么：拿样例 3 试了不可达那一档
- 得分：80 / 80
- 丢分丢在哪：没丢分
""",
}

BAD_EXPLAIN = {
    '缺一段': """# 讲解稿

## p1 · 舞台高度
### 解决什么问题
把 n 个观众的偏好高度换算成座位数，找到能让至少 k 个人看清的最大舞台高度。
### 为什么正确
高度越大座位数越少，可行性单调，所以能二分。
### 复杂度怎么推
二分 30 次，每次扫一遍数组，O(n log V)。
### 多大的规模会淘汰它

## p2 · 四边形合并
### 解决什么问题
每次合并连续三堆，求合到一堆的最小代价。
### 为什么正确
按断点枚举两侧的最优，覆盖了所有合法方案。
### 复杂度怎么推
状态 O(n^2)、转移 O(n)，所以 O(n^3)。
### 多大的规模会淘汰它
n 到 2000 就是 8×10^9 次操作，Python 一定超时。

## p3 · 数颜色
### 解决什么问题
每组询问问区间里有多少种不同的颜色。
### 为什么正确
扫到 r 时树状数组里每个颜色只留最后一次出现的位置，区间和就是颜色数。
### 复杂度怎么推
O((n + q) log n)。
### 多大的规模会淘汰它
现场数颜色那一版是 O(nq)，n = q = 2×10^5 时是 4×10^10。

## p4 · 最长公共子串
### 解决什么问题
两个串的最长公共子串长度。
### 为什么正确
二分长度，长度 L 可行则 L-1 也可行。
### 复杂度怎么推
O((n + m) log min(n, m))。
### 多大的规模会淘汰它
DP 版的状态是 O(nm)，n = m = 10^5 时放不下。

## p5 · 雨天迷宫
### 解决什么问题
网格图上从起点到终点的最小代价。
### 为什么正确
边权只有 0 和 1，双端队列保持距离单调，出队即最优。
### 复杂度怎么推
每个点最多进队一次，O(nm)。
### 多大的规模会淘汰它
600×600 = 36 万格还能跑，2000×2000 = 400 万格就很吃力。
""",
    '淘汰规模没有数字': """# 讲解稿

## p1 · 舞台高度
### 解决什么问题
把 n 个观众的偏好高度换算成座位数，找到能让至少 k 个人看清的最大舞台高度。
### 为什么正确
高度越大座位数越少，可行性单调，所以能二分。
### 复杂度怎么推
二分 30 次，每次扫一遍数组，O(n log V)。
### 多大的规模会淘汰它
n 再大很多就装不下了。

## p2 · 四边形合并
### 解决什么问题
每次合并连续三堆，求合到一堆的最小代价。
### 为什么正确
按断点枚举两侧的最优，覆盖了所有合法方案。
### 复杂度怎么推
状态 O(n^2)、转移 O(n)，所以 O(n^3)。
### 多大的规模会淘汰它
n 到 2000 就是 8×10^9 次操作，Python 一定超时。

## p3 · 数颜色
### 解决什么问题
每组询问问区间里有多少种不同的颜色。
### 为什么正确
扫到 r 时树状数组里每个颜色只留最后一次出现的位置，区间和就是颜色数。
### 复杂度怎么推
O((n + q) log n)。
### 多大的规模会淘汰它
现场数颜色那一版是 O(nq)，n = q = 2×10^5 时是 4×10^10。

## p4 · 最长公共子串
### 解决什么问题
两个串的最长公共子串长度。
### 为什么正确
二分长度，长度 L 可行则 L-1 也可行。
### 复杂度怎么推
O((n + m) log min(n, m))。
### 多大的规模会淘汰它
DP 版的状态是 O(nm)，n = m = 10^5 时放不下。

## p5 · 雨天迷宫
### 解决什么问题
网格图上从起点到终点的最小代价。
### 为什么正确
边权只有 0 和 1，双端队列保持距离单调，出队即最优。
### 复杂度怎么推
每个点最多进队一次，O(nm)。
### 多大的规模会淘汰它
600×600 = 36 万格还能跑，2000×2000 = 400 万格就很吃力。
""",
    '还有 TODO': """# 讲解稿

## p1 · 舞台高度
### 解决什么问题
把 n 个观众的偏好高度换算成座位数，找到能让至少 k 个人看清的最大舞台高度。
### 为什么正确
高度越大座位数越少，可行性单调，所以能二分。
### 复杂度怎么推
二分 30 次，每次扫一遍数组，O(n log V)。
### 多大的规模会淘汰它
n 到 10^7 还能跑，再大就要换别的做法。

## p2 · 四边形合并
### 解决什么问题
每次合并连续三堆，求合到一堆的最小代价。
### 为什么正确
TODO
### 复杂度怎么推
状态 O(n^2)、转移 O(n)，所以 O(n^3)。
### 多大的规模会淘汰它
n 到 2000 就是 8×10^9 次操作，Python 一定超时。

## p3 · 数颜色
### 解决什么问题
每组询问问区间里有多少种不同的颜色。
### 为什么正确
扫到 r 时树状数组里每个颜色只留最后一次出现的位置，区间和就是颜色数。
### 复杂度怎么推
O((n + q) log n)。
### 多大的规模会淘汰它
现场数颜色那一版是 O(nq)，n = q = 2×10^5 时是 4×10^10。

## p4 · 最长公共子串
### 解决什么问题
两个串的最长公共子串长度。
### 为什么正确
二分长度，长度 L 可行则 L-1 也可行。
### 复杂度怎么推
O((n + m) log min(n, m))。
### 多大的规模会淘汰它
DP 版的状态是 O(nm)，n = m = 10^5 时放不下。

## p5 · 雨天迷宫
### 解决什么问题
网格图上从起点到终点的最小代价。
### 为什么正确
边权只有 0 和 1，双端队列保持距离单调，出队即最优。
### 复杂度怎么推
每个点最多进队一次，O(nm)。
### 多大的规模会淘汰它
600×600 = 36 万格还能跑，2000×2000 = 400 万格就很吃力。
""",
}


def layer5(rep):
    """拿故意写坏的材料试 check_timeline.py：它必须点名到哪一条丢分。"""
    rep.layer('5 · check_timeline.py 抓不抓得住写坏的材料')
    script = HERE / 'check_timeline.py'
    if not script.is_file():
        rep.add(False, 'check_timeline.py 不在')
        return
    good_timeline = read_text(SOLUTIONS / 'timeline.md')
    good_explain = read_text(SOLUTIONS / 'explain.md')
    if good_timeline is None or good_explain is None:
        rep.add(False, 'solutions 一侧少了 timeline.md 或 explain.md（填好的示例）')
        return

    with tempfile.TemporaryDirectory(prefix='lab31_check_') as work:
        work = Path(work)
        target_script = work / 'check_timeline.py'
        target_script.write_text(script.read_text(encoding='utf-8'), encoding='utf-8')
        (work / 'timeline.md').write_text(good_timeline, encoding='utf-8')
        (work / 'explain.md').write_text(good_explain, encoding='utf-8')
        code, out, _err = run_python(target_script, cwd=work, timeout=120)
        rep.add(code == 0 and '条 FAIL' in out and '0 条 FAIL' in out,
                '拿**填好的**那份记录与讲解稿跑：退出码 0、0 条 FAIL'
                if code == 0 and '0 条 FAIL' in out else
                '拿填好的那份跑，退出码是 ' + str(code) + '，没到 0 条 FAIL：'
                + short(out.splitlines()[-1] if out.splitlines() else ''))

        for title, text in BAD_TIMELINE.items():
            (work / 'timeline.md').write_text(text, encoding='utf-8')
            (work / 'explain.md').write_text(good_explain, encoding='utf-8')
            code, out, _err = run_python(target_script, cwd=work, timeout=120)
            named = named_fails(out, 'p1', '记录')
            rep.add(code not in (0, None) and bool(named),
                    '把记录改成「' + title + '」：退出码 ' + str(code) + '，点名到「'
                    + short(named[0], 60) + '」'
                    if code not in (0, None) and named else
                    '把记录改成「' + title + '」：退出码 ' + str(code)
                    + '，但 FAIL 里没有一条点到「记录 pN」（第一条 FAIL 是「'
                    + short(first_fail(out), 40) + '」）')

        for title, text in BAD_EXPLAIN.items():
            (work / 'timeline.md').write_text(good_timeline, encoding='utf-8')
            (work / 'explain.md').write_text(text, encoding='utf-8')
            code, out, _err = run_python(target_script, cwd=work, timeout=120)
            named = named_fails(out, 'p1', '讲解稿')
            rep.add(code not in (0, None) and bool(named),
                    '把讲解稿改成「' + title + '」：退出码 ' + str(code) + '，点名到「'
                    + short(named[0], 60) + '」'
                    if code not in (0, None) and named else
                    '把讲解稿改成「' + title + '」：退出码 ' + str(code)
                    + '，但 FAIL 里没有一条点到「讲解稿 pN」（第一条 FAIL 是「'
                    + short(first_fail(out), 40) + '」）')


# ── 第 6 层 · 留白版留下的是不是「还没做的痕迹」 ─────────────────────

def layer6(rep):
    """留白版这一侧：答案还没交、模板还在、题面与样例都在。"""
    rep.layer('6 · 留白版留下的是不是「还没做的痕迹」')
    count = 0
    unanswered = 0
    for name in REF_FILES:
        path = ANSWER_DIR / name
        if not path.is_file():
            rep.add(False, 'answers/' + name + ' 不在——五道题各要一个答案文件')
            continue
        count += 1
        text = read_text(path) or ''
        if DEFERRED in text:
            unanswered += 1
        forbidden = []
        if re.search(r'^\s*(?:from|import)\s+(?:p[1-5]|reference|answer|tools)\b',
                     text, re.M):
            forbidden.append('import 了参考解那边的模块')
        if 'solutions' in text or 'reference/' in text:
            forbidden.append('提到了 solutions / reference 这个目录——答案要独立成篇')
        rep.add(not forbidden,
                'answers/' + name + ' 是一份独立的答案（没有转手去要参考解）'
                if not forbidden else
                'answers/' + name + ' 里 ' + '、'.join(forbidden)
                + ' —— 这一课要的是你自己写的那份')
    if count == len(REF_FILES):
        rep.add(True, '五道题的答案文件都在（answers/p1.py … p5.py）')
    if IS_STARTER:
        if unanswered == len(REF_FILES):
            rep.add(True, '五份答案都还是骨架（都留着「' + DEFERRED + '」）——'
                          '这就是留白版该有的样子')
        elif unanswered:
            rep.add(True, '有 ' + str(len(REF_FILES) - unanswered) + ' 份答案已经动过，'
                          + str(unanswered) + ' 份还是骨架')
        else:
            rep.add(False, '五份答案都看不出是骨架——留白版这一侧不该有写好的答案')
    else:
        same = []
        for name in REF_FILES:
            left = ANSWER_DIR / name
            right = REFERENCE_DIR / name
            same.append(left.is_file() and right.is_file()
                        and left.read_bytes() == right.read_bytes())
        rep.add(all(same), 'solutions 这一侧 answers/ 里放的就是 reference/ 里那五份参考解'
                if all(same) else
                'solutions 这一侧 answers/ 与 reference/ 对不上：'
                + '、'.join(name for name, ok in zip(REF_FILES, same) if not ok))

    # 两份文字材料的模板必须在，而且要留着待填的 TODO
    for name in ('timeline_template.md', 'explain_template.md'):
        path = HERE / name
        text = read_text(path)
        rep.add(text is not None and 'TODO' in text,
                name + ' 在，而且留着待填的 TODO' if text is not None and 'TODO' in text
                else (name + ' 不在' if text is None else name + ' 里一个 TODO 都没有——'
                      '模板要留出要填的位置'))
    score_text = read_text(HERE / 'score.py') or ''
    rep.add('score.json' in score_text and 'answers' in score_text,
            'score.py 读 answers/ 并把逐组结果写进 score.json'
            if 'score.json' in score_text and 'answers' in score_text else
            'score.py 里看不到 answers/ 或 score.json —— 判分脚本的接口不能改名')

    # 这一侧**不许**躺着参考解：参考解只在 solutions 那一侧。
    # 注意：REFERENCE_DIR 指的是 solutions 那一侧的位置，所以
    # 「留白版这一侧有没有参考解」要看**本目录**，不能看 REFERENCE_DIR。
    if not IS_STARTER:
        rep.add(REFERENCE_DIR.is_dir(),
                '这是 solutions 那一侧：reference/ 就在这里'
                if REFERENCE_DIR.is_dir() else
                'solutions 那一侧少了 reference/ —— 参考解应该在这里')
    elif (HERE / 'reference').is_dir():
        leaked = sorted(f.name for f in (HERE / 'reference').glob('*.py'))
        rep.add(False, '这一侧出现了 reference/（' + '、'.join(leaked)
                       + '）——参考解本来就不该在留白版里，学生先自己写')
    else:
        rep.add(True, '这一侧没有 reference/：参考解只在 solutions 那一侧')
    missing = []
    for pid in PROBLEM_IDS:
        folder = PROBLEMS / pid
        for need in ('statement.md', 'samples/sample1.in', 'samples/sample1.out'):
            if not (folder / need).is_file():
                missing.append(pid + '/' + need)
    rep.add(not missing, '五道题的题面与样例都在' if not missing
            else '缺这些文件：' + '、'.join(missing[:6]))
    return unanswered


def layer7(rep):
    """这一课真正要交的两份材料：这一侧要是待填的模板，solutions 一侧要是填好的。"""
    rep.layer('7 · 这一课要交的两份材料（timeline.md / explain.md）')
    script = HERE / 'check_timeline.py'
    for name in ('timeline.md', 'explain.md'):
        here = read_text(HERE / name)
        there = read_text(SOLUTIONS / name)
        if here is None:
            rep.add(False, '这一侧少了 ' + name + '——要交的就是它（先按模板起一份）')
        elif not IS_STARTER:
            rep.add(True, '这是 solutions 那一侧：' + name + ' 就该是填好的那一份（'
                          + str(len(here.splitlines())) + ' 行）')
        else:
            blanks = here.count('TODO') + here.count(DEFERRED)
            rep.add(blanks > 0,
                    name + ' 在（' + str(len(here.splitlines())) + ' 行，'
                    + str(blanks) + ' 处还没填）'
                    if blanks > 0 else
                    name + ' 里一处待填都没有——这一课要交的是**你填的**记录，'
                    '不是抄来的示例')
        if not IS_STARTER:
            continue
        if there is None:
            rep.add(False, 'solutions 一侧少了填好的 ' + name
                           + '——参考解要交一份完整的示例')
        else:
            rep.add(True, 'solutions 一侧有填好的 ' + name + '（'
                          + str(len(there.splitlines())) + ' 行）')
    if IS_STARTER:
        # 留白版：拿**这一侧**的材料跑一遍流程自检，必须报出「还没填」。
        # 这一条是这一课真正要判的东西——所以它必须 FAIL，
        # 否则就说明「还没做」被当成了「做完了」。
        work = Path(tempfile.mkdtemp(prefix='lab31_layer7_starter_'))
        try:
            (work / 'check_timeline.py').write_text(script.read_text(encoding='utf-8'),
                                                    encoding='utf-8')
            (work / 'timeline.md').write_text(read_text(HERE / 'timeline.md') or '',
                                              encoding='utf-8')
            (work / 'explain.md').write_text(read_text(HERE / 'explain.md') or '',
                                             encoding='utf-8')
            code, out, _err = run_python(work / 'check_timeline.py', cwd=work, timeout=120)
            named = [line.strip() for line in out.splitlines()
                     if line.strip().startswith('FAIL')]
            rep.add(code not in (0, None) and bool(named),
                    '拿这一侧的材料跑流程自检：退出码 ' + str(code) + '、'
                    + str(len(named)) + ' 条 FAIL，每条都点名到「记录 pN / 讲解稿 pN」'
                    '—— 这就是这一课要你补的东西'
                    if code not in (0, None) and named else
                    '拿这一侧还没填的材料跑流程自检，居然过了（退出码 ' + str(code)
                    + '）——那说明「还没做」被当成了「做完了」，判分器有问题')
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)
    if script.is_file() and (SOLUTIONS / 'timeline.md').is_file() \
            and (SOLUTIONS / 'explain.md').is_file():
        work = Path(tempfile.mkdtemp(prefix='lab31_layer7_'))
        try:
            (work / 'check_timeline.py').write_text(script.read_text(encoding='utf-8'),
                                                    encoding='utf-8')
            (work / 'timeline.md').write_text(read_text(SOLUTIONS / 'timeline.md'),
                                              encoding='utf-8')
            (work / 'explain.md').write_text(read_text(SOLUTIONS / 'explain.md'),
                                             encoding='utf-8')
            code, out, _err = run_python(work / 'check_timeline.py', cwd=work, timeout=120)
            rep.add(code == 0 and '0 条 FAIL' in out,
                    '拿 solutions 那份填好的材料跑流程自检：退出码 0、0 条 FAIL'
                    if code == 0 and '0 条 FAIL' in out else
                    '拿 solutions 那份材料跑流程自检：退出码 ' + str(code)
                    + '，最后一行是 ' + short(out.strip().splitlines()[-1:], 70))
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)


# ── 主流程 ────────────────────────────────────────────────────────────

def _starter_fail_lines():
    """拿**这一侧**的 timeline.md / explain.md 跑一遍流程自检，交回它的 FAIL 行。

    留白版的「还没做」就体现在这里：run_tests.py 自己那一层全是 PASS
    （脚手架是好的），而流程自检会指名道姓地说「记录 p3：这几格空着没填」。
    """
    script = HERE / 'check_timeline.py'
    if not script.is_file():
        return ['（check_timeline.py 不在，跑不了流程自检）']
    work = Path(tempfile.mkdtemp(prefix='lab31_starter_'))
    try:
        (work / 'check_timeline.py').write_text(script.read_text(encoding='utf-8'),
                                                encoding='utf-8')
        (work / 'timeline.md').write_text(read_text(HERE / 'timeline.md') or '',
                                          encoding='utf-8')
        (work / 'explain.md').write_text(read_text(HERE / 'explain.md') or '',
                                         encoding='utf-8')
        _code, out, _err = run_python(work / 'check_timeline.py', cwd=work, timeout=120)
        return [line.strip() for line in out.splitlines()
                if line.strip().startswith('FAIL')]
    finally:
        import shutil
        if str(work).startswith(tempfile.gettempdir()):
            shutil.rmtree(work, ignore_errors=True)


def main():
    quick = '--quick' in sys.argv
    print('=' * 72)
    print('lab 0031 · 自动判分（实验四：一次完整的赛前模拟）  ' + HERE.name)
    print('=' * 72)
    rep = Report()
    layer1(rep)
    cases = layer2(rep)
    expected = layer3(rep, cases)
    layer3b(rep, cases, expected)
    layer4(rep)
    layer5(rep)
    unanswered = layer6(rep)
    layer7(rep)
    rep.print()

    passed, failed = rep.counts()
    print('')
    print('=' * 72)
    print('脚手架本身：共 ' + str(passed) + ' 条 PASS、' + str(failed) + ' 条 FAIL')
    if IS_STARTER and unanswered:
        # 留白版：脚手架是好的，没做的是**内容**。所以这里要报的是
        # 流程自检对**这一侧的材料**给出的那几条 FAIL——那正是这一课要判的东西。
        print('')
        print('还没做的部分（这一课要判的就是这些）：')
        for line in _starter_fail_lines():
            print('  ' + line)
        print('')
        print(str(unanswered) + ' / 5 道题的答案还没有交（answers/p1.py … p5.py 还是骨架）。')
        print('先把四件事做完：')
        print('  1) 通读五道题、填那张「耗时 / 分值 / 复杂度上限」的表（15 分钟，不写代码）')
        print('  2) 定顺序并写下理由（之后不再改）')
        print('  3) 限时 4 小时走一遍，边做边填 timeline.md')
        print('  4) 写 explain.md 并复盘：换一种顺序能多拿几分')
        print('')
        print('这一侧**没有**参考解（reference/ 在 solutions 那一侧）：先自己写，')
        print('写完了再去对那一侧。上面那些「记录 pN：这几格空着没填」'
        '「讲解稿 pN：这几段几乎是空的」')
        print('正是这一课要交的东西，不是脚手架坏了——脚手架这一侧 0 条 FAIL。')
        print('跑分：py score.py    流程自检：py check_timeline.py')
        return 1
    print('接着跑：py score.py（跑答案算分）与 py check_timeline.py（查两份材料）')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
