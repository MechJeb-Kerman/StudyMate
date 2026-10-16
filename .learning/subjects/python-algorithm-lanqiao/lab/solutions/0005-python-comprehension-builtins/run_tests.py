#!/usr/bin/env python3
"""lab 0005 · 自动判分：跑任务脚本，比对输出。

用法（在 lab/0005-python-comprehension-builtins/ 目录里）：

    py run_tests.py

判法：
  - 每个任务单独起一个进程跑，只看 stdout 里的固定格式行，不 import 学生代码
    （唯一例外是任务 3：它交给判分一个函数接口，判分另起一个探针进程 import 它，
    看它交回来的到底是生成器还是列表，以及 len / 下标报什么错）；
  - 任务 1 用 loops_original.py（给好的循环版基准）当标准，逐行比对十个结果；
  - 任务 1 末尾另有一条总检：大纲要求 enumerate、zip、sorted(key=)、sum、max、any、
    all、map 各至少改写一处，这条查两个改写文件里这八个名字出现了没有；
  - 断言里的值来自课件的口径：推导式与循环版结果相同、目标名不泄漏、生成器只能走
    一遍且没有 len 也不能下标、zip 截断到最短、enumerate 的 start、sorted 返回新表、
    list.sort 返回 None、any([]) 是 False、all([]) 是 True。

退出码：0 = 六个任务都通过；1 = 还有没通过的。
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

BASELINE = 'loops_original.py'          # 十段循环的基准（给好的，别改）
TIMEOUT = 60

TODO_RE = re.compile(r'TODO\s+(\d+)')
FILE_LINE_RE = re.compile(r'File "([^"]*)", line (\d+)')


# ── 跑脚本 ────────────────────────────────────────────────────────────────

def run_script(name, stdin_text=''):
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
            [sys.executable, str(path)],
            cwd=str(HERE), env=env, timeout=TIMEOUT,
            input=stdin_text,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'out': '', 'err': '',
                'note': '跑了 ' + str(TIMEOUT) + ' 秒还没结束（死循环？在等输入？）'}
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-5:])
        note = ('脚本报错退出（退出码 ' + str(done.returncode) + '）'
                + todo_hint(name, done.stderr or '') + '：\n' + tail)
        return {'status': 'crash', 'out': done.stdout or '', 'err': done.stderr or '',
                'note': note}
    return {'status': 'ok', 'out': done.stdout or '', 'err': '', 'note': ''}


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


def get_lines(out, prefix):
    """按前缀取出所有匹配行剩下的内容（同一行打多次时用）。"""
    return [line[len(prefix):].strip() for line in out.splitlines() if line.startswith(prefix)]


def label_map(out):
    """把「01 平方 [9, …]」这样的行拆成 {编号: 结果}。"""
    got = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split(' ', 1)
        got[parts[0]] = parts[1].strip() if len(parts) > 1 else ''
    return got


def short(value, limit=70):
    """消息里的值太长就截断，别把一行撑爆。"""
    text = repr(value)
    if len(text) > limit:
        return text[:limit] + '…'
    return text


# ── 通用判定：按前缀逐行比期望值 ─────────────────────────────────────────

def check_fixed(filename, want, needs=None):
    """want: [(前缀, 期望值, 通过时的一句话, 对不上时的提示), …]。

    needs: {前缀: (依赖的前缀, 依赖的期望值, 提示)} —— 有些行在原样没填时也能「碰巧对」，
    那一条只有等被依赖的那行也对了才算数。
    """
    run = run_script(filename)
    if run['status'] != 'ok':
        return [(False, filename + ' 没跑通：' + run['note'])]
    got = {}
    for prefix, expect, _good, _hint in want:
        if isinstance(expect, list):
            found = get_lines(run['out'], prefix)
            got[prefix] = found if found else None
        else:
            got[prefix] = get_line(run['out'], prefix)

    checks = []
    for prefix, expect, good, hint in want:
        value = got[prefix]
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删'))
            continue
        if value != expect:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + short(expect)
                           + '：' + hint))
            continue
        need = (needs or {}).get(prefix)
        if need and got.get(need[0]) != need[1]:
            checks.append((False, prefix + ' 是 ' + short(value) + '，但「' + need[0]
                           + '」还没对：' + need[2] + '，这一条才有意义'))
            continue
        checks.append((True, good))
    return checks


# ── 任务 1 · 十段循环逐段改写 ────────────────────────────────────────────

TASK1_HINTS = {
    '01': 'TODO 01：这一段是「建空表 + append(算出什么)」，换成列表推导式'
          '（方括号里先写算出什么、再写 for 子句，末尾不写冒号）',
    '02': 'TODO 02：筛选的条件写在方括号最后（带 if 的列表推导式）',
    '03': 'TODO 03：累加循环换成一个现成的求和函数，把 data 整批交给它',
    '04': 'TODO 04：擂主那套循环换成一个现成的求最大值函数',
    '05': 'TODO 05：这是「数有几个」，不是「求和」——喂给求和函数的应该是每个满足条件的'
          '元素算作 1（写成生成器表达式，别建表）',
    '06': 'TODO 06：先设 False 再置位的判定，换成「存在一个满足就为真」的那个函数',
    '07': 'TODO 07：先设 True 再翻成 False 的判定，换成「全部满足才为真」的那个函数'
          '（注意条件要与循环版一致：非负）',
    '08': 'TODO 08：表达式写「算出什么」——这里要的是每个词的长度，不是词本身',
    '09': 'TODO 09：转换用的函数（int）已经有现成的，把它与列表交给 map，再用 list 收成表',
    '10': 'TODO 10：key 要交回一个元组：分数降序（第一项取负号）、同分编号升序；'
          '排序那一行用 sorted(records, key=你的键函数)',
}

REWRITE_BUILTINS = [
    ('sum(', 'task1_rewrite.py', '03 总和 / 05 计数'),
    ('max(', 'task1_rewrite.py', '04 最大'),
    ('any(', 'task1_rewrite.py', '06 有没有大于 5 的'),
    ('all(', 'task1_rewrite.py', '07 是不是全部非负'),
    ('map(', 'task1_rewrite.py', '09 一串字符串转整数'),
    ('sorted(', 'task1_rewrite.py', '10 排行榜'),
    ('enumerate(', 'task4_zip_enum.py', '01 编号 / 02 enumerate 表'),
    ('zip(', 'task4_zip_enum.py', '01 / 04 / 06 / 07 几处配对'),
]


def strip_comments(text):
    """把 # 注释去掉再找函数名：注释里写到的名字不算「用过」。"""
    return '\n'.join(line.split('#', 1)[0] for line in text.splitlines())


