"""任务 5 · sorted 的 key 与 list.sort 的返回值（参考解）

  · sorted(可迭代对象) 返回一个新表，原数据不动；
  · key= 指定「按什么比」：键函数是一元函数，每条记录只调用一次；
  · 元组按字典式顺序比：先比第一项，相同再比第二项 —— 这就是第二关键字的写法；
  · list.sort() 原地改，并且返回 None（写成 x = a.sort() 拿到的是 None）；
  · 排序是稳定的：等键记录保持原始顺序。

跑： py task5_sort.py
判： py run_tests.py
"""

records = [('A03', 80), ('A01', 95), ('A02', 80), ('A04', 95)]     # 别改
snapshot = [('A03', 80), ('A01', 95), ('A02', 80), ('A04', 95)]    # 别改：原始顺序的快照


def rank_key(rec):
    """分数降序（第一项取负号）、同分编号升序。"""
    return (-rec[1], rec[0])


board = sorted(records, key=rank_key)
print('01 排行榜', board)                 # 别改：期望 [('A01', 95), ('A04', 95), ('A02', 80), ('A03', 80)]
print('02 原记录没动', records == snapshot)  # 别改：期望 True（sorted 返回新表）

scores = [88, 95, 70]                     # 别改
ranked = sorted(scores, reverse=True)
print('03 sorted 新表', ranked)            # 别改：期望 [95, 88, 70]
print('04 原分数没动', scores)              # 别改：期望 [88, 95, 70]

trap = [88, 95, 70]                       # 别改
none_value = trap.sort()                  # 原地改 trap，交回来的东西是 None
print('05 sort 的返回值是 None', none_value is None)   # 别改：期望 True
print('06 被 sort 改过的原表', trap)        # 别改：期望 [70, 88, 95]

key_calls = 0                             # 别改


def count_key(rec):
    """会数自己被调用几次的键函数（别改）。"""
    global key_calls
    key_calls += 1
    return rec[1]


by_score = sorted(records, key=count_key)
print('07 按分数升序', by_score)            # 别改：期望 [('A03', 80), ('A02', 80), ('A01', 95), ('A04', 95)]
print('08 取键次数', key_calls)             # 别改：期望 4（四条记录，每条只取一次键）
