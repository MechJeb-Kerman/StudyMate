---
title: 推导式与常用内置工具
goal: 能用列表推导式与 sum、max、any、all、zip、enumerate、sorted 把手写循环压成一行，并说清生成器为什么只能走一遍、什么时候不该压成一行。
---

上一课的结尾是一份能读数据、能算、能输出的函数版解。这一课处理另一种在题解里到处都是的重复：每回要从一批数据算出另一批数据，都要先建一个空容器，再写一层 `for`，再往里 `append`。三行里两行是脚手架，只有一行在做实事。

题解里常见的 `a = [int(x) for x in data]`、`sum(1 for x in a if x > 0)`，去掉的正是这些脚手架。这些写法里每个词单独看都认识，自己落笔时又退回循环——多半是没把「它对应哪一段循环」对上。所以这一课的每一步都并排给两版：先写循环版，再写一行版，输出必须一致。

价值有两处。少写一层循环，就少一处下标写错的机会：`for i in range(len(a))` 得在三处同时把下标写对，换成 `for x in a` 只剩一处。题意也更清楚：`[x for x in a if x > 0]` 一眼读出「`a` 里大于 0 的那些」。这一课的目标是把最常用的十几个内置函数过成手感，让它们在写题时成为默认选择。

有一件事要先说清，免得走偏：压成一行**不等于**更快。它省的是代码行数与出错机会。几版写法落在同一个复杂度档位，差的是常数因子——这一课末尾有一次本机实测。真正决定过不过的仍是第 2 课那把尺子：由数据范围反推可接受的复杂度上限。这一课不改变那一层判断。

## 从三行循环到一行

列表推导式的英文名是 comprehension，这个词在数学与逻辑里本来指「用一个描述式确定一个集合」的写法——像 $\{x^2 \mid x \in \mathbb{N}\}$ 那样，先说清元素长什么样，再说明从哪些东西里取。Python 把这个写法搬进了代码：**列表推导式是用一个表达式、一个 `for` 子句和零个或多个 `if` 子句描述新列表的写法，写在方括号里，执行时按描述逐项算出元素，组成一个新列表。**

最小的一例是平方数列表：

```python
# 循环版：三行
squares = []
for x in range(10):
    squares.append(x ** 2)
print(squares)

# 推导式版：一行
squares = [x ** 2 for x in range(10)]
print(squares)
```

```text
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```

两版输出逐字相同。把一行版拆开，方括号里的三段与循环版一一对应：

| 方括号里的部分 | 例子 | 对应循环版里的哪一行 |
| --- | --- | --- |
| 表达式（算出什么） | `x ** 2` | `squares.append(x ** 2)` 里被追加的那个值 |
| `for` 子句（从哪批数据里取） | `for x in range(10)` | `for x in range(10):` |
| `if` 子句（取哪些，可以没有） | `if x > 0` | `if x > 0:` |

官方教程给出的正式说法是：方括号内包含「一个表达式，后面为一个 `for` 子句，然后，是零个或多个 `for` 或 `if` 子句」。有一处写法上的差别要记住：**这里的 `for` 子句末尾不写冒号。**

::: svg
alt: 列表推导式拆成表达式、for 子句与 if 子句三段，分别对应循环版的三行
caption: 方括号里的三段与循环版三行一一对应

<svg viewBox="0 0 520 240" role="img" aria-hidden="true">
  <g stroke="currentColor" fill="none">
    <rect x="8" y="22" width="168" height="46"/>
    <rect x="184" y="22" width="160" height="46"/>
    <rect x="352" y="22" width="160" height="46"/>
    <path d="M92 68 L92 98" stroke-dasharray="4 3"/>
    <path d="M264 68 L264 98" stroke-dasharray="4 3"/>
    <path d="M432 68 L432 98" stroke-dasharray="4 3"/>
    <rect x="8" y="104" width="504" height="128"/>
  </g>
  <g font-family="sans-serif" fill="currentColor">
    <g font-size="15" text-anchor="middle">
      <text x="92" y="51">[x * 2</text>
      <text x="264" y="51">for x in a</text>
      <text x="432" y="51">if x &gt; 0]</text>
    </g>
    <g font-size="12" text-anchor="middle">
      <text x="92" y="90">算出什么</text>
      <text x="264" y="90">从哪批数据里取</text>
      <text x="432" y="90">取哪些（可省）</text>
    </g>
    <g font-size="13">
      <text x="20" y="128">循环版</text>
      <text x="32" y="152">out = []</text>
      <text x="32" y="176">for x in a:</text>
      <text x="32" y="200">    if x &gt; 0: out.append(x * 2)</text>
      <text x="32" y="224">print(out)   # 与一行版输出相同</text>
    </g>
  </g>
