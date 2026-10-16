"""tools.py · lab 0030 的公共工具（给好的，别改）

这一课的主题是**提交前自检**。四个任务各管一件自检工具，但它们必须互相咬得上，
所以有几样东西放在这里给好，别自己另写一份：

  1. show_banner / show_line
     打印统一走这里。判分**按标签找行**（不按行号），标签与值之间是一个空格。

  2. cand_buggy(a) / cand_fixed(a)
     本课那个候选解：Kadane，但 best 从 0 起步。cand_buggy 留着那个 bug
     （面对全负数据交回 0），cand_fixed 是同一份代码把 best 从 -inf 起步的修法。
     两个都要在任务 1 里用到：「故意改坏一处，看对拍器抓不抓得到」这一条。

  3. ref_same_idea(a)
     照候选解**同一个错思路**再写一遍的「参考解」——这是对拍器里的装饰品。
     它永远与 cand_buggy 一致，所以它一组 bug 都抓不到。这句话是课件量出来的，
     本课的判分也把「同思路参考解抓到 0 组」当成硬事实核对。

  4. ref_dc(a) / ref_brute(a)
     两个**真的独立**的参考解：
       · ref_dc：分治（左半、右半、跨中点），与 Kadane 的想法毫无关系；
       · ref_brute：枚举所有子段一个不漏，最笨也最不会错。
     两个都必须**原样交回那个最大的负数**，不许把答案截到 0 起步——
     截了就跟候选解一起错，对拍器立刻变成装饰品。

  5. 任务 1 与任务 2 共用的随机口径（都写死在这儿）
     T1_SEED = 1, T1_TRIALS = 500, n ∈ 1..8, 取值 -9..9
     T2_SEED = 2, T2_TRIALS = 300, n ∈ 1..8, 取值 -9..9
     两个任务的数字（500 组里 0 组 / 58 组，300 组里 0 组 / 33 组）
     在补全之后应该是**逐字一样**的。对不上就是生成器或对拍器写歪了。

  6. 任务 3 的三组数据与期望，任务 4 的 MOD
     任务 3：CASES = [[1, 2, 3], [10, 20], [5]]，期望 [6, 30, 5]。
     任务 4：MOD = 10 ** 9 + 7。取不取模在 n <= 30 上看不出来，n = 50 才分家。

  7. gen_positive(n, rng) / gen_any(n, rng) / draw_case(rng)
     只给任务 2 当**反面教材**用的两个生成器，加上任务 2 每组的「先抽 n」那一步。
     照题面造数据的那个生成器（任务 2 的 TODO 3）请自己写进任务文件里。
     draw_case 单独列出来，是因为「先抽 n、再抽数组」这个次序要是变了，
     同一个种子就会抽出完全不同的数据，20 组小表的数字也就跟着变了。

  8. fib_nomod(n) / fib_mod(n, mod) / fib_count_mod(n, mod)
     任务 4 要对比的两版斐波那契，外加一份「n 小的时候直接递推数一数」的计数版。

  9. values_equal(got, want) / near(got, want) / TABLE_WIDTH
     比较与打印。**JSON 往返会把 tuple 变成 list**，所以比之前一律先归一化：
     values_equal 拿 json.dumps 再比，[1, 2] 与 (1, 2) 视为相等。
     这一课不量耗时，TABLE_WIDTH 只管对齐。

判分**不 replace 这份文件里的任何东西来帮你过**：它做的是另算一遍——
自己另写一份 cand / ref_dc / ref_brute / fib，拿自己造的数据（刻意换一个种子）
算期望值，再跟你的函数交回的东西、以及你脚本打印的行对上。
所以只写 print、不写实现是过不去的。
"""

import json
import random


# ── 1. 打印 ──────────────────────────────────────────────────────────────

def show_banner(title):
    """打印一行小节标题，四个任务的脚本都用它开头。"""
    print('== ' + title + ' ==')


def show_line(label, value):
    """打印一行「标签 值」，判分按标签取。标签与值之间是一个空格。"""
    print(label + ' ' + str(value))


# ── 2. 候选解：那个「best 从 0 起步」的 bug ──────────────────────────────

def cand_buggy(a):
    """候选解：Kadane，但 best 从 0 起步。

    面对全是负数的数据，循环体里的 cur 会被 max(0, ...) 按回 0，
    best 也就一直是 0——于是交回 0，而正确答案是那个最大的负数。
    """
    best = cur = 0
    for x in a:
        cur = max(0, cur + x)
        best = max(best, cur)
    return best


def cand_fixed(a):
    """同一份代码，只把初值从头改起——修好之后的样子。

    改的是两个初值，不是只改 best：
      · best 从 -inf 起步，这样「一个正数都没有」时它不会被按回 0；
      · cur 也要从 0 改成 -inf，否则 cur = max(0, ...) 那一句照样把当前段的和
        按回 0——模型还是「子段可以空」，全负数据上仍然交回 0。
    空数组交回 None，与 ref_brute 同一个口径。
    """
    if not a:
        return None
    best = cur = a[0]
    for x in a[1:]:
        cur = x if cur < 0 else cur + x
        if cur > best:
            best = cur
    return best


# ── 3. 同一个思路的「参考解」：装饰品 ────────────────────────────────────

def ref_same_idea(a):
    """照着候选解同一个错思路再写一遍，只是行文不同。

    它和 cand_buggy 都犯了「答案截到 0 起步」这个错，所以两版永远一致：
    500 组数据一组都抓不到。这种「参考解」是对拍器里的装饰品。
    """
    cur = 0
    ans = 0
    for x in a:
        cur += x
        if cur < 0:
            cur = 0
        if cur > ans:
            ans = cur
    return ans


