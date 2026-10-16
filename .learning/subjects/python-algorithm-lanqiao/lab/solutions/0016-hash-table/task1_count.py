"""任务 1 · 统计出现次数：列表版与字典版，结果必须逐字一致

目标：数出一批数据里每个元素各出现几次。
两版都要写：
  · 列表版 —— 按定义扫一遍：拿一个去重后的元素表，对每个元素把整批数据从头数到尾；
  · 字典版 —— 一边扫一边用字典记：扫到 x 就 cnt[x] = cnt.get(x, 0) + 1。

课件第 3 课量过的那笔账在这里再算一次：数据有 n 个、不同元素有 k 个，
列表版要比较 n × k 次，字典版只比较 n 次。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。
两版的耗时是分别量的，比的是趋势（字典版快几十倍以上），不是背下来的常数。

跑： py task1_count.py
判： py run_tests.py
"""

import time

# ── 给好的部分：造数据（别改）──────────────────────────────
n = 20000
mod = 500                      # 只有 0..499 这 500 个不同的值，重复很多
data = []
for i in range(n):
    data.append(i % mod)

# ── 第 1 版：列表版（按定义扫一遍）─────────────────────────
# TODO 1 参考解：先用「列表 + in 去重」拿到不同元素表，再对每个元素扫一遍整批数据。
t0 = time.perf_counter()       # 别改：计时开始
uniq = []
for x in data:
    if x not in uniq:
        uniq.append(x)
cnt_list = {}
for x in uniq:
    times = 0
    for y in data:
        if y == x:
            times += 1
    cnt_list[x] = times
t1 = time.perf_counter()       # 别改：计时结束

# ── 第 2 版：字典版（一遍哈希）─────────────────────────────
# TODO 2 参考解：只扫一遍，扫到 x 就 cnt[x] = cnt.get(x, 0) + 1。
t2 = time.perf_counter()       # 别改：计时开始
cnt_dict = {}
for x in data:
    cnt_dict[x] = cnt_dict.get(x, 0) + 1
t3 = time.perf_counter()       # 别改：计时结束

# ── 打印对照（这几行别改，自动判分按它们读结果）─────────────
print('列表版 不同元素', len(uniq), f'{t1 - t0:.6f} 秒')
print('字典版 不同元素', len(cnt_dict), f'{t3 - t2:.6f} 秒')
print('列表版 总次数', sum(cnt_list.values()))
print('字典版 总次数', sum(cnt_dict.values()))

# 两版结果逐字一致：把两个字典按同一个顺序摆成表再比
keys = sorted(cnt_dict)
same = True
for k in keys:
    if cnt_list.get(k) != cnt_dict.get(k):
        same = False
print('两版结果逐字一致', same)
print('字典版比列表版快', f'{round((t1 - t0) / max(t3 - t2, 1e-9), 1)} 倍')

# ── 对照：同一件事用 collections.Counter 写一遍（给好的，别改）──
# 课件讲过 Counter：元素是键、计数是值，查不存在的键返回 0。
# 它内部走的就是字典那套，结果与手写字典版相同。
from collections import Counter
c = Counter(data)
same_counter = True
for k in keys:
    if c[k] != cnt_dict.get(k):
        same_counter = False
print('Counter 与字典版一致', same_counter)

# ── 给判分脚本的接口（别改函数名与参数）──────────────────────
def count_list(items):
    """列表版：交回 {元素: 次数}。判分拿它在一组小数据上与字典版比对。"""
    # TODO 3 参考解：与 TODO 1 同一件事，数据换成参数 items。
    uniq = []
    for x in items:
        if x not in uniq:
            uniq.append(x)
    out = {}
    for x in uniq:
        times = 0
        for y in items:
            if y == x:
                times += 1
        out[x] = times
    return out


def count_dict(items):
    """字典版：交回 {元素: 次数}（一遍扫完）。"""
    # TODO 4 参考解：一遍扫，get 取不到就按 0 算。
    out = {}
    for x in items:
        out[x] = out.get(x, 0) + 1
    return out
