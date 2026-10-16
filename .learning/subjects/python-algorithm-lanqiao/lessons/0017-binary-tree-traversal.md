---
title: 树：会递归的结构
goal: 能用嵌套列表表示二叉树，写出前中后序与层序四种遍历，并用递归求树高、节点数与对称性。
---

## 树是递归定义的

前面十五课里的数据结构都是「平」的：列表按下标排成一行，栈和队列在一端进出，字典按键取值。树是第一个**有层次**的结构。

**树**（tree）是由 $n$ 个结点组成的有限集合。$n = 0$ 时称为**空树**；$n > 0$ 时有一个特定的结点称为**根**（root），其余结点被分成若干个互不相交的集合，每个集合本身又是一棵树，称为根的**子树**（subtree）。

这段定义里藏着一件事：**树的定义里出现了「树」这个词**。定义一棵树要用到更小的树，这与第 12 课讲的递归定义是同一件事。所以树的代码写成递归版是自然结果，不需要额外想办法。

几个后面会反复用到的词：

| 词 | 含义 |
| --- | --- |
| 根 | 最上面那个结点，它没有父结点 |
| 叶子 | 没有子结点的结点 |
| 子树 | 某个结点及其全部后代构成的树 |
| 结点的深度 | 从根到它的路径长度；根的深度是 0 |
| 树高 | 所有结点深度的最大值加一，也就是层数 |
| 二叉树 | 每个结点最多有两个子结点，分别叫左孩子与右孩子 |

二叉树的两个孩子有左右之分，这一点在判断对称时是关键。

::: quiz 理解 锚点：树的递归定义体现在哪里
:::

## 用嵌套列表表示树

二叉树有几种常见表示。这一课用**嵌套列表**，它把结构直接摆在代码里：

- 空树用 `None` 表示；
- 一个结点写成 `[值, 左子树, 右子树]`。

按这个约定搭一棵树：

```python
def node(v, l=None, r=None):
    return [v, l, r]

#        A
#      /   \
#     B     C
#    / \     \
#   D   E     F
T = node('A', node('B', node('D'), node('E')), node('C', None, node('F')))
```

这棵树的 6 个结点里，`D`、`E`、`F` 是叶子；`C` 只有右孩子；`B` 有两个孩子。整棵树的形状与上面的图一致。

选嵌套列表的理由是**基例一眼可见**：空树就是 `None`，代码里写 `if t is None` 就够了。用类来写（`class TreeNode`）也可以，但这一课不需要——把注意力留给遍历本身。

::: warn 空树必须作为基例
`if t is None: return ...` 是每个树函数的第一句。漏掉它不会算出一堆错误答案，而是**当场停下来**，报的是 `TypeError: 'NoneType' object is not subscriptable`。

崩的位置是第一个叶子那个不存在的孩子：拿示例树来说，走到 `D` 时会去调 `preorder(None)`，接着执行 `None[0]`——`None` 不能下标，于是报错。注意这个基例拦的不只是「整棵树是空的」，也拦「某个结点的孩子不存在」：`C` 的左孩子就是 `None`，遍历一定会走到那里。

这种「漏基例」的报错与第 12 课那种爆栈不一样。爆栈是递归不收敛、层数越堆越深；这里是**第一次碰到空结点就当场报错**，位置明确。看到 `NoneType` 就去想「哪个函数的基例漏了」。
:::

::: quiz 排错 锚点：空节点没作为基例处理
:::

## 三种遍历

**遍历**（traversal）指按某种顺序把每个结点访问一次。二叉树有三种主要的递归遍历，区别只在「根在什么时候被访问」：

```python
def preorder(t):
    if t is None:
        return []
    return [t[0]] + preorder(t[1]) + preorder(t[2])

def inorder(t):
    if t is None:
        return []
    return inorder(t[1]) + [t[0]] + inorder(t[2])

def postorder(t):
    if t is None:
        return []
    return postorder(t[1]) + postorder(t[2]) + [t[0]]

print('前序', preorder(T))
print('中序', inorder(T))
print('后序', postorder(T))
```

