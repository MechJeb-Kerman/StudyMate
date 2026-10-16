"""基准 · 十段循环（给好的，别改）

这十段都是题解里最常见的那种写法：先建一个空容器，再写一层 for，再往里 append；
判定与统计则先设一个旗子或计数器，循环里改它。每一段后面都跟着一句 print ——
那行 print 是判分接口，run_tests.py 按它读结果、与 task1_rewrite.py 逐行比对。

这一份是判分的标准来源（就像第 4 课实验里的 flat_odd.py）：**别改它**。
要写的是 task1_rewrite.py。

跑： py loops_original.py
"""

data = [3, -1, 4, 0, 7, 2]
words = ['pear', 'fig', 'apple']
data_str = ['3', '-1', '4']
records = [('A03', 80), ('A01', 95), ('A02', 80), ('A04', 95)]

# 01 平方：建空表，循环里 append(x ** 2)
sq = []
for x in data:
    sq.append(x ** 2)
print('01 平方', sq)

# 02 筛选：只要正的
kept = []
for x in data:
    if x > 0:
        kept.append(x)
print('02 正数', kept)

# 03 求和：从 0 开始一个一个加上去
total = 0
for x in data:
    total += x
print('03 总和', total)

# 04 求最大：先拿第一个当擂主，再逐个比
best = data[0]
for x in data:
    if x > best:
        best = x
print('04 最大', best)

# 05 计数：数有几个正的
pos_count = 0
for x in data:
    if x > 0:
        pos_count += 1
print('05 正数个数', pos_count)

# 06 判定「存在」：有没有大于 5 的
has_big = False
for x in data:
    if x > 5:
        has_big = True
print('06 有大于5', has_big)

# 07 判定「全部」：是不是全部非负
all_nonneg = True
for x in data:
    if x < 0:
        all_nonneg = False
print('07 全部非负', all_nonneg)

# 08 每个词的长度
lens = []
for w in words:
    lens.append(len(w))
print('08 词长', lens)

# 09 一串字符串转成整数
nums = []
for s in data_str:
    nums.append(int(s))
print('09 转整数', nums)

# 10 排行榜：分数从高到低；分数相同的按编号从小到大。
#    循环版只能自己一个个插：从头找第一个「该排在它后面」的位置，插进去。
board = []
for rec in records:
    pos = len(board)
    for i in range(len(board)):
        if board[i][1] < rec[1] or (board[i][1] == rec[1] and board[i][0] > rec[0]):
            pos = i
            break
    board.insert(pos, rec)
print('10 排行榜', board)
