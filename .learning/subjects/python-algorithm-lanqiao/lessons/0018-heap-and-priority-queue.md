---
title: 每次都要最小的那个
goal: 能用 heapq 解决取极值类问题，说出堆操作的复杂度，并手写一个数组实现的最小堆。
---

## 每次都要最小的那个

先看一道题，它是这一课的全部动机。

**合并果子**：有 $n$ 堆果子，每堆有各自的重量。每次可以合并两堆，代价是这两堆重量之和；合并后的新堆放回去。问把所有果子合并成一堆，总代价最小是多少。

要让总代价最小，每轮都挑**当前最轻的两堆**合并。于是这个算法每一步都在问同一个问题：**现在最小的是哪一堆？**

最直白的写法是每轮排一次序。这个写法能算对，但每一轮都要重排整个列表。问题在于「取最小值」这件事只需要一条信息，而排序把整张顺序都算了出来——多算的部分就是浪费的地方。

堆（heap）正是为这件事设计的结构：**它只维护「最小值在顶上」这一条性质，不做全排序。**

::: quiz 理解 锚点：堆为什么不做全排序
:::

## 数组里存一棵完全二叉树

堆的形状是一棵**完全二叉树**：每一层从左到右填满，只有最后一层可以不满，而且最后一层的结点也靠左排列。第 17 课讲过二叉树，这里用它的一个特殊形态。

这个形状有个好处：它可以**直接放进一个列表**，不需要左右孩子的引用。下标关系是固定的：

| 关系 | 公式 |
| --- | --- |
| 结点 $i$ 的左孩子 | $2i + 1$ |
| 结点 $i$ 的右孩子 | $2i + 2$ |
| 结点 $i$ 的父结点 | $(i - 1) // 2$ |

「完全」这个前提就是拿来保证上面三条不出错的：树里没有空洞，下标才连得上。所以堆用列表存，比用上一课的 `[值, 左, 右]` 更省——省掉了所有孩子的位置记录。

堆的性质只有一条，叫**堆序性质**：**每个结点都不大于它的两个孩子。** 注意它说的是「与两个孩子比」，不是「与所有后代比」。

::: quiz 理解 锚点：堆序性质说的是什么
:::

这一条推论很重要，也很容易搞错：

```python
import heapq

h = [5, 3, 8, 1, 9, 2, 7]
heapq.heapify(h)
print('heapify 之后', h)
print('h[0] =', h[0], '（一定是最小）')
print('h[1] =', h[1], ' 第 2 小是', sorted(h)[1], '-> 下标取第 k 小是错的')
```

```text
heapify 之后 [1, 3, 2, 5, 9, 8, 7]
h[0] = 1 （一定是最小）
h[1] = 3  第 2 小是 2 -> 下标取第 k 小是错的
```

`h[0]` 一定是最小值，这一点是堆序性质给的保证。但 `h[1]` 只是「根的左孩子」，它和第 2 小的元素没有关系——这里 `h[1]` 是 3，而第 2 小是 2。**要取第 $k$ 小，只能一个一个 `heappop` 出来，不能按下标取。**

还有一个常被说错的判断，顺手量一下：**对堆的列表排序，会不会「破坏」堆结构？** 不会。升序列表本身就是合法的最小堆：

```python
h.sort()
ok_left = all(h[i] <= h[2 * i + 1] for i in range(len(h) // 2))
ok_right = all(h[i] <= h[2 * i + 2] for i in range((len(h) - 1) // 2))
print('排序之后', h, '仍是合法最小堆:', ok_left and ok_right)
```

```text
排序之后 [1, 2, 3, 5, 7, 8, 9] 仍是合法最小堆: True
```

父结点的下标总比孩子小，值也总比孩子小，堆序性质两条都满足。所以排序排不出「坏掉的堆」。

