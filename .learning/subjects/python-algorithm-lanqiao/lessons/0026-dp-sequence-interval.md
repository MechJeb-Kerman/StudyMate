---
title: 序列与区间的状态设计
goal: 能为序列题与区间题各设计出状态定义，写清转移方程与枚举顺序，并用暴力版对拍。
---

## 背包的状态是给的

上一课的背包，状态几乎是递到手上的：**「容量」这个维度题目直接给了你**，你只要把物品一件件盖上去。

序列题不一样。题目只给你一个数组或一个字符串，**状态得自己设计**：

- 「前 $i$ 个元素的最大 XXX」？
- 「**以第 $i$ 个元素结尾**的最大 XXX」？
- 「两个序列的**前 $i$ 个配前 $j$ 个**」？

这三句话看着差不多，选错一句就写不出转移方程——**卡住的地方几乎都在这里，不在代码**。

这一课练四条套路，每条都先写状态定义再动手。

::: quiz 理解 锚点：序列题卡住通常卡在状态定义还是代码实现
:::

## 以 i 结尾：最长递增子序列

**最长递增子序列**（LIS）：从数组里挑出一些元素，保持原来的先后顺序，让它严格递增，问最多能挑几个。挑出来的**不必连续**。

先试一个想当然的状态：「前 $i$ 个元素里的最长递增子序列长度」。它坏在**接不上**——算前 $i$ 个的时候，你不知道那条子序列的结尾是几，就没办法判断 $a_i$ 能不能接在后面。

所以状态要**带上结尾**：

$$dp[i] = \text{以 } a_i \text{ 结尾的最长递增子序列长度}$$

这一下就能转移了：往前找一个比 $a_i$ 小的 $a_j$，接在它后面。

$$dp[i] = 1 + \max\{\,dp[j] \mid j < i,\ a_j < a_i\,\}$$

没有这样的 $j$ 时就是 1（自己单独成一条）。

```python
def lis_dp(a):
    """dp[i] = 以 a[i] 结尾的最长递增子序列长度。"""
    n = len(a)
    if n == 0:
        return 0, []
    dp = [1] * n
    for i in range(1, n):
        for j in range(i):
            if a[j] < a[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
    return max(dp), dp


A = [10, 9, 2, 5, 3, 7, 101, 18]
L, dp = lis_dp(A)
print(f'   序列 {A}')
print(f'   dp（以每个位置结尾的长度）: {dp}')
print(f'   最长递增子序列的长度: {L}')
```

```text
   序列 [10, 9, 2, 5, 3, 7, 101, 18]
   dp（以每个位置结尾的长度）: [1, 1, 1, 2, 2, 3, 4, 4]
   最长递增子序列的长度: 4
```

答案不是 `dp` 的最后一个值，是 **`max(dp)`**——最长的那条不一定结尾在最后一个位置。这里 `dp[7] = 4`、`dp[6] = 4`，恰好并列。

::: quiz 排错 锚点：LIS 的状态为什么不定义成前 i 个元素里的最长长度
:::

## 二分版与它的 tails

LIS 还有一版 $O(n \log n)$ 的写法，用 `bisect`：

```python
import bisect


def lis_bisect(a):
    """tails[k] = 所有长度为 k+1 的递增子序列里，结尾最小的那个值。"""
    tails = []
    for x in a:
        k = bisect.bisect_left(tails, x)
        if k == len(tails):
            tails.append(x)
        else:
            tails[k] = x
    return len(tails), tails


L2, tails = lis_bisect(A)
print(f'   序列 {A}')
print(f'   长度: {L2}')
print(f'   tails 数组: {tails}')
print(f'   两版长度一致? {L == L2}')
```

```text
   序列 [10, 9, 2, 5, 3, 7, 101, 18]
   长度: 4
   tails 数组: [2, 3, 7, 18]
   两版长度一致? True
```

