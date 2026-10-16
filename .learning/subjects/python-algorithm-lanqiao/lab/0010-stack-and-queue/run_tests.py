#!/usr/bin/env python3
"""lab 0010 · 自动判分：跑五个任务脚本，比对固定格式行。

用法（在 lab/0010-stack-and-queue/ 目录里）：

    py run_tests.py

判法：
  - 每个任务单独起一个进程跑，只看 stdout 里的固定格式行，不 import 学生代码；
  - 计数行（`计数 NN 标签 值`）、耗时行（`耗时 NN 标签 k=… 秒`）、倍数行
    （`倍数 NN 标签 值`）是判分接口，按两位编号取，编号与前缀都对得上才算；
  - **两个结构靠参照模型验**：任务 1 里栈与列表的 append/pop、队列与 deque 的
    append/popleft 在 300 步随机操作上逐步对照，一步一步都要一样；
  - **两个结构靠对拍验**：任务 3 的 is_valid 与 first_error 在九个用例上对照、
    任务 4 的两种求值在课件那几组表达式上对照、任务 5 的单调队列与暴力版对拍；
  - **耗时看趋势不看常数**：出队那一列只要求 popleft 比 pop(0) 快 20 倍以上；
    窗口最大值那一列只要求暴力版在 k 变大时明显变慢、单调队列那一列基本不动；
  - 任务 5 另有一条：漏掉队首过期检查的错版必须在 [7, 1, 1, 1, 1]、k = 3 上
    给出 [7, 7, 7]（与暴力的 [7, 1, 1] 不同）——这正是「该弹必须弹」的证据。

退出码：0 = 五个任务都通过；1 = 还有没通过的。
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMEOUT = 240
WINDOW_TIMEOUT = 300

TASKS = [
    ('任务 1 · 用列表写栈，用 deque 写队列', 'task1_stack_queue.py', None),
    ('任务 2 · 两种出队的代价', 'task2_queue_cost.py', None),
    ('任务 3 · 括号匹配与第一个错位', 'task3_brackets.py', None),
    ('任务 4 · 表达式求值（后缀一遍、中缀两栈）', 'task4_eval.py', None),
    ('任务 5 · 滑动窗口最大值（单调队列）', 'task5_window_max.py', None),
]


# ── 跑脚本 ────────────────────────────────────────────────────────────────

def run_script(name, timeout=TIMEOUT):
    """跑一个脚本 → dict(status, out, note)。状态：ok / missing / crash / timeout。"""
    path = HERE / name
    if not path.is_file():
        return {'status': 'missing', 'out': '', 'note': '还没建这个文件：' + name}
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    try:
        done = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(HERE), env=env, timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'out': '',
                'note': '跑了 ' + str(timeout) + ' 秒还没结束（死循环？）'}
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-5:])
        return {'status': 'crash', 'out': done.stdout or '',
                'note': ('脚本报错退出（退出码 ' + str(done.returncode) + '）：\n' + tail)}
    return {'status': 'ok', 'out': done.stdout or '', 'note': ''}


# ── 读输出 ────────────────────────────────────────────────────────────────

def get_line(out, prefix):
    """按前缀取一整行剩下的内容；没打到那一行就返回 None。"""
    for line in out.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def get_lines(out, prefix):
    return [line[len(prefix):].strip() for line in out.splitlines() if line.startswith(prefix)]


def count_value(out, index):
    """取 `计数 NN 标签 值` 里的值（只按编号找）。"""
    for entry in get_lines(out, '计数 ' + index + ' '):
        parts = entry.split()
        if len(parts) >= 2:
            return parts[-1]
    return None


def time_values(out, index):
    """取 `耗时 NN 标签 k=… 秒` 里的 (k, 秒数)；同一编号可能有多行。"""
    values = []
    for entry in get_lines(out, '耗时 ' + index + ' '):
        match = re.search(r'k=(\d+)\s+([\d.]+)', entry)
        if match:
            values.append((int(match.group(1)), float(match.group(2))))
    return values


def ratio_values(out, index):
    """取 `倍数 NN 标签 值` 里的倍数（同一编号可能有多行）。"""
    values = []
    for entry in get_lines(out, '倍数 ' + index + ' '):
        parts = entry.split()
        if parts:
            try:
                values.append(float(parts[-1]))
            except ValueError:
                pass
    return values


def short(text, limit=60):
    text = '' if text is None else str(text)
    return text if len(text) <= limit else text[:limit] + '…'


def parse_list(text):
    """把 '[3, 3, 5]' 解析成 [3, 3, 5]；解析不了交回 None。"""
    if text is None:
        return None
    body = text.strip()
    if not (body.startswith('[') and body.endswith(']')):
        return None
    inner = body[1:-1].strip()
    if not inner:
        return []
    out = []
    for piece in inner.split(','):
        try:
            out.append(int(piece.strip()))
        except ValueError:
            return None
    return out


# ── 任务 1 · 栈与队列 ─────────────────────────────────────────────────────

def check_task1():
    run = run_script('task1_stack_queue.py')
    if run['status'] != 'ok':
        return [(False, 'task1_stack_queue.py 没跑通：' + run['note'])]
    checks = []

    want = [
        ('栈 与参照模型一致', 'True', '栈的出栈顺序与「列表 append 后逐个 pop」的参照模型一致'),
        ('栈 出栈是入栈的反序', 'True', '出栈顺序正好是入栈顺序的反序——后进先出'),
        ('队列 与入队顺序相同', 'True', '出队顺序与入队顺序完全相同——先进先出'),
        ('随机 300 步 栈顶与模型一致', 'True', '300 步随机操作里，每一步的栈顶都与参照模型一致'),
        ('随机 300 步 队头与模型一致', 'True', '300 步随机操作里，每一步的队头都与参照模型一致'),
        ('随机 300 步 出栈顺序与模型一致', 'True', '300 步之后整体出栈，顺序仍与模型一致'),
        ('随机 300 步 出队顺序与模型一致', 'True', '300 步之后整体出队，顺序仍与模型一致'),
    ]
    for prefix, expect, good in want:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：先看 TODO 1 的 pop() 有没有真的交回取出来的元素、'
                             'TODO 2 的 dequeue() 是不是用了 popleft'))

    empty = get_line(run['out'], '空栈 pop 报错类型')
    if empty is None:
        checks.append((False, '没看到「空栈 pop 报错类型 …」这一行：带 print 的行别改、别删'))
    elif empty.startswith('IndexError') and 'pop from empty list' in empty:
        checks.append((True, '空栈上 pop 抛出 IndexError: pop from empty list（所以要先判空）'))
    else:
        checks.append((False, '空栈 pop 报错类型 打出 ' + short(empty)
                       + '，期望 IndexError: pop from empty list：'
                         'TODO 1 的 pop() 要写成 self._data.pop()，让空栈自然报错'))

    for index, expect, label in [('01', '30', '栈 出栈'), ('02', '150', '栈 随机步数'),
                                 ('03', '150', '队列 随机步数')]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))
    return checks


# ── 任务 2 · 两种出队的代价 ───────────────────────────────────────────────

def check_task2():
    run = run_script('task2_queue_cost.py')
    if run['status'] != 'ok':
        return [(False, 'task2_queue_cost.py 没跑通：' + run['note'])]
    checks = []

    same = get_line(run['out'], '两种写法的出队顺序一致')
    left = get_line(run['out'], '两种写法取完的元素个数')
    list_times = time_values(run['out'], '01')
    deque_times = time_values(run['out'], '02')

    # 计时真的量到了：留白版两行都是 0.000000
    for name, values, index in [('pop(0)', list_times, '01'), ('popleft', deque_times, '02')]:
        if not values:
            checks.append((False, '没看到「耗时 ' + index + ' ' + name + ' …」这一行：'
                                  'TODO ' + ('1' if index == '01' else '2')
                                  + ' 的循环还没写（这一行现在是 0.000000）'))
        elif values[0][1] <= 0:
            checks.append((False, name + ' 那一行的秒数是 0.000000：'
                           + 'TODO ' + ('1' if index == '01' else '2')
                           + ' 的循环还没写，或者计时那两行被挪到循环里面了'))
        elif values[0][0] != 200000:
            checks.append((False, name + ' 那一行的规模是 k=' + str(values[0][0])
                           + '，期望 k=200000：出队次数由 N 决定，别改'))
        else:
            checks.append((True, name + '：200000 次出队的耗时量到了（'
                           + f'{values[0][1]:.6f}' + ' 秒）'))

    if same == 'True' and left == '200000 200000':
        checks.append((True, '两种写法交回的元素个数都是 200000，顺序也一致——'
                             '两个循环做的是同一件事'))
    elif same == 'True':
        checks.append((False, '两种写法的顺序一致，但「取完的元素个数」打出 ' + short(left)
                       + '，期望 200000 200000：有一个循环没出队完就停了'))
    else:
        checks.append((False, '两种写法的出队顺序一致 打出 ' + short(same) + '，期望 True：'
                       '列表那一版要用 pop(0)、deque 那一版要用 popleft，'
                       '两个都是从**左端**取'))

    # 趋势：popleft 比 pop(0) 快 20 倍以上
    pair = get_line(run['out'], 'deque 比列表快')
    speed = None
    if pair:
        head = pair.split()[0]
        try:
            speed = float(head)
        except ValueError:
            speed = None
    timed_ok = bool(list_times and deque_times and list_times[0][1] > 0 and deque_times[0][1] > 0)
    if speed is None:
        checks.append((False, '没读到「deque 比列表快 … 倍」这一行'))
    elif not timed_ok:
        checks.append((False, '耗时的秒数还没量到真数（有一行是 0.000000）：'
                              '先把两个 TODO 的循环写出来，这一条倍数才有意义'))
    elif speed >= 20:
        checks.append((True, 'deque 比列表快 ' + f'{speed:.1f}'
                             + ' 倍——列表每次出队都要挪动后面的元素（O(n)），deque 两端都是 O(1)'))
    else:
        checks.append((False, 'deque 只比列表快 ' + f'{speed:.1f}' + ' 倍，期望 20 倍以上：'
                       '确认列表那一版写的是 pop(0)、deque 那一版写的是 popleft，'
                       '而且计时没有把两个循环混在一起'))

    ratio = ratio_values(run['out'], '03')
    timed_ok = bool(list_times and list_times[0][1] > 0)
    if not ratio:
        checks.append((False, '没看到「倍数 03 …」这一行'))
    elif not timed_ok:
        checks.append((False, '倍数还没意义（列表那一行的秒数是 0.000000）：先写 TODO 1'))
    elif ratio[-1] <= 1:
        checks.append((True, '倍数 03 ' + f'{ratio[-1]:.2f}'
                             + '：deque 的秒数比列表小，这个比值小于 1（两条计时各量各的）'))

    value = count_value(run['out'], '01')
    if value == 'True':
        checks.append((True, '计数 01 两种写法出队个数一致'))
    elif value is None:
        checks.append((False, '没看到「计数 01 …」这一行'))
    else:
        checks.append((False, '计数 01 打出 ' + short(value) + '，期望 True'))
    return checks


# ── 任务 3 · 括号匹配 ─────────────────────────────────────────────────────

VALID_WANT = [
    ('()[]{}', True), ('([)]', False), ('(]', False), ('((', False), ('()', True), ('', True),
    ('([{}])', True), (')))', False), ('(()', False),
]
ERROR_WANT = [
    ('()[]{}', -1), ('([)]', 2), ('(]', 1), ('((', 0), ('()', -1), ('', -1),
    ('([{}])', -1), (')))', 0), ('(()', 0),
]


def check_task3():
    run = run_script('task3_brackets.py')
    if run['status'] != 'ok':
        return [(False, 'task3_brackets.py 没跑通：' + run['note'])]
    checks = []

    rows = {}
    for line in run['out'].splitlines():
        if not line.startswith('用例 '):
            continue
        # 行格式：用例 <用 repr 打出来的文本> <is_valid> <first_error>
        # repr 让空文本也占一个词（打成 ''），所以按空格切词总能得到三段。
        parts = line[len('用例 '):].split()
        if len(parts) == 3:
            rows[parts[0].strip("'")] = (parts[1], parts[2])
    if not rows:
        return [(False, '没看到「用例 …」这几行：带 print 的行别改、别删')]

    bad_valid = []
    for text, want in VALID_WANT:
        got = rows.get(text)
        if got is None:
            bad_valid.append(text + '（这一行没打出来）')
        elif got[0] != str(want):
            bad_valid.append(text + '→' + got[0])
    if not bad_valid:
        checks.append((True, '九个用例的 is_valid 全部对上（含空文本、([)]、(] 、(( 这三组反例）'))
    else:
        checks.append((False, 'is_valid 有 ' + str(len(bad_valid)) + ' 组不对：'
                       + short('、'.join(bad_valid))
                       + '：TODO 1 要写「右括号时先看栈空不空、再看栈顶对不对，'
                         '读完 return not st」'))

    bad_err = []
    for text, want in ERROR_WANT:
        got = rows.get(text)
        if got is None:
            bad_err.append(text + '（这一行没打出来）')
        elif got[1] != str(want):
            bad_err.append(text + '→' + got[1] + '（期望 ' + str(want) + '）')
    if not bad_err:
        checks.append((True, '九个用例的 first_error 全部对上：(((' + ' 报 0（栈最底下那个左括号），'
                             + '([)] 报 2，(] 报 1，正确的报 -1'))
    else:
        checks.append((False, 'first_error 有 ' + str(len(bad_err)) + ' 组不对：'
                       + short('、'.join(bad_err))
                       + '：三种情形各自要交回哪个下标，见任务文件那张表；'
                         '左括号没等到时交回的是栈**最底下**那个的下标（st[0]，不是 st[-1]）'))

    for prefix, expect, good, hint in [
        ('一组用例里配对正确的个数', '4', '九个用例里有 4 个配对正确（()[]{} 、() 、空文本、([{}])）',
         '正确个数是 4；对不上说明 is_valid 在某一组上判反了'),
        ('校验 前六个用例逐字对照', 'True', '前六个用例的真假与课件那六组逐字一致',
         '课件那六组期望 True/False/False/False/True/True'),
        ('校验 后三个用例逐字对照', 'True', '后三个用例的首个错位与期望一致（-1 / 0 / 0）',
         '([{}]) 正确给 -1；))) 第一个字符就多余给 0；((( 是左括号没等到、给最底下那个的下标 0'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect + '：' + hint))

    for index, expect, label in [('01', '4', '配对正确个数'),
                                 ('02', '0', '(() 的首个错位'),
                                 ('03', '1', '(]  的首个错位')]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))
    return checks


# ── 任务 4 · 表达式求值 ───────────────────────────────────────────────────

RPN_WANT = {'34+2*': '14', '12+': '3', '93/': '3', '56+7*': '77', '52-3+': '6'}
MID_WANT = {'12+3': '15', '(1+2)*3': '9', '12*3+4': '40', '9-3+2': '8',
            '9-3-2': '4', '4*5-6/3': '18'}


def check_task4():
    run = run_script('task4_eval.py')
    if run['status'] != 'ok':
        return [(False, 'task4_eval.py 没跑通：' + run['note'])]
    checks = []

    rpn = {}
    mid = {}
    for line in run['out'].splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0] == '后缀':
            rpn[parts[1]] = parts[2]
        elif len(parts) == 3 and parts[0] == '中缀':
            mid[parts[1]] = parts[2]
    if not rpn:
        return [(False, '没看到「后缀 …」这几行：带 print 的行别改、别删')]

    bad = []
    for text, want in RPN_WANT.items():
        if rpn.get(text) != want:
            bad.append(text + '→' + str(rpn.get(text)))
    if not bad:
        checks.append((True, '后缀五组全部对上：34+2*=14、12+=3、93/=3、56+7*=77、52-3+=6'))
    else:
        checks.append((False, '后缀有 ' + str(len(bad)) + ' 组不对：' + short('、'.join(bad))
                       + '：TODO 1 里先弹出的是**右**操作数（b = st.pop() 再 a = st.pop()），'
                         '减法是 a - b'))

    if not mid:
        checks.append((False, '没看到「中缀 …」这几行'))
    else:
        bad_mid = []
        for text, want in MID_WANT.items():
            if mid.get(text) != want:
                bad_mid.append(text + '→' + str(mid.get(text)))
        if not bad_mid:
            checks.append((True, '中缀六组全部对上：含括号、(1+2)*3=9、9-3+2=8（同优先级从左往右）'))
        else:
            checks.append((False, '中缀有 ' + str(len(bad_mid)) + ' 组不对：'
                           + short('、'.join(bad_mid))
                           + '：TODO 2b 的优先级比较要用 >=（同优先级先算左边那个），'
                             '遇到右括号要把运算符栈弹到左括号为止'))

    for prefix, expect, good, hint in [
        ('后缀 五组全部对上', 'True', '后缀那一列的整体校验为 True（五组一个都没错）',
         '这一行比对的是五组后缀表达式各自的答案'),
        ('后缀 减法与除法没有写反', 'True', '52- 给 3、93/ 给 3：弹出顺序没写反',
         '写反了 52- 会变 -3、93/ 会变 0；要 b = st.pop() 先弹、a = st.pop() 后弹，算 a - b'),
        ('中缀 六组全部对上', 'True', '中缀那一列的整体校验为 True（六组一个都没错）',
         '含括号与同优先级的两组最容易错'),
        ('中缀 同优先级从左往右', 'True', '9-3+2 给 8、9-3-2 给 4：同优先级运算符从左往右算',
         'PRIORITY[栈顶] >= PRIORITY[t] 才是从左往右；写成 > 会把 9-3+2 算成 4'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect + '：' + hint))

    for prefix, expect in [('切分 (12+3)*4', "['(', 12, '+', 3, ')', '*', 4]"),
                           ('切分 7', '[7]')]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, prefix + ' ' + expect + '：多位数字被收成一个元素了'))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 2a 要把连续的数字攒成一个整数（12 应当是一个元素、不是两个）'))

    for index, label in [('01', '后缀 全部对上'), ('02', '中缀 全部对上'), ('03', '两种都算对')]:
        value = count_value(run['out'], index)
        if value == 'True':
            checks.append((True, '计数 ' + index + ' ' + label + ' True'))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 True'))
    return checks


# ── 任务 5 · 滑动窗口最大值 ───────────────────────────────────────────────

def check_task5():
    run = run_script('task5_window_max.py', timeout=WINDOW_TIMEOUT)
    if run['status'] != 'ok':
        return [(False, 'task5_window_max.py 没跑通：' + run['note'])]
    checks = []

    want = [
        ('课件数据 k=3 单调队列', '[3, 3, 5, 5, 6, 7]',
         '课件那一组 [1, 3, -1, -3, 5, 3, 6, 7]、k=3 的输出与课件逐字一致'),
        ('课件数据 k=3 暴力', '[3, 3, 5, 5, 6, 7]', '暴力版在同一组数据上给出同一个答案'),
        ('过期检查 k=3 暴力', '[7, 1, 1]', '暴力版在 [7, 1, 1, 1, 1]、k=3 上给出 [7, 1, 1]'),
        ('过期检查 k=3 漏检查版', '[7, 7, 7]',
         '漏掉队首过期检查的错版从第二个窗口起就错：它把早就滑出窗口的 7 一直当答案'),
        ('排列 20 个数 k=20', '[19]', 'k 等于数组长度时只有一个窗口，最大值是 19'),
    ]
    for prefix, expect, good in want:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 1 的三条要按顺序写（先弹队尾、再入队、再弹队首过期、'
                             '最后 i >= k - 1 时输出）；TODO 2 只去掉队首那一条'))

    for prefix, good, hint in [
        ('课件数据 与暴力一致', '单调队列版与暴力版在课件那一组上一致',
         '两版必须在同一组数据上给出同一个列表'),
        ('过期检查 k=3 单调队列', '单调队列版在 [7, 1, 1, 1, 1] 上给出 [7, 1, 1]',
         '这一行期望 [7, 1, 1]：7 滑出窗口之后就不能再当答案'),
        ('漏检查版与暴力不同', '漏检查版与暴力版不同——这正是「队首过期检查不能省」的证据',
         '这一行期望 True：漏掉过期检查会给 [7, 7, 7]，与暴力的 [7, 1, 1] 不同；'
         '打出 False 说明 TODO 2 写成正确版了'),
        ('排列 20 个数 与暴力一致', 'k=4 时单调队列版与暴力版一致',
         '排列里每个数出现一次，两版必须一致'),
        ('排列 20 个数 k=1', 'k=1 时每个窗口只有一个元素，输出就是数组本身',
         '这一行期望 True：k=1 时输出应当与数组逐项相同'),
        ('随机 2000 个数 k=37 与暴力一致', '有正有负的 2000 个数、k=37 上两版一致',
         '随机数据上更要两版一致'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif prefix == '过期检查 k=3 单调队列':
            got = parse_list(value)
            if got == [7, 1, 1]:
                checks.append((True, good))
            else:
                checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 [7, 1, 1]：' + hint))
        elif value == 'True':
            # 「一致/不同」类的行在留白版上可能碰巧成立（空表与空表一致、空表与暴力不同），
            # 先看被依赖的那几行对不对，这一条才有意义。
            if prefix == '课件数据 与暴力一致' and get_line(run['out'], '课件数据 k=3 暴力') != '[3, 3, 5, 5, 6, 7]':
                checks.append((False, prefix + ' 是 True，但暴力版那一行还没对：先让暴力那两行对上'))
            elif prefix == '漏检查版与暴力不同' and get_line(run['out'], '过期检查 k=3 漏检查版') != '[7, 7, 7]':
                checks.append((False, prefix + ' 是 True，但「过期检查 k=3 漏检查版」打出的是 '
                               + short(get_line(run['out'], '过期检查 k=3 漏检查版'))
                               + '，不是 [7, 7, 7]：空表与 [7, 1, 1] 当然不同，'
                                 '可那不是这一条要看的东西；先按 TODO 2 把漏检查的版本写对'))
            elif prefix == '随机 2000 个数 k=37 与暴力一致' and get_line(run['out'], '课件数据 与暴力一致') != 'True':
                checks.append((False, prefix + ' 是 True，但课件那一组还没对上：'
                               '先把 TODO 1 写对，这一条才有意义'))
            else:
                checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 True：' + hint))

    value = get_line(run['out'], '排列 20 个数 窗口个数')
    if value == '17':
        checks.append((True, '20 个数的数组、k=4 应当有 17 个窗口（n - k + 1）'))
    elif value is None:
        checks.append((False, '没看到「排列 20 个数 窗口个数 …」这一行'))
    else:
        checks.append((False, '窗口个数打出 ' + short(value) + '，期望 17：'
                       'i >= k - 1 那一句管的就是「第一个窗口凑满了才开始输出」'))

    for index, expect, label in [('01', 'True', '课件数据一致'),
                                 ('02', 'True', '漏检查版不同'),
                                 ('03', 'True', '窗口 2000 个数一致'),
                                 ('04', 'True', '四个 k 答案一致')]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))

    both = get_line(run['out'], '四个 k 上答案都与暴力一致')
    counts = get_line(run['out'], '同一规模上两个版本的答案个数')
    if both == 'True' and counts == '[19901, 19501, 19001, 18001]':
        checks.append((True, 'k = 100 / 500 / 1000 / 2000 四档上输出都与暴力一致（窗口个数也对）'))
    elif both == 'True':
        checks.append((False, '四个 k 上输出与暴力一致，但窗口个数打出 ' + short(counts)
                       + '，期望 [19901, 19501, 19001, 18001]'))
    else:
        checks.append((False, '四个 k 上答案都与暴力一致 打出 ' + short(both) + '，期望 True：'
                       '大数组上更要与暴力版一致'))

    wn = [seconds for _, seconds in time_values(run['out'], '01')]
    bf = [seconds for _, seconds in time_values(run['out'], '02')]
    if len(wn) == 4 and len(bf) == 4:
        if all(s <= 0 for s in wn) or all(s <= 0 for s in bf):
            checks.append((False, '四档耗时的秒数全是 0.000000：TODO 1 还没写出来，'
                                  '两个版本都还没真的跑'))
        else:
            checks.append((True, 'k = 100 / 500 / 1000 / 2000 四档的耗时都量到了'))
            # 趋势一：暴力那一列随 k 变大而明显变慢
            if bf[0] > 0 and bf[-1] / bf[0] >= 3:
                checks.append((True, '暴力那一列从 k=100 到 k=2000 涨了 '
                               + f'{bf[-1] / bf[0]:.1f}' + ' 倍——代价与 k 成正比（O(nk)）'))
            else:
                checks.append((False, '暴力那一列从 k=100 到 k=2000 只涨了 '
                               + f'{bf[-1] / max(bf[0], 1e-9):.1f}' + ' 倍，期望 3 倍以上：'
                                 '暴力版每个窗口都要重新扫一遍，k 越大越慢'))
            # 趋势二：单调队列那一列不随 k 增长
            if wn[0] > 0 and wn[-1] / wn[0] <= 4:
                checks.append((True, '单调队列那一列四档之间基本不动（'
                               + f'{wn[-1] / wn[0]:.2f}' + ' 倍）——每个下标只进出队一次'))
            else:
                checks.append((False, '单调队列那一列从 k=100 到 k=2000 涨了 '
                               + f'{wn[-1] / max(wn[0], 1e-9):.2f}' + ' 倍，期望 4 倍以内：'
                                 '这一列应当与 k 无关；确认它写的是队列版、不是暴力'))
            gaps = ratio_values(run['out'], '02')
            if gaps and gaps[-1] >= 20:
                checks.append((True, 'k=2000 这一档上暴力比单调队列慢 ' + f'{gaps[-1]:.1f}'
                               + ' 倍——两个数量级以上'))
            elif gaps and any(s > 0 for s in wn) and any(s > 0 for s in bf):
                checks.append((False, 'k=2000 这一档暴力只比单调队列慢 ' + f'{gaps[-1]:.1f}'
                               + ' 倍，期望 20 倍以上：先确认两版答案都对，再看计时是不是各量各的'))
    else:
        checks.append((False, '耗时行只读到 ' + str(len(wn)) + ' / ' + str(len(bf))
                       + ' 行（期望各 4 行，k = 100 / 500 / 1000 / 2000）：'
                         '带 print 的那两行别改、别删'))
    return checks


CHECKERS = {
    'task1_stack_queue.py': check_task1,
    'task2_queue_cost.py': check_task2,
    'task3_brackets.py': check_task3,
    'task4_eval.py': check_task4,
    'task5_window_max.py': check_task5,
}


def main():
    print('StudyMate lab 0010 · 自动判分（后进先出与先进先出）')
    print('目录：' + str(HERE))
    print()
    failed = []
    for title, filename, _ in TASKS:
        print(title + '（' + filename + '）')
        if not (HERE / filename).is_file():
            print('  FAIL  还没建这个文件：' + filename)
            print()
            failed.append(filename)
            continue
        checks = CHECKERS[filename]()
        all_ok = True
        for ok, message in checks:
            print('  ' + ('PASS' if ok else 'FAIL') + '  ' + message)
            if not ok:
                all_ok = False
        if all_ok:
            print('  → 这个任务过了')
        else:
            failed.append(filename)
        print()

    print('─' * 60)
    print('5 个任务：' + str(5 - len(failed)) + ' 个通过，' + str(len(failed)) + ' 个还没通过')
    if failed:
        print('没过的：' + '、'.join(failed))
        print('卡住了先读 ../README.md 的「卡壳顺序」：读错误信息 → 自己跑一遍 → 看 FAIL 行 → 再对线索。')
        print('五个任务都过了，再对照 ../solutions/0010-stack-and-queue/ 看参考解。')
        return 1
    print('五个任务都过了。现在去对照 ../solutions/0010-stack-and-queue/：')
    print('比一比你的写法与参考解，再用一句话回答「单调队列里两条弹出各自为什么不能省」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
