---
title: 读完输入再动手
goal: 能把单行多整数、多行整数、n×m 矩阵、混合行列与带空行的多组数据各读成指定的数据结构，并用最小样例与打印把输入层的错误定位出来。
---

第 1 课那道题只有一行输入，一个整数。第 4 课和第 5 课处理的 `data` 是已经切好的一串字符串。真实题面的输入要复杂得多：一行里塞好几个整数、一个数占一行、$n \times m$ 的矩阵、行列数写在第一行、数据块之间夹着空行。

学生通用的做法是 `input()` 一行一行读，一边读一边算。遇到「第一行 `n m`，接下来 `n` 行每行 `m` 个整数」时，卡住的位置常常落在第一步：数据还没有完整地落进一个数据结构，后面每一步都在猜自己读到哪儿了。这一课把动作定下来：**先用一次读入把整份输入变成数据结构，算法只面对数据结构。** 这门课后面每一道题都从这一步开始。

## 输入没读完，别动手

把常见输入摊开，格式只有几类，每一类这一课都会给一份能跑的模板：

- 单行多整数：`3 1 4 1 5 9`。
- 多行整数：第一行给个数 `n`，接下来 `n` 行每行一个整数；也有不给 `n`、一直给到输入结束的。
- 矩阵：先给 `n m`，再给 $n \times m$ 个整数，或者直接给 $n$ 行、每行 $m$ 个。
- 混合行列：同一份输入里既有定长的矩阵，后面又跟若干组查询。
- 多组数据：第一行给组数，组与组之间夹空行，数据块末尾还留一个空行。

这些格式的共同点是：空白字符在承担分组的职责。换行与空格告诉程序哪些数属于同一行、哪些数属于同一组，而程序得先把这份分组关系还原成数据结构，才轮得到算法。

规矩只有一句：**先读完、再算。** 读入只发生一次，结果是一个数据结构；算法从数据结构出发，不再碰输入。

::: svg
alt: 从标准输入到答案的五个阶段：标准输入、read 得到一整块文本、split 得到 token 表、解析函数得到数据结构、solve 只算
caption: 读入、解析、算法三段：标准输入只被碰一次，算法只面对数据结构

<svg viewBox="0 0 520 215" role="img" aria-hidden="true">
  <g stroke="currentColor" fill="none">
    <rect x="16" y="10" width="300" height="28"/>
    <rect x="16" y="50" width="300" height="28"/>
    <rect x="16" y="90" width="300" height="28"/>
    <rect x="16" y="130" width="300" height="28"/>
    <rect x="16" y="170" width="300" height="28"/>
    <path d="M166 38 L166 50"/>
    <path d="M166 78 L166 90"/>
    <path d="M166 118 L166 130"/>
    <path d="M166 158 L166 170"/>
    <path d="M330 10 L344 10 L344 118 L330 118" stroke-dasharray="4 3"/>
    <path d="M330 130 L344 130 L344 158 L330 158" stroke-dasharray="4 3"/>
    <path d="M330 170 L344 170 L344 198 L330 198" stroke-dasharray="4 3"/>
  </g>
  <g font-family="sans-serif" fill="currentColor" font-size="12">
    <text x="26" y="29">标准输入：一整串字符</text>
    <text x="26" y="69">sys.stdin.read()　→ 一整块文本</text>
    <text x="26" y="109">split()　→ token 表 ['3', '1', '4']</text>
    <text x="26" y="149">解析函数　→ 数据结构 [[3, 1], [4, 1]]</text>
    <text x="26" y="189">solve() 只算　→ print 答案</text>
    <text x="352" y="68">读入：只发生一次</text>
    <text x="352" y="150">解析：token 变数据结构</text>
    <text x="352" y="189">算法：只面对数据结构</text>
  </g>
</svg>
:::

「边读边算」的问题在「先读完再算的规矩」一节用一份对照代码讲清。这里先说它的两种表现：读到的位置与你以为的位置不一致；出错时报的那一行离真正的原因很远。

一次读完的代价是 $O(n)$ 的时间与额外空间——token 表与数据结构都随输入规模增长（第 2 课的口径：$O(n)$ 的额外空间意思是这类开销随输入规模线性增长，在题目给的数据规模内属于常规开销）。它不改变复杂度档位，省下来的是「读指针现在到哪了」这件事。

## 把整个输入读成一块

标准输入在 Python 里有一个名字：`sys.stdin`。官方文档把它和另外两条流写在同一处：

- `stdin` 用于所有交互式输入（包括对 `input()` 的调用）；
- `stdout` 用于 `print()` 和表达式语句的输出，以及用于 `input()` 的提示符；
- 解释器自身的提示符和它的错误消息都发往 `stderr`。

文档紧接着说明：这些流都是**常规文本文件**，与 `open()` 函数返回的对象一致。这句话给了两件事。一是 `sys.stdin` 上能用的读法就是文件对象的读法（`read`、`readline`、遍历整个文件对象、`readlines`），课本讲文件读写那一节可以直接搬过来。二是 `input()` 并不在另一条通道上，它只是 stdin 上的一个便利入口——这个认识在讲提示文字那一节会变成一个判零分的坑。

`sys.stdin.read()` 把整份输入读成一个字符串。字符串上的 `split()` 不带参数时按任意空白切分：空格、制表符、换行都算分隔符，连续几个当作一个，首尾的空白丢掉。于是一整份输入变成一张 **token 表**。

```python
import sys

text = sys.stdin.read()
tokens = text.split()
print(tokens)
print([int(x) for x in tokens])
```

样例 `sample1.in` 是一行 8 个整数：

```text
3 1 4 1 5 9 2 6
```

