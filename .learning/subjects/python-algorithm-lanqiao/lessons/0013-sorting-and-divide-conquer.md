---
title: 排序：分而治之的样板
goal: 能手写归并排序与快速排序，说清各自的复杂度与最坏情况，并按数据特点在几种排序之间做出选择。
---

## 内置排序之外

Python 的 `sorted` 已经是排序问题的现成答案。取两万个随机整数，手写的归并排序与它各跑一次：

| 写法 | 耗时（本机实测） |
| --- | --- |
| 手写归并排序 | 0.0265 秒 |
| `sorted` | 0.0014 秒 |

`sorted` 快约 19 倍。它由 C 实现，省掉了 Python 层每一次循环与比较的开销。

既然差距这么大，为什么还要手写一遍？因为这两个手写版提供的是一副**骨架**：归并排序的「分而治之」与快速排序的「划分」，在后面的算法里反复出现——求逆序对、求第 $k$ 大的数、按关键字分组、二分的边界收敛，用的都是同一套动作。把它们写熟，是为了在别的题里认出这副骨架。

## 分治的三段式

**分治**（divide and conquer）把一个问题拆成几份更小的同类问题，分别解决之后再合并结果。它由三段组成：

| 段 | 做什么 | 排序里的对应 |
| --- | --- | --- |
| 分 | 把问题切成规模更小的同类问题 | 把数组从中间切成两半 |
| 治 | 递归地解决这些子问题 | 对两半分别排序 |
| 合 | 把子问题的答案拼回原问题的答案 | 把两个有序段合并成一个有序段 |

三段里的第三段最容易被忽略。归并排序之所以能排好，靠的是「合并两个有序数组」这个动作本身非常便宜：两段各自有序时，只要不断比较两段当前的头部，取走较小的一个，一趟就能拼完。**分**与**治**把问题变小，**合**才让结果回到原规模。

这一课要写三个函数，对应三段：`merge`（合）、`merge_sort`（分与治）、`partition`（快排的分）。

::: quiz 理解 锚点：分治三段式里合这一步的作用
:::

## 归并排序

```python
def merge(left, right):
    out = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out

def merge_sort(a):
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    return merge(merge_sort(a[:mid]), merge_sort(a[mid:]))
```

`merge_sort` 的基例是 `len(a) <= 1`：长度为 0 或 1 的数组已经有序，直接返回。递归关系是把数组切成两半，各自排好之后合并。这与上一课那三个要素一一对应。

拿两万个随机整数验证一次：

```python
import random
import time

def time_it(f, reps=3):
    best = 1e9
    for _ in range(reps):
        t0 = time.perf_counter()
        f()
        t1 = time.perf_counter()
        if t1 - t0 < best:
            best = t1 - t0
    return best

random.seed(7)
d = [random.randrange(1000) for _ in range(20000)]

def run_merge():
    return merge_sort(d)

print('与 sorted 一致', merge_sort(d) == sorted(d))
print(f'归并 {time_it(run_merge, 1):.4f} 秒')
```

```text
与 sorted 一致 True
归并 0.0265 秒
```

`merge` 里有三处细节，写错任何一处结果都会错位：

- `while` 的条件是 `i < len(left) and j < len(right)`，两个都没走完时才能比较。写成 `or` 会在某一段走完后继续取下标，读到越界的位置。
- 比较用 `<=`。用 `<` 时，两段头部相等的情况下会先取右边那个，稳定排序的性质就丢了（这一课后面会讲稳定性）。
- 收尾的两行 `out.extend(...)` 不能省。`while` 停下来时，总有一段还剩几个元素，它们已经有序且都比 `out` 里的大，直接接在后面即可。

::: warn 合并时的下标错位不容易看出来
`while` 里少写一个条件、或者把 `i += 1` 与 `j += 1` 写反，结果往往只是「差不多对」——大部分位置正确，少数重复值或边界值跑到错误的位置。写完先拿一组有小规模、有重复值的数据（例如十个元素、其中三个相同）对一次，再看大规模。
:::

::: quiz 排错 锚点：归并合并时下标走错导致结果错位
:::

## 归并的深度与代价

上一课讲过递归深度受解释器上限约束。归并排序的深度是多少？把每一层的切分走一遍就能数出来：

