"""参考解 · 对拍器 lab 0015（实验二）

拷进任务目录覆盖同名文件即可直接跑（`tools.py`、`buggy.py`、`run_tests.py` 这里各有一份）：
把这一份 `stress.py` 与 `findings.md` 拷过去之后，`py run_tests.py` 应当四层全过、退出码 0。

五个 TODO 的参考写法各自的关键一行：

    TODO 1  brute_find    for i in range(len(a)): if a[i] == x: return i  → 最后 return -1
    TODO 2  gen_wide      n = random.randint(1, 8)；a = sorted(random.sample(range(100), n))；x 宽范围随机
            gen_boundary  random.randrange(4) 选一支：空数组 / 单元素且 x 就是它 /
                          全相同 / 答案在两端。**x 与形态绑在一起造**，不等随机去撞。
    TODO 3  stress        random.seed(seed) 在循环外设一次；每轮 as_lists 跑两边；
                          两个答案不一样就交回 (第几次, a, x, 候选, 参照)；全一样交回 None
    TODO 4  shrink        反复试删一个元素，**只有删完两边仍然不一致**才接受，一轮删不动了就交回

这份对拍器抓 buggy.py 靠的是哪一支：`gen_boundary` 里 `kind == 1` 那一支——
单元素数组 `[v]` 配上 `x = v`。两个条件必须**绑在一起造**：单元素数组本身不稀罕，
但「单元素」还要恰好配上「x 等于那个元素」才会让候选解给出 -1 而参照解给出 0。
分头随机的话，这两个条件同时成立的概率极低（课件里方案 D 与方案 E 的对比就是这件事：
400 倍的差距）。
"""

import random

from tools import as_lists, labels, load_buggy, match_found, show_count, show_pairs

TRIALS = 2000                                  # 别改：任务 3、5 的对拍轮次
SEED = 20261115                                # 别改：任务 3 用的那个种子


# ══ TODO 1 · 参照解：从头到尾线性扫一遍 ══════════════════════

def brute_find(a, x):
    """在 a 里找 x：找到交回第一个匹配的下标，没有交回 -1。

    写得笨一点是有意的：参照解的价值不在快，在于一眼看得出它确实在回答问题。
    """
    for i in range(len(a)):
        if a[i] == x:
            return i
    return -1


# ══ TODO 2 · 两个造数据器 ═══════════════════════════════════

def gen_wide():
    """宽范围随机的数据：a 升序、x 在 0 到 99 里随便取（常常不在 a 里）。"""
    n = random.randint(1, 8)
    a = sorted(random.sample(range(100), n))
    return a, random.randrange(100)


def gen_boundary():
    """边界形态的数据：空数组 / 单元素 / 全相同 / 答案在两端，四种各占一部分。

    关键是每一支里 **x 都按形态给**：
      · 单元素那一支把 x 设成那个元素（不是让随机去撞）；
      · 全相同那一支把 x 设成那个重复的值；
      · 答案在两端那一支让 x 取 a[0] 或 a[-1]。
    候选解只在「x 真的在数组里」+「答案恰好是最后剩下的那一格」时出错，
    所以这两件事要一起造出来，而不是各自随机、等它们碰头。
    """
    kind = random.randrange(4)
    if kind == 0:                              # 空数组
        return [], random.randrange(100)
    if kind == 1:                              # 单元素，x 就取那个元素
        v = random.randrange(100)
        return [v], v
    if kind == 2:                              # 全相同
        v = random.randrange(5)
        return [v] * random.randint(2, 6), v
    n = random.randint(2, 6)                   # 答案在两端
    a = sorted(random.sample(range(100), n))
    return a, (a[0] if random.randrange(2) == 0 else a[-1])


# ══ TODO 3 · 比对循环 ═══════════════════════════════════════

def stress(candidate, reference, gen, trials, seed=None):
    """跑 trials 轮：每轮造一组数据、两边各跑一次、不一致就把那一组交回来。

    交回 (第几次, a, x, 候选答案, 参照答案)；全一致交回 None。
    只回一句「有问题」没用——必须把那一组数据一起交回来，别人才复现得了。
    """
    if seed is not None:
        random.seed(seed)                      # 在循环**外面**设一次
    for t in range(1, trials + 1):
        a, x = gen()
        got, want = as_lists(candidate, reference, a, x)
        if got != want:
            return t, list(a), x, got, want
    return None


# ══ TODO 4 · 反例最小化 ═════════════════════════════════════

def shrink(candidate, reference, a, x):
    """反复试着删掉一个元素：只要删完两边**仍然不一致**，就接受这个更小的版本。"""
    cur = list(a)                              # 复制一份，别改调用处那张表
    changed = True
    while changed:
        changed = False
        for i in range(len(cur)):
            smaller = cur[:i] + cur[i + 1:]
            got, want = as_lists(candidate, reference, smaller, x)
            if got != want:                    # 接受之前**再比一次**，这一句不能省
                cur = smaller
                changed = True
                break                          # 从头再试
    return cur


if __name__ == '__main__':                     # 与留白版同一段，别改
    from buggy import cand_find

    print('对拍器 0015 · 候选解 buggy.cand_find，参照解 brute_find')
    print()

    print('第 1 步 · 参照解的三组手算数据')
    for arr, target, want in [([], 3, -1), ([5], 5, 0), ([63, 97], 97, 1)]:
        got = match_found(brute_find(arr, target), arr)
        print('  参照解 ' + 'a=' + repr(arr) + ' x=' + repr(target)
              + ' → ' + repr(got) + '（期望 ' + repr(want) + '）')
    print()

    print('第 2 步 · 造数据器各来三组看一眼')
    random.seed(SEED)
    for name, maker in (('gen_wide', gen_wide), ('gen_boundary', gen_boundary)):
        rows = []
        for _ in range(3):
            made = maker()
            rows.append(made)
        print('  ' + name + ' ' + repr(rows))
    print()

    print('第 3 步 · 同一个函数当候选与参照（这一条必须是 None）')
    same = stress(brute_find, brute_find, gen_boundary, TRIALS, seed=SEED)
    print('  ' + labels(same)[0])
    print()

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