`tails[k]` 的含义是「**所有长度为 $k+1$ 的递增子序列里，结尾最小的那个值**」。维护它的理由是：结尾越小，后面越容易接得上，所以每个长度只要留最小的那个结尾就够了。

**但 `tails` 不保证是一条子序列。** 这一课最值得记住的一件事故在这里：

```python
def is_subsequence(sub, a):
    """sub 是不是 a 的子序列（保持先后顺序，不必连续）。"""
    it = iter(a)
    return all(x in it for x in sub)


def lis_sequence(a):
    """老老实实从 dp 把一条真正的最长递增子序列恢复出来。"""
    n = len(a)
    dp = [1] * n
    prev = [-1] * n
    for i in range(1, n):
        for j in range(i):
            if a[j] < a[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j
    best = max(range(n), key=lambda i: dp[i])
    out = []
    while best != -1:
        out.append(a[best])
        best = prev[best]
    return out[::-1]


real = lis_sequence(A)
print(f'   序列 {A}')
print(f'   dp 版回溯出的一条最长递增子序列: {real}')
print(f'   二分版的 tails               : {tails}')
print(f'   两者相同吗: {real == tails}')
print(f'   tails 是原序列的子序列吗: {is_subsequence(tails, A)}')
```

```text
   序列 [10, 9, 2, 5, 3, 7, 101, 18]
   dp 版回溯出的一条最长递增子序列: [2, 5, 7, 101]
   二分版的 tails               : [2, 3, 7, 18]
   两者相同吗: False
   tails 是原序列的子序列吗: True
```

**长度一样，元素完全对不上。** 但这里有一句很容易脱口而出的话要拦住：`[2, 3, 7, 18]` **在这一组数据上恰好是原序列的一条合法子序列**（下标 2、4、5、7），而且严格递增——它自己就是一条最长递增子序列，只是跟 `dp` 回溯出来的那条**不是同一条**。

所以「`tails` 不能直接当答案」的理由**不是**「它不是子序列」，而是这两条：

- 它**不保证**是子序列；
- 就算是，也**不保证**是你要的那一条（题目可能要求字典序最小的那条）。

换一组数据就看得见第一条。`[2, 3, 1]` 里的 `1` 最后才出现，却把 `tails` 的第一格从 `2` 换成了 `1`：

```python
CASE = [2, 3, 1]
_, t = lis_bisect(CASE)
print(f'   序列 {CASE}')
print(f'   tails = {t}')
print(f'   tails 是原序列的子序列吗: {is_subsequence(t, CASE)}')
```

```text
   序列 [2, 3, 1]
   tails = [1, 3]
   tails 是原序列的子序列吗: False
```

`[1, 3]` 里 `1` 排在 `3` 前面，可原序列里 `1` 在 `3` **后面**。这不是精心构造的特例：

```python
import random

random.seed(4)
bad = 0
trials = 2000
first = None
for _ in range(trials):
    n = random.randint(3, 12)
    a = [random.randint(1, 15) for _ in range(n)]
    _, t = lis_bisect(a)
    if not is_subsequence(t, a):
        bad += 1
        if first is None:
            first = (a, t)
print(f'   {trials} 组随机数据里，tails 不是原序列子序列的有 {bad} 组')
print(f'   第一组: 序列 {first[0]}，tails = {first[1]}')
```

```text
   2000 组随机数据里，tails 不是原序列子序列的有 902 组
   第一组: 序列 [5, 2, 12, 7, 8, 3]，tails = [2, 3, 8]
```

**接近一半。** 所以这件事不能指望「碰巧对」——拿 `tails` 当答案，是拿一个约一半概率出错的东西当答案。

所以：**要长度就用二分版；要那条子序列本身，就得用 $O(n^2)$ 的 `dp` 加一个 `prev` 数组回溯。** 两版的长度是一样的：

