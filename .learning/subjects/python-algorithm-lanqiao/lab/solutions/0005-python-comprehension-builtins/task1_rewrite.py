"""任务 1 · 十段循环，逐段改写成一行（参考解）

循环版在同目录的 loops_original.py 里（给好的基准，别改）。这里把十段各压成一行：
能写推导式的写推导式，能换现成函数的换现成函数，十行输出必须与基准逐字一致。

跑： py task1_rewrite.py
判： py run_tests.py
"""

data = [3, -1, 4, 0, 7, 2]                                         # 别改
words = ['pear', 'fig', 'apple']                                   # 别改
data_str = ['3', '-1', '4']                                        # 别改
records = [('A03', 80), ('A01', 95), ('A02', 80), ('A04', 95)]     # 别改

# 01 平方：循环版「建空表 + append(x ** 2)」→ 一句描述
sq = [x ** 2 for x in data]
print('01 平方', sq)                     # 别改：期望 [9, 1, 16, 0, 49, 4]

# 02 筛选：条件写在方括号的最后，可以连着写两个 if
kept = [x for x in data if x > 0]
print('02 正数', kept)                    # 别改：期望 [3, 4, 7, 2]

# 03 求和：现成的求和函数收一个可迭代对象
total = sum(data)
print('03 总和', total)                   # 别改：期望 15

# 04 求最大：擂主那套循环换成一个函数
best = max(data)
print('04 最大', best)                    # 别改：期望 7

# 05 计数：读作「每个满足条件的元素算作 1，把它们加起来」——
#    喂给它的是生成器表达式，不建表
pos_count = sum(1 for x in data if x > 0)
print('05 正数个数', pos_count)            # 别改：期望 4

# 06 判定「存在」：只要有任意一个满足就为真
has_big = any(x > 5 for x in data)
print('06 有大于5', has_big)              # 别改：期望 True

# 07 判定「全部」：要一个反例都没有才为真
all_nonneg = all(x >= 0 for x in data)
print('07 全部非负', all_nonneg)           # 别改：期望 False

# 08 词长：表达式写「算出什么」
lens = [len(w) for w in words]
print('08 词长', lens)                    # 别改：期望 [4, 3, 5]

# 09 转整数：转换用的函数（int）已经有现成的，把它交给 map，
#    再用 list 把迭代器收成一张表
nums = list(map(int, data_str))
print('09 转整数', nums)                  # 别改：期望 [3, -1, 4]

# 10 排行榜：分数降序 + 同分编号升序。
#     元组按字典式顺序比：先比第一项，不相等就定了；分数要降序，所以第一项取负号；
#     同分再比编号，编号放第二项。
def rank_key(rec):
    return (-rec[1], rec[0])


board = sorted(records, key=rank_key)
print('10 排行榜', board)                 # 别改：期望 [('A01', 95), ('A04', 95), ('A02', 80), ('A03', 80)]
