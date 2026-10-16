"""对拍器 · lab 0015（实验二）

这一课要交的是一份对拍脚本：随机造数据、自动比对参照解与候选解、抓到反例、再把反例缩到最小。

四个部件（缺一件都跑不起来）：

    参照解     慢但一定对，当「标准答案」        brute_find
    候选解     要验的那一版，快但可能有错        buggy.py 里的 cand_find（给好的，别改）
    数据生成器 每次造一组新输入                  gen_wide 与 gen_boundary
    比对循环   跑两边、比结果、不一致就报告      stress

再配一个 shrink：抓到的那组数据往往比必要的更大，反复试着删掉一个元素，
只要两边还不一致就接受更小的那一版。

五个任务（课件「上手做」那一节就是这五步）：

    TODO 1  brute_find(a, x)                                    线性扫一遍
    TODO 2  gen_wide() / gen_boundary()                         两个造数据器
    TODO 3  stress(candidate, reference, gen, trials, seed)     比对循环
    TODO 4  shrink(candidate, reference, a, x)                  反例最小化
    TODO 5  对着 buggy.py 跑一遍，把结果写进 findings.md

接口（函数名、参数顺序、返回值的形状）都是判分接口，别改；函数体里怎么写随你。
下面最底下那段 `__main__` 是给好的，它会跑完五个任务、把 findings.md 要写的内容打印出来，别改它。

跑： py stress.py
判： py run_tests.py
"""

from tools import as_lists, labels, load_buggy, match_found, show_count, show_pairs

TRIALS = 2000                                  # 别改：任务 3、5 的对拍轮次
SEED = 20261115                                # 别改：任务 3 用的那个种子


# ══ TODO 1 ═════════════════════════════════════════════════
# 写参照解 brute_find(a, x)：在 a 里从头到尾线性扫一遍，
#   找到 x 交回它的下标（第一个等于 x 的那一格，从 0 起）；
#   扫完没找到交回 -1。
#
# 要点：
#   · 只用一个 for 循环加一个 if，不要写二分——参照解的价值不在快，在于**一眼看得出对不对**；
#   · 判空不用特判：a 是空表时 range(len(a)) 一次都不跑，直接落到 return -1；
#   · 下标从 0 起，是第一处匹配的位置。
#
# 写完先拿三组手算的小数据验一遍（空数组、一个元素、两个元素）：
#     brute_find([], 3) → -1      brute_find([5], 5) → 0      brute_find([63, 97], 97) → 1
def brute_find(a, x):
    return None


# ══ TODO 2 ═════════════════════════════════════════════════
# 写两个造数据器，都交回 (a, x) 两样东西。
#
# gen_wide()：宽范围随机的数据。
#   · a 必须**升序**——候选解是二分，无序的数据会让它给出没意义的答案，对拍报出来的东西也就没意义；
#   · 造法提示：先用 random.sample(range(100), n) 取 n 个互不相同的数、再 sorted 包一层，
#     其中 n = random.randint(1, 8)；x 用 random.randrange(100) 取（注意：x 常常不在 a 里）。
#
# gen_boundary()：专门造**边界形态**，四种各占一部分，别只写其中一种。
#   · 空数组；
#   · 单元素数组，而且 x 就取那个元素（这一支是把「数组只有一个元素」与「x 就在数组里」
#     两个条件绑在一起造出来——随机的 x 要恰好撞上单元素数组，概率太低）；
#   · 全相同：一个 0 到 4 之间的值重复 2 到 6 次，x 取那个值；
#   · 答案恰好在两端：取 2 到 6 个互不相同的数、sorted 之后，x 取 a[0] 或 a[-1]。
#   用 random.randrange(4) 选一支，四种形态在长跑里就都会出现。
#
# 为什么不能只写 gen_wide：这一课的 bug 只在「x 真的在数组里」而且「答案恰好是最后
# 剩下的那一格」时才露出来。gen_wide 的 x 大多不在数组里，两边都交回 -1，跑一万次也抓不到。
def gen_wide():
    return None


def gen_boundary():
    return None


# ══ TODO 3 ═════════════════════════════════════════════════
# 写比对循环 stress(candidate, reference, gen, trials, seed=None)：
#
#   · seed 不是 None 时，先 random.seed(seed)——**在循环外面设一次**；
#     设在循环里的话每次造数据都用同一个种子，两千次比的是同一组数据；
#   · 循环 trials 次（第几次从 1 开始数）；
#   · 每次 a, x = gen()，再拿 tools.as_lists(candidate, reference, a, x) 跑两边，
#     它交回 (候选的答案, 参照的答案) 两个数（两种「没找到」的写法已经归成 -1 了）；
#   · 两个数不一样 → 立刻交回 (第几次, a, x, 候选答案, 参照答案)；
#   · trials 次全一样 → 交回 None。
#
# 这个返回值是有意设计成这样的：只回一句「有问题」没用，必须把**那组数据**一起交回来，
# 别人（包括几小时之后的你）才能照着它复现。
#
# 写完先自己跑一次「同一个函数同时当候选与参照」：
#     stress(brute_find, brute_find, gen_boundary, 2000, seed=SEED)
# 必须是 None——同一个函数跟自己比，永远不该比出不一致。
# 判分第 2 层查的就是这一条：它专门抓「stress 根本没在比对」（漏了比那一行、
# 或者拿 gen() 的结果跟自己对上就交回）。
def stress(candidate, reference, gen, trials, seed=None):
    return None


