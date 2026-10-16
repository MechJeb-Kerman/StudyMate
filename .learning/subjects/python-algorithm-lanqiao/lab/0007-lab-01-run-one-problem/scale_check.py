"""任务 4 · 量一量：慢的那一行在哪里（提交前的复杂度判断）

题目 A 的正解在样例上看不出任何优势：只要答案对，怎么写都能过样例。
差别在数据规模上——这个脚本把两种查重写法放在同一份数据上各量一次，
再由你推断规模放大 10 倍要多久。

输出格式（判分按行读，**别改**；三个 TODO 填上就能打出来）：

    n=20000 列表 in 用时 0.855123 秒 不同元素 20000
    n=20000 集合 in 用时 0.001234 秒 不同元素 20000
    列表版放大 10 倍预计 85.51 秒 超出 1 秒时限 True

自己跑： py scale_check.py
判分：   py run_tests.py
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
    """跑一次 func(a)，量出耗时并交回 (耗时秒, 结果)（给好的，别改）。"""
    t0 = time.perf_counter()
    result = func(a)
    t1 = time.perf_counter()
    return t1 - t0, result


# ══ TODO 1 ═════════════════════════════════════════════════════════════════
# distinct_by_list(a)：用列表查重——每遇到一个数，`in` 从头比过去，没出现过就追加。
# 交回不同元素的个数。
def distinct_by_list(a):
    return 0


# ══ TODO 2 ═════════════════════════════════════════════════════════════════
# distinct_by_set(a)：同一件事换一个容器（第 3 课）。交回不同元素的个数。
def distinct_by_set(a):
    return 0


def main():
    a = make_data(N)

    t_list, count_list = time_it(distinct_by_list, a)
    print(f'n={N} 列表 in 用时 {t_list:.6f} 秒 不同元素 {count_list}')

    t_set, count_set = time_it(distinct_by_set, a)
    print(f'n={N} 集合 in 用时 {t_set:.6f} 秒 不同元素 {count_set}')

    # ══ TODO 3 ═════════════════════════════════════════════════════════════
    # 推断：n 从 20000 变成 200000（10 倍规模）时，列表版大约要跑多久？
    # 提示（第 2 课）：先数一数「列表版一共要比较多少次」，看它随规模怎么涨——
    #   涨 10 倍、还是涨 100 倍？再把这个倍数乘到实测的 t_list 上。
    predicted = 0.0
    print(f'列表版放大 10 倍预计 {predicted:.2f} 秒 超出 1 秒时限 {predicted > LIMIT}')


main()
