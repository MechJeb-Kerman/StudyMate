#!/usr/bin/env python3
"""lab 0016 · 自动判分：跑任务脚本，比对输出，另起探针 import 学生代码。

用法（在 lab/0016-hash-table/ 目录里）：

    py run_tests.py

判法：
  - 任务 1、2、3 各起一个进程跑，读它们打印出来的固定格式行；
  - 这三题还要另起**探针进程** import 任务脚本里的函数接口，拿一组判分自己的小数据
    去试：列表版与字典/集合版必须在**每一组**上逐字一致，只交一版不算过；
  - 任务 3 的探针专抓两数之和的两个边界：[3, 3] 必须是 (0, 1)（先查后存，
    当前元素配不上自己），以及同一个元素不能用两次；
  - 任务 4 起**两个进程**分别算同一批键的哈希值，比对「同进程内两次一致」与
    「跨进程不同」；桶号与冲突个数两次必须一样；
  - 任务 5 用探针试列表当键报什么错、浮点当键取不取得到、round 之后能不能取到。

断言里的口径来自课件正文：平均 O(1)、冲突必然存在（10 个键放 8 个桶按抽屉原理
一定有桶装 2 个以上）、哈希值跨进程不同而同进程内一致、两数之和先查后存。

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
TODO_RE = re.compile(r'TODO\s+(\d+)')
FILE_LINE_RE = re.compile(r'File "([^"]*)", line (\d+)')

TASKS = [
    ('任务 1 · 统计出现次数（列表版 vs 字典版）', 'task1_count.py', None),
    ('任务 2 · 第一个重复出现的元素（列表版 vs 集合版）', 'task2_first_repeat.py', None),
    ('任务 3 · 两数之和（列表版 vs 字典版，先查后存）', 'task3_two_sum.py', None),
    ('任务 4 · 手工算哈希值与桶号（冲突、跨进程）', 'task4_hash_buckets.py', None),
    ('任务 5 · 什么能当键（列表、浮点、稳定性）', 'task5_key_rules.py', None),
]


# ── 跑脚本 ────────────────────────────────────────────────────────────────

def _env():
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    return env


def run_script(name, timeout=TIMEOUT):
    """跑一个脚本 → dict(status, out, err, note)。状态：ok / missing / crash / timeout。"""
    path = HERE / name
    if not path.is_file():
        return {'status': 'missing', 'out': '', 'err': '',
                'note': '还没建这个文件：' + name}
    try:
        done = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(HERE), env=_env(), timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'out': '', 'err': '',
                'note': '跑了 ' + str(timeout) + ' 秒还没结束（死循环？两版都太大？）'}
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-5:])
        note = ('脚本报错退出（退出码 ' + str(done.returncode) + '）'
                + todo_hint(name, done.stderr or '') + '：\n' + tail)
        return {'status': 'crash', 'out': done.stdout or '', 'err': done.stderr or '',
                'note': note}
    return {'status': 'ok', 'out': done.stdout or '', 'err': '', 'note': ''}


def run_probe(code, timeout=TIMEOUT):
    """另起一个进程跑一小段探针代码（用它 import 学生代码）。"""
    try:
        done = subprocess.run(
            [sys.executable, '-B', '-c', code],
            cwd=str(HERE), env=_env(), timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return None, '探针跑了 ' + str(timeout) + ' 秒还没结束'
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-6:])
        return None, '探针报错退出：\n' + tail
    return done.stdout or '', ''


def todo_hint(name, err):
    """从 traceback 里找出报错落在哪个 TODO 段；认不出来就交回空串。"""
    lineno = None
    for line in err.splitlines():
        m = FILE_LINE_RE.search(line)
        if m and m.group(1).replace('\\', '/').endswith('/' + name):
            lineno = int(m.group(2))
    if lineno is None:
        return ''
    path = HERE / name
    if not path.is_file():
        return ''
    todo = None
    for i, text in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        m = TODO_RE.search(text)
        if m and i <= lineno:
            todo = m.group(1)
    if todo is None:
        return ''
    return '，报错落在 TODO ' + todo + ' 那一段（第 ' + str(lineno) + ' 行）'


# ── 读输出 ────────────────────────────────────────────────────────────────

def get_line(out, prefix):
    """按前缀取出一整行剩下的内容；没打到那一行就返回 None。"""
    for line in out.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def short(value, limit=70):
    text = repr(value)
    return text[:limit] + '…' if len(text) > limit else text


def want_line(out, prefix):
    """取一行并按空格切词，交回词表；没有那一行就交回 None。"""
    raw = get_line(out, prefix)
    return None if raw is None else raw.split()


def parse_pair(text):
    """把 '(0, 1)' 解析成 (0, 1)；解析不了就交回 None。"""
    if text is None:
        return None
    m = re.fullmatch(r'\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)', text.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)))


# ══ 任务 1 · 统计出现次数 ════════════════════════════════════════════════

PROBE_COUNT = '''
import json
import task1_count as t

def show(v):
    if not isinstance(v, dict):
        return '不是字典'
    return {str(k): v[k] for k in sorted(v, key=lambda z: str(z))}

cases = []
data_a = [3, 1, 4, 1, 5, 3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 2, 6]
data_b = ['x', 'y', 'x', 'z', 'y', 'x']
data_c = []
data_d = [7]
for label, items in [('A', data_a), ('B', data_b), ('C', data_c), ('D', data_d)]:
    cases.append([label, show(t.count_list(list(items))), show(t.count_dict(list(items)))])
print('PROBE ' + json.dumps(cases, ensure_ascii=False))
'''


def check_task1():
    checks = []
    run = run_script('task1_count.py')
    if run['status'] != 'ok':
        return [(False, 'task1_count.py 没跑通：' + run['note'])]

    u_list = want_line(run['out'], '列表版 不同元素')
    u_dict = want_line(run['out'], '字典版 不同元素')
    if u_list is None or u_dict is None:
        return [(False, '没看到「列表版 不同元素 …」「字典版 不同元素 …」这两行：'
                        '带 print 的行别改、别删')]

    # 数据是 i % 500 跑 20000 次，不同元素应当是 500
    if u_list and u_list[0] == '500':
        checks.append((True, '列表版去重后得到 500 个不同元素（0..499）'))
    else:
        checks.append((False, '列表版 不同元素 打出 ' + short(' '.join(u_list))
                              + '，期望 500：TODO 1 的去重那段还没写对（'
                              '先把 data 里出现过的值收进 uniq）'))
    if u_dict and u_dict[0] == '500':
        checks.append((True, '字典版的键数是 500'))
    else:
        checks.append((False, '字典版 不同元素 打出 ' + short(' '.join(u_dict))
                              + '，期望 500：TODO 2 的数数那段还没写对'))

    # 两版总次数都应当是 20000
    s_list = want_line(run['out'], '列表版 总次数')
    s_dict = want_line(run['out'], '字典版 总次数')
    for label, got in (('列表版', s_list), ('字典版', s_dict)):
        if got and got[0] == '20000':
            checks.append((True, label + '的总次数是 20000（每个元素都数到了一回）'))
        else:
            checks.append((False, label + ' 总次数 打出 ' + short(' '.join(got or []))
                                  + '，期望 20000：每个元素的次数加起来应当等于数据个数'))

    same = get_line(run['out'], '两版结果逐字一致')
    good = (same == 'True' and s_list and s_list[0] == '20000'
            and s_dict and s_dict[0] == '20000' and u_list and u_list[0] == '500')
    if good:
        checks.append((True, '两版结果逐字一致：列表版与字典版数出来的次数完全相同'))
    elif same == 'True':
        checks.append((False, '两版打出 True，但两版各自的元素个数/总次数还没对上：'
                              '先让上面几行对了，这一条才有意义'))
    else:
        checks.append((False, '两版结果逐字一致 打出 ' + short(same) + '，期望 True：'
                              '两版必须数出完全相同的次数表（先把两段 TODO 都写出来）'))

    # 计数：Counter 与字典版一致
    c_same = get_line(run['out'], 'Counter 与字典版一致')
    if c_same == 'True' and s_dict and s_dict[0] == '20000':
        checks.append((True, '库里现成的计数工具（Counter）与手写字典版结果相同'))
    elif c_same == 'True':
        checks.append((False, 'Counter 与字典版一致 打出 True，但字典版自己的总次数还没对上：'
                              '先让字典版数对，这一行才有意义'))
    else:
        checks.append((False, 'Counter 与字典版一致 打出 ' + short(c_same) + '，期望 True：'
                              '这一行是给好的对照；对不上说明字典版还没数对'))

    # 耗时趋势
    speed = get_line(run['out'], '字典版比列表版快')
    num = None
    if speed:
        m = re.match(r'([\d.]+)', speed)
        if m:
            num = float(m.group(1))
    if num is None:
        checks.append((False, '没读到「字典版比列表版快 … 倍」这一行'))
    elif num >= 5 and u_list and u_list[0] == '500' and s_dict and s_dict[0] == '20000':
        checks.append((True, '字典版比列表版快 ' + m.group(1) + ' 倍（趋势对了：'
                             '列表版是 n×k 次比较，字典版只扫 n 次）'))
    elif num >= 5:
        checks.append((False, '倍数够了，但两版的结果还没对上：'
                              '快慢要在两版都算对的前提下比，先把上面几行修好'))
    else:
        checks.append((False, '字典版只比列表版快 ' + m.group(1) + ' 倍，期望 5 倍以上：'
                              '这一版数据 k=500、n=20000，差距应当明显；'
                              '先确认列表版真的是「对每个不同元素扫一遍整批数据」'))

    checks += probe_count_checks()
    return checks


def probe_count_checks():
    out, err = run_probe(PROBE_COUNT)
    if out is None:
        return [(False, 'task1_count.py 交给判分的两个计数函数用不起来（探针报错）：\n' + err)]
    line = None
    for text in out.splitlines():
        if text.startswith('PROBE '):
            line = text[len('PROBE '):]
    if line is None:
        return [(False, '探针没拿到 task1_count.py 的结果')]
    import json
    try:
        cases = json.loads(line)
    except Exception as exc:
        return [(False, '探针结果读不出来：' + str(exc))]

    checks = []
    for label, got_list, got_dict in cases:
        expect = case_count_expect(label)
        if got_list == got_dict == expect and (label != 'C' or got_list == {}):
            # C 是空数据，两版都交回 {} 本来就对；但它单独对不算数，
            # 要等别的组也对上才算真的实现了（下面的「至少一组长数据对」会管这件事）
            checks.append((True, '判分小数据 ' + label + '：两版都是 ' + short(expect, 50)))
        elif got_list != got_dict:
            checks.append((False, '判分小数据 ' + label + '：列表版交回 ' + short(got_list, 50)
                                  + '，字典版交回 ' + short(got_dict, 50)
                                  + '，两版必须逐字一致'))
        else:
            checks.append((False, '判分小数据 ' + label + '：两版都交回 ' + short(got_list, 50)
                                  + '，期望 ' + short(expect, 50)))
    # 空数据那一组本来就「碰巧对」：只有当有数据的组也对上，才算真的实现了
    real = [c for c in cases if c[0] != 'C']
    if real and all(c[1] == c[2] == case_count_expect(c[0]) for c in real):
        checks.append((True, '有数据的三组也都对上了：两个计数函数是真的实现了，'
                             '不是空交回'))
    else:
        checks.append((False, '有数据的几组还没对上（空数据那一组碰巧对不算数）：'
                              'TODO 3 与 TODO 4 要真的实现两个计数函数'))
    return checks


def case_count_expect(label):
    if label == 'A':
        return {'1': 4, '2': 2, '3': 3, '4': 2, '5': 4, '6': 2, '8': 1, '9': 2}
    if label == 'B':
        return {'x': 3, 'y': 2, 'z': 1}
    if label == 'C':
        return {}
    return {'7': 1}


# ══ 任务 2 · 第一个重复出现的元素 ════════════════════════════════════════

PROBE_REPEAT = '''
import json
import task2_first_repeat as t

cases = []
sets = [
    ('A', [7, 9, 2, 8, 4, 6, 4, 1, 3, 4, 2, 8], 4),
    ('B', [1, 2, 3, 4], None),
    ('C', [], None),
    ('D', [5, 5], 5),
    ('E', ['a', 'b', 'a'], 'a'),
    ('F', ['x', 'y', 'z'], None),
]
for label, items, want in sets:
    cases.append([label, t.first_repeat_list(list(items)), t.first_repeat_set(list(items)), want])
print('PROBE ' + json.dumps(cases, ensure_ascii=False))
'''


def check_task2():
    checks = []
    run = run_script('task2_first_repeat.py')
    if run['status'] != 'ok':
        return [(False, 'task2_first_repeat.py 没跑通：' + run['note'])]

    pair = [want_line(run['out'], p) for p in
            ('列表版 第一个重复', '集合版 第一个重复')]
    names = ('列表版', '集合版')
    for name, got in zip(names, pair):
        if got is None:
            checks.append((False, '没看到「' + name + ' 第一个重复 …」这一行：带 print 的行别改'))
            continue
        if got and got[0] == '7':
            checks.append((True, name + '找到的第一个重复是 7（下标 2000 那个，前面出现过）'))
        else:
            checks.append((False, name + ' 第一个重复 打出 ' + short(' '.join(got))
                                  + '，期望 7：要在扫到它的那一刻就停下并交出它，'
                                    '不能扫完再回头找'))

    same = get_line(run['out'], '两版结果逐字一致')
    if same == 'True' and all(g and g[0] == '7' for g in pair):
        checks.append((True, '两版结果逐字一致，而且都在 7 上停下'))
    elif same == 'True':
        checks.append((False, '两版打出 True，但两版找到的元素还不是 7：先让上面两行对了'))
    else:
        checks.append((False, '两版结果逐字一致 打出 ' + short(same) + '，期望 True：'
                              '列表版与集合版必须交出同一个元素'))

    speed = get_line(run['out'], '列表版比集合版慢')
    num = None
    if speed:
        m = re.match(r'([\d.]+)', speed)
        if m:
            num = float(m.group(1))
    if num is None:
        checks.append((False, '没读到「列表版比集合版慢 … 倍」这一行'))
    elif num >= 3 and all(g and g[0] == '7' for g in pair):
        checks.append((True, '列表版比集合版慢 ' + m.group(1) + ' 倍（趋势对了：'
                             '列表的 in 要挨个比，集合走哈希）'))
    elif num >= 3:
        checks.append((False, '倍数够了，但两版找到的元素还不是 7：'
                              '快慢要在两版都算对的前提下比，先把上面两行修好'))
    else:
        checks.append((False, '列表版只比集合版慢 ' + m.group(1) + ' 倍，期望 3 倍以上：'
                              '确认列表版真的是列表 in（不是顺手也用了集合）'))

    checks += probe_repeat_checks()
    return checks


def probe_repeat_checks():
    out, err = run_probe(PROBE_REPEAT)
    if out is None:
        return [(False, 'task2_first_repeat.py 交给判分的两个函数用不起来（探针报错）：\n' + err)]
    line = None
    for text in out.splitlines():
        if text.startswith('PROBE '):
            line = text[len('PROBE '):]
    if line is None:
        return [(False, '探针没拿到 task2_first_repeat.py 的结果')]
    import json
    try:
        cases = json.loads(line)
    except Exception as exc:
        return [(False, '探针结果读不出来：' + str(exc))]

    checks = []
    for label, got_list, got_set, want in cases:
        ok = (got_list == got_set == want)
        if ok:
            checks.append((True, '判分小数据 ' + label + '：两版都交出 ' + short(want)))
        elif got_list != got_set:
            checks.append((False, '判分小数据 ' + label + '：列表版交出 ' + short(got_list)
                                  + '，集合版交出 ' + short(got_set) + '，两版必须一致'))
        else:
            checks.append((False, '判分小数据 ' + label + '：两版都交出 ' + short(got_list)
                                  + '，期望 ' + short(want)
                                  + ('' if label != 'B' else '（没有重复时要交出 None）')
                                  + ('' if label != 'D' else '（[5, 5] 的第一个重复就是 5）')))
    return checks


# ══ 任务 3 · 两数之和（先查后存是重点）════════════════════════════════════

PROBE_TWO_SUM = '''
import json
import task3_two_sum as t

cases = []
sets = [
    ('A', [2, 7, 11, 15], 9),
    ('B', [3, 3], 6),
    ('C', [1, 2], 100),
    ('D', [], 5),
    ('E', [4], 8),
    ('F', [0, 0], 0),
    ('G', [1, 2, 3, 4, 5], 9),
    ('H', [-3, 4, 3, 90], 0),
]
for label, nums, target in sets:
    cases.append([label, list(t.two_sum_list(list(nums), target)),
                  list(t.two_sum_dict(list(nums), target))])
print('PROBE ' + json.dumps(cases, ensure_ascii=False))
'''

TWO_SUM_WANT = {
    'A': [0, 1], 'B': [0, 1], 'C': [-1, -1], 'D': [-1, -1],
    'E': [-1, -1], 'F': [0, 1], 'G': [3, 4], 'H': [0, 2],
}


def check_task3():
    checks = []
    run = run_script('task3_two_sum.py')
    if run['status'] != 'ok':
        return [(False, 'task3_two_sum.py 没跑通：' + run['note'])]

    l_big = want_line(run['out'], '列表版 大数据')
    d_big = want_line(run['out'], '字典版 大数据')
    if l_big is None or d_big is None:
        return [(False, '没看到「列表版 大数据 …」「字典版 大数据 …」这两行：'
                        '带 print 的行别改、别删')]
    # big 是 0,2,4,... 两版都应当找到一对下标
    for name, got in (('列表版', l_big), ('字典版', d_big)):
        text = ''.join(got[:2]) if len(got) >= 2 else ''.join(got)
        if text.startswith('(') and text.endswith(')') and text != '(-1,-1)':
            checks.append((True, name + '在 20000 个偶数上找到了一对下标 ' + text))
        else:
            checks.append((False, name + ' 大数据 打出 ' + short(' '.join(got))
                                  + '：大数据里应当能找到一对（两个 TODO 都要接上）'))

    same = get_line(run['out'], '两版结果逐字一致')
    if same == 'True' and l_big[0].startswith('(') and not l_big[0].startswith('(-1'):
        checks.append((True, '两版在大数据上结果逐字一致'))
    elif same == 'True':
        checks.append((False, '两版打出 True，但两版都还没找到答案（都是 (-1, -1)）：'
                              '两版一致要在两版都算对的前提下才算数，把两个 TODO 写出来'))
    else:
        checks.append((False, '两版结果逐字一致 打出 ' + short(same) + '，期望 True：'
                              '同样的数据、同样的答案，两版必须交出同一对下标'))

    speed = get_line(run['out'], '字典版比列表版快')
    num = None
    if speed:
        m = re.match(r'([\d.]+)', speed)
        if m:
            num = float(m.group(1))
    if num is None:
        checks.append((False, '没读到「字典版比列表版快 … 倍」这一行'))
    elif num >= 20 and l_big[0].startswith('(') and not l_big[0].startswith('(-1'):
        checks.append((True, '字典版比列表版快 ' + m.group(1) + ' 倍（两个嵌套循环是 '
                             'n(n-1)/2 次比较，一遍哈希是 n 次）'))
    elif num >= 20:
        checks.append((False, '倍数够了，但两版在大数据上还没找到答案：'
                              '快慢要在两版都算对的前提下比'))
    else:
        checks.append((False, '字典版只比列表版快 ' + m.group(1) + ' 倍，期望 20 倍以上：'
                              '这一版数据 n=20000，两层循环约 2 亿次比较，'
                              '差距应当很大；确认字典版真的只扫了一遍'))

    # 小数据逐组：两版一致（还要至少一组真的找到了，否则是两版都空交回）
    # 行格式： 小数据 普通 (0, 1) 列表版 (0, 1) 一致 True
    #          [0]=label [1]=字典版 [2]='列表版' [3]=列表版 [4]='一致' [5]=True
    cases = {}
    for line in run['out'].splitlines():
        if line.startswith('小数据 '):
            parts = line[len('小数据 '):].split()
            if len(parts) >= 6:
                cases[parts[0]] = parts
    bad_small = 0
    found_small = 0
    for label, parts in cases.items():
        if parts[-1] != 'True':
            bad_small += 1
        if parts[1] != '(-1,-1)' or parts[3] != '(-1,-1)':
            found_small += 1
    if cases and not bad_small and found_small >= 3:
        checks.append((True, '五组小数据（普通 / 两个相同的数 / 找不到 / 空表 / 单个元素）'
                             '两版都逐字一致，其中 ' + str(found_small) + ' 组找到了答案'))
    elif cases and bad_small:
        checks.append((False, '五组小数据里有 ' + str(bad_small) + ' 组两版不一致：'
                              '两版必须在每一组上都交出同一个结果'))
    elif cases:
        checks.append((False, '五组小数据两版都一致，但五组都交回 (-1, -1)：'
                              '这是两个 TODO 都还没写的默认值，不是答案；'
                              '「普通」那组应当是 (0, 1)、「两个相同的数」应当是 (0, 1)'))
    else:
        checks.append((False, '没看到「小数据 …」这几行：带 print 的行别改、别删'))

    checks += probe_two_sum_checks()
    return checks


def probe_two_sum_checks():
    out, err = run_probe(PROBE_TWO_SUM)
    if out is None:
        return [(False, 'task3_two_sum.py 交给判分的两个函数用不起来（探针报错）：\n' + err)]
    line = None
    for text in out.splitlines():
        if text.startswith('PROBE '):
            line = text[len('PROBE '):]
    if line is None:
        return [(False, '探针没拿到 task3_two_sum.py 的结果')]
    import json
    try:
        cases = json.loads(line)
    except Exception as exc:
        return [(False, '探针结果读不出来：' + str(exc))]

    checks = []
    for label, got_list, got_dict in cases:
        want = TWO_SUM_WANT[label]
        note = {'B': '（[3, 3] 的答案是 (0, 1)：先查后存，当前元素还没入表，配不上自己）',
                'F': '（[0, 0] 目标 0，同样是 (0, 1)）',
                'G': '（只有 4 + 5 = 9，答案是 (3, 4)）',
                'H': '（-3 + 3 = 0，答案是 (0, 2)）'}.get(label, '')
        if got_list == got_dict == want:
            checks.append((True, '判分小数据 ' + label + '：两版都是 ' + short(want) + note))
        elif got_list != got_dict:
            checks.append((False, '判分小数据 ' + label + '：列表版交出 ' + short(got_list)
                                  + '，字典版交出 ' + short(got_dict)
                                  + '，两版必须一致' + note))
        else:
            hint = ''
            if label == 'B' and got_dict == [0, 0]:
                hint = ('——这是「先存后查」写反了：当前元素已经入表，于是配上了自己；'
                        '改成先查 need、再存 x')
            elif label == 'B' and got_dict == [1, 1]:
                hint = '——同一个元素用了两次（i 与 j 必须不同）'
            checks.append((False, '判分小数据 ' + label + '：两版都交出 ' + short(got_dict)
                                  + '，期望 ' + short(want) + note + hint))
    return checks


# ══ 任务 4 · 手工算哈希值与桶号 ══════════════════════════════════════════

PROBE_BUCKETS = '''
import json
import task4_hash_buckets as t

cases = []
cases.append(['one', t.bucket_of('apple', 8), t.bucket_of('apple', 8)])
cases.append(['same', t.bucket_of('apple', 16), t.bucket_of('apple', 16)])
cases.append(['range8', 0 <= t.bucket_of('apple', 8) < 8, 0 <= t.bucket_of('banana', 8) < 8])
cases.append(['range16', 0 <= t.bucket_of('apple', 16) < 16, 0 <= t.bucket_of('banana', 16) < 16])
c8 = t.conflicts(['apple', 'banana', 'cherry', 'date', 'fig', 'grape', 'kiwi'], 8)
c16 = t.conflicts(['apple', 'banana', 'cherry', 'date', 'fig', 'grape', 'kiwi'], 16)
cases.append(['conf8', list(c8), list(c16)])
cases.append(['drawer', list(t.conflicts(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'], 8)),
              list(t.conflicts(['a', 'b'], 8))])
print('PROBE ' + json.dumps(cases, ensure_ascii=False))
'''


def check_task4():
    checks = []
    runs = []
    for _ in range(2):
        run = run_script('task4_hash_buckets.py')
        if run['status'] != 'ok':
            return [(False, 'task4_hash_buckets.py 没跑通：' + run['note'])]
        runs.append(run)

    first, second = runs

    def rows(run, buckets):
        """按「桶数 <n>」那一行分段，只收该段里的键行（别让 16 桶那段覆盖 8 桶那段）。"""
        got = {}
        current = None
        for line in run['out'].splitlines():
            m = re.match(r'^桶数 (\d+)$', line)
            if m:
                current = int(m.group(1))
                continue
            if current != buckets:
                continue
            m = re.match(r'^键 (\S+) 哈希值 (-?\d+) 桶号 (\d+)$', line)
            if m:
                got[m.group(1)] = (int(m.group(2)), int(m.group(3)))
        return got

    r8a, r8b = rows(first, 8), rows(second, 8)
    r16 = rows(first, 16)
    if len(r8a) != 7:
        return [(False, '8 个桶那一轮应当打出 7 个键的「键 … 哈希值 … 桶号 …」行，'
                        '实际 ' + str(len(r8a)) + ' 行：TODO 1 还没写对（'
                        '那一行 print 是判分接口，别改）')]
    if len(r16) != 7:
        return [(False, '16 个桶那一轮应当打出 7 行，实际 ' + str(len(r16))
                        + ' 行：TODO 3 还没写对')]

    # 桶号范围（先确认哈希值不是占位的 0，否则「0 % 8 = 0」会假通过）
    all_zero = all(hv == 0 for hv, _ in r8a.values())
    bad = [k for k, (hv, slot) in r8a.items() if not (0 <= slot < 8) or hv % 8 != slot]
    if all_zero:
        checks.append((False, '8 个桶：七个键的哈希值全是 0 —— TODO 1 的 hv = hash(k) 还没写'
                              '（现在打的是占位值）'))
    elif not bad:
        checks.append((True, '8 个桶：每个键的桶号都等于 hash(k) % 8，而且落在 0..7 里'))
    else:
        checks.append((False, '8 个桶：这些键的桶号与 hash(k) % 8 对不上 —— ' + '、'.join(bad)
                              + '（TODO 1 的取余那一步）'))
    all_zero16 = all(hv == 0 for hv, _ in r16.values())
    bad16 = [k for k, (hv, slot) in r16.items() if not (0 <= slot < 16) or hv % 16 != slot]
    if all_zero16:
        checks.append((False, '16 个桶：七个键的哈希值全是 0 —— TODO 3 还没写'))
    elif not bad16:
        checks.append((True, '16 个桶：每个键的桶号都等于 hash(k) % 16，落在 0..15 里'))
    else:
        checks.append((False, '16 个桶：这些键的桶号与 hash(k) % 16 对不上 —— ' + '、'.join(bad16)))

    # 跨进程：哈希值一定不同（字符串哈希带随机种子）
    def hv_map(r):
        return {k: v[0] for k, v in r.items()}

    cross_same = (hv_map(r8a) == hv_map(r8b))
    if all_zero:
        checks.append((False, '两次运行的哈希值都是占位的 0：TODO 1 要算 hash(k)，'
                              '跨进程不同这件事才有得看'))
    elif not cross_same:
        checks.append((True, '跨进程哈希值不同：同样七个键，两次运行算出来的哈希值不一样 —— '
                             '字符串哈希带随机种子（本机 siphash13、seed_bits 128）'))
    else:
        checks.append((False, '两次运行的哈希值完全相同，期望不同：字符串哈希在进程启动时会加随机种子。'
                              '（若确实相同，检查是不是把哈希值写成了常量）'))

    # 同一次运行内部：同一个键算两次要一致（进程内稳定），这一条在下面「同进程内哈希值稳定」那行验；
    # 桶号也跟着跨进程变，所以这里不再比对两次运行的桶号，只看每一次内部「桶号 = 哈希值 % 桶数」。
    if all_zero:
        checks.append((False, '桶号现在是占位值，先让 TODO 1 算出真的桶号'))
    else:
        checks.append((True, '两次运行各自内部都满足「桶号 = 哈希值 % 桶数」：'
                             '哈希值换了，桶号也就跟着换——这是同一件事的两面'))

    # 冲突计数
    def conflict_row(run, buckets, label):
        return want_line(run['out'], str(buckets) + ' 个桶 ' + label)

    c8 = conflict_row(first, 8, '装了不止一个键的桶数')
    m8 = conflict_row(first, 8, '桶里最多装了')
    c16 = conflict_row(first, 16, '装了不止一个键的桶数')
    real8 = count_conflicts({k: v[1] for k, v in r8a.items()}, 8)
    real16 = count_conflicts({k: v[1] for k, v in r16.items()}, 16)
    conflict8_ok = bool(c8 and c8[0].isdigit() and int(c8[0]) == real8[0] and not all_zero)
    conflict16_ok = bool(c16 and c16[0].isdigit() and int(c16[0]) == real16[0] and not all_zero16)
    if conflict8_ok:
        checks.append((True, '8 个桶里有 ' + str(real8[0]) + ' 个桶装了不止一个键（数对了）'))
    else:
        checks.append((False, '8 个桶 装了不止一个键的桶数 打出 ' + short(' '.join(c8 or []))
                              + '，按你打出来的桶号数应当是 ' + str(real8[0])
                              + '：TODO 2 的统计还没写对'))
    if m8 and m8[0].isdigit() and int(m8[0]) == real8[1]:
        checks.append((True, '8 个桶里最多的那个装了 ' + str(real8[1]) + ' 个键'))
    else:
        checks.append((False, '8 个桶 桶里最多装了 打出 ' + short(' '.join(m8 or []))
                              + '，按你打出来的桶号应当是 ' + str(real8[1])))

    # 抽屉原理：10 个键放 8 个桶一定有冲突（用探针的 conflicts 验）
    if conflict16_ok:
        checks.append((True, '16 个桶里有 ' + str(real16[0]) + ' 个桶装了不止一个键（数对了）'))
    else:
        checks.append((False, '16 个桶 装了不止一个键的桶数 打出 ' + short(' '.join(c16 or []))
                              + '，按你打出来的桶号应当是 ' + str(real16[0])
                              + '：TODO 4 的统计还没写对'))

    if real8[0] >= 1 and not all_zero:
        checks.append((True, '7 个键放 8 个桶就出现了冲突（' + str(real8[0]) + ' 个桶装了不止一个）—— '
                             '桶数不比键数多时，冲突是常态'))
    else:
        checks.append((False, '还没数出冲突：先让 TODO 1 算出真的桶号、TODO 2 数出冲突桶数'))
    trend = get_line(first['out'], '桶变多了 冲突没变多')
    if trend == 'True' and conflict8_ok and conflict16_ok and real8[0] >= 1:
        checks.append((True, '桶从 8 个加到 16 个之后，冲突没有变多（桶多了每桶平均键数就少了）'))
    elif trend == 'True':
        checks.append((False, '桶变多了 冲突没变多 打出 True，但两个冲突数还没数对：'
                              '先让 TODO 2 与 TODO 4 的数法对了，这一行才有意义'))
    else:
        checks.append((False, '桶变多了 冲突没变多 打出 ' + short(trend) + '，期望 True'))

    stable = get_line(first['out'], '同进程内哈希值稳定')
    if stable == 'True' and not all_zero:
        checks.append((True, "同一个进程内 hash('apple') 两次结果一致 —— 哈希值在进程内是稳定的"))
    elif stable == 'True':
        checks.append((False, '同进程内哈希值稳定 打出 True，但哈希值还是占位的 0：'
                              '先让 TODO 1 真的算一次 hash(k)，这一行才有意义'))
    else:
        checks.append((False, '同进程内哈希值稳定 打出 ' + short(stable) + '，期望 True：'
                              '跨进程变、进程内不变，这两件事要分清楚'))

    # 原因那一行
    reason = get_line(first['out'], '原因')
    if reason is None:
        checks.append((False, '没看到「原因 …」这一行：带 print 的行别改、别删'))
    elif reason.startswith('TODO'):
        checks.append((False, 'TODO 7 还没写：把「哈希值跨进程为什么会不同」用一两句话写进 reason'))
    elif len(reason) >= 10:
        checks.append((True, '写下了原因（' + str(len(reason)) + ' 字）：'
                             + short(reason, 60)))
    else:
        checks.append((False, '原因 只写了 ' + short(reason) + '，太短：'
                              '要说清「进程启动时给哈希加了随机种子」以及「为什么要加」'))

    checks += probe_bucket_checks()
    return checks


def count_conflicts(slots_by_key, buckets):
    """按 {键: 桶号} 数 (装了不止一个键的桶数, 最多几个键)。"""
    counts = {}
    for slot in slots_by_key.values():
        counts[slot] = counts.get(slot, 0) + 1
    conflict = sum(1 for v in counts.values() if v > 1)
    most = max(counts.values()) if counts else 0
    return (conflict, most)


def probe_bucket_checks():
    out, err = run_probe(PROBE_BUCKETS)
    if out is None:
        return [(False, 'task4_hash_buckets.py 交给判分的函数用不起来（探针报错）：\n' + err)]
    line = None
    for text in out.splitlines():
        if text.startswith('PROBE '):
            line = text[len('PROBE '):]
    if line is None:
        return [(False, '探针没拿到 task4_hash_buckets.py 的结果')]
    import json
    try:
        cases = json.loads(line)
    except Exception as exc:
        return [(False, '探针结果读不出来：' + str(exc))]

    data = {name: vals for name, *vals in cases}
    checks = []

    one = data.get('one')
    if one and one[0] == one[1] and isinstance(one[0], int) and one[0] != 0:
        checks.append((True, 'bucket_of 同一个键算两次结果一致'))
    elif one and one[0] == one[1] and one[0] == 0:
        checks.append((False, 'bucket_of 交回 0（TODO 5 还没写）：它要交回 hash(key) % buckets'))
    else:
        checks.append((False, 'bucket_of 交回 ' + short(one) + '：同一个键算两次要一致'
                              '（TODO 5）'))

    rng8, rng16 = data.get('range8'), data.get('range16')
    if rng8 == [True, True] and rng16 == [True, True] and one and one[0] != 0:
        checks.append((True, 'bucket_of 的桶号落在 0..桶数-1 里（8 与 16 都对）'))
    elif one and one[0] == 0:
        checks.append((False, 'bucket_of 的桶号恒为 0，看不出落位对不对：'
                              '先让 TODO 5 真的算一次 hash(key) % buckets'))
    else:
        checks.append((False, 'bucket_of 的桶号越界了（8 个桶得到 ' + short(rng8)
                              + '，16 个桶得到 ' + short(rng16) + '）：别忘了对桶数取余'))

    conf8, conf16 = data.get('conf8'), data.get('conf16')
    # conflicts 交回 (桶数, 最多几个)；JSON 序列化后是 [[装了几个的桶数, 最多的键数], ...]
    def unpack(pair):
        if isinstance(pair, list) and len(pair) == 2 and isinstance(pair[0], list) \
                and len(pair[0]) == 2:
            return tuple(pair[0])
        return None

    got8 = unpack(conf8)
    if got8 and got8[0] >= 1:
        checks.append((True, 'conflicts 在 8 个桶上数出 ' + str(list(got8)) + '：7 个键进 8 个桶，'
                             '确实出现了冲突'))
    else:
        checks.append((False, 'conflicts(七个键, 8) 交回 ' + short(conf8)
                              + '，期望「不止一个键的桶数 ≥ 1」：TODO 6 还没写对'))

    drawer = data.get('drawer')
    ten = unpack(drawer) if isinstance(drawer, list) and len(drawer) == 2 else None
    if ten and ten[0] >= 1:
        checks.append((True, '抽屉原理：10 个键放 8 个桶，conflicts 数出 ' + str(list(ten))
                             + '——一定装不下，冲突必然存在'))
    else:
        checks.append((False, 'conflicts(十个键, 8) 交回 ' + short(drawer)
                              + '，期望至少 1：10 个键放进 8 个桶按抽屉原理一定有桶装 2 个以上'))
    return checks


# ══ 任务 5 · 什么能当键 ══════════════════════════════════════════════════

PROBE_KEYS = '''
import json
import task5_key_rules as t

h1 = t.hash_of('abc')
h2 = t.hash_of('abc')
print('PROBE ' + json.dumps([h1, h2], ensure_ascii=False))
'''


def check_task5():
    checks = []
    run = run_script('task5_key_rules.py')
    if run['status'] != 'ok':
        return [(False, 'task5_key_rules.py 没跑通：' + run['note'])]

    err_type = get_line(run['out'], '列表当键 异常类型')
    err_msg = get_line(run['out'], '列表当键 报错说')
    if err_type == 'TypeError':
        checks.append((True, '列表当键报的是 TypeError（不是 KeyError，也不是别的）'))
    else:
        checks.append((False, '列表当键 异常类型 打出 ' + short(err_type) + '，期望 TypeError：'
                              'TODO 1 要用 try / except 接住 d[[1, 2]] 抛出的异常'))
    if err_msg and 'list' in err_msg and 'unhashable' in err_msg:
        checks.append((True, '报错话里指名了 list 不可哈希：' + short(err_msg, 70)))
    else:
        checks.append((False, '列表当键 报错说 打出 ' + short(err_msg)
                              + '，期望话里带 unhashable 与 list'))

    mentions = get_line(run['out'], '列表当键 提到 dict key')
    if mentions == 'True':
        checks.append((True, "新版 Python 的措辞里确实有 “dict key” 这一句"
                             "（cannot use 'list' as a dict key …）"))
    else:
        checks.append((False, '列表当键 提到 dict key 打出 ' + short(mentions) + '，期望 True：'
                              '新版把这个报错写得更直白了'))

    cell = get_line(run['out'], '元组当键 取到')
    missing = get_line(run['out'], '元组当键 键不存在时 get 交回')
    if cell == 'A' and missing == 'None':
        checks.append((True, '元组可以当键（取到 A）；键不在时 get 交回默认值 None，不报 KeyError'))
    else:
        checks.append((False, '元组当键 打出 取到 ' + short(cell) + ' / 不存在时 ' + short(missing)
                              + '，期望 A 与 None：元组里的元素可哈希，元组就可哈希；'
                                '取不存在的键用 get'))

    by_float = get_line(run['out'], '浮点当键 0.1+0.2 取到')
    by_round = get_line(run['out'], '浮点当键 先 round 再取到')
    neq = get_line(run['out'], '浮点当键 不相等')
    if by_float == 'None' and by_round == '零点三元' and neq == 'True':
        checks.append((True, '浮点当键：0.1 + 0.2 取不到（是另一把键），'
                             'round 到固定小数位之后就取到了'))
    else:
        checks.append((False, '浮点当键 打出 不 round 时 ' + short(by_float)
                              + ' / round 之后 ' + short(by_round) + ' / 不相等 ' + short(neq)
                              + '，期望 None / 零点三元 / True：'
                                '0.1 + 0.2 的真实值是 0.30000000000000004，'
                                '与 0.3 是两把不同的键；先 round 到固定小数位再当键'))

    stable = get_line(run['out'], '同进程内两次一致')
    same_obj = get_line(run['out'], '相同内容不同对象也一致')
    if stable == 'True' and same_obj == 'True':
        checks.append((True, '同一个进程内：同一个串两次一致，内容相同的两个串也一致'))
    else:
        checks.append((False, '同进程内两次一致 ' + short(stable) + '、'
                              '相同内容不同对象也一致 ' + short(same_obj) + '，都期望 True：'
                              '相等的对象哈希值必须相同'))

    equal_hash = get_line(run['out'], '相等则哈希相同')
    if equal_hash == 'True':
        checks.append((True, '1 与 1.0 相等，哈希值也相同 —— 可哈希的定义里那一条'))
    else:
        checks.append((False, '相等则哈希相同 打出 ' + short(equal_hash) + '，期望 True'))

    checks += probe_key_checks()
    return checks


def probe_key_checks():
    """起两个进程分别算 hash('abc')，比对跨进程结果。"""
    outs = []
    for _ in range(2):
        out, err = run_probe(PROBE_KEYS)
        if out is None:
            return [(False, 'task5_key_rules.py 交给判分的 hash_of 用不起来（探针报错）：\n' + err)]
        line = None
        for text in out.splitlines():
            if text.startswith('PROBE '):
                line = text[len('PROBE '):]
        if line is None:
            return [(False, '探针没拿到 task5_key_rules.py 的 hash_of 结果')]
        import json
        try:
            outs.append(json.loads(line))
        except Exception as exc:
            return [(False, '探针结果读不出来：' + str(exc))]

    checks = []
    (a1, a2), (b1, b2) = outs
    if a1 is not None and a1 != 0 and a1 == a2:
        checks.append((True, "同一个进程里 hash_of('abc') 两次一致（哈希值进程内稳定）"))
    else:
        checks.append((False, "hash_of('abc') 两次得到 " + short([a1, a2])
                              + '，期望两次相同且不是 0：TODO 4 要交回 hash(text)'))
    if a1 != 0 and a1 != b1:
        checks.append((True, "跨进程 hash_of('abc') 不同（" + short(a1) + ' vs ' + short(b1)
                             + '）—— 进程启动时的随机种子在起作用'))
    elif a1 == 0:
        checks.append((False, 'hash_of 交回 0，TODO 4 还没写'))
    else:
        checks.append((False, '两次进程算出同一个哈希值（' + short(a1) + '），期望不同：'
                              '字符串哈希带随机种子；若确实相同，检查是不是把结果写成了常量'))
    return checks


# ══ 主流程 ════════════════════════════════════════════════════════════════

CHECKERS = {
    'task1_count.py': check_task1,
    'task2_first_repeat.py': check_task2,
    'task3_two_sum.py': check_task3,
    'task4_hash_buckets.py': check_task4,
    'task5_key_rules.py': check_task5,
}


def main():
    print('StudyMate lab 0016 · 自动判分（为什么字典查得那么快）')
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
        print('五个任务都过了，再对照 ../solutions/0016-hash-table/ 看参考解。')
        return 1
    print('五个任务都过了。现在去对照 ../solutions/0016-hash-table/：')
    print('比一比你的两版写法与参考解，再用一句话回答「这三题里，哪一行决定了快慢」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