```term
$ cat sample1.in | python read_block.py
['3', '1', '4', '1', '5', '9', '2', '6']
[3, 1, 4, 1, 5, 9, 2, 6]
```

第一行打印出来的是 token 表：**一整份输入在这里变成了一个字符串列表，每一项是一个 token**。第二行是按 token 逐个转出来的整数列表。要留意的正是第一行——token 表里全是字符串，这件事在「读进来的都是字符串」一节会变成一个安静的坑。

官方文档还有一条备注：要从标准流写入或读取二进制数据，请使用底层二进制 `buffer` 对象。读入这一路上对应的是 `sys.stdin.buffer.read()`，它交回的是字节串，切出来的 token 是 `bytes`：

```python
import sys

tokens = sys.stdin.buffer.read().split()
print(tokens[0], type(tokens[0]))
print(sum(map(int, tokens)))
```

```term
$ cat sample1.in | python buffer_read.py
b'3' <class 'bytes'>
31
```

第一个 token 的类型是 `bytes`（打印成 `b'3'`）。`int()` 也接受 `bytes`（实测 `b'3'` 得 3），所以 `map(int, tokens)` 照样能用。这层 `buffer` 省掉的是文本解码这一步，代价是 token 变成了 `bytes`：一旦某处要拿 token 与普通字符串比较或拼接，还得自己 `decode()`。普通题目用 `sys.stdin.read()` 就够。

读法之间差多少，本机实测一次（20 万个整数、每行一个）：

| 读法 | 本机实测 |
| --- | --- |
| `input()` 一次读一行（20 万次调用） | 约 120 毫秒 |
| `for line in sys.stdin` 逐行读 | 约 65 到 90 毫秒 |
| `sys.stdin.read().split()` | 约 70 毫秒 |
| `sys.stdin.buffer.read().split()` | 约 70 毫秒 |

::: warn 别背这些毫秒
数字是本机实测，换机器、换 Python 版本都会变。要记的是两条：这几种读法都落在同一档复杂度（都是 $O(n)$），差的是常数；逐行 `input()` 每次调用都要付一笔固定开销（第 4 课量过），20 万次叠起来本机慢了约一倍。哪种更快我没有找到官方给出的速度结论，上面的数字是自己量的。从「先读完」里拿到的主要东西是一份完整、可打印、可检查的数据结构；速度上的差别只是附带。
:::

::: quiz 理解 锚点：sys.stdin 整体读入与按空白切分
:::

## 按行读还是一起读

按行切分的读法，官方教程在文件对象那一节写得很全，四条都用得上：

- `f.read(size)` 省略 `size` 时读回整个文件的内容；
- `f.readline()` 读单行，**字符串末尾保留换行符**，只有在文件最后一行不以换行符结尾时才会省略；只要它返回空字符串就表示到了文件末尾，**空行用 `'\n'` 表示**，这个字符串只包含一个换行符；
- 从文件里读多行时，可以循环遍历整个文件对象；
- 要以列表形式读出所有行，可以用 `list(f)` 或 `f.readlines()`。

实测最直观。下面的程序把三种读法都用一遍（第三次调用是故意的）：

```python
import sys

line = sys.stdin.readline()
print('readline ->', repr(line))
print('readlines ->', repr(sys.stdin.readlines()))
print('input     ->', repr(input()))
```

```term
$ cat sample4.in | python three_readers.py
readline -> '3 4\n'
readlines -> ['1 2 3 4\n', '5 6 7 8\n', '9 10 11 12\n', '2\n', '1 1\n', '3 4\n']
Traceback (most recent call last):
  File "three_readers.py", line 5, in <module>
    print('input     ->', repr(input()))
          ~~~~~^^
EOFError: EOF when reading a line
```

前两行确认了两条官方口径：`readline()` 交回的行末尾留着 `\n`（`'3 4\n'`），`readlines()` 只是把剩下的行都装进一个列表，每一项同样带着 `\n`。最后一次调用报错是因为读取位置**只能往前**：`readline()` 拿走了第 1 行，`readlines()` 拿走了剩下全部，`input()` 被调用时已经到末尾。

整体读入也一样。`sys.stdin.read()` 读完之后再用 `input()`，同样撞 EOF：

```python
import sys

data = sys.stdin.read().split()
print('读到的 token 数:', len(data))
n = int(input())
print('再读一行:', n)
```

```term
$ cat sample4.in | python read_then_input.py
读到的 token 数: 19
Traceback (most recent call last):
  File "read_then_input.py", line 4, in <module>
    n = int(input())
          ~~~~~^^
EOFError: EOF when reading a line
```

结论很直接：**一份程序里只用一种读入口，而且只读一次。** 读完之后，所有需要的数据都在你手上。

`input()` 与 `readline()` 的差别只有一处：`input()` 交回的那一行去掉了行尾换行符。实测读 `sample2.in` 的第一行 `5`：

```term
$ cat sample2.in | python input_strip.py
'5'
长度 1
```

两种切分的分工，用一张表记：

| | 按空白切分 `text.split()` | 按行切分 `text.splitlines()` |
| --- | --- | --- |
| 分隔依据 | 任意空白（空格、制表符、换行） | 换行符 |
| 换行去了哪 | 消失，与空格等价 | 行边界保留成列表元素 |
| 连续空白 | 当作一个 | 空行切出一个空字符串 `''` |
| 行尾换行符 | 当作空白处理，不保留 | 不保留（`readline()` 保留 `\n`） |
| 适合的题面 | 「给 $n \times m$ 个整数」这类只讲个数的 | 「每行一组」「每行一条记录」这类行本身有含义的 |
| 怕什么 | 基本不怕，空白怎么排都行 | 空行、折行、行首缩进 |

::: quiz 理解 锚点：按行读与按空白切分的差别
:::

