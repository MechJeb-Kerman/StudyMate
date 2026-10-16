"""任务 3 · 双指针：两个下标都只往前走

前缀和版已经把两层循环降成一层，代价是额外拿出了一张 n+1 项的表。
如果数组里的元素全是正数，还有一条更省的路：**双指针**，也叫**滑动窗口**
——用两个下标 l <= r 框住一段连续的区间，让它们在数组上同步往右滑。

它的想法是：固定右端点时，区间和随左端点向右移动而变小。
既然「和」这个量随两个下标各自单调变化，就不必为每个区间重新计算，
只维护当前窗口的和，按三种情形调整：

    和小于 S：把 r 往右移一格，把新元素加进来；
    和等于 S：答案加一，随后把 l 往右移一格，减掉左边那个元素；
    和大于 S：把 l 往右移一格，减掉左边那个元素。

这一段代码里 l 由 for 循环一路往右，r 只在 while 里往右，两个下标都不回头。

接口：文件名、函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是两个 TODO。

跑： py task3_window.py
判： py run_tests.py
"""

from task1_brute import count_brute
from task2_prefix import count_prefix
from tools import make_positive_array, make_mixed_array, show_count


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 count_window(a, S)：滑动窗口版，交回答案。
#
# 要点（照上面那三种情形写）：
#   n = len(a); r = 0; s = 0; count = 0
#   for l in range(n):
#       while r < n and s < S:      还差得远、且右边还有元素，就右扩
#           s += a[r]
#           r += 1
#       if s == S:                  扩完了再判一次
#           count += 1
#       s -= a[l]                   左端点往右移一格，把那一个减掉
#   return count
#
# 两处不能省：
#   - while 的条件里除了 s < S 还要有 r < n，否则 r 会越过数组末尾；
#   - 每轮末尾那一次 s -= a[l] 是「l 往右移」的落地，漏了它窗口就只会涨。
def count_window(a, S):
    return 0


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 count_window_broken(a, S)：把上面那份的 while 条件改成只看 s < S，
# 也就是去掉 r < n。这是故意的错版，用来复现「右指针越过数组末尾」这个报错。
#
# 要点：与 TODO 1 只差一处——while 写成 while s < S:
# 其余原样（先加 a[r] 再 r += 1、判 s == S、末尾 s -= a[l]）。
def count_window_broken(a, S):
    return 0


if __name__ == '__main__':
    SMALL = [4, 0, 0, 4, 0]                                   # 别改
    print('小数组 双指针', count_window(SMALL, 4))              # 别改：期望 4
    print('小数组 暴力', count_brute(SMALL, 4))                # 别改：期望 9
    print('小数组 两版答案一致', count_window(SMALL, 4) == count_brute(SMALL, 4))   # 别改：期望 False

    a1 = make_positive_array(2000)                            # 别改
    print('全正数 2000 个数 双指针', count_window(a1, 2000))     # 别改：期望 44
    print('全正数 与暴力一致', count_window(a1, 2000) == count_brute(a1, 2000))     # 别改：期望 True

    a2 = make_mixed_array(300)                                # 别改
    print('含负数 300 个数 双指针', count_window(a2, 30))        # 别改：期望 4
    print('含负数 与暴力一致', count_window(a2, 30) == count_brute(a2, 30))         # 别改：期望 False
    print('含负数 前缀和与暴力一致', count_prefix(a2, 30) == count_brute(a2, 30))   # 别改：期望 True

    # 去掉 r < n 之后会怎样：a 只有两个数、S 大到永远凑不出来。
    # 这一段是给好的（判分接口）：它把报错接住、只看报错的类型，别改。
    try:
        print('错版在 [1, 2] 上', count_window_broken([1, 2], 100))
    except IndexError as exc:
        print('错版在 [1, 2] 上报错 IndexError:', exc)

    show_count(3, '双指针 正数', count_window(a1, 2000))         # 别改
    show_count(4, '双指针 含负数', count_window(a2, 30))         # 别改