真正的代价在别处：排序是 $O(n \log n)$、`heapify` 是 $O(n)$；更要紧的是，**如果你每插入一个就排一次，那就回到了合并果子列表版的处境**——每轮 $O(n \log n)$，堆的优势全丢掉。坑不在「结构坏了」，在「偷偷把复杂度换回了高的那个」。

::: quiz 排错 锚点：对堆的列表排序会不会破坏堆结构
:::

::: quiz 理解 锚点：完全二叉树的数组下标关系
:::

## 合并果子两种写法

现在把两种写法并排放在一起。列表版每轮排序，堆版每轮弹出两个再压回一个：

```python
import heapq
import random
import time

def merge_list(a):
    a = sorted(a)
    total = 0
    while len(a) > 1:
        x = a.pop(0)
        y = a.pop(0)
        s = x + y
        total += s
        a.append(s)
        a.sort()
    return total

def merge_heap(a):
    heapq.heapify(a)
    total = 0
    while len(a) > 1:
        x = heapq.heappop(a)
        y = heapq.heappop(a)
        s = x + y
        total += s
        heapq.heappush(a, s)
    return total

random.seed(11)
for n in (1000, 2000, 4000):
    data = [random.randint(1, 1000) for _ in range(n)]
    t0 = time.perf_counter(); r1 = merge_list(list(data)); t1 = time.perf_counter()
    t2 = time.perf_counter(); r2 = merge_heap(list(data)); t3 = time.perf_counter()
    print(f'n={n:>5}  列表 {t1-t0:.4f} 秒   堆 {t3-t2:.4f} 秒   相差 {(t1-t0)/(t3-t2):>6.1f} 倍   两边结果一致 {r1 == r2}')
```

| $n$ | 列表版 | 堆版 | 相差 | 两边结果一致 |
| --- | --- | --- | --- | --- |
| 1000 | 0.0014 秒 | 0.0004 秒 | 3.4 倍 | 是 |
| 2000 | 0.0043 秒 | 0.0008 秒 | 5.5 倍 | 是 |
| 4000 | 0.0155 秒 | 0.0018 秒 | 8.8 倍 | 是 |

（本机实测。秒数每次运行都会浮动：同一段代码第二次跑得到 0.0011 / 0.0041 / 0.0164 与 0.0005 / 0.0010 / 0.0016，倍数落在 2 到 11 倍之间。**要看的是倍数随规模变大这个趋势，不是某一次的具体秒数。**）

两边结果一致——所以这不是「谁算得对」的区别，是代价的区别。

看关键的一列：规模翻倍时差距从 3.4 倍涨到 5.5 倍再到 8.8 倍。原因是两边每一步的代价不同：

| 每轮的动作 | 列表版 | 堆版 |
| --- | --- | --- |
| 找最小的两个 | 排序一次 $O(n \log n)$ | 弹两次各 $O(\log n)$ |
| 放回新堆 | 追加后又要重排 | 压入一次 $O(\log n)$ |
| 一轮合计 | $O(n \log n)$ | $O(\log n)$ |
| $n$ 轮合计 | $O(n^2 \log n)$ | $O(n \log n)$ |

堆版每一步都是对数时间，因为它不需要知道其余元素的顺序——**只要保证最小那个在顶上就够了**。这就是「少维护一些信息」换来速度的地方。

::: quiz 理解 锚点：为什么堆能在对数时间取到最小
:::

## 建堆比逐个插入快

把一堆现有的数变成堆，有两种做法：建个空列表逐个 `heappush`，或者直接把整个列表交给 `heapify`。后者更快，而且快得不只是常数：

```python
import heapq
import random
import time

for n in (100000, 400000):
    data = [random.randrange(10**9) for _ in range(n)]
    t0 = time.perf_counter()
    a = list(data)
    heapq.heapify(a)
    t1 = time.perf_counter()
    t2 = time.perf_counter()
    b = []
    for v in data:
        heapq.heappush(b, v)
    t3 = time.perf_counter()
    print(f'n={n:>7}  heapify {t1-t0:.4f} 秒   逐个 push {t3-t2:.4f} 秒   相差 {(t3-t2)/(t1-t0):.1f} 倍')
```

