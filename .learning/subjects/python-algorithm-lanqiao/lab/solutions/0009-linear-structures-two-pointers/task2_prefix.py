"""任务 2 · 前缀和（参考解）"""

from task1_brute import count_brute
from tools import make_positive_array, make_mixed_array, show_count


def build_pre(a):
    pre = [0]
    for x in a:
        pre.append(pre[-1] + x)
    return pre


def count_prefix(a, S):
    pre = build_pre(a)
    seen = {0: 1}
    count = 0
    for r in range(len(a)):
        need = pre[r + 1] - S
        count += seen.get(need, 0)
        seen[pre[r + 1]] = seen.get(pre[r + 1], 0) + 1
    return count


if __name__ == '__main__':
    SMALL = [4, 0, 0, 4, 0]
    print('前缀和表', build_pre(SMALL))

    print('小数组', count_prefix(SMALL, 4))
    print('与暴力一致', count_prefix(SMALL, 4) == count_brute(SMALL, 4))

    a1 = make_positive_array(2000)
    print('全正数 2000 个数', count_prefix(a1, 2000))

    a2 = make_mixed_array(300)
    print('含负数 300 个数', count_prefix(a2, 30))
    print('含负数时仍与暴力一致', count_prefix(a2, 30) == count_brute(a2, 30))

    pre = build_pre(a1)
    print('区间和公式', pre[101] - pre[1])
    print('同一段逐项加', sum(a1[1:101]))
    print('公式与切片一致', pre[101] - pre[1] == sum(a1[1:101]))

    show_count(2, '前缀和', count_prefix(SMALL, 4))
