"""任务 3 · 多组数据要清空（lab 0030 · 提交前自检）· 参考解

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
本节的 Solver 是**故意**把状态放在外面的那一版——不然「忘了清空」这个 bug 就没有了。

run_cases 里 reset 的位置是这一节的关键：
  · reset_per_case 为假 → 一组都不清（也不能在循环外面补一次，那会让 bug 消失）；
  · reset_per_case 为真 → **每问之前**清一次，这才是「每问都清空」。

接口：文件名、函数名、带 print 的行都是判分接口，别改。

跑： py task3_reset.py
判： py run_tests.py
"""

from tools import CASES, EXPECT, show_banner, show_line, values_equal

# 占位那一格长这样：留白版打出来一眼就知道这一段还没接上。
MISSING = '（还没接上）'


def cell(value):
    """打印一格：值还是占位。"""
    return MISSING if value is None else str(value)


class Solver:
    """状态放在对象的属性上：self.total 活得比一组数据长，只有 reset 能清掉它。"""

    def __init__(self):
        self.total = 0

    def reset(self):
        """唯一能清掉跨组状态的地方。改成在 answer 里顺手清，这一节就没有 bug 可看了。"""
        self.total = 0

    def answer(self, a):
        """把这一组累加进 self.total，交回 self.total——**不清空**。"""
        for x in a:
            self.total += x
        return self.total


def run_cases(cases, reset_per_case, solver=None):
    """按同一个类跑完所有组，交回每组一个答案。

    reset_per_case 决定「每问之前清不清」：
      · 真 → 第一组 6、第二组 30、第三组 5，与期望一致；
      · 假 → 6、36、41：第一组照样对，第二组起就叠着上一次的答案。
    第二行那个 36 就是「只拿第一组试就看不出来」的证据。
    """
    if solver is None:
        solver = Solver()
    out = []
    for a in cases:
        if reset_per_case:
            solver.reset()
        out.append(solver.answer(a))
    return out


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
