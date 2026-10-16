"""任务 2 · 两种队列的代价对照（留白版）

目标：同样出队 20 万次，一次用列表的 pop(0)，一次用 deque 的 popleft，
      量出两次耗时，并证明两种写法的出队顺序一致（队列是先进先出）。

跑： py task2_queue.py
判： py run_tests.py
"""

import time
import collections

count = 200000

# ══ 第 1 步：用列表当队列，出队 count 次 ═══════════════════
q = []
for i in range(count):
    q.append(i)

# TODO 1：量下面这段出队的耗时（结果存进 t_pop0，前 5 个出队元素存进 head_list）
#   t0 = time.perf_counter()
#   for i in range(count):
#       x = q.pop(0)
#       if i < 5:
#           head_list.append(x)
#   t1 = time.perf_counter()
# 提示：t0 取在循环之前、t1 取在循环之后，中间不要夹别的代码
head_list = []
t_pop0 = 0.0

# ══ 第 2 步：换成 deque，再出队 count 次 ═══════════════════
# TODO 2：dq = collections.deque()，用 for 循环把 0..count-1 用 append 放进去
# TODO 3：照 TODO 1 的形状再量一次，把出队方法换成 popleft，
#         耗时存进 t_popleft，前 5 个出队元素存进 head_deque
head_deque = []
t_popleft = 0.0

# ── 检查两种写法的出队顺序是否一致（别改）──────────────────
same = False
if len(head_list) == 5:
    if len(head_deque) == 5:
        same = True
        for i in range(5):
            if head_list[i] != head_deque[i]:
                same = False

# ── 打印（这三行别改）──────────────────────────────────────
print('pop(0)', count, '次', f'{t_pop0:.6f}', '秒')
print('popleft', count, '次', f'{t_popleft:.6f}', '秒')
print('出队顺序一致', same)
