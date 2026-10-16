"""任务 5 · 实测耗时对照（参考解）"""

from task1_brute import count_brute
from task2_prefix import count_prefix
from task3_window import count_window
from tools import make_positive_array, show_time, ratio_hint, timed


def time_three(a, S):
    b, tb = timed(count_brute, a, S)
    p, tp = timed(count_prefix, a, S)
    w, tw = timed(count_window, a, S)
    return (tb, tp, tw)


def best_of_three(a, S):
    b = p = w = None
    for _ in range(3):
        tb, tp, tw = time_three(a, S)
        if b is None or tb < b:
            b = tb
        if p is None or tp < p:
            p = tp
        if w is None or tw < w:
            w = tw
    return (b, p, w)


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

    arr = make_positive_array(2000)
    tb, tp, tw = best_of_three(arr, 2000)
    ratio_hint(7, '暴力比双指针', tb, tw)
    ratio_hint(8, '前缀和比双指针', tp, tw)
