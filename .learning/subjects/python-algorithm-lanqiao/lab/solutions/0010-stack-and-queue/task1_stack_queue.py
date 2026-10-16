"""任务 1 · 用列表写栈，用 deque 写队列（参考解）"""

from collections import deque
from tools import make_perm, shuffle, show_count


class Stack:
    def __init__(self):
        self._data = []

    def push(self, x):
        self._data.append(x)

    def pop(self):
        return self._data.pop()

    def top(self):
        return self._data[-1]

    def is_empty(self):
        return not self._data


class Queue:
    def __init__(self):
        self._data = deque()

    def enqueue(self, x):
        self._data.append(x)

    def dequeue(self):
        return self._data.popleft()

    def front(self):
        return self._data[0]

    def is_empty(self):
        return not self._data


if __name__ == '__main__':
    order = make_perm(30)
    st = Stack()
    for x in order:
        st.push(x)
    stack_out = []
    while not st.is_empty():
        stack_out.append(st.pop())

    model = []
    for x in order:
        model.append(x)
    model_out = []
    while model:
        model_out.append(model.pop())

    print('栈 入栈顺序', order)
    print('栈 出栈顺序', stack_out)
    print('栈 与参照模型一致', stack_out == model_out)
    print('栈 出栈是入栈的反序', stack_out == list(reversed(order)))
    show_count(1, '栈 出栈', len(stack_out))

    empty_stack = Stack()
    try:
        empty_stack.pop()
        print('空栈 pop 报错类型 没有报错')
    except IndexError as exc:
        print('空栈 pop 报错类型 IndexError:', exc)

    q = Queue()
    for x in order:
        q.enqueue(x)
    queue_out = []
    while not q.is_empty():
        queue_out.append(q.dequeue())
    print('队列 与入队顺序相同', queue_out == order)
    print('队列 出队与前 4 个', queue_out[:4])

    ops = shuffle(424242, 300)
    st2 = Stack()
    q2 = Queue()
    st_model = []
    q_model = []
    stack_rows = []
    queue_rows = []
    for i in range(len(ops)):
        if i % 2 == 0:
            st2.push(i)
            st_model.append(i)
            stack_rows.append((st_model[-1], st2.top()))
        else:
            q2.enqueue(i)
            q_model.append(i)
            queue_rows.append((q_model[0], q2.front()))

    stack_steps_ok = True
    for a, b in stack_rows:
        if a != b:
            stack_steps_ok = False
    queue_steps_ok = True
    for a, b in queue_rows:
        if a != b:
            queue_steps_ok = False

    print('随机 300 步 栈顶与模型一致', stack_steps_ok)
    print('随机 300 步 队头与模型一致', queue_steps_ok)

    out1 = []
    while not st2.is_empty():
        out1.append(st2.pop())
    out2 = []
    while not q2.is_empty():
        out2.append(q2.dequeue())
    print('随机 300 步 出栈顺序与模型一致', out1 == list(reversed(st_model)))
    print('随机 300 步 出队顺序与模型一致', out2 == q_model)

    show_count(2, '栈 随机步数', len(stack_rows))
    show_count(3, '队列 随机步数', len(queue_rows))
