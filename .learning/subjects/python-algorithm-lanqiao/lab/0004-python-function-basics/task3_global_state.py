"""任务 3 · 故意用全局变量在函数之间传状态

同一道题（读入 N、求 1 到 N 之间的奇数个数）再写一版：
数据不靠参数与 return 传，全靠全局变量。

这一版的**第一行**输出必须和任务 1 的函数版逐字一致；
后面两行是给判分看的——只有值真的存进了全局变量，函数外面才读得到它。

顺带看一眼：读 read_n 的定义那一行，能看出它动了哪个数据吗？

文件名与三个函数名是判分接口，别改。

跑： py task3_global_state.py      （敲一个数回车）
判： py run_tests.py
"""

n_global = 0
count_global = 0


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 read_n()：读入一行、转成整数、负数归零，把结果存进全局 n_global。
# 提示：要在函数里改全局变量，函数体第一行写 global n_global。
def read_n():
    pass


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 odd_count()：从 n_global 里读数据，把答案存进全局 count_global。
def odd_count():
    pass


# ══ TODO 3 ═════════════════════════════════════════════════
# 写 show()：把 count_global 打印出来。
def show():
    pass


# ── 入口（别改）────────────────────────────────────────────
# 注意：这里没有 solve——数据靠全局变量自己流动。
read_n()
odd_count()
show()
print('函数外读到全局 n_global', n_global)
print('函数外读到全局 count_global', count_global)
