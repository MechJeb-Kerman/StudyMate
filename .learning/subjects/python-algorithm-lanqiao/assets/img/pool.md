# Python 算法与蓝桥杯 · 图片库索引

本索引是课件挑图的唯一检索入口：课件读本文件，不翻 `pool/` 目录。
`主题标签` 与文件名用同一套词，主题词逐字取自科目 `GLOSSARY.md`（`算法`、`数据结构`、`栈`、`队列`、`堆`、`哈希表`、`二分查找`…）。

| 文件 | 主题标签 | 一句话说明 | 来源 URL | 许可 | 尺寸 | 抓取日期 |
|---|---|---|---|---|---|---|
| 数据结构-堆-上浮插入-commons-01.png | 数据结构 / 堆 | 向二叉堆插入新元素、新结点与父结点逐层比较交换的"上浮"过程：能讲清堆插入为什么是 O(log n)；**图中示例是 max-heap，讲 Python `heapq`（最小堆）时须说明"方向相反"** | https://commons.wikimedia.org/wiki/File:Dsa_binary_heap_push.png | CC BY 3.0 | 585×458 | 2026-10-04 |
| 数据结构-堆-数组存储-commons-01.png | 数据结构 / 堆 | 同一棵完全二叉树的"树形"与"数组（列表）"两种画法并排对照：能讲清堆用连续存储实现、父子下标关系（2i+1 / 2i+2）以及为什么堆不用指针 | https://commons.wikimedia.org/wiki/File:Dsa_binary_heap_array.png | CC BY 3.0 | 500×140 | 2026-10-04 |
| 数据结构-哈希表-拉链法冲突-commons-01.png | 数据结构 / 哈希表 | 两个不同的键被哈希到同一个槽位时，用链表把冲突元素挂在同一槽后的"拉链"示意：能讲清哈希表平均 O(1)、最坏退化（查时要顺着链表逐个走），以及 `dict`/`set` 冲突处理的直观模型 | https://commons.wikimedia.org/wiki/File:Hashtable_linkedlist_collision.png | CC BY-SA 2.5 | 500×246 | 2026-10-04 |
| 数据结构-队列-广度优先访问顺序-commons-01.gif | 数据结构 / 队列 | 广度优先搜索的访问顺序动画：一层一层向外扩展，先入队的先被访问——正是队列"先进先出"在算法里的用处 | https://commons.wikimedia.org/wiki/File:Breadth-First-Search-Algorithm.gif | CC BY-SA 3.0 | 500×500 | 2026-10-04 |
| 数据结构-栈-深度优先访问顺序-commons-01.gif | 数据结构 / 栈 | 深度优先搜索的访问顺序动画：一条路走到底再回头——对应栈的"后进先出"与递归的调用栈 | https://commons.wikimedia.org/wiki/File:Depth-First-Search.gif | CC BY-SA 3.0 | 500×500 | 2026-10-04 |
| 数据结构-二分查找-区间收缩-commons-01.png | 数据结构 / 二分查找 | 有序数组里二分查找的区间收缩示意：每轮把待查区间折半——能讲清 O(log n) 怎么来的，以及"边界开闭"为什么容易写错 | https://commons.wikimedia.org/wiki/File:Binary_Search_Example.png | CC0 | 500×281 | 2026-10-04 |

## Gaps

- **OI Wiki 一张都没取到，原因是格式**：该站所有结构示意图（`ds/stack` 的栈、`ds/binary-heap` 的堆插入、`ds/dsu` 的并查集、`graph/save` 的邻接表、`basic/sort-intro` 的排序过程等）都是 **SVG 矢量图**，页内位图只有 MathJax 用的 1×1 占位 GIF。本角色规格只收 jpg/png/webp/gif 位图（不转格式、不截图），因此该站可用图为 0；已查页面：`ds/stack/`、`ds/binary-heap/`、`ds/dsu/`、`basic/binary/`、`basic/sort-intro/`、`graph/save/`。**若希望 OI Wiki 的图进课件，需要总控决定：要么放行 SVG（但课件硬约束是位图 ≤500 KB），要么把「截图/导出 PNG」交给别的环节。**
- **Python 官方文档未取到图**：`docs.python.org/3/` 以文字与代码为主，与数据结构/性能相关的结构示意图极少；站内图片多为官方 logo/图标，按过滤规则不收。本轮**没有实际下载**该站图片（该站无点名清单条目页时未逐一枚举），若总控要求逐页核，请在下轮点名具体页面。
- **Wikimedia Commons 的限额已用满**：本轮该站取满 6 张（规格上限），仍有高价值候选未取，下一轮可优先补：
  - `Category:Binary heaps`：`File:Dsa_binary_heap_pop.png`（弹出/下沉过程，CC BY 3.0）、`File:Binary Heap with Array Implementation.JPG`（堆与数组实现并排，CC0）、`File:InsertingIntoBinaryHeap.gif`（插入动画，CC0）。
  - `Category:Hash tables`：`File:Linear Probing Deletion.png`（线性探测删除，CC BY-SA 4.0）、`File:Dsa hash table.png`（CC BY 3.0）。
  - `Category:Depth-first search`：`File:Depth-first-tree.png`（树的 DFS 访问次序，CC BY-SA 3.0）。
  - `Category:Graph theory`：`File:Edge-weighted graph.png`（带权图，CC0）、`File:Cubical graph with weights.png`（CC0）。
- **没找到的图（想抓但站内确实没有合适的）**：
  - **图的邻接矩阵 / 邻接表对照**：Commons `Category:Adjacency matrix`、`Category:Adjacency list` 的成员多为矢量或与本课程无关的矩阵数学图，未找到「同一张图用两种表示并排」的位图；OI Wiki 有但为 SVG。
  - **排序各步骤的中间状态（冒泡/选择/插入/快排）**：Commons 无 `Category:Sorting algorithms` 这个分类，`Category:Sorting algorithms animations`、`Category:Quicksort`、`Category:Bubble sort`、`Category:Merge sort` 均无 ≥400px 的可用位图；这类过程图建议由「讲解」环节自产（走「讲解」规格的配图路径）。
  - **二叉树遍历顺序（前/中/后序）**：Commons 无 `Category:Tree traversals`；候选集中在矢量图。
  - **递归与调用栈**、**时间复杂度增长曲线**、**内存连续 vs 链式存储**：未找到贴合本课程口径的位图；这类"结构+过程"示意更适合由「讲解」自产。
- **术语表待补词**：本轮命名用到的 `二分查找`、`二叉树`、`图的表示（邻接矩阵/邻接表）`、`遍历（广度优先/深度优先）`、`排序（冒泡/选择/插入/快排）` 等词**不在 `GLOSSARY.md` 两节里**。文件名与标签已尽量只落在表内词（`数据结构`、`堆`、`哈希表`、`栈`、`队列`）上，但**建议总控把 `二分查找`、`二叉树`、`广度优先搜索`、`深度优先搜索`、`排序` 补进术语表**，后续采图与课件才能逐字对齐。
