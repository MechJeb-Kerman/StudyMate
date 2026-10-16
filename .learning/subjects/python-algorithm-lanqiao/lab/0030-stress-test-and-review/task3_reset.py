"""任务 3 · 多组数据要清空（lab 0030 · 提交前自检）

课件那一节量出来的第三组硬事实是：**多组数据的错法里，第一组往往是对的。**

题面写「共 T 组数据」的时候，多了一个全新的出错面：组与组之间的状态。
凡是**定义在循环外面**的东西——全局变量、类属性、累加器、上一次的答案——
都必须在新一组开始时清掉。漏一个，第一组对、第二组开始就错：

    class Solver:
        def __init__(self):
            self.total = 0

        def reset(self):
            self.total = 0

        def answer(self, a):
            for x in a:
                self.total += x
            return self.total

三组数据 [[1, 2, 3], [10, 20], [5]]，正确答案 [6, 30, 5]。

    忘了清空      : [6, 36, 41]
    每问都清空    : [6, 30, 5]
    忘了清空对吗: False    每问清空对吗: True

看到那个 `6` 了吗——**第一组是对的**。所以如果你只拿样例的第一组数据试，什么都看不出来。
第二组 36 = 6 + 30、第三组 41 = 36 + 5，全是上一次的答案叠上去的。

最省事的修法不是「记住要清空」，而是**别把状态放在外面**：把每组的处理写成一个函数，
所有中间量都是局部变量，退出函数自然就清掉了。要清的东西越少，忘清的机会越少。

这个任务要把这两组输出亲手打出来，并交出「两组各自是否等于期望」这个判断。

接口：文件名、函数名、带 print 的行都是判分接口，别改；要写的是三个 TODO。

跑： py task3_reset.py
判： py run_tests.py
"""

from tools import CASES, EXPECT, show_banner, show_line, values_equal

# 占位那一格长这样：留白版打出来一眼就知道这一段还没接上。
MISSING = '（还没接上）'


def cell(value):
    """打印一格：值还是占位。"""
    return MISSING if value is None else str(value)


# ══ TODO 1 ═════════════════════════════════════════════════
# class Solver：那份「状态放在外面」的处理类。三个方法，照课件写就够：
#
#     __init__(self)      self.total = 0            ← 状态定义在对象上，它活得比一组数据长
#     reset(self)         self.total = 0            ← 唯一能把它清掉的地方
#     answer(self, a)     把 a 里每个数累加进 self.total，交回 self.total
#
# answer 里**不许**自己偷偷把 total 归零：那样「忘了清空」这个 bug 就复现不出来了。
# 这个 bug 的功能就是「只要没人调 reset，状态就一直留着」。
class Solver:

    def __init__(self):
        pass

    def reset(self):
        pass

    def answer(self, a):
        return 0


# ══ TODO 2 ═════════════════════════════════════════════════
# run_cases(cases, reset_per_case, solver=None) → 每组一个答案的 list
#
#     if solver is None:
#         solver = Solver()       ← 没传就自己起一个（别把 Solver() 写成参数默认值）
#     out = []
#     for a in cases:
#         if reset_per_case:
#             solver.reset()          ← 每问都清空：这一句就是「对」的那一版
#         out.append(solver.answer(a))
#     return out
#
# 要点：
#
#   · reset_per_case 为假时，**一组都不许清**（也不能在循环外面补一次 reset：
#     那会让「忘了清空」也变对，这一节的现象就没了）；
#   · solver 允许从外面传进来——判分要往里塞自己那个类，看这条链通不通；
#     写成 solver = Solver() 的默认参数就把缝堵上了；
#   · 交回的是**新 list**，别把 types 里的列表改掉。
def run_cases(cases, reset_per_case, solver=None):
    return []


if __name__ == '__main__':                      # 别改：判分读的就是下面这些行
    show_banner('0030 多组数据：第一组往往是对的')

    leaky = run_cases(CASES, False)
    clean = run_cases(CASES, True)

    show_line('   三组数据      :', str(CASES))
    show_line('   忘了清空      :', cell(leaky))
    show_line('   每问都清空    :', cell(clean))
    show_line('   正确答案      :', str(EXPECT))
    show_line('   忘了清空对吗:', str(values_equal(leaky, EXPECT))
              + '    每问清空对吗: ' + str(values_equal(clean, EXPECT)))
    show_line('   → 两组各自的第 1 组:',
              '忘了清空 ' + cell(leaky[0] if leaky else None)
              + ' / 每问清空 ' + cell(clean[0] if clean else None)
              + ' / 期望 ' + str(EXPECT[0]))