| $n$ | heapify | 逐个 push | 相差 |
| --- | --- | --- | --- |
| 100000 | 0.0024 秒 | 0.0091 秒 | 3.9 倍 |
| 400000 | 0.0107 秒 | 0.0358 秒 | 3.3 倍 |

（本机实测；第二次跑是 0.0021 / 0.0100 与 0.0093 / 0.0379，倍数为 4.5 与 3.8。）

两者都是原地改列表。区别在复杂度：`heapify` 是 $O(n)$，逐个 `heappush` 是 $O(n \log n)$。三次多一点而不是「快一点点」，来自两种建堆方式的不同——逐个插入要把它一路**上浮**到合适的位置，而 `heapify` 从最后一个非叶结点往前逐个**下沉**，越靠近底部的结点被下沉的次数越少。

所以只要数据已经全在手里（不是一个个流进来的），就用 `heapify`。

::: quiz 理解 锚点：heapify 与逐个 push 的区别
:::

## 上浮与下沉

`heapq` 提供的两个内部动作叫**上浮**（sift up）与**下沉**（sift down）：

- **上浮**：新元素追加到末尾（也就是树的最下面一层靠右），然后不断与父结点比较，比父结点小就交换，直到不再比父结点小。用于插入。
- **下沉**：把末尾元素搬到根上，然后不断与较小的那个孩子比较，比孩子大就交换，直到不再比孩子大。用于弹出。

两者的共同点是**每一层只走一步**，所以一次操作最多走树高那么多步，也就是 $O(\log n)$。写成代码：

```python
class MinHeap:
    def __init__(self):
        self.a = []

    def push(self, v):
        self.a.append(v)
        self._up(len(self.a) - 1)

    def pop(self):
        a = self.a
        top = a[0]
        last = a.pop()
        if a:
            a[0] = last
            self._down(0)
        return top

    def _up(self, i):
        a = self.a
        while i > 0:
            p = (i - 1) // 2
            if a[p] <= a[i]:
                break
            a[p], a[i] = a[i], a[p]
            i = p

    def _down(self, i):
        a = self.a
        n = len(a)
        while True:
            l = 2 * i + 1
            r = l + 1
            m = i
            if l < n and a[l] < a[m]:
                m = l
            if r < n and a[r] < a[m]:
                m = r
            if m == i:
                break
            a[i], a[m] = a[m], a[i]
            i = m

random.seed(9)
vals = [random.randrange(1000) for _ in range(500)]
mine = MinHeap()
for v in vals:
    mine.push(v)
theirs = list(vals)
heapq.heapify(theirs)
out_mine = [mine.pop() for _ in range(len(vals))]
out_theirs = [heapq.heappop(theirs) for _ in range(len(vals))]
print('手写堆弹出的序列与 heapq 一致:', out_mine == out_theirs)
print('与原数组排序一致:', out_mine == sorted(vals))
print('前 8 个', out_mine[:8])
```

```text
手写堆弹出的序列与 heapq 一致: True
与原数组排序一致: True
前 8 个 [0, 3, 5, 5, 6, 7, 8, 8]
```

与 `heapq` 逐个弹出的序列完全一致。注意 `pop` 里那三步的顺序：先记下根（答案）、再把末尾元素取出来、然后把它放到根上往下沉。**如果先把根删掉再取末尾，下标就乱了**——这是手写堆最常见的错。

::: quiz 排错 锚点：以为堆是有序数组按下标取第 k 小
:::

## 前 k 大不必排全序

「求前 $k$ 大」也可以用堆。写起来就是一行 `heapq.nlargest(k, data)`，它内部维护一个大小为 $k$ 的最小堆：

