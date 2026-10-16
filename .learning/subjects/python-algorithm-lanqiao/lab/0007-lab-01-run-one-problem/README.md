# 实验一 · 把一道题跑通（`lab/0007-lab-01-run-one-problem/`）

这是本课程的第一个「可运行产物」实验。前六课学的是零件——循环、函数、推导式、输入解析、
复杂度估算；这次要把它们装成一台能跑的机器：**一份能读入题目输入、给出答案、
并用样例自动判定对错的脚本**。

题目材料在 `problems.md`（两道题、两种输入格式），判分脚本是 `run_tests.py`，
参考解在 `../solutions/0007-lab-01-run-one-problem/`（做完才对照）。

## 目录一览

| 文件 | 是什么 | 谁写 |
| --- | --- | --- |
| `problems.md` | 题目 A 与题目 B 的题面（输入格式、样例、数据规模、时限） | 给好的，别改 |
| `solve_a.py` | **任务 1**：题目 A 的脚本，三段各一个函数（标着 `TODO` 的段落要你写） | 你写 |
| `solve_b.py` | **任务 2**：题目 B 的脚本，五个函数各管一件事 | 你写 |
| `selfcheck.py` | **任务 3**：你自己的自测脚本——跑样例、逐组比对、打印 PASS / FAIL | 你写 |
| `scale_check.py` | **任务 4**：两种查重写法的耗时对照 + 「放大 10 倍要多久」的估算 | 你写 |
| `run_tests.py` | 判分脚本：分层跑上面四件事，逐条给 PASS / FAIL | 给好的，别改 |
| `sample_a1.in` / `.out` … `sample_b2.in` / `.out` | 题面给的四组样例（自测脚本的标准答案） | 给好的，别改 |
| `tests/a3.*`、`tests/b3.*` | 同一份数、换行换了排版的判分数据 | 给好的，别改 |
| `tests/a_big.*`、`tests/b_big.*` | 大数据（题目 A 十万个数；题目 B 300×100） | 给好的，别改 |
| `probe_wrong_a.py` | 一份故意写错的解，判分拿它试你的自测脚本 | 给好的，别改 |

**文件名与函数名是判分接口**：`solve_a.py` / `solve_b.py` / `selfcheck.py` / `scale_check.py`
这四个文件名，以及每个文件里已经写好的函数名（`read_all` / `parse_input` / `count_distinct` /
`row_maxes` / `most_common` / `solve` / `run_solver` / `normalize` / `check_one` /
`distinct_by_list` / `distinct_by_set`）都别改；函数体里怎么写随你。

## 怎么跑

先 `cd` 进这个目录（`lab/0007-lab-01-run-one-problem/`）：

```text
py solve_a.py                 # 单独跑没用：它在等标准输入
cat sample_a1.in | py solve_a.py     # 把样例接进去跑一遍，先看它打印什么（PowerShell 的 cat 就是 Get-Content）
py selfcheck.py               # 你自己的自测脚本：四组样例逐组 PASS / FAIL
py scale_check.py             # 任务 4 的耗时对照（要跑几秒）
py run_tests.py               # 判分：五层一起判，逐条给 PASS / FAIL
```

Windows 上 `python` 可能是应用商店的占位符（敲下去没反应），用 `py`。本机 `py` 指向 Python 3.14.7。
CMD 里读文件用 `py solve_a.py < sample_a1.in`；PowerShell 不支持 `<`，用上面那种管道写法。

## 判分怎么分层

`run_tests.py` 把结果分成五层，**每一层的失败指向不同的原因**（详细说明在 `../README.md`）：

| 层 | 跑什么 | 没过通常说明 |
| --- | --- | --- |
| 1 · 样例 | 题面给的四组样例 | 读入 / 求解 / 输出哪一段还没接上 |
| 2 · 折行组 | 同一份数、换行换了排版（`tests/a3`、`tests/b3`） | 输入解析层：用 `input()` 逐行读，读的位置与数据的行绑死了 |
| 3 · 大数据 | 题目 A 十万个数、题目 B 300×100（限时 2 秒） | 复杂度：容器选错（列表查重是 O(n²)），不是「写错了」 |
| 4 · 自测脚本 | 你的 `selfcheck.py`，**外加一次探针** | 自测脚本没有真的比对（判分会把 `solve_a.py` 换成故意写错的解试它） |
| 5 · 规模对照 | `scale_check.py` 的三行输出 | 两种容器的量级没量出来，或者「放大 10 倍」推成了 10 倍（那是平方级，应是 100 倍） |

第 1、2 层没过时，第 3–5 层直接跳过——样例都没过，大数据组的失败信息没有参考价值。
退出码：五层都过是 0，还有没过的（或跳过的）是 1，最后一行会点出是哪几层。

## 期望输出形状

任务 1 与任务 2 的输出就是题面的答案，逐字比对：

```text
$ cat sample_a1.in | py solve_a.py
3

$ cat sample_b2.in | py solve_b.py
30 30 7 9
5 2
```

任务 3 的输出（格式是判分接口，照抄）：

```text
$ py selfcheck.py
样例 A1 PASS
样例 A2 PASS
样例 B1 PASS
样例 B2 PASS
自测通过 4/4 组
```

任务 4 的输出（格式是判分接口，三个 `TODO` 填上就能打出来；秒数只作参考）：

```text
$ py scale_check.py
n=20000 列表 in 用时 0.855123 秒 不同元素 20000
n=20000 集合 in 用时 0.001234 秒 不同元素 20000
列表版放大 10 倍预计 85.51 秒 超出 1 秒时限 True
```

## 两条规矩

- **留白版原样跑是不通过的**：`solve_a.py` 现在打出 `0`、`solve_b.py` 打出空行与 `0 0`、
  `selfcheck.py` 一组都不报、`scale_check.py` 两行的秒数都小到 `0.000000`。这是起点，不是 bug；
  判分脚本会指名缺哪一段。
- **别动给好的东西**：`problems.md`、`run_tests.py`、`sample_*.in/out`、`tests/`、`probe_wrong_a.py`
  都是判分接口。自测脚本里允许用 `sys` / `os` / `subprocess` 这几个标准库（它们是脚本的工具）；
  算法代码只用前六课学过的东西，写法边界见 `../README.md`。

卡住了先读 `../README.md` 的「卡壳顺序」：读错误信息 → 自己跑一遍 → 看 FAIL 行 → 再对线索。
