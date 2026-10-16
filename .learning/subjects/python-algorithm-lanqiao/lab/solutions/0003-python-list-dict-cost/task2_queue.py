"""任务 2 · pop(0) 与 popleft 的对照（参考解）

要看的趋势：两者出的元素完全一样（都是先进先出），代价却差两个数量级——
pop(0) 每次要把后面 n-1 个元素往左挪一格（$O(n)$，出 n 个就是 $O(n^2)$），
popleft() 只是挪一下队头指针（$O(1)$）。
本机实测（非通用值）：pop(0) 20 万次约 2.74 秒、popleft 约 0.013 秒，差约 200 倍。
"""

import time
import collections

count = 200000

q = []
for i in range(count):
    q.append(i)

head_list = []
t0 = time.perf_counter()
for i in range(count):
    x = q.pop(0)
    if i < 5:
        head_list.append(x)
t1 = time.perf_counter()
t_pop0 = t1 - t0

dq = collections.deque()
for i in range(count):
    dq.append(i)

head_deque = []
t0 = time.perf_counter()
for i in range(count):
    x = dq.popleft()
    if i < 5:
        head_deque.append(x)
t1 = time.perf_counter()
t_popleft = t1 - t0

same = False
if len(head_list) == 5:
    if len(head_deque) == 5:
        same = True
        for i in range(5):
            if head_list[i] != head_deque[i]:
                same = False

print('pop(0)', count, '次', f'{t_pop0:.6f}', '秒')
print('popleft', count, '次', f'{t_popleft:.6f}', '秒')
print('出队顺序一致', same)