```python
import heapq
import random
import time

random.seed(5)
big = [random.randrange(10**9) for _ in range(200000)]
for k in (10, 1000):
    t0 = time.perf_counter(); a = sorted(big, reverse=True)[:k]; t1 = time.perf_counter()
    t2 = time.perf_counter(); b = heapq.nlargest(k, big); t3 = time.perf_counter()
    print(f'k={k:>5}  sorted 取前 k {t1-t0:.4f} 秒   nlargest {t3-t2:.4f} 秒   一致 {a == b}')
```

| $k$ | `sorted` 取前 $k$ | `nlargest` | 一致 |
| --- | --- | --- | --- |
| 10 | 0.0283 秒 | 0.0059 秒 | 是 |
| 1000 | 0.0245 秒 | 0.0051 秒 | 是 |

（本机实测；第二次跑是 0.0250 / 0.0227 与 0.0033 / 0.0036。）

20 万个数里取前 10 大，`nlargest` 快约 5 到 8 倍。说实话：这个差距在日常代码里没什么意义，20 万个数排序也只要 0.03 秒。它值得记住的理由是**$k$ 远小于 $n$ 时不必排全序**，而这个判断在别处会反复用到。

`nsmallest(k, data)` 是同一件事的另一头。

::: quiz 应用 锚点：前 k 大为什么不必排全序
:::

## 最大堆的两种写法

`heapq` 里的「堆」默认指最小堆。要取最大值，传统的做法是**把数取负再放进去**——因为最小的负数对应最大的原数：

```python
import heapq

vals = [5, 3, 8, 1, 9, 2]
neg = [-v for v in vals]
heapq.heapify(neg)
print('负数法弹出:', [-heapq.heappop(neg) for _ in range(len(vals))])

mh = list(vals)
heapq.heapify_max(mh)
print('heapify_max 弹出:', [heapq.heappop_max(mh) for _ in range(len(vals))])
```

```text
负数法弹出: [9, 8, 5, 3, 2, 1]
heapify_max 弹出: [9, 8, 5, 3, 2, 1]
```

两种写法给出同一个序列。第二行用的是 Python 3.14 新增的最大堆 API：`heapify_max`、`heappush_max`、`heappop_max`、`heappushpop_max`、`heapreplace_max` 五个函数，名字都带 `_max` 后缀。

那还要不要学取负的写法？**要**，理由有两条：

- 蓝桥杯的评测机不一定跑 3.14。取负的写法在所有版本上都能用，`_max` 那些函数在 3.13 及更早的版本上会直接 `AttributeError`。
- 取负的写法能用在**元组**上，比如把 `(优先级, 任务号)` 放进堆里按优先级排。这时候要取负的是元组的第一项，写成 `(-优先级, 任务号)` 就行——这类需求比单纯求最大值常见得多。

判断规则很简单：**能用现成的就用现成的，需要交付给不确定版本的环境时用取负。**

::: quiz 应用 锚点：求最大值的取负写法
:::

## 对顶堆求中位数

堆还有一个不显眼但很有用的搭配：**两个堆一起用**，一个存较小的一半（最大堆），一个存较大的一半（最小堆），两者的大小差不超过一。这样中位数就在两个堆顶之间。

**数据流中位数**：数字一个一个到来，每来一个就报出当前所有数的中位数。排序的做法是每来一个重排一次，而对顶堆每来一个只要两次堆操作：

```python
import heapq

def running_median(stream):
    lo = []      # 较小的一半，用负数存成最大堆
    hi = []      # 较大的一半，最小堆
    out = []
    for v in stream:
        heapq.heappush(lo, -v)                    # 先无条件放进 lo
        heapq.heappush(hi, -heapq.heappop(lo))    # lo 里最大的那个挪到 hi
        if len(hi) > len(lo):                     # hi 不能比 lo 长
            heapq.heappush(lo, -heapq.heappop(hi))
        if len(lo) > len(hi):
            out.append(-lo[0])                    # 总数为奇数，lo 顶上是中位数
        else:
            out.append((-lo[0] + hi[0]) / 2)      # 偶数个，取两个堆顶的平均
    return out

stream = [5, 15, 1, 3, 8, 7, 9, 10, 6, 11, 4]
med = running_median(stream)
print('流', stream)
print('中位数', [int(m) if m == int(m) else m for m in med])
```

