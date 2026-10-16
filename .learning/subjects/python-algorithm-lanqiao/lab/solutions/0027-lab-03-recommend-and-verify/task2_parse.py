"""任务 2 · 返回文本的两层解析（lab 0027）· 参考解

即使提示词写了「不要围栏」，真实返回的文本仍然可能带围栏、带前后解释。
这不是模型不听话，是**文本生成本身就有浮动**。所以解析器要分两层：

    第一层 剥围栏；
    第二层 取第一个 `{` 到最后一个 `}` 之间那段。

然后才 json.loads。六种形态样本上的成绩是：朴素 json.loads 过 1 种，加固版过 5 种。

第六种（字符串里的引号没有转义）两版都会失败——**失败的方式是交回一个明确的失败标记**，
不抛异常、不交回半个字典。整条链要能带着「这一段失败了」继续往下走，所以失败也得是一种**值**。

三个坑：

  1. 正则里的 re.S 是必需的。不加它，`.` 不匹配换行，围栏里的内容就抓不到。
  2. 剥围栏要在**取大括号之前**。
  3. 找大括号之前先看两端的下标（find 找不到交回 -1，切片会切出一段乱七八糟的东西）。

跑： py task2_parse.py
判： py run_tests.py
"""

import re

from tools import (ESCAPE_TRAP, FENCE, clamp, marker_cell, safe_load, sample_texts,
                   show_banner, show_line)


def parse_naive(raw):
    """最直觉的写法：直接 json.loads；失败交回 '<异常类名>' 这个标记。"""
    value, exc = safe_load(raw)
    if exc is None:
        return value
    return '<' + type(exc).__name__ + '>'


def parse_robust(raw):
    """先剥围栏，再取第一个 { 到最后一个 } 之间那段，最后 json.loads。"""
    text = raw.strip()
    pattern = re.escape(FENCE) + r'(?:json)?\s*(.+?)' + re.escape(FENCE)
    found = re.search(pattern, text, re.S)
    if found:
        text = found.group(1).strip()
    lo, hi = text.find('{'), text.rfind('}')
    if lo == -1 or hi == -1 or hi < lo:
        return '<没有找到 JSON 对象>'
    value, exc = safe_load(text[lo:hi + 1])
    if exc is None:
        return value
    return '<' + type(exc).__name__ + '>'


def show_one(value):
    """一条解析结果排成要打印的那一格：字典取 family，失败标记原样，别的形状截断显示。"""
    if isinstance(value, dict):
        return value['family']
    if isinstance(value, str):
        return value
    return clamp(value)


def explain_samples():
    """六种形态逐条打印，交回 (朴素过的种数, 加固过的种数)。"""
    count_naive = 0
    count_robust = 0
    for name, raw in sample_texts().items():
        got_naive = parse_naive(raw)
        got_robust = parse_robust(raw)
        count_naive += 1 if not isinstance(got_naive, str) else 0
        count_robust += 1 if not isinstance(got_robust, str) else 0
        print(name)
        print('   朴素: ' + show_one(got_naive))
        print('   加固: ' + show_one(got_robust))
    print('六种里成功解析：朴素 ' + str(count_naive) + ' 种，加固 ' + str(count_robust) + ' 种')
    return count_naive, count_robust


if __name__ == '__main__':
    show_banner('0027 六种形态样本')
    naive_ok, robust_ok = explain_samples()
    show_line('朴素过的种数', naive_ok)
    show_line('加固过的种数', robust_ok)

    show_banner('0027 第六种坏在哪')
    trap_naive = parse_naive(ESCAPE_TRAP)
    trap_robust = parse_robust(ESCAPE_TRAP)
    print('   原文: ' + ESCAPE_TRAP)
    print('   朴素: ' + show_one(trap_naive))
    print('   加固: ' + show_one(trap_robust))
    print('   大括号配平吗: ' + str(ESCAPE_TRAP.count('{') == ESCAPE_TRAP.count('}')))
    print('   括号是配平的，坏的是字符串内容本身。')
    print('   朴素交回的是标记吗: ' + marker_cell(trap_naive))
    print('   加固交回的是标记吗: ' + marker_cell(trap_robust))

    show_banner('0027 加固版多认下来的四种')
    print('   加固版认下来 ' + str(robust_ok))
    print('   朴素版认下来 ' + str(naive_ok))