def coverage_checks():
    """大纲要求：enumerate、zip、sorted(key=)、sum、max、any、all、map 各至少改一处。"""
    missing = []
    for name, filename, where in REWRITE_BUILTINS:
        path = HERE / filename
        if not path.is_file():
            missing.append(name.strip('(') + '（' + filename + ' 还没建）')
            continue
        text = strip_comments(path.read_text(encoding='utf-8', errors='replace'))
        if name not in text:
            missing.append(name.strip('(') + '（该用在 ' + where + '）')
    if missing:
        return [(False, '大纲要求这八个现成函数各至少改写一处，还差：' + '、'.join(missing))]
    return [(True, '大纲要求的八个现成函数各至少改写一处：'
                   'sum / max / any / all / map / sorted / enumerate / zip')]


def check_task1():
    """十段循环逐段改写成一行：与循环版基准逐字比对。"""
    base = run_script(BASELINE)
    if base['status'] != 'ok':
        return [(False, BASELINE + ' 跑不起来（它是给好的基准，别改）：' + base['note'])]
    base_labels = label_map(base['out'])
    if len(base_labels) != 10:
        return [(False, '基准 ' + BASELINE + ' 应该打出十行结果，实际 ' + str(len(base_labels))
                       + ' 行：这一份别改')]
    checks = [(True, '基准 ' + BASELINE + ' 跑通，十行结果都在（它是比对的标准）')]

    run = run_script('task1_rewrite.py')
    if run['status'] != 'ok':
        return checks + [(False, 'task1_rewrite.py 没跑通：' + run['note'])]
    got = label_map(run['out'])

    bad = 0
    for key in sorted(base_labels):
        want = base_labels[key]
        mine = got.get(key)
        if mine == want:
            checks.append((True, key + ' 与循环版逐字一致'))
        else:
            bad += 1
            checks.append((False, key + ' 打出 ' + short(mine, 40) + '，循环版是 '
                           + short(want, 40) + '：' + TASK1_HINTS[key]))
    if bad:
        checks.append((False, '十段里有 ' + str(bad) + ' 段还没对上：'
                              '改写只动写法，结果必须与循环版逐字一致'))
    else:
        checks.append((True, '十段结果全部与循环版逐字一致'))
    checks += coverage_checks()
    return checks


