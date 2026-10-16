"""任务 2 · 带条件与嵌套的推导式（参考解）

四件事：
  ① 两个 if 子句：连着写两个 if，等价于循环版里连着写两个 if（是「与」）；
  ② 两个 for 子句：把嵌套的列表展平，for 与 if 的先后与循环版从上到下一致；
  ③ 推导式里再嵌推导式：转置一个矩阵；
  ④ 目标名不泄漏：推导式的目标名只活在它内部，不会盖掉外面的同名变量。

跑： py task2_nested.py
判： py run_tests.py
"""

matrix = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]     # 别改
vec = [[1, 2, 3], [4, 5, 6]]                              # 别改

# ① 循环版：for x in range(10): if x % 2 == 0: if x > 4: kept.append(x)
two_cond = [x for x in range(10) if x % 2 == 0 if x > 4]
print('01 两个条件', two_cond)             # 别改：期望 [6, 8]

# ② 循环版：for elem in vec: for num in elem: flat.append(num)
flat = [num for elem in vec for num in elem]
print('02 展平', flat)                     # 别改：期望 [1, 2, 3, 4, 5, 6]

# ③ 循环版：for i in range(4): 里面再 for row in matrix: 取 row[i]
transposed = [[row[i] for row in matrix] for i in range(4)]
print('03 转置', transposed)                # 别改：期望 [[1, 5, 9], [2, 6, 10], [3, 7, 11], [4, 8, 12]]

# ④ 先给 y 一个旧值，再用推导式（而不是循环）建平方表
y = '旧值'                                 # 别改
squares_y = [y ** 2 for y in range(4)]
print('04 平方表', squares_y)               # 别改：期望 [0, 1, 4, 9]
print('05 推导式外 y', y)                   # 别改：期望 旧值

# 给好的对照：循环版的目标名会留在外面
for y in range(4):
    pass
print('06 循环外 y', y)                     # 别改：期望 3