</svg>
:::

另有一处差别与作用域有关，写函数时会撞上：循环版的目标名会留在外面，推导式的不会。

```python
for x in range(3):
    pass
print(x)                          # 2，循环的目标名留在外面

print([y for y in range(3)])      # [0, 1, 2]
print(y)                          # NameError
```

```text
2
[0, 1, 2]
NameError: name 'y' is not defined
```

官方语言参考把这条写得很明确：推导式在一个隐式的嵌套作用域里执行，赋给目标的名字不会「泄漏」到外层。教程在讲循环建表时也提醒过前半句——「这段代码创建（或覆盖）变量 `x`，该变量在循环结束后仍然存在」。对第 4 课刚学的函数来说，这条差别是有用的：函数里写推导式，不会意外改掉外层的同名变量。

::: quiz 理解 锚点：列表推导式与循环版的对应
:::

## 带条件的推导式

官方教程把列表推导式的用途写成两条：对序列里的每个元素应用某种操作，用结果建新表；或者用满足特定条件的元素建子序列。上一节是第一条，这一节是第二条。

```python
vec = [-4, -2, 0, 2, 4]

# 循环版
kept = []
for x in vec:
    if x >= 0:
        kept.append(x)
print(kept)

# 推导式版
print([x for x in vec if x >= 0])
```

```text
[0, 2, 4]
[0, 2, 4]
```

本课程里，条件推导式最常出现在两个位置，都在你已经写过的代码里：

- 读进来的 `data` 是一串字符串，先整批转成整数：`a = [int(x) for x in data]`。
- 第 3 课查重里的 `seen` 是集合，筛出还没出现过的元素：`[x for x in data if x not in seen]`。这一步 `seen` 自始至终不变，只是一次筛选，正适合推导式；而查重本身要一边判断一边往 `seen` 里加，那属于下一节末尾要说的边界。

要两个条件，就再写一个 `if` 子句：`[x for x in range(10) if x % 2 == 0 if x > 4]` 得到 `[6, 8]`。这两个 `if` 与循环版里连着写两个 `if` 是一回事。

::: quiz 理解 锚点：带条件的推导式
:::

## 两层循环压成一行

方括号里可以写两个 `for`，这时它对应的是两层循环。官方教程的例子是把两个列表里不相等的元素两两组合：

```python
# 推导式版
print([(x, y) for x in [1, 2, 3] for y in [3, 1, 4] if x != y])

# 循环版
combs = []
for x in [1, 2, 3]:
    for y in [3, 1, 4]:
        if x != y:
            combs.append((x, y))
print(combs)
```

```text
[(1, 3), (1, 4), (2, 3), (2, 1), (2, 4), (3, 1), (3, 4)]
[(1, 3), (1, 4), (2, 3), (2, 1), (2, 4), (3, 1), (3, 4)]
```

要留意的是**顺序**：一行版里 `for` 与 `if` 的先后，和循环版里从上到下的顺序一致——先 `for x`，再 `for y`，最后 `if x != y`。教程在同一处专门写了一句「上面两段代码中，`for` 和 `if` 的顺序相同」；写反了，得到的元素集合就变了。

两个 `for` 还能把嵌套的列表展平：

```python
vec = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
print([num for elem in vec for num in elem])
```

```text
[1, 2, 3, 4, 5, 6, 7, 8, 9]
```

推导式里还能再嵌一个推导式，这时外层每取一个值就构造一整行。转置一个矩阵是它的例子：

```python
matrix = [
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9, 10, 11, 12],
]

# 嵌套推导式版
print([[row[i] for row in matrix] for i in range(4)])

# 循环版
transposed = []
for i in range(4):
    row_out = []
    for row in matrix:
        row_out.append(row[i])
    transposed.append(row_out)
print(transposed)
```