# ── 任务 2 · 带条件与嵌套的推导式 ────────────────────────────────────────

def check_task2():
    """两个 if 子句、两个 for 子句、嵌套推导式，以及目标名不泄漏。"""
    want = [
        ('01 两个条件', '[6, 8]', '01：两个 if 子句是「与」的关系（既要偶数又要大于 4）',
         'TODO 01：条件写在方括号最后，两个条件各写一个 if 子句，顺序与循环版一致'),
        ('02 展平', '[1, 2, 3, 4, 5, 6]', '02：两个 for 子句把两层循环压成一行，顺序与循环版一致',
         'TODO 02：方括号里先写 for elem in vec，再写 for num in elem（顺序别对调）'),
        ('03 转置', '[[1, 5, 9], [2, 6, 10], [3, 7, 11], [4, 8, 12]]',
         '03：推导式里再嵌一层推导式，外层每取一个 i 就构造一整行',
         'TODO 03：外层 for i in range(4)，里层 [row[i] for row in matrix]'),
        ('04 平方表', '[0, 1, 4, 9]', '04：平方表是用推导式建的（不是循环）',
         'TODO 04：把方括号里的描述写全：算出什么、从哪批数据里取'),
        ('05 推导式外 y', '旧值', '05：推导式的目标名没有泄漏，外面的 y 还是旧值',
         'TODO 04 要先写出推导式；这一行看的是「推导式的 y 有没有盖掉外面的 y」'),
        ('06 循环外 y', '3', '06：给好的对照行 —— 循环版的目标名留在了外面（y 变成 3）',
         '这一行是给好的对照，别改'),
    ]
    needs = {'05 推导式外 y': ('04 平方表', '[0, 1, 4, 9]',
                              '先看 04 那一行（它才是你写的推导式）')}
    return check_fixed('task2_nested.py', want, needs)


# ── 任务 3 · 生成器表达式与惰性 ──────────────────────────────────────────

PROBE = '''
import task3_generator as t
g = t.squares_gen(6)
print('探针 类型', type(g).__name__)
try:
    print('探针 len', '没有报错，长度是 ' + str(len(g)))
except Exception as e:
    print('探针 len', type(e).__name__ + ': ' + str(e))
try:
    print('探针 下标', '没有报错，取到 ' + repr(g[0]))
except Exception as e:
    print('探针 下标', type(e).__name__ + ': ' + str(e))
try:
    print('探针 求和', str(sum(g)))
except Exception as e:
    print('探针 求和', type(e).__name__ + ': ' + str(e))
'''


def probe_checks():
    """另起一个进程 import 学生代码，看它交给判分的到底是不是生成器。"""
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    try:
        done = subprocess.run(
            [sys.executable, '-B', '-c', PROBE], cwd=str(HERE), env=env, timeout=TIMEOUT,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return [(False, '探针 import task3_generator.py 时跑了 ' + str(TIMEOUT) + ' 秒还没结束')]
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-5:])
        return [(False, 'task3_generator.py 交给判分的 squares_gen 用不起来（探针报错退出）：\n' + tail)]
    out = done.stdout or ''
    checks = []
    kind = get_line(out, '探针 类型')
    if kind == 'generator':
        checks.append((True, 'squares_gen 交回来的是生成器（不是列表）'))
    else:
        checks.append((False, 'squares_gen 交回来的东西类型是 ' + repr(kind)
                              + '，期望 generator：TODO 03 要把方括号换成圆括号'))
    length = get_line(out, '探针 len') or ''
    if 'has no len()' in length:
        checks.append((True, '生成器没有长度：len(生成器) 报 TypeError 说 has no len()'))
    else:
        checks.append((False, 'len(squares_gen(6)) 的结果是 ' + repr(length)
                              + '，期望报 TypeError 说 has no len()：'
                              + '生成器是惰性的，手上只有当前这个值，数不出长度'))
    sub = get_line(out, '探针 下标') or ''
    if 'not subscriptable' in sub:
        checks.append((True, '生成器不能下标：生成器[0] 报 TypeError 说 not subscriptable'))
    else:
        checks.append((False, '生成器[0] 的结果是 ' + repr(sub) + '，期望报 TypeError 说 '
                              'not subscriptable：没有下标可取（要按下标取就先建成表）'))
    total = get_line(out, '探针 求和') or ''
    if total == '55':
        checks.append((True, '探针把它加了一遍：0²+1²+…+5² = 55'))
    else:
        checks.append((False, '探针把 squares_gen(6) 加起来得到 ' + repr(total)
                              + '，期望 55：它产生的值要和列表推导式一样'))
    return checks

