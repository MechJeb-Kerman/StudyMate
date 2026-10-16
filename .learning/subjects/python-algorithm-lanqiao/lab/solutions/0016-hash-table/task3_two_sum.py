"""任务 3 · 两数之和：列表版与字典版，结果必须逐字一致

目标：给一串整数与一个目标值，找出**两个不同的位置** i < j 使 nums[i] + nums[j] == target，
交出下标对 (i, j)；找不到就交出 (-1, -1)。

  · 列表版 —— 两层循环按定义比较，第一层取 i，第二层取 j > i，加起来看看等不等于目标；
  · 字典版 —— 只扫一遍：扫到 x 时先算「要配谁」need = target - x，
              再问 need 在不在字典里（在 → 命中，交出 (seen[need], i)），
              最后才把 x 与它的下标记进字典。

**先查后存**是这一题的重点，也是判分必查的边界：
  nums = [3, 3], target = 6 的答案是 (0, 1)，不是 (0, 0)——
  扫到下标 1 的 3 时，前面存进去的是下标 0 的那个；当前元素还没入表，配不上自己。
写成「先存后查」的话 [3, 3] 会打出 (0, 0)，判分专门拿这一组数据抓它。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。

跑： py task3_two_sum.py
判： py run_tests.py
"""

import time

# ── 给好的部分：数据（别改）────────────────────────────────
small = [2, 7, 11, 15]
same = [3, 3]                  # 这一组专抓「先存后查」与「同一个元素用两次」
none = [1, 2]
big = []
for i in range(20000):
    big.append(i * 2)          # 20000 个互不相同的偶数
big_target = 39996 + 39998     # 只有最后两个数配得上（前面没有更小的和）

# ── 第 1 版：列表版（两层循环按定义比）─────────────────────
# TODO 1 参考解：两层循环按定义比，j 从 i + 1 起（保证两个位置不同）。
t0 = time.perf_counter()       # 别改：计时开始
ans_list = (-1, -1)
for i in range(len(big)):
    for j in range(i + 1, len(big)):
        if big[i] + big[j] == big_target:
            ans_list = (i, j)
            break
    if ans_list != (-1, -1):
        break
t1 = time.perf_counter()       # 别改：计时结束

# ── 第 2 版：字典版（一遍哈希，先查后存）───────────────────
# TODO 2 参考解：先查 need、再存 x —— 顺序写反了 [3, 3] 就会打出 (0, 0)。
t2 = time.perf_counter()       # 别改：计时开始
ans_dict = (-1, -1)
seen = {}
for i in range(len(big)):
    x = big[i]
    need = big_target - x
    if need in seen:
        ans_dict = (seen[need], i)
        break
    seen[x] = i
t3 = time.perf_counter()       # 别改：计时结束

# ── 打印对照（这几行别改，自动判分按它们读结果）─────────────
print('列表版 大数据', ans_list, f'{t1 - t0:.6f} 秒')
print('字典版 大数据', ans_dict, f'{t3 - t2:.6f} 秒')
print('两版结果逐字一致', ans_list == ans_dict)
print('字典版比列表版快', f'{round((t1 - t0) / max(t3 - t2, 1e-9), 1)} 倍')

# ── 给判分脚本的接口（别改函数名与参数）──────────────────────
# 两份函数都交回下标对 (i, j)（i < j）；找不到交回 (-1, -1)。
def two_sum_list(nums, target):
    """列表版：两层循环。"""
    # TODO 3 参考解
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return (i, j)
    return (-1, -1)


def two_sum_dict(nums, target):
    """字典版：一遍哈希，先查后存。"""
    # TODO 4 参考解：先查 need，再存 x。
    seen = {}
    for i in range(len(nums)):
        x = nums[i]
        need = target - x
        if need in seen:
            return (seen[need], i)
        seen[x] = i
    return (-1, -1)


# ── 小数据逐组对照（这几行别改；两版必须在每一组上都一致）────
cases = [('普通', small, 9), ('两个相同的数', same, 6),
         ('找不到', none, 100), ('空表', [], 5), ('只有一个元素', [4], 8)]
for label, nums, target in cases:
    pair = two_sum_dict(nums, target)
    back = two_sum_list(nums, target)
    print('小数据', label, pair, '列表版', back, '一致', pair == back)
