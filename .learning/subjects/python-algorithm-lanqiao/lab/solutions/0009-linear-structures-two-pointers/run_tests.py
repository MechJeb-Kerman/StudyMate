#!/usr/bin/env python3
"""lab 0009 · 自动判分：跑五个任务脚本，比对固定格式行。

用法（在 lab/0009-linear-structures-two-pointers/ 目录里）：

    py run_tests.py

判法：
  - 每个任务单独起一个进程跑，只看 stdout 里的固定格式行，不 import 学生代码
    （任务脚本自己在顶层 import 前面任务的函数，那是它们之间的事）；
  - 计数行（`计数 NN 标签 值`）与耗时行（`耗时 NN 标签 n=… 秒`）是判分接口，
    按两位编号取，编号与前缀都对得上才算；
  - **三个版本的正确性靠对拍验**：任务 4 把暴力版当基准，任务 2、3 各自交回
    「与暴力一致」这一行；任务 1 的暴力版自己另有课件给的小数组答案（期望 9）；
  - **耗时看趋势不看常数**：这张表里的绝对值换台机器就变，判分只要求
    暴力那一列在「规模翻倍」时涨得明显比两个线性版多（课件口径：暴力约四倍、
    线性约两倍），以及同规模上暴力比双指针慢两个数量级以上；
  - 任务 3 另有一条：去掉 r < n 的错版必须在 [1, 2]、S = 100 上报 IndexError
    （这正是 r < n 不能省的证据）。

退出码：0 = 五个任务都通过；1 = 还有没通过的。
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMEOUT = 120

# 课件与本机实测的口径（判分只把它们当区间，不当精确值）
NUM_RE = re.compile(r'-?\d+')

TASKS = [
    ('任务 1 · 暴力版：先写对，再当基准', 'task1_brute.py', None),
    ('任务 2 · 前缀和：把区间和变成两次取表相减', 'task2_prefix.py', None),
    ('任务 3 · 双指针：两个下标都只往前走', 'task3_window.py', None),
    ('任务 4 · 对拍：三个版本答案对不对得上', 'task4_compare.py', None),
    ('任务 5 · 三个版本的实测耗时对照', 'task5_scale.py', None),
]


# ── 跑脚本 ────────────────────────────────────────────────────────────────

def run_script(name):
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
            cwd=str(HERE), env=env, timeout=TIMEOUT,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'out': '',
                'note': '跑了 ' + str(TIMEOUT) + ' 秒还没结束（死循环？）'}
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-5:])
        return {'status': 'crash', 'out': done.stdout or '',
                'note': ('脚本报错退出（退出码 ' + str(done.returncode) + '）：\n' + tail)}
    return {'status': 'ok', 'out': done.stdout or '', 'note': ''}


# ── 读输出 ────────────────────────────────────────────────────────────────

def get_line(out, prefix):
    """按前缀取一整行剩下的内容；同一前缀打多次时取**最后一次**（脚本可能被 import 重跑）。"""
    found = None
    for line in out.splitlines():
        if line.startswith(prefix):
            found = line[len(prefix):].strip()
    return found


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
    """取 `耗时 NN 标签 n=… 秒` 里的 (n, 秒数)；同一编号可能有多行（多个规模）。"""
    values = []
    for entry in get_lines(out, '耗时 ' + index + ' '):
        match = re.search(r'n=(\d+)\s+([\d.]+)', entry)
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


# ── 任务 1 · 暴力版 ───────────────────────────────────────────────────────

def check_task1():
    run = run_script('task1_brute.py')
    if run['status'] != 'ok':
        return [(False, 'task1_brute.py 没跑通：' + run['note'])]
    checks = []
    want = [
        ('小数组', '9', '小数组 [4, 0, 0, 4, 0]、S = 4 的答案是 9'),
        ('全正数 2000 个数', '44', '2000 个正整数的数组上答案是 44'),
        ('含负数 300 个数', '106', '含负数的 300 个数上答案是 106'),
    ]
    for prefix, expect, good in want:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删'))
        elif value != expect:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 1 的两层循环还没写对（r 要从 l 起、'
                             '先 s += a[r] 再判断）'))
        else:
            checks.append((True, good))
    value = count_value(run['out'], '01')
    if value == '9':
        checks.append((True, '计数 01 暴力 9：判分接口那一行也在'))
    elif value is None:
        checks.append((False, '没看到「计数 01 …」这一行：show_count 那一行别改、别删'))
    else:
        checks.append((False, '计数 01 打出 ' + short(value) + '，期望 9'))
    return checks


# ── 任务 2 · 前缀和 ───────────────────────────────────────────────────────

def check_task2():
    run = run_script('task2_prefix.py')
    if run['status'] != 'ok':
        return [(False, 'task2_prefix.py 没跑通：' + run['note'])]
    checks = []
    table = get_line(run['out'], '前缀和表')
    if table is None:
        checks.append((False, '没看到「前缀和表 …」这一行：带 print 的行别改、别删'))
    elif table == '[0, 4, 4, 4, 8, 8]':
        checks.append((True, '前缀和表 [0, 4, 4, 4, 8, 8]：pre[0] = 0、长度是 n + 1'))
    else:
        checks.append((False, '前缀和表打出 ' + short(table) + '，期望 [0, 4, 4, 4, 8, 8]：'
                           'TODO 1 要先放好 pre = [0] 这个起点，再逐个 append(pre[-1] + x)'))

    want = [
        ('小数组', '9', '小数组的答案是 9'),
        ('全正数 2000 个数', '44', '2000 个正整数的数组上答案是 44'),
        ('含负数 300 个数', '106', '含负数的 300 个数上答案是 106——前缀和不受正负影响'),
    ]
    for prefix, expect, good in want:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value != expect:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 2 里 need 要用 pre[r + 1] - S，'
                             'seen 的初值要写 {0: 1}，且每轮先查后记'))
        else:
            checks.append((True, good))

    for prefix, good, hint in [
        ('与暴力一致', '小数组上与前缀和版与暴力版一致',
         'TODO 2 还没写对（这一行比对的是两个函数的返回值）'),
        ('含负数时仍与暴力一致', '含负数时前缀和版仍与暴力版一致——它没有「元素必须为正」这条前提',
         '前缀和版在含负数的数组上也应当与暴力版一致；对不上说明 TODO 2 有问题'),
    ]:
        value = get_line(run['out'], prefix)
        if value == 'True':
            # 留白版上两版的答案都是 0，「一致」也会成立——先看被依赖的那一行。
            if get_line(run['out'], '小数组') != '9':
                checks.append((False, prefix + ' 是 True，但「小数组」还没对：'
                               '先把 TODO 2 写出来，这一条才有意义'))
                continue
            checks.append((True, good))
        elif value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 True：' + hint))

    for prefix, expect in [('区间和公式', '4790'), ('同一段逐项加', '4790')]:
        value = get_line(run['out'], prefix)
        if value == expect:
            checks.append((True, prefix + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：这一段是给好的，对不上说明 TODO 1 交回的表不对'))
    value = get_line(run['out'], '公式与切片一致')
    if value == 'True':
        checks.append((True, 'pre[r+1] - pre[l] 与逐项相加结果相同'))
    elif value is not None:
        checks.append((False, '公式与切片一致 打出 ' + short(value) + '，期望 True'))

    value = count_value(run['out'], '02')
    if value == '9':
        checks.append((True, '计数 02 前缀和 9'))
    elif value is None:
        checks.append((False, '没看到「计数 02 …」这一行'))
    else:
        checks.append((False, '计数 02 打出 ' + short(value) + '，期望 9'))
    return checks


# ── 任务 3 · 双指针 ───────────────────────────────────────────────────────

def check_task3():
    run = run_script('task3_window.py')
    if run['status'] != 'ok':
        return [(False, 'task3_window.py 没跑通：' + run['note'])]
    checks = []
    want = [
        ('小数组 双指针', '4', '正数（含 0）的小数组上双指针只数到 4'),
        ('小数组 暴力', '9', '同一批数据上暴力版数到 9'),
        ('全正数 2000 个数 双指针', '44', '2000 个正整数的数组上双指针版给出 44'),
        ('含负数 300 个数 双指针', '4', '含负数的 300 个数上双指针版只给出 4'),
    ]
    for prefix, expect, good in want:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value != expect:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 1 的 while 要写 while r < n and s < S:，'
                             '末尾别漏 s -= a[l]'))
        else:
            checks.append((True, good))

    for prefix, expect, good, hint in [
        ('小数组 两版答案一致', 'False',
         '小数组上两版答案不一致（False）——这正是 0 破坏单调性的证据',
         '这一行期望 False：双指针版在含 0 的数组上会少算，与暴力版对不上才是对的；'
         '打出 True 说明 TODO 1 写的不是课件那一版'),
        ('全正数 与暴力一致', 'True',
         '全为正数时双指针版与暴力版一致——单调性前提成立',
         '全为正数时双指针版必须与暴力版一致；对不上说明 TODO 1 写错了'),
        ('含负数 与暴力一致', 'False',
         '含负数时双指针版与暴力版不一致——前提被破坏了',
         '这一行期望 False：含负数（或 0）时双指针会漏解；'
         '打出 True 说明 TODO 1 写的不是课件那一版'),
        ('含负数 前缀和与暴力一致', 'True',
         '同一批含负数的数据上，前缀和版仍与暴力版一致',
         '前缀和版在含负数时也应当与暴力版一致'),
    ]:
        value = get_line(run['out'], prefix)
        if value == expect:
            # 「一致」类的行在留白版上也会碰巧成立（两边都是 0），
            # 所以先看被依赖的那一行对不对，这一条才有意义。
            if prefix == '全正数 与暴力一致' and get_line(run['out'], '全正数 2000 个数 双指针') != '44':
                checks.append((False, prefix + ' 是 True，但「全正数 2000 个数 双指针」还没对：'
                               '先把 TODO 1 的滑动窗口写出来，这一条才有意义'))
                continue
            if prefix == '含负数 前缀和与暴力一致' and get_line(run['out'], '含负数 300 个数 双指针') != '4':
                checks.append((False, prefix + ' 是 True，但「含负数 300 个数 双指针」还没对：'
                               '先把 TODO 1 的滑动窗口写出来，这一条才有意义'))
                continue
            checks.append((True, good))
        elif value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect + '：' + hint))

    value = get_line(run['out'], '错版在 [1, 2] 上报错 IndexError')
    if value is None:
        checks.append((False, '没看到「错版在 [1, 2] 上报错 IndexError …」这一行'))
    elif 'list index out of range' in value:
        checks.append((True, '去掉 r < n 的错版在下标越界时报了 IndexError: list index out of range'))
    else:
        checks.append((False, '错版那一段打出 ' + short(value) + '，期望报 list index out of range：'
                           'TODO 2 要把 while 写成 while s < S:（去掉 r < n）'))

    for index, expect, label in [('03', '44', '双指针 正数'), ('04', '4', '双指针 含负数')]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))
    return checks


# ── 任务 4 · 对拍 ─────────────────────────────────────────────────────────

def check_task4():
    run = run_script('task4_compare.py')
    if run['status'] != 'ok':
        return [(False, 'task4_compare.py 没跑通：' + run['note'])]
    checks = []
    want = [
        ('小数组三版答案', '(9, 9, 4)', '小数组上三版答案 (9, 9, 4)：双指针比暴力少 5 个'),
        ('第一个反例', '[4, 0, 0, 4, 0]', '找出的第一个反例就是小数组 [4, 0, 0, 4, 0]'),
        ('反例上三版答案', '(9, 9, 4)', '反例上三版答案 (9, 9, 4)'),
        ('全正数上三版始终一致', 'True', '全正数的数组上三个版本答案始终一致'),
        ('含负数上的三版答案', '(106, 106, 4)', '含负数的 300 个数上三版答案 (106, 106, 4)'),
    ]
    for prefix, expect, good in want:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value != expect:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 1 要交回三个版本各自的答案，'
                             'TODO 2 要在找到第一个不一致的数组时立刻交回它'))
        elif prefix == '全正数上三版始终一致' and get_line(run['out'], '小数组三版答案') != '(9, 9, 4)':
            # 留白版上「始终一致」也会成立（三个版本都交回 0），先看被依赖的那一行。
            checks.append((False, prefix + ' 是 True，但「小数组三版答案」还没对：'
                           '先把 TODO 1 写出来，这一条才有意义'))
        else:
            checks.append((True, good))

    value = count_value(run['out'], '05')
    if value == '3':
        checks.append((True, '计数 05 反例总数 3：小数组上有 3 个 S 让两版答案分岔'))
    elif value is None:
        checks.append((False, '没看到「计数 05 …」这一行'))
    else:
        checks.append((False, '计数 05 打出 ' + short(value) + '，期望 3：'
                           '这一行数的是「哪些 S 让双指针与暴力答案不同」'))
    return checks


# ── 任务 5 · 耗时对照 ─────────────────────────────────────────────────────

def check_task5():
    run = run_script('task5_scale.py')
    if run['status'] != 'ok':
        return [(False, 'task5_scale.py 没跑通：' + run['note'])]
    checks = []

    brute = time_values(run['out'], '01')
    prefix = time_values(run['out'], '02')
    window = time_values(run['out'], '03')

    for name, values, index in [('暴力', brute, '01'), ('前缀和', prefix, '02'), ('双指针', window, '03')]:
        sizes = [n for n, _ in values]
        # 三行都在，且**秒数不是全 0**：留白版的三行也在（都是 0.000000），
        # 那不算「量到了」——这一条只有真的计过时才给 PASS。
        if len(values) == 3 and sizes == [500, 1000, 2000]:
            if all(seconds <= 0 for _, seconds in values):
                checks.append((False, name + '的三行秒数都是 0.000000：'
                               'TODO 1 还没接上 timed，或者 TODO 2 的 best_of_three 还交回 0.0'))
            elif not any(seconds > 0 for _, seconds in values):
                checks.append((False, name + '的秒数没量到（都是 0）：TODO 1 还没接上 timed'))
            else:
                checks.append((True, name + '：三个规模（500 / 1000 / 2000）的耗时都量到了'))
        elif not values:
            checks.append((False, '没看到「耗时 ' + index + ' …」这一行：'
                                  'TODO 1 的 time_three 还没量出 ' + name + ' 的秒数'
                                  '（现在三行都是 0.000000）'))
        else:
            checks.append((False, name + '只量到 ' + str(len(values)) + ' 行（'
                           + str(sizes) + '），期望 500 / 1000 / 2000 三个规模各一行'))

    # 趋势一：暴力那两行应当是「翻倍涨约四倍」
    if len(brute) == 3 and brute[0][1] > 0:
        ratios = []
        for i in range(1, 3):
            base = brute[i - 1][1]
            if base > 0:
                ratios.append(brute[i][1] / base)
        if len(ratios) == 2:
            if ratios[0] >= 2.5 and ratios[1] >= 2.5:
                checks.append((True, '暴力那一列随规模翻倍涨了 '
                               + f'{ratios[0]:.2f} 倍与 {ratios[1]:.2f} 倍——O(n²) 的样子'))
            else:
                checks.append((False, '暴力那一列翻倍时只涨了 ' + f'{ratios[0]:.2f} 与 {ratios[1]:.2f}'
                               + ' 倍，期望都在 2.5 倍以上（O(n²) 该是四倍上下）：'
                                 'TODO 1 要真的计时，别把三个版本的时间混在一起量'))

    # 趋势二：两个线性版翻倍时涨得明显比暴力少
    for name, values in [('前缀和', prefix), ('双指针', window)]:
        if len(values) == 3 and values[0][1] > 0 and brute and len(brute) == 3:
            ratios = []
            for i in range(1, 3):
                base = values[i - 1][1]
                if base > 0:
                    ratios.append(values[i][1] / base)
            if not ratios:
                continue
            brute_ratio = brute[2][1] / brute[1][1] if brute[1][1] > 0 else 0
            if max(ratios) < brute_ratio:
                checks.append((True, name + '那一列翻倍涨 ' + f'{max(ratios):.2f}'
                               + ' 倍，比暴力的 ' + f'{brute_ratio:.2f} 倍小——线性版的样子'))
            else:
                checks.append((False, name + '那一列翻倍涨了 ' + f'{max(ratios):.2f}'
                               + ' 倍，不比暴力的 ' + f'{brute_ratio:.2f} 倍小：'
                                 '两个线性版随规模应当约两倍地涨'))

    # 趋势三：同规模上暴力比双指针慢两个数量级以上
    gap = ratio_values(run['out'], '07')
    timed_ok = (len(brute) == 3 and brute[0][1] > 0 and len(window) == 3 and window[0][1] > 0)
    if not gap:
        checks.append((False, '没看到「倍数 07 …」这一行（暴力比双指针）'))
    elif not timed_ok:
        checks.append((False, '计时还没量到真数（有几行的秒数是 0.000000）：'
                              '先把 TODO 1 的 time_three 接上 timed，这一条倍数才有意义'))
    elif gap[-1] >= 100:
        checks.append((True, '同一规模上暴力比双指针慢 ' + f'{gap[-1]:.2f}'
                       + ' 倍——两个数量级以上，这就是换走法挣来的差距'))
    else:
        checks.append((False, '暴力只比双指针慢 ' + f'{gap[-1]:.2f}' + ' 倍，期望 100 倍以上：'
                       '先确认两个版本的答案都对，再看计时那几行是不是按三个函数分开量的'))

    gap2 = ratio_values(run['out'], '08')
    if gap2 and 0.2 <= gap2[-1] <= 20:
        checks.append((True, '前缀和比双指针 ' + f'{gap2[-1]:.2f}'
                       + ' 倍——同是 O(n)，差距很小，说明省下的不是数量级'))
    return checks


CHECKERS = {
    'task1_brute.py': check_task1,
    'task2_prefix.py': check_task2,
    'task3_window.py': check_task3,
    'task4_compare.py': check_task4,
    'task5_scale.py': check_task5,
}


def main():
    print('StudyMate lab 0009 · 自动判分（一维数据的两种走法）')
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
        print('五个任务都过了，再对照 ../solutions/0009-linear-structures-two-pointers/ 看参考解。')
        return 1
    print('五个任务都过了。现在去对照 ../solutions/0009-linear-structures-two-pointers/：')
    print('比一比你的写法与参考解，再用一句话回答「双指针那三个前提，哪一个在这道题上不成立」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
