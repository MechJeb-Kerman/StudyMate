# 参考解 · lab 0007 · 实验一：把一道题跑通

**四个任务都做过一遍再打开这里。** 这里的五个 `.py` 与任务目录里的文件同名
（`solve_a.py`、`solve_b.py`、`selfcheck.py`、`scale_check.py`、`probe_wrong_a.py`）：

```text
把 solutions/0007-lab-01-run-one-problem/ 里的 .py 拷进 lab/0007-lab-01-run-one-problem/ 覆盖同名文件
py run_tests.py       → 五层全过，退出码 0（本机实测 1.5 秒左右，其中 scale_check 自己占 0.9 秒）
py selfcheck.py       → 样例 A1 / A2 / B1 / B2 全 PASS，自测通过 4/4 组
```

参考解是自包含的：`run_tests.py` 与 `probe_wrong_a.py` 在任务目录里也各有一份，
样例与 `tests/` 的数据两边共用，拷 `.py` 过去直接就能跑。

## 逐个任务看什么

| 任务 | 参考解补上的关键几行 | 要看的现象 |
| --- | --- | --- |
| 1 · 题目 A | `read_all()` 里 `sys.stdin.read()`；`parse_input` 里 `tokens = text.split()` 后 `int(tokens[0])` 与 `[int(x) for x in tokens[1:1 + n]]`；`count_distinct` 里 `seen = set()` 配 `seen.add(x)` | 样例 `3`、`4`；折行组 `tests/a3.in` 同样是 `4`；十万个数 0.05 秒左右 |
| 2 · 题目 B | `n, m = int(tokens[0]), int(tokens[1])`；`vals = [int(x) for x in tokens[2:2 + n * m]]`；`grid = [vals[i * m:(i + 1) * m] for i in range(n)]`；`row_maxes` 一行 `[max(row) for row in grid]`；`most_common` 用字典计数 + `sorted(counts.items(), key=key_of)[0]` | `sample_b1` → `91 95 100` / `60 3`；`sample_b2` → `30 30 7 9` / `5 2`（**并列取最小**）；300×100 数据 0.03 秒左右 |
| 3 · 自测脚本 | `run_solver` 用 `subprocess.run([sys.executable, 脚本], cwd=HERE, input=输入文本, ...)`；`normalize` 去掉行尾空白与末尾空行；`check_one` 先看退出码再看输出 | 四组样例全 PASS；判分的探针把 `solve_a.py` 换成错的解后，A1 / A2 变 FAIL 而 B1 / B2 仍 PASS |
| 4 · 规模对照 | `distinct_by_list` 用列表 `in`；`distinct_by_set` 用集合；`predicted = t_list * 100` | 列表约 0.85 秒、集合约 0.0016 秒（差 500 倍上下）；放大 10 倍预计约 85 秒，远超 1 秒时限 |

## 每个任务的「为什么」

- **任务 1**：三段的分工就是第 6 课那条规矩的落地——**标准输入只被碰一次**
  （`read_all`），**解析只在解析层做**（`parse_input` 交出 `(n, a)`，字符串不进算法层），
  **算法只面对数据结构**（`count_distinct(a)`）。这样分完之后，「读错了」与「算错了」
  是两处可以分别打印、分别验证的地方——判分脚本第 1 层与第 2 层的分工也是这么来的。
- **任务 1 的复杂度**：`count_distinct` 里那一行 `if x in seen` / `seen.add(x)` 用了什么容器，
  决定了这道题能不能跑完十万个数。列表版每次 `in` 都要从头比过去，总共约 $n^2/2$ 次比较；
  集合版平均每次 $O(1)$，整段 $O(n)$。**答案、样例、代码形状都一样，只有容器换了。**
- **任务 2 的解析**：题面写明了「只约定个数与先后顺序」，所以按空白读（`text.split()`）
  是按题面办事，不是取巧；先把 $n \times m$ 个数取成一段 `vals`，再按 `m` 个一段切成 `grid`，
  换行排在哪里都不影响结果。用 `input()` 一行一行读的版本在 `tests/b3.in` 上会直接
  `ValueError`——那一组的数没换，只是排版换了。
