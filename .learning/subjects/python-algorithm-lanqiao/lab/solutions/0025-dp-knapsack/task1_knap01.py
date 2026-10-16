"""任务 1 · 0/1 背包的两版写法：二维表与一维逆序

这一课要写两段：

  TODO 1  knap01_2d(w, v, C)       0/1 背包 · 二维：dp[i][c] = 只看前 i 件、容量上限 c 的最大价值
  TODO 2  knap01_1d_rev(w, v, C)   0/1 背包 · 一维滚动数组 · 内层**逆序**

两版回答的是同一个问题，所以**任何一组数据上答案都必须一样**。
这一份会把两版的答案一行行摆出来对，还会把四条不变式打成 True / False。

二维版三步（课件「二维写法」那一节）：

    dp[i][c] = dp[i-1][c]                            不拿第 i 件：答案跟前 i-1 件一样
    if c >= w[i-1]:
        dp[i][c] = max(dp[i][c],
                       dp[i-1][c - w[i-1]] + v[i-1])     拿：腾出 w[i-1] 的容量，价值加 v[i-1]

**拿的那一支查的是 dp[i-1]，不是 dp[i]**。这个下标就是下一课一切差别的源头：
`i-1` 意味着「第 i 件还没被拿过」，所以同一件物品不会被拿第二次。

一维版是同一件事压成一行表：算第 i 件时只用到第 i-1 行，于是一行反复覆盖自己。
代价是**必须从大到小遍历容量**——算 `dp[c]` 用到的 `dp[c - w[i]]` 下标更小，
逆序还没走到那儿，所以它一定还是「前 i-1 件」的结果。

参考解（solutions/）：两段 TODO 都填好了，可以直接跑 `py run_tests.py` 对照。

接口：文件名、函数名、上面那些给好的数据、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那两段。

跑： py task1_knap01.py
判： py run_tests.py
"""

from tools import (brute01, make_cases, show_case, show_check, show_json,
                   show_pair)

# ── 给好的数据（别改）──────────────────────────────────────────────

# 第一个例子与课件「从选与不选说起」那一节逐字相同
BAG_W = [2, 3, 4, 5]
BAG_V = [3, 4, 5, 6]
BAG_C = 8

# 第二个例子：一张只有一件物品的表，用来看「容量装不下」与「刚好装上」两档
ONE_W = [7]
ONE_V = [9]

# 对拍那一批：固定种子 2025 造 12 组（n ≤ 6、重量 ≤ 9、价值 ≤ 20、容量 ≤ 22）。
# 种子与取数次序都是判分接口——判分拿同一个种子自己复现这 12 组，
# 再拿自己那份参照实现重算期望值，所以这里别改种子、别改取数次序。
CASES_DP = make_cases(2025, 12, 6, 9, 20, 22)

DP_PROBE_SEED = 707                  # 判分探针自己造数据用的种子（任务里只打印它）
DP_PROBE_TRIALS = 15
DP_PROBE_LIMITS = (6, 9, 20, 22)     # 与 CASES_DP 同一套上限


# ══ TODO 1 ═════════════════════════════════════════════════════
# 补 knap01_2d(w, v, C)：0/1 背包的二维版，交回 dp[n][C]（能装下的最大总价值）。
#   n = len(w)；dp = [[0] * (C + 1) for _ in range(n + 1)]（第 0 行全是 0，
#   意思是「一件都不看」时价值当然是 0）；
#   外层 for i in range(1, n + 1)，内层 for c in range(C + 1)：
#       第一行先写不拿那一支 dp[i][c] = dp[i - 1][c]；
#       第二行判 if c >= w[i - 1]: 拿第 i 件，查的是 **dp[i - 1][c - w[i - 1]] + v[i - 1]**。
#   最后 return dp[n][C]。
#   两个下标都对上物品的下标：dp 的第 i 行对应 w[i - 1] / v[i - 1] 那一件。
def knap01_2d(w, v, C):
    n = len(w)
    dp = [[0] * (C + 1) for _ in range(n + 1)]      # 第 0 行：一件都不看，价值是 0
    for i in range(1, n + 1):
        for c in range(C + 1):
            dp[i][c] = dp[i - 1][c]                             # 不拿第 i 件
            if c >= w[i - 1]:                                   # 拿：查的是 dp[i-1]
                dp[i][c] = max(dp[i][c], dp[i - 1][c - w[i - 1]] + v[i - 1])
    return dp[n][C]