# ── 4. 两个真的独立的参考解 ──────────────────────────────────────────────

def ref_dc(a):
    """独立参考解之一：分治（左半 / 右半 / 跨中点），与 Kadane 毫无关系。

    跨中点那一段从中间往两边扫：左边只取后缀最大值、右边只取前缀最大值。
    空数组交回 None，与 ref_brute 同一个口径（最大子段至少要取一个元素）。
    """
    if not a:
        return None
    return _dc(a, 0, len(a) - 1)


def _dc(a, lo, hi):
    if lo == hi:
        return a[lo]
    mid = (lo + hi) // 2
    left = _dc(a, lo, mid)
    right = _dc(a, mid + 1, hi)
    cross = _cross(a, lo, mid, hi)
    return max(left, right, cross)


def _cross(a, lo, mid, hi):
    """跨中点的最大子段：左半的后缀最大 + 右半的前缀最大（两边都至少取一个）。"""
    best_left = float('-inf')
    s = 0
    for i in range(mid, lo - 1, -1):
        s += a[i]
        if s > best_left:
            best_left = s
    best_right = float('-inf')
    s = 0
    for i in range(mid + 1, hi + 1):
        s += a[i]
        if s > best_right:
            best_right = s
    return best_left + best_right


def ref_brute(a):
    """独立参考解之二：枚举所有子段，一个不漏。

    最笨的办法，但最不会错：它不假设任何东西，也不需要「子段和为负就丢掉」
    这种结论正确。空数组交回 None。
    """
    best = None
    for i in range(len(a)):
        s = 0
        for j in range(i, len(a)):
            s += a[j]
            if best is None or s > best:
                best = s
    return best


# ── 5. 任务 1 / 任务 2 共用的随机口径 ────────────────────────────────────

T1_SEED = 1
T1_TRIALS = 500
T1_N_HI = 8
T1_LO = -9
T1_HI = 9

T2_SEED = 2
T2_TRIALS = 300


def draw_case(rng, n_hi, lo, hi):
    """「先抽 n、再抽数组」——这个次序是随机口径的一部分，别改。"""
    n = rng.randint(1, n_hi)
    return [rng.randint(lo, hi) for _ in range(n)]


# ── 6. 任务 3 / 任务 4 的给好常量 ────────────────────────────────────────

CASES = [[1, 2, 3], [10, 20], [5]]
EXPECT = [6, 30, 5]

MOD = 10 ** 9 + 7

# 任务 4 打印表上那几档 n：小到看不出差别、到大到一眼看出，中间是分家的那一点。
T4_ROWS = (10, 30, 50, 100, 1000, 10000)
T4_TAIL = 14
T4_BIG = 10000

# 两版斐波那契第一个分家的 n：第 45 个数 1134903170 第一次超过 10 ** 9 + 7。
# 这个数是**算出来的**，不是背下来的：45 点开头的表里 n = 30 还相等、n = 50 已经不同，
# 中间那一点就是 45。任务 4 的判分也拿它当硬事实核对。
T4_FIRST_N = 45
T4_FIRST_NOMOD = 1134903170
T4_FIRST_MOD = 134903163


# ── 7. 任务 2 的两个反面教材生成器 ──────────────────────────────────────

def gen_positive(n, rng):
    """造「至少有一个正数」的数据——很多人的生成器就是这样写的。

    这一句 max(a) > 0 看着无害，其实把整类「全负」数据挡在门外了，
    而本课那个 bug 恰好只在全负数据上出现。
    """
    while True:
        a = [rng.randint(-9, 9) for _ in range(n)]
        if max(a) > 0:
            return a


def gen_any(n, rng):
    """照题面造：题面允许负数，就允许全负、允许全零。"""
    return [rng.randint(-9, 9) for _ in range(n)]


# ── 8. 任务 4 的两版斐波那契 ────────────────────────────────────────────

def fib_nomod(n):
    """不取模：Python 的整数不会溢出，所以它交回的是一个**巨大的正确值**。"""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fib_mod(n, mod=MOD):
    """中途取模：每一步 (a + b) % mod。"""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, (a + b) % mod
    return a


def fib_count(n, mod=MOD, limit=20000):
    """不取模那一版在 n 处的**十进制位数**：就是 len(str(第 n 个斐波那契数))。

    n = 10000 时是 2090 位（1000 是 209 位，十倍 n 大约多 209 位）——
    这个数只能从**不取模**那一版拿到：取模之后的值永远是 10 位以内，
    「差了 2080 位」这件事在小数据上完全看不出来。
    n 超过 limit 时交回 None（本站用不到那么远）。
    """
    if n > limit:
        return None
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return len(str(a))


# ── 9. 比较与打印 ────────────────────────────────────────────────────────

TABLE_WIDTH = 14


def values_equal(got, want):
    """归一化之后比。JSON 往返会把 tuple 变成 list，所以先把两边都丢给 json.dumps。"""
    if isinstance(got, (list, tuple)) and isinstance(want, (list, tuple)):
        try:
            return json.dumps(list(got)) == json.dumps(list(want))
        except (TypeError, ValueError):
            return list(got) == list(want)
    return got == want


def near(got, want, ratio=0.75):
    """耗时之类的可比量：只用它比较，且两侧都要有噪声容差。

    ratio 那一档是给「本来就慢」的实现留的余量；返回 True 的三种情形是
    「没超」「跟期望差不多」和「期望本来就不慢」。本课真正的判据全是确定值，
    这个函数留给想自己加一条计时对照的同学。
    """
    got = to_number(got)
    want = to_number(want)
    if got is None or want is None:
        return False
    if want <= 0:
        return True
    return got <= want / ratio


def to_number(value):
    """把 '12'、12、12.0、None 一律化成 float（化不动就 None）。"""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None