```python
deepest = 0

def depth_of(n, d=1):
    global deepest
    if d > deepest:
        deepest = d
    if n <= 1:
        return
    depth_of(n // 2, d + 1)
    depth_of(n - n // 2, d + 1)

for n in (8, 1000, 32768, 100000):
    deepest = 0
    depth_of(n)
    print(f'n={n:>6} 最大深度 {deepest}')
```

```text
n=     8 最大深度 4
n=  1000 最大深度 11
n= 32768 最大深度 16
n=100000 最大深度 18
```

每切一层，规模减半，所以深度是 $\lceil \log_2 n \rceil + 1$。$n = 100000$ 时只有 18 层，离上一课那个 1000 的上限极远。

再看时间。每一层都要把所有 $n$ 个元素搬一遍，共 $\lceil \log_2 n \rceil + 1$ 层，所以总代价是 $O(n \log n)$。合并本身是线性的，这一点是归并排序效率的来源。

::: quiz 理解 锚点：归并排序的递归深度为什么是 O(log n)
:::

## 快速排序与划分

快速排序走的是另一条路：它不合并，而是选一个**主元**，把数组分成「比主元小的」与「不小于主元的」两段，再对两段分别递归。分完就已经确定主元的最终位置，不需要合并这一步。

```python
def partition(a, lo, hi):
    p = a[lo]
    i = lo
    for j in range(lo + 1, hi + 1):
        if a[j] < p:
            i += 1
            a[i], a[j] = a[j], a[i]
    a[lo], a[i] = a[i], a[lo]
    return i

def quick_sort(a, lo=0, hi=None):
    if hi is None:
        hi = len(a) - 1
    if lo >= hi:
        return a
    k = partition(a, lo, hi)
    quick_sort(a, lo, k - 1)
    quick_sort(a, k + 1, hi)
    return a
```

`i` 的含义是「已确定小于主元的那一段的末尾下标」。扫描一遍 `j`，每次遇到比主元小的元素，就把 `i` 往前推一格，并把它换到 `i` 这个位置。扫描结束后，`a[lo]` 与 `a[i]` 交换，主元落到 `i` 上，它的左边全比它小、右边全不比它小。函数返回 `i`，递归的两段就以 `i` 为界。

## 划分的逐步过程

取 `a = [3, 1, 4, 1, 5, 9, 2]`，主元是开头的 3，把划分过程逐步打出来：

```python
a = [3, 1, 4, 1, 5, 9, 2]
p = a[0]
i = 0
print('主元 3，初始', a)
for j in range(1, len(a)):
    v = a[j]
    if v < p:
        i += 1
        a[i], a[j] = a[j], a[i]
        print(f'j={j} 读到 {v} < 3，i 增到 {i}，交换后', a)
    else:
        print(f'j={j} 读到 {v} >= 3，i 停在 {i}，不动')
a[0], a[i] = a[i], a[0]
print('主元落位到下标', i, a)
```

```text
主元 3，初始 [3, 1, 4, 1, 5, 9, 2]
j=1 读到 1 < 3，i 增到 1，交换后 [3, 1, 4, 1, 5, 9, 2]
j=2 读到 4 >= 3，i 停在 1，不动
j=3 读到 1 < 3，i 增到 2，交换后 [3, 1, 1, 4, 5, 9, 2]
j=4 读到 5 >= 3，i 停在 2，不动
j=5 读到 9 >= 3，i 停在 2，不动
j=6 读到 2 < 3，i 增到 3，交换后 [3, 1, 1, 2, 5, 9, 4]
主元落位到下标 3 [2, 1, 1, 3, 5, 9, 4]
```

一趟扫描结束，主元 3 落在下标 3，左边的 `[2, 1, 1]` 全小于它，右边的 `[5, 9, 4]` 全不小于它。接着对这两段各做一次同样的事，整个数组就排好了。

这一步的代价是 $O(n)$：`j` 从 `lo + 1` 走到 `hi`，每个元素最多被交换一次。

## 有序数据上的退化

快排的代价取决于划分得均不均匀。若每次主元都恰好落在中间，深度仍是 $O(\log n)$，总代价 $O(n \log n)$；若每次主元都落在端点，两段变成「空的」与「剩下全部」，深度就退化成 $O(n)$。

用上面那个「永远取开头作主元」的版本，喂一组已经排好的数据：