```text
[[1, 5, 9], [2, 6, 10], [3, 7, 11], [4, 8, 12]]
[[1, 5, 9], [2, 6, 10], [3, 7, 11], [4, 8, 12]]
```

这一层也是**该停手的地方**。官方在这一节末尾紧接着写了一句：实际应用中，最好用内置函数替代复杂的流程语句，此时 `zip()` 函数更好用。同一件事用 `zip` 写：

```python
matrix = [
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9, 10, 11, 12],
]
print(list(zip(matrix[0], matrix[1], matrix[2])))
print([sum(row) for row in matrix])
```

```text
[(1, 5, 9), (2, 6, 10), (3, 7, 11), (4, 8, 12)]
[10, 26, 42]
```

上面这个 `zip` 写法把行数写死了（三行就写三个参数）。官方给的是 `zip(*matrix)`，用星号把矩阵的各行拆成参数传进去，这个写法用到解包实参，遇到再补。转置这个例子到 `zip` 就到头了：再往里叠第三层 `for`，读的人得先在心里把三层展开才能确认结果，那时就该换回循环或现成函数。判断标准在「压成一行值不值」一节统一给。

::: quiz 排错 锚点：把逻辑挤成一行看不懂的推导式
:::

## 生成器表达式

把方括号换成圆括号，就是**生成器表达式**。官方语言参考的说法是：生成器表达式的语法与列表推导式相同，只是方括号换成了圆括号；它在运行时的值是一个生成器迭代器，产生的值与对应的列表推导式一样。

两种写法放在一起看，差别不在结果，在**什么时候算**：

```python
squares = [x ** 2 for x in range(10)]     # 列表：10 个元素已经全部算好
gen = (x ** 2 for x in range(10))         # 生成器：还没算，等着被要
print(squares)
print(gen)
print(sum(gen))     # 第一次：全部取出来加一遍
print(sum(gen))     # 第二次：已经空了
```

```text
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
<generator object <genexpr> at 0x...>
285
0
```

两次 `sum` 的结果不同，是这一节最该记住的现象：第一次要的时候它把 10 个数逐个算出来交出去，加完是 285；第二次再要，里面已经没有东西可给了，加一个空序列得 0。**生成器只能走一遍。**

官方把这件事叫**惰性求值**：除了最左侧 `for` 子句里的那个来源，其余表达式都推迟到向迭代器要值时才算。这里的来源是 `range(10)`，它会立刻求值——好处是来源写错时错误当场就报，不必等到取值那一刻。

没有长度、不能按下标取，也是同一个原因：

```python
gen = (x ** 2 for x in range(10))
print(len(gen))
```

```text
TypeError: object of type 'generator' has no len()
```

```python
gen = (x ** 2 for x in range(10))
print(gen[0])
```

```text
TypeError: 'generator' object is not subscriptable
```

与第 3 课的口径合起来看，两种写法的代价差别就很清楚了：

| | 列表推导式 `[...]` | 生成器表达式 `(...)` |
| --- | --- | --- |
| 什么时候算 | 写出来时就把元素全算好，建成一张表 | 每要一个才算一个 |
| 额外占用 | $O(n)$，一格一个元素 | $O(1)$，手上只留当前这个值 |
| 能遍历几次 | 想遍历几次都行 | 一次，取完就空 |
| 能 `len`、能下标吗 | 都能 | 都不能，报 `TypeError` |
| 什么时候用 | 结果要反复用、要按位置取、要 `len` | 结果只是喂给 `sum`、`max`、`any` 这类函数走一遍 |

::: svg
alt: 列表推导式先把整张表建好再交给 sum，生成器表达式算一个交一个，额外占用分别为 O(n) 与 O(1)
caption: 建表与惰性：前者额外占用 O(n) 且能反复用，后者额外占用 O(1) 但只能走一遍

