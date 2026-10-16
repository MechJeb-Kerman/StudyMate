"""任务 4 · 表达式求值（参考解）"""

from tools import show_count


def eval_rpn(s):
    st = []
    for ch in s:
        if ch in '0123456789':
            st.append(int(ch))
        else:
            b = st.pop()
            a = st.pop()
            if ch == '+':
                st.append(a + b)
            elif ch == '-':
                st.append(a - b)
            elif ch == '*':
                st.append(a * b)
            else:
                st.append(a // b)
    return st[-1]


def parse(s):
    out = []
    num = ''
    for ch in s:
        if ch.isdigit():
            num = num + ch
        else:
            if num != '':
                out.append(int(num))
                num = ''
            out.append(ch)
    if num != '':
        out.append(int(num))
    return out


def value(s):
    PRIORITY = {'*': 2, '/': 2, '+': 1, '-': 1}
    nums = []
    ops = []

    def apply_top():
        op = ops.pop()
        b = nums.pop()
        a = nums.pop()
        if op == '+':
            nums.append(a + b)
        elif op == '-':
            nums.append(a - b)
        elif op == '*':
            nums.append(a * b)
        else:
            nums.append(a // b)

    for t in parse(s):
        if isinstance(t, int):
            nums.append(t)
        elif t == '(':
            ops.append(t)
        elif t == ')':
            while ops and ops[-1] != '(':
                apply_top()
            ops.pop()
        else:
            while ops and ops[-1] != '(' and PRIORITY[ops[-1]] >= PRIORITY[t]:
                apply_top()
            ops.append(t)
    while ops:
        apply_top()
    return nums[-1]


if __name__ == '__main__':
    rpn_cases = ['34+2*', '12+', '93/', '56+7*', '52-3+']
    rpn_want = [14, 3, 3, 77, 6]

    for s in rpn_cases:
        print('后缀', s, eval_rpn(s))

    rpn_ok = True
    for i in range(len(rpn_cases)):
        if eval_rpn(rpn_cases[i]) != rpn_want[i]:
            rpn_ok = False
    print('后缀 五组全部对上', rpn_ok)
    print('后缀 减法与除法没有写反', eval_rpn('52-') == 3 and eval_rpn('93/') == 3)

    print('切分 (12+3)*4', parse('(12+3)*4'))
    print('切分 7', parse('7'))

    mid_cases = ['12+3', '(1+2)*3', '12*3+4', '9-3+2', '9-3-2', '4*5-6/3']
    mid_want = [15, 9, 40, 8, 4, 18]

    for s in mid_cases:
        print('中缀', s, value(s))

    mid_ok = True
    for i in range(len(mid_cases)):
        if value(mid_cases[i]) != mid_want[i]:
            mid_ok = False
    print('中缀 六组全部对上', mid_ok)
    print('中缀 同优先级从左往右', value('9-3+2') == 8 and value('9-3-2') == 4)

    show_count(1, '后缀 全部对上', rpn_ok)
    show_count(2, '中缀 全部对上', mid_ok)
    show_count(3, '两种都算对', rpn_ok and mid_ok)