## 先读完再算的规矩

拿一份「边读边算」的程序看它怎么错。题面是：第一行 `n m`，接下来是 $n \times m$ 个整数，求所有数之和。

```python
import sys

n, m = map(int, input().split())
total = 0
for _ in range(n):
    row = list(map(int, input().split()))
    total += sum(row)
print(total)
```

同一份程序，两组输入。第一组是排版整齐的 `sample3.in`：

```text
3 4
1 2 3 4
5 6 7 8
9 10 11 12
```

```term
$ cat sample3.in | python rows_running.py
78
```

结果对。换一块数据（`sample6.in`），还是那 12 个数，只是换行位置被换过：

```text
3 4
1 2 3 4
5 6
7 8
9 10 11 12
```

```term
$ cat sample6.in | python rows_running.py
36
```

36 是错的，正确答案是 78，而这个程序一个错字都没报。错在读取这一层：`input()` 每被调用一次就吃掉一行，「第 `i` 次循环」于是与「输入的第 `i` 行」绑在了一起。这份程序认为每行恰好是矩阵的一行，而实际数据里有两行被折开了，于是它读到的三行是 `1 2 3 4`、`5 6`、`7 8`，最后一行 `9 10 11 12` 根本没被读。**读过的位置拿不回来：前面读错一段，后面每一次读都跟着错。**

换「先读完、再算」的写法，同一块数据：

```python
import sys

def read_all():
    return sys.stdin.read()

def parse_matrix(text):
    tokens = text.split()
    n, m = int(tokens[0]), int(tokens[1])
    vals = [int(x) for x in tokens[2:2 + n * m]]
    return n, m, [vals[i * m:(i + 1) * m] for i in range(n)]

def solve():
    n, m, a = parse_matrix(read_all())
    print('n m =', n, m)
    for i, row in enumerate(a):
        print('第', i, '行长度', len(row), row)
    print('总和', sum(sum(row) for row in a))

solve()
```

```term
$ cat sample6.in | python tokens_then_compute.py
n m = 3 4
第 0 行长度 4 [1, 2, 3, 4]
第 1 行长度 4 [5, 6, 7, 8]
第 2 行长度 4 [9, 10, 11, 12]
总和 78
```

78 是对的，原因落在 `split()` 上：它只认空白，不区分空白长什么样（一个空格、一行、三行都一样），所以换行怎么排都不影响切出来的 token 表；矩阵的三行是从 token 表上按 `m` 个一段切出来的，切的位置由 `n`、`m` 决定。

这次的 12 个数被折行，是我为了让错位看得见而改的排版；真实评测数据多半按题面排版给你，所以「边读边算」在很多题上也能过。它的代价在别处：这份程序把「输入的换行位置」当成了算法的一部分，一旦样例、别人分享的数据、或者从题面复制粘贴时换行被打乱，读指针就错位，而报错的位置与原因隔得很远（后面「多组数据与空行」里那份逐行版程序，报错在第 3 行，原因在第 2 行那个空行上）。

把这条规矩用第 4 课的骨架固定下来：

```python
import sys

def read_all():
    """唯一碰标准输入的地方。"""
    return sys.stdin.read()

def parse_input(text):
    """只面对数据：字符串进来，数据结构出去。"""
    ...

def solve():
    data = parse_input(read_all())
    ...

solve()
```

三条纪律：

- 读入只写在一个函数里，只被调用一次；
- 解析函数的输入是字符串、输出是数据结构，里面不出现 `input()`、`sys.stdin`；
- `solve()` 拿到数据结构之后才开始算，算的那部分代码里看不到读入。

::: quiz 排错 锚点：边读边算导致读指针错位
:::

::: quiz 改造 锚点：把逐行读入改写成解析函数
:::

## 五种格式的解析模板

下面五份模板各是一个能跑的程序：一个 `read_all()`、一个解析函数、一个 `solve()`。样例输入存成了文件（`sample1.in` 到 `sample6.in`），跑法统一是 `cat 样例文件 | python 程序.py`。每份模板都标出它产出的数据结构。

### 单行多整数

样例 `sample1.in`：

```text
3 1 4 1 5 9 2 6
```

`one_line.py`：

```python
import sys

def read_all():
    """唯一读标准输入的地方：整份输入读成一个字符串。"""
    return sys.stdin.read()

def parse_ints(text):
    """按空白切分整份输入，逐个转成整数。"""
    return [int(x) for x in text.split()]

def parse_ints_loop(text):
    """同一件事的循环版。"""
    out = []
    for x in text.split():
        out.append(int(x))
    return out

def parse_ints_map(text):
    """同一件事的 map 版（第 5 课的工具）。"""
    return list(map(int, text.split()))

def solve():
    text = read_all()
    a = parse_ints(text)
    print(a)
    print(sum(a), max(a))
    print('推导式版与循环版一致:', a == parse_ints_loop(text))
    print('推导式版与 map 版一致:', a == parse_ints_map(text))
    print('token 表:', text.split())

solve()
```

```term
$ cat sample1.in | python one_line.py
[3, 1, 4, 1, 5, 9, 2, 6]
31 9
推导式版与循环版一致: True
推导式版与 map 版一致: True
token 表: ['3', '1', '4', '1', '5', '9', '2', '6']
```

产出的数据结构：`[3, 1, 4, 1, 5, 9, 2, 6]`，一个整数列表；`sum` 得 31，`max` 得 9。

转换这一步有三种写法，输出逐字一致（第 5 课那条：改写完必须对着原版比对输出）：

| 写法 | 代码 | 什么时候用 |
| --- | --- | --- |
| 列表推导式 | `[int(x) for x in text.split()]` | 默认写法 |
| 循环加 `append` | 先 `out = []`，再逐项 `out.append(int(x))` | 转换里还要顺手做别的事 |
| `map` | `list(map(int, text.split()))` | 转换函数已经现成，这里是 `int` |

