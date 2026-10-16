"""任务 2 · 内层循环的方向：0/1 背包写成正序会偏大

这一课要写三段：

  TODO 1  knap01_1d_fwd(w, v, C)   0/1 背包 · 一维 · 内层**正序**（错：同一件物品会被重复选）
  TODO 2  knap_complete(w, v, C)   完全背包 · 一维 · 内层正序（对：每件物品可以拿任意多件）
  TODO 3  first_wrong(w, v, C)     在**其中一个容量**上，正序与枚举对不上时交回
                                   (容量, 枚举给的正确答案, 正序给的错答案)；对得上就交回 None

TODO 1 与 TODO 2 的循环体**逐字相同**，只差函数名与注释：

    for i in range(len(w)):
        for c in range(w[i], C + 1):        # 正序
            dp[c] = max(dp[c], dp[c - w[i]] + v[i])

同一段代码在 0/1 背包里是错的、在完全背包里是对的，这就是这一课的核心。

为什么正序在 0/1 背包里会错：算 `dp[c]` 用到的 `dp[c - w[i]]` **在本轮已经被更新过了**
——那一格已经是「前 i 件」的结果，可能已经拿过第 i 件。于是同一件物品被拿了第二次、第三次。
逆序就没有这个问题：算 `dp[c]` 时 `dp[c - w[i]]` 的下标更小，**逆序还没走到那儿**。

错得很有规律：答案**总是偏大**，而且**恰好等于完全背包**。
背包问题里「偏大」就是铁证——一个偏大的答案意味着某种你其实没有的资源被用掉了
（这里是同一件物品被拿了多次）。这一份会把两件事都打成数字给你看。

参考解（solutions/）：三段 TODO 都填好了，可以直接跑 `py run_tests.py` 对照。

接口：文件名、函数名、上面那些给好的数据、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那三段。

跑： py task2_direction.py
判： py run_tests.py
"""

from tools import (brute01, is_neg, knap01_1d_rev, make_cases, rng, show_case,
                   show_check, show_json, show_note, show_pair)

# ── 给好的数据（别改）──────────────────────────────────────────────

# 课件「内层循环的方向」那一节那个例子
DIR_W = [2, 3, 4, 5]
DIR_V = [3, 4, 5, 6]
DIR_CAPS = (6, 8, 10, 12)

# 对拍那一批：固定种子 5 造 400 组（n ≤ 8、重量 ≤ 9、价值 ≤ 20、容量 ≤ 20）。
# 种子与取数次序都是判分接口：判分拿同一个种子自己复现这 400 组，
# 再拿自己那份参照实现重算「多少组对不上」「是不是每一组都偏大」。
CASES_DIR = make_cases(5, 400, 8, 9, 20, 20)

# 「揪出一组」用更长的一串数据：从第 1 组开始往后找，找到第一组就打印它。
# 判分自己也会拿同样的种子复现这一串，确认你交回的就是**第一组**。
# 种子同样取 5——课件那一段用的就是这个种子，出来的第一组是
# 重量 [6, 9, 1, 8, 4]、价值 [2, 6, 4, 12, 16]、容量 8（逆序 20、正序 32、枚举 20）。
RNG_SEED = 5
RNG_TRIALS = 4000
RNG_N_HI = 8
RNG_W_HI = 9
RNG_V_HI = 20
RNG_C_HI = 20

# 「偏大」那一列用的物品（固定四个）与一批容量：
# 同一批物品只换容量，看偏大的量随容量怎么变。
PICK_W = [3, 5, 2, 8]
PICK_V = [7, 11, 4, 15]
PICK_CAPS = (3, 5, 8, 11, 14, 20, 33, 50)


# ══ TODO 1 ═════════════════════════════════════════════════════
# 补 knap01_1d_fwd(w, v, C)：把一维版的内层循环方向改成正序，其他一个字都不动。
#   dp = [0] * (C + 1)；
#   外层 for i in range(len(w))，内层 for c in range(w[i], C + 1)：
#       dp[c] = max(dp[c], dp[c - w[i]] + v[i])
#   最后 return dp[C]。
#   这一版是**故意写错的**（它是这一课要看的对象，不是要改的错）：
#   它会给出偏大的答案。别在这里补判重、也别加「每件只能用一次」的判断——
#   要看的就是「方向改了、答案偏大」这个现象本身。
def knap01_1d_fwd(w, v, C):
    dp = [0] * (C + 1)
    for i in range(len(w)):
        for c in range(w[i], C + 1):                # 正序：dp[c-w[i]] 本轮已更新过
            dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]