# ══ TODO 2 ═════════════════════════════════════════════════════
# 补 knap01_1d_rev(w, v, C)：同一件事压成一维，内层容量**从大到小**。
#   dp = [0] * (C + 1)；
#   外层 for i in range(len(w))，内层 for c in range(C, w[i] - 1, -1)：
#       dp[c] = max(dp[c], dp[c - w[i]] + v[i])
#   最后 return dp[C]。
#   写成 range(w[i], C + 1)（正序）就不是 0/1 背包了：算 dp[c] 时 dp[c - w[i]]
#   在本轮已经被更新过，同一件物品会被拿第二次、第三次——任务 2 专门看这件事。
def knap01_1d_rev(w, v, C):
    dp = [0] * (C + 1)
    for i in range(len(w)):
        for c in range(C, w[i] - 1, -1):            # 逆序：dp[c-w[i]] 还没被本轮更新过
            dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]


if __name__ == '__main__':                       # 别改：这层守卫让判分 import 它时不出声
    # ── 1. 第一个例子：三版答案要一致（别改）──────────────────────
    two = knap01_2d(BAG_W, BAG_V, BAG_C)                                     # 别改
    one = knap01_1d_rev(BAG_W, BAG_V, BAG_C)                                 # 别改
    brute = brute01(BAG_W, BAG_V, BAG_C)                                     # 别改
    show_pair('例子 二维 与 一维逆序', two, one)                                # 别改
    show_check('例子 与枚举一致', two == brute and one == brute, '枚举 ' + str(brute))   # 别改
    show_check('例子 两版一致', two == one)                                     # 别改
    show_case('例子', BAG_W, BAG_V, BAG_C, two, one, brute)                    # 别改

    # ── 2. 单件物品那一档（别改）─────────────────────────────────
    for cap in (6, 7, 8):                                                    # 别改
        a = knap01_2d(ONE_W, ONE_V, cap)                                     # 别改
        b = knap01_1d_rev(ONE_W, ONE_V, cap)                                 # 别改
        show_case('单件 容量 ' + str(cap), ONE_W, ONE_V, cap, a, b,          # 别改
                  brute01(ONE_W, ONE_V, cap))                                # 别改

    # ── 3. 对拍那一批：12 组数据（别改）───────────────────────────
    show_json('数据 二维', {'seed': 2025, 'trials': 12, 'limits': [6, 9, 20, 22],   # 别改
                            'cases': CASES_DP})                                  # 别改
    ok_count = 0                                                             # 别改
    brute_count = 0                                                          # 别改
    for index, (ws, vs, cc) in enumerate(CASES_DP, 1):                       # 别改
        a = knap01_2d(ws, vs, cc)                                            # 别改
        b = knap01_1d_rev(ws, vs, cc)                                        # 别改
        want = brute01(ws, vs, cc)                                           # 别改
        # 「一致」的要求是**两边都给出了答案**且相等：两个 None 不算一致
        if a is not None and a == b:                                         # 别改
            ok_count += 1                                                    # 别改
        if a == want and b == want:                                          # 别改
            brute_count += 1                                                 # 别改
        show_case(index, ws, vs, cc, a, b, want)                             # 别改
    show_pair('对拍 两版一致且都给出答案的组数 与 总组数', ok_count, len(CASES_DP))   # 别改
    show_check('对拍 两版处处一致', ok_count == len(CASES_DP))                   # 别改
    show_pair('对拍 两版都对上枚举的组数 与 总组数', brute_count, len(CASES_DP))  # 别改

    # ── 4. 四条不变式（别改）────────────────────────────────────
    # 答案不会超过「所有物品都拿」的价值，也不会是负数——两版都查一遍
    bound_ok = True                                                          # 别改
    for ws, vs, cc in CASES_DP:                                              # 别改
        bound = sum(vs)                                                      # 别改
        a, b = knap01_2d(ws, vs, cc), knap01_1d_rev(ws, vs, cc)              # 别改
        for got in (a, b):                                                   # 别改
            if got is None or got < 0 or got > bound:                        # 别改
                bound_ok = False                                             # 别改
    show_check('不变式 答案在 0 与总价值之间', bound_ok)                          # 别改
    zero_two = knap01_2d(BAG_W, BAG_V, 0)                                    # 别改
    zero_one = knap01_1d_rev(BAG_W, BAG_V, 0)                                # 别改
    show_pair('不变式 容量为 0 时两版都交回 0', 0 if zero_two is None else zero_two,   # 别改
              0 if zero_one is None else zero_one)                           # 别改
    show_check('不变式 容量为 0 时两版是 0', zero_two == 0 and zero_one == 0)    # 别改

    # ── 5. 探针要用的那批数据的说明（别改）───────────────────────
    show_json('数据 探针', {'seed': DP_PROBE_SEED, 'trials': DP_PROBE_TRIALS,  # 别改
                            'limits': list(DP_PROBE_LIMITS)})                 # 别改