```text
流 [5, 15, 1, 3, 8, 7, 9, 10, 6, 11, 4]
中位数 [5, 10, 5, 4, 5, 6, 7, 7.5, 7, 7.5, 7]
```

读一遍前几步就能看懂它在维持什么。第一层保证 `lo` 里的每个数都不大于 `hi` 里的每个数（把 `lo` 的最大值挪到 `hi`）；第二层保证两个堆的长度差不超过一。这两条不变式一立住，中位数只能在两个堆顶里出现。

这和第 14 课二分的「循环不变式」是同一套思路：**先说清每一步结束时什么一定成立，再写代码维持它。**

::: quiz 应用 锚点：对顶堆为什么用两个堆
:::

## 这一课用到的判断

- **堆只维护一条性质**：每个结点不大于它的两个孩子。最小值一定在 `h[0]`，但**其余位置没有顺序**，不能按下标取第 $k$ 小。
- **堆在列表里是一棵完全二叉树**：$i$ 的孩子是 $2i+1$ 与 $2i+2$，父结点是 $(i-1)//2$。
- **插入是上浮、弹出是下沉**，每次最多走树高那么多步，所以都是 $O(\log n)$。
- **数据已在手里就用 `heapify`**（$O(n)$），别逐个 `heappush`（$O(n \log n)$）。
- **合并果子**：列表版每轮排序是 $O(n^2 \log n)$，堆版是 $O(n \log n)$；实测 $n = 4000$ 时差 8.8 倍。
- **求最大值**有两种写法：取负（全版本可用，且能用在元组上），或 3.14 的 `heapify_max` 系列。
- **两个堆能维持「中位数在堆顶」**，靠的是「`lo` 全不大于 `hi`」与「长度差不超过一」这两条不变式。

::: practice 上手做 | 三题加一个手写堆

这一课的动手部分落在 lab 里（任务与断言见 [lab/0018-heap-and-priority-queue/](../lab/0018-heap-and-priority-queue/)，做完对照 [lab/solutions/](../lab/solutions/)）。要做的是四件事。

1. 用 `heapq` 把**合并果子**写出来，并与「每轮排序」的列表版在 $n$ 为 1000、2000、4000 上各量一次耗时；确认两边答案一致，把耗时做成一张表。
2. **第 $k$ 大**：给一组数和 $k$，交出第 $k$ 大的值。先用 `sorted` 写一版，再用大小为 $k$ 的最小堆写一版，比较两者在 $k$ 很小与 $k$ 接近 $n$ 时的差别。
3. **数据流中位数**：按上面的对顶堆写法实现，并单独打印每一步之后两个堆的长度与堆顶，用来看那两条不变式是怎么维持的。
4. **手写一个最小堆**的数组实现（`push`、`pop`、`_up`、`_down`），在一组随机数上与 `heapq` 对照弹出序列，必须完全一致。

:::

::: resources
- [Python 官方文档 · heapq](https://docs.python.org/zh-cn/3/library/heapq.html) | `heapify` 是 $O(n)$、`heappush`/`heappop` 是 $O(\log n)$；3.14 新增的 `_max` 系列也在这里
- 《算法导论（第 3 版）》第 6 章 堆排序 | 书 · 堆序性质、上浮与下沉、建堆为什么是线性的
- [Python 官方文档 · 3.14 新变化](https://docs.python.org/zh-cn/3/whatsnew/3.14.html) | `heapify_max` 等五个函数的加入记录（本机跑的是 3.14，可以直接用）
:::

::: related
- [第 17 课：树：会递归的结构](0017-binary-tree-traversal.html)
- [第 3 课：列表与字典的隐藏价格](0003-python-list-dict-cost.html)
:::
