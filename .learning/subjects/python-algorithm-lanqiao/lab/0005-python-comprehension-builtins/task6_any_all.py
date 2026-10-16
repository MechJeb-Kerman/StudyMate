"""任务 6 · any 与 all：判定循环的两种换法

  · any(可迭代对象)：有任意一个元素为真就是 True；空序列是 False（一个满足的都没有）；
  · all(可迭代对象)：所有元素都为真才是 True；空序列也算 True（一个反例也没有）；
  · 两个默认答案相反 —— 所以用 all 检查「这批数据是不是都合法」时，空数据也会给 True，
    要判空前先判空（if not nums:）；
  · 它们能确定结果就不再往下取值（短路），所以能提前停。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几行（现在都是占位值）。

跑： py task6_any_all.py
判： py run_tests.py
"""

data = [3, -1, 4, 0, 7]                   # 别改
empty = []                                # 别改


# ══ TODO 01 ═════════════════════════════════════════════════
# 循环版：has_pos = False 然后 for x in data: if x > 0: has_pos = True
has_pos = None
print('01 有正数', has_pos)                # 别改：期望 True


# ══ TODO 02 ═════════════════════════════════════════════════
# 循环版：all_pos = True 然后 for x in data: if x <= 0: all_pos = False
all_pos = None
print('02 全部为正', all_pos)               # 别改：期望 False


# ══ TODO 03 ═════════════════════════════════════════════════
# 把上面那个「存在」的判断放到空的那个列表上，看它给出什么。
empty_any = None
print('03 空数据 any', empty_any)           # 别改：期望 False


# ══ TODO 04 ═════════════════════════════════════════════════
# 再换成「全部」的判断，同样用空的列表。
empty_all = None
print('04 空数据 all', empty_all)           # 别改：期望 True


# ══ TODO 05 ═════════════════════════════════════════════════
# 写 all_valid(nums)：这批数据是不是都大于 0。先用「全部满足才为真」的函数写，
# 不加判空 —— 05 那一行会打出什么，正是这一课要留心的地方。
def all_valid(nums):
    return None


# ══ TODO 06 ═════════════════════════════════════════════════
# 写 all_valid_nonempty(nums)：空数据先交回 False，其余照 05 那样判断。
def all_valid_nonempty(nums):
    return None


print('05 空数据 不判空版', all_valid([]))                        # 别改：期望 True
print('06 空数据 判空版', all_valid_nonempty([]))                  # 别改：期望 False
print('07 非空数据 两版', all_valid([2, 4]), all_valid_nonempty([2, 4]))      # 别改：期望 True True
print('08 有负数 两版', all_valid([2, -4]), all_valid_nonempty([2, -4]))      # 别改：期望 False False


# ══ TODO 07 ═════════════════════════════════════════════════
# 用「存在」的函数判断这个列表里有没有正数（表达式用 positive(x)）。
# 提示：第一个元素就满足，所以判定函数只会被调用 1 次 —— 这就是短路。
seen = 0                                  # 别改


def positive(x):
    """会数自己被调用几次的判定函数（别改）。"""
    global seen
    seen += 1
    return x > 0


found = None
print('09 any 结果', found)                # 别改：期望 True
print('10 any 看了几个', seen)              # 别改：期望 1
