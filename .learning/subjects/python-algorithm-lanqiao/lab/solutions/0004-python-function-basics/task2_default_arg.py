"""任务 2 参考解 · 默认值只在定义时算一次

A：默认值写成 arg=i，读到 def 那一行时就把 i 当时的 5 记下来了，
   之后把 i 改成 6 也不影响它。
B：默认值是列表时所有没给这个实参的调用共用同一个列表；
   修法是把默认值写成 None，在函数体里判断、真的没给才新建。

B 段「调用一次、立刻打印一次」才看得见叠加的过程（课件里也是这么打印的）：
最后一次打印 b1，它已经是 [1, 2, 3]——第一次调用的返回值被后面两次改掉了。
"""

# ══ A · 默认值只算一次 ═════════════════════════════════════
i = 5


def show_default(arg=i):        # 这一行执行时 i 是 5，默认值就定死在 5
    return arg


i = 6
print('A 默认值', show_default())          # 5


# ══ B · 默认值是列表时 ═════════════════════════════════════
def grow_bad(a, L=[]):          # 陷阱版：三次调用共用这一个列表
    L.append(a)
    return L


def grow_ok(a, L=None):         # 修好版：默认为 None，没给才新建
    if L is None:
        L = []
    L.append(a)
    return L


b1 = grow_bad(1)
print('B 陷阱版 第 1 次', b1)              # [1]
b2 = grow_bad(2)
print('B 陷阱版 第 2 次', b2)              # [1, 2]
b3 = grow_bad(3)
print('B 陷阱版 第 3 次', b3)              # [1, 2, 3]
print('B 陷阱版是同一个列表', b1 is b2)      # True
print('B 陷阱版 b1 现在', b1)               # [1, 2, 3]：第一次的返回值被后面两次改掉了

g1 = grow_ok(1)
g2 = grow_ok(2)
g3 = grow_ok(3)
print('B 修好版', g1, g2, g3)              # [1] [2] [3]
print('B 修好版是同一个列表', g1 is g2)      # False

extra = [7]
g4 = grow_ok(8, extra)
print('B 修好版接现成列表', g4, extra)       # [7, 8] [7, 8]