def check_task3():
    """惰性、只能走一遍、没有 len、不能下标、短路。"""
    want = [
        ('01 建好之后 calls', '0', '01：生成器写出来时一个都还没算（惰性）',
         'TODO 01：把方括号换成圆括号 —— 列表推导式是「建好就算完」，'
         '这一行要的是「还没算」的那个写法（现在打出 6 就是还在建表）'),
        ('02 第一次 sum', '55', '02：第一次取，逐个算出来加一遍得 55',
         'TODO 01：一样的算式，0²+1²+…+5² = 55；现在对不上说明这一行还不是那个写法'),
        ('03 第一次 sum 之后 calls', '6', '03：取到空了，正好算了 6 个',
         'TODO 01：取完一遍应该正好算了 6 个数'),
        ('04 第二次 sum', '0', '04：第二次要，里面已经空了 —— 生成器只能走一遍',
         'TODO 01：这一行要看的现象是「第二次要什么都没有」；'
         '现在打出 55 说明它还是能反复用的那份表'),
        ('05 第二次 sum 之后 calls', '6', '05：第二次没有再算（计数没涨）',
         'TODO 01：第二次不该重新算，计数还是 6'),
        ('06 建表之后 calls', '6', '06：列表推导式是建表时就把元素全算好',
         'TODO 02：这一行换成列表推导式（建表就算完）'),
        ('07 表能反复用', '55 55', '07：表能反复用，两次求和都是 55',
         'TODO 02：换成列表推导式之后，两次求和都是 55'),
        ('08 any 提前停 calls', '3', '08：any 到第 3 个数就定下了（0、1 不满足，4 满足）',
         'TODO 04：把 any 那一行写出来（表达式用 slow_square(x) > 3）；'
         '「提前停」靠的是 any 一确定就不再往下取值'),
        ('09 any 的值', 'True', '09：any 的结果是对的',
         'TODO 04：any 的写法是「有没有满足条件的」'),
        ('10 all 提前停 calls', '4', '10：all 到第 4 个数出现反例就定下了',
         'TODO 05：把 all 那一行写出来（表达式用 slow_square(x) < 5）；'
         'all 见到第一个反例就停'),
        ('11 all 的值', 'False', '11：all 的结果是对的（9 不小于 5，出现了反例）',
         'TODO 05：all 的写法是「是不是全部都满足」'),
        ('12 map 第一次', '[3, -1, 4]', '12：map 交回的是迭代器，第一次用 list 收得下三个数',
         '这一行是给好的，别改它的 print；它演示 map 的返回值也是个迭代器'),
        ('13 map 第二次', '[]', '13：第二次已经空了 —— 迭代器只能用一次',
         '这一行是给好的，别改它的 print'),
    ]
    needs = {
        '02 第一次 sum': ('01 建好之后 calls', '0', '先看 01：生成器写出来时应该一个都还没算'),
        '03 第一次 sum 之后 calls': ('01 建好之后 calls', '0',
                                     '先看 01：生成器写出来时应该一个都还没算'),
        '05 第二次 sum 之后 calls': ('01 建好之后 calls', '0',
                                     '先看 01：生成器写出来时应该一个都还没算'),
    }
    return check_fixed('task3_generator.py', want, needs) + probe_checks()


# ── 任务 4 · 把下标循环换成 enumerate 与 zip ─────────────────────────────