| $n$ | 耗时（本机实测） | 相邻两行的倍率 |
| --- | --- | --- |
| 400 | 0.002109 秒 | — |
| 800 | 0.007990 秒 | 3.79 |
| 1600 | 0.027468 秒 | 3.44 |
| 3200 | 0.110224 秒 | 4.01 |

规模翻倍、耗时涨约四倍，这是平方级的形状。规模再大一点，代价不只是变慢：

```text
已有序 n=1600 固定主元 -> RecursionError: maximum recursion depth exceeded
```

深度涨到 $n$，撞上了上一课那个 1000 的上限。上一课说过「深度随规模线性增长时要考虑改写」，这里正好是一个实例。

修法是把主元选得随机一点，让划分不容易总是落在端点上：

```python
def quick_sort_random(a, lo=0, hi=None):
    if hi is None:
        hi = len(a) - 1
    if lo >= hi:
        return a
    m = random.randrange(lo, hi + 1)
    a[lo], a[m] = a[m], a[lo]
    k = partition(a, lo, hi)
    quick_sort_random(a, lo, k - 1)
    quick_sort_random(a, k + 1, hi)
    return a
```

同一组已有序的数据，换成随机主元之后：$n = 1600$ 时 0.001023 秒（固定主元是 0.027468 秒，差约 27 倍），$n = 20000$ 时 0.018757 秒。

::: warn 已有序的数据比你想象的常见
输入是排好序的、逆序的、或者「几乎有序只有几个位置错位」，这几种在真实题目里都常出现。快排的固定主元版在这几种输入上都会退化，**测性能时一定要专门造一组有序数据**，只用随机数据测会把这个坑藏起来。
:::

::: quiz 排错 锚点：快排对有序数据退化到平方级
:::

::: quiz 改造 锚点：用随机主元修掉快排的退化
:::

## 计数排序

前两种排序都靠比较元素大小来决定次序，这类算法的时间下界是 $O(n \log n)$。若数据的取值落在一个小范围里，可以换一种完全不比较的做法。

**计数排序**先数出每个值出现了几次，再按值的顺序把它们写回：

```python
def counting_sort(a, maxv):
    cnt = [0] * (maxv + 1)
    for x in a:
        cnt[x] += 1
    out = []
    for v in range(maxv + 1):
        out.extend([v] * cnt[v])
    return out
```

两万个取值在 $0$ 到 $999$ 之间的整数，测一次：

```python
d4 = [random.randrange(1000) for _ in range(20000)]
print('结果一致', counting_sort(d4, 999) == sorted(d4))

def run_count():
    return counting_sort(d4, 999)

def run_sorted():
    return sorted(d4)

print(f'计数 {time_it(run_count, 1):.4f} 秒  sorted {time_it(run_sorted):.4f} 秒')
```

本机跑出来是：

| 写法 | 耗时（本机实测） |
| --- | --- |
| 计数排序 | 0.0008 秒 |
| `sorted` | 0.0016 秒 |

计数排序比内置的 `sorted` 还快一倍。它的代价是 $O(n + V)$，其中 $V$ 是值域的宽度；这里 $V = 1000$，与 $n$ 同量级。适用条件是两条：**取值是整数（或能一一对应到整数）**，且**值域不比 $n$ 大多少**。值域有 $10^9$ 那么宽时，那张计数表就开不出来了。

::: quiz 应用 锚点：按值域选择计数排序
:::

## 键与稳定排序

题面常常要求「按某个关键字排序」，而关键字不一定是元素本身。`sorted` 用一个 `key` 函数来指定取哪个字段：

```python
pairs = [(1, 'a'), (0, 'x'), (1, 'b'), (0, 'y'), (1, 'c')]

def first(x):
    return x[0]

print(sorted(pairs, key=first))
```

```text
[(0, 'x'), (0, 'y'), (1, 'a'), (1, 'b'), (1, 'c')]
```

看两组关键字相同的元素：`(0, 'x')` 在 `(0, 'y')` 前面，`(1, 'a')`、`(1, 'b')`、`(1, 'c')` 保持着原来在列表里的先后。这种「关键字相同的元素保持原有相对次序」的性质叫**稳定**。Python 的 `sorted` 与 `list.sort` 都是稳定的。

`key` 还有一个容易忽略的性质：**每个元素只调用一次**。`sorted` 的内部做法是先把每个元素的键算出来存到一边，按键排序，再去掉键取回原元素；官方文档把这套做法叫「装饰 - 排序 - 去装饰」（decorate-sort-undecorate）。把调用次数数出来：

