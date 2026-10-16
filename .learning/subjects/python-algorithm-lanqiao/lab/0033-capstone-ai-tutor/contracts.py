"""contracts.py · 五段的输入输出契约（lab 0033 任务 1 · 参考解）

这一课的流水线是五段：

    题目文本 → 1 提取题意（调模型） → 2 推荐候选算法 → 3 写解法 → 4 自动验证 → 5 出记录

**流水线最常见的死法不是某一段写错，而是段与段之间对不上。** 防它的办法是把每段的
输入输出契约**先写下来**（在写实现之前），再让每两段之间跑一次检查。

这张表就是这一课最值钱的产物之一：有了它，第 4 段和第 5 段可以分别开发、分别测；
没有它，你只能在整条流水线跑起来的时候才发现字段名对不上——那时候你根本不知道是哪一段的问题。

判分接口（别改名字与形状）：

    CONTRACTS    {段名: TypeSpec}                     —— 五段都要有
    TABLE_ROWS   [(段号, 输入, 输出契约), …]           —— 判分核对这张表的排列
    contract_table()                                  —— 交回那张表（供打印）

段名必须逐字是这五个字符串：'1 提取题意' / '2 推荐算法' / '3 写解法' / '4 验证' / '5 出记录'。

跑： py contracts.py
判： py run_tests.py
"""

from tools import BOOL, INT, LIST_STR, STR, TEXT, TODO_NAMES, TypeSpec, \
    is_bool, is_cases, is_dict_str_int, is_int, is_list_str, is_str, is_text, show_banner

# 五个段的段名（判分按这几个字符串取契约，别改）。
STAGES = ['1 提取题意', '2 推荐算法', '3 写解法', '4 验证', '5 出记录']

# ══ TODO 1 ═════════════════════════════════════════════════
# 把五段的契约写出来：{段名: TypeSpec(段名, {字段名: 检查这个值的函数})}。
#
# 契约表（课件第 2 节那张五行表，字段名与类型都要照它来）：
#
#   段            输入                输出（契约）
#   1 提取题意    题目文本（str）      {title: str, constraints: {n_max: int, value_max: int}, ask: str}
#   2 推荐算法    第 1 段的 dict       {candidates: [str], reasons: [str], picked: str}
#   3 写解法      第 2 段的 dict       {code: str, entry: str, complexity: str}
#   4 验证        第 3 段的 dict + 数据 {passed: bool, evidence: [str], failing_case: str or None}
#   5 出记录      第 4 段的 dict       {problem: str, picked: str, passed: bool, evidence: [str],
#                                       seed: int, rerun: str}
#
# 第 4 段的 passed 一定是 is_bool：写成松口径的话，'False' 这个**非空字符串**
# 在布尔语境里是 True，报告会静默地写「验证 通过」。
# 第 4 段与第 5 段多几个判分要用的字段（cases / outputs / results / seed / failed_first / mode），
# 照下面写就行。**契约里只放那一段真的产出的字段**：「哪一段吃什么」「哪一段允许返回 None」
# 是这张表的另外两列，写在 TABLE_ROWS 那张表里，不放进契约——
# 不然拿契约去查运行结果时会冒出「缺字段 takes」这种没意义的报错。
CONTRACTS = {}
# 全部字段里只有一处可能是 None：第 4 段的 failing_case（一组都没跑起来时）。
# 别的地方都不许用 None 表示「还没有」——那与「真的没有」分不开。

# 五段里只有第 1 段与第 2 段要调模型；**带重试的只有第 1 段**。
MODEL_STAGES = [STAGES[0], STAGES[1]]
RETRY_STAGES = [STAGES[0]]


# ══ TODO 2 ═════════════════════════════════════════════════
# 把检查器写出来：check_contract(spec, obj) —— 契约不对就**抛 TypeError**，
# 并且说清是**哪一段的哪个字段**、那个字段应该是什么类型；对了就原样交回 obj。
#
# 为什么抛而不是交回一个 False：下游拿到的是「这一段能不能用」这个结论，
# 一个 False 很容易被顺手 `if not x` 吃掉、然后接着往下算——那就又回到静默错误了。
# 抛出来是为了让错误停在**它发生的那一段**，而不是五层之外。
#
# 这一条是整课的判据：判分会给它一个 passed 被写成字符串 'False' 的记录，
# 它必须在边界就喊「字段 passed 应为 bool，实际是 str」。
def check_contract(spec, obj):
    raise NotImplementedError('contracts.py TODO 2（check_contract）还没写')


def contract_error(spec, obj):
    """这一句给运行结果用：契约不对时交回一句说明，全对时交回空串（给好的，别改）。"""
    from tools import contract_error as _error
    return _error(spec, obj)


# ══ TODO 3 ═════════════════════════════════════════════════
# 这张表本身：[(段号, 输入, 输出契约)]，五行，顺序就是流水线的顺序。
#
# 「输入」那一列写人话（比如 '题目文本（str）'），「输出契约」那一列写字段与类型
# （比如 '{title: str, constraints: {n_max: int, value_max: int}, ask: str}'）。
# 判分会核对：五行齐全、顺序对、段号是 1..5、输出契约那一列里五个段的关键字段都点到了。
TABLE_ROWS = []
# 表里第 4、5 段比课件那五行多了几个字段：判分与记录模板都要用（cases / outputs /
# results / seed / failed_first / mode）。课件那张表是**最低要求**，不是上限。


def contract_table():
    """交回那张表（判分与脚本打印它）。给好的：TODO 3 写完它自己就有内容了。"""
    return list(TABLE_ROWS)


if __name__ == '__main__':                      # 别改：判分读的就是下面这几行
    show_banner('0033 五段的契约表')
    rows = contract_table()
    print('  契约表 ' + str(len(rows)) + ' 行')
    if not rows:
        # 还没接上时把五段各打两行占位：**打印行数不许随进度变**，判分读的就是这几行。
        for number in range(1, 6):
            print('  第 ' + str(number) + ' 段  输入: ' + TODO_NAMES[1])
            print('           输出: ' + TODO_NAMES[3])
    for number, takes, gives in rows:
        print('  第 ' + str(number) + ' 段  输入: ' + str(takes))
        print('           输出: ' + str(gives))
    show_banner('0033 五段契约的字段与类型')
    for number, stage in enumerate(STAGES, 1):
        spec = CONTRACTS.get(stage)
        print('  ' + stage + ': ' + (spec.describe() if spec is not None
                                     else TODO_NAMES[1]))
