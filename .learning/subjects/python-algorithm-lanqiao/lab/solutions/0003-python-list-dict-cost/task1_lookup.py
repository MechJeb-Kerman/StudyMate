"""任务 1 · 三种查法的耗时对照（参考解）

要看的趋势：列表 in 要一个个比过去（这 200 个目标都在末尾附近，每次几乎扫完整个列表），
集合与字典走哈希直接落位，所以后两行的数字小得几乎看不见。
本机实测（Python 3.14 free-threading，非通用值）：列表约 1.5 秒、集合约 0.000018 秒、
字典约 0.000016 秒——差约 5 个数量级。
"""

import time

n = 1000000
lookup = 200

lst = []
for i in range(n):
    lst.append(i)
s = set()
for i in range(n):
    s.add(i)
d = {}
for i in range(n):
    d[i] = i

targets = []
for i in range(n - lookup, n):
    targets.append(i)

t0 = time.perf_counter()
for x in targets:
    y = x in lst
t1 = time.perf_counter()
t_list = t1 - t0

t0 = time.perf_counter()
for x in targets:
    y = x in s
t1 = time.perf_counter()
t_set = t1 - t0

t0 = time.perf_counter()
for x in targets:
    y = x in d
t1 = time.perf_counter()
t_dict = t1 - t0

print('列表 in', f'{t_list:.6f}', '秒')
print('集合 in', f'{t_set:.6f}', '秒')
print('字典查', f'{t_dict:.6f}', '秒')
