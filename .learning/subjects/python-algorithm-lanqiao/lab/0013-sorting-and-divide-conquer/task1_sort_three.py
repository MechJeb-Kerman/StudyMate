"""任务 1 · 手写三种排序 + 一批数据的正确性对照

这一课的动手部分从这里开始：把课件里那五个函数抄进这一个文件，再拿**四类数据**各验一次。

四类数据（都由 tools.py 造，每次跑出来都一样）：
  · 随机    —— 0 到 10^9-1，值域很大
  · 已有序  —— 排好的；快排固定主元版在这一类上会退化，这一课要专门盯它
  · 逆序    —— 从大到小；对固定主元版退化得最彻底
  · 重复值  —— 只有 20 种取值、n=20000，重复很多

四件事一起做：
  1. 抄五个函数：merge / merge_sort / partition / quick_sort / counting_sort；
  2. 再写随机主元的快排，以及「在比较里调 key」的归并版；
  3. 造四类数据，每一类都确认「归并 == 快排 == 随机主元快排 == 计数排序 == sorted」；
  4. 把两件「看不见的事」变成数字：归并排序的递归深度、
     `sorted(key=)` 与手写归并各把键函数调用了多少次。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。
判分还会另起一个进程 import 你这个文件里的函数，拿它自己造的小数据再试一遍——
所以函数名与参数必须与下面写的一致。

跑： py task1_sort_three.py       （一秒出头）
判： py run_tests.py
"""

import random
import sys

from tools import (
    make_random, make_sorted, make_reversed, make_duplicates,
    show, show_error, attempt,
)


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 merge(left, right)：合并两个**已经有序**的表，交回一个有序表。
#
# 这是分治三段式的第三段，也是归并排序效率的来源：两段各自有序时，
# 只要不断比较两段的头部、取走较小的一个，一趟线性扫描就拼完了。
#
# 要点（课件里那三处细节，少一处结果就会错位）：
#   out = []；i = 0；j = 0
#   while i < len(left) and j < len(right):    两个都没走完才比较
#   ... 比大小用 <= 而不是 <（相等时先取左边，稳定排序就保住了）
#   收尾的两行 out.extend(left[i:]) / out.extend(right[j:]) 不能省
#
# 写错会怎样：while 的条件写成 or、或者 i += 1 与 j += 1 写反，
# 结果往往只是「差不多对」——大部分位置对，少数重复值或边界值跑到错的位置。
def merge(left, right):
    return []


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 merge_sort(a)：分与治。
#
#   if len(a) <= 1: return a        基例：0 个或 1 个元素已经有序
#   mid = len(a) // 2
#   return merge(merge_sort(a[:mid]), merge_sort(a[mid:]))
#
# 深度是 ⌈log2 n⌉ + 1，离递归上限极远——下面第 4 段那张深度表就是量这件事。
def merge_sort(a):
    return a


# ══ TODO 3 ═════════════════════════════════════════════════
# 写 partition(a, lo, hi)：快排的「分」，交回主元落位后的下标。
#
#   p = a[lo]                    主元取这一段开头（这一课故意这么取）
#   i = lo                       i 的含义：已确定「小于主元」的那一段的末尾下标
#   for j in range(lo + 1, hi + 1):
#       if a[j] < p:             先 i += 1，再交换 a[i] 与 a[j]
#   最后交换 a[lo] 与 a[i]，返回 i
#
# 这一段是**原地**改 a 的，不新建表。它只排 a[lo..hi] 这一段。
def partition(a, lo, hi):
    return lo


# ══ TODO 4 ═════════════════════════════════════════════════
# 写 quick_sort(a, lo=0, hi=None)：快排的「治」。
#
#   hi is None 时 -> len(a) - 1
#   if lo >= hi: return a        这一段空了或只剩一个元素
#   k = partition(a, lo, hi)
#   quick_sort(a, lo, k - 1)；quick_sort(a, k + 1, hi)
#   return a
#
# 注意：这一版**永远取开头作主元**——它在本文件里排四类数据都正确，
# 但到第三个任务会退化。别在这里提前「修」掉它。
def quick_sort(a, lo=0, hi=None):
    return a


# ══ TODO 5 ═════════════════════════════════════════════════
# 写 counting_sort(a, maxv)：计数排序，交回**新表**（不改 a）。
#
#   cnt = [0] * (maxv + 1)       表的长度是值域宽度，不是 n
#   for x in a: cnt[x] += 1
#   再按值的顺序写回：for v in range(maxv + 1): out.extend([v] * cnt[v])
#
# 它完全不比较元素大小，所以不受 O(n log n) 下界约束；代价 O(n + V)。
# 表长 = maxv + 1 这一条，到第四个任务会咬人。
def counting_sort(a, maxv):
    return []


# ══ TODO 6 ═════════════════════════════════════════════════
# 写 quick_sort_random(a, lo=0, hi=None)：把主元选得随机一点。
#
# 与 quick_sort 只差两行（写在 partition 之前）：
#   m = random.randrange(lo, hi + 1)     在 lo..hi 里随机挑一个位置
#   a[lo], a[m] = a[m], a[lo]            把它换到开头，后面的划分原样不动
#
# 为什么这样就不退化了：固定主元每次落在端点时，两段变成「空的」与「剩下全部」；
# 随机主元让划分不容易总是落在端点上，期望深度回到 O(log n)。
# 顶上已经 import random，课件那一版就是这么写的。
def quick_sort_random(a, lo=0, hi=None):
    return a


