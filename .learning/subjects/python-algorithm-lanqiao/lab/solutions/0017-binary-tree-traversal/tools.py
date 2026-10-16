"""tools.py · lab 0017 的公共工具（给好的，别改）

这里放五样东西，四个任务都从这里取：

  1. node(v, l=None, r=None)
     这一课的表示约定：一个结点写成 [值, 左子树, 右子树]，空树写 None。
     与课件「用嵌套列表表示树」那一节逐字相同。四个任务都用它搭树，
     任务 3 自己写的 build_chain / build_balanced 也用它。

  2. show_count(index, label, value) / show_time(index, label, extra, seconds)
     打印固定格式的计数行与耗时行，判分按行读它们。
     格式： 计数 NN <label> <value>
             耗时 NN <label> <n=…> <秒数> 秒
     例：   计数 01 示例树 前序 6
             耗时 01 链状树 拼接 n=200 0.000054 秒

  3. show_label(label, value) / show_pair(label, first, second)
     打印一行普通结果、或一行「一个标签带两个值」的结果。
     任务 2 的表格与任务 3 的三种规模都靠这两行给出判分要读的东西。
     例：   示例树 后序 ['D', 'E', 'B', 'F', 'C', 'A']
             链状 n=  100 树高   100  递归再深一层 998 跑得动

  4. show_recursion_error(index, label)
     专门打印任务 3 那种「递归撞上限」的行。
     例：   计数 02 链状 爆栈长度 999

  5. timed(func, *args)
     跑一次并量耗时 → (函数交回的值, 秒数)。计时口径与第 3 课一致：
     前后各取一次 perf_counter、相减，中间不夹别的代码。

这一课的四样东西（四种遍历、四个递归汇总函数、形状与递归深度、拼接与累加器）
与这份工具是配套的：留白版原样跑时，所有计数都会打出 0、耗时都会打出 0.000000、
树高那几行打出 0——那是起点，不是 bug。
"""

import time

# ── 表示约定：嵌套列表 ──────────────────────────────────────────────────


def node(v, l=None, r=None):
    """搭一个结点：[值, 左子树, 右子树]。空树用 None，不调用这个函数。"""
    return [v, l, r]


# ── 打印：格式就是判分接口 ──────────────────────────────────────────────


def show_count(index, label, value):
    """打印一行计数。index 是两位编号，label 是中文标签。"""
    print('计数 ' + str(index).zfill(2) + ' ' + label + ' ' + str(value))


def show_time(index, label, extra, seconds):
    """打印一行耗时（六位小数）。extra 是规模标签，例如 'n=200'。"""
    print('耗时 ' + str(index).zfill(2) + ' ' + label + ' ' + str(extra)
          + ' ' + f'{seconds:.6f}' + ' 秒')


def show_label(label, value):
    """打印一行普通结果：<label> <value>。"""
    print(str(label) + ' ' + str(value))


def show_pair(label, first, second):
    """打印一行「一个标签带两个值」：<label> <first> <second>。"""
    print(str(label) + ' ' + str(first) + ' ' + str(second))


def show_recursion_error(index, label, value=0):
    """打印一行「递归撞上限」的计数：<label> <value> 已爆栈。

    任务 3 用它把「链状树加到多长就爆栈」写成一行判分能读的数字。
    """
    print('计数 ' + str(index).zfill(2) + ' ' + label + ' ' + str(value) + ' 已爆栈')


# ── 计时 ────────────────────────────────────────────────────────────────


def timed(func, *args):
    """跑一次并量耗时 → (函数交回的值, 秒数)。

    计时口径与第 3 课一致：前后各取一次 perf_counter、相减，
    中间不夹别的代码。
    """
    start = time.perf_counter()
    value = func(*args)
    end = time.perf_counter()
    return value, end - start
