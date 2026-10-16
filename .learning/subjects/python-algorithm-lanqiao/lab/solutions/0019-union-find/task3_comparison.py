#!/usr/bin/env python3
"""任务 3 · 2×2 对照表 —— 参考解"""

from __future__ import annotations

import random
import time

from tools import PROBE_DATA, height_of, find_steps, dsu_variants


def measure(name, cls, n, queries):
    dsu = cls(n)

    for i in range(n - 1):
        dsu.union(i, i + 1)

    h = height_of(dsu.parent)

    # 测查询前的 find 步数（取链的根的另一端）
    pre_steps = 0
    for node in range(min(n, 10)):
        pre_steps += find_steps(dsu, node)

    pairs = [(random.randrange(n), random.randrange(n)) for _ in range(queries)]

    t0 = time.perf_counter()
    for a, b in pairs:
        _ = dsu.find(a)
        _ = dsu.find(b)
    t1 = time.perf_counter()
    elapsed = t1 - t0

    # 测查询后的 find 步数
    post_steps = 0
    for node in range(min(n, 10)):
        post_steps += find_steps(dsu, node)

    total_finds = queries * 2
    print(f'变体 {name} 树高 {h} 耗时 {elapsed:.6f} 秒 查询次数 {total_finds}')
    print(f'变体 {name} 找根步数 查前 {pre_steps} 查后 {post_steps}')

    return h, elapsed, total_finds, pre_steps, post_steps


if __name__ == '__main__':
    random.seed(42)
    n = PROBE_DATA['task3']['n']
    qc = PROBE_DATA['task3']['queries']

    print('2×2 对照表（链状递增边 n=2000，2 万次查询）')
    print()
    print(f'{"变体":>10}  {"树高":>6}  {"耗时(秒)":>12}  {"查询次数":>10}')

    results = []
    for name, cls in dsu_variants():
        h, elapsed, total, pre, post = measure(name, cls, n, qc)
        results.append((name, h, elapsed, total, pre, post))

    print()
    print(f'{"变体":>10}  {"树高":>6}  {"耗时(秒)":>12}  {"查询次数":>10}  {"步数(查前)":>10}  {"步数(查后)":>10}')
    for name, h, elapsed, total, pre, post in results:
        print(f'{name:>10}  {h:>6}  {elapsed:>12.6f}  {total:>10}  {pre:>10}  {post:>10}')