"""任务 4 · 故意写错一次（lab 0029）

前三段都在「让它更快」，这一段是**回头验对拍器**。

课件那句话是：**每改一处都要回验。** 可「回验」这件事本身也得被验一次——
如果你的对拍器根本抓不到错，那它每一轮都交回「0 组不一致」，
你看到的是一个**永远说没事**的哨兵。所以这一步要**故意把某一招改坏一次**。

错法就取课件那个：把 `while i < stop` 里的 `stop = n` 写成 `stop = n - 1`——
最后**一个**元素不看了。这段代码长得跟对的那版几乎一模一样：

    stop = n - 1 if broken else n       ← 差别只有这一处

只有一个元素的数组，答案会直接变成 0：**错得不多，但已经错了。**
这正是它值得当例子的原因：**改一处都要回验，靠看是看不住的。**

接口：文件名、函数名、带 print 的行都是判分接口，别改；要写的是四个 TODO：

    TODO 1  audit_broken_once   先把坏的那一版跑一遍：抓到没有、证据是什么
    TODO 2  count_matches       那个会数数的循环（broken 就是你要写坏的那一版）
    TODO 3  audit               对拍本身：(不一致组数, 总组数)
    TODO 4  audit_after_fix     **改回来之后**再对拍一次：(不一致组数, 总组数)

对拍的数据与口径都由 tools 给好（`audit_cases` / `audit_run` / `audit_pair` /
`audit_fixed` / `count_matches`），判分自己另算一遍，不吃脚本里这几个数。

跑： py task4_break_it.py
判： py run_tests.py
"""

from tools import (AUDIT, audit_cases, audit_fixed, audit_pair, audit_run,
                   count_matches, show_banner, show_line)

# 对拍数据组的规模：由 tools.AUDIT 定（种子钉死 → 每组数据每次都一样）。
CASES = audit_cases(AUDIT['cases'], AUDIT['size'], AUDIT['value_hi'], AUDIT['seed'])


# ══ TODO 1 ═════════════════════════════════════════════════
# audit_broken_once(cases=None, low=AUDIT['low'], high=AUDIT['high'])：
# 先把坏的那一版跑一遍：交回一个字典（这几个键是判分接口，别改）。
#
# 三行就够，剩下的都在 tools 里：
#
#     if cases is None:
#         cases = CASES
#     return audit_pair(cases, low, high, True)      # True 就是「用坏的那一版」
#
# 交回的那几个键：
#
#     cases     对拍了几组
#     right     对的那版加起来多少
#     wrong     坏的那版加起来多少
#     misses    两组答案对不上的组数（这一格就是「抓到没有」的答案）
#     same      misses == 0（对拍说「一样」）
#     evidence  最早对不上的那一组： (原始数据, 对的答案, 坏的答案)，全对得上时 None
#
# **「抓到没有」不能只看 misses 是不是 0**——证据那一格才是能复现的东西。
# 有反例的否掉比没有反例的通过更有价值，对拍也一样。
def audit_broken_once(cases=None, low=AUDIT['low'], high=AUDIT['high']):
    return {'cases': 0, 'right': 0, 'wrong': 0, 'misses': 0,
            'same': True, 'evidence': None}


# ══ TODO 2 ═════════════════════════════════════════════════
# count_matches(values, lo, hi, broken=False)：数一数 values 里有多少个元素落在 [lo, hi] 里。
#
# 这就是那个「会数数的循环」，`broken` 那一个开关就是你要**故意写坏**的地方：
#
#     stop = len(values) - 1 if broken else len(values)     ← 只差这一处
#     hits = 0
#     i = 0
#     while i < stop:                     # 坏的那一版看不到最后一个元素
#         value = values[i]
#         if lo <= value <= hi:
#             hits += 1
#         i += 1
#     return hits
#
# 区别只有一处：坏的那版最后一个元素不看。所以
#   · 只有一个元素的数组上，答案直接变成 0（错得不多，但已经错了）；
#   · 空数组上两版都是 0（这一组两组答案一样，不算「露了」）。
#
# 判分拿**它自己的**五组数据（含空数组、单元素）调这个函数，两版答案都要与它另算的一致。
# tools 里有一份口径相同的实现，可以拿来对（别直接 return 它——那样这个 TODO 就没写了）。
def count_matches(values, lo, hi, broken=False):
    return 0


