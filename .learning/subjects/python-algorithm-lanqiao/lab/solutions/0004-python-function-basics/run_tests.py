#!/usr/bin/env python3
"""lab 0004 · 自动判分：跑任务脚本，比对输出。

用法（在 lab/0004-python-function-basics/ 目录里）：

    py run_tests.py

判法：
  - 每个任务单独起一个进程跑，只看 stdout 里的固定格式行，不 import 学生代码；
  - 任务 1 与任务 3 用同一批输入分别跑 flat_odd.py（基准）与学生的脚本，逐字比对——
    「输出与原版一致」是这一课的硬指标；
  - 任务 1 与任务 3 另外看一眼前面有没有写出那几个函数名（函数名是给好的接口），
    防止把摊平版直接抄过来当交差。

退出码：0 = 四个任务都通过；1 = 还有没通过的。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ── 验收样本（课件里那张表：输入 → 1 到 N 之间的奇数个数）──────────────────
CASES = [
    ('0', '0'),
    ('1', '1'),
    ('10', '5'),
    ('1234567', '617284'),
]
CASE_TEXT = '0→0、1→1、10→5、1234567→617284'

BASELINE = 'flat_odd.py'          # 摊平版基准（给好的，别改）
TIMEOUT = 60


def run_script(name, stdin_text=''):
    """跑一个脚本 → (状态, stdout, 备注)。状态：ok / missing / crash / timeout。"""
    path = HERE / name
    if not path.is_file():
        return 'missing', '', '还没建这个文件：' + name
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    try:
        done = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(HERE), env=env, timeout=TIMEOUT,
            input=stdin_text,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return 'timeout', '', '跑了 ' + str(TIMEOUT) + ' 秒还没结束（在等输入？死循环？）'
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-5:])
        return 'crash', done.stdout or '', ('脚本报错退出（退出码 ' + str(done.returncode)
                                            + '）：\n' + tail)
    return 'ok', done.stdout or '', ''


def get_line(out, prefix):
    """按前缀取出一整行剩下的内容；没打到那一行就返回 None。"""
    for line in out.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def first_line(out):
    """第一行非空输出（任务 1、3 的答案就打在它上面）。"""
    for line in out.splitlines():
        if line.strip():
            return line.strip()
    return ''


def missing_defs(filename, names):
    """文件里有没有写出这几个函数；缺了返回一句提示，都齐了返回 None。"""
    path = HERE / filename
    if not path.is_file():
        return '还没建这个文件：' + filename
    text = path.read_text(encoding='utf-8', errors='replace')
    gone = []
    for name in names:
        if 'def ' + name + '(' not in text:
            gone.append(name)
    if gone:
        return (filename + ' 里没找到这几个函数定义：' + '、'.join(gone)
                + '（文件名与函数名是给好的接口，别改）')
    return None


def baseline_answers():
    """跑摊平版基准 → (每组的答案, 错误提示)。"""
    answers = {}
    for case in CASES:
        status, out, note = run_script(BASELINE, case[0] + '\n')
        if status != 'ok':
            return None, BASELINE + ' 跑不起来（它是给好的基准，别改）：' + note
        answers[case[0]] = first_line(out)
    return answers, ''


# ── 每个任务一组判定：(通过?, 一句话) ──────────────────────────────────────

def check_task1():
    """把摊平版改写成四个函数，输出必须与摊平版逐字一致。"""
    answers, err = baseline_answers()
    if answers is None:
        return [(False, err)]
    checks = []
    for case in CASES:
        got = answers[case[0]]
        if got != case[1]:
            checks.append((False, '基准 ' + BASELINE + ' 在输入 ' + case[0] + ' 时打出 '
                           + repr(got) + '，应该是 ' + case[1] + '：这一份别改'))
    if checks:
        return checks
    checks.append((True, '基准 ' + BASELINE + ' 四组输入都对上：' + CASE_TEXT))

    gone = missing_defs('task1_functions.py', ['read_n', 'odd_count', 'show', 'solve'])
    if gone:
        return [(False, gone)]
    checks.append((True, 'read_n / odd_count / show / solve 四个函数都在'))

    bad = []
    for case in CASES:
        given = case[0]
        status, out, note = run_script('task1_functions.py', given + '\n')
        if status == 'missing':
            return [(False, note)]
        if status == 'crash':
            return [(False, 'task1_functions.py 在输入 ' + given + ' 时报错：' + note)]
        if status == 'timeout':
            return [(False, 'task1_functions.py 在输入 ' + given + ' 时' + note)]
        got = first_line(out)
        if got != answers[given]:
            bad.append((given, answers[given], got))
    if bad:
        one = bad[0]
        hint = ''
        if one[2] == '':
            hint = '（一行都没打印出来：solve 里还有没填的 TODO？）'
        checks.append((False, '输入 ' + one[0] + ' 时函数版打出 ' + repr(one[2])
                       + '，摊平版打出 ' + repr(one[1]) + hint))
        checks.append((False, '四组输入里有 ' + str(len(bad)) + ' 组对不上：'
                       + '改写只动代码的组织方式，输出必须逐字一致'))
        return checks
    checks.append((True, '四组输入与摊平版逐字一致：' + CASE_TEXT))
    return checks


def check_task2():
    """默认值只在定义时算一次 + 可变默认参数的陷阱与修法。"""
    status, out, note = run_script('task2_default_arg.py', '')
    if status != 'ok':
        return [(False, 'task2_default_arg.py 没跑通：' + note)]
    checks = []
    first = get_line(out, 'A 默认值')
    if first is None:
        return [(False, '没看到「A 默认值 …」这一行：带 print 的行别改、别删')]
    if first == '5':
        checks.append((True, 'A：改完全局变量 i 之后再调用，默认值仍是 5'))
    else:
        checks.append((False, 'A 打出的是 ' + first + '，期望 5：默认值要写在 def 那一行'
                              '（arg=i），它不是每次调用时去读 i'))

    want = [('B 陷阱版 第 1 次', '[1]',
             '陷阱版第一次调用拿到的是只装了 1 的那个列表'),
            ('B 陷阱版 第 2 次', '[1, 2]',
             '陷阱版第二次调用拿到同一个列表，里面已经装过 1'),
            ('B 陷阱版 第 3 次', '[1, 2, 3]',
             '陷阱版第三次调用接着往同一个列表里追加'),
            ('B 陷阱版是同一个列表', 'True',
             'b1 is b2 是 True，印证三次拿到的是同一个列表'),
            ('B 陷阱版 b1 现在', '[1, 2, 3]',
             '第一次调用的返回值被后面两次改掉了——b1 不再是 [1]'),
            ('B 修好版', '[1] [2] [3]',
             '修好版每次调用都得到自己的空列表'),
            ('B 修好版是同一个列表', 'False',
             'g1 is g2 是 False，说明每次都是新列表'),
            ('B 修好版接现成列表', '[7, 8] [7, 8]',
             '调用处给了现成列表时，往那份列表里追加')]
    got = {}
    for prefix, expect, good in want:
        got[prefix] = get_line(out, prefix)
    # 这几条是「并列观察」：前面的值不对时，它们通过也不说明 TODO 填对了
    # （留白原样跑时 b1 is b2 本来就是 True），所以要先看被依赖的那一行。
    needs = {
        'B 陷阱版是同一个列表': ('B 陷阱版 第 3 次', '[1, 2, 3]',
                                 '先把 grow_bad 的 TODO 填上（L.append(a) 再 return L）'),
        'B 陷阱版 b1 现在': ('B 陷阱版 第 3 次', '[1, 2, 3]',
                             '先把 grow_bad 的 TODO 填上（L.append(a) 再 return L）'),
        'B 修好版是同一个列表': ('B 修好版', '[1] [2] [3]',
                                 '先把 grow_ok 的 TODO 填上（L 是 None 时新建空列表）'),
    }
    for prefix, expect, good in want:
        value = got[prefix]
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删'))
            continue
        if value == expect:
            need = needs.get(prefix)
            if need and got[need[0]] != need[1]:
                checks.append((False, prefix + ' 是 ' + repr(value) + '，但「' + need[0]
                               + '」还没对：' + need[2] + '，这一条才有意义'))
                continue
            checks.append((True, good))
        elif prefix == 'B 修好版':
            checks.append((False, prefix + ' 打出 ' + repr(value) + '，期望 ' + repr(expect)
                           + '：grow_ok 里 L 是 None 时要新建空列表（if L is None: L = []）'))
        elif prefix.startswith('B 陷阱版 第'):
            checks.append((False, prefix + ' 打出 ' + repr(value) + '，期望 ' + repr(expect)
                           + '：grow_bad 要照课件写成 L.append(a) 再 return L'))
        else:
            checks.append((False, prefix + ' 打出 ' + repr(value) + '，期望 ' + repr(expect)))
    return checks


def check_task3():
    """故意用全局变量传状态的版本：答案一致，且函数外读得到全局变量。"""
    answers, err = baseline_answers()
    if answers is None:
        return [(False, err)]
    gone = missing_defs('task3_global_state.py', ['read_n', 'odd_count', 'show'])
    if gone:
        return [(False, gone)]
    checks = [(True, 'read_n / odd_count / show 三个函数都在')]
    bad = []
    for case in CASES:
        given = case[0]
        status, out, note = run_script('task3_global_state.py', given + '\n')
        if status == 'missing':
            return [(False, note)]
        if status == 'crash':
            return [(False, 'task3_global_state.py 在输入 ' + given + ' 时报错：' + note)]
        if status == 'timeout':
            return [(False, 'task3_global_state.py 在输入 ' + given + ' 时' + note)]
        got_first = first_line(out)
        got_n = get_line(out, '函数外读到全局 n_global')
        got_c = get_line(out, '函数外读到全局 count_global')
        if got_first != answers[given] or got_n != str(int(given)) or got_c != answers[given]:
            bad.append((given, answers[given], got_first, got_n, got_c))
    if bad:
        one = bad[0]
        checks.append((False, '输入 ' + one[0] + ' 时第一行打出 ' + repr(one[2])
                       + '，函数版打出 ' + repr(one[1]) + '：答案必须与函数版逐字一致'))
        checks.append((False, '全局变量没读到位：n_global 是 ' + repr(one[3])
                       + '、count_global 是 ' + repr(one[4])
                       + '（read_n 要把值存进全局 n_global，odd_count 要读它、'
                       + '把答案存进 count_global；函数里改全局变量要先写 global）'))
        return checks
    checks.append((True, '四组输入的第一行与函数版逐字一致：' + CASE_TEXT))
    checks.append((True, '函数外读得到 n_global 与 count_global：数据确实靠全局变量流动'))
    return checks


def check_task4():
    """就地改 vs 复制一份：调用处的列表变没变。"""
    status, out, note = run_script('task4_copy_list.py', '')
    if status != 'ok':
        return [(False, 'task4_copy_list.py 没跑通：' + note)]
    checks = []
    want = [('就地版 返回', '[11, 12, 13]', '就地版返回的列表是 [11, 12, 13]'),
            ('就地版 调用处', '[11, 12, 13]', '就地版把调用处的 a 也改了——这是它的效果'),
            ('就地版 改坏了调用处', 'True', '就地版确实改到了调用处的列表'),
            ('副本版 返回', '[11, 12, 13]', '副本版返回的列表也是 [11, 12, 13]'),
            ('副本版 调用处', '[1, 2, 3]', '副本版没动调用处的 b'),
            ('副本版 没改调用处', 'True', 'nums = nums[:] 保护了调用处的数据')]
    # 「没改调用处」是并列观察：add_copy 原样没填时 b 当然没被改，通过也不算数。
    needs = {'副本版 调用处': ('副本版 返回', '[11, 12, 13]',
                               '先把 add_copy 的 TODO 填上（nums = nums[:] 后用下标循环加 delta）'),
             '副本版 没改调用处': ('副本版 返回', '[11, 12, 13]',
                                   '先把 add_copy 的 TODO 填上（nums = nums[:] 后用下标循环加 delta）')}
    got = {}
    for prefix, expect, good in want:
        got[prefix] = get_line(out, prefix)
    for prefix, expect, good in want:
        value = got[prefix]
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删'))
        elif value == expect:
            need = needs.get(prefix)
            if need and got[need[0]] != need[1]:
                checks.append((False, prefix + ' 是 ' + repr(value) + '，但「' + need[0]
                               + '」还没对：' + need[2] + '，这一条才有意义'))
                continue
            checks.append((True, good))
        elif prefix == '副本版 调用处' and value == '[11, 12, 13]':
            checks.append((False, '副本版把调用处的 b 也改了：add_copy 里要先写 '
                                  'nums = nums[:] 复制一份，后面都改副本'))
        elif prefix in ('就地版 返回', '副本版 返回') and value == '[1, 2, 3]':
            checks.append((False, prefix + ' 打出 [1, 2, 3]：那个函数的 TODO 还没填'
                           '（要用下标循环把每个元素加 delta）'))
        else:
            checks.append((False, prefix + ' 打出 ' + repr(value) + '，期望 ' + repr(expect)))
    return checks


TASKS = [
    ('任务 1 · 摊平版改写成四个函数', 'task1_functions.py', check_task1),
    ('任务 2 · 默认值只算一次', 'task2_default_arg.py', check_task2),
    ('任务 3 · 全局变量传状态版', 'task3_global_state.py', check_task3),
    ('任务 4 · 别改坏调用处的列表', 'task4_copy_list.py', check_task4),
]


def main():
    print('StudyMate lab 0004 · 自动判分（把一段代码变成函数）')
    print('目录：' + str(HERE))
    print()
    failed = []
    for title, filename, checker in TASKS:
        print(title + '（' + filename + '）')
        if not (HERE / filename).is_file():
            print('  FAIL  还没建这个文件：' + filename)
            print()
            failed.append(filename)
            continue
        checks = checker()
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
    print('4 个任务：' + str(4 - len(failed)) + ' 个通过，'
          + str(len(failed)) + ' 个还没通过')
    if failed:
        print('没过的：' + '、'.join(failed))
        print('卡住了先读 ../README.md 的「卡壳顺序」：读错误信息 → 自己跑一遍 → 看 FAIL 行 → 再对线索。')
        print('四个任务都过了，再对照 ../solutions/0004-python-function-basics/ 看参考解。')
        return 1
    print('四个任务都过了。现在去对照 ../solutions/0004-python-function-basics/：')
    print('比一比你的写法和参考解，再说一句「read_n 的定义那一行为什么看不出它动了哪些数据」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
