"""任务 4 · 完全背包与分组背包：两种变形各跟暴力版对拍

这一课要写三段：

  TODO 1  knap_complete2(w, v, C)      完全背包 · 换一种循环次序（物品在外、容量在内正序）
  TODO 2  knap_complete_cap(w, v, C)   完全背包 · 课件那一版（容量在外、逐容量从小往大推）
  TODO 3  knap_group(groups, C)        分组背包：**每组最多选一件**，
                                       组在外、容量在中（逆序）、组内物品在最里

完全背包允许每件物品拿任意多件，所以两版都该给出同一个答案
（判分拿的都是判分自己那份参照实现，两版都要对上它）：

    # 课件那一版：按容量从小到大逐个推
    dp = [0] * (C + 1)
    for c in range(1, C + 1):
        for i in range(len(w)):
            if w[i] <= c:
                dp[c] = max(dp[c], dp[c - w[i]] + v[i])

    # 另一版：物品在外、容量在内**正序**
    dp = [0] * (C + 1)
    for i in range(len(w)):
        for c in range(w[i], C + 1):
            dp[c] = max(dp[c], dp[c - w[i]] + v[i])

两版的差别只在「谁在外层」。**内层容量都必须是正序**——正序读到的是本轮已更新过的结果，
所以同一件还可以再拿一次，这正是完全背包要的（0/1 背包里同一个正序就是错的，任务 2 看过）。

分组背包只多一层循环，骨架还是「选与不选」：

    for g in groups:                       # 组在外层
        for c in range(C, -1, -1):         # 容量在中层、**逆序**
            for gw, gv in g:               # 组内物品在最里层
                if c >= gw:
                    dp[c] = max(dp[c], dp[c - gw] + gv)

容量逆序保证**这一组不会被选两次**——它跟 0/1 背包是同一个道理，
只不过「一件物品」换成了「一组里的一个选择」。

三句话归位：**每件能拿几次**（一次 → 逆序；任意多次 → 正序）、
**有没有分组约束**（有 → 加一层组循环）、**问不超过还是恰好**（恰好 → 非法状态设负无穷）。

接口：文件名、函数名、上面那些给好的数据、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那三段。

跑： py task4_complete_group.py
判： py run_tests.py
"""

from tools import (brute01, brute_complete, brute_group, is_neg, make_cases,
    NEG,
                   make_groups, show_case, show_check, show_groups, show_json,
                   show_pair)

# ── 给好的数据（别改）──────────────────────────────────────────────

# 小例子：与课件「完全背包：正序就是答案」那一节逐字相同
SM_W = [2, 3, 4]
SM_V = [3, 4, 5]
SM_CAPS = (4, 6, 8, 10, 12)

# 完全背包对拍那一批：固定种子 11 造 300 组（n ≤ 5、重量 ≤ 8、价值 ≤ 15、容量 ≤ 25）。
# 种子与取数次序都是判分接口：判分拿同一个种子自己复现这 300 组，
# 再拿自己那份参照实现重算每一组的期望值。
CASES_CG = make_cases(11, 300, 5, 8, 15, 25)

# 分组背包的两个例子
#   例一：三组（课件「变形：分组背包」那一节那一副），容量 1..12 逐个试
GRP1 = [[(2, 3), (3, 4)], [(4, 5), (5, 6)], [(1, 8)]]
GRP1_CAPS = tuple(range(1, 13))
#   例二：组里件数不齐（有一组只有一件、有一组三件），容量 1..14
GRP2 = [[(1, 4)], [(3, 7), (4, 9)], [(2, 3), (5, 10), (6, 11)]]
GRP2_CAPS = tuple(range(1, 15))

# 分组背包对拍那一批：固定种子 23 造 60 组（每组 ≤ 3 个小组、每组 ≤ 3 件、
# 重量 ≤ 7、价值 ≤ 12、容量 ≤ 18）。枚举每组三种可能，最坏 4^3 = 64 种组合，数得完。
CASES_GRP = make_groups(23, 60, 3, 3, 7, 12, 18)

