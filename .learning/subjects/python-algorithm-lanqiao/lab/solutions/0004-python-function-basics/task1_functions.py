"""任务 1 参考解 · 摊平版改写成四个函数

与 flat_odd.py 逐字一致的函数版：
  read_n() 读入并检查 → odd_count(n) 算 → show(count) 打印 → solve() 串起来
"""


def read_n():
    n = int(input())        # 读入不带提示参数：提示文字会写进 stdout
    if n < 0:
        n = 0
    return n


def odd_count(n):
    return (n + 1) // 2     # 算法与摊平版一字不差，只是把 print 换成 return


def show(count):
    print(count)            # 只负责输出，不交回值


def solve():
    n = read_n()
    show(odd_count(n))      # 算出来的值直接交给 show，不必再落地一个名字


# ── 入口 ───────────────────────────────────────────────────
solve()