```python
import random
random.seed(3)
bad = 0
trials = 500
for _ in range(trials):
    n = random.randint(0, 40)
    a = [random.randint(1, 30) for _ in range(n)]
    if lis_dp(a)[0] != lis_bisect(a)[0]:
        bad += 1
print(f'   {trials} 组随机数据（长度 0~40、元素 1~30）：两版长度不一致的有 {bad} 组')
dup = [5, 5, 5, 5]
print(f'   全相同元素的例子 {dup}: DP 版给 {lis_dp(dup)[0]}，二分版给 {lis_bisect(dup)[0]}')
```

```text
   500 组随机数据（长度 0~40、元素 1~30）：两版长度不一致的有 0 组
   全相同元素的例子 [5, 5, 5, 5]: DP 版给 1，二分版给 1
```

「长度」这件事上两版**从不出错**，所以混用导致答案错，错的一定是**「你问的是长度还是序列」**这一层——不是长度算错了，是拿一个记账数组当答案交上去了。

::: warn
「严格递增」和「不下降」是两个不同的题。`bisect_left` 遇到相等的值会**替换**，得到的是严格递增；换成 `bisect_right` 就变成不下降。题目说「严格」还是「不下降」，先看清再写。
:::

::: quiz 应用 锚点：要输出那条最长递增子序列本身时该用哪一版
:::

## 两维状态：最长公共子序列

**最长公共子序列**（LCS）：两个字符串，找出同时是二者子序列的最长那个，问长度。

这次要**同时盯住两个字符串**，所以状态是两维的：

$$dp[i][j] = s \text{ 的前 } i \text{ 个字符与 } t \text{ 的前 } j \text{ 个字符的 LCS 长度}$$

转移分两种：

- 末尾字符相同（$s_{i-1} = t_{j-1}$）：**这一对可以配起来**，答案就是 $dp[i-1][j-1] + 1$；
- 不同：至少有一个字符用不上，取 $\max(dp[i-1][j],\ dp[i][j-1])$。

```python
def lcs(s, t):
    """dp[i][j] = s 的前 i 个字符与 t 的前 j 个字符的最长公共子序列长度。"""
    n, m = len(s), len(t)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m], dp


S1, S2 = 'ABCBDAB', 'BDCABA'
L3, table = lcs(S1, S2)
print(f'   s = {S1}    t = {S2}')
print(f'   最长公共子序列长度: {L3}')
print(f'   dp 表（s 往下、t 往右，都是前 i / 前 j 个字符）：')
print('        ""  ' + '  '.join(S2))
for i, row in enumerate(table):
    tag = '"' if i == 0 else S1[i - 1]
    print(f'   {tag:>3}  ' + '  '.join('%2d' % v for v in row))
```

```text
   s = ABCBDAB    t = BDCABA
   最长公共子序列长度: 4
   dp 表（s 往下、t 往右，都是前 i / 前 j 个字符）：
        ""  B  D  C  A  B  A
     "   0   0   0   0   0   0   0
     A   0   0   0   0   1   1   1
     B   0   1   1   1   1   2   2
     C   0   1   1   2   2   2   2
     B   0   1   1   2   2   3   3
     D   0   1   2   2   2   3   3
     A   0   1   2   2   3   3   4
     B   0   1   2   2   3   4   4
```

**把这张表打印出来，是这一课最省事的自查手段。** 三个规矩一眼可查：

- 第一行和第一列全是 0（空串配任何串，公共子序列长度都是 0）；
- 每一格只依赖**左边、上边、左上**三个方向；
- 表是**逐行逐列**填的，所以「前 $i$ 前 $j$」这种定义天然符合递推顺序——不需要像区间 DP 那样操心枚举顺序。

::: quiz 应用 锚点：LCS 的表里每一格依赖哪三个方向
:::

## 区间 DP：最长回文子序列

**最长回文子序列**（LPS）：从一个字符串里挑出一些字符（保持顺序），让它是个回文，问最多挑几个。

这次的状态是**一个区间**：

