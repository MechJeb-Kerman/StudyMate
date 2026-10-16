"""任务 2 · 返回文本的两层解析（lab 0027）

即使提示词写了「不要围栏」，真实返回的文本仍然可能带围栏、带前后解释。
这不是模型不听话，是**文本生成本身就有浮动**。所以解析器要分两层：

    第一层 剥围栏；
    第二层 取第一个 `{` 到最后一个 `}` 之间那段。

然后才 json.loads。判分要的是**两版都写**、并且六种形态样本上的成绩对得上：

    朴素 json.loads：六种里过 1 种；
    加固版：六种里过 5 种。

第六种（字符串里的引号没有转义）两版都会失败——**但失败的方式必须是交回一个明确的
失败标记**，不许抛异常，也不许交回半个字典（比如已经取到 family 就交回 {'family': …}）。
整条链要能带着「这一段失败了」继续往下走，所以失败也得是一种**值**。

三个坑，都是这一课特意埋的：

  1. 正则里的 re.S 是必需的。不加它，`.` 不匹配换行，而 JSON 一定是多行的，
     围栏里的内容就抓不到——那样「套了 json 围栏」这一种也过不去，成绩会变成 1 种。
  2. 剥围栏要在**取大括号之前**：先剥再取，顺序反了等于没剥。
  3. 找大括号之前先看两端的下标。`find` 找不到交回 -1，
     这时 text[lo:hi + 1] 会切出一段你没打算切的东西，而不是报错。

接口：文件名、函数名、带 print 的行都是判分接口，别改；要写的是三个 TODO。

跑： py task2_parse.py
判： py run_tests.py
"""

import re

from tools import (ESCAPE_TRAP, FENCE, clamp, marker_cell, safe_load, sample_texts,
                   show_banner, show_line)


# ══ TODO 1 ═════════════════════════════════════════════════
# parse_naive(raw)：最直觉的写法——直接 json.loads(raw)。
#
# 要点：
#   · 成功 → 交回那个字典（原样交回，别去挑键）；
#   · 失败 → 交回**字符串标记** '<异常类名>'，例如 '<JSONDecodeError>'。
#     用 '<' + type(exc).__name__ + '>' 拼出来（tools.safe_load 已经把异常接住了，
#     它交回 (值, 异常对象) 两样，异常是 None 就说明成功了）；
#   · 绝对不许把这个异常抛出去——抛出去整条链就断在这里。
def parse_naive(raw):
    return None


# ══ TODO 2 ═════════════════════════════════════════════════
# parse_robust(raw)：先剥围栏，再取第一个 { 到最后一个 } 之间那段，最后 json.loads。
#
# 步骤（顺序别换）：
#   1. text = raw.strip()
#   2. 用 re.search 找围栏：模式是 re.escape(FENCE) + '(?:json)?\\s*(.+?)' + re.escape(FENCE)，
#      末尾要带 re.S。**别在源码里写出连续三个反引号**（会打断阅卷工具链），
#      要拼就拼 re.escape(FENCE)，或者写 re 的 {3} 量词。
#      找到就把 group(1) 取出来 strip 一下当新的 text。
#   3. lo, hi = text.find('{'), text.rfind('}')
#   4. lo == -1 或 hi == -1 或 hi < lo → 交回 '<没有找到 JSON 对象>'
#      （**先判这个再做切片**：find 交回 -1 时切片会切出一段乱七八糟的东西）
#   5. 对 text[lo:hi + 1] 跑 safe_load；成了交回那个字典，
#      败了照样交回 '<异常类名>' 这个字符串标记。
def parse_robust(raw):
    return None


# ══ TODO 3 ═════════════════════════════════════════════════
# explain_samples()：把六种形态样本逐条打印出来，交回 (朴素过的种数, 加固过的种数)。
#
# 打印格式是判分接口，照课件那一节的形状写：
#
#     <名字>
#         朴素: <family 或失败标记>
#         加固: <family 或失败标记>
#     ……六组……
#     六种里成功解析：朴素 N 种，加固 M 种
#
# 中间那三行的规则：
#   · 解析结果不是 str（也就是拿到的真是字典）→ 打印它['family']；
#   · 解析结果是 str（失败标记）→ 原样打印那个标记；
#   · 别的形状（比如 None：函数还是占位值，或者交回了半个字典以外的东西）→ 打印 clamp(结果)。
#     千万别直接取 ['family']——留白版交回 None 时那会抛 TypeError。
#
# 计分口径：一次解析算「过了」当且仅当它的结果是 str 以外的东西。六组数完交回两个整数。
# 注意**交回的必须是两个整数**：下面调用处那行是解包，交回 None 会直接崩在解包上。
def explain_samples():
    return 0, 0


def show_one(value):
    """一条解析结果排成要打印的那一格：字典取 family，失败标记原样，别的形状截断显示。"""
    if isinstance(value, dict):
        return value['family']
    if isinstance(value, str):
        return value
    return clamp(value)


if __name__ == '__main__':                      # 别改：判分读的就是下面这几行
    show_banner('0027 六种形态样本')
    naive_ok, robust_ok = explain_samples()
    show_line('朴素过的种数', naive_ok)          # 别改：期望 1
    show_line('加固过的种数', robust_ok)          # 别改：期望 5

    show_banner('0027 第六种坏在哪')
    trap_naive = parse_naive(ESCAPE_TRAP)
    trap_robust = parse_robust(ESCAPE_TRAP)
    print('   原文: ' + ESCAPE_TRAP)                                        # 别改
    print('   朴素: ' + show_one(trap_naive))                               # 别改：期望 <JSONDecodeError>
    print('   加固: ' + show_one(trap_robust))                              # 别改：期望 <JSONDecodeError>
    print('   大括号配平吗: ' + str(ESCAPE_TRAP.count('{') == ESCAPE_TRAP.count('}')))  # 别改
    print('   括号是配平的，坏的是字符串内容本身。')                          # 别改
    print('   朴素交回的是标记吗: ' + marker_cell(trap_naive))                # 别改：期望 <JSONDecodeError>
    print('   加固交回的是标记吗: ' + marker_cell(trap_robust))               # 别改：期望 <JSONDecodeError>

    show_banner('0027 加固版多认下来的四种')
    print('   加固版认下来 ' + str(robust_ok))                    # 别改：期望 5
    print('   朴素版认下来 ' + str(naive_ok))                     # 别改：期望 1
