"""任务 3 参考解 · 故意用全局变量在函数之间传状态

数据不靠参数与 return：read_n 把结果写进 n_global，
odd_count 从 n_global 读、把答案写进 count_global，show 打印 count_global。

对照点：看 read_n 的定义那一行，看不出它动了 n_global；
调用处必须知道「要先调 read_n」这个隐式顺序。这就是它难查的原因。
"""

n_global = 0
count_global = 0


def read_n():
    global n_global             # 不写这一行，n_global 就成了局部名字
    n_global = int(input())
    if n_global < 0:
        n_global = 0


def odd_count():
    global count_global
    count_global = (n_global + 1) // 2


def show():
    print(count_global)


# ── 入口 ───────────────────────────────────────────────────
read_n()
odd_count()
show()
print('函数外读到全局 n_global', n_global)
print('函数外读到全局 count_global', count_global)