def check_task4():
    """编号从 1 起、zip 截断到最短、取一列、配对、转置。"""
    want = [
        ('01 编号', ['1 第一题 80', '2 第二题 95', '3 第三题 60'],
         '01：编号从 1 起，值与编号一次取出（不用再写下标）',
         'TODO 01：改成位置与值一起取的写法，编号从 1 起（默认从 0 起，'
         '那样第一行会是 0）；两列数要对齐取，别把分数当名字'),
        ('02 enumerate 表', "[(1, '第一题'), (2, '第二题'), (3, '第三题')]",
         '02：enumerate 给每项配上位置号，start 决定从几起',
         'TODO 02：用位置与值一起取的那个函数，带上 start=1，再用 list 收成表'),
        ('03 zip 截断长度', '2', '03：zip 在最短的那个用完时就停（3 对 2，只出 2 对）',
         'TODO 03：两个序列长度不齐时不会报错，只会变短；数一数实际配出几对'),
        ('04 zip 截断表', "[('第一题', 80), ('第二题', 95)]",
         '04：截断后的配对表就是两对',
         'TODO 04：把两个序列一一配对的写法用上，再用 list 收成表'),
        ('05 分数列', '[80, 95, 60]', '05：用 [分数 for _, 分数 in 配对] 单独取一列',
         'TODO 05：想单独取配对里的某一列，用一个不对应的名字接住另一列（推导式）'),
        ('06 配对表', "[('第一题', 80), ('第二题', 95), ('第三题', 60)]",
         '06：完整的配对表（长度齐的时候三对都在）',
         'TODO 06：把两个序列一一配对（这次不截断）'),
        ('07 转置', '[[1, 5, 9], [2, 6, 10], [3, 7, 11], [4, 8, 12]]',
         '07：把每一行当成一个参数交给 zip，它按位置把同列的元素配成一组',
         'TODO 07：三行矩阵转置，把 matrix[0]、matrix[1]、matrix[2] 交给配对函数，'
         '再把每组收成列表（原来的两层下标循环不用写）'),
    ]
    return check_fixed('task4_zip_enum.py', want)


# ── 任务 5 · sorted 的 key 与 list.sort 的返回值 ─────────────────────────

def check_task5():
    """按第二关键字排序、sorted 返回新表、list.sort 返回 None、键函数只调用一次。"""
    want = [
        ('01 排行榜', "[('A01', 95), ('A04', 95), ('A02', 80), ('A03', 80)]",
         '01：分数降序、同分按编号升序，排行榜对了',
         'TODO 01：key 要交回一个元组：分数降序（第一项取负号）、同分编号升序；'
         '分数相同的两条要按编号从小到大排（现在这一行对不上）'),
        ('02 原记录没动', 'True', '02：排序用的是返回新表的那一个，原记录没被动过',
         'TODO 01：这一行看的是原记录有没有被改；要用「返回新表」的排序写法'),
        ('03 sorted 新表', '[95, 88, 70]', '03：sorted 返回一张新的有序表（原表不动）',
         'TODO 02：这一行要一张降序的新表，用「返回新表」的那个写法（不是原地排序）'),
        ('04 原分数没动', '[88, 95, 70]', '04：原分数还是原来的顺序（sorted 没动它）',
         'TODO 02：这一行看的是原分数有没有被动；要用「返回新表」的写法'),
        ('05 sort 的返回值是 None', 'True', '05：原地排序交回来的是 None —— 这就是那个坑',
         'TODO 03：这里要真的调用一次原地排序，把它的返回值接住；'
         '你会发现接住的是 None（写成 x = a.sort() 的坑就在这）'),
        ('06 被 sort 改过的原表', '[70, 88, 95]', '06：原地排序确实把原表改了',
         'TODO 03：原地排序会直接把原表排好（这一行要看到它被改了）'),
        ('07 按分数升序', "[('A03', 80), ('A02', 80), ('A01', 95), ('A04', 95)]",
         '07：分数升序；同分的两条保持了原始顺序（排序是稳定的）',
         'TODO 04：用 sorted(records, key=count_key) 排一遍'),
        ('08 取键次数', '4', '08：四条记录，键函数只被调用 4 次（不是每比一次调一次）',
         'TODO 04：键函数每条记录只调用一次，四条记录就是 4 次'),
    ]
    needs = {
        '02 原记录没动': ('01 排行榜', "[('A01', 95), ('A04', 95), ('A02', 80), ('A03', 80)]",
                        '先把 01 排对，再看原记录动没动'),
        '04 原分数没动': ('03 sorted 新表', '[95, 88, 70]', '先把 03 排对，再看原分数动没动'),
        '05 sort 的返回值是 None': ('06 被 sort 改过的原表', '[70, 88, 95]',
                                  '先真的调用一次原地排序（06 那一行要看到原表被改了）'),
    }
    return check_fixed('task5_sort.py', want, needs)