`map` 返回迭代器（第 5 课），要收进列表才能反复用；只要直接喂给 `sum`、`max` 这类走一遍就完的函数，可以省掉 `list(...)`，写成 `sum(map(int, tokens))`。

::: quiz 应用 锚点：把单行多整数读成整数列表
:::

### 多行整数

样例 `sample2.in`，第一行给 `n`：

```text
5
3
-1
4
2
7
```

`many_lines.py`：

```python
import sys

def read_all():
    return sys.stdin.read()

def parse_n_then_lines(text):
    """第一行是 n，接下来 n 行每行一个整数。"""
    lines = [line for line in text.splitlines() if line.strip()]
    n = int(lines[0])
    return [int(line) for line in lines[1:n + 1]]

def solve():
    a = parse_n_then_lines(read_all())
    print(a)
    print(len(a), sum(a))

solve()
```

```term
$ cat sample2.in | python many_lines.py
[3, -1, 4, 2, 7]
5 15
```

数据结构：`[3, -1, 4, 2, 7]`，长度 5，与第一行的 `n` 对得上。第二个 `print` 就是输入层的自检——长度与题面给的个数一致，才轮到看答案 15 对不对。

三处边界：

- 取 `lines[1:n + 1]` 而不是 `lines[1:]`：按题面给的 `n` 取，多出来的行会被当成数据。
- `if line.strip()` 那一层是给空行准备的。`line.strip()` 去掉这一行首尾的空白（行尾的换行符也在内），空行于是剩下空字符串 `''`，被这个条件筛掉；`splitlines()` 正是把空行切成 `''` 的。而 `int('')` 与 `int('\n')` 都会报 `ValueError: invalid literal for int() with base 10: ''`。
- 用 `splitlines()` 而不是 `readline()`：后者交回的字符串末尾留着 `\n`。`int('5\n')` 虽然也能算出 5（`int` 会去掉首尾空白），但那个换行符会留在数据里，后面拿它做字符串处理时碍事。

不给 `n` 的版本，题面是「一行一个整数，给到输入结束」。样例 `sample2b.in`（第 4 行是空行，数据本身只有 5 个数）：

```text
3
-1
4

2
7
```

`many_lines_eof.py`：

```python
import sys

def read_all():
    return sys.stdin.read()

def parse_ints_to_eof(text):
    """不给 n：一行一个整数，读到没有为止，空行跳过。"""
    return [int(line) for line in text.splitlines() if line.strip()]

def solve():
    a = parse_ints_to_eof(read_all())
    print(a)
    print(len(a), sum(a))

solve()
```

```term
$ cat sample2b.in | python many_lines_eof.py
[3, -1, 4, 2, 7]
5 15
```

空行被 `if line.strip()` 跳过了，剩下的 5 个数一个不少。

### 矩阵 n×m

样例 `sample3.in`：

```text
3 4
1 2 3 4
5 6 7 8
9 10 11 12
```

矩阵有两种读法，`matrix.py` 把两种都写出来对比：

```python
import sys

def read_all():
    return sys.stdin.read()

def parse_matrix_by_lines(text):
    """按行读：第一行 n m，接下来正好 n 行、每行 m 个数。"""
    lines = [line for line in text.splitlines() if line.strip()]
    n, m = map(int, lines[0].split())
    return n, m, [list(map(int, line.split())) for line in lines[1:n + 1]]

def parse_matrix_by_tokens(text):
    """按空白读：token 从头取 n*m 个，再按 m 个一行切开。"""
    tokens = text.split()
    n, m = int(tokens[0]), int(tokens[1])
    vals = [int(x) for x in tokens[2:2 + n * m]]
    return n, m, [vals[i * m:(i + 1) * m] for i in range(n)]

def solve():
    text = read_all()
    n1, m1, a1 = parse_matrix_by_lines(text)
    n2, m2, a2 = parse_matrix_by_tokens(text)
    print('按行读 ->', a1)
    print('按空白读 ->', a2)
    print('两种读法一致:', a1 == a2)

solve()
```

```term
$ cat sample3.in | python matrix.py
按行读 -> [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]
按空白读 -> [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]
两种读法一致: True
```

数据结构：`[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]`，三行四列的二维列表（列表的列表）。取 `a[1][2]` 得 7：`a[1]` 是第二行 `[5, 6, 7, 8]`，再取它的第 3 个元素（下标从 0 起）。

按空白读那一版的核心是两步：先把 $n \times m$ 个数取成一段 `vals`，再按 `m` 个一段切开。

::: svg
alt: token 表按 m 个一段切片：表头两个 token 之后，vals 的前三个是第 0 行、后三个是第 1 行
caption: token 表与切片：第 i 行是 vals 上从 i*m 起的一段

