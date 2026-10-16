"""任务 4 · 放大十倍看趋势（参考解）

要看的趋势：n 从 10^5 放大到 10^6，
  · 列表 in 变成约 10 倍（每次几乎扫完整个列表，$O(n)$，规模涨十倍耗时也涨十倍）；
  · 集合 in 几乎不动（约 1 倍，哈希查找与元素个数无关）。
所以「放大十倍」这一步能把「哪一行跟着规模涨」直接看出来——这就是估算复杂度的实感。
"""

import time

lookup = 200

# ══ 第 1 组：n = 100000 ═══════════════════════════════════
n_small = 100000
lst_small = []
for i in range(n_small):
    lst_small.append(i)
s_small = set()
for i in range(n_small):
    s_small.add(i)
targets_small = []
for i in range(n_small - lookup, n_small):
    targets_small.append(i)

t0 = time.perf_counter()
for x in targets_small:
    y = x in lst_small
t1 = time.perf_counter()
t_list_small = t1 - t0

t0 = time.perf_counter()
for x in targets_small:
    y = x in s_small
t1 = time.perf_counter()
t_set_small = t1 - t0

# ══ 第 2 组：n = 1000000 ══════════════════════════════════
n_big = 1000000
lst_big = []
for i in range(n_big):
    lst_big.append(i)
s_big = set()
for i in range(n_big):
    s_big.add(i)
targets_big = []
for i in range(n_big - lookup, n_big):
    targets_big.append(i)

t0 = time.perf_counter()
for x in targets_big:
    y = x in lst_big
t1 = time.perf_counter()
t_list_big = t1 - t0

t0 = time.perf_counter()
for x in targets_big:
    y = x in s_big
t1 = time.perf_counter()
t_set_big = t1 - t0

ratio_list = 0.0
if t_list_small > 0:
    ratio_list = t_list_big / t_list_small
ratio_set = 0.0
if t_set_small > 0:
    ratio_set = t_set_big / t_set_small

print('n=100000 列表 in', f'{t_list_small:.6f}', '秒', '集合 in', f'{t_set_small:.6f}', '秒')
print('n=1000000 列表 in', f'{t_list_big:.6f}', '秒', '集合 in', f'{t_set_big:.6f}', '秒')
print('列表 in 放大十倍变成', f'{ratio_list:.2f}', '倍')
print('集合 in 放大十倍变成', f'{ratio_set:.2f}', '倍')
