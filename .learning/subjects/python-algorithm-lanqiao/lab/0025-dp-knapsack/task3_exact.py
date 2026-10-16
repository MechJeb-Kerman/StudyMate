"""任务 3 · 恰好装满：非法状态要设成负无穷

前面所有写法回答的都是「**不超过**容量 C 的最大价值」。还有一问：
**恰好装满容量 C** 的最大价值是多少？（有时无解。）

这一课要写四段：

  TODO 1  knap01_exact(w, v, C)          恰好装满：只把 dp[0] 设 0，其余全是负无穷
  TODO 2  knap01_exact_rev(w, v, C)      初始化照上面那一版，但内层容量写成**正序**
                                         （错：容量 6 = 3+3 这种同一件被拿了第二次的格子会被算成有解）
  TODO 3  probe_exact(w, v, C)           按「恰好装满」那一版独立写一遍
                                         （判分也拿它探针：说明这一段不是照着抄上面的）
  TODO 4  first_short(w, v, C)           在**这一个容量**上，恰好装满与正序那一版给出不同答案时交回
                                         (容量, 恰好装满的答案, 正序那一版的答案)；一样就交回 None

正确版的骨架（与「不超过」那版只差第一行与那个 if）：

    NEG = float('-inf')
    dp = [NEG] * (C + 1)          # 非法状态：这个容量凑不出来
    dp[0] = 0                     # 容量 0 谁都能装满，价值是 0
    for i in range(len(w)):
        for c in range(C, w[i] - 1, -1):        # 内层容量逆序
            if dp[c - w[i]] != NEG:             # 那一格凑不出来就别往这儿搬
                dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]                  # 还是 NEG 就说明这个容量凑不出来

**方向就是这一课的那件事。** 逆序时算 `dp[c]` 读到的 `dp[c - w]` 下标更小、
本轮还**没走到**，读到的就是「前 i 件」的结果，所以同一件不会被重复拿。
重量 3/5/7（价值 = 重量）时，每一件只用一次，凑得出来的只有 3、5、7、8（3+5）、
10（3+7）、12（5+7）、15（3+5+7）——无解的正好是 1、2、4、6、9、11、13。
换成正序，算到容量 6 时 `dp[3]` 已经被本轮填成 3 了，于是 3+3 被算进去，
9（3+3+3）、11、13 也一样——报出来的「无解」就比真正的无解少。

为什么 `-inf` 能挡住：`dp[c - w]` 是 `-inf` 时，`-inf + v` 还是 `-inf`，
**比 `-inf` 不大**，那一格就不会被填上。没填上就等于「这个容量凑不出来」。

为什么全 0 初始化是错的：它把「凑不出来」这一档也当成 0 价值，
于是算出来的其实是**「不超过」的答案**——一个看着很正常、也确实是某个问题的答案的数，
只是**回答的不是你问的那个问题**。容量 11、物品重量 3 / 5 / 7 时，
正确回答是「无解」，写错初始化给 10。

参考解（solutions/）：四段 TODO 都填好了，可以直接跑 `py run_tests.py` 对照。

接口：文件名、函数名、上面那些给好的数据、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那四段。

跑： py task3_exact.py
判： py run_tests.py
"""

from tools import (NEG, brute01, fmt, is_neg, make_cases, show_case, show_check,
                   show_four, show_json, show_note, show_pair)

# ── 给好的数据（别改）──────────────────────────────────────────────

# 课件「恰好装满与不超过」那一节那个例子：价值 = 重量，
# 所以「装满多少」就是价值——凑得出来的容量一眼能看出来。
EX_W = [3, 5, 7]
EX_V = [3, 5, 7]
EX_CAPS = tuple(range(1, 16))        # 容量 1..15 逐个问一遍

# 凑不出来的那些容量：EX_W 每一件只用一次，凑得出的只有 0、3、5、7、8、10、12、15
UNREACHABLE = (1, 2, 4, 6, 9, 11, 13, 14)

# 第二个例子：重量 4 / 6、价值 5 / 8——容量 6 恰好装满只有「拿重量 6 那件」一条路，
# 容量 8 要 4+4、容量 12 要 4+4+4，都是同一件拿两次以上，所以那两个容量无解。
EX2_W = [4, 6]
EX2_V = [5, 8]
EX2_CAPS = (4, 6, 8, 10, 12)

# 再一个例子：有一件 1 重的物品，于是所有容量都凑得出来
EX3_W = [1, 4, 9]
EX3_V = [2, 5, 12]
EX3_CAPS = tuple(range(1, 13))

