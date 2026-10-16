"""任务 2 · 前 k 大不必排全序：大小为 k 的最小堆就够了

课件「前 k 大不必排全序」那一节：写起来就是一行 `heapq.nlargest(k, data)`，
它内部维护一个**大小为 k 的最小堆**。

    走一遍 data：堆没满就压进去；满了就与堆顶（这 k 个里最小的那个）比一比——
    比堆顶小就丢掉，比堆顶大就顶掉它。

所以堆里始终只有 k 个数，最后堆里就是前 k 大。排序版要把 n 个数的**整个顺序**都算出来，
而这里只需要「谁在 k 名以内」——这就是「$k$ 远小于 $n$ 时不必排全序」。

要紧的一句实话：这不是「堆总比排序快」。k 小的时候差距明显（课件实测 20 万个数取前 10 大，
快 5 到 8 倍）；k 涨到 n 的一半时，那口大小为 k 的堆自己就要维护 $O(k)$ 个数，
两者差不多了；取第 k 大更是**不需要有序**。所以这一份要把 k 从小到大量一条出来。

接口：文件名、函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那几段。

跑： py task2_kth_largest.py
判： py run_tests.py

参考解。与任务目录里的同名文件只差标着 TODO 的四段。
"""

import heapq
import random

from tools import best_of, show_count, show_label, show_time

N = 200000                                     # 别改：与课件量过的那一等规模一样
K_SMALL = 10                                   # 别改：k 很小
K_COUNT = 3                                    # 别改：这里从 k=1 数到 k=3 的个数
REPEATS = 5                                    # 别改：每档跑这么多次，取最快的一次
SEED = 5                                       # 别改：课件那段就是 random.seed(5)


# ══ TODO 1 ═════════════════════════════════════════════════
# 补 kth_by_sort(a, k)：排序版——第 k 大就是降序排完的第 k 个。
#   b = sorted(a, reverse=True)；return b[k - 1]
#   注意是 k - 1：k 是「第几个」，下标从 0 起，第 1 大是 b[0]。
#   这一版是**基准**：它算得对，只是把整个顺序都算了出来。
def kth_by_sort(a, k):
    """排序版（基准）：降序排完取第 k-1 项。"""
    b = sorted(a, reverse=True)
    return b[k - 1]


# ══ TODO 2 ═════════════════════════════════════════════════
# 补 kth_by_minheap(a, k)：堆版——用一个**大小为 k 的最小堆**。
#   照课件「f 远小于 n 时不必排全序」那一节的意思写：
#     h = a[:k]；heapq.heapify(h)              先拿前 k 个建堆
#     for v in a[k:]:                          从第 k + 1 个数开始一个个过
#         if v > h[0]: heapq.heapreplace(h, v) 比堆顶大就顶掉它（弹顶 + 压入，一步）
#     return h[0]                              堆里是最大的 k 个，堆顶上就是第 k 大
#   为什么 h[0] 就是第 k 大：堆里始终是「目前见过的最大的 k 个数」，而 h[0] 是这 k 个里
#   最小的那个——比它大的数正好有 k - 1 个，所以它是第 k 大。
#   别用 heappop(h) 再 heappush(h, v)：那是两步，heapreplace 一步做完（对数时间）。
def kth_by_minheap(a, k):
    """堆版：大小为 k 的最小堆，堆顶上就是第 k 大。"""
    h = list(a[:k])
    heapq.heapify(h)
    for v in a[k:]:
        if v > h[0]:
            heapq.heapreplace(h, v)
    return h[0]


