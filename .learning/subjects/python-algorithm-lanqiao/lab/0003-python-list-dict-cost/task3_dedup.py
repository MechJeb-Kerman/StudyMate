"""任务 3 · 把列表查重改成集合查重（留白版）

目标：先看懂列表版查重，再把它改成集合版；两次的结果必须一模一样，
      耗时差多少由你自己量出来。

跑： py task3_dedup.py
判： py run_tests.py
"""

import time

n = 20000
data = []
for i in range(n):
    data.append(i % 5000)

# ══ 列表版（给好的，先跑一遍看懂它在做什么）═══════════════
seen = []
dup_list = 0
t0 = time.perf_counter()
for x in data:
    if x in seen:
        dup_list += 1
    else:
        seen.append(x)
t1 = time.perf_counter()
t_list_dedup = t1 - t0
distinct_list = len(seen)

# ══ 集合版（留白：只换容器、改一行 append）════════════════
# TODO 1：seen_set 从空集合开始（提示：空集合只能写 set()，{} 建的是空字典）
seen_set = set()

# TODO 2：照上面那段再来一遍，这次：
#         - in 的容器用 seen_set
#         - 新元素用 seen_set.add(x) 放进去
#         - 重复个数存进 dup_set、不同元素个数存进 distinct_set
#         - 前后各取一次 perf_counter()，差值存进 t_set_dedup
dup_set = 0
distinct_set = 0
t_set_dedup = 0.0

# ── 结果比对（别改）────────────────────────────────────────
same = False
if dup_list == dup_set:
    if distinct_list == distinct_set:
        same = True

# ── 打印（这四行别改）──────────────────────────────────────
print('列表版 不同元素', distinct_list, '重复', dup_list, f'{t_list_dedup:.6f}', '秒')
print('集合版 不同元素', distinct_set, '重复', dup_set, f'{t_set_dedup:.6f}', '秒')
print('结果一致', same)
