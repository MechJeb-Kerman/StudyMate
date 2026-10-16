"""任务 1 · 用列表写栈，用 deque 写队列

这一课的两条线性结构，先把它们各写一遍。

    栈（stack）—— 只允许在同一端插入和删除：后进先出（LIFO）。
                   用列表实现：append 进栈、不带参数的 pop 出栈、st[-1] 看栈顶。

    队列（queue）—— 一端插入、另一端删除：先进先出（FIFO）。
                    用 collections.deque 实现：append 进队、popleft 出队、q[0] 看队头。

四条判空都写 `not data` 或 `len(data) == 0` 都行，这一课统一用 `not data`。

判分要看的不只是「结果对不对」，而是**你的结构与参照模型在每一步都一致**：
下面那段 300 次随机操作里，每做一步就把模型的结果与你的结果写成一行，
两列必须一直一样。有一条不一样，说明某一次操作的顺序或取值错了。

接口：文件名、函数名、类名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的两段。

跑： py task1_stack_queue.py
判： py run_tests.py
"""

from collections import deque
from tools import make_perm, shuffle, show_count


# ══ TODO 1 ═════════════════════════════════════════════════
# 补 Stack 类的四个方法：push / pop / top / is_empty。
#   self._data 是那个列表（在 __init__ 里建好的，别改成别的名字）。
#   push(x)：把 x 追加到末尾；
#   pop()  ：把末尾那一个**取出来并交回**（这一句是整段的核心）；
#   top()  ：只看末尾那一个，不取出来；
#   is_empty()：栈里一个元素都没有时为 True。
#
# 写错时最常见的两种症状：
#   · pop() 里写成 self._data.pop() 却忘了 return —— 交回的是 None；
#   · pop() 里写成 self._data.pop(0) —— 那是从**另一头**取，顺序就反了。
class Stack:
    def __init__(self):
        self._data = []

    def push(self, x):
        # TODO 1（这一行只是占位，把它换成真的入栈）
        pass

    def pop(self):
        # TODO 1（这一行只是占位，把它换成真的出栈，并交回取出来的那个元素）
        return None

    def top(self):
        # TODO 1
        return None

    def is_empty(self):
        # TODO 1
        return True


# ══ TODO 2 ═════════════════════════════════════════════════
# 补 Queue 类的四个方法：enqueue / dequeue / front / is_empty。
#   self._data 是那个 deque（在 __init__ 里建好的，别改成列表）。
#   enqueue(x)：把 x 追加到右端；
#   dequeue() ：从左端取出并交回（deque 的方法名叫 popleft，不是 pop）；
#   front()   ：只看左端那一个（下标 0），不取出来；
#   is_empty()：队列里一个元素都没有时为 True。
#
# 症状对照：dequeue() 里写成 self._data.pop() 交回的是**最后进来的**那个，
# 队列就成了栈——判分那一段「入队顺序」与「参照模型」会立刻不一样。
class Queue:
    def __init__(self):
        self._data = deque()

    def enqueue(self, x):
        # TODO 2
        pass

    def dequeue(self):
        # TODO 2
        return None

    def front(self):
        # TODO 2
        return None

    def is_empty(self):
        # TODO 2
        return True


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声
    # ── 一、栈：进去与出来的顺序 ────────────────────────────────
    order = make_perm(30)                      # 别改：0..29 的一个固定排列
    st = Stack()                               # 别改
    for x in order:                            # 别改
        st.push(x)
    stack_out = []                             # 别改
    while not st.is_empty():                   # 别改
        stack_out.append(st.pop())

    model = []                                 # 别改：参照模型：同一个列表上 append 与 pop
    for x in order:                            # 别改
        model.append(x)
    model_out = []                             # 别改
    while model:                               # 别改
        model_out.append(model.pop())

    print('栈 入栈顺序', order)                                          # 别改
    print('栈 出栈顺序', stack_out)                                       # 别改
    print('栈 与参照模型一致', stack_out == model_out)                     # 别改：期望 True
    print('栈 出栈是入栈的反序', stack_out == list(reversed(order)))        # 别改：期望 True
    show_count(1, '栈 出栈', len(stack_out))                              # 别改

    # 空栈上取元素会怎样：这一段是给好的（判分接口），只打出报错的类型，别改
    empty_stack = Stack()                      # 别改
    try:
        empty_stack.pop()
        print('空栈 pop 报错类型 没有报错')       # 别改
    except IndexError as exc:
        print('空栈 pop 报错类型 IndexError:', exc)   # 别改

    # ── 二、队列：进去与出来的顺序 ──────────────────────────────
    q = Queue()                                # 别改
    for x in order:                            # 别改
        q.enqueue(x)
    queue_out = []                             # 别改
    while not q.is_empty():                    # 别改
        queue_out.append(q.dequeue())
    print('队列 与入队顺序相同', queue_out == order)                       # 别改：期望 True
    print('队列 出队与前 4 个', queue_out[:4])                            # 别改

    # ── 三、300 次固定随机操作：每一步都要与参照模型对上 ─────────
    ops = shuffle(424242, 300)                 # 别改：300 个固定顺序的数，每次运行都一样
    st2 = Stack()                              # 别改
    q2 = Queue()                               # 别改
    st_model = []                              # 别改
    q_model = []                               # 别改
    stack_rows = []                            # 别改
    queue_rows = []                            # 别改
    for i in range(len(ops)):                  # 别改
        if i % 2 == 0:                         # 别改：偶数步做栈，奇数步做队列
            st2.push(i)
            st_model.append(i)
            stack_rows.append((st_model[-1], st2.top()))        # 别改
        else:
            q2.enqueue(i)
            q_model.append(i)
            queue_rows.append((q_model[0], q2.front()))         # 别改

    stack_steps_ok = True                      # 别改
    for a, b in stack_rows:                    # 别改
        if a != b:
            stack_steps_ok = False
    queue_steps_ok = True                      # 别改
    for a, b in queue_rows:                    # 别改
        if a != b:
            queue_steps_ok = False

    print('随机 300 步 栈顶与模型一致', stack_steps_ok)                    # 别改：期望 True
    print('随机 300 步 队头与模型一致', queue_steps_ok)                    # 别改：期望 True

    out1 = []                                  # 别改
    while not st2.is_empty():                  # 别改
        out1.append(st2.pop())
    out2 = []                                  # 别改
    while not q2.is_empty():                   # 别改
        out2.append(q2.dequeue())
    print('随机 300 步 出栈顺序与模型一致', out1 == list(reversed(st_model)))   # 别改：期望 True
    print('随机 300 步 出队顺序与模型一致', out2 == q_model)                   # 别改：期望 True

    show_count(2, '栈 随机步数', len(stack_rows))                          # 别改
    show_count(3, '队列 随机步数', len(queue_rows))                        # 别改