<svg viewBox="0 0 520 250" role="img" aria-hidden="true">
  <g stroke="currentColor" fill="none">
    <rect x="8" y="30" width="110" height="44"/>
    <rect x="150" y="30" width="220" height="44"/>
    <rect x="400" y="30" width="112" height="44"/>
    <path d="M118 52 L150 52"/>
    <path d="M370 52 L400 52"/>
    <rect x="8" y="152" width="110" height="44"/>
    <rect x="150" y="152" width="220" height="44"/>
    <rect x="400" y="152" width="112" height="44"/>
    <path d="M118 174 L150 174"/>
    <path d="M370 174 L400 174"/>
    <path d="M456 196 L456 216 L260 216 L260 196" stroke-dasharray="4 3"/>
  </g>
  <g font-family="sans-serif" fill="currentColor">
    <g font-size="13">
      <text x="8" y="20">列表推导式</text>
      <text x="8" y="142">生成器表达式</text>
    </g>
    <g font-size="13" text-anchor="middle">
      <text x="63" y="57">来源 a</text>
      <text x="260" y="57">整张新表：n 个元素</text>
      <text x="456" y="57">sum(…)</text>
      <text x="63" y="179">来源 a</text>
      <text x="260" y="179">算一个、交一个</text>
      <text x="456" y="179">sum(…)</text>
    </g>
    <g font-size="12" text-anchor="middle">
      <text x="260" y="100">先把 n 个元素全部算好，再交给 sum；额外占用 O(n)</text>
      <text x="260" y="240">边算边交，不建表；额外占用 O(1)，取完就空</text>
      <text x="352" y="212">要一个才算一个</text>
    </g>
  </g>
</svg>
:::

调用处还有个括号可以省，官方专门写了一条：生成器表达式是唯一的实参、又没有关键字实参时，可以省掉外面那层括号。

```python
print(sum(x ** 2 for x in range(10)))                    # 285
print(sum((x ** 2 for x in range(10)), start=1000))      # 1285
```

```text
285
1285
```

::: warn sum 这类函数会把东西取完
`sum`、`max`、`any`、`all` 会一直向可迭代对象要值，直到它结束——上面第二次 `sum(gen)` 得 0，正是第一次已经把生成器取空了。如果来源本身永远不结束，这些函数就会一直要下去，程序停在原地不动。要处理不会结束的序列，得自己在循环里判断什么时候停，不能直接套这些函数。
:::

::: quiz 理解 锚点：生成器表达式与惰性求值
:::

## 不再数下标的两个函数

这两个函数解决的尴尬是同一类：循环体里明明只要元素，却不得不先弄一个下标出来。

官方教程把它们安排在「循环的技巧」一节：在序列中循环时，用 `enumerate()` 可以同时取出位置索引和对应的值；同时循环两个或多个序列时，用 `zip()` 可以把元素一一匹配。

```python
names = ['第一题', '第二题', '第三题']
scores = [80, 95, 60]

for i in range(len(names)):                # 下标版
    print(i, names[i], scores[i])

for i, name in enumerate(names):           # 位置与值一次取出
    print(i, name)

for name, score in zip(names, scores):     # 两个序列一一匹配
    print(name, score)
```

```text
0 第一题 80
1 第二题 95
2 第三题 60
0 第一题
1 第二题
2 第三题
第一题 80
第二题 95
第三题 60
```

下标版要在三个地方写对同一个下标，两种新写法各只剩一处：

- `enumerate` 的计数默认从 0 起，要按题号从 1 数就写 `enumerate(names, start=1)`。
- 位置与配对都要拿到时，两个可以叠起来用：`for i, (name, score) in enumerate(zip(names, scores))`。
- `zip` 在最短的那个序列用完时就停：`zip(names, scores[:2])` 只给出两组。长度不齐不会报错，只会悄悄变短，用之前确认两个序列是对齐的。
- `enumerate` 的名字里有个迭代器的意思：它也是走一遍就空的，不存在「重置」。
- 想单独取出配对里的某一列，可以写作 `[score for _, score in zip(names, scores)]`——用一个不对应的名字 `_` 接住那一列。

```python
names = ['第一题', '第二题', '第三题']
scores = [80, 95, 60]
print(list(enumerate(names, start=1)))
print(list(zip(names, scores[:2])))
print([score for _, score in zip(names, scores)])
for i, (name, score) in enumerate(zip(names, scores)):
    print(i, name, score)
```

```text
[(1, '第一题'), (2, '第二题'), (3, '第三题')]
[('第一题', 80), ('第二题', 95)]
[80, 95, 60]
0 第一题 80
1 第二题 95
2 第三题 60
```

