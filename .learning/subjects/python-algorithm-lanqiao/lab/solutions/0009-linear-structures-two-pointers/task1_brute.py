"""任务 1 · 暴力版（参考解）"""

from tools import make_positive_array, make_mixed_array, show_count


def count_brute(a, S):
    n = len(a)
    count = 0
    for l in range(n):
        s = 0
        for r in range(l, n):
            s += a[r]
            if s == S:
                count += 1
    return count


if __name__ == '__main__':
    SMALL = [4, 0, 0, 4, 0]
    print('小数组', count_brute(SMALL, 4))

    a1 = make_positive_array(2000)
    print('全正数 2000 个数', count_brute(a1, 2000))

    a2 = make_mixed_array(300)
    print('含负数 300 个数', count_brute(a2, 30))

    show_count(1, '暴力', count_brute(SMALL, 4))