<svg viewBox="0 0 520 170" role="img" aria-hidden="true">
  <g stroke="currentColor" fill="none">
    <rect x="22" y="24" width="116" height="32" stroke-dasharray="4 3"/>
    <rect x="28" y="24" width="52" height="32"/>
    <rect x="86" y="24" width="52" height="32"/>
    <rect x="144" y="24" width="52" height="32"/>
    <rect x="202" y="24" width="52" height="32"/>
    <rect x="260" y="24" width="52" height="32"/>
    <rect x="318" y="24" width="52" height="32"/>
    <rect x="376" y="24" width="52" height="32"/>
    <rect x="434" y="24" width="52" height="32"/>
    <path d="M144 58 L144 74 L312 74 L312 58"/>
    <path d="M318 58 L318 74 L486 74 L486 58"/>
  </g>
  <g font-family="sans-serif" fill="currentColor">
    <g font-size="12">
      <text x="22" y="16">表头：第一行 n m</text>
      <text x="228" y="92" text-anchor="middle">第 0 行：vals[0*3 : 1*3]</text>
      <text x="402" y="92" text-anchor="middle">第 1 行：vals[1*3 : 2*3]</text>
      <text x="28" y="124">vals = tokens[2 : 2 + n*m]　→　[4, 5, 6, 7, 8, 9]</text>
      <text x="28" y="152">第 i 行 = vals[i*m : (i+1)*m]（切片右端不包含）</text>
    </g>
    <g font-size="13" text-anchor="middle">
      <text x="54" y="45">2</text>
      <text x="112" y="45">3</text>
      <text x="170" y="45">4</text>
      <text x="228" y="45">5</text>
      <text x="286" y="45">6</text>
      <text x="344" y="45">7</text>
      <text x="402" y="45">8</text>
      <text x="460" y="45">9</text>
    </g>
  </g>
</svg>
:::

关于那段切片：

- 切片右端不包含（第 3 课）：`vals[i * m:(i + 1) * m]` 取的是第 `i` 行那 `m` 个数。
- 每一行是一个**新**列表（切片是复制，第 4 课那条口径），所以改一行里的某个数，不会串到别的行。
- 按行读那一版依赖「换行位置与题面一致」。`matrix.py` 拿到 `sample6.in` 时两种读法就不一致了——按行读得到 `[[1, 2, 3, 4], [5, 6], [7, 8]]`，这正是上一节那个 36 的来源。题面没讲清换行怎么排的时候，用按空白读的版本。

::: quiz 应用 锚点：把矩阵输入读成二维列表
:::

### 混合行列

样例 `sample4.in`：第一行 `n m`，接着是矩阵，然后一行给查询个数 `q`，再 `q` 行每行两个整数。

```text
3 4
1 2 3 4
5 6 7 8
9 10 11 12
2
1 1
3 4
```

`matrix_and_queries.py`：

```python
import sys

def read_all():
    return sys.stdin.read()

def parse_matrix_and_queries(text):
    """第一行 n m；接着 n*m 个数是矩阵；再一个 q；再 q 组「行 列」。"""
    tokens = text.split()
    n, m = int(tokens[0]), int(tokens[1])
    pos = 2
    vals = [int(x) for x in tokens[pos:pos + n * m]]
    pos += n * m
    matrix = [vals[i * m:(i + 1) * m] for i in range(n)]
    q = int(tokens[pos])
    pos += 1
    queries = []
    for _ in range(q):
        r, c = int(tokens[pos]), int(tokens[pos + 1])
        pos += 2
        queries.append((r, c))
    print('还剩没用的 token:', tokens[pos:])
    return matrix, queries

def solve():
    matrix, queries = parse_matrix_and_queries(read_all())
    print(matrix)
    print(queries)
    for r, c in queries:
        print(r, c, '->', matrix[r - 1][c - 1])

solve()
```

```term
$ cat sample4.in | python matrix_and_queries.py
还剩没用的 token: []
[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]
[(1, 1), (3, 4)]
1 1 -> 1
3 4 -> 12
```

数据结构是两块：`matrix` 是三行四列的二维列表；`queries` 是元组的列表 `[(1, 1), (3, 4)]`。最后两行说明查询里的行列从 1 数起（第 3 行第 4 列是 12），所以取值要写 `matrix[r - 1][c - 1]`。

`pos` 是这一版的要点：读的位置从隐式的读指针变成了一个**显式的下标变量**，可以打印、可以对照长度。最后那行 `还剩没用的 token: []` 就是输入层的自检——token 一个不剩，说明个数都对上了；剩下若干个说明有数据没读，`pos` 越过末尾则说明读多了。

::: quiz 应用 锚点：混合行列读成矩阵与查询两块
:::

### 多组数据与空行

样例 `sample5.in`（组间有空行，末尾也有一个空行）：

```text
2

3
1 2 3

4
10 20 30 40

```

`groups.py`：

```python
import sys

def read_all():
    return sys.stdin.read()

def parse_groups_with_t(text):
    """第一行是组数 t；每组先一行 n，再来 n 个数。"""
    tokens = text.split()
    t = int(tokens[0])
    pos = 1
    groups = []
    for _ in range(t):
        n = int(tokens[pos])
        pos += 1
        groups.append([int(x) for x in tokens[pos:pos + n]])
        pos += n
    print('读完时 pos =', pos, '/ token 总数 =', len(tokens))
    return groups

def solve():
    groups = parse_groups_with_t(read_all())
    print(groups)
    print([sum(g) for g in groups])

solve()
```

```term
$ cat sample5.in | python groups.py
读完时 pos = 10 / token 总数 = 10
[[1, 2, 3], [10, 20, 30, 40]]
[6, 100]
```

数据结构：`[[1, 2, 3], [10, 20, 30, 40]]`，列表的列表，每一组是内层列表。`pos` 与 `len(tokens)` 都是 10，说明空行什么都没影响——`split()` 把空行当成空白，切完就没了。这条也正是「末尾空行」与「组间空行」在按空白切分的读法下不需要额外代码的原因。

不给组数的版本（一直读到输入结束），样例 `sample5b.in`：

```text
3
1 2 3

4
10 20 30 40

```

`groups_to_eof.py` 把 `pos` 指针换成 `while pos < len(tokens)`：

```python
import sys

def read_all():
    return sys.stdin.read()

def parse_groups_to_eof(text):
    """不给组数：一直读到 token 用完。"""
    tokens = text.split()
    pos = 0
    groups = []
    while pos < len(tokens):
        n = int(tokens[pos])
        pos += 1
        groups.append([int(x) for x in tokens[pos:pos + n]])
        pos += n
    return groups

def solve():
    print(parse_groups_to_eof(read_all()))

solve()
```

