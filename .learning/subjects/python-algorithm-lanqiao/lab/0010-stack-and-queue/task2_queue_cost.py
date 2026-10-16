"""任务 2 · 两种出队的代价：list.pop(0) 与 deque.popleft()

第 3 课量过一次「同一个队列操作在两个容器上差多少」，这一课要把它与两个结构
放在一起看：队列的容器为什么定在 deque 上，而不是「列表也能用，先用着」。

出队 20 万次，两种写法各量一次：

    · 用列表当队列：每次出队写 lst.pop(0)。列表的元素连续存放，删掉第一个之后
      后面的元素全都要往前挪一格，这是第 3 课价格表里的 O(n)；出 n 次就是 O(n²)。
    · 用 deque 当队列：每次出队写 dq.popleft()。deque 两端进出都是 O(1)，
      出 n 次仍是 O(n)。

这一份比的是**量级**，不是背下来的常数：换台机器绝对值会变，
但「popleft 比 pop(0) 快 20 倍以上」这一条不变。

接口：文件名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的两段（每段就是那一个出队循环）。

跑： py task2_queue_cost.py
判： py run_tests.py
"""

import time
from collections import deque
from tools import show_count, show_time, ratio_hint

N = 200000                                     # 别改：出队次数

# ── 给好的部分：两份数据（别改）─────────────────────────────
lst = list(range(N))                           # 别改
dq = deque(range(N))                           # 别改


# ══ TODO 1 ═════════════════════════════════════════════════
# 用列表当队列，出队 N 次：循环里写 lst.pop(0)，把取出来的数累加进 total_list。
#   计时由外面那两行 t0 / t1 管，你只写中间那个循环。
#   要点：一定要写 lst.pop(0)（从**左端**取），不是 lst.pop()。
t0 = time.perf_counter()                       # 别改：计时开始
total_list = 0                                 # 别改
# TODO 1（这一行只是占位，把它换成那个出队循环）
t1 = time.perf_counter()                       # 别改：计时结束


# ══ TODO 2 ═════════════════════════════════════════════════
# 用 deque 当队列，出队同样的 N 次：循环里写 dq.popleft()，累加进 total_deque。
#   要点：方法名是 popleft，不是 pop；写成 pop() 就是从右端取，顺序反了、
#   而且两个 total 对不上。
t2 = time.perf_counter()                       # 别改：计时开始
total_deque = 0                                # 别改
# TODO 2（这一行只是占位，把它换成那个出队循环）
t3 = time.perf_counter()                       # 别改：计时结束


# ── 打印对照（这几行别改，自动判分按它们读结果）─────────────
list_seconds = t1 - t0                         # 别改
deque_seconds = t3 - t2                        # 别改

print('pop(0)  出队', N, '次', f'{list_seconds:.6f}', '秒')        # 别改
print('popleft 出队', N, '次', f'{deque_seconds:.6f}', '秒')       # 别改
print('两种写法的出队顺序一致', total_list == total_deque)          # 别改：期望 True
print('两种写法取完的元素个数', N - len(lst), N - len(dq))          # 别改：期望 200000 200000
print('deque 比列表快', f'{round(list_seconds / max(deque_seconds, 1e-9), 1)}', '倍')   # 别改

show_time(1, 'pop(0) ', 'k=' + str(N), list_seconds)               # 别改
show_time(2, 'popleft', 'k=' + str(N), deque_seconds)              # 别改
ratio_hint(3, 'deque 比列表快', deque_seconds, list_seconds)        # 别改
show_count(1, '两种写法出队个数一致', total_list == total_deque)     # 别改