::: quiz 理解 锚点：zip 与 enumerate 的用法
:::

::: quiz 改造 锚点：把下标循环改成 enumerate 与 zip
:::

## sorted 的 key

排序这件事本身内置函数已经做完了，真正需要写的是「按什么排」。官方排序指南开头的两条口径是：`sorted()` 函数接受一个可迭代对象，返回一个新的有序列表；`key` 形参用来指定一个函数，在比较之前对每个元素调用它，用它的返回值参与比较。

先看没写 `key` 与写了 `key` 的区别：

```python
records = [('john', 'A', 12), ('jane', 'B', 15), ('dave', 'B', 10)]

print(sorted(records))                       # 没给 key：按整个元组比，先比第一项
print(sorted(records, key=lambda s: s[2]))   # 给了 key：按第三项比
```

```text
[('dave', 'B', 10), ('jane', 'B', 15), ('john', 'A', 12)]
[('dave', 'B', 10), ('john', 'A', 12), ('jane', 'B', 15)]
```

`lambda` 这个名字来自 λ 演算——二十世纪三十年代用来研究可计算性的一套形式系统，它就是「一个没有名字的函数」的写法。`lambda s: s[2]` 与第 4 课那样的定义是同一个东西：

```python
def key_of(s):
    return s[2]

records = [('john', 'A', 12), ('jane', 'B', 15), ('dave', 'B', 10)]
print(sorted(records, key=key_of))
```

```text
[('dave', 'B', 10), ('john', 'A', 12), ('jane', 'B', 15)]
```

区别只在不用起名字。`lambda` 的限制是冒号右边只能写一个表达式（不能赋值、不能写多个分支），当 `key` 用刚好够。给 `key` 传的函数必须是**一元函数**——只收一个元素，交出参与比较的键。

按第二关键字排序，是这一课最值钱的一招。官方排序指南给多级排序写了两条路。第一条是让 `key` 返回一个元组：

```python
records = [('john', 'A', 12), ('jane', 'B', 15), ('dave', 'B', 10)]
print(sorted(records, key=lambda s: (s[1], s[2])))
```

```text
[('john', 'A', 12), ('dave', 'B', 10), ('jane', 'B', 15)]
```

元组之间比较用的是**字典式顺序**（官方教程对序列比较的讲法）：先比第一个对应元素，不相等就定了；相等再比后面两个，以此类推。所以 `(s[1], s[2])` 读作「先按第二项排，第二项相同再按第三项」。

第二条路用排序的**稳定性**。官方排序指南的原话是：排序保证稳定——等键记录保持原始顺序；并且说明这个特性使得借助一系列排序步骤构建复杂排序成为可能。于是「先按次要键排一遍，再按主要键排一遍」就能得到多级排序：

```python
records = [('john', 'A', 12), ('jane', 'B', 15), ('dave', 'B', 10)]
s = sorted(records, key=lambda r: r[2])       # 先按次要键：年龄
print(sorted(s, key=lambda r: r[1]))          # 再按主要键：成绩
```

```text
[('john', 'A', 12), ('dave', 'B', 10), ('jane', 'B', 15)]
```

`key` 还有一条性能上的性质，官方指南专门点明：**键函数只需在输入的每个记录上调用恰好一次**。用一个会打印的函数当 `key` 就能看见：

```python
def show(s):
    print('取键', s)
    return s[2]

records = [('john', 'A', 12), ('jane', 'B', 15), ('dave', 'B', 10)]
print(sorted(records, key=show))
```

```text
取键 ('john', 'A', 12)
取键 ('jane', 'B', 15)
取键 ('dave', 'B', 10)
[('dave', 'B', 10), ('john', 'A', 12), ('jane', 'B', 15)]
```

三条记录只打印三行，而排序过程中元素之间要比很多次。这也是 `key` 比「让元素自己会比较」划算的地方：取键一次，比较很多次。

同一套 `key` 写法在 `min`、`max` 上也能用（官方指南把 `sorted`、`list.sort`、`min`、`max` 列在同一组）：

```python
records = [('john', 'A', 12), ('jane', 'B', 15), ('dave', 'B', 10)]
print(max(records, key=lambda s: s[2]))
```

