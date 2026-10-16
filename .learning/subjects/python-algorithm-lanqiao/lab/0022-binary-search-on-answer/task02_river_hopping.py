"""任务 2 · 跳石头（River Hopping / 跳石头）

题目：一条河从 0 到 river_len，中间有 N 块石头在 positions[i]。你可以移走至多
remove_limit 块石头（不能移 0 和 river_len）。问：移走之后，相邻落脚点（含起点
和终点）之间的最小距离最大能是多少？

这也是二分答案：
  1. check(min_gap) —— 判断能否通过移走 ≤ remove_limit 块石头，使所有间隔 ≥ min_gap
  2. 在 [1, river_len] 里二分猜答案

接口：函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的两段。

跑： py task02_river_hopping.py
判： py run_tests.py
"""

from tools import make_river_stones, show_count, show_time, timed


# ══ TODO 1 ════════════════════════════════════════════════════
# 写 check_jump(stones, river_len, min_gap, remove_limit)：
# 判断能否用 ≤ remove_limit 次移除，使相邻落脚点的间距 ≥ min_gap。
#
# 要点：
#   prev = 0
#   removed = 0
#   for pos in stones:
#       if pos - prev < min_gap:
#           removed += 1          这石头太小了 → 移掉
#       else:
#           prev = pos           够大 → 留着，更新前一个位置
#   if river_len - prev < min_gap:
#       最后一段如果也不够，必须移掉一块→但终点不能移，
#       所以这里的处理是：最后一段不够意味着无解，return False
#   return removed <= remove_limit
def check_jump(stones, river_len, min_gap, remove_limit):
    return False


# ══ TODO 2 ════════════════════════════════════════════════════
# 写 max_min_gap(stones, river_len, remove_limit)：二分答案
# 找最大的可行最小间距。
#
# 要点：
#   lo = 1, hi = river_len
#   当 lo < hi 时：
#       mid = (lo + hi + 1) // 2
#       if check_jump(stones, river_len, mid, remove_limit):
#           lo = mid
#       else:
#           hi = mid - 1
#   return lo
def max_min_gap(stones, river_len, remove_limit):
    return 0


if __name__ == '__main__':                    # 别改
    # ── 课件数据 ─────────────────────────────────────────────
    river_len = 25                            # 别改
    stones = [2, 11, 14, 17, 21]              # 别改
    print('河长', river_len)                   # 别改
    print('石头', stones)                      # 别改

    # ── 验证 check 函数 ─────────────────────────────────────
    print('min_gap=4 移除2', check_jump(stones, river_len, 4, 2))   # 别改：期望 True
    print('min_gap=4 移除1', check_jump(stones, river_len, 4, 1))   # 别改：期望 False
    print('min_gap=5 移除2', check_jump(stones, river_len, 5, 2))   # 别改：期望 False

    # ── 验证二分答案 ─────────────────────────────────────────
    print('移除2 最大最小间距', max_min_gap(stones, river_len, 2))   # 别改：期望 4
    print('移除0 最大最小间距', max_min_gap(stones, river_len, 0))   # 别改：期望 2
    print('移除3 最大最小间距', max_min_gap(stones, river_len, 3))   # 别改：期望 6

    # ── 扫描全部移除数 ───────────────────────────────────────
    for r in range(len(stones) + 1):          # 别改
        ans = max_min_gap(stones, river_len, r)  # 别改
        print('移除' + str(r), ans)             # 别改

    # ── 边界 ─────────────────────────────────────────────────
    print('无石头 移除0', max_min_gap([], 10, 0))         # 别改：期望 10
    print('一块石头 移除0', max_min_gap([5], 10, 0))      # 别改：期望 5
    print('一块石头 移除1', max_min_gap([5], 10, 1))      # 别改：期望 10

    # ── 计数行 ───────────────────────────────────────────────
    ans4, _ = timed(max_min_gap, stones, river_len, 2)    # 别改
    show_count('01', '移除2 答案', ans4)                   # 别改