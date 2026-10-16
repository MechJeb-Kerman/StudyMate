#!/usr/bin/env python3
"""lab 0006 · 自动判分：跑六个任务脚本，比对输出。

用法（在 lab/0006-python-io-and-debug/ 目录里）：

    py run_tests.py

判法：
  - 每个任务单独起一个进程跑，只看 stdout 里的固定格式行，**不 import 学生代码**
    （唯一例外是任务 6 的 same_output：判分把它交给一个探针进程 import 一次，
    拿几组只差末尾换行、只差一个空格的文本试它，看它是不是真的在逐字比）；
  - 任务 1 按格式各起一次进程，把对应的样例文件接到标准输入上，比数据的结构
    （与课件写死的产出逐字一致：单行多整数 [3, 1, 4, 1, 5, 9, 2, 6]、
    多行整数 [3, -1, 4, 2, 7]、矩阵 [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]、
    混合 [(1, 1), (3, 4)]、多组 [[1, 2, 3], [10, 20, 30, 40]]）；
  - 任务 2 是这一课的要害：**同一份数、只把换行位置换掉**（sample3 整齐 / sample6 折行），
    「边读边算」版在折行上打出 36（正确是 78），「先读完再算」版两版都必须是 78；
  - 任务 5 会**改一处学生代码里的提示**（把 clean 版临时替换成带提示的版本），
    看判分还能不能验出 stdout 被污染 —— 也就是说这条检查本身要有效。

退出码：0 = 六个任务都通过；1 = 还有没通过的。
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

TIMEOUT = 60

# 三个「形状固定」的产出的对照表：任务 1 各格式的期望行（前缀 → 期望值）
EXPECT = {
    'one': [('01 单行多整数', '[3, 1, 4, 1, 5, 9, 2, 6]')],
    'lines': [('02 多行整数', '[3, -1, 4, 2, 7]')],
    'matrix': [
        ('03 矩阵 n m 3 4', None),   # 前缀式取行，见下
    ],
    'mq': [],
    'groups': [('05 多组数据', '[[1, 2, 3], [10, 20, 30, 40]]')],
}

MATRIX_GRID = '[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]'


# ── 跑脚本 ────────────────────────────────────────────────────────────────

def run_script(name, args=(), stdin_text=None, timeout=TIMEOUT):
    """跑一个脚本 → dict(status, out, err, note)。状态：ok / missing / crash / timeout。"""
    path = HERE / name
    if not path.is_file():
        return {'status': 'missing', 'out': '', 'err': '',
                'note': '还没建这个文件：' + name}
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    try:
        done = subprocess.run(
            [sys.executable, str(path)] + list(args),
            cwd=str(HERE), env=env, timeout=timeout,
            input=stdin_text,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'out': '', 'err': '',
                'note': '跑了 ' + str(timeout) + ' 秒还没结束（死循环？在等输入？）'}
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-5:])
        return {'status': 'crash', 'out': done.stdout or '', 'err': done.stderr or '',
                'note': '脚本报错退出（退出码 ' + str(done.returncode) + '）：\n' + tail}
    return {'status': 'ok', 'out': done.stdout or '', 'err': '', 'note': ''}


def run_with_sample(name, args, sample):
    """把某个样例文件接到标准输入上跑。"""
    path = HERE / sample
    if not path.is_file():
        return {'status': 'missing', 'out': '', 'err': '',
                'note': '判分用的样例不在了：' + sample + '（别删 sample*.in）'}
    return run_script(name, args=args,
                      stdin_text=path.read_text(encoding='utf-8', errors='replace'))


def run_plain(name, args=()):
    """跑一个不读输入的脚本（标准输入给空）。"""
    return run_script(name, args=args, stdin_text='')


def short(value, limit=90):
    text = str(value)
    return text if len(text) <= limit else text[:limit] + '…'


def get_line(out, prefix):
    """按前缀取出一整行剩下的内容；没打到那一行就返回 None。"""
    for line in out.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def get_line_exact(out, label):
    """按「标签 + 一个空格」取一整行，标签后面紧跟空格才算。

    用来区分互相是前缀的标签：'03 矩阵' 与 '03 矩阵 n m'。
    """
    prefix = label + ' '
    for line in out.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def got_labels(out):
    """把「01 xxx」这样的行拆成 {编号: 后面的内容}。"""
    seen = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split(' ', 1)
        seen[parts[0]] = parts[1].strip() if len(parts) > 1 else ''
    return seen


# ── 任务 1 · 五种格式各解析一次 ──────────────────────────────────────────

TASK1_CASES = [
    # (格式名, 样例文件, 期望整行, 对不上时的提示)
    ('one', 'sample1.in', '01 单行多整数 [3, 1, 4, 1, 5, 9, 2, 6]',
     'TODO 2：整份输入按空白切分（text.split()）之后，token 表里全是字符串，'
     '要逐个转成 int。'),
    ('lines', 'sample2.in', '02 多行整数 [3, -1, 4, 2, 7]',
     'TODO 3：按行切分用 splitlines()；先取第一行的 n，再取它后面 n 行；'
     '空行会被切成空字符串，int(\'\') 报 ValueError，所以要筛掉。'),
    ('matrix', 'sample3.in',
     '03 矩阵 [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]',
     'TODO 4：先把 n、m 取出来，再把 n*m 个数取成一段 vals，'
     '第 i 行是 vals[i*m:(i+1)*m]（切片右端不包含）。别按行切开。'),
    ('mq', 'sample4.in',
     '04 矩阵与查询 [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]',
     'TODO 5：用一个显式下标变量（pos）一段一段往前推；'
     '矩阵那段按上面的办法切，然后读 q，再循环 q 次各读两个数配成元组。'),
    ('groups', 'sample5.in',
     '05 多组数据 [[1, 2, 3], [10, 20, 30, 40]]',
     'TODO 6：第一行是组数 t；每组先读一行 n，再读 n 个数；'
     '读完一组别忘了让下标推过那 n 个数。空行按空白切分时什么都不用做。'),
]


def find_line(out, want):
    """输出里有没有与 want 逐字相同的一行。"""
    for line in out.splitlines():
        if line.strip() == want:
            return True
    return False


def probe_lines(out, prefix):
    """取出所有以 prefix 开头的行（用来在 FAIL 里显示实际打出了什么）。"""
    return [line for line in out.splitlines() if line.startswith(prefix)]


def task1(report):
    for which, sample, want, hint in TASK1_CASES:
        run = run_with_sample('task1_parse.py', [which], sample)
        if run['status'] != 'ok':
            report.check(False, sample + ' 上没跑通：' + run['note'])
            continue
        if find_line(run['out'], want):
            report.check(True, sample + ' → ' + short(want))
            continue
        shown = probe_lines(run['out'], want.split(' ', 2)[0] + ' ') or run['out'].splitlines()
        report.check(False, sample + ' 期望这一行：\n  ' + want + '\n实际打出：\n  '
                      + '\n  '.join(short(x) for x in shown[:3])
                      + '\n带 print 的行是判分接口，别改；要写的是 TODO 那几段。\n' + hint)

    # 任务 1 的两个附加检查：混合的查询、矩阵的 n m
    run = run_with_sample('task1_parse.py', ['mq'], 'sample4.in')
    if run['status'] == 'ok':
        queries = get_line(run['out'], '04 查询')
        if queries == '[(1, 1), (3, 4)]':
            report.check(True, 'sample4.in → 04 查询 [(1, 1), (3, 4)]（元组的列表）')
        else:
            report.check(False, 'sample4.in 的查询打出 ' + short(queries)
                          + '，期望 [(1, 1), (3, 4)]\n'
                          'TODO 5：查询要配成元组再 append 进列表，'
                          '每一组读两个数（行列），不要读成一个。')

    run = run_with_sample('task1_parse.py', ['matrix'], 'sample3.in')
    if run['status'] == 'ok':
        nm = get_line(run['out'], '03 矩阵 n m')
        if nm == '3 4':
            report.check(True, 'sample3.in → 03 矩阵 n m 3 4')
        else:
            report.check(False, 'sample3.in 的 n m 打出 ' + short(nm) + '，期望 3 4\n'
                          'TODO 4：n、m 是 token 表的前两个，别忘了先转 int。')

    # 折行组：矩阵必须按空白读，不能按行切开
    run = run_with_sample('task1_parse.py', ['matrix'], 'sample6.in')
    if run['status'] != 'ok':
        report.check(False, 'sample6.in（折行）上没跑通：' + run['note'])
    elif find_line(run['out'], '03 矩阵 ' + MATRIX_GRID):
        report.check(True, 'sample6.in（同一份数、换行位置被打乱）→ 03 矩阵 与 '
                      'sample3.in 完全一致：按空白读不受排版影响')
    else:
        report.check(False, 'sample6.in（折行）打出 ' + short(probe_lines(run['out'], '03 矩阵'))
                      + '，期望与 sample3.in 相同的 ' + short(MATRIX_GRID) + '\n'
                      '这一组与 sample3.in 是同一份数、只是换行位置不同。'
                      '按行切开会读出 [[1, 2, 3, 4], [5, 6], [7, 8]] —— '
                      'TODO 4 要用「按空白读再按 m 个一段切开」的写法。')


# ── 任务 2 · 先读完、再算（这一课的要害）────────────────────────────────

def task2(report):
    # 对照：边读边算版在折行数据上静默算错（36），在整齐数据上是对的（78）
    run = run_with_sample('task2_read_then_compute.py', ['running'], 'sample3.in')
    if run['status'] == 'ok':
        value = get_line(run['out'], '边读边算')
        if value == '78':
            report.check(True, '对照：边读边算版在 sample3.in（整齐）上得 78——它是对的')
        else:
            report.check(False, '对照：边读边算版在 sample3.in 上打出 ' + short(value)
                          + '，期望 78\n这一段是给好的对照，别改它。')
    run = run_with_sample('task2_read_then_compute.py', ['running'], 'sample6.in')
    if run['status'] != 'ok':
        report.check(False, '对照：边读边算版在 sample6.in 上没跑通：' + run['note'])
    else:
        value = get_line(run['out'], '边读边算')
        if value == '36':
            report.check(True, '对照：同一份数折行之后，边读边算版打出 36'
                          '（正确答案是 78）——而且它一个错字都没报')
        elif value == '78':
            report.check(False, '对照版在 sample6.in 上也打出 78 了：'
                          'sum_rows_running 是给好的「边读边算」对照，别改它——'
                          '它按 input() 逐行读，折行版应当少读一段、打出 36。')
        else:
            report.check(False, '对照版在 sample6.in 上打出 ' + short(value)
                          + '，期望 36（错的答案，正是要看的现象）')

    # TODO 2：先读完再算，两种排版都要 78
    for sample in ('sample3.in', 'sample6.in'):
        run = run_with_sample('task2_read_then_compute.py', ['tokens'], sample)
        if run['status'] != 'ok':
            report.check(False, sample + ' 上没跑通：' + run['note'])
            continue
        value = get_line(run['out'], '先读完再算')
        if value == '78':
            report.check(True, 'TODO 2：' + sample + ' → 先读完再算 78')
        else:
            report.check(False, 'TODO 2：' + sample + ' 打出 ' + short(value)
                          + '，期望 78\n'
                          'text.split() 只认空白、不区分空白长什么样，所以换行怎么排都不影响；'
                          '矩阵的第 i 行是从 token 表上按 m 个一段切出来的，'
                          '切的位置由 n、m 决定，与换行无关。')

    # TODO 3：解析函数 + 算法两段
    for sample in ('sample3.in', 'sample6.in'):
        run = run_with_sample('task2_read_then_compute.py', ['parsed'], sample)
        if run['status'] != 'ok':
            report.check(False, sample + '（parsed）没跑通：' + run['note'])
            continue
        grid = get_line(run['out'], '解析后求和')
        lengths = get_line(run['out'], '每行长度')
        nm = get_line(run['out'], '解析 n m')
        if nm != '3 4':
            report.check(False, 'TODO 3：' + sample + ' 的「解析 n m」打出 ' + short(nm)
                          + '，期望 3 4')
            continue
        if lengths != '[4, 4, 4]':
            report.check(False, 'TODO 3：' + sample + ' 的「每行长度」打出 ' + short(lengths)
                          + '，期望 [4, 4, 4]\n'
                          '每行应当是 m 个数；少了就是切片右端写错（切片右端不包含）。')
            continue
        if grid != '78':
            report.check(False, 'TODO 3：' + sample + ' 的「解析后求和」打出 ' + short(grid)
                          + '，期望 78')
            continue
        report.check(True, 'TODO 3：' + sample + ' → n m 3 4、每行长度 [4, 4, 4]、求和 78')


# ── 任务 3 · 读进来的都是字符串 ─────────────────────────────────────────

TASK3_WANT = [
    ('01 字符串 10 < 9', 'True',
     'TODO 1：直接比两个字符串就是 \'10\' < \'9\'。字符串按字符逐个比编码，'
     '\'1\' 是 49、\'9\' 是 57，第一位就分出大小了。'),
    ('02 字符串 2 < 10', 'False',
     'TODO 1：\'2\' 的编码 50 比 \'1\' 的 49 大，所以是 False。'),
    ('03 直接排序', "['10', '100', '2', '9']",
     'TODO 2：直接 sorted(raw) 排的是字符串，\'100\' 排在 \'2\' 前面。'),
    ('04 按整数排序', "['2', '9', '10', '100']",
     'TODO 2：要按数值排就得指定「按什么排」——sorted(raw, key=int)。'),
    ('05 字符串最大值', '9',
     'TODO 3：max(raw) 在字符串上比，取回的是 \'9\'（打印出来不带引号）。'),
    ('06 转整数后最大值', '100',
     'TODO 3：先转成整数再求最大才是 100——和上一行的 9 不是一个答案。'),
    ('07 混着比的报错类型', 'TypeError',
     'TODO 4：\'10\' < 5 报 TypeError；用 try / except 接住，'
     '用 type(e).__name__ 拿到类名。'),
    ('08 解析层转完', '[31, 9, 100]',
     'TODO 5：token 表进来、整数列表出去——在解析层一次转完，算法层就看不到数字字符串。'),
]


def task3(report):
    run = run_plain('task3_string_trap.py')
    if run['status'] != 'ok':
        report.check(False, 'task3_string_trap.py 没跑通：' + run['note'])
        return
    for prefix, expect, hint in TASK3_WANT:
        value = get_line(run['out'], prefix)
        if value is None:
            report.check(False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删')
            continue
        if value != expect:
            report.check(False, prefix + ' 打出 ' + short(value) + '，期望 ' + short(expect)
                          + '\n' + hint)
            continue
        report.check(True, prefix + ' ' + short(expect))


# ── 任务 4 · 用打印缩小出错范围 ─────────────────────────────────────────

DIAG_ROW_RE = re.compile(r'^诊断 第 (\d+) 行长度 (\d+) (\[.*\])$')


def task4(report):
    # TODO 1：把切片改对（sample3 上每行应当是 4 个）
    run = run_with_sample('task4_debug.py', ['diagnose'], 'sample3.in')
    if run['status'] != 'ok':
        report.check(False, 'task4_debug.py diagnose 没跑通：' + run['note'])
        return
    nm = get_line(run['out'], '诊断 n m')
    if nm != '3 4':
        report.check(False, 'TODO 2：没看到「诊断 n m 3 4」这一行（现在打出 ' + short(nm)
                      + '）\n诊断要打印题面给的 n 与 m，前缀别改。')
    else:
        report.check(True, 'TODO 2：诊断打出了「诊断 n m 3 4」——这就是定位的起点')

    rows = [m.groups() for m in (DIAG_ROW_RE.match(l) for l in run['out'].splitlines()) if m]
    if len(rows) != 3:
        report.check(False, 'TODO 2：诊断要按行打出三行「诊断 第 i 行长度 L [内容]」'
                      '（现在认得出 ' + str(len(rows)) + ' 行）\n'
                      '提示：for i, row in enumerate(a) 拿行号，配 len(row) 与 row。')
    else:
        lengths = [int(r[1]) for r in rows]
        if lengths == [4, 4, 4]:
            report.check(True, 'TODO 2：三行「诊断 第 i 行长度」都是 4')
        else:
            report.check(False, 'TODO 2：三行的长度打出 ' + str(lengths)
                          + '，期望 [4, 4, 4]\n'
                          '先别急着改切片——让这一行把「行长度是 3、而 n m 说该有 4 个数」'
                          '打出来，结论自己就浮出来了。')

    total = get_line(run['out'], '诊断 总和')
    if total is None:
        report.check(False, 'TODO 2：没看到「诊断 总和 …」这一行')
    else:
        report.check(True, 'TODO 2：诊断打出了「诊断 总和 ' + short(total) + '」——'
                      '它和「诊断 n m」一起就是定位的全部依据')

    # TODO 1：修好之后每行 4 个、总和 78
    fixed_len = get_line(run['out'], '修复后 每行长度')
    fixed_sum = get_line(run['out'], '修复后 总和')
    if fixed_len == '[4, 4, 4]' and fixed_sum == '78':
        report.check(True, 'TODO 1：切片改对之后每行长度 [4, 4, 4]、总和 78')
    elif fixed_len != '[4, 4, 4]':
        report.check(False, 'TODO 1：修复后每行长度打出 ' + short(fixed_len)
                      + '，期望 [4, 4, 4]\n'
                      '切片右端不包含：要取 m 个数，右端得写成 (i + 1) * m。')
    else:
        report.check(False, 'TODO 1：修复后总和打出 ' + short(fixed_sum) + '，期望 78')

    # TODO 3：repr 看不可见字符
    run = run_with_sample('task4_debug.py', ['repr'], 'sample1.in')
    if run['status'] != 'ok':
        report.check(False, 'task4_debug.py repr 没跑通：' + run['note'])
        return
    value = get_line(run['out'], '原文 repr')
    want = r"'3 1 4 1 5 9 2 6\n'"
    if value is None:
        report.check(False, 'TODO 3：没看到「原文 repr …」这一行')
    elif value == want:
        report.check(True, 'TODO 3：原文 repr 打出 ' + value
                      + '——引号与末尾的 \\n 都现出来了')
    else:
        report.check(False, 'TODO 3：原文 repr 打出 ' + short(value) + '，期望 ' + want + '\n'
                      'repr() 会把引号与换行显示成 \\n；这里要交回**第一行原文**的 repr。'
                      '空行的 ValueError 就是靠它一眼分清读到的是 \\n 还是空串。')


# ── 任务 5 · 提示混进标准输出（判分自己也要能验出来）────────────────────

PROMPT_POLLUTION = '请输入'


def task5(report):
    # 干净版：标准输出逐字就是答案
    run = run_script('task5_clean_stdout.py', args=['clean'], stdin_text='10\n')
    if run['status'] != 'ok':
        report.check(False, 'task5_clean_stdout.py clean 没跑通：' + run['note'])
        return
    out = run['out']
    if out == '20\n':
        report.check(True, 'TODO 1：clean 版的标准输出逐字是「20\\n」——'
                      'input() 没带提示、print 只打印答案')
    elif out.strip() == '20':
        report.check(False, 'TODO 1：clean 版打出的值是对的，但标准输出是 ' + repr(out)
                      + '，多了一个换行/别的字符\n'
                      '评测机逐字比对：标准输出要恰好是答案那一行。')
    else:
        report.check(False, 'TODO 1：clean 版的标准输出是 ' + repr(out) + '，期望「20\\n」\n'
                      '读一个整数 N、打印 N*2；input() 括号里不写参数，'
                      'print 里也不要加前缀。')

    # 脏版：标准输出里出现了不该有的东西
    run = run_script('task5_clean_stdout.py', args=['dirty'], stdin_text='10\n')
    if run['status'] != 'ok':
        report.check(False, 'task5_clean_stdout.py dirty 没跑通：' + run['note'])
    else:
        out = run['out']
        polluted = (PROMPT_POLLUTION in out) or (out.strip() != '20')
        if polluted and '20' in out:
            report.check(True, 'TODO 2：dirty 版的标准输出是 ' + repr(out)
                          + '——答案还在，但混进了别的东西，逐字比对就会失败')
        elif out.strip() == '20':
            report.check(False, 'TODO 2：dirty 版的标准输出也是干净的 ' + repr(out) + '\n'
                          '这一版的用途就是把两个错都犯上：input() 带提示'
                          '（提示会写进标准输出）、print 加与答案无关的前缀。')
        else:
            report.check(False, 'TODO 2：dirty 版的标准输出是 ' + repr(out)
                          + '，连答案 20 都看不到了')

    # 判分自己的有效性证明：把 clean 临时换成带提示的版本，检查必须能抓到
    src = HERE / 'task5_clean_stdout.py'
    text = src.read_text(encoding='utf-8', errors='replace')
    marker = 'def clean():'
    index = text.find(marker)
    if index < 0:
        report.check(False, '在 task5_clean_stdout.py 里找不到 def clean()：'
                      '函数名与文件名是判分接口，别改。')
        return
    head = text[:index]
    tail_lines = text[index:].splitlines(keepends=True)
    # 找到 clean 的函数体范围（到下一个顶格 def 或文件末尾）
    body_end = len(tail_lines)
    for i, line in enumerate(tail_lines[1:], 1):
        if line.startswith('def ') or line.startswith('# ══'):
            body_end = i
            break
    patched = (head
               + 'def clean():\n'
               + '    n = int(input("请输入 N："))\n'
               + '    print(n * 2)\n\n\n'
               + ''.join(tail_lines[body_end:]))
    tmp = HERE / '_probe_task5.py'
    try:
        tmp.write_text(patched, encoding='utf-8')
        run = run_script('_probe_task5.py', args=['clean'], stdin_text='10\n')
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    if run['status'] != 'ok':
        report.check(False, '探针没跑成：' + run['note'])
        return
    probe_out = run['out']
    if probe_out != '20\n' and '20' in probe_out:
        report.check(True, '探针：把 clean 换成带提示的版本之后，标准输出变成了 '
                      + repr(probe_out) + ' —— 这一课的检查确实能验出 stdout 被污染')
    elif probe_out == '20\n':
        report.check(False, '探针：带提示的版本居然也打出干净的 ' + repr(probe_out) + '\n'
                      'input() 的提示走的是标准输出（官方文档：stdout 用于 print() 的输出'
                      '以及用于 input() 的提示符），提示会紧贴在答案前面。')
    else:
        report.check(False, '探针：带提示的版本打出 ' + repr(probe_out) + '，连答案都没了')


# ── 任务 6 · 提交前的两个搜索与一次逐字比对 ─────────────────────────────

PROBE_SAME_OUTPUT = r'''
import json
import sys

sys.path.insert(0, sys.argv[1])
import importlib.util

spec = importlib.util.spec_from_file_location("m6", sys.argv[2])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

cases = [
    ("78\n", "78\n", True, "完全相同"),
    ("78\n", "78", True, "只差末尾那一个换行（文件末尾的约定，要放过）"),
    ("78", "78\n", True, "反过来只差末尾换行（也要放过）"),
    ("78 \n", "78\n", False, "行尾多一个空格（逐字比对要抓）"),
    ("78\n", "78\n79\n", False, "少一行"),
    ("78\n79\n", "78\n", False, "多一行"),
    ("答案 78\n", "78\n", False, "多了一个与答案无关的前缀"),
    ("78\n", " 78\n", False, "行首多一个空格"),
]
out = []
for actual, expected, want, why in cases:
    try:
        got = mod.same_output(actual, expected)
    except Exception as exc:                 # noqa: BLE001
        out.append([why, None, want, type(exc).__name__ + ': ' + str(exc)])
        continue
    out.append([why, bool(got), want, ""])
print(json.dumps(out, ensure_ascii=False))
'''


def task6(report):
    run = run_plain('task6_submit_check.py')
    if run['status'] != 'ok':
        report.check(False, 'task6_submit_check.py 没跑通：' + run['note'])
        return

    # 给好的四行自检
    inline = [
        ('01 完全相同', 'True'),
        ('02 末尾换行', 'True'),
        ('03 行尾多空格', 'False'),
        ('04 少一行', 'False'),
    ]
    for prefix, expect in inline:
        value = get_line(run['out'], prefix)
        if value is None:
            report.check(False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删')
        elif value != expect:
            report.check(False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                          + '\n提示：两边都按 splitlines() 切成行列表再比 —— '
                          '行内与行数的差别都会保留，而末尾那一个换行是文件约定、要放过。')
        else:
            report.check(True, prefix + ' ' + expect)

    # TODO 2：两个搜索关键词
    value = get_line(run['out'], '05 搜两个关键词')
    if value is None:
        report.check(False, '没看到「05 搜两个关键词 …」这一行')
    else:
        ok = ("'input('" in value and "'print('" in value)
        if ok:
            report.check(True, 'TODO 2：两个关键词 ' + short(value))
        else:
            report.check(False, 'TODO 2：搜两个关键词打出 ' + short(value)
                          + '，期望 [\'input(\', \'print(\']\n'
                          '就是课件那两条规矩对应的两个函数名加左括号：'
                          '一个会把提示写进标准输出，一个是打印本身。')

    # 探针：拿八组只差一个字符/一行的文本试 same_output
    probe = HERE / '_probe_task6.py'
    try:
        probe.write_text(PROBE_SAME_OUTPUT, encoding='utf-8')
        run = run_plain('_probe_task6.py', args=[str(HERE), str(HERE / 'task6_submit_check.py')])
    finally:
        try:
            probe.unlink()
        except OSError:
            pass
    if run['status'] != 'ok':
        report.check(False, '探针没跑成：' + run['note'])
        return
    import json as _json
    try:
        results = _json.loads(run['out'].strip().splitlines()[-1])
    except (ValueError, IndexError):
        report.check(False, '探针读不到结果：' + short(run['out']))
        return
    wrong = [r for r in results if r[1] != r[2]]
    if not wrong:
        report.check(True, '探针：八组文本（含只差末尾换行、只差一个空格、多一行、'
                      '多一个前缀）逐组都对上了——same_output 真的在做逐字比对')
        return
    details = '\n'.join('  · ' + w[0] + '：交回 ' + str(w[1]) + '，期望 ' + str(w[2])
                        + (('（' + w[3] + '）') if w[3] else '')
                        for w in wrong[:4])
    report.check(False, '探针：same_output 有 ' + str(len(wrong)) + ' 组不对：\n' + details
                  + '\n提示：别用 strip() 把两边的空白都抹掉 —— 那样「末尾多一个换行」'
                  '与「行尾多一个空格」就都抓不出来了；两边都 splitlines() 再比。')


# ── 入口 ──────────────────────────────────────────────────────────────────

class Report:
    def __init__(self, title):
        self.title = title
        self.lines = []
        self.failed = 0

    def check(self, ok, message):
        self.lines.append(('PASS' if ok else 'FAIL', message))
        if not ok:
            self.failed += 1

    def passed(self):
        return self.failed == 0 and bool(self.lines)

    def show(self):
        print(self.title)
        for kind, message in self.lines:
            for index, piece in enumerate(message.split('\n')):
                head = '  ' + kind + '  ' if index == 0 else '        '
                print(head + piece)
        print()


def main():
    print('StudyMate lab 0006 · 自动判分（读完输入再动手）')
    print('目录：' + str(HERE))
    print()

    tasks = [
        ('任务 1 · 五种格式各解析一次（task1_parse.py）', task1),
        ('任务 2 · 先读完再算：换行换了，答案不能变（task2_read_then_compute.py）', task2),
        ('任务 3 · 读进来的都是字符串（task3_string_trap.py）', task3),
        ('任务 4 · 用打印缩小出错范围（task4_debug.py）', task4),
        ('任务 5 · 提示混进标准输出（task5_clean_stdout.py）', task5),
        ('任务 6 · 提交前的两个搜索与一次逐字比对（task6_submit_check.py）', task6),
    ]
    reports = []
    for title, fn in tasks:
        report = Report(title)
        try:
            fn(report)
        except Exception as exc:             # noqa: BLE001
            report.check(False, '判分这一层自己出错了：' + type(exc).__name__ + ': ' + str(exc))
        report.show()
        reports.append((title, report))

    print('─' * 60)
    done = [name for name, rep in reports if rep.passed()]
    undone = [name for name, rep in reports if not rep.passed()]
    print('六个任务：' + str(len(done)) + ' 个通过，' + str(len(undone)) + ' 个还没过')
    if undone:
        print('没过的：')
        for name in undone:
            print('  · ' + name)
        print('卡住了先读 ../README.md 的「卡壳顺序」：读错误信息 → 自己跑一遍 → '
              '看 FAIL 行 → 再对线索。')
        return 1
    print('六个任务都过了。现在去对照 ../solutions/0006-python-io-and-debug/：')
    print('比一比你的写法与参考解，再回答一句「哪一行决定了折行数据算不算得对」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
