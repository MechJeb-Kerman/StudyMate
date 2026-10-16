"""任务 4 参考解 · 别改坏调用处的列表

add_inplace：顺着传进来的引用就地改，调用处的列表跟着变（有时正是想要的效果）。
add_copy：先 nums = nums[:] 换一份副本，后面都改副本，调用处不受影响。
"""

a = [1, 2, 3]


def add_inplace(nums, delta):
    for i in range(len(nums)):
        nums[i] = nums[i] + delta
    return nums


result_a = add_inplace(a, 10)
print('就地版 返回', result_a)                  # [11, 12, 13]
print('就地版 调用处', a)                       # [11, 12, 13]
print('就地版 改坏了调用处', a != [1, 2, 3])     # True


b = [1, 2, 3]


def add_copy(nums, delta):
    nums = nums[:]                  # 复制一份，代价 O(k)
    for i in range(len(nums)):
        nums[i] = nums[i] + delta
    return nums


result_b = add_copy(b, 10)
print('副本版 返回', result_b)                  # [11, 12, 13]
print('副本版 调用处', b)                       # [1, 2, 3]
print('副本版 没改调用处', b == [1, 2, 3])       # True
