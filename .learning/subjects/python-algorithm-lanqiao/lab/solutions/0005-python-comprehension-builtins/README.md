# 参考解 · lab 0005 · 推导式与常用内置工具

**做完六个任务再打开这里。** 这里的六个 `.py` 与任务目录里的文件同名：
把它们拷进 `lab/0005-python-comprehension-builtins/` 覆盖同名文件，再跑 `py run_tests.py`，应当六个任务全过。
（参考解是自包含的：`loops_original.py` 与 `run_tests.py` 这里各有一份，拷过去直接就能跑。）

## 逐个任务看什么

| 任务 | 参考解里补上的关键几行 | 要看的现象 |
| --- | --- | --- |
| 1 | 十段各压成一行：两处列表推导式、`sum(data)`、`max(data)`、`sum(1 for x in data if x > 0)`、`any(...)` / `all(...)`、`list(map(int, data_str))`、`sorted(records, key=rank_key)` | 十行输出与 `loops_original.py` **逐字一致**：压成一行改的是写法，不是结果 |
| 2 | `[x for x in range(10) if x % 2 == 0 if x > 4]`、`[num for elem in vec for num in elem]`、`[[row[i] for row in matrix] for i in range(4)]`、`[y ** 2 for y in range(4)]` | 05 打出 `旧值`：推导式里的 `y` 没盖掉外面的 `y`；对照 06（循环版把 `y` 留成了 3） |
| 3 | `(slow_square(x) for x in range(6))`、`[slow_square(x) for x in range(6)]`、`any(slow_square(x) > 3 for x in range(6))`、`all(slow_square(x) < 5 for x in range(6))`、`squares_gen` 交回圆括号版 | 01 是 0（还没算）、04 是 0（第二次空了）、06 是 6（建表就算完）、08 是 3、10 是 4（短路） |
| 4 | `for i, (name, score) in enumerate(zip(names, scores), start=1)`、`list(zip(...))`、`[score for _, score in zip(names, scores)]`、`[list(col) for col in zip(matrix[0], matrix[1], matrix[2])]` | 编号从 1 起；长度 3 配 2 只出 2 对（zip 截断到最短）；三行矩阵按列配成 4 组 |
| 5 | `return (-rec[1], rec[0])`、`board = sorted(records, key=rank_key)`、`ranked = sorted(scores, reverse=True)`、`none_value = trap.sort()` | 01 排行榜固定；02/04 原数据没动；05 是 True（原地排序交回 None）；06 原表被改了；07 同分的两条保持原顺序（稳定）；08 取键 4 次 |
| 6 | `any(x > 0 for x in data)`、`all(x > 0 for x in data)`、`all(x > 0 for x in nums)`、`if not nums: return False` | 03 是 False、04 是 True（空序列的默认答案相反）；05 是 True（不判空的那版）、06 是 False；10 只看了 1 个（短路） |

判分另有一条总检：大纲要求 `enumerate`、`zip`、`sorted(key=)`、`sum`、`max`、`any`、`all`、`map` **各至少改写一处**，
它查的是任务 1 与任务 4 这两个改写文件里这八个名字出现了没有（注释里写不算）。

## 每个任务的「为什么」

- **任务 1**：这十段是同一个模式：先建空容器（或设一个旗子），再写一层循环改它，循环本身没有别的用处。
  换成一行版后，代码里剩下的正好是逐段改写的对照表上那一列。判定与统计那三段最容易写错方向：
  「数有几个」是 `sum(1 for …)`（每个满足条件的算 1），不是 `sum(x for …)`（那是求和）；
  `any` 是「存在一个」，`all` 是「一个反例都没有」，两个别写反。
- **任务 2**：一行里 `for` 与 `if` 的先后，与循环版从上到下的顺序**一一对应**：先 `for x`，再 `if`，
  再 `for num`…… 顺序写错，取到的元素就变了（两个 `for` 对调＝先按列后按行）。
  `05` 那一行是这一课最容易被忽略的一条：推导式在自己的隐式作用域里执行，目标名不会泄漏到外面——
  所以外面的 `y` 还是 `旧值`，而循环版的 `y` 会变成 `3`。
- **任务 3**：列表推导式是「建出来就把元素全算好」（额外占用 $O(n)$，但能反复遍历、能 `len`、能下标）；
  生成器表达式是「要一个才算一个」（额外占用 $O(1)$，但只能走一遍、没有 `len`、不能下标）。
  `04` 打出 `0` 不是 bug，是它的性质：第一次 `sum` 已经把它取空了。
  `08`/`10` 那两个计数说明 `any`、`all` 能确定结果就不再多取一个值——这也是它们能用在「大序列上判存在」的原因。
- **任务 4**：`zip` 在最短的那个序列用完时就停，长度不齐**不报错**，只会悄悄变短——所以 `03` 是 2 而不是 3。
  它也是迭代器：`enumerate`、`zip`、`map` 都一样，取完就空、不存在「重置」。
  `07` 的两种写法结果相同（嵌套推导式 / `zip`），但列一多，`zip` 那版不用写下标也不用叠三层 `for`。
- **任务 5**：`sorted` 返回**新表**，`list.sort()` 原地改并**返回 `None`**（官方指南特意标注「返回 `None` 以避免混淆」）。
  排行榜那一条靠的是「元组按字典式顺序比」：先比第一项（`-rec[1]`，取负号就把降序变成升序问题），
  相同再比第二项（编号）。`08` 说明键函数每条记录只调用**一次**——取键一次、比较很多次。
- **任务 6**：`any` 与 `all` 在空序列上的默认答案相反（`False` / `True`）。第二条不是对称美，是定义推出来的：
  「所有元素都为真」在空数据上没有反例。所以 `all_valid` 那种「这批数据是不是都合法」的检查，
  空数据会给 `True`——要按题目要求另外判空（`all_valid_nonempty` 就是那一版）。

## 常见错法（对照自己的写法）

- **排行榜用 `records.sort()`**：排行榜看着对，但原记录被改掉了，`02 原记录没动` 会变 `False`。
  要「新表 + 原数据不动」就用 `board = sorted(records, key=rank_key)`。
- **key 只写 `rec[1]`（忘了负号）**：分数变成升序；同分那两条的顺序也会反（`A03` 跑到 `A02` 前面）。
- **`ranked = scores.sort(reverse=True)`**：`ranked` 接住的是 `None`，`03` 会打出 `None`。
  改成 `sorted(...)`（新表）或 `scores.sort(...)` 之后直接用 `scores`（原地改）——两种改法都对，
  看你后面还要不要原来的顺序。
- **生成器用两次**：把 `(...)` 写对之后又指望它能反复遍历——`04` 会打出 `0`，那是正常的。
  要反复用就先建成表（任务 3 的 `06`/`07` 就是对照）。
- **`any(x > 0, data)` / `sum(x > 0, data)`**：`any`、`all`、`sum` 只收一个可迭代对象；
  带条件要写成生成器表达式 `any(x > 0 for x in data)`（`map` 才是「函数 + 序列」两个参数）。
- **`enumerate` 忘了 `start=1`**：三行编号会从 0 起。
- **以为 `zip` 会补齐或报错**：它截断到最短，`03` 因此是 2。
- **任务 1 直接抄 `loops_original.py`**：输出是逐字一致的，但总检那条会 FAIL，并点名还差哪几个内置函数没改写。
- **只按 `print` 后的期望值凑数字**：判分读的就是这些行，硬凑等于没做；
  改完先自己跑 `py <任务文件>.py` 对一遍，再跑 `py run_tests.py`。