CG_PROBE_SEED = 404                  # 判分探针自己造数据用的种子（任务里只打印它）
CG_PROBE_TRIALS = 10
CG_PROBE_LIMITS = (5, 8, 15, 25)     # 与 CASES_CG 同一套上限
GRP_PROBE_SEED = 505
GRP_PROBE_TRIALS = 8
GRP_PROBE_LIMITS = (3, 3, 7, 12, 18)


# ══ TODO 1 ═════════════════════════════════════════════════════
# 补 knap_complete2(w, v, C)：完全背包 · 物品在外、容量在内正序。
#   dp = [0] * (C + 1)；
#   外层 for i in range(len(w))，内层 for c in range(w[i], C + 1)：
#       dp[c] = max(dp[c], dp[c - w[i]] + v[i])
#   最后 return dp[C]。
#   注意：这与任务 2 的 TODO 1（内层正序的 0/1 版）**循环一模一样**，
#   区别只在问题本身——这里每件可以拿任意多件，所以正序是对的。
def knap_complete2(w, v, C):
    # 补这一段：见上面那几行说明。
    return NEG


# ══ TODO 2 ═════════════════════════════════════════════════════
# 补 knap_complete_cap(w, v, C)：完全背包 · 课件那一版「按容量从小到大逐个推」。
#   dp = [0] * (C + 1)；
#   外层 for c in range(1, C + 1)，内层 for i in range(len(w))：
#       if w[i] <= c: dp[c] = max(dp[c], dp[c - w[i]] + v[i])
#   最后 return dp[C]。
#   这一版与 TODO 1 是**两种不同的循环次序、同一个问题**，
#   所以两版必须给出同一个答案——「谁在外层」不影响结果，只要「能不能重复拿」
#   这件事由正序那一边（内层容量）表达出来。
#   循环结束时 c 停在 C 上，`return dp[C]` 与课件里的 `return dp[c]` 是同一个数。
def knap_complete_cap(w, v, C):
    # 补这一段：见上面那几行说明。
    return NEG


# ══ TODO 3 ═════════════════════════════════════════════════════
# 补 knap_group(groups, C)：分组背包——每组最多选一件。
#   groups 是「一串小组」，每组是 [(重量, 价值), …] 的一张表；
#   dp = [0] * (C + 1)；
#   for g in groups:                        组在外层
#       for c in range(C, -1, -1):          容量在中层、逆序（一组不会被选两次）
#           for gw, gv in g:                组内物品在最里层
#               if c >= gw:
#                   dp[c] = max(dp[c], dp[c - gw] + gv)
#   最后 return dp[C]。
#   顺带留意一件事：**同组里两件物品不会同时被拿**，因为容量那一层是逆序——
#   换成 range(0, C + 1) 正序，同一组就会被选两次（那又是 0/1 变完全背包那个错）。
def knap_group(groups, C):
    # 补这一段：见上面那几行说明。
    return NEG


