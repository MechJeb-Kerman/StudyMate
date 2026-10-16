"""参考解 · 任务 4 · 量一量：慢的那一行在哪里（实验一）

题目 A 的正解用集合查重；换成列表查重（`if x in seen`）在样例上看不出任何区别——
这一个脚本把两种写法放在同一份数据上各量一次，再由你推断规模放大 10 倍要多久。

输出格式（判分按行读，别改）：

    n=20000 列表 in 用时 0.855123 秒 不同元素 20000
    n=20000 集合 in 用时 0.001234 秒 不同元素 20000
    列表版放大 10 倍预计 85.51 秒 超出 1 秒时限 True

跑： py scale_check.py
判： py run_tests.py
"""

import random
import time

N = 20000          # 本机量得动的小规模；题目 A 的大数据是 10 万个
LIMIT = 1.0        # 题面给的时限（秒）


def make_data(n):
    """造 n 个数（给好的，别改）：与题目 A 同一档取值（1 到 10^9）。"""
    rnd = random.Random(20240007)
    return [rnd.randint(1, 10 ** 9) for _ in range(n)]


def time_it(func, a):
    """跑一次 func(a)，量耗时并交回 (耗时秒, 结果)（给好的，别改）。"""
    t0 = time.perf_counter()
    result = func(a)
    t1 = time.perf_counter()
    return t1 - t0, result


def distinct_by_list(a):
    """列表查重：每次 `in` 都要从头比过去，整段是 O(n²)。"""
    seen = []
    for x in a:
        if x in seen:
            continue
        seen.append(x)
    return len(seen)


def distinct_by_set(a):
    """集合查重：`in` 与 `add` 都是平均 O(1)，整段是 O(n)。"""
    seen = set()
    for x in a:
        seen.add(x)
    return len(seen)


def main():
    a = make_data(N)

    t_list, count_list = time_it(distinct_by_list, a)
    print(f'n={N} 列表 in 用时 {t_list:.6f} 秒 不同元素 {count_list}')

    t_set, count_set = time_it(distinct_by_set, a)
    print(f'n={N} 集合 in 用时 {t_set:.6f} 秒 不同元素 {count_set}')

    # 列表版的操作次数 ≈ 每次 `in` 扫过的长度之和，规模扩大 k 倍，它就扩大 k² 倍：
    # n 从 20000 到 200000 是 10 倍规模，列表版要慢约 100 倍。
    predicted = t_list * 100
    print(f'列表版放大 10 倍预计 {predicted:.2f} 秒 超出 1 秒时限 {predicted > LIMIT}')


main()
