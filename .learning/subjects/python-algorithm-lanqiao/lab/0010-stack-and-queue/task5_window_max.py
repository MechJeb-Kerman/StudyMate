"""任务 5 · 滑动窗口最大值：单调队列，两条弹出缺一不可

题目：给定 n 个整数的数组 a 与窗口长度 k，输出每个长度 k 的窗口里的最大值。

第 9 课的双指针也用一个窗口框住连续一段，但那里「加一个元素、减一个元素之后，
关心的那个量不往回走」——窗口最大值不满足这条：最大值可能是窗口最左边那个元素，
它一走，窗口里的最大值就得重新找。

单调队列把「没用的旧值当场丢掉」搬到了队列上：队列里存**下标**，队首是当前窗口
最大值的下标，队列中下标对应的值自队首向队尾递减。窗口右端每移到一个新位置 i：

    弹队尾：只要队尾下标对应的值不大于 a[i]，就把它弹出；
    把 i 入队；
    弹队首：若队首下标已经滑出窗口（下标不大于 i - k），把它弹出；
    此时队首就是当前窗口最大值的下标。

三个函数：

    range_max(a, k)   暴力版：每个窗口取一次最大值，代价 O(nk)。给好的，别改。
    max_window(a, k)  单调队列版（TODO 1）。
    bad_window(a, k)  故意漏掉队首那条过期检查的错版（TODO 2）。

接口：函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的两段。

跑： py task5_window_max.py
判： py run_tests.py
"""

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


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 max_window(a, k)：单调队列版，交回每个窗口的最大值组成的列表。
#
# 要点（照上面那三条写，顺序不能换）：
#   q = deque()                    存**下标**，不是值；a[q[0]] 是当前窗口最大值
#   res = []
#   for i in range(len(a)):
#       while q and a[q[-1]] <= a[i]:      队尾更小（或相等）的元素再也用不到
#           q.pop()
#       q.append(i)
#       if q[0] <= i - k:                  队首已经滑出窗口
#           q.popleft()
#       if i >= k - 1:                     第一个窗口凑满了才开始输出
#           res.append(a[q[0]])
#   return res
#
# 两处细节：
#   · 队尾那条用的是 `<=`：相等时留下新的那个（它更晚离开窗口）；
#   · i >= k - 1 那一句管开头：前 k-1 个位置上的窗口还没凑满 k 个数，不输出。
#     少了它，输出会比正确答案多 k-1 项。
def max_window(a, k):
    return []


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 bad_window(a, k)：与 max_window 只差一处——**去掉队首那条过期检查**
# （不写 if q[0] <= i - k 那两行）。
#
# 这是故意的错版：队首留在那里的是早已滑出窗口的旧值，从第二个窗口起就全错。
# 它是这一课的「该弹的时候没弹」在队列上的样子，判分拿 [7, 1, 1, 1, 1]、k = 3
# 那一组数据抓它：正确是 [7, 1, 1]，漏掉检查是 [7, 7, 7]。
def bad_window(a, k):
    return []


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声
    b = [1, 3, -1, -3, 5, 3, 6, 7]             # 别改：课件那一组
    print('课件数据 k=3 单调队列', max_window(b, 3))                      # 别改：期望 [3, 3, 5, 5, 6, 7]
    print('课件数据 k=3 暴力', range_max(b, 3))                          # 别改：期望同上
    print('课件数据 与暴力一致', max_window(b, 3) == range_max(b, 3))      # 别改：期望 True

    c = [7, 1, 1, 1, 1]                        # 别改：专抓队首过期检查的那一组
    print('过期检查 k=3 单调队列', max_window(c, 3))                      # 别改：期望 [7, 1, 1]
    print('过期检查 k=3 漏检查版', bad_window(c, 3))                      # 别改：期望 [7, 7, 7]
    print('过期检查 k=3 暴力', range_max(c, 3))                          # 别改：期望 [7, 1, 1]
    print('漏检查版与暴力不同', bad_window(c, 3) != range_max(c, 3))       # 别改：期望 True

    k1 = make_perm(20)                         # 别改：每个数出现一次，一眼看得出下标
    print('排列 20 个数 与暴力一致', max_window(k1, 4) == range_max(k1, 4))   # 别改：期望 True
    print('排列 20 个数 窗口个数', len(max_window(k1, 4)))                  # 别改：期望 17
    print('排列 20 个数 k=1', max_window(k1, 1) == k1)                    # 别改：期望 True
    print('排列 20 个数 k=20', max_window(k1, 20))                       # 别改：期望 [19]

    s1 = make_mixed(2000)                      # 别改：有正有负
    print('随机 2000 个数 k=37 与暴力一致', max_window(s1, 37) == range_max(s1, 37))   # 别改：期望 True

    show_count(1, '课件数据一致', max_window(b, 3) == range_max(b, 3))     # 别改
    show_count(2, '漏检查版不同', bad_window(c, 3) != range_max(c, 3))    # 别改
    show_count(3, '窗口 2000 个数一致', max_window(s1, 37) == range_max(s1, 37))   # 别改

    # ── 把「与 k 有关」写成一张表 ────────────────────────────────
    # 给好的部分：造一份 20000 项的数据，四个窗口长度 k = 100 / 500 / 1000 / 2000。
    # 单调队列那一列每次都是 O(n)，暴力那一列是 O(nk)——所以同一行里两个数越差越远。
    big = make_mixed(20000)                    # 别改
    k_sizes = [100, 500, 1000, 2000]           # 别改
    window_times = []                          # 别改
    brute_times = []                          # 别改
    brute_answers = []                         # 别改
    same_all = True                            # 别改

    for k in k_sizes:                          # 别改
        ans, tw = timed(max_window, big, k)    # 别改：交回 (答案, 秒数)
        ref, tb = timed(range_max, big, k)     # 别改
        window_times.append(tw)                # 别改
        brute_times.append(tb)                 # 别改
        brute_answers.append(ref)              # 别改
        if ans != ref:                         # 别改
            same_all = False                   # 别改
        show_time(1, '单调队列', 'k=' + str(k), tw)                  # 别改
        show_time(2, '暴力    ', 'k=' + str(k), tb)                  # 别改

    print('四个 k 上答案都与暴力一致', same_all)                          # 别改：期望 True
    print('同一规模上两个版本的答案个数', [len(x) for x in brute_answers])   # 别改：期望 [19901, 19501, 19001, 18001]

    # 倍数：k=100 与 k=2000 这两行里，暴力比单调队列各快/慢多少
    ratio_hint(1, 'k=100  暴力比单调队列慢', brute_times[0], window_times[0])     # 别改
    ratio_hint(2, 'k=2000 暴力比单调队列慢', brute_times[3], window_times[3])     # 别改
    show_count(4, '四个 k 答案一致', same_all)                          # 别改