```text
前序 ['A', 'B', 'D', 'E', 'C', 'F']
中序 ['D', 'B', 'E', 'A', 'C', 'F']
后序 ['D', 'E', 'B', 'F', 'C', 'A']
```

三个函数几乎一样，差别只在那一行里 `[t[0]]` 的位置：

| 遍历 | 根的位置 | 记法 | 示例树的结果 |
| --- | --- | --- | --- |
| 前序 | 最前 | 根 → 左子树 → 右子树 | `A B D E C F` |
| 中序 | 中间 | 左子树 → 根 → 右子树 | `D B E A C F` |
| 后序 | 最后 | 左子树 → 右子树 → 根 | `D E B F C A` |

名字里的「前中后」指的就是根被访问的位置。写成递归之后，**子树内部的顺序由同一个函数自己保证**——你不需要在脑子里模拟整棵树的每一层，只要确认「根放在哪、左子树交给自己、右子树交给自己」这三件事，剩下的自然成立。

::: quiz 理解 锚点：三种遍历的区别与命名由来
:::

::: quiz 排错 锚点：遍历顺序与题目要求对不上
:::

## 层序遍历用队列

三种递归遍历都在往深处走。还有一种走法是**一层一层**来，叫**层序遍历**（也叫广度优先遍历）。

它不好写成递归，因为「先访问完第 1 层再访问第 2 层」这个要求与栈的次序相反。用第 10 课的队列才对：

```python
from collections import deque

def level_order(t):
    if t is None:
        return []
    out = []
    q = deque([t])
    while q:
        x = q.popleft()
        out.append(x[0])
        if x[1] is not None:
            q.append(x[1])
        if x[2] is not None:
            q.append(x[2])
    return out

print('层序', level_order(T))
```

```text
层序 ['A', 'B', 'C', 'D', 'E', 'F']
```

队列里存的每一项都是**子树**（一个 `[值, 左, 右]` 列表），不是单个值。取出一个结点时先把它的值收进结果，再把它存在的孩子从右边排进队列。先进先出这条性质保证了：同一层的结点按从左到右的次序被处理。

用 `list` 加 `pop(0)` 也能写，但第 3 课量过：`pop(0)` 要从头部挪动整个列表，20 万次约 2.74 秒，而 `deque.popleft()` 约 0.013 秒。层序遍历里每个结点出队一次，正是这条差距被放大的地方。

::: quiz 理解 锚点：层序遍历为什么用队列
:::

## 递归返回值汇总子树

树函数的通用写法是：**在每个结点上，用两个孩子交回的答案算出自己的答案**。求节点数与树高就是这样：

```python
def count(t):
    if t is None:
        return 0
    return 1 + count(t[1]) + count(t[2])

def height(t):
    if t is None:
        return 0
    return 1 + max(height(t[1]), height(t[2]))

print('节点数', count(T), ' 树高', height(T))
```

```text
节点数 6  树高 3
```

看 `height` 那一行：左子树交回一个高度，右子树交回一个高度，两边取较大者再加一（加上根自己这一层）。**递归的返回值就是「这棵子树的高度」**，于是整棵树的答案由两个子树的答案拼出来。这个形状在第 24 课（动态规划）里会再见到一次。

判断对称是同一套写法的两两配对版本：

```python
def is_mirror(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return a[0] == b[0] and is_mirror(a[1], b[2]) and is_mirror(a[2], b[1])

def is_symmetric(t):
    return t is None or is_mirror(t[1], t[2])

S = node('A', node('B', node('D')), node('B', None, node('D')))
print('对称树', is_symmetric(S))
print('示例树', is_symmetric(T))
print('空树', is_symmetric(None))
print('单点', is_symmetric(node('A')))
print('只差一个值', is_symmetric(node('A', node('B'), node('C'))))
```

```text
对称树 True
示例树 False
空树 True
单点 True
只差一个值 False
```