# ══ TODO 2 ═════════════════════════════════════════════════════
# 补 knap_complete(w, v, C)：完全背包允许每件物品拿任意多件，所以正序就是对的。
#   函数体与 TODO 1 **逐字相同**（dp = [0] * (C + 1)、外层物品、内层容量正序、
#   同一行 dp[c] = max(dp[c], dp[c - w[i]] + v[i])、最后 return dp[C]）。
#   两段代码一样、问题不一样，所以同一个写法一个是错的、一个是对的。
def knap_complete(w, v, C):
    dp = [0] * (C + 1)
    for i in range(len(w)):
        for c in range(w[i], C + 1):                # 正序读到的就是「已经可以再拿一次」
            dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]


# ══ TODO 3 ═════════════════════════════════════════════════════
# 补 first_wrong(w, v, C)：在**容量 C 这一个容量上**，正序与「枚举出来的正确答案」
# 对不上时，交回 (C, 枚举的答案, 正序的答案)；对得上就交回 None。
#   fwd = knap01_1d_fwd(w, v, C)
#   want = brute01(w, v, C)
#   if fwd != want: return (C, want, fwd)
#   return None
#   三件事按这个次序：**先算正序版、再算枚举、再比**。
#   它是「偏大」那一列用的：同一批物品换个容量再问一次，
#   就能看见它在哪些容量上错、错多少——错得有没有规律，靠这一列判断。
def first_wrong(w, v, C):
    fwd = knap01_1d_fwd(w, v, C)                    # 先算正序那一版
    want = brute01(w, v, C)                         # 再算枚举（裁判）
    if fwd != want:                                 # 再比：不同就把两个答案都交回
        return (C, want, fwd)
    return None