```term
$ cat sample5b.in | python groups_to_eof.py
[[1, 2, 3], [10, 20, 30, 40]]
```

两种版本的差别只在有没有组数这一行，空行在两种版本里都不需要额外处理。

同一份输入用 `input()` 逐行读就会崩，崩的位置还很容易看错：

```python
t = int(input())
for _ in range(t):
    n = int(input())
    a = list(map(int, input().split()))
    print(sum(a))
```

```term
$ cat sample5.in | python groups_by_input.py
Traceback (most recent call last):
  File "groups_by_input.py", line 3, in <module>
    n = int(input())
ValueError: invalid literal for int() with base 10: ''
```

报错指的是第 3 行，`int('')` 的原因却是第 2 行那个空行——它被 `input()` 当成了一行的内容。找错的第一个动作是把它打出来看：`print(repr(input()))` 会显示 `'\n'`，一看就知道读到的是一行空行，而不是一个数。

::: quiz 应用 锚点：多组数据读成列表的列表
:::

## 读进来的都是字符串

教材讲 `input()` 时给过一句要紧的话：**使用函数 `input()` 时，Python 将用户输入解读为字符串。** 书里的例子是问年龄，敲 21，变量拿到的是 `'21'`。它接着说：如果只想打印输入，这一点问题都没有；但要把它当数用，就会引发错误——书里那行 `age >= 18` 报的就是类型错误（在本机 3.14 上，这条报错现在的写法是 `TypeError: '<' not supported between instances of 'str' and 'int'`）。

`sys.stdin` 这条路一样：token 表里全是字符串。两个字符串比较的时候不会报类型错误，规则换成了另一套：

```python
print('10' < '9')
print('2' < '10')
print(sorted(['10', '9', '100', '2']))
print(sorted(['10', '9', '100', '2'], key=int))
print(max(['10', '9']), min(['10', '9']))
print(max([int(x) for x in ['10', '9']]))
```

```term
$ python str_cmp.py
True
False
['10', '100', '2', '9']
['2', '9', '10', '100']
9 10
10
```

结果都反直觉：`'10'` 小于 `'9'`；排序出来 `'100'` 排在 `'2'` 前面；`max(['10', '9'])` 得 `'9'`，转成整数再求最大才是 10。

原因是**字符串比较按字符逐个进行**：从第 1 个字符起比编码顺序，一旦不同就定了输赢，长度根本轮不到参与。`'1'` 的编码是 49，`'9'` 的编码是 57，`'10'` 的第 1 个字符更小，结论当场就定下了。

::: svg
alt: 字符串 10 与 9 逐字符比较：第一位 1 的编码 49 小于 9 的编码 57，比较在此结束
caption: 字符串比较按位：第一位分出大小，后面的字符没轮到

<svg viewBox="0 0 520 180" role="img" aria-hidden="true">
  <g stroke="currentColor" fill="none">
    <rect x="88" y="28" width="52" height="52" stroke-dasharray="4 3"/>
    <rect x="88" y="94" width="52" height="52" stroke-dasharray="4 3"/>
    <rect x="90" y="30" width="48" height="48"/>
    <rect x="150" y="30" width="48" height="48"/>
    <rect x="90" y="96" width="48" height="48"/>
  </g>
  <g font-family="sans-serif" fill="currentColor">
    <g font-size="22" text-anchor="middle">
      <text x="114" y="64">1</text>
      <text x="174" y="64">0</text>
      <text x="114" y="130">9</text>
    </g>
    <g font-size="12">
      <text x="16" y="60">s1 = '10'</text>
      <text x="16" y="126">s2 = '9'</text>
      <text x="230" y="46">第 1 位：'1' 的编码是 49</text>
      <text x="230" y="76">第 1 位：'9' 的编码是 57</text>
      <text x="230" y="112">57 更大，比较在这里结束</text>
      <text x="16" y="172">'0' 没轮到：字符串比较从第 1 个字符起逐个比，一旦不同就结束</text>
    </g>
  </g>
</svg>
:::

编码可以用 `ord()` 直接看：`ord('1')` 得 49，`ord('9')` 得 57。

修法落在转换的时机上：**在解析层一次转完，算法层看不到数字字符串。** 这一课的五份模板都是这个结构——`parse_*` 交给 `solve` 的数据里，数字已经是 `int`。三条纪律：

- 解析函数的输出里不放数字字符串；
- 求和、求极值、比较、排序之前，用 `print(type(a[0]), a[:5])` 看一眼类型与前几个值；
- 要输出的时候再让数字变回文本，这件事 `print` 自己做。

一个字符串与一个整数混着比会当场报错：`'10' < 5` 得 `TypeError: '<' not supported between instances of 'str' and 'int'`。报错拦下你是好事；两个都是字符串时它不报错，这才是这个坑难查的原因。

::: quiz 排错 锚点：把字符串当数字比较
:::

## 用打印定位错误

本节的手法都围绕一件事：**先把出错的位置缩小，再改代码**。在二十行代码里随机加 `print`，只会让输出变长。