- **任务 2 的并列取最小**：把「次数最多、分数最小」写成一个键 `(-times, score)`，
  升序排完取第一条（第 5 课排行榜那一招）。只写 `max(counts, key=counts.get)` 会取到
  **最先插进字典**的那个分数：`sample_b2` 里每个分数都出现 2 次，它会打出 `10 2`，正确答案是 `5 2`。
- **任务 3**：自测脚本就是评测机的雏形：**跑脚本 → 拿标准输出 → 与 `.out` 逐字比 → 报一行结论**。
  三条容易漏的：路径要按 `__file__` 算（否则换个目录就找不到文件）；退出码不是 0 时
  要报错原因而不是去比输出；比对前统一去掉行尾空白（否则 `\r\n` 与 `\n` 会变成假失败）。
  判分之所以敢把 `solve_a.py` 换成错的解试它一次，就是为了排除「永远报 PASS」的假自测。
- **任务 4**：两种写法的差距不在「代码好不好看」，而在**操作次数随规模怎么涨**。
  列表版是平方级：规模扩大 10 倍，比较次数扩大 100 倍，所以实测 0.85 秒要推成约 85 秒，
  这已经远超题面 1 秒的时限——**这个判断应该在写代码之前就做完**（第 2 课）。
  题目 A 的十万个数数据正是用来验证这个判断的。

## 可以接受的别的写法

- `count_distinct`：`return len(set(a))` 一行也可以（同样是 $O(n)$）；
  `sorted(a)` 之后数相邻不同也行（$O(n \log n)$，能过十万，但比集合慢）。
  判分只看答案与耗时，不看用了哪种容器。
- `most_common`：`sorted(counts.items(), key=key_of)[0]` 与「先取最大次数、再在并列里取最小分数」
  两段写法都对；键写 `(-times, score)` 取第一条，等价于写 `(times, -score)` 取最后一条。
- `parse_input`：`map(int, ...)` 配 `list(...)`、或列表推导式都行；关键是**别一行一行读**。
- `selfcheck.py`：可以用 `subprocess`（参考解），也可以自己拼 `os.system` 那种调用；
  格式只要「样例 <标签> PASS/FAIL」四行 + 最后一行「自测通过 4/4 组」就对。

## 常见错法（对照自己的写法）

- **用 `n = int(input())` 加 `a = list(map(int, input().split()))`**：样例全过，`tests/a3.in`
  立刻错（那道题的数被折成了三行）。这是本实验最常见的一个错法，也正是第 6 课那条规矩要治的。
- **`read_all()` 写了却没用**（直接把 `input()` 写在 `solve` 里）：第 1 层能过、第 2 层过不去；
  改成「一次读完 → 按空白切分」即可。
- **题目 A 用列表查重**：样例、折行组全过，第 3 层十万个数的数据超时——这不是「写错了」，
  是容器的复杂度选错；换成集合或字典。
- **把 `print` 调试留在代码里**：多打一行「答案是：」会让四组样例全部 FAIL（评测机逐字比）。
  调试打印用完就删，或者改成写 `sys.stderr`。
- **自测脚本永远报 PASS**（或者固定 `return True`）：第 4 层的探针会抓住它。判分只看
  「换成故意错的解之后你有没有报 FAIL」这一条证据。
- **自测脚本里写死了绝对路径**：探针在副本目录里跑它，会找不到 `solve_a.py`——
  路径用 `os.path.dirname(os.path.abspath(__file__))` 算。
- **`most_common` 里 `max(counts, key=counts.get)`**：`sample_b2` 打出 `10 2`（应为 `5 2`）——
  并列时它给的是插入顺序里最靠前的那个分数，不是最小的。
- **`scale_check.py` 把「放大 10 倍」推成 10 倍**：列表版是平方级，规模 10 倍对应时间约 100 倍；
  那一行填 `t_list * 10` 会被第 5 层点出来。

## 做完之后

用一句话回答：**这两道脚本里，哪一行决定了题目 A 能不能跑完十万个数？**
（能说出「哪一行 → 用了什么容器 → 复杂度是多少 → 为什么 10 万个数上它还能过」，
这个实验就算到位了。）