```python
calls = 0

def counted(x):
    global calls
    calls += 1
    return x[0]

data = [(random.randrange(100), i) for i in range(2000)]

calls = 0
sorted(data, key=counted)
print('sorted(key=) 调用 key', calls, '次')
```

```text
sorted(key=) 调用 key 2000 次
```

2000 个元素调用 2000 次，正好是 $n$。

把手写排序写成「在比较里调用 `key`」的版本，这一条就破了：每次比较都要算两个键，而一次排序要比较约 $n \log n$ 次。同样两千个元素，手写归并版的 `key` 被调用 **38738 次**（本机实测），是前者的约 19 倍；两个版本的时间是 0.000183 秒与 0.003672 秒，差约 20 倍。

所以「内置 `sorted` 永远比手写快」这句话在简单数据上成立，而当 `key` 是一个开销不小的函数时，手写版若把 `key` 放进比较里，两者都会变慢，手写版还会慢得更多。若确实要手写排序又需要 `key`，就先把键算好存到一边——`sorted` 快在这里，仿照它的做法才有意义。

另有一处边界要留意：`sorted` 要求元素之间能比较。字典与集合这类元素之间没有大小关系，直接对它们排序会报 `TypeError`，要改成按某个字段排，也就是给出 `key`。

::: quiz 排错 锚点：以为内置 sorted 永远比手写快
:::

## 这一课用到的判断

- **手写排序的价值在骨架**：分治的三段（分、治、合）与划分这两个动作，在后面的题里反复出现。日常要排序直接用 `sorted`。
- **分治的第三段不能省**：合并两个有序段是归并排序效率的来源，代价 $O(n)$。
- **归并的深度是 $O(\log n)$**，远离递归上限；**快排退化时深度是 $O(n)$**，会直接撞上限。
- **快排的代价取决于划分是否均匀**。已有序、逆序、几乎有序的输入会让固定主元版退化成 $O(n^2)$，测性能时必须专门造这类数据。
- **计数排序不受 $O(n \log n)$ 下界约束**，代价 $O(n + V)$，前提是值为整数且值域不大。
- **比较类排序的下界是 $O(n \log n)$**，归并与快排的均摊代价已经达到这个下界。
- **Python 的排序是稳定的**，且 `key` 对每个元素只调用一次（装饰 - 排序 - 去装饰）。要手写排序又带 `key`，先把键算好。

::: practice 上手做 | 手写三种排序并对照

这一课的动手部分落在 lab 里（任务与断言见 [lab/0013-sorting-and-divide-conquer/](../lab/0013-sorting-and-divide-conquer/)，做完对照 [lab/solutions/](../lab/solutions/)）。要做的是四件事。

1. 把 `merge`、`merge_sort`、`partition`、`quick_sort`、`counting_sort` 五个函数抄进一个文件，用 `random` 造几组数据（随机、已有序、逆序、含大量重复值），每一组都确认手写版的结果与 `sorted` 逐字一致。
2. 造一张耗时表：$n$ 取 400、800、1600、3200，每档分别跑归并、固定主元快排、随机主元快排、`sorted`，看每一列的相邻两行是几倍关系，并指出哪一列的形状不是 $n \log n$。
3. 把已有序数据那一组单独留出来，用固定主元快排跑一次，把 `RecursionError` 的现场抄下来；再换成随机主元跑，记下两次的耗时比。
4. 把数据换成 $0$ 到 $999$ 之间的整数，比较计数排序与 `sorted` 的耗时；再把值域改成 $0$ 到 $10^9$，说明计数排序为什么不能用了，实际跑一次看它会怎样。

:::

::: resources
- [Python 官方文档 · 排序指南](https://docs.python.org/3/howto/sorting.html) | 官方文档 · `key` 只调用一次、稳定性、装饰 - 排序 - 去装饰、部分排序
- [Python 官方文档 · sorted](https://docs.python.org/3/library/functions.html#sorted) | 官方文档 · `sorted` 的签名与稳定性保证
- 《算法（第 4 版）》第 2 章 排序 | 书 · 归并与快排的推导与图示；当参考书查
:::

::: related
- [上一课：递归：函数调用自己](0012-recursion-and-stack.html)
- [第 3 课：列表与字典的隐藏价格](0003-python-list-dict-cost.html)
:::