# 对拍那一批：固定种子 31 造 10 组（n ≤ 5、重量 ≤ 8、价值 ≤ 15、容量 ≤ 20）。
# 种子与取数次序都是判分接口：判分拿同一个种子自己复现这 10 组，
# 再拿自己那份参照实现重算「恰好装满」与「逆序那一版」两列期望值。
CASES_EX = make_cases(31, 10, 5, 8, 15, 20)

EX_PROBE_SEED = 99                   # 判分探针自己造数据用的种子（任务里只打印它）
EX_PROBE_TRIALS = 12
EX_PROBE_LIMITS = (5, 8, 15, 20)     # 与 CASES_EX 同一套上限


def badinit_exact(w, v, C):
    """「恰好装满」但初始化照「不超过」那版写成全 0——课件里那个对照用的错版。

    它不是 TODO，是给好的对照：这一份用它来数「两种初始化答案不同的容量个数」。
    初始化全 0 会把「凑不出来」当成 0 价值，于是它交回的其实是「不超过」的答案。
    """
    dp = [0] * (C + 1)            # 初始化写成了「不超过」那一版：全是 0
    for i in range(len(w)):
        for c in range(C, w[i] - 1, -1):
            dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]


# ══ TODO 1 ═════════════════════════════════════════════════════
# 补 knap01_exact(w, v, C)：交回「恰好装满容量 C」的最大价值；凑不出来就交回负无穷。
#   dp = [NEG] * (C + 1)；dp[0] = 0（只改这一格！）；
#   外层 for i in range(len(w))，内层 for c in range(C, w[i] - 1, -1)：**逆序**；
#   搬之前先判 if dp[c - w[i]] != NEG:，满足才 dp[c] = max(dp[c], dp[c - w[i]] + v[i])；
#   最后 return dp[C]（它还是 NEG 就表示这个容量凑不出来）。
#   返回的一定是数字或负无穷：别把 -inf 改写成 0、None 或 -1，
#   判分要按「无解」这一档读它（tools.fmt 会把 -inf 打成「无解」）。
def knap01_exact(w, v, C):
    # 补这一段：见上面那几行说明。
    return NEG


# ══ TODO 2 ═════════════════════════════════════════════════════
# 补 knap01_exact_rev(w, v, C)：初始化照 TODO 1，但内层容量写成**正序**——
# 正序读到的 dp[c - w] 是本轮刚填上的值，同一件会被拿第二次，
# 于是容量 6（3+3）、9（3+3+3）、11、13 被算成有解，「无解」那一档就漏报了。
#   dp = [NEG] * (C + 1)；dp[0] = 0；
#   外层 for i in range(len(w))、内层 for c in range(w[i], C + 1)：正序；
#   if dp[c - w[i]] != NEG: dp[c] = max(dp[c], dp[c - w[i]] + v[i])；
#   最后 return dp[C]。
#   这一版是**故意写错的那一支**（它是这一课要看的对照），别改成逆序、也别去掉那个 if。
def knap01_exact_rev(w, v, C):
    # 补这一段：见上面那几行说明。
    return NEG


# ══ TODO 3 ═════════════════════════════════════════════════════
# 补 probe_exact(w, v, C)：按「恰好装满」那一版**独立写一遍**，交回同一个答案。
#   它与 TODO 1 回答的是同一个问题，所以任何一组数据上都必须给出同一个值
#   （凑不出来时两边都是负无穷）。判分也会另起一个进程 import 这一个函数，
#   拿判分自己造的数据去试——所以它必须自己站得住，不能去调 TODO 1。
#   写法上与 TODO 1 等价就行：初始化只留 dp[0] = 0，非法状态用 NEG 挡住
#   （`if dp[c - w] != NEG` 那一句别丢），内层容量也照 TODO 1 那样**逆序**。
def probe_exact(w, v, C):
    # 与 TODO 1 等价、独立写一遍：一张表，只有 dp[0] 是 0
    # TODO 3
    # 第四条路：逐容量从小到大推（课件「另一种写法」那一节）。
    # dp[0] = 0，其余 NEG；for c in range(1, C + 1)：
    #   再 for ww, vv in zip(w, v)：if c >= ww and dp[c - ww] != NEG 就更新。
    # 它必须与 TODO 1 给出同一个值。
    return NEG


