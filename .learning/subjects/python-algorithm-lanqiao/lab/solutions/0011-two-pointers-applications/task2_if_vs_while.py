"""任务 2 · 该收一格还是收到位：if 与 while 的差别

任务 1 的 `while l < r` 版本里，每轮只动一格，写成 `if` 与写成 `while` 都对——
外层循环一定会带着新的 (l, r) 回来再比一次，没收够的格数还有机会在下一轮补上。

把外层换成 `for l in range(len(a))` 之后，这两种写法就分开了：`l` 一去不回，
同一个 `l` 与更小的 `r` 的组合再没有人检查。看课件那组数据：

    a = [1, 4, 5, 9, 11]，目标值 10，答案只有一对：1 + 9 = 10，下标 (0, 3)。

    two_sum_if    右指针每轮只收一格   ->  None（漏了 1 + 9）
    two_sum_while 右指针一直收到不再偏大 ->  (0, 3)

判据只有一句话：**移动一格之后，我还会回到同一个 (l, r) 组合重新比一次吗？**
外层是 `while l < r` 会，`if` 够用；外层是 `for l` 不会，该用 `while` 的地方写成 `if` 就漏解。

接口：函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的两段。

跑： py task2_if_vs_while.py
判： py run_tests.py
"""

from tools import make_sorted_unique, show_count


def two_sum_brute(a, target):
    """两层循环的基准版（给好的，别改）：判分与下面那几行都拿它当对照。"""
    n = len(a)
    for i in range(n):
        for j in range(i + 1, n):
            if a[i] + a[j] == target:
                return (i, j)
    return None


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 two_sum_if(a, target)：外层 for、右指针每轮**只收一格**。
#
# 要点（照课件那一版写，别去修它——它就是要漏解的那一版）：
#   r = len(a) - 1
#   for l in range(len(a)):
#       if l >= r:  break                  两个下标交错就停
#       s = a[l] + a[r]
#       if s == target:  return (l, r)
#       if s > target:   r -= 1            只收一格，没有再比
#   return None
#
# 它漏解的原因：和偏大时只收一格，下一轮 `for` 已经把 l 交给下一个值，
# 于是「同一个 l、更小的 r」这些组合再也没被检查。
def two_sum_if(a, target):
    r = len(a) - 1
    for l in range(len(a)):
        if l >= r:
            break
        s = a[l] + a[r]
        if s == target:
            return (l, r)
        if s > target:
            r -= 1              # 只收一格：l 已经交给下一个值，(l, r-1) 再没人比
    return None


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 two_sum_while(a, target)：外层照旧 for，但右指针**一直收到不再偏大**。
#
# 要点：
#   r = len(a) - 1
#   for l in range(len(a)):
#       while l < r and a[l] + a[r] > target:      一直收，直到不再偏大
#           r -= 1
#       if l >= r:  break                          收过头、两个下标相遇就停
#       if a[l] + a[r] == target:  return (l, r)
#   return None
#
# 内层 while 的条件里带了 l < r：它保证 r 不会收到 l 左边去——两个下标交错之后再比较，
# 得到的一对次序也就反了。
def two_sum_while(a, target):
    r = len(a) - 1
    for l in range(len(a)):
        while l < r and a[l] + a[r] > target:
            r -= 1              # 一直收到不再偏大
        if l >= r:
            break
        if a[l] + a[r] == target:
            return (l, r)
    return None


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声
    a = [1, 4, 5, 9, 11]                       # 别改：课件那一组
    print('课件数据 if 版', two_sum_if(a, 10))                    # 别改：期望 None
    print('课件数据 while 版', two_sum_while(a, 10))               # 别改：期望 (0, 3)
    print('课件数据 两版不同', two_sum_if(a, 10) != two_sum_while(a, 10))   # 别改：期望 True

    # 逐轮状态（给好的）：把 if 版每一轮的 l / r / 和打出来，
    # 对着这一列就能看出它在哪一轮把 (0, 3) 交出去之后再也没回来。
    r = len(a) - 1                             # 别改
    rows = []                                  # 别改
    for l in range(len(a)):                    # 别改
        if l >= r:                             # 别改
            rows.append((l, r, None))          # 别改
            break                              # 别改
        rows.append((l, r, a[l] + a[r]))       # 别改
        if a[l] + a[r] == 10:                  # 别改
            break                              # 别改
        if a[l] + a[r] > 10:                   # 别改
            r -= 1                             # 别改
    print('if 版逐轮状态', rows)                                 # 别改
    print('if 版第 1 轮之后 r 已经收到', rows[0][1] - 1)           # 别改：期望 3
    print('if 版把 (0, 3) 那一对跳过了', True)                     # 别改

    # 五组数据：if 版在这些数据上会漏解，while 版要与暴力版一致
    cases = [([1, 4, 5, 9, 11], 10), ([2, 3, 4], 6), ([1, 2, 3, 4, 5], 9),
             ([1, 1, 2], 3), ([5, 6, 7, 8], 13)]               # 别改
    missing = 0                                # 别改
    agree = 0                                  # 别改
    for arr, target in cases:                  # 别改
        got_if = two_sum_if(arr, target)
        got_while = two_sum_while(arr, target)
        ok = two_sum_while(arr, target) is not None and got_while == two_sum_brute(arr, target)
        if got_if is None and got_while is not None:
            missing += 1
        if ok:
            agree += 1
        print('数据', arr, target, 'if', got_if, 'while', got_while, 'while对', ok)     # 别改

    print('if 版漏解组数', missing)                               # 别改：期望 1
    print('while 版与暴力一致组数', agree)                         # 别改：期望 5
    show_count(1, '两版不同', two_sum_if(a, 10) != two_sum_while(a, 10))    # 别改
    show_count(2, 'if 版漏解组数', missing)                        # 别改
    show_count(3, 'while 版一致组数', agree)                       # 别改
