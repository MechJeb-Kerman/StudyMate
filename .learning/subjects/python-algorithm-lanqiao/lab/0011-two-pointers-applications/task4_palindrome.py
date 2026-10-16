"""任务 4 · 回文判定：两头向中间

题目：判断一个序列是不是回文，也就是它与自己的逆序逐项相等。列表与字符串都按下标取元素、
都用 len 取长度，所以同一段代码对两者都成立。

两个下标的职责在这里**完全对称**：l 从左往右、r 从右往左，每轮比较 s[l] 与 s[r]。
移动条件是两条，与两数之和那种「只动一个」不同——比较结果只有相等与不相等两种，
不相等直接给出结论，相等则两个指针一起动。

    每轮开始之前的命题：  [0, l) 与 (r, n-1] 已经逐对比较过，每一对都相等；
                          因此整个序列是不是回文，只剩 [l, r] 这一段还没查。
    l 保证：左边已经比过的部分不需要再比。  r 保证：右边已经比过的部分不需要再比。

奇数长度的序列不用特判：中间那一项与自身相等，两个指针在中间那一格相遇（l == r），
循环条件 l < r 不成立而正常结束。

判分还会另起一个探针 import 你的函数（`probes/probe_task4.py`），拿一组判分自己的数据
逐项试：两版都必须在**每一组**上交出同一个结果。

接口：函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的两段。

跑： py task4_palindrome.py
判： py run_tests.py
"""

from tools import show_count


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 is_palindrome(s)：是回文交回 True，否则 False。序列可以是字符串、也可以是列表。
#
# 要点：
#   l = 0
#   r = len(s) - 1
#   while l < r:                          两个指针相向而行，相遇或交错就停
#       if s[l] != s[r]:  return False    不相等直接给结论，不必再比
#       l += 1
#       r -= 1                            相等则两个一起动
#   return True
#
# 三处边界：
#   · 空文本与单元素：l < r 一开始就不成立，直接交回 True（两者都算回文）；
#   · 长度是偶数时两个指针交错（l > r）结束，奇数时在中间相遇（l == r）结束，
#     两种情况都不用特判；
#   · 相等时**两个**指针都要动。只动一个会原地打转，跑不完。
def is_palindrome(s):
    return False


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 first_mismatch(s)：是回文交回 -1，否则交回**第一处不相等**的两个下标 (l, r)。
#
# 要点：与 is_palindrome 是同一趟走法，只把 `return False` 换成交出那一对下标。
#   （下标对里的两个数：左边那个是 l，右边那个是 r。）
#   走完都没遇到不相等的，就交回 -1。
#
# 两者对「是不是回文」的判断必须完全一致：把 first_mismatch(s) == -1 与 is_palindrome(s)
# 摆在一起看，两列在每一组数据上都该一样——判分就是这么查的。
def first_mismatch(s):
    return -1


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声
    cases = ['上海自来水来自海上', 'abccba', 'abcabc', [1, 2, 3, 2, 1], [1, 2, 2, 1],
             [], [9], 'a', 'ab', [1, 2]]       # 别改：字符串与列表各几组，含空序列与单元素
    want = [True, True, False, True, True, True, True, True, False, False]   # 别改

    for s in cases:                            # 别改
        print('用例', repr(s), is_palindrome(s), first_mismatch(s))        # 别改

    ok = 0                                     # 别改
    for i in range(len(cases)):                # 别改
        if is_palindrome(cases[i]) == want[i]: # 别改
            ok += 1                            # 别改
    print('十组用例的判定对上', ok)                                 # 别改：期望 10

    consistent = True                          # 别改
    for s in cases:                            # 别改
        if (first_mismatch(s) == -1) != is_palindrome(s):              # 别改
            consistent = False                 # 别改
    print('两版判定完全一致', consistent)                           # 别改：期望 True

    print('第一处错位 abcabc', first_mismatch('abcabc'))            # 别改：期望 (0, 5)
    print('第一处错位 [1, 2, 2, 3]', first_mismatch([1, 2, 2, 3]))  # 别改：期望 (0, 3)
    print('第一处错位 abca', first_mismatch('abca'))                # 别改：期望 (1, 2)

    show_count(1, '判定对上组数', ok)                              # 别改：期望 10
    show_count(2, '两版一致', consistent)                          # 别改
    show_count(3, 'abcabc 错位', first_mismatch('abcabc') == (0, 5))    # 别改
    show_count(4, '列表 [1,2,2,3] 错位', first_mismatch([1, 2, 2, 3]) == (0, 3))   # 别改
