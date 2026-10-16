"""任务 3 · 列表查重改集合查重（参考解）

改动只有两处：容器从 [] 换成 set()，新元素从 append(x) 换成 add(x)；
x in seen 那一行不用改（集合同样支持 in）。结果必须一模一样。
本机口径：n = 20000、取值 0..4999 时，列表版约 0.3 秒（每来一个元素都要扫一遍 seen，
是 $O(n^2)$ 的根源），集合版约 0.002 秒（每次 in 平均 $O(1)$），差两个数量级。
"""

import time

n = 20000
data = []
for i in range(n):
    data.append(i % 5000)

# ══ 列表版 ════════════════════════════════════════════════
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

# ══ 集合版（只换容器、改一行 append）══════════════════════
seen_set = set()
dup_set = 0
t0 = time.perf_counter()
for x in data:
    if x in seen_set:
        dup_set += 1
    else:
        seen_set.add(x)
t1 = time.perf_counter()
t_set_dedup = t1 - t0
distinct_set = len(seen_set)

same = False
if dup_list == dup_set:
    if distinct_list == distinct_set:
        same = True

print('列表版 不同元素', distinct_list, '重复', dup_list, f'{t_list_dedup:.6f}', '秒')
print('集合版 不同元素', distinct_set, '重复', dup_set, f'{t_set_dedup:.6f}', '秒')
print('结果一致', same)
