"""任务 2 · 两种出队的代价（参考解）"""

import time
from collections import deque
from tools import show_count, show_time, ratio_hint

N = 200000

lst = list(range(N))
dq = deque(range(N))

t0 = time.perf_counter()
total_list = 0
for _ in range(N):
    total_list += lst.pop(0)
t1 = time.perf_counter()

t2 = time.perf_counter()
total_deque = 0
for _ in range(N):
    total_deque += dq.popleft()
t3 = time.perf_counter()

list_seconds = t1 - t0
deque_seconds = t3 - t2

print('pop(0)  出队', N, '次', f'{list_seconds:.6f}', '秒')
print('popleft 出队', N, '次', f'{deque_seconds:.6f}', '秒')
print('两种写法的出队顺序一致', total_list == total_deque)
print('两种写法取完的元素个数', N - len(lst), N - len(dq))
print('deque 比列表快', f'{round(list_seconds / max(deque_seconds, 1e-9), 1)}', '倍')

show_time(1, 'pop(0) ', 'k=' + str(N), list_seconds)
show_time(2, 'popleft', 'k=' + str(N), deque_seconds)
ratio_hint(3, 'deque 比列表快', deque_seconds, list_seconds)
show_count(1, '两种写法出队个数一致', total_list == total_deque)