$$dp[i][j] = s[i..j] \text{ 这段里的最长回文子序列长度}$$

转移看两头：

- $s_i = s_j$：两头能配上，$dp[i][j] = dp[i+1][j-1] + 2$；
- 不同：至少丢一头，$dp[i][j] = \max(dp[i+1][j],\ dp[i][j-1])$。

```python
def lps(s):
    """dp[i][j] = s[i..j] 里最长回文子序列的长度。"""
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1
    for length in range(2, n + 1):                 # 小区间先算
        for i in range(0, n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]


for s in ('character', 'abba', 'abcda', 'aaaa'):
    print(f'   "{s}" 的最长回文子序列长度: {lps(s)}')
```

```text
   "character" 的最长回文子序列长度: 5
   "abba" 的最长回文子序列长度: 4
   "abcda" 的最长回文子序列长度: 3
   "aaaa" 的最长回文子序列长度: 4
```

注意 `dp[i][j]` 依赖的是 **$dp[i+1][\cdot]$ 和 $dp[\cdot][j-1]$**——**比它更小的区间**。所以填表顺序不能随便：**必须先算短的区间，再算长的。**

这就是区间 DP 跟 LCS 最大的不同：LCS 的依赖方向（左、上、左上）天然对应逐行逐列，而区间 DP 的依赖是「更短的区间」，**必须显式按区间长度从小到大枚举**。

::: quiz 理解 锚点：区间 DP 为什么必须先算短区间
:::

## 断点枚举：石子合并

**石子合并**：一排石子堆，每次只能把**相邻**两堆合成一堆，代价是合并后那一堆的重量（也就是这两堆重量之和），问把所有石子合成一堆的**最小总代价**。

状态还是区间：

$$dp[i][j] = \text{把第 } i \text{ 堆到第 } j \text{ 堆合成一堆的最小代价}$$

转移要**枚举最后那一次合并是在哪里断开的**：

$$dp[i][j] = \min_{i \le k < j}\bigl(dp[i][k] + dp[k+1][j]\bigr) + \text{sum}(i..j)$$

最后加的那一项 $\text{sum}(i..j)$ 是**这次合并本身的代价**：不管前面怎么合，第 $i$ 到第 $j$ 堆合成一堆，这一下必然要把区间内所有石子清点一遍。用前缀和可以 $O(1)$ 拿到。

```python
from functools import lru_cache


def stone_dp(a, order='asc'):
    """dp[i][j] = 把第 i 堆到第 j 堆合成一堆的最小代价。"""
    n = len(a)
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] + a[i]
    dp = [[0] * n for _ in range(n)]
    big = float('inf')
    lengths = range(2, n + 1) if order == 'asc' else range(n, 1, -1)
    for length in lengths:
        for i in range(0, n - length + 1):
            j = i + length - 1
            best = big
            for k in range(i, j):
                cand = dp[i][k] + dp[k + 1][j]
                if cand < best:
                    best = cand
            dp[i][j] = best + pre[j + 1] - pre[i]
    return dp[0][n - 1], dp


def stone_brute(a):
    """枚举每一次合并的是相邻哪两堆。"""

    @lru_cache(maxsize=None)
    def go(t):
        if len(t) == 1:
            return 0
        best = float('inf')
        for k in range(len(t) - 1):
            cost = t[k] + t[k + 1]
            nxt = t[:k] + (cost,) + t[k + 2:]
            best = min(best, cost + go(nxt))
        return best

    return go(tuple(a))


ST = [4, 1, 2, 3]
print(f'   石子 {ST}')
print(f'   区间 DP（长度从小到大）: {stone_dp(ST)[0]}')
print(f'   暴力枚举所有合并顺序  : {stone_brute(ST)}')
ST2 = [3, 4, 5, 6, 7]
print(f'   石子 {ST2}: 区间 DP {stone_dp(ST2)[0]}，暴力 {stone_brute(ST2)}')
```

