"""任务 4 · 破坏单调性：二分答案会怎样？

二分答案依赖 check 函数的**单调性**——「x 可行 → 所有比 x 小的也一定可行」。
如果 check 不单调，二分答案的结果会随着**初始区间**变化而漂移，不再可信。

这一关的任务是：
  + TODO 1：写一个**不单调**的 check 函数 check_bad(x)：
    当 x 为偶数且 x ≤ 8 时返回 True，否则返回 False。
    这个函数的 True 区间是 {2, 4, 6, 8}，不是从 1 开始的连续段。

  + TODO 2：在不通的初始区间 [lo, hi] 上跑二分答案，观察结果：
    - [1, 20]  →  结果是多少？（它可能找到 8，也可能找到 2）
    - [1, 10]  →  结果是多少？
    - [1, 5]   →  结果是多少？
    然后把每个结果和暴力枚举的真·答案（8）比较，看到差别。

  + TODO 3：写 brute_bad(lo, hi) 枚举初始区间内所有值，找出真正最大的可行值。

要点：
  二分答案（上取整版本）在 check 不单调时，找到的不一定是全局最大值——
  它找到的是「二分路径上第一个遇到的峰值」，依赖初始区间。

接口：函数名、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的三段。

跑： py task04_break_monotonicity.py
判： py run_tests.py
"""

from tools import show_count


# ── 正确的 check（单调）—— 用作对照 ──────────────────────────────
def check_good(x):
    """单调版：x ≤ 8 时可行。True 区间是 [1, 8]。"""
    return x <= 8


# ══ TODO 1 ══════════════════════════════════════════════════════
# 写 check_bad(x)：不单调，当 x 为偶数且 x ≤ 8 时返回 True。
#
# 要点：
#   return (x % 2 == 0) and (x <= 8)
def check_bad(x):
    return False


# ══ TODO 2 ══════════════════════════════════════════════════════
# 写 binary_search_on_answer(check_fn, lo, hi)：
# 标准二分答案模板（上取整），找最大可行值。
#
# 要点：
#   当 lo < hi 时：
#       mid = (lo + hi + 1) // 2
#       if check_fn(mid):
#           lo = mid
#       else:
#           hi = mid - 1
#   return lo if check_fn(lo) else 0
def binary_search_on_answer(check_fn, lo, hi):
    return 0


# ══ TODO 3 ══════════════════════════════════════════════════════
# 写 brute_best(check_fn, lo, hi)：在 [lo, hi] 中枚举，找出真正最大的可行值。
# 这是暴力枚举的"真·答案"。
#
# 要点：
#   for x in range(hi, lo - 1, -1):
#       if check_fn(x):
#           return x
#   return 0
def brute_best(check_fn, lo, hi):
    return 0


if __name__ == '__main__':                     # 别改
    # ── 单调对照 ─────────────────────────────────────────────
    print('单调 check_good(8)', check_good(8))               # 别改：True
    print('单调 二分 [1, 20]', binary_search_on_answer(check_good, 1, 20))  # 别改：8
    print('单调 暴力 [1, 20]', brute_best(check_good, 1, 20))              # 别改：8

    # ── 不单调 ───────────────────────────────────────────────
    print('不单调 check_bad(8)', check_bad(8))               # 别改：True
    print('不单调 check_bad(7)', check_bad(7))               # 别改：False
    print('不单调 check_bad(6)', check_bad(6))               # 别改：True
    print('不单调 check_bad(4)', check_bad(4))               # 别改：True
    print('不单调 check_bad(2)', check_bad(2))               # 别改：True

    # ── 不同初始区间的二分结果 ───────────────────────────────
    for lo, hi in [(1, 20), (1, 10), (1, 8), (1, 5), (3, 10), (5, 20)]:  # 别改
        bs = binary_search_on_answer(check_bad, lo, hi)     # 别改
        bf = brute_best(check_bad, lo, hi)                  # 别改
        match = '一致' if bs == bf else '不一致'              # 别改
        print(f'区间 [{lo}, {hi}]  二分 {bs}  暴力 {bf}  {match}')  # 别改

    # ── 结论 ─────────────────────────────────────────────────
    bs_8 = binary_search_on_answer(check_bad, 1, 20)        # 别改
    bf_8 = brute_best(check_bad, 1, 20)                     # 别改
    print('二分答案认为最大可行值是', bs_8)                   # 别改
    print('暴力枚举认为最大可行值是', bf_8)                   # 别改
    print('两者一致？', bs_8 == bf_8)                         # 别改

    # ── 计数行 ───────────────────────────────────────────────
    show_count('01', 'check_bad(8)', check_bad(8))                     # 别改
    show_count('02', '二分 [1,20] 结果', bs_8)                         # 别改
    show_count('03', '暴力 [1,20] 结果', bf_8)                         # 别改
    show_count('04', '两者一致', 1 if bs_8 == bf_8 else 0)             # 别改