`is_mirror(a, b)` 问的是「以 `a` 为根的子树与以 `b` 为根的子树是否互为镜像」。注意最后一行里两个递归调用的参数：`is_mirror(a[1], b[2])` 与 `is_mirror(a[2], b[1])` —— **左对右、右对左**，这就是「镜像」在代码里的写法。若写成 `a[1]` 对 `b[1]`，判的就不是对称而是「两棵子树一模一样」。

四个基例分支（都空、只有一个空、都非空）缺一个都会算错。`a is None or b is None` 这一句能拦住「一边空一边不空」的情形——它交回 `False`，而漏掉它就会去取 `None[0]` 而报错。

::: quiz 应用 锚点：用递归返回值汇总子树信息
:::

## 树高与递归深度

上一节问的是「树有多高」。这一节问的是另一件事：**算这棵树的时候，递归会走到多深？**

两者在平衡树上接近，在不平衡树上差得很远。造两种形状来量：

```python
import sys

def build_balanced(n):
    def rec(k):
        if k == 0:
            return None
        left = k // 2
        return node(k, rec(left), rec(k - 1 - left))
    return rec(n)

def build_chain(n):
    t = None
    for i in range(n):
        t = node(i, t, None)
    return t

for n in (998, 999, 1000):
    try:
        print(f'链长 {n:>5} 树高 {height(build_chain(n))}  跑得动')
    except RecursionError:
        print(f'链长 {n:>5}  RecursionError')

for n in (1000, 100000):
    print(f'n={n:>6} 平衡树树高 {height(build_balanced(n))}')
print('当前递归上限', sys.getrecursionlimit())
```

```text
链长   998 树高 998  跑得动
链长   999  RecursionError
链长  1000  RecursionError
n=  1000 平衡树树高 10
n=100000 平衡树树高 17
当前递归上限 1000
```

链状树（每个结点只有左孩子）在 998 层时还跑得动，999 层就抛 `RecursionError`。这个数字与第 12 课实测的「最深进入 998 层」完全一致——同一个上限，在那里由函数的自我调用撞上，在这里由树的深度撞上。

同样是一千个结点，平衡树的高度是 10；十万个结点的平衡树高度只有 17。递归的深度等于树高，所以：

| 树的形状 | $n$ 个结点时的树高 | 递归深度 |
| --- | --- | --- |
| 平衡树 | 约 $\log_2 n$ | 十万结点也只有 17 层 |
| 链状树 | $n$ | 一千结点就爆栈 |

这就是这一课与第 12、13 课共用的那条判断：**递归深度取决于形状，不取决于规模**。

::: warn 题目数据可能故意给一条链
多数题目给的树是随机的，深度接近 $\log n$；但有的题会专门给「一条链」或者「每层只挂一个孩子」的极端数据。递归写法在这种输入上会爆栈。规模到 $10^5$ 时不要假设树的深度很小——要么按题目保证的平衡性来判断，要么改用显式栈的迭代写法。
:::

::: quiz 排错 锚点：不平衡的树上递归过深爆栈
:::

## 拼接结果的隐藏代价

前面三个遍历用的是「左子树结果 + 根 + 右子树结果」这种拼接写法。它读起来最贴近定义，但**每一层都要复制一遍子树的结果**，而子树的大小与树的形状有关。

把拼接版与累加器版放在一起量：

```python
import time

def preorder_acc(t, out=None):
    if out is None:
        out = []
    if t is None:
        return out
    out.append(t[0])
    preorder_acc(t[1], out)
    preorder_acc(t[2], out)
    return out

for n in (200, 400, 800):
    ct = build_chain(n)
    best_concat = 1e9
    best_acc = 1e9
    for _ in range(20):
        t0 = time.perf_counter()
        preorder(ct)
        t1 = time.perf_counter()
        if t1 - t0 < best_concat:
            best_concat = t1 - t0
        t0 = time.perf_counter()
        preorder_acc(ct)
        t1 = time.perf_counter()
        if t1 - t0 < best_acc:
            best_acc = t1 - t0
    print(f'链长 {n:>4}  拼接 {best_concat:.6f} 秒   累加器 {best_acc:.6f} 秒')
```