```text
   石子 [4, 1, 2, 3]
   区间 DP（长度从小到大）: 19
   暴力枚举所有合并顺序  : 19
   石子 [3, 4, 5, 6, 7]: 区间 DP 57，暴力 57
```

`[4, 1, 2, 3]` 的 19 是这么来的：先合 1 和 2 成 3（代价 3，剩 4、3、3），再合两个 3 成 6（代价 6，剩 4、6），最后合成 10（代价 10）——3 + 6 + 10 = **19**。

::: quiz 应用 锚点：石子合并的转移方程为什么要加区间和那一项
:::

## 枚举顺序写反会怎样

把 `range(2, n+1)` 改成 `range(n, 1, -1)`——**区间长度从大到小枚举**，其他一个字不动：

```python
for st in ([4, 1, 2, 3], [3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6]):
    asc = stone_dp(st, 'asc')[0]
    desc = stone_dp(st, 'desc')[0]
    print(f'   {st}: 长度从小到大 {asc}，从大到小 {desc}')
```

```text
   [4, 1, 2, 3]: 长度从小到大 19，从大到小 10
   [3, 4, 5, 6, 7]: 长度从小到大 57，从大到小 25
   [1, 2, 3, 4, 5, 6]: 长度从小到大 51，从大到小 21
```

答案**偏小**，而且小得离谱。

原因不绕：长度从大到小枚举时，算长区间要用到的短区间**还没被算过**，`dp[i][k]` 和 `dp[k+1][j]` 都还是初始的 0。于是转移只加上了「这次合并的代价」，**前面所有合并的代价全被漏掉了**。区间越长漏得越多——57 变 25、51 变 21，正是这个道理。

上一课背包写错方向时答案是**偏大**的（同一件物品被拿了多次）；这里写错顺序答案是**偏小**的（有些代价没被算进去）。两次都说明同一件事：

::: tip
**答案偏离的方向会告诉你错在哪一类。** 背包偏大 → 用掉了不存在的资源；区间 DP 偏小 → 少算了本该付出的代价。看到答案不对，先问「它错向了哪边」，比从头读代码有效得多。
:::

::: quiz 排错 锚点：区间 DP 长度从大到小枚举，答案会偏大还是偏小
:::

## 随机对拍

区间 DP 的枚举顺序、断点范围、前缀和边界，都是「看一眼看不出错」的地方。对拍照旧是最省事的办法：

```python
import random
random.seed(9)
bad_asc = bad_desc = 0
trials = 200
for _ in range(trials):
    n = random.randint(1, 7)
    a = [random.randint(1, 20) for _ in range(n)]
    want = stone_brute(a)
    if stone_dp(a, 'asc')[0] != want:
        bad_asc += 1
    if stone_dp(a, 'desc')[0] != want:
        bad_desc += 1
print(f'   {trials} 组随机石子堆（1~7 堆）：')
print(f'      长度从小到大与暴力不一致的有 {bad_asc} 组')
print(f'      长度从大到小与暴力不一致的有 {bad_desc} 组')
```

```text
   200 组随机石子堆（1~7 堆）：
      长度从小到大与暴力不一致的有 0 组
      长度从大到小与暴力不一致的有 137 组
```

**从小到大 0 组错，从大到小 137 组错**——200 组里错了三分之二还多。

序列题的暴力版比背包更好写：石子合并直接递归枚举「这次合哪两堆」，LIS 直接枚举子集。**只要暴力版能写出来，就没有对拍不出来的序列题。**

::: quiz 应用 锚点：为什么序列题的暴力版比背包更容易写出来
:::

## 这一课用到的判断