# ══ TODO 4 ═════════════════════════════════════════════════════
# 补 first_short(w, v, C)：在**容量 C 这一个容量上**，恰好装满与正序那一版给出不同答案时
# 交回 (C, 恰好装满的答案, 正序那一版的答案)；一样就交回 None。
#   ex = knap01_exact(w, v, C)
#   fwd = knap01_exact_rev(w, v, C)
#   if ex != fwd: return (C, ex, fwd)
#   return None
#   注意 ex / fwd 是负无穷时也要能比：**负无穷与任何数字都不相等**，
#   而两个负无穷彼此相等——所以「正序多算成有解」的容量天然会被这一条挑出来。
def first_short(w, v, C):
    # 补这一段：见上面那几行说明。
    return None


if __name__ == '__main__':                       # 别改：这层守卫让判分 import 它时不出声
    # ── 1. 第一个例子：容量 1..15 逐个问一遍（别改）────────────────
    show_json('数据 例子', {'w': EX_W, 'v': EX_V, 'caps': list(EX_CAPS),        # 别改
                            'unreachable': list(UNREACHABLE)})                  # 别改
    for cap in EX_CAPS:                                                      # 别改
        ex = knap01_exact(EX_W, EX_V, cap)                                   # 别改
        rev = knap01_exact_rev(EX_W, EX_V, cap)                              # 别改
        probe = probe_exact(EX_W, EX_V, cap)                                 # 别改
        limit = brute01(EX_W, EX_V, cap)                                     # 别改
        # 标签带「例一 容量」前缀：下面第 6 段那批对拍用的标签是纯编号（1、2、…），
        # 两者不能撞——判分按标签整段找行，撞了就读到错的那一行。
        show_case('例一 容量 ' + str(cap), EX_W, EX_V, cap, ex, rev, probe, limit)   # 别改
    ex_ok = sum(1 for c in EX_CAPS if knap01_exact(EX_W, EX_V, c) == NEG)     # 别改
    show_pair('例子 无解的容量个数 与 容量个数', ex_ok, len(EX_CAPS))            # 别改
    show_check('例子 无解的容量正好是 1 2 4 6 9 11 13',                        # 别改
               all(knap01_exact(EX_W, EX_V, c) == NEG for c in UNREACHABLE)  # 别改
               and all(knap01_exact(EX_W, EX_V, c) != NEG                    # 别改
                       for c in EX_CAPS if c not in UNREACHABLE))            # 别改
    # 凑得出来时「恰好装满」的价值不会超过「不超过」那一问的价值
    show_check('例子 恰好装满不超过不超过那一问',                                # 别改
               all((knap01_exact(EX_W, EX_V, c) == NEG)                      # 别改
                   or knap01_exact(EX_W, EX_V, c) <= brute01(EX_W, EX_V, c)  # 别改
                   for c in EX_CAPS))                                        # 别改

    # ── 2. 两种方向的差别（别改）─────────────────────────────────
    diff = 0                                                                 # 别改
    for cap in EX_CAPS:                                                      # 别改
        if knap01_exact(EX_W, EX_V, cap) != knap01_exact_rev(EX_W, EX_V, cap):  # 别改
            diff += 1                                                        # 别改
    show_pair('差别 方向不同的容量个数 与 容量个数', diff, len(EX_CAPS))          # 别改
    # 正序多算的是「同一件拿了第二次」的那些容量：6 = 3+3、9 = 3+3+3、14 = 7+7
    show_check('差别 正序多算的都是要重复用同一件的容量',                          # 别改
               all(knap01_exact_rev(EX_W, EX_V, c) != NEG                         # 别改
                   for c in (6, 9, 14)))                                      # 别改
    # 全 0 初始化把「凑不出来」当成 0 价值，于是交回的是「不超过」的答案
    show_check('差别 全 0 初始化的那一版给出的是不超过那一问的答案',                 # 别改
               all(badinit_exact(EX_W, EX_V, c) == brute01(EX_W, EX_V, c)     # 别改
                   for c in UNREACHABLE))                                    # 别改

    # ── 3. 两种初始化的差别（别改）───────────────────────────────
    bad_diff = 0                                                             # 别改
    for cap in EX_CAPS:                                                      # 别改
        if knap01_exact(EX_W, EX_V, cap) != badinit_exact(EX_W, EX_V, cap):   # 别改
            bad_diff += 1                                                    # 别改
    show_pair('差别 两种初始化答案不同的容量个数 与 容量个数', bad_diff, len(EX_CAPS))   # 别改
    show_check('差别 凑不出来的那些容量上两者都不同',                            # 别改
               all(knap01_exact(EX_W, EX_V, c) != badinit_exact(EX_W, EX_V, c)  # 别改
                   for c in UNREACHABLE))                                    # 别改
    show_check('差别 全 0 初始化在凑不出来的容量上给出的是不超过的答案',            # 别改
               all(badinit_exact(EX_W, EX_V, c) == brute01(EX_W, EX_V, c)     # 别改
                   for c in UNREACHABLE))                                    # 别改

    # ── 4. 第二个例子（第四条路）（别改）─────────────────────────
    for cap in EX2_CAPS:                                                     # 别改
        show_case('例二 容量 ' + str(cap), EX2_W, EX2_V, cap,                  # 别改
                  knap01_exact(EX2_W, EX2_V, cap),                           # 别改
                  knap01_exact_rev(EX2_W, EX2_V, cap),                        # 别改
                  probe_exact(EX2_W, EX2_V, cap))                            # 别改

    # ── 5. 第三个例子：有一件 1 重的物品（别改）─────────────────
    all_reach = True                                                         # 别改
    for cap in EX3_CAPS:                                                     # 别改
        ex = knap01_exact(EX3_W, EX3_V, cap)                                 # 别改
        # 这一条问的是「**不超过**那一问」：有 1 重那件（价值 2）垫底，
        # 1..12 每个容量都装得下，brute01 给的答案一定大于 0。
        # 「恰好装满」那一问里 2、3、6、7、8、11、12 是凑不出来的（要同一件拿两次以上），
        # 那是上面「无解」那一档的事，两者不是一回事，别把这一条改成按恰好装满判。
        if brute01(EX3_W, EX3_V, cap) <= 0:                                  # 别改
            all_reach = False                                                # 别改
        show_case('例三 容量 ' + str(cap), EX3_W, EX3_V, cap, ex,              # 别改
                  knap01_exact_rev(EX3_W, EX3_V, cap),                       # 别改
                  probe_exact(EX3_W, EX3_V, cap))                            # 别改
    show_check('例三 每个容量都装得满', all_reach)                              # 别改

    # ── 6. 两版一致吗 + 对拍那一批（别改）───────────────────────
    show_json('数据 恰好装满对拍', {'seed': 31, 'trials': 10,                    # 别改
                                    'limits': [5, 8, 15, 20],                # 别改
                                    'cases': CASES_EX})                      # 别改
    agree = 0                                                                # 别改
    short_groups = 0                                                         # 别改
    for index, (ws, vs, cc) in enumerate(CASES_EX, 1):                       # 别改
        ex = knap01_exact(ws, vs, cc)                                        # 别改
        fwd = knap01_exact_rev(ws, vs, cc)                                   # 别改
        probe = probe_exact(ws, vs, cc)                                      # 别改
        # 「一致」的要求是**两边都给出了答案**：两个 None 不算一致
        if ex is not None and ((is_neg(ex) and is_neg(probe)) or ex == probe):   # 别改
            agree += 1                                                       # 别改
        if (not is_neg(fwd)) and is_neg(ex):                                 # 别改
            short_groups += 1                                                # 别改
        show_case(index, ws, vs, cc, ex, fwd, probe, brute01(ws, vs, cc))     # 别改
    show_pair('对拍 两版一致且都给出答案的组数 与 总组数', agree, len(CASES_EX))   # 别改
    show_pair('对拍 正序多算而逆序填不上的组数 与 总组数', short_groups, len(CASES_EX))   # 别改
    show_check('对拍 两版处处一致', agree == len(CASES_EX))                      # 别改

    # ── 7. 探针要用的那批数据的说明（别改）───────────────────────
    show_json('数据 探针', {'seed': EX_PROBE_SEED, 'trials': EX_PROBE_TRIALS,    # 别改
                            'limits': list(EX_PROBE_LIMITS)})                 # 别改
    show_four('收尾 无解的组数 有解的组数 一致的组数 总组数',                      # 别改
              sum(1 for ws, vs, cc in CASES_EX if is_neg(knap01_exact(ws, vs, cc))),   # 别改
              sum(1 for ws, vs, cc in CASES_EX if not is_neg(knap01_exact(ws, vs, cc))),   # 别改
              agree, len(CASES_EX))                                           # 别改
    show_note('说明 无解那一档怎么读', '凑不出来时打的是 ' + fmt(NEG))            # 别改
