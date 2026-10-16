"""parse.py · 三层解析：模型返回的是文本，不是结构化数据（lab 0033 任务 2，留白版）

第一段要调模型。**这里有一个必须一开始就承认的前提：模型返回的是一段文本。**
哪怕你在提示词里写了「只输出 JSON」，它也可能给你围栏、给你前言、或者因为长度限制被截断。

四种真实会遇到的样子（预置在 tools.PRESETS / fake_model.samples() 里，别改）：

    干净 JSON   '{"title": "拨钟问题", …}'
    带围栏       三个反引号 + json + 一段 JSON + 三个反引号
    带前言       '好的，我先把题意理一遍：…' 前面垫一段、后面缀一段
    被截断       开头是对的，结尾断在半截——**括号根本没闭合**

三档解析器，一层比一层能多救回一种：

    parse_naive        裸 json.loads                                    过 1/4
    parse_strip_fence  先剥围栏再 json.loads                              过 2/4
    parse_extract      剥围栏 + 提取首个**括号平衡**的 {...}                过 3/4
    parse_json         三档串起来（就是第一段用的那个）                    也是 3/4

**「被截断」那一档，再聪明的解析器也救不回来**——那不是格式问题，是**内容不完整**。
它只能靠另外两种办法：让模型少说点（response_format / 输出结构尽量扁平），或者**重试**。
重试在流水线那一段做（pipeline.py TODO 6），这里只负责**如实报告**「这一段坏了」。
判分接口（别改名字与形状）就是下面 TODO 4 / TODO 5 那两段里的五个函数。

    parse_naive(raw)         → 值 或 抛 ParseFailure
    parse_strip_fence(raw)   → 值 或 抛 ParseFailure
    parse_extract(raw)       → 值 或 抛 ParseFailure
    parse_json(raw)          → 值 或 抛 ParseFailure（三档串起来）
    explain_samples()        → [(样本名, 这一档吃不吃得下, 说明), …] 四行

失败一律抛 tools.ParseFailure，**reason 是一段说得清的说明**（不是把 json 的异常原样抛出去）：
「没找到 {」与「括号不闭合（找得到 { 却找不到配对的 }）——这是**被截断**，不是格式问题」
是两句不同的话，第二句才是被截断的样子。判分读的就是这两句。

跑： py parse.py
判： py run_tests.py
"""

from tools import (FENCE, ParseFailure, PRESETS, TRUNCATED_NOTE, _balanced_span, _raw_load,
                   _strip_fence, is_truncated_preset, parse_json as parse_json_three_layer,
                   show_banner, todo_mark)

# ══ TODO 4 ═════════════════════════════════════════════════
# 第一档 / 第二档：裸 json.loads，以及先剥围栏再 json.loads。
#
#   parse_naive(raw)        直接 json.loads（连 strip 都算「多做的」——它就该只过干净那一种）；
#   parse_strip_fence(raw)  剥掉最外面那一层围栏（连 'json' 那个语言标记一起剥）再 json.loads。
#                           没围栏时它就是一次普通的 json.loads。
#
# 两档都要：成功了交回值，失败了**抛 ParseFailure**（说明里带上原始异常的类型名）。
# 别把 json 的异常直接放出去，也别交回 None——调用处要能分辨「解析失败」与「解析出来是 null」。
# 提示：tools 里有 _raw_load(text)（一次 json.loads，失败转成 ParseFailure）与
#       _strip_fence(text)（剥围栏），直接用它们。
def parse_naive(raw):
    raise NotImplementedError('parse.py TODO 3（parse_naive）还没写')


def parse_strip_fence(raw):
    raise NotImplementedError('parse.py TODO 4（parse_strip_fence）还没写')


# ══ TODO 5 ═════════════════════════════════════════════════
# 第三档：从**任意位置**找出第一个**括号平衡**的 {...} 再解析。
#
#   1) 找第一个 '{'（找不到 → ParseFailure('没找到 {')）；
#   2) 从那里往右走，遇到 '{' 深度加一、'}' 深度减一，深度第一次回到 0 就是那个对象的右边界；
#   3) 走到头都没回到 0 → 括号不闭合：**这就是被截断**，抛出去的说明里要带上
#      tools.TRUNCATED_NOTE 那句话（判分按它认「这一段是被截断，不是格式问题」）。
#
# 两个必须照顾到的地方：
#   · 深度计数要跳过**字符串里面**的花括号（"…{…}" 那种内容不该影响计数）；
#   · 起点用第一个 '{'，不是第一个 '{' 到最后一个 '}' 那一段——后者在前言里也带花括号时会取错。
# 提示：tools._balanced_span(text) 交回 (起点, 终点)，可以不自己写；
#       自己写也行，判分只看行为（剥完围栏 + 取首个平衡对象之后能不能拿下）。
def parse_extract(raw):
    raise NotImplementedError('parse.py TODO 5（parse_extract）还没写')


# ── 给好的：三档串起来的那一个，与每档各自能吃下哪几种 ────────────────────

def parse_json(raw):
    """三档串起来：裸的 → 剥围栏的 → 提取首个平衡对象的（给好的，别改）。

    这就是第一段真正要用的那一个；它吃不下时抛 ParseFailure，reason 是**第一档**的说明
    ——第一档的说明最贴近原文（比如「括号不闭合」，那是被截断的样子）。
    """
    raise NotImplementedError('parse.py TODO 3 / 4 / 5（三档解析）还没写')


def explain_samples():
    """四份预置输出逐条过一遍三档，交回 [(名字, 哪几档吃得下, 原文摘要), …]（给好的，别改）。"""
    rows = []
    for name, raw in PRESETS.items():
        winners = []
        for label, fn in (('裸', parse_naive), ('剥围栏', parse_strip_fence),
                          ('提取', parse_extract)):
            try:
                fn(raw)
                winners.append(label)
            except Exception:
                pass
        rows.append((name, '、'.join(winners) if winners else '三档都不行',
                     raw[:44].replace('\n', ' ')))
    return rows


if __name__ == '__main__':                      # 别改：判分读的就是下面这几行
    show_banner('0033 四种真实会遇到的模型输出')
    for name, raw in PRESETS.items():
        print('  ' + name + ': ' + repr(raw[:60]))
    show_banner('0033 三档解析器各吃下几种')
    for name, winners, brief in explain_samples():
        print('  ' + name + ': ' + winners)
    show_banner('0033 被截断那一档为什么救不回来')
    try:
        parse_json(PRESETS['被截断'])
        print('  解析结果: 竟然解析出来了')
    except ParseFailure as exc:
        print('  解析结果: ' + exc.reason)
    except NotImplementedError as exc:
        print('  解析结果: ' + str(exc))
    except NotImplementedError as exc:
        print('  解析结果: ' + str(exc))
    print('  这一份是不是被截断: ' + str(is_truncated_preset(PRESETS['被截断'])))
    print('  截断的判据: ' + TRUNCATED_NOTE)
    show_banner('0033 每档各自的战果')
    good = 0
    for name, raw in PRESETS.items():
        try:
            parse_json(raw)
            good += 1
            print('  ' + name + ': 拿下')
        except ParseFailure as exc:
            print('  ' + name + ': 失败（' + exc.reason + '）')
        except NotImplementedError as exc:
            print('  ' + name + ': 失败（' + str(exc) + '）')
        except NotImplementedError as exc:
            print('  ' + name + ': 失败（' + str(exc) + '）')
    print('  三档串起来吃下: ' + str(good) + '/4 种')
    if good < 4:
        print('  → 剩下的那一档要走**重试**：' + todo_mark(6) + '（重试在流水线那一段）')
