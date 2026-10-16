"""任务 1 · 暴力版：先写对，再当基准

这一课要写同一道题的三个版本，它是第一个。题目：

    给定 n 个整数组成的数组 a 与一个整数 S，
    求和恰好等于 S 的连续区间有多少个。

区间是 a[l] 到 a[r] 这一段（闭区间，0 <= l <= r <= n-1）。
最直接的写法是枚举所有区间，每对 (l, r) 都把区间里的数加一遍。
下面这份换了个加法顺序：固定左端点 l，右端点 r 一路往右扩、边扩边累加，
省掉了每个区间重头再算一遍的开销——结果与「每对都重算一遍」完全一样。

这一份必须写对：后面两个版本都要拿它当参照（对拍）。
它慢，但正确性一眼能看清，这正是它的用处。

接口：文件名、函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那一段。

跑： py task1_brute.py
判： py run_tests.py
"""

from tools import make_positive_array, make_mixed_array, show_count


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 count_brute(a, S)：用两层循环枚举所有区间，数出「和恰好等于 S」的区间有几个。
#
# 要点：
#   外层循环   for l in range(n)                 左端点从左到右
#   进入外层先写  s = 0                          以 l 开头的区间，和从 0 开始累
#   内层循环   for r in range(l, n)              右端点从 l 一路往右扩
#                s += a[r]                       先把 a[r] 加进来
#                if s == S: count += 1           再判断这一个区间
#   r 要从 l 起（不是从 0 起），否则含重复与反向的区间会被数进来。
#   最后 return count。
def count_brute(a, S):
    return 0


SMALL = [4, 0, 0, 4, 0]                            # 别改：后面几个任务共用它

if __name__ == '__main__':                         # 别改：这层守卫让别的任务 import 它时不出声
    print('小数组', count_brute(SMALL, 4))              # 别改：期望 9

    a1 = make_positive_array(2000)                     # 别改
    print('全正数 2000 个数', count_brute(a1, 2000))     # 别改：期望 44

    a2 = make_mixed_array(300)                         # 别改
    print('含负数 300 个数', count_brute(a2, 30))        # 别改：期望 106

    show_count(1, '暴力', count_brute(SMALL, 4))        # 别改
