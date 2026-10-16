"""任务 5 · 三个版本的实测耗时对照

三个版本都写对了，最后一步是把「复杂度」这件事变成看得见的数字：
同一批数据上各跑一次，把耗时摆在一起，看它们随规模怎么涨。

这一份不做正确性判断（那是任务 4 的事），它只管计时。
计时口径与第 3 课一致：前后各取一次 perf_counter 相减，中间不夹别的代码。

接口：文件名、函数名、规模那几行、带 print 的行都是判分接口，别改；
要写的是两个 TODO。

跑： py task5_scale.py          （要跑几秒，最慢的是暴力版）
判： py run_tests.py
"""

from task1_brute import count_brute
from task2_prefix import count_prefix
from task3_window import count_window
from tools import make_positive_array, show_time, ratio_hint, timed


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 time_three(a, S)：把三个版本各跑一次、各量一次耗时，
# 交回 (暴力秒数, 前缀和秒数, 双指针秒数) 三个数。
#
# 要点：
#   b, tb = timed(count_brute, a, S)      timed 在 tools.py 里，交回 (答案, 秒数)
#   p, tp = timed(count_prefix, a, S)
#   w, tw = timed(count_window, a, S)
#   return (tb, tp, tw)
#
# 要按这个顺序计时：先暴力、再前缀和、最后双指针。
# 三个答案不看，这一份只看时间——但顺手对一眼三版答案是否一致也有用。
def time_three(a, S):
    return (0.0, 0.0, 0.0)


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 best_of_three(a, S)：同一批数据上把 time_three 跑三次，
# 逐列取**最小值**交回，也就是 (最小暴力, 最小前缀和, 最小双指针)。
#
# 要点：
#   b = p = w = None                      先留三个名字
#   for _ in range(3):
#       tb, tp, tw = time_three(a, S)
#       逐个与手上的最小值比，更小就换掉
#   return (b, p, w)
#
# 为什么取最小值：这台机器上还有别的程序在跑，某一次可能被系统调度打断，
# 量出来偏大。取三次里最小的那一次，最接近这段代码本身的代价——
# 课件里那张耗时表就是这么量的。
def best_of_three(a, S):
    return (0.0, 0.0, 0.0)


# ── 三个规模，逐行量（这一段是给好的，别改）─────────────────────────
if __name__ == '__main__':
    SIZES = [500, 1000, 2000]
    prev = (0.0, 0.0, 0.0)

    for i, n in enumerate(SIZES):
        arr = make_positive_array(n)
        tb, tp, tw = best_of_three(arr, n)
        show_time(1, '暴力  ', n, tb)
        show_time(2, '前缀和', n, tp)
        show_time(3, '双指针', n, tw)
        if i > 0:
            ratio_hint(4, '暴力  放大', tb, prev[0])
            ratio_hint(5, '前缀和放大', tp, prev[1])
            ratio_hint(6, '双指针放大', tw, prev[2])
        prev = (tb, tp, tw)

    # 同一规模上两个线性版的差距（这一段是给好的，别改）
    arr = make_positive_array(2000)
    tb, tp, tw = best_of_three(arr, 2000)
    ratio_hint(7, '暴力比双指针', tb, tw)
    ratio_hint(8, '前缀和比双指针', tp, tw)
