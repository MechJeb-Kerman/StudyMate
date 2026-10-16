"""任务 3 · 括号匹配与第一个错位（参考解）"""

from tools import show_count


def is_valid(s):
    pair = {')': '(', ']': '[', '}': '{'}
    st = []
    for ch in s:
        if ch in '([{':
            st.append(ch)
        elif ch in ')]}':
            if not st or st[-1] != pair[ch]:
                return False
            st.pop()
    return not st


def first_error(s):
    pair = {')': '(', ']': '[', '}': '{'}
    st = []
    for i in range(len(s)):
        ch = s[i]
        if ch in '([{':
            st.append(i)
        elif ch in ')]}':
            if not st:
                return i
            if s[st[-1]] != pair[ch]:
                return i
            st.pop()
    if st:
        return st[0]
    return -1


if __name__ == '__main__':
    cases = ['()[]{}', '([)]', '(]', '((', '()', '', '([{}])', ')))', '(()']

    for s in cases:
        print('用例', repr(s), is_valid(s), first_error(s))

    valid_count = 0
    for s in cases:
        if is_valid(s):
            valid_count += 1
    print('一组用例里配对正确的个数', valid_count)
    print('校验 前六个用例逐字对照', [is_valid(s) for s in cases[:6]] == [True, False, False, False, True, True])
    print('校验 后三个用例逐字对照', [first_error(s) for s in cases[6:]] == [-1, 0, 0])
    show_count(1, '配对正确个数', valid_count)
    show_count(2, '(() 的首个错位', first_error('(()'))
    show_count(3, '(]  的首个错位', first_error('(]'))