```text
('jane', 'B', 15)
```

::: quiz 理解 锚点：sorted 的 key 参数
:::

::: quiz 应用 锚点：按第二关键字给记录排序
:::

## 两个排序函数差在哪

`sorted(a)` 与 `a.sort()` 排出来的顺序一样，区别有两处，官方排序指南开头就写了。第一处：`list.sort()` 原地修改列表，而 `sorted()` 由可迭代对象新建一个有序列表。第二处就是本课要记的那个坑——指南在讲 `list.sort()` 时特别标注了它「返回 `None` 以避免混淆」。

写 `x = a.sort()`，你以为拿到的是排好序的新表，实际拿到的是 `None`，而原列表已经被改过了：

```python
c = [3, 1, 2]
x = c.sort()          # 想拿到新表
print(x)              # None
print(c)              # 原表已经被改了

d = [3, 1, 2]
d = d.sort()          # 把结果又赋回 d
print(d)              # None
print(d[0])
```

```text
None
[1, 2, 3]
None
TypeError: 'NoneType' object is not subscriptable
```

第二段里 `d[0]` 报 `TypeError`，是因为 `d` 这个名字已经被赋成了 `None`，再往下用它（取下标、求长度、当参数传）都会报错。这种错误报的那一行往往离出错的写法很远，是它难查的原因。

第三处差别在同一段官方指南里：`list.sort()` 只为列表定义，`sorted()` 接受任何可迭代对象。

```python
print(sorted({3, 1, 2}))
print(hasattr({3, 1, 2}, 'sort'))
```

```text
[1, 2, 3]
False
```

集合可以交给 `sorted()`（交回来的是列表），但它自己没有 `.sort`；元组、字符串同理。

选法就一条：结果要给别的变量用、或者原数据还要保留，用 `sorted(...)`；原数据可以就地改掉、也不再需要旧顺序，用 `a.sort()`。

::: quiz 排错 锚点：把 list.sort 的返回值当新列表
:::

## 统计与判定的现成函数

教材在讲数字列表时介绍过一组现成函数：`max()`、`min()`、`sum()` 分别求最大、最小与总和。这三个加上 `any()` 与 `all()`，覆盖了「把一批数据扫一遍、得出一个数或一个判断」这类循环的大半。

官方文档给 `any` 与 `all` 的定义是：`any(iterable)` 在可迭代对象里有任意一个元素为真时返回 `True`，空的可迭代对象返回 `False`；`all(iterable)` 在所有元素都为真时返回 `True`（空的可迭代对象也算）。两段定义后面都附了一段等价的 `for` 循环代码，函数体里是 `if …: return …`——也就是说，能确定结果时它就不再往下取值了。

四组对照，左边是循环版，右边是一行版，得出的是同一个数：

| 要做的事 | 循环版 | 一行版 |
| --- | --- | --- |
| 求和 | `total = 0`，循环里 `total += x` | `sum(a)` |
| 求最大 | `best = a[0]`，循环里比一次 | `max(a)` |
| 数有几个满足条件的 | `c = 0`，循环里 `if x > 0: c += 1` | `sum(1 for x in a if x > 0)` |
| 有没有满足条件的 | `found = False`，循环里置 `True` | `any(x > 0 for x in a)` |

```python
a = [3, -1, 4, 0, 7]
print(sum(a))                                          # 13
print(max(a), min(a))                                  # 7 -1
print(sum(1 for x in a if x > 0))                      # 3
print(any(x > 5 for x in a))                           # True
print(all(x > 0 for x in a))                           # False
print(any(x > 0 for x in []), all(x > 0 for x in []))  # 空序列的默认答案
```

```text
13
7 -1
3
True
False
False True
```

最后一行是空序列的口径，两个函数的默认答案相反：`any` 在空序列上返回 `False`（一个满足的都没有），`all` 在空序列上返回 `True`（一个反例也没有）。判空数据时要留意这对不对称：用 `all` 检查「这批数据是不是都合法」，空数据也会给出 `True`。

