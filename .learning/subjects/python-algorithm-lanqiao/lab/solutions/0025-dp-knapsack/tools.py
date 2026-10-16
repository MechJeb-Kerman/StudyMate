"""tools.py · lab 0025 的公共工具（给好的，别改）

这里放五样东西，四个任务都从这里取：

  1. 造数据
     rng(seed)                            固定种子的随机数发生器
     make_cases(seed, trials, n_hi, w_hi, v_hi, c_hi)
                                          一批「重量/价值/容量」的测试数据，
                                          每项是 (ws, vs, C) 三个一组的元组
     make_groups(seed, trials, ...)       分组背包的测试数据：
                                          每组是 [(重量, 价值), ...] 的一张表
     DEPTH                                对拍用的规模（n ≤ 8，2^8 = 256 个子集，
                                          枚举得完）——小到能枚举是对拍的前提

  2. 参照实现（判分与对拍用的「标准答案」，不是你要写的那几段）
     brute01(w, v, C)                     枚举所有子集——0/1 背包的裁判
     brute_complete(w, v, C)              逐容量递推——完全背包的裁判
     brute_group(groups, C)               枚举每组「不选 / 选第几件」——分组背包的裁判
     knap01_1d_rev(w, v, C)               0/1 背包一维逆序（正确版，第一课就给过）
     这四个**只用来看对拍结果对不对**，任务里要写的函数一个都不许调它们
     （调了就成「拿自己验自己」了）。

  3. 负无穷与它的打印
     NEG                                   float('-inf')
     is_neg(x)                             这个值是不是负无穷（-inf 与 '无解' 都算）
     fmt(x)                                打印用：-inf 写成 '无解'，其余写数字本身

  4. 打印：格式就是判分接口（编号与标签都别改）
     show_json(label, obj)                 <label> <一行 JSON>（判分自己造的数据从这里读）
     show_pair(label, a, b)                <label> <a> <b>
     show_four(label, a, b, c, d)          <label> <a> <b> <c> <d>
     show_check(label, ok, note='')        <label> True / <label> False <备注>
     show_same(label, a, b)                <label> True或False <b>（两版答案一致吗 + 另一个值）
     show_note(label, note)                <label> <备注>
     show_case(index, ws, vs, C, *values)  <index> 重量 <ws> 价值 <vs> 容量 <C> 结果 <v1> <v2>…

  5. 计时
     timed(func, *args)                   跑一次并量耗时 → (函数交回的值, 秒数)

两个约定记牢：

  * **判分读的是你脚本自己 print 出来的那些行**（第 4 节那几个函数），
    所以带 print 的行、编号、标签都别改；
  * **判分只判趋势不核绝对值**：秒数换台机器就变，别背；而每一组数据的答案
    （价值、偏大的数额、-inf 的格、对拍的组数）都是**确定值**，那些是精确判的。
"""

import json
import random
import time

# ── 一、造数据 ──────────────────────────────────────────────────────────

# 对拍用的规模上限：n ≤ 8，枚举得完（2^8 = 256 个子集）。
# 对拍三要点里的第一条就是「数据要小，小到能枚举」。
DEPTH = 8


def rng(seed):
    """固定种子的随机数发生器：同一个 seed 永远给出同一批数据。

    判分拿同一个 seed 自己复现一份，所以答案必须对得上——
    「我这边是这样造的」不算理由。
    """
    return random.Random(seed)


def make_cases(seed, trials, n_hi, w_hi, v_hi, c_hi):
    """造一批 0/1 与完全背包的测试数据 → [(ws, vs, C), …]，一共 trials 组。

    每一组里：件数 n 在 1..n_hi 之间、每件重量 1..w_hi、每件价值 1..v_hi、
    容量 1..c_hi。**取数的次序**（先件数、再逐件重量、再逐件价值、最后容量）
    与判分那一份逐字相同——次序换了数据就不是同一批了。
    """
    r = rng(seed)
    out = []
    for _ in range(trials):
        n = r.randint(1, n_hi)
        ws = [r.randint(1, w_hi) for _ in range(n)]
        vs = [r.randint(1, v_hi) for _ in range(n)]
        cc = r.randint(1, c_hi)
        out.append((ws, vs, cc))
    return out


def make_groups(seed, trials, g_hi, per_hi, w_hi, v_hi, c_hi):
    """造一批分组背包的数据 → [[(重量, 价值), …], …]，一共 trials 组。

    每组里有 1..g_hi 个小组、每组里 1..per_hi 件物品；
    重量 1..w_hi、价值 1..v_hi；容量 1..c_hi。
    取数次序与 make_cases 一样是「先数、再逐件取」，判分那一份完全相同。
    """
    r = rng(seed)
    out = []
    for _ in range(trials):
        g = r.randint(1, g_hi)
        groups = []
        for _ in range(g):
            k = r.randint(1, per_hi)
            groups.append([(r.randint(1, w_hi), r.randint(1, v_hi)) for _ in range(k)])
        out.append((groups, r.randint(1, c_hi)))
    return out


# ── 二、参照实现（判分用的标准答案；任务里要写的函数别调它们）──────────


def brute01(w, v, C):
    """枚举所有子集——0/1 背包的标准答案，物品少的时候才能用。

    它对每一件物品都只有「拿」与「不拿」两种可能，所以一定不会重复拿。
    """
    best = 0
    n = len(w)
    for mask in range(1 << n):
        tw = tv = 0
        for i in range(n):
            if mask >> i & 1:
                tw += w[i]
                tv += v[i]
        if tw <= C and tv > best:
            best = tv
    return best


