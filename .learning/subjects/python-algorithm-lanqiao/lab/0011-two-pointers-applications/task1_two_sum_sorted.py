"""任务 1 · 有序数组的两数之和：对撞指针

题目：数组 a 已经按非降序排好，找一对下标 i < j 使 a[i] + a[j] = S，交出 (i, j)；
没有这样的一对就交出 None。

最直接的写法是枚举所有下标对，代价 O(n²)。对撞指针给出的是另一种走法：取 l = 0、
r = n - 1，每轮比较 a[l] + a[r] 与 S，按结果移动其中一个下标。三条移动规则：

    a[l] + a[r] == S   ->  return (l, r)     什么都没有丢，已经找到
    a[l] + a[r] <  S   ->  l += 1            丢掉 a[l]
    a[l] + a[r] >  S   ->  r -= 1            丢掉 a[r]

后两条靠**有序**这条前提才成立：和偏小时，a[l] 与 [l, r] 里任何一个元素的和都不超过
a[l] + a[r]，所以第一格不必再当左端；和偏大时对称。

一句话记住两个指针各自保证什么：**答案如果存在，它的两个下标一定落在 [l, r] 之内**。
每轮丢掉的那一格由上面两条规则保证不可能出现在答案里。

写完之后把注释补上（这一课的四个任务都要求写注释，判分不查注释，但这是这一课的目的）：
每一行移动条件旁边写一句「这一步丢掉了什么、为什么可以丢」。

接口：函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的两段（第二段是注释）。

跑： py task1_two_sum_sorted.py
判： py run_tests.py
"""

from tools import make_sorted_unique, show_count, show_time, timed


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 two_sum_brute(a, target)：两层循环枚举所有下标对 i < j，找到就交出 (i, j)，
# 扫完没有就交出 None。它是后面那个对撞版的**基准**，先把它写对。
#
# 要点：
#   n = len(a)
#   for i in range(n):
#       for j in range(i + 1, n):         j 从 i + 1 起（同一个元素不能用两次）
#           if a[i] + a[j] == target: return (i, j)
#   return None
def two_sum_brute(a, target):
    return None


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 two_sum_sorted(a, target)：对撞指针版，交出 (l, r)；没有就交出 None。
#
# 要点（照上面那张表写）：
#   l = 0
#   r = len(a) - 1
#   while l < r:                          区间里至少留两个候选下标
#       s = a[l] + a[r]                   每轮只算一次这个和，后面都用 s
#       if s == target:  return (l, r)
#       if s < target:   l += 1           和偏小 → 丢掉左端那一格
#       else:            r -= 1           和偏大 → 丢掉右端那一格
#   return None
#
# 循环条件是 l < r 而不是 l <= r：l 与 r 相等时区间里只剩一个下标，
# 凑不出两个不同的位置；真跑到那里就说明没有答案。
# 每轮只动**一个**下标——同时动两个会跳过候选。
def two_sum_sorted(a, target):
    return None


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声
    a = [1, 4, 5, 9, 11, 15]                   # 别改：课件那一组
    print('课件数据 目标 10', two_sum_sorted(a, 10))            # 别改：期望 (0, 3)
    print('课件数据 目标 20', two_sum_sorted(a, 20))            # 别改：期望 (2, 5)
    print('课件数据 目标 100', two_sum_sorted(a, 100))          # 别改：期望 None
    print('课件数据 暴力对照', [two_sum_brute(a, t) for t in [10, 20, 100]])   # 别改：期望 [(0, 3), (2, 5), None]
    print('课件数据 三组一致', two_sum_sorted(a, 10) == two_sum_brute(a, 10)
          and two_sum_sorted(a, 20) == two_sum_brute(a, 20)
          and two_sum_sorted(a, 100) == two_sum_brute(a, 100))   # 别改：期望 True

    # 边界：空表、只有一个元素、两个元素、负数
    small = [([], 5), ([7], 14), ([3, 3], 6), ([-5, -1, 0, 2], -6)]     # 别改
    for arr, target in small:                  # 别改
        print('边界', arr, target, two_sum_sorted(arr, target), two_sum_brute(arr, target))   # 别改

    # 判分按这两行读「对撞版与基准在每一组上是否一致」
    same_small = True                          # 别改
    for arr, target in small:                  # 别改
        if two_sum_sorted(arr, target) != two_sum_brute(arr, target):
            same_small = False
    print('边界四组 对撞与暴力一致', same_small)                  # 别改：期望 True

    # ── 五组规模上的一致性与轮数 ────────────────────────────────
    # 给好的部分：每组都是**严格递增**的数组、目标值固定取最后两项之和，
    # 所以答案是 (n-2, n-1)。轮数由你自己数（见 TODO 3）。
    sizes = [20, 200, 2000, 8000]              # 别改
    rounds = []                                # 别改
    same_all = True                            # 别改

    for n in sizes:                            # 别改
        arr = make_sorted_unique(n)            # 别改
        target = arr[n - 2] + arr[n - 1]       # 别改
        got, seconds = timed(two_sum_sorted, arr, target)      # 别改
        ref = two_sum_brute(arr, target)                       # 别改
        if got != ref:                         # 别改
            same_all = False                   # 别改
        print('规模 ', n, '对撞', got, '暴力', ref, '一致', got == ref)     # 别改
        show_time(2, '对撞', 'n=' + str(n), seconds)                     # 别改

    print('四组规模 对撞与暴力全一致', same_all)                  # 别改：期望 True

    # ── TODO 3：把对撞版的轮数数出来 ────────────────────────────
    # 目标值取最后两项之和时，两个指针要从两端一路收到右上角，也就是 n - 1 轮。
    # 判分读下面这一行，所以 rings 要按 sizes 里每个规模各放一个轮数。
    # 提示：轮数 = n - 1 —— 每轮至少有一个指针移动一格，指针合计最多走 n - 1 格。
    rounds = [0, 0, 0, 0]                      # TODO 3：把这四个 0 换成对应规模的轮数
    print('每档的轮数', rounds)                                  # 别改：期望 [19, 199, 1999, 7999]
    rounds_ok = rounds == [n - 1 for n in sizes]                # 别改
    print('轮数与 n-1 相同', rounds_ok)                           # 别改：期望 True

    show_count(1, '课件三组一致', two_sum_sorted(a, 10) == two_sum_brute(a, 10)
               and two_sum_sorted(a, 20) == two_sum_brute(a, 20)
               and two_sum_sorted(a, 100) == two_sum_brute(a, 100))     # 别改
    show_count(2, '边界四组一致', same_small)                              # 别改
    show_count(3, '四组规模一致', same_all)                                # 别改
    show_count(4, '轮数正确', rounds_ok)                                   # 别改
