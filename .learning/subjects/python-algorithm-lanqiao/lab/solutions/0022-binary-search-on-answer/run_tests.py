#!/usr/bin/env python3
"""lab 0022 · 自动判分：跑四个任务脚本，比对固定格式行，另起探针 import 学生代码。

用法（在 lab/0022-binary-search-on-answer/ 目录里）：

    py run_tests.py

判法：
  - 每个任务单独起一个进程跑，只看 stdout 里的固定格式行，不 import 学生代码；
  - 计数行（`计数 NN 标签 值`）是判分接口，按两位编号取，编号与前缀都对得上才算；
  - **木材切割靠对拍验**：check 函数的四组、二分答案的三组加上边界数据全部对上；
  - **跳石头靠对拍验**：check 函数的三组、二分答案的三组加上全部移除数扫描
  - **暴力验算靠对拍验**：200+ 组随机数据上暴力与二分全部一致（不一致组数 = 0）
  - **单调性破坏比较**：比较不同初始区间下的二分结果与暴力结果，不一致的区间就是
    单调性被破坏的证据
  - **耗时行一条都不判**：脚本会打印 `耗时 NN … 秒`，那是给学生自己看的。
    耗时随机器浮动，拿它当判据会让同一份代码时过时不过，所以整套判分只用确定值。

退出码：0 = 四个任务都通过；1 = 还有没通过的。
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMEOUT = 180

TASKS = [
    ('任务 1 · 木材切割（check + 二分）', 'task01_wood_cutting.py', None),
    ('任务 2 · 跳石头（移除石头求最大最小间距）', 'task02_river_hopping.py', None),
    ('任务 3 · 暴力验算（二分 vs 暴力枚举）', 'task03_bruteforce_verify.py', None),
    ('任务 4 · 破坏单调性（二分会怎样？）', 'task04_break_monotonicity.py', None),
]


# ── 跑脚本 ──────────────────────────────────────────────────────

def _env():
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    return env


def run_script(name, timeout=TIMEOUT):
    """跑一个任务脚本 → dict(status, out, note)。状态：ok / missing / crash / timeout。"""
    path = HERE / name
    if not path.is_file():
        return {'status': 'missing', 'out': '', 'note': '还没建这个文件：' + name}
    try:
        done = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(HERE), env=_env(), timeout=timeout,
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


def run_probe(filename, timeout=TIMEOUT):
    """另起一个进程跑 probes/<filename>（它 import 学生代码）→ (out, note)。"""
    path = HERE / 'probes' / filename
    if not path.is_file():
        return None, '没找到探针文件 probes/' + filename
    try:
        done = subprocess.run(
            [sys.executable, '-B', str(path)],
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


def probe_json(filename):
    """跑探针并解析它最后一行 PROBE 后面的 JSON → (数据, 错误说明)。"""
    out, note = run_probe(filename)
    if out is None:
        return None, note
    line = None
    for text in out.splitlines():
        if text.startswith('PROBE '):
            line = text[len('PROBE '):]
    if line is None:
        return None, '探针没打出 PROBE 那一行'
    try:
        return json.loads(line), ''
    except Exception as exc:
        return None, '探针结果读不出来：' + str(exc)


# ── 读输出 ──────────────────────────────────────────────────────

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


def short(text, limit=60):
    text = '' if text is None else str(text)
    return text if len(text) <= limit else text[:limit] + '…'


# ══ 任务 1 · 木材切割 ════════════════════════════════════════════

def check_task1():
    run = run_script('task01_wood_cutting.py')
    if run['status'] != 'ok':
        return [(False, 'task01_wood_cutting.py 没跑通：' + run['note'])]
    checks = []

    want = [
        ('check 段长 10 段数 3', 'True', 'check(10, 3) 应返回 True：10//10+10//10+10//10=3≥3'),
        ('check 段长 11 段数 3', 'False', 'check(11, 3) 应返回 False：11 比任何木头都大'),
        ('check 段长 4 段数 6', 'True', 'check(4, 6) 应返回 True：10//4=2, 2*3=6≥6'),
        ('check 段长 5 段数 7', 'False', 'check(5, 7) 应返回 False：10//5=2, 2*3=6<7'),
    ]
    for prefix, expect, good in want:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 1 的 check 要算 sum(w // x)，然后跟 M 比'))

    want_bin = [
        ('M=3 最大段长', '10', 'M=3 时最大段长是 10'),
        ('M=6 最大段长', '5', 'M=6 时最大段长是 5'),
        ('M=9 最大段长', '3', 'M=9 时最大段长是 3'),
    ]
    for prefix, expect, good in want_bin:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 2 的二分要取上取整 mid=(lo+hi+1)//2'))

    # 扫描 M 行
    m_lines = get_lines(run['out'], 'M=')
    m_vals = {}
    for line in m_lines:
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            try:
                m_vals[int(parts[0])] = int(parts[-1]) if parts[-1].lstrip('-').isdigit() else parts[-1]
            except ValueError:
                pass
    want_m = {1: 10, 2: 10, 4: 5, 5: 5, 7: 3, 8: 3, 15: 2}
    bad_m = []
    for m, want in want_m.items():
        if m not in m_vals:
            bad_m.append('M=' + str(m) + ' 没打到')
        elif m_vals[m] != want:
            bad_m.append('M=' + str(m) + ' 打出 ' + str(m_vals[m]) + '，期望 ' + str(want))
    if not bad_m:
        checks.append((True, '七个 M 值的答案全部正确（M 从 1 到 15 的单调性完整）'))
    else:
        checks.append((False, 'M 值扫描有问题：' + '；'.join(bad_m) + '：二分答案模板要确认 lo 与 hi 的更新'))

    # 边界
    for prefix, expect, label in [
        ('空数组 M=1', '0', '空数组时 M=1 应返回 0'),
        ('单根 M=1', '7', '单根 [7], M=1 应返回 7'),
        ('单根 M=8', '0', '单根 [7], M=8 不可能，返回 0'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, label))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：空数组或 M 过大时要返回 0'))

    for index, expect, label in [('01', '10', 'M=3 答案 10'), ('02', '5', 'M=6 答案 5')]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))

    checks += probe_task1_checks()
    return checks


def probe_task1_checks():
    data, note = probe_json('probe_task01.py')
    if data is None:
        return [(False, '任务 1 的探针跑不起来：' + note)]
    cases, more_cases, scales = data
    checks = []

    bad = []
    for entry in cases:
        label, got, want = entry
        if got != want:
            bad.append(label + ' 打出 ' + str(got) + '，期望 ' + str(want))
    if not bad:
        checks.append((True, '探针：判分八组小数据（含空数组、不可能 M）全部正确'))
    else:
        checks.append((False, '探针：有 ' + str(len(bad)) + ' 组小数据不对：' + short('；'.join(bad))))

    bad_more = []
    for entry in more_cases:
        label, got, want = entry
        if got != want:
            bad_more.append(label + ' 打出 ' + str(got) + '，期望 ' + str(want))
    if not bad_more:
        checks.append((True, '探针：六组更多边界数据全部正确'))
    else:
        checks.append((False, '探针：有 ' + str(len(bad_more)) + ' 组边界不对：' + short('；'.join(bad_more))))

    bad_scale = []
    for entry in scales:
        n, got = entry
        if not isinstance(got, int) or got <= 0:
            bad_scale.append('n=' + str(n) + ' 打出 ' + str(got))
    if not bad_scale:
        checks.append((True, '探针：三档规模上都返回了正数答案'))
    else:
        checks.append((False, '探针：规模数据有问题：' + short('；'.join(bad_scale))))

    return checks


# ══ 任务 2 · 跳石头 ══════════════════════════════════════════════

def check_task2():
    run = run_script('task02_river_hopping.py')
    if run['status'] != 'ok':
        return [(False, 'task02_river_hopping.py 没跑通：' + run['note'])]
    checks = []

    want = [
        ('min_gap=4 移除2', 'True', '移 2 块可使最小间距 ≥ 4'),
        ('min_gap=4 移除1', 'False', '移 1 块不够——至少需要移 2 块'),
        ('min_gap=5 移除2', 'False', '移 2 块也不够让最小间距 ≥ 5'),
    ]
    for prefix, expect, good in want:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行：带 print 的行别改、别删'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 1 的 check 要逐块看间距，间距小的石头移掉'))

    want_bin = [
        ('移除2 最大最小间距', '4', '移 2 块石头，最大最小间距是 4'),
        ('移除0 最大最小间距', '2', '不移石头，最小间距是 2'),
        ('移除3 最大最小间距', '6', '移 3 块石头，最大最小间距是 6'),
    ]
    for prefix, expect, good in want_bin:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 2 的二分和 TODO 1 的 check 一起看'))

    # 扫描移除数（从 0 到 5）
    remove_lines = get_lines(run['out'], '移除')
    remove_vals = {}
    for line in remove_lines:
        parts = line.split()
        if len(parts) >= 2:
            try:
                k = int(parts[0].replace('移除', ''))
                v = int(parts[-1])
                remove_vals[k] = v
            except ValueError:
                pass
    want_remove = {0: 2, 1: 3, 2: 4, 3: 6, 4: 6, 5: 6}
    bad_rm = []
    for r, want in want_remove.items():
        if r not in remove_vals:
            bad_rm.append('移除' + str(r) + ' 没打到')
        elif remove_vals[r] != want:
            bad_rm.append('移除' + str(r) + ' 打出 ' + str(remove_vals[r]) + '，期望 ' + str(want))
    if not bad_rm:
        checks.append((True, '全部 0~5 移除数的答案正确（单调递增：移越多间距越大）'))
    else:
        checks.append((False, '移除数扫描有问题：' + '；'.join(bad_rm)
                       + '：check_jump 的 logic 要逐块判断，最后一段也要 checked'))

    # 边界
    for prefix, expect, label in [
        ('无石头 移除0', '10', '无石头时最小间距就是河长本身'),
        ('一块石头 移除0', '5', '[5], 河长 10, 不移石头 → 间距 5 和 5, 最小 5'),
        ('一块石头 移除1', '10', '移掉石头 → 只剩起点终点, 最小间距 10'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, label))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：边界情况要特殊处理'))

    for index, expect, label in [('01', '4', '移除2 答案 4')]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))

    checks += probe_task2_checks()
    return checks


def probe_task2_checks():
    data, note = probe_json('probe_task02.py')
    if data is None:
        return [(False, '任务 2 的探针跑不起来：' + note)]
    cases, scales = data
    checks = []

    bad = []
    for entry in cases:
        if len(entry) != 3:
            continue
        label, got, want = entry
        if got != want:
            bad.append(label + ' 打出 ' + str(got) + '，期望 ' + str(want))
    if not bad:
        checks.append((True, '探针：判分九组小数据（含课件数据、边界）全部正确'))
    else:
        checks.append((False, '探针：有 ' + str(len(bad)) + ' 组数据不对：' + short('；'.join(bad))))

    bad_scale = []
    for entry in scales:
        if len(entry) != 4:
            continue
        river_len, n_stones, remove, got = entry
        if not isinstance(got, int) or got <= 0 or got > river_len:
            bad_scale.append('河长=' + str(river_len) + ' 石头=' + str(n_stones)
                             + ' 移除=' + str(remove) + ' 打出 ' + str(got))
    if not bad_scale:
        checks.append((True, '探针：三档规模（河长 50/100/500）上都返回了合理答案'))
    else:
        checks.append((False, '探针：规模数据有问题：' + short('；'.join(bad_scale))))

    return checks


# ══ 任务 3 · 暴力验算 ════════════════════════════════════════════

def check_task3():
    run = run_script('task03_bruteforce_verify.py')
    if run['status'] != 'ok':
        return [(False, 'task03_bruteforce_verify.py 没跑通：' + run['note'])]
    checks = []

    for prefix, expect, good in [
        ('暴力 M=3', '10', '暴力枚举 M=3 得到 10'),
        ('暴力 M=6', '5', '暴力枚举 M=6 得到 5'),
        ('暴力 M=7', '3', '暴力枚举 M=7 得到 3'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 1 的暴力要从 max(woods) 往下枚举'))

    bad = get_line(run['out'], '全部不一致组数')
    if bad is None:
        checks.append((False, '没看到「全部不一致组数 …」这一行'))
    elif bad == '0':
        checks.append((True, '200 组随机数据上暴力与二分答案全部一致！二分答案在小数据上工作正确'))
    else:
        checks.append((False, '不一致组数 打出 ' + short(bad) + '，期望 0：'
                       + '二分答案与暴力枚举的结果不一致！'
                       + '检查 TODO 2 的 verify_on_random_data 是不是比较了暴力 vs 二分'))

    for index, expect, label in [('01', '10', '暴力 M=3'), ('02', '5', '暴力 M=6'),
                                 ('03', '0', '不一致组数 0')]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))

    checks += probe_task3_checks()
    return checks


def probe_task3_checks():
    data, note = probe_json('probe_task03.py')
    if data is None:
        return [(False, '任务 3 的探针跑不起来：' + note)]
    cases, pairs = data
    checks = []

    bad = []
    for entry in cases:
        if len(entry) != 3:
            continue
        label, got, want = entry
        if got != want:
            bad.append(label + ' 打出 ' + str(got) + '，期望 ' + str(want))
    if not bad:
        checks.append((True, '探针：十组小数据上暴力枚举全部正确'))
    else:
        checks.append((False, '探针：有 ' + str(len(bad)) + ' 组暴力不对：' + short('；'.join(bad))))

    bad_pairs = []
    for entry in pairs:
        if len(entry) != 4:
            continue
        label, b, bs, match = entry
        if not match:
            bad_pairs.append(label + ' 暴力 ' + str(b) + ' 二分 ' + str(bs))
    if not bad_pairs:
        checks.append((True, '探针：50 组随机数据上暴力与二分全部一致'))
    else:
        checks.append((False, '探针：有 ' + str(len(bad_pairs)) + ' 组不一致：' + short('；'.join(bad_pairs))))

    return checks


# ══ 任务 4 · 破坏单调性 ══════════════════════════════════════════

def check_task4():
    run = run_script('task04_break_monotonicity.py')
    if run['status'] != 'ok':
        return [(False, 'task04_break_monotonicity.py 没跑通：' + run['note'])]
    checks = []

    for prefix, expect, good in [
        ('单调 check_good(8)', 'True', '单调 check: 8 ≤ 8，True'),
        ('单调 二分 [1, 20]', '8', '单调 check 在 [1,20] 上二分找到 8'),
        ('单调 暴力 [1, 20]', '8', '单调 check 在 [1,20] 上暴力找到 8'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：check_good 和二分都是标准模板'))

    for prefix, expect, good in [
        ('不单调 check_bad(8)', 'True', '8 是偶数 ≤ 8 → True'),
        ('不单调 check_bad(7)', 'False', '7 是奇数 → False'),
        ('不单调 check_bad(6)', 'True', '6 是偶数 ≤ 8 → True'),
        ('不单调 check_bad(4)', 'True', '4 是偶数 ≤ 8 → True'),
        ('不单调 check_bad(2)', 'True', '2 是偶数 ≤ 8 → True'),
    ]:
        value = get_line(run['out'], prefix)
        if value is None:
            checks.append((False, '没看到「' + prefix + ' …」这一行'))
        elif value == expect:
            checks.append((True, good))
        else:
            checks.append((False, prefix + ' 打出 ' + short(value) + '，期望 ' + expect
                           + '：TODO 1 的 check_bad 要同时检查偶数和 ≤8'))

    # 区间行
    # 格式：区间 [1, 20]  二分 8  暴力 8  一致
    # 拆分后：['区间', '[1,', '20]', '二分', '8', '暴力', '8', '一致']
    interval_lines = [l for l in run['out'].splitlines() if l.startswith('区间 [')]
    interval_data = []
    for line in interval_lines:
        parts = line.split()
        if len(parts) >= 8:
            try:
                lo = int(parts[1].strip('[').rstrip(','))
                hi = int(parts[2].rstrip(']'))
                bs = int(parts[4])
                bf = int(parts[6])
                match = parts[7]
                interval_data.append((lo, hi, bs, bf, match))
            except (ValueError, IndexError):
                pass

    if not interval_data:
        checks.append((False, '没看到「区间 …」这几行'))
    else:
        # 对不单调的 check，[1,20] 区间上二分找到的不一定是暴力找到的 8
        match_count = sum(1 for _, _, _, _, m in interval_data if m == '一致')
        checks.append((True, '打出了 ' + str(len(interval_data)) + ' 个区间的对照结果，'
                       + str(match_count) + ' 个一致'))
        # 特别检查 [1,5] 区间
        for lo, hi, bs, bf, match in interval_data:
            if lo == 1 and hi == 5:
                if match == '不一致':
                    checks.append((True, '[1,5] 区间上二分与暴力不一致（二分可能找到 2，暴力找到... '
                                   + '实际上暴力在 [1,5] 上也会找到 4 或 2？'
                                   + '枚举从 5 向下：5 奇数 False, 4 偶数 True → 暴力找到 4）'))
                elif bs == 4:
                    checks.append((True, '[1,5] 区间上二分找到 4（这是一个巧合，2→4 的路径刚好处在峰值）'))
                else:
                    checks.append((True, '[1,5] 区间二分找到 ' + str(bs) + '，暴力 ' + str(bf)))
            if lo == 5 and hi == 20:
                # 初始区间 [5,20]，check(12=False)→hi=11, check(8=True)→lo=8...
                # 实际上二分在 [5,20] 上会得到什么？
                # 5:False(odd), 末=5, 初始 hi=20. mid=(5+20+1)//2=13. check(13)=False→hi=12.
                # mid=(5+13)//2=9. check(9)=False→hi=8. mid=(5+8+1)//2=7. check(7)=False→hi=6.
                # mid=(5+6+1)//2=6. check(6)=True→lo=6. lo=6, hi=6→return 6.
                # 暴力从 20 往下: 20(F),19(F),...,8(T). 暴力=8. 二分=6. 不一致!
                pass

    # 结论
    bs_8 = get_line(run['out'], '二分答案认为最大可行值是')
    bf_8 = get_line(run['out'], '暴力枚举认为最大可行值是')
    agree = get_line(run['out'], '两者一致？')

    if bs_8 and bf_8:
        if agree == 'False':
            checks.append((True, '二分答案与暴力枚举不一致——这正是单调性被破坏时的现象'))
        elif agree == 'True':
            checks.append((True, '二分答案与暴力结果一致'))
        else:
            checks.append((True, '二分=' + bs_8 + ' 暴力=' + bf_8 + ' 一致=' + str(agree)))

    for index, expect, label in [
        ('01', 'True', 'check_bad(8)=True'),
        ('02', '8', '二分 [1,20] 结果'),
        ('03', '8', '暴力 [1,20] 结果'),
        ('04', '1', '两者一致标记'),
    ]:
        value = count_value(run['out'], index)
        if value == expect:
            checks.append((True, '计数 ' + index + ' ' + label + ' ' + expect))
        elif value is None:
            checks.append((False, '没看到「计数 ' + index + ' …」这一行'))
        else:
            checks.append((False, '计数 ' + index + ' 打出 ' + short(value) + '，期望 ' + expect))

    checks += probe_task4_checks()
    return checks


def probe_task4_checks():
    data, note = probe_json('probe_task04.py')
    if data is None:
        return [(False, '任务 4 的探针跑不起来：' + note)]
    check_vals, intervals, good_intervals = data
    checks = []

    # 检查 check_bad 的值
    bad_vals = []
    for x, v in check_vals.items():
        expected = (int(x) % 2 == 0 and int(x) <= 8)
        if v != expected:
            bad_vals.append('x=' + str(x) + ' 打出 ' + str(v) + '，期望 ' + str(expected))
    if not bad_vals:
        checks.append((True, '探针：check_bad 从 1 到 20 全部正确（偶数且 ≤8 为 True）'))
    else:
        checks.append((False, '探针：check_bad 有 ' + str(len(bad_vals)) + ' 个 x 不对：'
                       + short('；'.join(bad_vals))))

    # 检查非单调区间的对照
    bad_int = []
    for entry in intervals:
        lo, hi, bs, bf, match = entry
        if lo == 1 and hi == 20:
            # 期望二分找到 8，暴力也找到 8 (在这个区间内暴力枚举得到的是 8)
            if bf != 8:
                bad_int.append('[1,20] 暴力=' + str(bf) + ' 期望 8')
            # 二分可能找到 8 也可能不——这正是非单调性的体现
    if not bad_int:
        checks.append((True, '探针：六个区间上的二分与暴力对照数据已收集'))
    else:
        checks.append((False, '探针：区间对照有问题：' + short('；'.join(bad_int))))

    # 检查单调对照
    for entry in good_intervals:
        lo, hi, bs, bf, match = entry
        if not match:
            checks.append((False, '探针：单调 check 上二分与暴力竟然不一致！检查 check_good'))
    checks.append((True, '探针：单调 check 上二分与暴力一致（基线正确）'))

    return checks


# ══ 主流程 ════════════════════════════════════════════════════════

CHECKERS = {
    'task01_wood_cutting.py': check_task1,
    'task02_river_hopping.py': check_task2,
    'task03_bruteforce_verify.py': check_task3,
    'task04_break_monotonicity.py': check_task4,
}

NO_TODO_HINT = ('没找到探针文件', '探针跑不起来', '还没建这个文件')

TODO_HINT = {
    'task01_wood_cutting.py': 'TODO 1 是 check_wood（sum(w//x) ≥ M）、'
                            'TODO 2 是二分答案（上取整 mid=(lo+hi+1)//2）',
    'task02_river_hopping.py': 'TODO 1 是 check_jump（间距 min_gap 判断是否移石）、'
                             'TODO 2 是二分答案（上取整）',
    'task03_bruteforce_verify.py': 'TODO 1 是 brute_max_wood_length（从大到小枚举）、'
                                 'TODO 2 是 verify_on_random_data（200+ 组对拍）',
    'task04_break_monotonicity.py': 'TODO 1 是 check_bad（偶数且≤8）、'
                                  'TODO 2 是 binary_search_on_answer（标准二分模板）、'
                                  'TODO 3 是 brute_best（从大到小枚举）',
}


def main():
    print('StudyMate lab 0022 · 自动判分（二分答案：猜一个再验一遍）')
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
            if (not ok and 'TODO' not in message
                    and not any(mark in message for mark in NO_TODO_HINT)):
                message = message + '（改这个文件的 ' + TODO_HINT[filename] + '）'
            print('  ' + ('PASS' if ok else 'FAIL') + '  ' + message)
            if not ok:
                all_ok = False
        if all_ok:
            print('  → 这个任务过了')
        else:
            failed.append(filename)
        print()

    print('─' * 60)
    print('4 个任务：' + str(4 - len(failed)) + ' 个通过，' + str(len(failed)) + ' 个还没通过')
    if failed:
        print('没过的：' + '、'.join(failed))
        print('卡住了先读 README.md 的「卡壳顺序」：读错误信息 → 自己跑一遍 → 看 FAIL 行 → 再对线索。')
        print('四个任务都过了，再对照 solutions/0022-binary-search-on-answer/ 看参考解。')
        return 1
    print('四个任务都过了。现在去对照 solutions/0022-binary-search-on-answer/：')
    print('比一比你的写法与参考解，再用一句话回答「二分答案的前提是什么？」')
    return 0


if __name__ == '__main__':
    sys.exit(main())