def knap01_1d_rev(w, v, C):
    """0/1 背包 · 一维滚动数组 · 内层逆序（正确版）。

    与课件第 25 课那一版逐字相同：对拍时拿它当「逆序那一支」的参照。
    任务 1 要写的是你自己那一版，不是调这一个。
    """
    dp = [0] * (C + 1)
    for i in range(len(w)):
        for c in range(C, w[i] - 1, -1):
            dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[C]


def brute_complete(w, v, C):
    """完全背包的参照实现：按容量从小到大推。

    算 dp[c] 时把所有物品都试一遍，所以「同一件拿多次」是天然允许的。
    """
    dp = [0] * (C + 1)
    for c in range(1, C + 1):
        for i in range(len(w)):
            if w[i] <= c:
                dp[c] = max(dp[c], dp[c - w[i]] + v[i])
    return dp[c]


def brute_group(groups, C):
    """分组背包的参照实现：枚举每组「不选 / 选第 1 件 / 选第 2 件……」

    一组里最多选一件这件事，靠「枚举时每组只挑一个下标」直接表达出来。
    """
    best = 0
    picks = [range(-1, len(g)) for g in groups]
    for pick in _product(picks):
        tw = tv = 0
        for i, j in enumerate(pick):
            if j >= 0:
                tw += groups[i][j][0]
                tv += groups[i][j][1]
        if tw <= C and tv > best:
            best = tv
    return best


def _product(pools):
    """itertools.product 的等价物（本文件自己带着，省得任务里再 import）。"""
    out = [[]]
    for pool in pools:
        out = [acc + [x] for acc in out for x in pool]
    return out


# ── 三、负无穷与它的打印 ────────────────────────────────────────────────

# 「恰好装满」里表示「这个容量凑不出来」的那个值：
# -inf + v 还是 -inf，比 -inf 不大，所以那一格永远填不上。
NEG = float('-inf')


def is_neg(x):
    """这个值是不是「无解」那一档：-inf、None、字符串 '无解' 都算。

    判分读的是打印出来的文本，所以留白版的 None 与参考解的 -inf
    在判分眼里是同一档（都表示那一段还没写出能用的答案）。
    """
    if x is None:
        return True
    if isinstance(x, str):
        return x.strip() in ('无解', '-inf', 'None')
    if isinstance(x, float):
        return x == NEG
    return False


def fmt(x):
    """打印用：负无穷写 '无解'，其余写数字本身（-0.0 之类不出现）。"""
    if is_neg(x):
        return '无解'
    return str(x)


# ── 四、打印：格式就是判分接口（别改）──────────────────────────────────


def show_json(label, obj):
    """打印 <label> <一行 JSON>。

    判分**自己造的那批数据**从这里读：任务脚本把它打印出来，
    判分才好在同一批数据上重算期望值。一行一个 JSON，别换行、别加别的。
    """
    print(str(label) + ' ' + json.dumps(obj, ensure_ascii=False))


def show_pair(label, a, b):
    """打印 <label> <a> <b>。"""
    print(str(label) + ' ' + str(a) + ' ' + str(b))


def show_four(label, a, b, c, d):
    """打印 <label> <a> <b> <c> <d>。"""
    print(str(label) + ' ' + str(a) + ' ' + str(b) + ' ' + str(c) + ' ' + str(d))


def show_check(label, ok, note=''):
    """打印一行判定：<label> True 或 <label> False <备注>。"""
    tail = '' if note == '' else ' ' + str(note)
    print(str(label) + ' ' + str(bool(ok)) + tail)


def show_same(label, a, b):
    """打印「一致吗」以及另一个值：<label> True/False <b>。

    两个值都是 -inf（或都是「无解」）时算一致——「凑不出来」与「凑不出来」
    是同一个答案，判分也这么算。
    """
    if is_neg(a) and is_neg(b):
        same = True
    else:
        same = (a == b)
    print(str(label) + ' ' + str(same) + ' ' + fmt(b))


def show_note(label, note):
    """打印 <label> <备注>（备注那一列）。"""
    print(str(label) + ' ' + str(note))


def show_case(index, ws, vs, C, *values):
    """打印一行用例结果：

        <index> 重量 <ws> 价值 <vs> 容量 <C> 结果 <v1> <v2> …

    ws / vs 用列表原样打印（判分拿 ast.literal_eval 读回来）；
    values 是这一组数据上各个写法的答案，按任务文件里写好的次序列出。
    """
    body = ' '.join(fmt(x) for x in values)
    print(str(index) + ' 重量 ' + str(list(ws)) + ' 价值 ' + str(list(vs))
          + ' 容量 ' + str(C) + ' 结果 ' + body)


def show_groups(index, groups, C, *values):
    """分组背包那一行用例结果：

        <index> 组 <组表> 容量 <C> 结果 <v1> <v2> …

    groups 原样打印成一行（判分拿 ast.literal_eval 读回来），
    组内是 (重量, 价值) 的元组——读回来是元组还是列表都不影响比较。
    """
    body = ' '.join(fmt(x) for x in values)
    print(str(index) + ' 组 ' + str([list(g) for g in groups])
          + ' 容量 ' + str(C) + ' 结果 ' + body)


# ── 五、计时 ────────────────────────────────────────────────────────────


def timed(func, *args):
    """跑一次并量耗时 → (函数交回的值, 秒数)。

    计时口径与第 3 课一致：前后各取一次 perf_counter、相减，中间不夹别的代码。
    """
    start = time.perf_counter()
    value = func(*args)
    end = time.perf_counter()
    return value, end - start