# ══ TODO 7 ═════════════════════════════════════════════════
# 写 merge_depth(n)：**数一数**归并排序在规模 n 上的最大递归深度。
#
# 别真去排序，只把「怎么切」走一遍——切法必须与 merge_sort 完全一致：
# 每一层的规模 mid = n // 2 与 n - mid，n <= 1 的那一层不再往下切。
#
# 写法（一层一层往下数，不用递归）：
#   level = [n]；depth = 0
#   while level:                 这一层还有规模没展开
#       depth += 1
#       nxt = []
#       for size in level:
#           if size > 1:         切成两半，压进下一层
#               half = size // 2
#               nxt.append(half)
#               nxt.append(size - half)
#       level = nxt
#   return depth
#
# 数出来应当是 ⌈log2 n⌉ + 1：n=8 是 4、n=1000 是 11、n=32768 是 16、n=100000 是 18。
def merge_depth(n):
    return 0


# ══ TODO 8 ═════════════════════════════════════════════════
# 写 merge_sort_key(a, key)：手写归并 + **在比较里调 key** 的版本。
#
# 这是「以为内置 sorted 永远比手写快」那一段的对照：sorted(key=) 先把每个元素的键
# 算出来存到一边、按键排完再取回原元素（装饰 - 排序 - 去装饰），每个元素只算一次键；
# 而这一版每次比较都要算两个键——一次排序要比较约 n log n 次。
#
# 要点：结构照 merge_sort / merge 写，只把比较换成 key(左边) 与 key(右边)：
#   if key(left[i]) <= key(right[j]):   取左边那一个
#   两半的切法与 merge_sort 一模一样（mid = len(a) // 2）。
# a 里的元素是**原元素**（这里就是那几对元组），key 是取键的函数。
def merge_sort_key(a, key):
    return a


# ══ TODO 9 ═════════════════════════════════════════════════
# 写 counting_calls(f, a)：把「键函数被调用了几次」数出来。
#
# 传进来的 f 是下面那个会自己记数的键函数，a 是要排序的元素表。
# 这一份要做的事只有一句：**让 f 去处理这批元素**——
#
#   return f(a)
#
# 它本身不数数；数数的是 f。写这一行的意义是让「谁调用了键函数」这件事有个名字。
def counting_calls(f, a):
    return None


# ── 给好的部分：造数据、打印、第 4 段（别改）─────────────────────────────
if __name__ == '__main__':
    print('任务 1 · 手写三种排序 + 一批数据的正确性对照')

    # 跟四类数据各对一次，所以这一段要有个上限：固定主元快排在**已有序 / 逆序**数据上
    # 每次只削掉一个元素，n = 20000 就要落 20000 层 —— 默认上限（1000）撑不住。
    # 这一段的目的是看「五个函数抄对了没有」，所以这里把上限调大，
    # 让快排在四类数据上都跑得出结果。**注意这里调大不是修好了它**：
    # 「它在有序数据上要落 20000 层」这件事本身，就是第三个任务的题目。
    # （重复值那一类只有 20 种取值，划分会把相等的元素全推到一边，深度也有一千多层。）
    sys.setrecursionlimit(21000)

    SIZE = 20000
    KINDS = 20

    datasets = [
        ('随机', make_random(SIZE)),
        ('已有序', make_sorted(SIZE)),
        ('逆序', make_reversed(SIZE)),
        ('重复值', make_duplicates(SIZE, KINDS)),
    ]

    # ── 第 1 段：四类数据上逐个版本与 sorted 对照 ───────────────────────
    for i, (name, data) in enumerate(datasets, 1):
        want = sorted(data)
        got = {
            '归并': attempt(merge_sort, list(data)),
            '快排': attempt(quick_sort, list(data)),
            '随机主元': attempt(quick_sort_random, list(data)),
            '计数': attempt(counting_sort, list(data), max(data)),
        }
        ok = 0
        for label in ('归并', '快排', '随机主元', '计数'):
            ca = got[label]
            if ca.ok and ca.value == want:
                ok += 1
            elif ca.error:
                show_error(i, label + ' ' + name, ca.error)
        show('一致', i, name, ok)

    # ── 第 2 段：整数版与带 key 版必须给出同一个序列 ─────────────────────
    class KeyCounter:
        """一个会数自己被调用几次的键函数（第 3 段用它）。"""

        def __init__(self):
            self.calls = 0

        def __call__(self, item):
            self.calls += 1
            return item[0]

    pairs = [(3, 'c'), (1, 'a'), (3, 'a'), (2, 'b'), (1, 'b'), (3, 'b')]

    def first_of(item):
        return item[0]

    want_pairs = sorted(pairs, key=first_of)
    got_pairs = attempt(merge_sort_key, list(pairs), first_of)
    show('一致', 5, '带key', int(got_pairs.ok and got_pairs.value == want_pairs))

    # ── 第 3 段：键函数被调用了几次 ─────────────────────────────────────
    key_data = [(i % 97, i) for i in range(2000)]

    # 手写这一版：比较里带着 key（就是把键函数用起来的那种写法）
    c1 = KeyCounter()

    def key_of(item):
        return c1(item)

    def merge_by_key(items):
        return merge_sort_key(items, key_of)

    counting_calls(merge_by_key, key_data)
    show('键调用', 6, '手写', c1.calls)

    # 内置这一版：sorted 的 key 参数替我们调用同一个键函数
    c2 = KeyCounter()

    def sorted_by_key(items):
        return sorted(items, key=c2)

    counting_calls(sorted_by_key, key_data)
    show('键调用', 7, 'sorted', c2.calls)

    # ── 第 4 段：归并的递归深度 ─────────────────────────────────────────
    print('深度 08 归并 n=8 ' + str(merge_depth(8)))
    print('深度 09 归并 n=1000 ' + str(merge_depth(1000)))
    print('深度 10 归并 n=32768 ' + str(merge_depth(32768)))
    print('深度 11 归并 n=100000 ' + str(merge_depth(100000)))
