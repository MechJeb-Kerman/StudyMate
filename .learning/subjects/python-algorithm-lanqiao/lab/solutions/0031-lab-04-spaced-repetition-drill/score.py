#!/usr/bin/env python3
r"""lab 0031 · 判分脚本（实验四：一次完整的赛前模拟）

用法（在 lab/0031-lab-04-spaced-repetition-drill/ 目录里）：

    py score.py

它做三件事，一件都不多：

    1 · 读 answers/p1.py … answers/p5.py（没有的文件按 0 分算，不报错）
    2 · 对每题跑 problems/pN/cases/ 下的**全部**测试数据，逐组对比输出
    3 · 打印每题得分与总分，并把逐组结果写进 score.json

这个脚本**不判对错语义**——它只做「跑题 + 对比输出」。
你的程序交不出答案（报错、超时、输出对不上）都只记这一组不过，
每题的分按测试点平分。

退出码：五道题都满分是 0，还有丢分的（或还没交手）是 1。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

ANSWERS = HERE / 'answers'
PROBLEMS = HERE / 'problems'
SCORE_JSON = HERE / 'score.json'

# 每题一道题一个子目录，题目点数与时限写在 problems/manifest.json 里。
PROBLEM_IDS = ['p1', 'p2', 'p3', 'p4', 'p5']

# 判分自己的兜底时限：单组数据最多跑这么久（题面写的时限是评测机上的，
# 本机慢一些，这里宽一点）。manifest.json 里每题可以各写一个。
DEFAULT_TIMEOUT = 15.0


def load_manifest():
    path = PROBLEMS / 'manifest.json'
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def case_files(pid):
    """这一题的测试数据：cases/case01.in … 按编号排好。"""
    folder = PROBLEMS / pid / 'cases'
    if not folder.is_dir():
        return []
    return sorted(folder.glob('case*.in'))


def normalize(text):
    """对比输出时的口径：去掉每行末尾空白、去掉整段首尾空行。

    行内空白、大小写都照原样比——题面怎么写就怎么比。
    """
    if text is None:
        return ''
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    rows = [line.rstrip() for line in text.split('\n')]
    while rows and not rows[0]:
        rows.pop(0)
    while rows and not rows[-1]:
        rows.pop()
    return '\n'.join(rows)


def run_case(script, data, timeout):
    """跑一组数据 → (是否通过, 说明, 用时秒, 实际输出的开头若干字)。"""
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    started = time.perf_counter()
    try:
        done = subprocess.run([sys.executable, str(script)], cwd=str(script.parent),
                              input=data, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return False, '超时（超过 ' + str(timeout) + ' 秒）', timeout, ''
    except Exception as exc:
        return False, '起不了子进程：' + type(exc).__name__ + ': ' + str(exc), 0.0, ''
    used = time.perf_counter() - started
    if done.returncode != 0:
        tail = ' '.join((done.stderr or '').strip().splitlines()[-1:])
        return False, '退出码 ' + str(done.returncode) + '（' + tail[:90] + '）', used, done.stdout or ''
    return True, '', used, done.stdout or ''


def first_difference(got, want):
    """对不上时点出第一处不一样，省得自己去 diff。"""
    rows_got = got.split('\n')
    rows_want = want.split('\n')
    for i in range(max(len(rows_got), len(rows_want))):
        a = rows_got[i] if i < len(rows_got) else '（没有这一行）'
        b = rows_want[i] if i < len(rows_want) else '（多出这一行）'
        if a != b:
            return '第 ' + str(i + 1) + ' 行：交回 ' + repr(a[:40]) + '，期望 ' + repr(b[:40])
    return '对的'


def check_problem(pid, info, timeout):
    """判一题：逐组跑，交回 (得分, 满分, 逐组结果)。"""
    total = int(info['points'])
    files = case_files(pid)
    script = ANSWERS / (pid + '.py')
    rows = []
    if not files:
        return 0, total, [{'case': '-', 'ok': False, 'note': 'problems/' + pid
                           + '/cases/ 里没有测试数据'}]
    if not script.is_file():
        for path in files:
            rows.append({'case': path.name, 'ok': False,
                         'note': 'answers/' + pid + '.py 不在（还没交手）'})
        return 0, total, rows

    per = total / len(files)
    got_points = 0.0
    for path in files:
        data = path.read_text(encoding='utf-8', errors='replace')
        want_path = path.with_suffix('.out')
        want = normalize(want_path.read_text(encoding='utf-8', errors='replace')) \
            if want_path.is_file() else None
        ok, note, used, out = run_case(script, data, timeout)
        if ok and want is None:
            ok, note = False, '判分数据缺 case*.out（这一组没法比）'
        elif ok:
            got = normalize(out)
            if got == want:
                note = ''
            else:
                ok = False
                note = first_difference(got, want)
        row = {'case': path.name, 'ok': bool(ok), 'seconds': round(used, 3)}
        if note:
            row['note'] = note
        if ok:
            got_points += per
        rows.append(row)

    score = int(round(got_points)) if abs(got_points - round(got_points)) < 1e-9 \
        else round(got_points, 2)
    return score, total, rows


def main():
    print('═' * 72)
    print('lab 0031 · 判分（一次完整的赛前模拟）')
    print('═' * 72)

    manifest = load_manifest()
    if manifest is None:
        print('FAIL 找不到 problems/manifest.json——判分数据就在 problems/ 里，别改目录名')
        return 1

    problems = manifest.get('problems', {})
    report = {'total': 0, 'max_total': 0, 'problems': {}}
    for pid in PROBLEM_IDS:
        info = problems.get(pid)
        if info is None:
            print('FAIL manifest.json 里没有 ' + pid)
            return 1
        timeout = float(info.get('timeout_seconds', DEFAULT_TIMEOUT))
        score, total, rows = check_problem(pid, info, timeout)
        report['problems'][pid] = {
            'title': info.get('title', pid),
            'points': total,
            'score': score,
            'cases': rows,
        }
        report['total'] += score
        report['max_total'] += total

        title = info.get('title', pid)
        print('')
        print('── ' + pid + ' · ' + title + '（' + str(total) + ' 分）'
              + ' ' + '─' * max(0, 40 - len(title) - len(pid)))
        for row in rows:
            mark = 'PASS' if row['ok'] else 'FAIL'
            line = '  ' + mark + ' ' + row['case']
            if 'seconds' in row:
                line += '  ' + f"{row['seconds']:.2f}s"
            if row.get('note'):
                line += '  ' + row['note']
            print(line)
        print('  得分：' + str(score) + ' / ' + str(total))

    print('')
    print('═' * 72)
    print('总分：' + str(report['total']) + ' / ' + str(report['max_total']))
    report['note'] = ('这一课真正要判的是 timeline.md 与 explain.md：'
                      '跑 py check_timeline.py')
    SCORE_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2,
                                     sort_keys=False) + '\n', encoding='utf-8')
    print('逐组结果已写进：' + SCORE_JSON.name)
    print('接着跑：py check_timeline.py   （记录与讲解稿那一侧的自检）')
    return 0 if report['total'] == report['max_total'] else 1


if __name__ == '__main__':
    sys.exit(main())
