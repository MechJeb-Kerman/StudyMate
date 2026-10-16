"""任务 3 · 双指针（参考解）"""

from task1_brute import count_brute
from task2_prefix import count_prefix
from tools import make_positive_array, make_mixed_array, show_count


def count_window(a, S):
    n = len(a)
    r = 0
    s = 0
    count = 0
    for l in range(n):
        while r < n and s < S:
            s += a[r]
            r += 1
        if s == S:
            count += 1
        s -= a[l]
    return count


def count_window_broken(a, S):
    n = len(a)
    r = 0
    s = 0
    count = 0
    for l in range(n):
        while s < S:
            s += a[r]
            r += 1
        if s == S:
            count += 1
        s -= a[l]
    return count


if __name__ == '__main__':
    SMALL = [4, 0, 0, 4, 0]
    print('小数组 双指针', count_window(SMALL, 4))
    print('小数组 暴力', count_brute(SMALL, 4))
    print('小数组 两版答案一致', count_window(SMALL, 4) == count_brute(SMALL, 4))

    a1 = make_positive_array(2000)
    print('全正数 2000 个数 双指针', count_window(a1, 2000))
    print('全正数 与暴力一致', count_window(a1, 2000) == count_brute(a1, 2000))

    a2 = make_mixed_array(300)
    print('含负数 300 个数 双指针', count_window(a2, 30))
    print('含负数 与暴力一致', count_window(a2, 30) == count_brute(a2, 30))
    print('含负数 前缀和与暴力一致', count_prefix(a2, 30) == count_brute(a2, 30))

    try:
        print('错版在 [1, 2] 上', count_window_broken([1, 2], 100))
    except IndexError as exc:
        print('错版在 [1, 2] 上报错 IndexError:', exc)

    show_count(3, '双指针 正数', count_window(a1, 2000))
    show_count(4, '双指针 含负数', count_window(a2, 30))