# ══ TODO 3 ═════════════════════════════════════════════════
# 补 topk_by_heap(a, k)：拿大小为 k 的最小堆取**前 k 大**，交回一个降序列表
#   （与 heapq.nlargest(k, a) 逐项一致）。
#     h = a[:k]；heapq.heapify(h)；过一遍 a[k:]（比堆顶大就 heapreplace）；
#     最后把堆里的东西**逐个 heappop** 出来 append 进结果——heappop 是从小到大，
#     所以要 reverse 一下（或者用 h.sort(reverse=True)，都不一样地想一想为什么）。
#   这里为什么要一个个弹：堆只保证 h[0] 最小，**其余位置没有顺序**，
#   不能拿 h 当排好序的列表直接交回。
def topk_by_heap(a, k):
    """大小为 k 的最小堆取出前 k 大，交回降序列表。"""
    h = list(a[:k])
    heapq.heapify(h)
    for v in a[k:]:
        if v > h[0]:
            heapq.heapreplace(h, v)
    out = [heapq.heappop(h) for _ in range(len(h))]
    out.reverse()
    return out


# ══ TODO 4 ═════════════════════════════════════════════════
# 补 smaller_heap_better(ratios)：ratios 是 [(k, 排序版比堆版慢几倍), …]。
#   交回 True / False：k 小的时候那个倍数是不是更大——也就是
#   「k 远小于 n 时，堆省下的活更多」这一条判断。
#   写法：拿 ratios 里 k 最小那一项与 k 最大那一项的倍数比一比（用下标取首尾即可）。
def smaller_heap_better(ratios):
    """k 最小时那个倍数是不是更大（首项与末项比）。"""
    if len(ratios) < 2:
        return False
    return float(ratios[0][1]) > float(ratios[-1][1])


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声

    random.seed(SEED)                          # 别改
    DATA = [random.randrange(10 ** 9) for _ in range(N)]     # 别改

    # ── 一、两种写法给出同一个值（这几行别改）────────────────────
    for k in (1, 2, K_COUNT, K_SMALL, N // 2, N - 1, N):       # 别改
        s = kth_by_sort(DATA, k)               # 别改
        h = kth_by_minheap(DATA, k)            # 别改
        print('k=' + str(k), '排序版', s, '堆版', h)             # 别改
        show_label('第k大 k=' + str(k) + ' 一致', s == h)        # 别改：期望 True

    show_count(1, '第k大 k=' + str(K_SMALL), kth_by_minheap(DATA, K_SMALL))    # 别改
    show_count(2, '第k大 k=' + str(N), kth_by_minheap(DATA, N))                # 别改

    # ── 二、k 很小：sorted 取前 k 与 nlargest 对照（这一段别改）──
    a = sorted(DATA, reverse=True)[:K_SMALL]   # 别改
    b = heapq.nlargest(K_SMALL, DATA)          # 别改
    print('前' + str(K_SMALL) + '大 两版一致', a == b)             # 别改：期望 True
    show_label('前' + str(K_SMALL) + '大 两版一致', a == b)        # 别改：期望 True
    show_label('前' + str(K_SMALL) + '大 前三个', str(b[:3]))      # 别改
    mine = topk_by_heap(DATA, K_SMALL)         # 别改
    show_label('自己写的堆 前' + str(K_SMALL) + '大 与 nlargest 一致', mine == b)   # 别改
    show_label('自己写的堆 前' + str(K_SMALL) + '大 前三个', str(list(mine[:3])))   # 别改

    # ── 三、k 从小到大，看两种写法的差距怎么变（这几行别改）──────
    ratios = []                                # 别改
    for k in (K_SMALL, N // 2, N - 1):         # 别改
        t_sort = best_of(kth_by_sort, DATA, k, repeats=REPEATS)          # 别改
        t_heap = best_of(kth_by_minheap, DATA, k, repeats=REPEATS)       # 别改
        ratios.append((k, t_sort / max(t_heap, 1e-9)))                   # 别改
        show_time(1, '第k大 排序版', 'k=' + str(k), t_sort)               # 别改
        show_time(2, '第k大 堆版  ', 'k=' + str(k), t_heap)               # 别改
        show_label('倍数 k=' + str(k) + ' 排序比堆', round(t_sort / max(t_heap, 1e-9), 2))   # 别改

    show_count(3, 'k小的时候堆更划算', smaller_heap_better(ratios))       # 别改
    print('k 小的时候堆更划算', smaller_heap_better(ratios))               # 别改：期望 True
