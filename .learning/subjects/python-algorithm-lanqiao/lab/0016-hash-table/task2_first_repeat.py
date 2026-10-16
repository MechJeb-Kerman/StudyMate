"""任务 2 · 找第一个重复出现的元素：列表版与集合版，结果必须逐字一致

目标：从头扫一批数据，交出**第一个**「前面已经见过」的元素。

  · 列表版 —— seen 是一个列表，每见到一个元素就问 `x in seen`（`in` 在列表上是挨个比）；
  · 集合版 —— seen 是一个集合，`x in seen` 走哈希直接落位，`seen.add(x)` 记下见过。

两版都要在**发现重复的那一刻立刻停下**并交出这个元素，不能扫完再回头找；
没有重复就交出 None。两版结果必须逐字一致。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。

跑： py task2_first_repeat.py
判： py run_tests.py
"""

import time

# ── 给好的部分：造数据（别改）──────────────────────────────
# 前 2000 个互不相同，第 2001 个（下标 2000）是前面出现过的 7 —— 第一个重复就是它。
n = 2000
data = []
for i in range(n):
    data.append(i * 3 + 1)
data.append(7)                 # 第一个重复出现的元素
for i in range(5000):
    data.append(i % 100)       # 后面还有一大堆重复，别管它们

# ── 第 1 版：列表版（seen 用列表，in 挨个比）────────────────
# TODO 1：先把 seen_list 建成空列表；
#         再从头扫 data，对每个 x 判断 x 在不在 seen_list 里：
#         在 → 把 first_list 记成这个 x 并跳出循环（break）；
#         不在 → 把它 append 进 seen_list。
t0 = time.perf_counter()       # 别改：计时开始
seen_list = None
first_list = None
t1 = time.perf_counter()       # 别改：计时结束

# ── 第 2 版：集合版（seen 用集合，走哈希）──────────────────
# TODO 2：同一个形状，把 seen 换成集合（空集合只能写 set()），用 add 记下见过的元素。
t2 = time.perf_counter()       # 别改：计时开始
seen_set = None
first_set = None
t3 = time.perf_counter()       # 别改：计时结束

# ── 打印对照（这几行别改，自动判分按它们读结果）─────────────
print('列表版 第一个重复', first_list, f'{t1 - t0:.6f} 秒')
print('集合版 第一个重复', first_set, f'{t3 - t2:.6f} 秒')
print('两版结果逐字一致', first_list == first_set)
print('列表版比集合版慢', f'{round((t1 - t0) / max(t3 - t2, 1e-9), 1)} 倍')

# ── 给判分脚本的接口（别改函数名与参数）──────────────────────
# 两份函数都交回「第一个重复出现的元素」；一个重复都没有时交回 None。
def first_repeat_list(items):
    """列表版：seen 用列表。"""
    # TODO 3：与 TODO 1 同一件事，写成一个函数。
    return None


def first_repeat_set(items):
    """集合版：seen 用集合。"""
    # TODO 4：与 TODO 2 同一件事，写成一个函数。
    return None