if __name__ == '__main__':                       # 别改：这层守卫让判分 import 它时不出声
    # ── 1. 每个容量四行：逆序 / 正序 / 枚举 / 完全背包（别改）────────
    for cap in DIR_CAPS:                                                     # 别改
        rev = knap01_1d_rev(DIR_W, DIR_V, cap)                               # 别改
        fwd = knap01_1d_fwd(DIR_W, DIR_V, cap)                               # 别改
        comp = knap_complete(DIR_W, DIR_V, cap)                              # 别改
        want = brute01(DIR_W, DIR_V, cap)                                    # 别改
        show_case('方向 容量 ' + str(cap), DIR_W, DIR_V, cap, rev, fwd, want, comp)   # 别改
        show_check('方向 容量 ' + str(cap) + ' 正序等于完全背包', fwd == comp)   # 别改
        show_check('方向 容量 ' + str(cap) + ' 正序比正确答案大',                   # 别改
                   (not is_neg(fwd)) and (not is_neg(want)) and fwd > want)     # 别改
    show_note('说明 这一段比的是三支', '逆序（对）、正序（错）、枚举（裁判）')        # 别改

    # ── 2. 对拍那一批：400 组（别改）────────────────────────────
    show_json('数据 方向对拍', {'seed': 5, 'trials': 400,                       # 别改
                                'limits': [8, 9, 20, 20], 'cases': CASES_DIR})  # 别改
    bad_fwd = 0                                                              # 别改
    bad_rev = 0                                                              # 别改
    always_bigger = True                                                     # 别改
    always_equal_complete = True                                             # 别改
    for ws, vs, cc in CASES_DIR:                                             # 别改
        want = brute01(ws, vs, cc)                                           # 别改
        fwd = knap01_1d_fwd(ws, vs, cc)                                      # 别改
        if knap01_1d_rev(ws, vs, cc) != want:                                # 别改
            bad_rev += 1                                                     # 别改
        if fwd != want:                                                      # 别改
            bad_fwd += 1                                                     # 别改
            if not (fwd is not None and fwd > want):                         # 别改
                always_bigger = False                                        # 别改
            if fwd != knap_complete(ws, vs, cc):                             # 别改
                always_equal_complete = False                                # 别改
    show_pair('对拍 逆序与枚举不一致的组数 与 总组数', bad_rev, len(CASES_DIR))    # 别改
    show_pair('对拍 正序与枚举不一致的组数 与 总组数', bad_fwd, len(CASES_DIR))    # 别改
    show_check('对拍 不一致的那些组里正序总是偏大', always_bigger)                # 别改
    show_check('对拍 不一致的那些组里正序都等于完全背包', always_equal_complete)   # 别改

    # ── 3. 揪出一组（别改）────────────────────────────────────
    # 取数次序与 tools.make_cases 逐字相同（先件数、再逐件重量、再逐件价值、最后容量）：
    # 判分按同一个种子从第 1 组开始往后找，找到的第一组就是这个次序下的那一组。
    # 少取一次、多取一次、或者把容量提前，找到的就是另一组了。
    r = rng(RNG_SEED)                                                        # 别改
    found = None                                                             # 别改
    for _ in range(RNG_TRIALS):                                              # 别改
        n = r.randint(1, RNG_N_HI)                                           # 别改
        ws = [r.randint(1, RNG_W_HI) for _ in range(n)]                      # 别改
        vs = [r.randint(1, RNG_V_HI) for _ in range(n)]                      # 别改
        cc = r.randint(1, RNG_C_HI)                                          # 别改
        if knap01_1d_fwd(ws, vs, cc) != brute01(ws, vs, cc):                  # 别改
            found = (ws, vs, cc)                                             # 别改
            break                                                            # 别改
    show_json('数据 揪出一组', {'seed': RNG_SEED, 'trials': RNG_TRIALS,          # 别改
                                'n_hi': RNG_N_HI, 'limits': [RNG_W_HI, RNG_V_HI,  # 别改
                                                             RNG_C_HI]})      # 别改
    if found is None:                                                        # 别改
        show_note('揪出一组', '没找到（正序那一版还没写出能用的答案）')             # 别改
    else:                                                                    # 别改
        ws, vs, cc = found                                                   # 别改
        show_case('揪出', ws, vs, cc, knap01_1d_fwd(ws, vs, cc),              # 别改
                  brute01(ws, vs, cc), knap_complete(ws, vs, cc))             # 别改

    # ── 4. 八个容量上的偏大情况（别改）───────────────────────────
    bigger_count = 0                                                         # 别改
    for cap in PICK_CAPS:                                                    # 别改
        res = first_wrong(PICK_W, PICK_V, cap)                               # 别改
        want = brute01(PICK_W, PICK_V, cap)                                  # 别改
        fwd = knap01_1d_fwd(PICK_W, PICK_V, cap)                             # 别改
        comp = knap_complete(PICK_W, PICK_V, cap)                            # 别改
        if fwd is not None and fwd > want:                                   # 别改
            bigger_count += 1                                                # 别改
        # 说明词按「正序比正确答案大/小/一样」来打：偏大就写「偏大」，
        # 一样就写「对得上」。不能只看 first_wrong 交回没交回——
        # 它交回非 None 只说明「对不上」，而这里要写的是**往哪边不对**。
        if fwd is None:                                                      # 别改
            note_cmp = '没答案'                                               # 别改
        elif fwd > want:                                                     # 别改
            note_cmp = '偏大'                                                 # 别改
        elif fwd < want:                                                     # 别改
            note_cmp = '偏小'                                                 # 别改
        else:                                                                # 别改
            note_cmp = '对得上'                                               # 别改
        show_case('偏大 容量 ' + str(cap), PICK_W, PICK_V, cap, want, fwd, comp,   # 别改
                  note_cmp)                                                  # 别改
        # 同一批物品、只换容量：正序的答案是不是**处处都不小于**枚举出来的正确答案？
        # 「对不上」时它一定偏大——偏大就是铁证（用掉了你其实没有的资源）。
        show_check('偏大 容量 ' + str(cap) + ' 正序不小于正确答案',                # 别改
                   fwd is not None and fwd >= want)                          # 别改
        show_check('偏大 容量 ' + str(cap) + ' 对不上就是偏大',                    # 别改
                   (res is not None) == (fwd != want))                       # 别改
    show_note('偏大 偏大的容量个数', bigger_count)                               # 别改
    show_json('数据 偏大', {'caps': list(PICK_CAPS), 'w': PICK_W, 'v': PICK_V})    # 别改
    show_note('说明 偏大那一列', '只看「偏大 / 对得上」这一列与那个个数')
