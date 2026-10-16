"""任务 5 · 滑动窗口最大值（参考解）"""

from collections import deque
from tools import make_perm, make_mixed, show_count, show_time, ratio_hint, timed


def range_max(a, k):
    """暴力版：对每个窗口重新取一次最大值。给好的，别改。"""
    res = []
    if k <= 0 or k > len(a):
        return res
    for i in range(len(a) - k + 1):
        best = a[i]
        for j in range(i + 1, i + k):
            if a[j] > best:
                best = a[j]
        res.append(best)
    return res


def max_window(a, k):
    q = deque()
    res = []
    for i in range(len(a)):
        while q and a[q[-1]] <= a[i]:
            q.pop()
        q.append(i)
        if q[0] <= i - k:
            q.popleft()
        if i >= k - 1:
            res.append(a[q[0]])
    return res


def bad_window(a, k):
    q = deque()
    res = []
    for i in range(len(a)):
        while q and a[q[-1]] <= a[i]:
            q.pop()
        q.append(i)
        if i >= k - 1:
            res.append(a[q[0]])
    return res


if __name__ == '__main__':
    b = [1, 3, -1, -3, 5, 3, 6, 7]
    print('课件数据 k=3 单调队列', max_window(b, 3))
    print('课件数据 k=3 暴力', range_max(b, 3))
    print('课件数据 与暴力一致', max_window(b, 3) == range_max(b, 3))

    c = [7, 1, 1, 1, 1]
    print('过期检查 k=3 单调队列', max_window(c, 3))
    print('过期检查 k=3 漏检查版', bad_window(c, 3))
    print('过期检查 k=3 暴力', range_max(c, 3))
    print('漏检查版与暴力不同', bad_window(c, 3) != range_max(c, 3))

    k1 = make_perm(20)
    print('排列 20 个数 与暴力一致', max_window(k1, 4) == range_max(k1, 4))
    print('排列 20 个数 窗口个数', len(max_window(k1, 4)))
    print('排列 20 个数 k=1', max_window(k1, 1) == k1)
    print('排列 20 个数 k=20', max_window(k1, 20))

    s1 = make_mixed(2000)
    print('随机 2000 个数 k=37 与暴力一致', max_window(s1, 37) == range_max(s1, 37))

    show_count(1, '课件数据一致', max_window(b, 3) == range_max(b, 3))
    show_count(2, '漏检查版不同', bad_window(c, 3) != range_max(c, 3))
    show_count(3, '窗口 2000 个数一致', max_window(s1, 37) == range_max(s1, 37))

    big = make_mixed(20000)
    k_sizes = [100, 500, 1000, 2000]
    window_times = []
    brute_times = []
    brute_answers = []
    same_all = True

    for k in k_sizes:
        ans, tw = timed(max_window, big, k)
        ref, tb = timed(range_max, big, k)
        window_times.append(tw)
        brute_times.append(tb)
        brute_answers.append(ref)
        if ans != ref:
            same_all = False
        show_time(1, '单调队列', 'k=' + str(k), tw)
        show_time(2, '暴力    ', 'k=' + str(k), tb)

    print('四个 k 上答案都与暴力一致', same_all)
    print('同一规模上两个版本的答案个数', [len(x) for x in brute_answers])

    ratio_hint(1, 'k=100  暴力比单调队列慢', brute_times[0], window_times[0])
    ratio_hint(2, 'k=2000 暴力比单调队列慢', brute_times[3], window_times[3])
    show_count(4, '四个 k 答案一致', same_all)
