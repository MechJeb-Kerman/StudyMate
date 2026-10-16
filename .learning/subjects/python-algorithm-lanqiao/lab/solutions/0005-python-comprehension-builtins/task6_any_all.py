"""任务 6 · any 与 all：判定循环的两种换法（参考解）

  · any(可迭代对象)：有任意一个元素为真就是 True；空序列是 False（一个满足的都没有）；
  · all(可迭代对象)：所有元素都为真才是 True；空序列也算 True（一个反例也没有）；
  · 两个默认答案相反，所以用 all 检查「这批数据是不是都合法」时，空数据也会给 True ——
    判空前先判空（if not nums:）；
  · 它们能确定结果就不再往下取值（短路），所以能提前停。

跑： py task6_any_all.py
判： py run_tests.py
"""

data = [3, -1, 4, 0, 7]                   # 别改
empty = []                                # 别改

# 01 循环版：found = False; for x in data: if x > 0: found = True
has_pos = any(x > 0 for x in data)
print('01 有正数', has_pos)                # 别改：期望 True

# 02 循环版：ok = True; for x in data: if x < 0: ok = False
all_pos = all(x > 0 for x in data)
print('02 全部为正', all_pos)               # 别改：期望 False（0 不是正数）

empty_any = any(x > 0 for x in empty)
print('03 空数据 any', empty_any)           # 别改：期望 False

empty_all = all(x > 0 for x in empty)
print('04 空数据 all', empty_all)           # 别改：期望 True


def all_valid(nums):
    """这批数据是不是都大于 0（不判空的那一版）。"""
    return all(x > 0 for x in nums)


def all_valid_nonempty(nums):
    """空数据先交回 False，再用 all。"""
    if not nums:
        return False
    return all(x > 0 for x in nums)


print('05 空数据 不判空版', all_valid([]))                        # 别改：期望 True（要留心的地方）
print('06 空数据 判空版', all_valid_nonempty([]))                  # 别改：期望 False
print('07 非空数据 两版', all_valid([2, 4]), all_valid_nonempty([2, 4]))      # 别改：期望 True True
print('08 有负数 两版', all_valid([2, -4]), all_valid_nonempty([2, -4]))      # 别改：期望 False False

seen = 0                                  # 别改


def positive(x):
    """会数自己被调用几次的判定函数（别改）。"""
    global seen
    seen += 1
    return x > 0


found = any(positive(x) for x in [1, 2, -3, 4, 5])
print('09 any 结果', found)                # 别改：期望 True
print('10 any 看了几个', seen)              # 别改：期望 1（第一个就满足了，不再往下取）
