"""任务 4 · 别改坏调用处的列表

两个函数做同一件事：把列表里每个元素都加上一个数。
  add_inplace(nums, delta)：直接在传进来的那个列表上改
  add_copy(nums, delta)：先复制一份，只改副本

跑完看两件事：返回的列表是不是都对，调用处的列表各变成了什么。

带 print 的行是判分接口，别改。

跑： py task4_copy_list.py
判： py run_tests.py
"""

a = [1, 2, 3]


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 add_inplace(nums, delta)：用下标循环就地改 nums 的每个元素，
# 再把 nums 交回调用处。（这一版就是要你看它把调用处改坏。）
def add_inplace(nums, delta):
    return nums


result_a = add_inplace(a, 10)
print('就地版 返回', result_a)                  # 这行别改
print('就地版 调用处', a)                       # 这行别改：会被改坏
print('就地版 改坏了调用处', a != [1, 2, 3])     # 这行别改：期望 True


b = [1, 2, 3]


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 add_copy(nums, delta)：先在函数里写 nums = nums[:] 复制一份，
# 再在副本上用下标循环加 delta，最后把副本交回调用处。
def add_copy(nums, delta):
    return nums


result_b = add_copy(b, 10)
print('副本版 返回', result_b)                  # 这行别改
print('副本版 调用处', b)                       # 这行别改：不该被改
print('副本版 没改调用处', b == [1, 2, 3])       # 这行别改：期望 True
