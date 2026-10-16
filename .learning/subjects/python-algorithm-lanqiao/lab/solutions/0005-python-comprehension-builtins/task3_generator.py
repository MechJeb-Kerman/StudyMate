"""任务 3 · 生成器表达式：什么时候算、能不能反复用（参考解）

方括号换成圆括号就是生成器表达式：结果一样，但算的时机不一样。
这一份用「会数自己被调用几次」的函数把两件事变成看得见的数字：
  ① 惰性：生成器写出来时一个都还没算（计数为 0），要一个才算一个；
  ② 只能走一遍：第一次取完，第二次要就什么都没有了（计数也不再涨）；
  ③ 表能反复用：列表推导式是建表时就把元素全算好，之后想用几次用几次；
  ④ any / all 能确定结果就不再往下取（短路）；
  ⑤ map 交回来的也是迭代器，同样只能用一次。

跑： py task3_generator.py
判： py run_tests.py
"""

calls = 0                                  # 别改：下面用它数 slow_square 被调用了几次


def slow_square(x):
    """算 x 的平方，并把「被调用了一次」记进 calls。"""
    global calls
    calls += 1
    return x * x


calls = 0                                  # 别改
gen = (slow_square(x) for x in range(6))
print('01 建好之后 calls', calls)           # 别改：期望 0（一个都还没算）
print('02 第一次 sum', sum(gen))            # 别改：期望 55
print('03 第一次 sum 之后 calls', calls)     # 别改：期望 6（取到空了，算了 6 个）
print('04 第二次 sum', sum(gen))            # 别改：期望 0（已经空了）
print('05 第二次 sum 之后 calls', calls)     # 别改：期望 6（没有重新算）

calls = 0                                  # 别改
lst = [slow_square(x) for x in range(6)]
print('06 建表之后 calls', calls)           # 别改：期望 6（建表时全算好了）
print('07 表能反复用', sum(lst), sum(lst))   # 别改：期望 55 55

calls = 0                                  # 别改
has_big = any(slow_square(x) > 3 for x in range(6))
print('08 any 提前停 calls', calls)         # 别改：期望 3（0、1 都不满足，到 4 就定了）
print('09 any 的值', has_big)               # 别改：期望 True

calls = 0                                  # 别改
all_small = all(slow_square(x) < 5 for x in range(6))
print('10 all 提前停 calls', calls)         # 别改：期望 4（到 9 出现反例就定了）
print('11 all 的值', all_small)             # 别改：期望 False

data_str = ['3', '-1', '4']                # 别改
m = map(int, data_str)
print('12 map 第一次', list(m))             # 别改：期望 [3, -1, 4]
print('13 map 第二次', list(m))             # 别改：期望 []（迭代器取完就空）


def squares_gen(n):
    """交回一个生成器表达式（给判分脚本用，别改）。"""
    return (x * x for x in range(n))
