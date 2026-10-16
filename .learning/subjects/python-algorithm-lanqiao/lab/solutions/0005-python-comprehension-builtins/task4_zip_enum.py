"""任务 4 · 把下标循环换成 enumerate 与 zip（参考解）

下标版在三个地方写同一个下标（i、names[i]、scores[i]），换成这两个函数后每处只剩一次：
  · enumerate(a, start=1)：位置与值一次取出，计数从 1 起（默认从 0 起）；
  · zip(a, b)：两个序列一一配对，在最短的那个用完时就停（长度不齐不报错，只会悄悄变短）；
  · 想单独取配对里的某一列，用 [score for _, score in zip(...)]；
  · 转置矩阵：把每一行当成一个参数交给 zip，它按位置把同列的元素配成一组。

跑： py task4_zip_enum.py
判： py run_tests.py
"""

names = ['第一题', '第二题', '第三题']                        # 别改
scores = [80, 95, 60]                                      # 别改
matrix = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]      # 别改

# 01 下标版：for i in range(len(names)): print('01 编号', i, names[i], scores[i])
#    要的是「编号从 1 起」，所以 enumerate 要带上 start=1
for i, (name, score) in enumerate(zip(names, scores), start=1):
    print('01 编号', i, name, score)        # 别改：期望 1 第一题 80 / 2 第二题 95 / 3 第三题 60

enum_list = list(enumerate(names, start=1))
print('02 enumerate 表', enum_list)          # 别改：期望 [(1, '第一题'), (2, '第二题'), (3, '第三题')]

cut_len = len(list(zip(names, scores[:2])))
print('03 zip 截断长度', cut_len)             # 别改：期望 2（zip 在短的那个用完时就停）

cut_pairs = list(zip(names, scores[:2]))
print('04 zip 截断表', cut_pairs)             # 别改：期望 [('第一题', 80), ('第二题', 95)]

score_col = [score for _, score in zip(names, scores)]
print('05 分数列', score_col)                 # 别改：期望 [80, 95, 60]

pairs = list(zip(names, scores))
print('06 配对表', pairs)                     # 别改：期望 [('第一题', 80), ('第二题', 95), ('第三题', 60)]

# 07 下标版是两层循环：for i in range(4): 里面再 for row in matrix: col.append(row[i])
transposed = [list(col) for col in zip(matrix[0], matrix[1], matrix[2])]
print('07 转置', transposed)                  # 别改：期望 [[1, 5, 9], [2, 6, 10], [3, 7, 11], [4, 8, 12]]