秒数取 20 次里最快的一次，即使这样每次运行的末几位仍会有浮动：

```text
链长  200  拼接 0.000054 秒   累加器 0.000012 秒
链长  400  拼接 0.000192 秒   累加器 0.000035 秒
链长  800  拼接 0.000726 秒   累加器 0.000081 秒
```

链长从 200 涨到 800（四倍），拼接版从 0.000054 秒涨到 0.000726 秒（约 13 倍），每翻一倍涨约 3.6 到 3.8 倍——这是平方级的形状。累加器版只涨约 6.8 倍，接近线性的两倍。

同一对函数放到**平衡树**上，差距要小得多：$n = 4000$ 时拼接 0.000484 秒、累加器 0.000349 秒，只差约 1.4 倍。原因还是形状：平衡树上每个结点的子树都不大，拼接要复制的量少；链状树上越靠近根的结点，子树越大，复制的总量按平方级涨。

所以这一条判断有两层：

- 遍历这种「把结果收集起来」的函数，用**累加器**（传一个列表进去，往里面 `append`）比拼接结果稳。
- 代价与**树的形状**有关，不只是与 $n$ 有关。测性能时不能只测一种形状。

::: quiz 排错 锚点：拼接结果在链状树上的平方级代价
:::

## 这一课用到的判断

- **树是递归定义的**，所以树函数写成递归是自然结果。每个函数的第一句都是 `if t is None` 这个基例。
- **三种遍历只差根的位置**：前序在最前、中序在中间、后序在最后。子树内部交给同一个函数自己保证。
- **层序遍历用队列**，不能用递归；队列里存的是子树，`deque.popleft()` 而不是 `list.pop(0)`。
- **递归返回值用来汇总子树信息**：节点数、树高、是否对称都是「两个孩子交回答案，在根上合并」。
- **递归深度等于树高**，而树高取决于形状：平衡树约 $\log_2 n$（十万结点 17 层），链状树是 $n$（不到一千层就爆栈）。
- **收集结果用累加器，不要拼接**。拼接版在链状树上的代价是平方级。

::: practice 上手做 | 九个小函数与两种树的形状

这一课的动手部分落在 lab 里（任务与断言见 [lab/0017-binary-tree-traversal/](../lab/0017-binary-tree-traversal/)，做完对照 [lab/solutions/](../lab/solutions/)）。要做的是四件事。

1. 把 `node`、`preorder`、`inorder`、`postorder`、`level_order` 五个函数抄进一个文件，用嵌套列表搭出课件那棵示例树，确认四种遍历的输出与课件逐字一致；再自己搭两棵树（一棵只有左孩子一直往下的链、一棵每层都挂满的平衡树）各跑一遍。
2. 补 `count`、`height`、`is_mirror`、`is_symmetric` 四个函数，在示例树之外再造四组数据（空树、单点、对称树、只有一处不同的树），把四组结果做成一张表。
3. 造一张「形状与递归深度」的表：链状树与平衡树各取 $n$ 为 100、1000、10000，数出树高；把链状树的 $n$ 逐步加到爆栈，记下那个临界值，并与第 12 课的上限对照。
4. 把前序遍历写成两个版本（拼接版与累加器版），在链状树与平衡树上各量一次耗时，做成一张表；指出哪一列的形状不是线性。

:::

::: resources
- [OI Wiki · 树基础](https://oi-wiki.org/graph/tree-basic/) | 树的定义与术语、四种存储方式、树上 DFS 与 BFS、二叉树遍历（本课术语口径出自这里）
- 《算法导论（第 3 版）》第 12 章 二叉搜索树 | 书 · 树的遍历与递归结构；当参考书查
- [Python 官方文档 · collections](https://docs.python.org/zh-cn/3/library/collections.html) | `deque` 的两端进出都是 $O(1)$，层序遍历用它（第 10 课已量过代价）
:::

::: related
- [第 12 课：递归：函数调用自己](0012-recursion-and-stack.html)
- [第 10 课：后进先出与先进先出](0010-stack-and-queue.html)
:::