1. 先跑最小样例。拿题面给的第一组样例（通常最小），不要从大样例开始。大样例只会告诉你「错了」，最小样例能让你把中间值一眼读完。
2. 打印数据结构与它的长度。`print('n m =', n, m)`、`print(len(row), row)`，与题面给的 `n`、`m` 对一遍。长度对不上就是解析层的问题，算法先别看。
3. 用 `repr()` 看不可见的字符。`print(repr(line))` 会把引号、`\n`、多余的空格显示出来（官方教程在讲输出格式时给过这条：只想快速显示变量进行调试，可以用 `repr()` 或 `str()`）。空行导致的 `ValueError` 靠它一眼分清读到的是 `'\n'` 还是 `''`。
4. 把「读」与「算」分开打印。先打印全部数据结构，再打印算法结果：答案不对而数据结构是对的，问题在算法；数据结构本身就错，先修解析。这一步能省掉大量来回。
5. 二分注释掉一半。确认数据结构没错之后，把 `solve()` 的后半先注释掉、或者先 `return` 前半的结果，看答案从哪一半开始不对，范围每次减半。
6. 打印指针下标。token 版的解析里 `pos` 是显式变量，`print('pos', pos, 'len', len(tokens))` 一句话告诉你读多了还是读少了（多组数据那份模板里就是这么自检的）。
7. 改对了就收手。调试用的 `print` 必须在提交前删掉，原因见下一节。

走一遍完整的例子。要算矩阵所有数的和，切片右端写错了一个：

```python
import sys

def read_all():
    return sys.stdin.read()

def parse_matrix(text):
    tokens = text.split()
    n, m = int(tokens[0]), int(tokens[1])
    vals = [int(x) for x in tokens[2:2 + n * m]]
    return n, m, [vals[i * m:i * m + m - 1] for i in range(n)]

def solve():
    n, m, a = parse_matrix(read_all())
    print('n m =', n, m)
    for i, row in enumerate(a):
        print('第', i, '行长度', len(row), row)
    print('总和', sum(sum(row) for row in a))

solve()
```

```term
$ cat sample3.in | python slice_bug.py
n m = 3 4
第 0 行长度 3 [1, 2, 3]
第 1 行长度 3 [5, 6, 7]
第 2 行长度 3 [9, 10, 11]
总和 54
```

输出里的 `n m = 3 4` 说每行该有 4 个数，紧接着的「行长度 3」说只有 3 个，结论就出来了：每一行少了 1 个数，问题在切片的右端（`i * m + m - 1`）。改回 `(i + 1) * m`：

```term
$ cat sample3.in | python slice_fixed.py
n m = 3 4
第 0 行长度 4 [1, 2, 3, 4]
第 1 行长度 4 [5, 6, 7, 8]
第 2 行长度 4 [9, 10, 11, 12]
总和 78
```

这次定位只用了两行输出，靠的是第 2 条手法。切片右端写错这类 bug 不会报错，只会让结果偏小，属于必须靠打印长度才能找出来的那一类。

::: quiz 排错 锚点：用打印缩小出错范围
:::

## 提示文字混进标准输出

教材在讲 `input()` 时给了一条写法建议：每当使用函数 `input()` 时，都应指定清晰易懂的提示。它面向的程序是交互式的：程序暂停下来等人敲一行，提示告诉你该输入什么。蓝桥杯的评测机不读提示。它把标准输入接到数据文件上，运行你的程序，然后拿你的标准输出与标准答案**逐字比对**——多一个字符、多一行、少一个换行都算错。

`input()` 的提示走哪条流，官方文档在讲 `sys.stdin` 的地方写明了：`stdout` 用于 `print()` 和表达式语句的输出，**以及用于 `input()` 的提示符**。提示与答案走的是同一条流，评测机读的正是它。

实测一次，把两条流分别重定向到两个文件：

```python
n = int(input("请输入 N："))
print(n * 2)
```

```term
$ echo 10 | python prompt_demo.py > out.txt 2> err.txt
$ cat out.txt
请输入 N：20
$ cat err.txt
```

`err.txt` 是空的。提示「请输入 N：」紧贴在答案 `20` 前面，占的是标准输出——在评测机上，这一行就是让逐字比对失败的那一行。

::: svg
alt: input 的提示文字写进 stdout，stderr 里什么都没有，评测机读的是 stdout
caption: 提示与答案走同一条流：stderr 里空无一物，评测机只读 stdout

<svg viewBox="0 0 520 195" role="img" aria-hidden="true">
  <g stroke="currentColor" fill="none">
    <rect x="12" y="64" width="150" height="64"/>
    <rect x="222" y="18" width="170" height="52"/>
    <rect x="222" y="122" width="170" height="52"/>
    <rect x="412" y="18" width="96" height="52"/>
    <path d="M162 76 L192 76 L192 44 L222 44"/>
    <path d="M162 116 L192 116 L192 148 L222 148"/>
    <path d="M392 44 L412 44"/>
  </g>
  <g font-family="sans-serif" fill="currentColor" font-size="12">
    <text x="24" y="88">程序</text>
    <text x="24" y="110">input("请输入 N：")</text>
    <text x="234" y="40">stdout（标准输出）</text>
    <text x="234" y="62">请输入 N：20</text>
    <text x="234" y="144">stderr（标准错误）</text>
    <text x="234" y="166">什么都没有</text>
    <text x="422" y="40">评测机</text>
    <text x="422" y="62">逐字比对</text>
    <text x="12" y="188">提示走 stdout 这条流，评测机读的正是它</text>
  </g>
</svg>
:::

于是两条规矩：

- 竞赛代码里用 `input()` 时，括号里永远不写参数；
- `print` 只打印答案本身。`print('答案：', x)` 与 `print(x)` 之间的差别，就是判零分与满分之间的差别。

这一课的模板顺带解决了第一条：读入走 `sys.stdin.read()`，`input()` 根本不出现，想加提示也没有地方加。哪道题非用 `input()` 不可的时候，提交前做两个搜索：

- 搜 `input(`：括号里凡是写了东西的，删掉；
- 搜 `print(`：凡是打印内容与答案无关的（调试行、长度检查、`n m`、`还剩没用的 token`），删掉。