第三行的 `sum(1 for x in a if x > 0)` 读法是「每个满足条件的元素算作 1，把它们加起来」。它也可以写成 `len([x for x in a if x > 0])`：先建一张筛过的表再数长度，结果一样，代价是那张表——$O(n)$ 个元素的空间（第 3 课的口径）。喂给 `sum` 的生成器表达式不建表，所以计数这种「只为了走一遍」的场合用它更合适。

::: quiz 理解 锚点：any 与 all 的返回值
:::

::: quiz 改造 锚点：用内置函数替换计数与判定循环
:::

## map 与列表推导式

`map` 把现成的函数套到每个元素上。官方教程在讲推导式时给过一个对照：`squares = list(map(lambda x: x**2, range(10)))` 与 `squares = [x**2 for x in range(10)]` 等价，并说明后者更简洁、易读。

它最实用的场合是「转换用的函数已经有现成的」，比如把一串字符串变成整数：

```python
data = ['3', '-1', '4']
print(list(map(int, data)))       # 收成一张表
print(sum(map(int, data)))        # 直接喂给 sum，不建表
print([int(x) for x in data])     # 推导式版
```

```text
[3, -1, 4]
6
[3, -1, 4]
```

`int` 在这里就是第 4 课那条「函数是值，可以当参数传」的直接用法：`map` 拿到 `int` 这个函数，对每个元素调用一次。两点与前面呼应：`map` 返回的是迭代器，所以要么用 `list(...)` 收下，要么直接交给 `sum` 这类函数；也正因为是迭代器，它只能用一次。

```python
data = ['3', '-1', '4']
m = map(int, data)
print(list(m))
print(list(m))     # 第二次已经空了
```

```text
[3, -1, 4]
[]
```

要写的是自己的一条表达式，或者还要加条件筛选时，列表推导式更顺手：`[x * 2 for x in a if x > 0]` 一句话说清了「取正的、翻倍」，用 `map` 得拆成两步。

## 压成一行值不值

前面一直说：压成一行，省下来的是行数；速度上几版同档。这里实测一次。本机（Python 3.14.7，free-threading 构建）建一张 $10^6$ 个元素的表：

| 写法 | 本机实测 |
| --- | --- |
| 循环 + `append` | 约 40 毫秒 |
| 列表推导式 | 约 32 毫秒 |
| `list(map(lambda x: x * 2, range(n)))` | 约 55 毫秒 |
| 循环里带 `if` 计数 | 约 27 毫秒 |
| `sum(1 for x in range(n) if x % 2 == 0)` | 约 30 毫秒 |

第三行值得多看一眼：它最慢。原因是那个 `lambda` 每处理一个元素就要调用一次函数，第 4 课量过的那笔调用开销在这里被乘上了一百万次。这说明两件事：写成一行与快不快是两回事；这几版写法都落在同一档复杂度（都是 $O(n)$），差的是常数因子。

::: warn 别背这些毫秒
表里的数字是本机实测，换机器、换 Python 版本都会变。要记的是两条：几版写法复杂度同档、差在常数倍以内；「一行」省下来的是行数与出错机会，与时间无关。真想压常数，那是后面「让 Python 再快一点」那一课的事。
:::

几版写法既然在速度上同档，什么时候用一行版、什么时候老实写循环，就只剩可读性一条标准。教材在讲循环建表时给过一句可以当准则的话：**你首先应该考虑的是，编写清晰易懂且能完成所需功能的代码**；它还给了触发条件——当你觉得编写三四行代码来生成列表有点繁复时，就应考虑用这种写法。反过来，下面几种情形该写回循环：

| 情形 | 为什么 | 怎么写 |
| --- | --- | --- |
| 循环要维护一个跨轮次的状态 | 推导式里没有地方放「上一轮留下的东西」 | 第 3 课的查重：一边判断一边往 `seen` 里加 |
| 一个元素要产生好几样东西，或要顺带打印 | 表达式只有一个位置，放不下多件事 | 写循环，或把那段逻辑抽成函数 |
| `for` 与 `if` 叠到三层以上 | 读的人要先在心里展开才能确认结果 | 写循环；或者按官方那句，换现成函数 |
| 这段代码你打算反复调试 | 一行里看不到中间值 | 先写循环版跑通，再考虑压成一行 |

最后一行是这一课的用法建议：改写的顺序是先写清楚，再压紧。压完必须对着循环版比对输出，逐字一致才算改完——这正是练习里要做的事。