# ══ TODO 4 ═════════════════════════════════════════════════
# 写反例最小化 shrink(candidate, reference, a, x)：
#
#   · 从 cur = list(a) 开始（复制一份，别去改调用处那张表）；
#   · 反复试：把 cur 里第 i 个元素删掉得到 smaller = cur[:i] + cur[i + 1:]，
#     拿 as_lists 跑一遍两边——**只要两边还不一致**，就 cur = smaller 并从头再试；
#   · 一轮下来一个元素都删不掉了，就交回 cur（一张表）。
#
# 关键：接受更小的版本之前，必须**再比一次**。少了这一次，shrink 会把反例删到两边一致，
# 那样得到的「最小反例」根本复现不了原来的错。
#
# 交回的是**数组**（不是 (a, x) 两个）：x 从头到尾不变——最小化的是数据，不是答案。
def shrink(candidate, reference, a, x):
    return None


if __name__ == '__main__':                     # 别改：下面这一段跑完五个任务、打印要抄进 findings.md 的东西
    import random

    from buggy import cand_find

    print('对拍器 0015 · 候选解 buggy.cand_find，参照解 brute_find')
    print()

    # ── 第 1 步 · 参照解单独验：三组手算的小数据 ──────────────────
    print('第 1 步 · 参照解的三组手算数据')
    for arr, target, want in [([], 3, -1), ([5], 5, 0), ([63, 97], 97, 1)]:
        got = match_found(brute_find(arr, target), arr)
        print('  参照解 ' + 'a=' + repr(arr) + ' x=' + repr(target)
              + ' → ' + repr(got) + '（期望 ' + repr(want) + '）')
    print()

    # ── 第 2 步 · 两个造数据器长什么样 ────────────────────────────
    print('第 2 步 · 造数据器各来三组看一眼')
    random.seed(SEED)
    for name, maker in (('gen_wide', gen_wide), ('gen_boundary', gen_boundary)):
        rows = []
        for _ in range(3):
            made = maker()
            rows.append(made)
        print('  ' + name + ' ' + repr(rows))
    print()

    # ── 第 3 步 · 同一个函数当两边，2000 次必须一次都抓不到 ────────
    print('第 3 步 · 同一个函数当候选与参照（这一条必须是 None）')
    same = stress(brute_find, brute_find, gen_boundary, TRIALS, seed=SEED)
    print('  ' + labels(same)[0])
    print()

    # ── 第 4 步 · 对拍 buggy.py ───────────────────────────────────
    print('第 4 步 · 对拍 buggy.py')
    hit = stress(cand_find, brute_find, gen_boundary, TRIALS, seed=SEED)
    for line in labels(hit):
        print('  ' + line)
    show_count(1, '种子 ' + str(SEED) + ' 抓到', None if hit is None else hit[0])
    again = stress(cand_find, brute_find, gen_boundary, TRIALS, seed=SEED)
    show_count(2, '同一种子再跑一次 抓到', None if again is None else again[0])

    raw_a, raw_x = [None], None
    if hit is not None:
        _, raw_a, raw_x, _, _ = hit
    print()

    # ── 第 5 步 · 反例最小化 ─────────────────────────────────────
    print('第 5 步 · 反例最小化')
    small_a = shrink(cand_find, brute_find, raw_a, raw_x)
    raw_got, raw_want = as_lists(cand_find, brute_find, raw_a, raw_x)
    got, want = as_lists(cand_find, brute_find, small_a, raw_x)
    print('  原始反例: ' + repr(raw_a) + ' x = ' + repr(raw_x) + '  候选 ' + repr(raw_got)
          + '  参照 ' + repr(raw_want))
    print('  最小化后: ' + repr(small_a) + ' x = ' + repr(raw_x) + '  候选 ' + repr(got)
          + '  参照 ' + repr(want))
    show_count(3, '最小反例长度', None if small_a is None else len(small_a))
    print()

    # ── findings.md 要写的东西 ────────────────────────────────────
    source = load_buggy()
    culprit = None
    for number in range(1, len(source) + 1):
        if source[number - 1].strip().startswith('while lo < hi:'):
            culprit = number
            break
    print('findings.md 这样写（三样东西，缺一样第 4 层就不过）：')
    print('  原始反例: a = ' + repr(raw_a) + ', x = ' + repr(raw_x))
    print('  最小反例: a = ' + repr(small_a) + ', x = ' + repr(raw_x))
    print('  出错的行: buggy.py 第 ' + str(culprit) + ' 行  '
          + repr('' if culprit is None else source[culprit - 1].strip()))
    print()
    print('（还有一个形态问题：这一组反例是 空数组 / 单元素 / 全相同 / 答案在两端 里的哪一种？'
          + '想清楚了写进 findings.md 末尾那句话。）')
