#!/usr/bin/env python3
"""lab 0003 · 自动判分：跑任务脚本、读它们打印出来的数字。

用法（在 lab/0003-python-list-dict-cost/ 目录里）：

    py run_tests.py

判法：每个任务单独起一个进程跑，只看 stdout 里那几行固定格式的数字，
      不 import 也不检查学生代码的写法。
      数字必须真的是量出来的——留白没填时打出来的是 0，一律判不通过。

退出码：0 = 四个任务都通过；1 = 还有没通过的。
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ── 判定阈值（口径见 lab/README.md「怎么算过」）─────────────────────────────
# 它们是「差得足够远」的下限，不是要背的秒数：同一份代码换台机器绝对值会变，
# 但列表 in 与集合 in 的差距、pop(0) 与 popleft 的差距都是几个数量级。
MIN_LIST_LOOKUP = 0.05      # 列表 in 200 次至少要能量到的秒数（本机约 1.5 秒）
MIN_POP0_TOTAL = 0.10       # pop(0) 20 万次至少要能量到的秒数（本机约 2.7 秒）
LIST_OVER_HASH = 50         # 列表 in 至少要比集合/字典慢这么多倍（本机约 8 万倍）
POP0_OVER_POPLEFT = 20      # pop(0) 至少要比 popleft 慢这么多倍（本机约 200 倍）
DEDUP_OVER_SET = 3          # 列表查重至少要比集合查重慢这么多倍（本机约 30 倍）
SCALE_LIST_MIN = 4.0        # 规模放大十倍后，列表 in 至少要涨到这么多倍（本机约 10-14 倍）
SCALE_LIST_MAX = 40.0       # 涨得比这还多，多半是两次查的次数不一样
SCALE_SET_MAX = 5.0         # 集合 in 放大十倍后不该涨过这么多倍（本机约 1 倍）
EXPECTED_COUNT = 200000     # task2 的出队次数（count 是给好的，别改）
EXPECTED_DISTINCT = 5000    # task3 的数据：0..4999 各出现 4 次
EXPECTED_DUP = 15000

TIMEOUTS = {
    'task1_lookup.py': 300,
    'task2_queue.py': 300,
    'task3_dedup.py': 300,
    'task4_scale.py': 600,
}


def run_script(name: str):
    """跑一个任务脚本 → (状态, stdout, 备注)。状态：ok / missing / crash / timeout。"""
    path = HERE / name
    if not path.is_file():
        return 'missing', '', f'还没建这个文件：{name}'
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    try:
        done = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(HERE), env=env, timeout=TIMEOUTS.get(name, 300),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
        )
    except subprocess.TimeoutExpired:
        return 'timeout', '', f'跑了 {TIMEOUTS.get(name, 300)} 秒还没结束（死循环？规模写大了？）'
    if done.returncode != 0:
        tail = '\n'.join(
            line for line in (done.stderr or '').strip().splitlines()[-5:]
        )
        return 'crash', done.stdout or '', f'脚本报错退出（退出码 {done.returncode}）：\n{tail}'
    return 'ok', done.stdout or '', ''


def find(out: str, pattern: str):
    """按整行取出一组数字；没打到那一行就返回 None。"""
    match = re.search(pattern, out, re.M)
    if not match:
        return None
    if match.groups():
        return tuple(float(value) for value in match.groups())
    return ()


def show(value: float) -> str:
    return f'{value:.6f}'


# ── 每个任务一组判定：(通过?, 一句话) ──────────────────────────────────────

def check_task1(out: str):
    got = find(out, r'^列表 in ([0-9]+\.[0-9]+) 秒$'), \
        find(out, r'^集合 in ([0-9]+\.[0-9]+) 秒$'), \
        find(out, r'^字典查 ([0-9]+\.[0-9]+) 秒$')
    if any(item is None for item in got):
        return [(False, '三行对照表没打全：要有「列表 in X 秒」「集合 in X 秒」「字典查 X 秒」'
                        '三行（那三行是给好的，别改格式）')]
    t_list, t_set, t_dict = (item[0] for item in got)
    checks = [(True, f'三行都读到了：列表 in {show(t_list)} 秒 / 集合 in {show(t_set)} 秒 '
                     f'/ 字典查 {show(t_dict)} 秒')]
    checks.append((
        t_list >= MIN_LIST_LOOKUP,
        f'列表 in 量到 {show(t_list)} 秒，是真的量出来的'
        if t_list >= MIN_LIST_LOOKUP else
        f'列表 in 只量到 {show(t_list)} 秒：TODO 1 那一整段（t0、循环、t1、相减）还没写？'
    ))
    checks.append((
        t_set > 0 and t_dict > 0,
        '集合 in 与字典查也都量到了'
        if t_set > 0 and t_dict > 0 else
        '集合 in 或 字典查 还是 0：TODO 2、TODO 3 那两段还没写'
    ))
    if t_set > 0 and t_dict > 0:
        ok = t_list >= LIST_OVER_HASH * t_set and t_list >= LIST_OVER_HASH * t_dict
        checks.append((
            ok,
            f'趋势对上了：列表 in 比集合 in 慢 {t_list / t_set:.0f} 倍、比字典慢 '
            f'{t_list / t_dict:.0f} 倍'
            if ok else
            f'列表 in 应该比集合 in 慢 {LIST_OVER_HASH} 倍以上，现在只有 '
            f'{t_list / t_set:.1f} 倍：两个都重跑一次，看看量集合那段是不是把 s 写成了 lst'
        ))
    return checks


def check_task2(out: str):
    got0 = find(out, r'^pop\(0\) ([0-9]+) 次 ([0-9]+\.[0-9]+) 秒$')
    got1 = find(out, r'^popleft ([0-9]+) 次 ([0-9]+\.[0-9]+) 秒$')
    same = re.search(r'^出队顺序一致 (True|False)$', out, re.M)
    if got0 is None or got1 is None or same is None:
        return [(False, '三行没打全：要有「pop(0) 200000 次 X 秒」「popleft 200000 次 X 秒」'
                        '「出队顺序一致 True/False」')]
    count, t_pop0 = got0
    _, t_popleft = got1
    checks = [(True, f'两行耗时都读到了：pop(0) {show(t_pop0)} 秒 / popleft {show(t_popleft)} 秒')]
    checks.append((
        int(count) == EXPECTED_COUNT,
        f'出队 {int(count)} 次，规模没被改小'
        if int(count) == EXPECTED_COUNT else
        f'出队次数是 {int(count)}，应该是 {EXPECTED_COUNT}（count 是给好的，别改）'
    ))
    checks.append((
        t_pop0 >= MIN_POP0_TOTAL,
        f'pop(0) 量到 {show(t_pop0)} 秒，是真的量出来的'
        if t_pop0 >= MIN_POP0_TOTAL else
        f'pop(0) 只量到 {show(t_pop0)} 秒：TODO 1 那一整段还没写？'
    ))
    if t_popleft > 0:
        ok = t_popleft <= t_pop0 / POP0_OVER_POPLEFT
        checks.append((
            ok,
            f'popleft 比 pop(0) 快 {t_pop0 / t_popleft:.0f} 倍'
            if ok else
            f'popleft 应该比 pop(0) 快 {POP0_OVER_POPLEFT} 倍以上，现在只有 '
            f'{t_pop0 / t_popleft:.1f} 倍：检查 deque 那段出队用的是不是 popleft、'
            f'列表那段用的是不是 pop(0)'
        ))
    else:
        checks.append((False, 'popleft 还是 0：TODO 2、TODO 3 那两段还没写'))
    checks.append((
        same.group(1) == 'True',
        '两种写法的出队顺序一致：先进先出没被改坏'
        if same.group(1) == 'True' else
        '出队顺序一致 是 False：两段都要真的把元素出队（各出 5 个记下来再比），'
        'deque 那段别写成 pop()'
    ))
    return checks


def check_task3(out: str):
    got_list = find(out, r'^列表版 不同元素 ([0-9]+) 重复 ([0-9]+) ([0-9]+\.[0-9]+) 秒$')
    got_set = find(out, r'^集合版 不同元素 ([0-9]+) 重复 ([0-9]+) ([0-9]+\.[0-9]+) 秒$')
    same = re.search(r'^结果一致 (True|False)$', out, re.M)
    if got_list is None or got_set is None or same is None:
        return [(False, '三行没打全：要有「列表版 不同元素 X 重复 Y Z 秒」'
                        '「集合版 不同元素 X 重复 Y Z 秒」「结果一致 True/False」')]
    distinct_list, dup_list, t_list_dedup = got_list
    distinct_set, dup_set, t_set_dedup = got_set
    checks = [(True, f'两版都读到了：列表版 不同元素 {int(distinct_list)} 重复 {int(dup_list)}，'
                     f'集合版 不同元素 {int(distinct_set)} 重复 {int(dup_set)}')]
    checks.append((
        int(dup_set) == EXPECTED_DUP,
        f'集合版数出 {int(dup_set)} 个重复（和给好的列表版一致）'
        if int(dup_set) == EXPECTED_DUP else
        f'集合版数出 {int(dup_set)} 个重复，应该是 {EXPECTED_DUP}：TODO 2 那段还没写，'
        f'或者把 add 写成了 append'
    ))
    checks.append((
        same.group(1) == 'True' and int(distinct_list) == int(distinct_set),
        '两版结果一模一样：集合版是等价改写'
        if same.group(1) == 'True' and int(distinct_list) == int(distinct_set) else
        '结果一致 是 False：集合版要和列表版数出同样的不同元素数与重复数'
    ))
    checks.append((
        t_set_dedup > 0 and t_list_dedup >= DEDUP_OVER_SET * t_set_dedup,
        f'集合版比列表版快 {t_list_dedup / t_set_dedup:.0f} 倍'
        if t_set_dedup > 0 and t_list_dedup >= DEDUP_OVER_SET * t_set_dedup else
        (f'集合版的耗时还是 0：TODO 2 里前后那两次 perf_counter() 还没有'
         if t_set_dedup <= 0 else
         f'集合版只比列表版快 {t_list_dedup / t_set_dedup:.1f} 倍，应该差 {DEDUP_OVER_SET} 倍以上：'
         f'看看 in 的容器是不是真的换成了 seen_set')
    ))
    return checks


def check_task4(out: str):
    small = find(out, r'^n=100000 列表 in ([0-9]+\.[0-9]+) 秒 集合 in ([0-9]+\.[0-9]+) 秒$')
    big = find(out, r'^n=1000000 列表 in ([0-9]+\.[0-9]+) 秒 集合 in ([0-9]+\.[0-9]+) 秒$')
    rl = find(out, r'^列表 in 放大十倍变成 ([0-9]+\.[0-9]+) 倍$')
    rs = find(out, r'^集合 in 放大十倍变成 ([0-9]+\.[0-9]+) 倍$')
    if small is None or big is None or rl is None or rs is None:
        return [(False, '四行没打全：两组「n=… 列表 in X 秒 集合 in X 秒」'
                        '加两行「… 放大十倍变成 X 倍」')]
    t_list_small, t_set_small = small
    t_list_big, t_set_big = big
    checks = [(True, f'两组数字都读到了：n=100000 列表 {show(t_list_small)} 秒 / '
                     f'n=1000000 列表 {show(t_list_big)} 秒')]
    done = t_list_small > 0 and t_set_small > 0 and t_list_big > 0 and t_set_big > 0
    checks.append((
        done,
        '四次查法都量到了' if done else
        '还有没量到的（打出来是 0.000000）：TODO 1 - TODO 4 四处逐个补上'
    ))
    if done:
        checks.append((
            SCALE_LIST_MIN <= rl[0] <= SCALE_LIST_MAX,
            f'列表 in 放大十倍变成 {rl[0]:.2f} 倍：跟着规模线性变慢'
            if SCALE_LIST_MIN <= rl[0] <= SCALE_LIST_MAX else
            (f'列表 in 只变成 {rl[0]:.2f} 倍（该接近 10）：n=1000000 那次（TODO 3）'
             f'是不是还没量、或者两组查的次数不一样'
             if rl[0] < SCALE_LIST_MIN else
             f'列表 in 变成 {rl[0]:.2f} 倍，比 10 倍还多：两组是不是查了不同次数')
        ))
        checks.append((
            rs[0] < SCALE_SET_MAX,
            f'集合 in 放大十倍变成 {rs[0]:.2f} 倍：几乎不随规模变'
            if rs[0] < SCALE_SET_MAX else
            f'集合 in 变成 {rs[0]:.2f} 倍，应该几乎不动：TODO 4 那段量的是不是列表'
            f'（或者两组查的次数不一样）'
        ))
    return checks


TASKS = [
    ('任务 1 · 三种查法的耗时对照', 'task1_lookup.py', check_task1),
    ('任务 2 · pop(0) 与 popleft 的对照', 'task2_queue.py', check_task2),
    ('任务 3 · 列表查重改集合查重', 'task3_dedup.py', check_task3),
    ('任务 4 · 放大十倍看趋势', 'task4_scale.py', check_task4),
]


def main() -> int:
    print('StudyMate lab 0003 · 自动判分（列表与字典的隐藏价格）')
    print(f'目录：{HERE}')
    print()
    failed = []
    for title, filename, checker in TASKS:
        print(f'{title}（{filename}）')
        status, out, note = run_script(filename)
        if status != 'ok':
            print(f'  FAIL  {note}')
            if out.strip():
                print('  ---- 脚本已经打印出来的内容 ----')
                for line in out.strip().splitlines()[-5:]:
                    print(f'  | {line}')
            print()
            failed.append(filename)
            continue
        checks = checker(out)
        for ok, message in checks:
            print(f'  {"PASS" if ok else "FAIL"}  {message}')
        if all(ok for ok, _ in checks):
            print('  → 这个任务过了')
        else:
            failed.append(filename)
        print()

    print('─' * 60)
    print(f'{len(TASKS)} 个任务：{len(TASKS) - len(failed)} 个通过，{len(failed)} 个还没通过')
    if failed:
        print('没过的：' + '、'.join(failed))
        print('卡住了先读 ../README.md 的「卡壳顺序」：读错误信息 → 看提示 → 再对线索。')
        print('全部通过之后，再对照 ../solutions/0003-python-list-dict-cost/ 看参考解。')
        return 1
    print('四个任务都过了。现在去对照 ../solutions/0003-python-list-dict-cost/：')
    print('比一比你的写法和参考解的差距，再说一句「哪一行决定了快慢」。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