# ── 任务 6 · any 与 all ─────────────────────────────────────────────────

def check_task6():
    """两种判定循环的换法、空序列的默认答案、判空、短路。"""
    want = [
        ('01 有正数', 'True', '01：存在一个满足就为真',
         'TODO 01：先设 False 再置位的判定，换成「存在」那个函数（喂生成器表达式）'),
        ('02 全部为正', 'False', '02：要全部满足才为真（0 不是正数，所以是假）',
         'TODO 02：先设 True 再翻成 False 的判定，换成「全部」那个函数；'
         '条件要与循环版一致（大于 0）'),
        ('03 空数据 any', 'False', '03：空数据上 any 是 False —— 一个满足的都没有',
         'TODO 03：把数据换成空的那个列表；空序列上「存在」的答案是 False'),
        ('04 空数据 all', 'True', '04：空数据上 all 是 True —— 一个反例也没有',
         'TODO 04：空序列上「全部」的答案是 True（两个默认答案相反，这是最容易记错的地方）'),
        ('05 空数据 不判空版', 'True', '05：不判空的那一版，空数据也给出 True',
         'TODO 05：用「全部」那个函数写；空数据会给 True，这正是要留心的口径'),
        ('06 空数据 判空版', 'False', '06：先判空的那一版，空数据交回 False',
         'TODO 06：函数体第一行先判空（空数据直接交回 False），再用「全部」那个函数'),
        ('07 非空数据 两版', 'True True', '07：数据都合法时两版都给 True',
         'TODO 05 与 06：两版都要用「全部」那个函数写出来'),
        ('08 有负数 两版', 'False False', '08：出现一个不合法时两版都给 False',
         'TODO 05 与 06：两版都要用「全部」那个函数写出来'),
        ('09 any 结果', 'True', '09：any 的结果是对的',
         'TODO 07：把 any 那一行写出来（表达式用 positive(x)）'),
        ('10 any 看了几个', '1', '10：第一个就满足了，any 不再往下取（短路）',
         'TODO 07：第一个数就满足，判定函数只会被调用 1 次'),
    ]
    needs = {'10 any 看了几个': ('09 any 结果', 'True', '先把 07 那一行写出来')}
    return check_fixed('task6_any_all.py', want, needs)


TASKS = [
    ('任务 1 · 十段循环逐段改写成一行', 'task1_rewrite.py', check_task1),
    ('任务 2 · 带条件与嵌套的推导式', 'task2_nested.py', check_task2),
    ('任务 3 · 生成器表达式与惰性', 'task3_generator.py', check_task3),
    ('任务 4 · 把下标循环换成 enumerate 与 zip', 'task4_zip_enum.py', check_task4),
    ('任务 5 · sorted 的 key 与 list.sort 的返回值', 'task5_sort.py', check_task5),
    ('任务 6 · any 与 all', 'task6_any_all.py', check_task6),
]


def main():
    print('StudyMate lab 0005 · 自动判分（推导式与常用内置工具）')
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
    print('6 个任务：' + str(6 - len(failed)) + ' 个通过，' + str(len(failed)) + ' 个还没通过')
    if failed:
        print('没过的：' + '、'.join(failed))
        print('卡住了先读 ../README.md 的「卡壳顺序」：读错误信息 → 自己跑一遍 → 看 FAIL 行 → 再对线索。')
        print('六个任务都过了，再对照 ../solutions/0005-python-comprehension-builtins/ 看参考解。')
        return 1
    print('六个任务都过了。现在去对照 ../solutions/0005-python-comprehension-builtins/：')
    print('比一比你的写法与参考解，再用一句话回答「这十段里哪几段其实不该压成一行」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