## 这一课用到的 Python

| 要做的事 | 写法 | 边界 |
| --- | --- | --- |
| 用描述式建新表 | `[x * 2 for x in a]` | `for` 子句末尾不写冒号；目标名不会留到外面 |
| 只取满足条件的元素 | `[x for x in a if x > 0]` | 条件写在最后，可以连着写两个 `if` |
| 两层循环压一行 | `[(x, y) for x in a for y in b]` | `for` 与 `if` 的顺序要和循环版一致 |
| 不建表的写法 | `(x * 2 for x in a)` | 只能走一遍；没有 `len`，不能下标 |
| 位置与值一起取 | `for i, v in enumerate(a, start=1)` | 也是迭代器，取完就空 |
| 两个序列配对 | `for x, y in zip(a, b)` | 在最短的那个用完时停，长度不齐不报错 |
| 指定排序依据 | `sorted(a, key=lambda s: s[2])` | 键函数每条记录只调用一次，必须是一元函数 |
| 多关键字排序 | `key=lambda s: (s[1], s[2])` | 元组按字典式顺序比：先比第一个键，相同再比第二个 |
| 保留原顺序 | `b = sorted(a)` | `a.sort()` 原地改并返回 `None` |
| 求和、极值、判定 | `sum(a)`、`max(a)`、`any(...)`、`all(...)` | `any([])` 得 `False`，`all([])` 得 `True` |
| 用现成函数做转换 | `list(map(int, data))` | 返回迭代器；要写表达式就改用列表推导式 |
| 计数 | `sum(1 for x in a if x > 0)` | 写成 `len([...])` 会先建一张表 |

这套工具在后面每一课都会出现：第 3 课的容器选择、这一课的一行写法、下一课的输入解析会连在一起用——把「第一行 `n m`，接下来 `n` 行每行 `m` 个整数」读成二维列表，靠的就是推导式配 `split` 与 `map`。

::: practice 练习 | 十条循环，逐条改写成一行

这一课的动手部分落在 lab 里（任务与断言见 [lab/0005-python-comprehension-builtins/](../lab/0005-python-comprehension-builtins/)，做完对照 [lab/solutions/](../lab/solutions/)）。要做的是三件事。

1. 从自己过去写过的代码里收集十段循环（求导、统计、筛选、查重、按关键字排序都算），先把每一段的输入与输出记下来。
2. 逐段改写：能压成推导式的压成推导式，能换成内置函数的换成内置函数，其中 `enumerate`、`zip`、`sorted(key=)`、`sum`、`max`、`any`、`all`、`map` 各至少出现一处。每改完一段，用同一组输入跑新旧两版，输出必须逐字一致。
3. 给每一段写一句判断：改完是更清楚了，还是更难读了。判为「更难读」的那几段写回循环版，并在旁边注明撞上了哪一条边界（跨轮次的状态、多件事挤在一个表达式里、`for` 与 `if` 叠了三层以上、要留着调试）。

:::

::: resources
- [Python 官方教程 · 数据结构](https://docs.python.org/zh-cn/3/tutorial/datastructures.html) | 5.1.3 列表推导式、5.1.4 嵌套推导式、5.6 循环的技巧（`enumerate` 与 `zip`），本课的写法与顺序口径出自这里
- [Python 语言参考 · 表达式](https://docs.python.org/zh-cn/3/reference/expressions.html) | 6.2.5 至 6.2.9：推导式的隐式作用域与子句顺序、集合与字典推导式、生成器表达式与惰性求值
- [Python 官方文档 · 排序指南](https://docs.python.org/zh-cn/3/howto/sorting.html) | `sorted` 与 `list.sort` 的区别、`key` 只调用一次、稳定性与多级排序
- [Python 官方文档 · 内置函数](https://docs.python.org/zh-cn/3/library/functions.html) | `sum`、`max`、`min`、`any`、`all`、`enumerate`、`map`、`zip` 的签名与空序列口径
- 《Python 编程：从入门到实践（第 2 版）》第 4 章 操作列表 | 本地教材：4.3.3 数字列表的统计、4.3.4 列表解析（本课程统一叫列表推导式）
:::
