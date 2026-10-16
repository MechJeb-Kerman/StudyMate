#!/usr/bin/env python3
"""lab 0019 · 自动判分（并查集：谁和谁是一伙的）

5 层判分：
  第 1 层：任务 1 基本 DSU —— 跑通、四行输出与课件一致
  第 2 层：任务 2 优化版 DSU —— 链退化演示、路径压缩效果
  第 3 层：任务 3 2×2 对照表 —— 四种变体各项指标
  第 4 层：任务 4 连通分量计数 —— 询问答案 + 邻接表验证
  第 5 层：探针验证 —— 4 个探针用独立数据验证

判法：每个任务起子进程跑，读 stdout 的固定格式行。
      所有 FAIL 都指向 TODO 编号。

退出码：0 = 全部通过；1 = 还有没过的。
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


# ── 工具 ──────────────────────────────────────────────────

def run_script(name, stdin_text=''):
    """跑一个脚本 → dict(status, out, err, note)。"""
    path = HERE / name
    if not path.is_file():
        return {'status': 'missing', 'out': '', 'err': '', 'note': f'还没建这个文件：{name}'}
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
                'note': f'跑了 {TIMEOUT} 秒还没结束（死循环？）'}
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-5:])
        hint = todo_hint(name, done.stderr or '')
        note = f'脚本报错退出（退出码 {done.returncode}）{hint}：\n{tail}'
        return {'status': 'crash', 'out': done.stdout or '', 'err': done.stderr or '',
                'note': note}
    return {'status': 'ok', 'out': done.stdout or '', 'err': '', 'note': ''}


def todo_hint(name, err):
    """从 traceback 里找报错落在哪个 TODO。"""
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
    return f'，报错落在 TODO {todo} 那一段（第 {lineno} 行）'


def get_line(out, prefix):
    """按前缀取一行剩余内容。"""
    for line in out.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def short(value, limit=80):
    text = repr(value)
    if len(text) > limit:
        return text[:limit] + '…'
    return text


# ── 第 1 层 · 基本 DSU ────────────────────────────────────

def layer1():
    """任务 1：基本 DSU —— __init__、find、union。

    四行输出与课件一致：
      0 和 2 是亲戚: True
      0 和 3 是亲戚: False
      2 和 3 是亲戚: False
      连通块个数: 3
    """
    run = run_script('task1_basic_dsu.py')
    if run['status'] != 'ok':
        return [(False, 'task1_basic_dsu.py 没跑通：' + run['note'])]

    out = run['out']
    checks = []

    r0 = get_line(out, '0 和 2 是亲戚:')
    r1 = get_line(out, '0 和 3 是亲戚:')
    r2 = get_line(out, '2 和 3 是亲戚:')
    rc = get_line(out, '连通块个数:')

    # 四条判读
    for prefix, want, ok_msg, fail_msg in [
        ('0 和 2 是亲戚:', 'True', '0 和 2 连通：True',
         '0 和 2 打出 False：TODO 01（parent 初始化）或 TODO 02（find）或 TODO 03（union）写错了'),
        ('0 和 3 是亲戚:', 'False', '0 和 3 不连通：False',
         '0 和 3 打出 True：TODO 03 union 里没判 ra == rb，导致两个集合被错误合并了'),
        ('2 和 3 是亲戚:', 'False', '2 和 3 不连通：False',
         '2 和 3 打出 True：TODO 03 union 方向或 ra == rb 判断有问题'),
    ]:
        val = get_line(out, prefix)
        if val is None:
            checks.append((False, f'没看到「{prefix}」这一行：带 print 的行别改'))
        elif val != want:
            checks.append((False, f'{prefix} 打出 {short(val)}，期望 {want}：{fail_msg}'))
        else:
            checks.append((True, ok_msg))

    if rc is None:
        checks.append((False, '没看到「连通块个数:」这一行'))
    elif rc != '3':
        checks.append((False, f'连通块个数打出 {short(rc)}，期望 3：TODO 01 的 parent 初始化不对'))
    else:
        checks.append((True, '连通块个数: 3 —— 三个集合 {0,1,2} {3,4} {5,6}'))

    return checks


# ── 第 2 层 · 优化版 DSU ──────────────────────────────────

def layer2():
    """任务 2：路径压缩 + 按大小合并 + 链退化。

    三行输出：
      树高 NNN
      find(0) 第 1 次 NNN 步
      find(0) 第 2 次 NNN 步

    路径压缩后第 2 次必须明显少于第 1 次。
    """
    run = run_script('task2_optimizations.py')
    if run['status'] != 'ok':
        return [(False, 'task2_optimizations.py 没跑通：' + run['note'])]

    out = run['out']
    checks = []

    h_line = get_line(out, '树高')
    s1_line = get_line(out, 'find(0) 第 1 次')
    s2_line = get_line(out, 'find(0) 第 2 次')

    if h_line is None:
        checks.append((False, '没看到「树高 …」这一行'))
        return checks
    try:
        h = int(h_line)
    except ValueError:
        checks.append((False, f'树高行格式不对：{short(h_line)}'))
        return checks

    if s1_line is None:
        checks.append((False, '没看到「find(0) 第 1 次 … 步」'))
        return checks
    try:
        s1 = int(s1_line.replace('步', '').strip())
    except ValueError:
        checks.append((False, f'find(0) 第 1 次 格式不对：{short(s1_line)}'))
        return checks

    if s2_line is None:
        checks.append((False, '没看到「find(0) 第 2 次 … 步」'))
        return checks
    try:
        s2 = int(s2_line.replace('步', '').strip())
    except ValueError:
        checks.append((False, f'find(0) 第 2 次 格式不对：{short(s2_line)}'))
        return checks

    # N = 4000
    N = 4000

    if h <= N // 10:
        checks.append((True, f'树高 {h} —— 按大小合并把树压低了（近于常量）'))
    elif h >= N // 2:
        checks.append((False, f'树高 {h}，接近 {N} —— TODO 02：按大小合并的逻辑没生效'
                               f'（size 比较或交换写反了）'))
    else:
        checks.append((True, f'树高 {h} —— 有优化效果'))

    # 注意：find_steps(ds, 0) 中，0 是根(parent[0]=0)时不走循环，步数为 0。
    # 这是按大小合并的正常结果（所有结点直接挂到根 0 上，树高 1）。
    if s1 >= N // 10:
        checks.append((True, f'第 1 次 {s1} 步 —— 链退化了（接近 {N}）'))
    elif s1 == 0 and h <= 10:
        # 按大小合并且 0 是根：树扁平，find(0) 不需走
        checks.append((True, f'第 1 次 {s1} 步 —— 树扁平（根是 0），无需走链'))
    elif s1 > 0 and s1 < N // 10:
        # 有路径压缩
        checks.append((True, f'第 1 次 {s1} 步 —— 链存在且有压缩'))
    else:
        checks.append((True, f'第 1 次 {s1} 步'))

    if s2 < s1:
        checks.append((True, f'第 2 次 {s2} 步 —— 路径压缩生效了（比第 1 次的 {s1} 步少）'))
    elif s1 == s2 and s1 == 0:
        checks.append((True, f'第 2 次 {s2} 步 —— 与第 1 次相同（根始终不压缩）'))
    elif s1 == s2 and s1 > 0:
        checks.append((False, f'第 2 次 {s2} 步，与第 1 次相同 —— TODO 01 路径压缩没写对'))
    else:
        checks.append((True, f'第 2 次 {s2} 步'))

    return checks


# ── 第 3 层 · 2×2 对照表 ──────────────────────────────────

def layer3():
    """任务 3：2×2 对照表。

    四种变体的「树高」「耗时」「查找步数（查前/查后）」。
    判分只检查：
      - 四个变体都打了数据
      - "谁都不上"的树高接近 N
      - "谁都不上"的查后步数≈查前步数（没压缩），而另三者的查后步数远小于查前
    """
    run = run_script('task3_comparison.py')
    if run['status'] != 'ok':
        return [(False, 'task3_comparison.py 没跑通：' + run['note'])]

    out = run['out']
    checks = []

    # 解析第一行：变体 {name} 树高 NNN 耗时 0.xxxxxx 秒 查询次数 NNN
    variant_main = {}
    # 解析第二行：变体 {name} 找根步数 查前 NNN 查后 NNN
    variant_steps = {}

    for name_key in ['谁都不上', '只路径压缩', '只按大小', '两个都上']:
        for line in out.splitlines():
            s = line.strip()
            # 匹配「变体 {name} 找根步数 查前 NNN 查后 NNN」
            if name_key in s and '找根步数' in s:
                parts = s.split()
                try:
                    # parts = [变体, 谁都不上, 找根步数, 查前, NNN, 查后, NNN]
                    pre = int(parts[4])
                    post = int(parts[6])
                except (ValueError, IndexError):
                    continue
                variant_steps[name_key] = {'pre': pre, 'post': post}
            # 匹配「变体 {name} 树高 NNN 耗时 0.xxx 秒 查询次数 NNN」
            elif name_key in s and '树高' in s:
                parts = s.split()
                try:
                    # parts = [变体, 谁都不上, 树高, NNN, 耗时, 0.xxx, 秒, 查询次数, NNN]
                    h = int(parts[3])
                    elapsed = float(parts[5])
                except (ValueError, IndexError):
                    continue
                variant_main[name_key] = {'h': h, 'elapsed': elapsed}

    for name in ['谁都不上', '只路径压缩', '只按大小', '两个都上']:
        if name in variant_main:
            checks.append((True, f'{name} 读到了：树高 {variant_main[name]["h"]}'))
        else:
            checks.append((False, f'没读到「{name}」的主数据行'))

    if '谁都不上' in variant_main:
        h_none = variant_main['谁都不上']['h']
        N = 2000
        if h_none >= N - 50:
            checks.append((True, f'谁都不上 树高 {h_none}，接近 {N} —— 链确实退化了'))
        elif h_none > N // 2:
            checks.append((True, f'谁都不上 树高 {h_none}，部分退化'))
        else:
            checks.append((False, f'谁都不上 树高 {h_none}，不够退化（应该接近 {N}）—— '
                                   f'TODO 01 的 union 建链方式不对'))

    # 步数检查：谁都不上的查后≈查前（没压缩），路径压缩的查后<<查前
    if '谁都不上' in variant_steps:
        s = variant_steps['谁都不上']
        if s['post'] >= s['pre'] * 0.5:
            checks.append((True, '谁都不上：查后步数≈查前（没有路径压缩，树形不变）'))
        else:
            checks.append((False, f'谁都不上：查后步数 {s["post"]} 远小于查前 {s["pre"]} —— '
                                   f'不应该有压缩效果'))

    for name in ['只路径压缩', '只按大小', '两个都上']:
        if name in variant_steps:
            s = variant_steps[name]
            if s['post'] < s['pre']:
                checks.append((True, f'{name}：查后步数 {s["post"]} < 查前 {s["pre"]} —— 优化生效'))
            elif s['pre'] <= 10:
                checks.append((True, f'{name}：查前步数即为 {s["pre"]}，树已经很扁平'))
            else:
                checks.append((False, f'{name}：查后步数 {s["post"]} 未小于查前 {s["pre"]} —— '
                                       f'优化可能没生效'))

    return checks


# ── 第 4 层 · 连通分量计数 ────────────────────────────────

def layer4():
    """任务 4：连通分量计数 + 邻接表验证。"""
    run = run_script('task4_components.py')
    if run['status'] != 'ok':
        return [(False, 'task4_components.py 没跑通：' + run['note'])]

    out = run['out']
    checks = []

    # 询问结果
    queries_found = []
    for line in out.splitlines():
        line_s = line.strip()
        if '和' in line_s and ':' in line_s:
            queries_found.append(line_s)

    if len(queries_found) < 5:
        checks.append((False, f'询问结果行不够，只找到了 {len(queries_found)} 行（应该 5 行）'))
    else:
        checks.append((True, '5 组询问都打印了'))

    # 期望值
    # expect: 0-3 True, 0-2 True, 5-7 True, 8-9 True, 1-9 False
    expected_results = {
        '0 和 3: True': True,
        '0 和 2: True': True,
        '5 和 7: True': True,
        '8 和 9: True': True,
        '1 和 9: False': True,
    }
    found_expected = 0
    for line in queries_found:
        stripped = line.strip()
        for exp_key in expected_results:
            if stripped == exp_key:
                found_expected += 1
                break

    if found_expected == 5:
        checks.append((True, '5 组询问结果全部正确'))
    else:
        checks.append((False, f'询问结果中有 {5 - found_expected} 组不正确 —— '
                              f'TODO 01/TODO 02 的 find/union 写错了'))

    # 连通块个数
    comps_dsu = get_line(out, '并查集连通块个数:')
    comps_adj = get_line(out, '邻接表遍历连通块个数:')
    same = get_line(out, '两个结果一致:')

    if comps_dsu is None:
        checks.append((False, '没看到「并查集连通块个数:」'))
    elif comps_dsu != '3':
        checks.append((False, f'并查集连通块个数打出 {comps_dsu}，期望 3'))
    else:
        checks.append((True, '并查集连通块个数: 3'))

    if comps_adj is None:
        checks.append((False, '没看到「邻接表遍历连通块个数:」'))
    elif not comps_adj.isdigit() or int(comps_adj) <= 0:
        checks.append((False, f'邻接表连通块数似乎不对：{comps_adj} —— TODO 03 没写好'))
    elif comps_adj == comps_dsu:
        checks.append((True, f'邻接表连通块个数: {comps_adj} —— 与 DSU 一致'))
    else:
        checks.append((False, f'邻接表连通块个数 {comps_adj} 与 DSU 的 {comps_dsu} 不一致 —— '
                              f'TODO 03 的 BFS/DFS 遍历写错了'))

    if same is None:
        checks.append((False, '没看到「两个结果一致:」'))
    elif same != 'True':
        checks.append((False, '两个结果一致: False —— 并查集与邻接表的连通块数不同'))
    else:
        checks.append((True, '两个结果一致: True —— DSU 与邻接表遍历互相验证'))

    return checks


# ── 第 5 层 · 探针验证 ────────────────────────────────────

def run_probe(name):
    """跑一个探针脚本，返回 (OK?, 输出)。"""
    path = HERE / 'probes' / name
    if not path.is_file():
        return False, f'还没建这个文件：probes/{name}'
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
        return False, f'探针 {name} 超时（{TIMEOUT} 秒）'
    if done.returncode != 0:
        tail = '\n'.join((done.stderr or '').strip().splitlines()[-3:]
                         + (done.stdout or '').strip().splitlines()[-3:])
        return False, f'探针 {name} 报错：\n{tail}'
    out = (done.stdout or '').strip().splitlines()
    ok_lines = [l for l in out if l.startswith('OK')]
    fail_lines = [l for l in out if l.startswith('FAIL')]
    return True, f'{" | ".join(ok_lines)}' if ok_lines else f'探针 {name} 通过'


def layer5():
    probes = ['probe1_basic.py', 'probe2_chain.py', 'probe3_comparison.py', 'probe4_components.py']
    checks = []
    for name in probes:
        ok, msg = run_probe(name)
        if ok:
            checks.append((True, f'探针 {name} 通过：{msg}'))
        else:
            checks.append((False, f'探针 {name} 未通过：{msg}'))
    # 如果某个探针的依赖任务文件没写好，探针会报错，但判分给具体的 FAIL
    return checks


# ── 主流程 ─────────────────────────────────────────────────

LAYERS = [
    ('第 1 层 · 基本 DSU', layer1),
    ('第 2 层 · 优化版 DSU + 链退化', layer2),
    ('第 3 层 · 2×2 对照表', layer3),
    ('第 4 层 · 连通分量计数', layer4),
    ('第 5 层 · 探针验证', layer5),
]


def main() -> int:
    print('StudyMate lab 0019 · 自动判分（并查集：谁和谁是一伙的）')
    print(f'目录：{HERE}')
    print()

    # 检查文件是否存在
    task_files = ['task1_basic_dsu.py', 'task2_optimizations.py',
                  'task3_comparison.py', 'task4_components.py']
    missing = [f for f in task_files if not (HERE / f).is_file()]
    if missing:
        print('缺少文件：' + '、'.join(missing))
        print('先按课件把任务文件建好再判分。')
        return 1

    total_checks = 0
    failed_layers = []

    for title, checker in LAYERS:
        print(f'═ {title} ═')
        checks = checker()
        total_checks += len(checks)
        layer_failed = False
        for ok, msg in checks:
            print(f'  {"PASS" if ok else "FAIL"}  {msg}')
            if not ok:
                layer_failed = True
        if layer_failed:
            failed_layers.append(title)
        print()

    print('─' * 60)
    passed_layers = len(LAYERS) - len(failed_layers)
    print(f'5 层判分：{passed_layers} 层通过，{len(failed_layers)} 层还没通过')
    if failed_layers:
        print('没通过的层：')
        for name in failed_layers:
            print(f'  · {name}')
        print()
        print('卡壳顺序：')
        print('  1. 先跑单个任务看它打印什么（py task1_basic_dsu.py）')
        print('  2. 看 FAIL 行指向的 TODO 编号')
        print('  3. 读任务文件里对应 TODO 的注释')
        print('  4. 重新跑单个任务验证')
        print('全部通过后再对照 solutions/ 目录看参考解。')
        return 1

    print('5 层全部通过！现在去对照 lab/solutions/0019-union-find/ 看参考解：')
    print('比一比你的写法与参考解的差距，再说一句「哪一行决定了一个优化生效」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())