"""任务 4 · 放大十倍，看哪一行跟着涨（留白版）

目标：同一段查法代码，n 从 10^5 放大到 10^6（十倍），
      量出「列表 in」与「集合 in」各自变成了几倍。
要点：数字来自你自己的机器，别背课件里的秒数；要记的是趋势。

跑： py task4_scale.py
判： py run_tests.py
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

# TODO 1：量 lst_small 的查法耗时（for x in targets_small: y = x in lst_small），存进 t_list_small
t_list_small = 0.0
# TODO 2：量 s_small 的查法耗时，存进 t_set_small
t_set_small = 0.0

# ══ 第 2 组：n = 1000000（放大十倍，代码形状和上面一样）══
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

# TODO 3：量 lst_big 的查法耗时，存进 t_list_big
t_list_big = 0.0
# TODO 4：量 s_big 的查法耗时，存进 t_set_big
t_set_big = 0.0

# ── 算倍数并打印（别改）────────────────────────────────────
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