- **背包的状态是给的，序列题的状态要自己设计。** 卡住的地方几乎都在状态定义，不在代码。
- **LIS 的状态必须「以 $i$ 结尾」**。「前 $i$ 个里的最长长度」接不上——算前 $i$ 个时不知道那条子序列结尾是几，没法判断 $a_i$ 能否接上。
- **答案是 `max(dp)` 而不是 `dp[n-1]`**：最长的那条不一定结尾在最后。
- **`tails` 只是记账数组，不能当答案。** `tails[k]` 记的是「长度为 $k+1$ 的递增子序列里最小的那个结尾」。实测 `tails = [2, 3, 7, 18]` 与 `dp` 回溯出的 `[2, 5, 7, 101]`——**长度一样、元素完全对不上**。它甚至**不保证是子序列**：`[2, 3, 1]` 的 `tails` 是 `[1, 3]`，可 `1` 在原序列里排在 `3` 后面；2000 组随机数据里有 **902 组** 是这样。要长度用二分版，要序列本身用 `dp` 加 `prev` 回溯。
- **别把「这组碰巧对」当成规律。** `[10,9,2,5,3,7,101,18]` 上 `tails` 恰好是一条合法子序列，很容易由此得出「它就是答案」——换一组就塌。判断一个写法能不能用，要看它**有没有保证**，不看它在样例上跑没跑对。
- **两版的长度从不出错**：500 组随机数据上不一致 0 组。所以混用出的错，一定出在「你问的是长度还是序列」。
- **`bisect_left` 是严格递增，`bisect_right` 是不下降**，先看清题目要哪个。
- **LCS 的状态是「两个前缀」**：$dp[i][j]$ 只依赖左边、上边、左上三个方向，逐行逐列填即可。
- **区间 DP 的状态是一个区间**：$dp[i][j]$ 依赖的是**更短的区间**`dp[i+1][j-1]`、`dp[i+1][j]`、`dp[i][j-1]`，所以**必须按区间长度从小到大枚举**。
- **石子合并的转移要枚举断点 $k$**，末尾再加上区间和——那是这次合并本身的代价，不管前面怎么合都躲不掉。
- **枚举顺序写反的后果是答案偏小**：短区间还没算，`dp` 里还是 0，前面所有合并的代价全被漏掉。实测 `[3,4,5,6,7]` 由 57 变 25、`[1,2,3,4,5,6]` 由 51 变 21；200 组对拍从大到小错 **137** 组、从小到大错 **0** 组。
- **答案偏离的方向指向错的类型**：偏小 → 少算了代价；偏大（如上一课的背包）→ 用掉了不存在的资源。
- **打印状态表自查**：LCS 的表第一行第一列全是 0；石子合并的表主对角线全是 0。表本身不对，转移一定不对。

::: practice 上手做 | 四道题先写状态再写代码

这一课配了动手练习，在 [lab/0026-dp-sequence-interval/](../lab/0026-dp-sequence-interval/)。

1. `task1_lis.py`：写 $O(n^2)$ 的 DP 版与 $O(n \log n)$ 的二分版，并实现「恢复一条真正的最长递增子序列」。
2. `task2_lcs.py`：写最长公共子序列，并把整张状态表打印出来。
3. `task3_palindrome.py`：写最长回文子序列，注意按区间长度从小到大枚举。
4. `task4_stone.py`：写石子合并，跟暴力版对拍；再故意把长度顺序写反，观察答案偏小。

跑法、判分在读什么、卡住了先看哪里，都写在该目录的说明与 `../lab/README.md` 里。写完想对照，看 [lab/solutions/](../lab/solutions/)。

:::

::: resources
- [洛谷题单：动态规划的线性与区间模型](https://www.luogu.com.cn/training/106) | 题单 · 从线性 DP 到区间 DP 的成体系练习
- [OI Wiki：动态规划基础](https://oi-wiki.org/dp/basic/) | 文章 · 状态设计与转移方程的一般方法
- [第 25 课：背包：选与不选](0025-dp-knapsack.html) | 上一课讲清了「遍历方向」，这一课把状态设计往前推一步
- [第 24 课：动态规划：把重复计算记下来](0024-dp-from-recursion.html) | 记忆化、递推与状态定义的基础在这一课
:::