# ══ TODO 3 ═════════════════════════════════════════════════
# audit(cases=None, low=AUDIT['low'], high=AUDIT['high'])：
# 对拍本身 → (不一致组数, 总组数)。默认跑**对的那一版**。
#
#     if cases is None:
#         cases = CASES
#     right, _wrong, misses, _evidence = audit_run(cases, low, high, False)
#     return misses, len(cases)
#
# 对拍的口径（第 15 课那套）：同一批数据交给两个版本各跑一遍，
# 答案不一致就记一组「露了」，并**留下最早那一组的原始数据当证据**。
def audit(cases=None, low=AUDIT['low'], high=AUDIT['high']):
    return 0, len(CASES)


# ══ TODO 4 ═════════════════════════════════════════════════
# audit_after_fix(cases=None, low=AUDIT['low'], high=AUDIT['high'])：
# **把错改回来之后**再对拍一次 → (不一致组数, 总组数)。
#
#     if cases is None:
#         return audit_fixed()                       # tools 里给好的那一格：(0, 组数)
#     _right, _wrong, misses, _evidence = audit_run(cases, low, high, False)
#     return misses, len(cases)
#
# 这一格必须是 0：坏的那一版能被我抓到、改回来之后就抓不到了，
# **两头都对上**，才说明「抓到的」真的是我写坏的那一处，而不是碰巧。
def audit_after_fix(cases=None, low=AUDIT['low'], high=AUDIT['high']):
    return 0, len(CASES)


def _safe_row(record, keys):
    """打印用：拿不到就退回占位值——**留白版也要能把这几行打出来**（判分要读行数）。"""
    if not isinstance(record, dict):
        return [0] * len(keys)
    return [record.get(key, 0) for key in keys]


def _safe_pair(value, fill=(0, 0)):
    """打印用：把 (不一致组数, 总组数) 这种两格的表安全地摊开。"""
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return value[0], value[1]
    return fill


if __name__ == '__main__':                      # 别改：判分读的就是下面这几行
    show_banner('0029 对拍：先跑对的那一版')
    ROWS, TOTAL = _safe_pair(audit(CASES))                           # 别改
    show_line('对拍的数据组数', TOTAL)                              # 别改
    show_line('两版答案不一致的组数', ROWS)                         # 别改

    show_banner('0029 故意写错一次')
    BROKEN = audit_broken_once(CASES)                               # 别改
    _RIGHT, _WRONG, _MISSES, _SAME = _safe_row(
        BROKEN, ['right', 'wrong', 'misses', 'same'])               # 别改
    show_line('对的那版加起来', _RIGHT)                             # 别改
    show_line('坏的那版加起来', _WRONG)                             # 别改
    show_line('坏版露了几组', _MISSES)                              # 别改
    show_line('对拍抓到了吗', bool(_MISSES > 0))                    # 别改：期望 True
    show_line('两版答案一样吗', _SAME)                              # 别改：期望 False

    show_banner('0029 证据：最早对不上的那一组')
    EVIDENCE = BROKEN.get('evidence') if isinstance(BROKEN, dict) else None
    show_line('对不上的数据长这样', '' if EVIDENCE is None else EVIDENCE[0])   # 别改
    show_line('这组数据上一组的答案', '' if EVIDENCE is None else EVIDENCE[1])  # 别改
    show_line('这组数据上坏版的答案', '' if EVIDENCE is None else EVIDENCE[2])  # 别改
    print('   差别只有一处：stop = n - 1 if broken else n —— 最后一个元素不看了。')   # 别改
    print('   只有一个元素的数组上，答案会直接变成 0：错得不多，但已经错了。')        # 别改

    show_banner('0029 改回来之后')
    FIXED, TOTAL_FIXED = _safe_pair(audit_after_fix(CASES))          # 别改
    show_line('改回来之后不一致的组数', FIXED)                      # 别改：期望 0
    show_line('改回来之后还是坏的吗', bool(FIXED > 0))              # 别改：期望 False
    print('   两头都对上才说明「抓到的」真的是我写坏的那一处：'          # 别改
          '坏版被抓到 ' + str(_MISSES) + ' 组，改回来之后 0 组。')

    show_banner('0029 这一段的结论')
    print('   对拍器自己也要被验一次：抓不到错的对拍器，每轮都说「没事」。')   # 别改
    print('   优化不许改答案——顺序是先让它对，再让它快，每快一次都重新证明它对。')   # 别改