第 1 课记下的这条误解在这里落到手上：它从一条「知道就好」的注意事项，变成提交前要动手检查的两处。

::: quiz 排错 锚点：input 提示混进标准输出
:::

## 样例与提交的两条路径

同一道题在这门课里要跑两条路：自测的时候你在本机跑，提交的时候评测机跑。两条路的接口是同一个——标准输入与标准输出。所以自测的做法是把样例输入存成文件，再把这个文件接到标准输入上：

```term
$ cat sample1.in | python one_line.py
[3, 1, 4, 1, 5, 9, 2, 6]
```

Windows 的 cmd 里也可以写 `python one_line.py < sample1.in`；PowerShell 不支持 `<`，用 `cat 文件 | python 程序.py` 这一行。这条命令下程序读到的标准输入就是那个文件的内容，提交时评测机做的事与它一样，只是换了一份数据。

由此有三条自测纪律：

- 别在代码里写死样例文件名。程序里出现「打开某个固定文件」这一步，提交时那个文件不存在，而评测机给的是标准输入。
- 输出与样例逐字对一遍，包括空格与换行。这一步也是调试痕迹暴露的地方：多出来的 `还剩没用的 token: []` 在这里就会露出来。
- 每组样例都先打印一次解析结果（长度与内容），对上了再看答案。这一课的五组样例就是这么过的；把数据结构的检查与算法答案的检查分开做，出错时能省一半时间。

输入层写错的人常常以为是算法错了。数据少读了一段、多读了一位，算法拿到的数据结构就不对，算出来的结果自然不对，而报错信息可能落在算法那一半。先打印数据结构这一步，把这两件事分开了。

## 这一课用到的 Python

| 要做的事 | 写法 | 边界 |
| --- | --- | --- |
| 一次读完 | `sys.stdin.read()` | 读完之后流停在末尾，再 `input()` 会 `EOFError` |
| 按空白切分 | `text.split()` | 连续空白算一个，首尾丢掉；空串得 `[]` |
| 按行切分 | `text.splitlines()` | 不保留行尾换行符；`readline()` 会保留 `\n` |
| 空行跳过 | `if line.strip()` | `int('')`、`int('\n')` 都报 `ValueError` |
| 转成整数 | `[int(x) for x in tokens]` | 与 `list(map(int, tokens))`、循环加 `append` 输出一致 |
| 快速读入 | `sys.stdin.buffer.read().split()` | token 是 `bytes`，`int()` 同样接 |
| n×m 铺成二维列表 | `[vals[i*m:(i+1)*m] for i in range(n)]` | 切片右端不包含；每行是新列表 |
| 多组数据 | `t = int(tokens[0])` 加 `pos` 指针 | 每组结束要 `pos += n`；读完打印 `pos` 与 `len(tokens)` 核对 |
| 一行一个整数 | `[int(line) for line in text.splitlines() if line.strip()]` | 行数由输入决定时用这版 |
| 看不可见字符 | `print(repr(line))` | 显示引号与 `\n` |
| 读一行整数 | `n = int(input())` | 竞赛代码里括号不写参数；提示会写进 stdout |
| 比大小、排序前 | 先转 `int` | `'10' < '9'` 是 `True`；`sorted` 要 `key=int` |

这一课练的动作会一直用下去：紧接着的实验一要把读入、求解、输出组装成一个能跑的脚本，读入那一半就是这里的五份模板；第 3 课的容器选择决定解析出来的数据结构长什么样；第 5 课的推导式与 `map` 负责把 token 表变成数字。先读完、再算，后面每一道题都从这一步开始。

::: practice 练习 | 五组样例与一次打印定位

这一课的动手部分落在 lab 里（任务与断言见 [lab/0006-python-io-and-debug/](../lab/0006-python-io-and-debug/)，做完对照 [lab/solutions/](../lab/solutions/)）。要做的是三件事。

1. 备五组不同格式的样例（单行多整数、多行整数、矩阵、混合行列、末尾空行），每组用这一课的模板解析成指定的数据结构，并把结果打印出来与题面核对。每一组都要写清你产出的数据结构长什么样（每一维有多少个元素、元素是什么类型）。
2. 在解析或求解里故意写错一处下标，先用最小样例跑一次，再用打印（长度、`repr`、指针下标）把出错范围缩到某一处，改对。记下你打印了什么、看到什么、据此得出什么结论。
3. 交出去之前把调试用的 `print` 全部删掉，确认标准输出只剩答案那一行：拿样例输入跑一遍，输出与题面样例逐字对得上。

:::

::: resources
- [Python 官方文档 · sys](https://docs.python.org/zh-cn/3/library/sys.html) | `stdin`、`stdout`、`stderr` 是常规文本文件对象；`input()` 的调用与提示符都走它们；二进制读写用底层 `buffer`——本课的主要依据
- [Python 官方教程 · 输入与输出](https://docs.python.org/zh-cn/3/tutorial/inputoutput.html) | 7.1 用 `repr()` 或 `str()` 调试；7.2.1 文件对象的方法：`read` 省略 `size` 读回全部、`readline()` 保留行尾换行符、空行是 `'\n'`、遍历文件对象、`readlines()`
- [Python 官方文档 · 内置函数](https://docs.python.org/zh-cn/3/library/functions.html) | `input()`、`int()`、`map()` 的签名与边界
- [OI Wiki · 复杂度](https://oi-wiki.org/basic/complexity/) | 空间复杂度与「常数」的口径，判断一次读完要付多少代价时用
- 《Python 编程：从入门到实践（第 2 版）》第 7 章 用户输入和 while 循环 | 本地教材：7.1 `input()` 的工作原理与提示（prompt），7.1.2 输入得到的是字符串、把它当数用会报类型错误
:::