if __name__ == '__main__':                       # 别改：这层守卫让判分 import 它时不出声
    # ── 1. 小例子：三支摆在一起（别改）───────────────────────────
    for cap in SM_CAPS:                                                      # 别改
        a = knap_complete2(SM_W, SM_V, cap)                                  # 别改
        b = knap_complete_cap(SM_W, SM_V, cap)                               # 别改
        show_case('小例 容量 ' + str(cap), SM_W, SM_V, cap, a, b,              # 别改
                  brute01(SM_W, SM_V, cap), brute_complete(SM_W, SM_V, cap))  # 别改
        show_check('小例 容量 ' + str(cap) + ' 两版一致', a == b)               # 别改

    # ── 2. 完全背包对拍：300 组（别改）───────────────────────────
    show_json('数据 完全背包对拍', {'seed': 11, 'trials': 300,                    # 别改
                                    'limits': [5, 8, 15, 25],                 # 别改
                                    'cases': CASES_CG})                       # 别改
    agree_cg = 0                                                             # 别改
    bad_a = 0                                                                # 别改
    bad_b = 0                                                                # 别改
    ge01 = 0                                                                 # 别改
    for index, (ws, vs, cc) in enumerate(CASES_CG, 1):                       # 别改
        a = knap_complete2(ws, vs, cc)                                       # 别改
        b = knap_complete_cap(ws, vs, cc)                                    # 别改
        want = brute_complete(ws, vs, cc)                                    # 别改
        if a == b:                                                           # 别改
            agree_cg += 1                                                    # 别改
        if a != want:                                                        # 别改
            bad_a += 1                                                       # 别改
        if b != want:                                                        # 别改
            bad_b += 1                                                       # 别改
        if (not is_neg(a)) and (not is_neg(b)) and a >= brute01(ws, vs, cc):  # 别改
            ge01 += 1                                                        # 别改
        show_case(index, ws, vs, cc, a, b, want, brute01(ws, vs, cc))         # 别改
    show_pair('对拍 完全背包两版一致的组数 与 总组数', agree_cg, len(CASES_CG))    # 别改
    show_pair('对拍 物品在外那版对不上参照的组数 与 总组数', bad_a, len(CASES_CG))  # 别改
    show_pair('对拍 课件那版对不上参照的组数 与 总组数', bad_b, len(CASES_CG))     # 别改
    show_check('对拍 两版一致', agree_cg == len(CASES_CG))                      # 别改
    show_check('对拍 两版都等于参照实现', bad_a == 0 and bad_b == 0)            # 别改
    # 完全背包的答案**永远不小于** 0/1 背包——可选的方案多了，最大值只会更大或不变
    show_check('对拍 完全背包答案都不小于 0/1 背包', ge01 == len(CASES_CG))      # 别改

    # ── 3. 分组背包例一：容量 1..12（别改）───────────────────────
    for cap in GRP1_CAPS:                                                    # 别改
        got = knap_group(GRP1, cap)                                          # 别改
        want = brute_group(GRP1, cap)                                        # 别改
        show_groups('组一 容量 ' + str(cap), GRP1, cap, got, want)             # 别改
        show_check('组一 容量 ' + str(cap) + ' 与枚举一致', got == want)        # 别改

    # ── 4. 分组背包例二：组里件数不齐（别改）─────────────────────
    ok2 = 0                                                                  # 别改
    for cap in GRP2_CAPS:                                                    # 别改
        got = knap_group(GRP2, cap)                                          # 别改
        want = brute_group(GRP2, cap)                                        # 别改
        if got == want:                                                      # 别改
            ok2 += 1                                                         # 别改
        show_groups('组二 容量 ' + str(cap), GRP2, cap, got, want)             # 别改
    show_pair('组二 与枚举一致的容量个数 与 容量个数', ok2, len(GRP2_CAPS))        # 别改

    # ── 5. 分组背包对拍：60 组（别改）───────────────────────────
    show_json('数据 分组背包对拍', {'seed': 23, 'trials': 60,                      # 别改
                                    'limits': [3, 3, 7, 12, 18],               # 别改
                                    'cases': CASES_GRP})                      # 别改
    agree_grp = 0                                                            # 别改
    for index, (groups, cc) in enumerate(CASES_GRP, 1):                      # 别改
        got = knap_group(groups, cc)                                         # 别改
        want = brute_group(groups, cc)                                       # 别改
        if got == want:                                                      # 别改
            agree_grp += 1                                                   # 别改
        show_groups(index, groups, cc, got, want)                            # 别改
    show_pair('对拍 分组背包与枚举一致的组数 与 总组数', agree_grp, len(CASES_GRP))   # 别改
    show_check('对拍 分组背包处处与枚举一致', agree_grp == len(CASES_GRP))        # 别改

    # ── 6. 探针要用的那批数据的说明（别改）───────────────────────
    show_json('数据 探针', {'cg_seed': CG_PROBE_SEED, 'cg_trials': CG_PROBE_TRIALS,   # 别改
                            'cg_limits': list(CG_PROBE_LIMITS),                    # 别改
                            'grp_seed': GRP_PROBE_SEED,                           # 别改
                            'grp_trials': GRP_PROBE_TRIALS,                       # 别改
                            'grp_limits': list(GRP_PROBE_LIMITS)})                # 别改
