"""任务 1 · 三种查法的耗时对照（留白版）

目标：同一份数据，用「列表 in」「集合 in」「字典查」各跑一遍，打印三行耗时。
要点：计时用 time.perf_counter() 前后各取一次、相减；查的次数都是 200 次。

跑： py task1_lookup.py
判： py run_tests.py
"""

import time

n = 1000000
lookup = 200

# ── 给好的部分：造数据（n = 10^6）──────────────────────────
lst = []
for i in range(n):
    lst.append(i)
s = set()
for i in range(n):
    s.add(i)
d = {}
for i in range(n):
    d[i] = i

# 要查的目标：最后 200 个数（接近末尾，列表得从头扫过来）
targets = []
for i in range(n - lookup, n):
    targets.append(i)

# ── 第 1 步：量「列表 in」──────────────────────────────────
# TODO 1：t0 = time.perf_counter()
#         写一段 for x in targets: y = x in lst
#         t1 = time.perf_counter()
#         把 t1 - t0 存进 t_list
t_list = 0.0

# ── 第 2 步：量「集合 in」──────────────────────────────────
# TODO 2：和上面同一个形状，把 lst 换成 s，结果存进 t_set
t_set = 0.0

# ── 第 3 步：量「字典查」───────────────────────────────────
# TODO 3：和上面同一个形状，把 lst 换成 d，结果存进 t_dict
t_dict = 0.0

# ── 打印对照表（这三行别改，自动判分按它们读数字）──────────
print('列表 in', f'{t_list:.6f}', '秒')
print('集合 in', f'{t_set:.6f}', '秒')
print('字典查', f'{t_dict:.6f}', '秒')
