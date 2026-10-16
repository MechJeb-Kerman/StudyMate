# Python 算法与蓝桥杯 Resources

> 定位：**延伸阅读 + 易变内容的核对来源**，不是"知识来源清单"（模型已掌握稳定基础知识）。
> 稳定知识节点可以不在这里留条目；易变/版本相关内容必须在这里有核对过的官方来源。
> 本清单按盘问结果定向：目标深度「精通（原理与复杂度都要吃透）」，数据结构与算法零起点，Python 只会基础部分，每周 10 小时以上，配套项目「AI 刷题助手」，明确不学 C/C++ 竞赛写法与 Linux 环境。

## Knowledge

### 延伸阅读（算法与数据结构主干、Python 起步、真题入口）

- [Book: 算法（第4版） by Robert Sedgewick / Kevin Wayne（中文版，图灵社区）](https://www.ituring.com.cn/book/1806)
  一行说明：数据结构与算法主干教材——排序、查找、二叉搜索树/红黑树、散列表、图与最短路，含大量图示与复杂度分析；讲"为什么正确、复杂度怎么推"时用它做章节顺序与深度依据。代码是 Java，只取原理与图示，不照抄写法。
- [Source: Algorithms, 4th Edition 官方 booksite（Princeton University）](https://algs4.cs.princeton.edu/home/)
  已落盘 `sources/algs4-princeton-booksite.md`：上一条教材的官方配套站（章节清单、算法可视化 demo、完整代码与习题）；做"实现自己的堆/并查集后跟成熟实现对照"这个动作时，从这里的官方实现取对照基准。
- [Course: Algorithms, Part I（Princeton，Sedgewick 主讲，Coursera）](https://www.coursera.org/learn/algorithms-part1)
  一行说明：与上面教材配套的公开课（Part I 覆盖复杂度分析、并查集、排序、查找、图基础）；进度卡住或想听一遍原理推导时按周跟看。
- [Book: 算法导论 Introduction to Algorithms by Cormen 等（MIT Press / 机械工业出版社中文版）](https://mitpress.mit.edu/9780262046305/introduction-to-algorithms/)
  一行说明：复杂度的形式化定义（Θ/O/Ω）、算法正确性证明与主定理的权威依据；讲"复杂度怎么推、为什么正确"遇到争议时的最终裁判。注意：该出版社页面拒绝本机自动抓取（403），仅供学生手动打开。
- [Local: Python编程：从入门到实践（第2版）](reference/python-crash-course-2e.md)
  一行说明：Python 基础语法热身与函数/推导式补齐的本地教材依据（学生自评函数与推导式不熟，前几个节点用它对齐 Python 侧写法）。
- [Source: OI Wiki（中文算法竞赛百科）](https://oi-wiki.org/)
  已落盘 `sources/oi-wiki-index.md`：中文竞赛知识主干来源，给大纲定"数据结构 / 基础算法 / DP / 图论"的节点顺序与深度。注意其代码示例多为 C++，只取原理、复杂度与题型，不学 C++ 竞赛写法。
- [Source: OI Wiki：复杂度](https://oi-wiki.org/basic/complexity/)
  已落盘 `sources/oi-wiki-complexity.md`：复杂度定义、渐进符号、主定理与"数据规模 ↔ 可接受复杂度"的对照；教学生从题面数据范围反推复杂度上限时直接引这一页。
- [Source: OI Wiki：并查集 DSU](https://oi-wiki.org/ds/dsu/)
  已落盘 `sources/oi-wiki-dsu.md`：并查集的路径压缩与按秩合并、复杂度证明；数据结构入门后第一个"能自己实现并证明复杂度"的载体。
- [Source: OI Wiki：二分查找](https://oi-wiki.org/basic/binary/)
  已落盘 `sources/oi-wiki-binary-search.md`：二分答案与二分查找的边界写法、单调性判定；对应"二分 + 判定函数"这一蓝桥杯高频套路。
- [Source: OI Wiki：前缀和与差分](https://oi-wiki.org/basic/prefix-sum/)
  已落盘 `sources/oi-wiki-prefix-sum.md`：一维/二维前缀和、差分与前缀和的互逆关系；对应区间求和/区间修改类题型。
- [Source: OI Wiki：动态规划基础](https://oi-wiki.org/dp/basic/)
  已落盘 `sources/oi-wiki-dp-basic.md`：DP 的状态设计与转移推导入门；讲"为什么这个状态能覆盖所有情况"时对齐这里。
- [Source: OI Wiki：DFS（搜索）](https://oi-wiki.org/search/dfs/)
  已落盘 `sources/oi-wiki-dfs.md`：DFS 与回溯、剪枝与搜索树规模估算；配合 Python 递归深度限制（见 sys 那条）讲清"为什么 DFS 会爆栈"。
- [Source: Python 官方教程：数据结构](https://docs.python.org/zh-cn/3/tutorial/datastructures.html)
  已落盘 `sources/python-tutorial-datastructures.md`：list/dict/set/tuple、切片、推导式的官方口径；学生起点补齐用，也用于核对进阶写法（嵌套推导式、多重赋值）。
- [Source: Python 官方教程：更多控制流工具](https://docs.python.org/zh-cn/3/tutorial/controlflow.html)
  已落盘 `sources/python-tutorial-controlflow.md`：**`4.8 定义函数` 与 `4.9 函数定义详解`**（4.9.1 默认值参数、4.9.2 关键字参数、4.9.3 特殊参数、4.9.4 任意实参列表、4.9.5 解包实参列表、4.9.6 Lambda 表达式、4.9.7 文档字符串、4.9.8 函数注解）的官方中文口径。**「默认值只在定义时求值一次」「可变默认参数的官方警告」「实参是按值调用、值始终是对象的引用」这三段是讲函数参数时的唯一权威依据**——讲第 4 课《把一段代码变成函数》时讲解角色最初只能联网核对、本地无据可查，本条目就是补这个缺口；除函数参数外，本章的 `4.1`–`4.7` 与 `4.10` 编码风格也可作为流程控制与风格的官方旁证。
- [Source: 排序指南 Sorting HOW TO（Python 官方）](https://docs.python.org/zh-cn/3/howto/sorting.html)
  已落盘 `sources/python-howto-sorting.md`：`sorted`/`list.sort` 的 key、稳定性、多级排序与 `cmp_to_key`；讲"排序是很多算法前置步骤"时用它给官方口径。
- [Doc: 蓝桥云课题库（含"蓝桥杯真题卷""算法"分类）](https://www.lanqiao.cn/problems/)
  一行说明：真题与练习入口，用于核对考点覆盖方向（**非大纲原文**）；页面为动态加载，抓不到题目正文，只能作为方向旁证与学生练习入口。

### 易变内容的官方核对来源（Python 版本/标准库行为 + 大模型 API）

- [Source: heapq --- 堆队列算法（Python 3.14 官方文档·中文）](https://docs.python.org/zh-cn/3/library/heapq.html)
  已落盘 `sources/python-stdlib-heapq.md`：核对堆 API 的版本差异——**最大堆 API（`heapify_max`/`heappush_max`/`heappop_max`）是 3.14 新增**，旧版本只能"取负模拟最大堆"；学生环境是 3.14，核对后再决定教学用哪种写法。
- [Source: bisect --- 数组二分算法（Python 3.14 官方文档·中文）](https://docs.python.org/zh-cn/3/library/bisect.html)
  已落盘 `sources/python-stdlib-bisect.md`：核对 `bisect_left`/`bisect_right` 的插入位置语义、`lo`/`hi` 参数与 `key` 参数（3.10 起）的版本差异，避免手写二分与标准库行为不一致。
- [Source: collections --- 容器数据类型（Python 3.14 官方文档·中文）](https://docs.python.org/zh-cn/3/library/collections.html)
  已落盘 `sources/python-stdlib-collections.md`：核对 `deque`（BFS 队列）、`Counter`、`defaultdict`、`OrderedDict` 的行为与版本变更；讲"Python 里队列不要用 list.pop(0)"时以此页为据。
- [Source: itertools --- 迭代器函数（Python 3.14 官方文档·中文）](https://docs.python.org/zh-cn/3/library/itertools.html)
  已落盘 `sources/python-stdlib-itertools.md`：核对 `permutations`/`combinations`/`accumulate`/`groupby`/`batched` 等函数签名与新增版本（如 `batched` 是 3.12 起），枚举与预处理写法以官方口径为准。
- [Source: sys --- 系统相关参数与函数（Python 3.14 官方文档·中文）](https://docs.python.org/zh-cn/3/library/sys.html)
  已落盘 `sources/python-stdlib-sys.md`：核对 `sys.stdin` 的读取方式（含 `buffer`/`readline` 与快速读入写法）、`sys.setrecursionlimit` 与默认递归上限、`sys.maxsize`；讲"DFS 爆栈"和"怎么快读入"时必须核这一页。
- [Source: functools --- 高阶函数与可调用对象操作（Python 3.14 官方文档·中文）](https://docs.python.org/zh-cn/3/library/functools.html)
  已落盘 `sources/python-stdlib-functools.md`：核对 `lru_cache`/`cache`（记忆化搜索的教学写法）与 `cmp_to_key`（自定义排序）的签名与行为差异。
- [Source: timeit --- 测量小段代码的执行时间（Python 3.14 官方文档·中文）](https://docs.python.org/zh-cn/3/library/timeit.html)
  已落盘 `sources/python-stdlib-timeit.md`：核对性能测量的官方方法（`timeit`/`-m timeit`、`number` 与重复次数的取舍）；"自实现 vs 标准库实现的性能差异"这类实验要按此页口径做，避免用 `time.time()` 单次计时下结论。
- [Source: TimeComplexity（python.org 官方 wiki）](https://wiki.python.org/moin/TimeComplexity)
  已落盘 `sources/python-wiki-time-complexity.md`：核对 Python 容器（list/dict/set/deque）各操作的均摊复杂度，用来对照自己实现的复杂度分析。**注意该 wiki 已归档冻结**（页面首段声明不再编辑、只作为快照保留），正文指向在维护的替代项目 [Python Time & Space Complexity Reference](https://pythoncomplexity.com/)；需要更新数据时以替代项目与官方文档为准。
- [Source: Python 3.14 有什么新变化（官方文档·中文）](https://docs.python.org/zh-cn/3/whatsnew/3.14.html)
  已落盘 `sources/python-whatsnew-3.14.md`：核对 3.14 相对旧版本的语言与标准库差异（新增/废弃/行为变更）的总入口；本机 Python 是 3.14，凡"网上教程写法跑不通"先查这里。
- [Source: Python 对自由线程的支持 free-threading（官方文档·中文）](https://docs.python.org/zh-cn/3/howto/free-threading-python.html)
  已落盘 `sources/python-howto-free-threading.md`：核对 3.13+/3.14 自由线程构建（本机 `python3.14t`）与常规 GIL 构建的差异；做性能对照实验时必须先核这里，否则"同一算法快慢"的结论会被构建差异污染。
- [Source: DeepSeek API 官方文档（中文首页）](https://api-docs.deepseek.com/zh-cn/)
  已落盘 `sources/deepseek-api-docs.md`：核对调用方式（`base_url`、OpenAI/Anthropic 兼容格式、首个可跑样例），项目「AI 刷题助手」接大模型时以此为准。
- [Source: DeepSeek API 参考：创建对话补全](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion)
  已落盘 `sources/deepseek-api-reference-chat-completion.md`：核对请求/响应字段、消息结构与错误码；接口字段随版本变动，改代码前核这一页。
- [Source: DeepSeek API 价格与模型名（官方）](https://api-docs.deepseek.com/zh-cn/quick_start/pricing)
  已落盘 `sources/deepseek-api-pricing-models.md`：核对**模型名与价格**（本页明确写了旧模型名已下线、请求会被转到新模型），模型选择与调用成本估算前必须核这一页。

## Wisdom (Communities)

- [洛谷（中文算法竞赛社区与评测）](https://www.luogu.com.cn/)
  一行说明：中文题库+讨论区，用于求"我这复杂度为什么过不了""这题思路对吗"这类实践问题，也能看到同题的多种复杂度过法。
- [Python Discourse（python.org 官方社区）](https://discuss.python.org/)
  一行说明：问 Python 语言与标准库行为的官方社区（例如"这个 API 在 3.14 里为什么这样"）；语言层面拿不准时用，答案是核心开发者口径。

## Gaps

- **蓝桥杯官方竞赛大纲取不到正文**：大赛官网 `https://dasai.lanqiao.cn/` 是 Vue 单页应用，正文全在 1.3 MB 的前端包（`index-*.js`）里，HTML 只有 SEO meta；无法核实"Python 组考纲"的条目级依据。替代做法：大纲深度改用 OI Wiki 章节体系（原理主干）+ 蓝桥真题实际考点（方向旁证）交叉确定。
- **蓝桥云课题库正文抓不到**：`https://www.lanqiao.cn/problems/` 为 Nuxt 动态加载，HTML 只有导航外壳，题目正文需 JS 渲染；只能取到"蓝桥杯真题卷""算法"等分类标签作为考点方向旁证，不能当官方大纲原文，也无法离线存档真题。
- **本机搜索引擎不可用，来源发现只能靠已知固定入口**：`web_search` 无 API key；百度返回"百度安全验证"（反爬）；Bing 中文长查询被切词（返回"蓝"字的字典释义）；mojeek/brave/searx/duckduckgo 不可达。后果：无法系统核实"某来源是否存在"及其官方 URL。因此中文竞赛教材类条目（如《算法竞赛入门经典》《算法竞赛进阶指南》）**未收录**——不是判断其质量不足，而是无法核实一个可长期访问的官方页面。
- **大模型 API 厂商未确认**：学生"有可用 API key"，但未给出厂商；OpenAI 官方文档本机 403（Cloudflare 拦截）、Anthropic 文档返回"App unavailable in region"，只有 DeepSeek 官方文档可取到正文。若最终改用 OpenAI/Anthropic，需要另找可访问的官方核对来源（或经代理）。
- **竞赛向 Python 权威入口缺可核实页面**：cses.fi（Competitive Programmer's Handbook）本机连接失败；Cambridge《Competitive Programming in Python》未核实到可长期访问的官方页面。主干因此采用"OI Wiki（原理）+ 本地教材（Python 语法）+ 蓝桥真题（实践）"组合，而不是单一 Python 竞赛教材。
- **3.14t（free-threading 构建）在算法竞赛场景下的性能缺官方基准**：官方只有 free-threading 的机制说明，没有"3.14t vs 3.14（GIL 版）跑同一算法"的对照数据；因此"复杂度上限对应多少秒""哪个写法更快"只能靠本地实测（timeit，见上表）与题面数据范围反推，不能引用权威结论。
