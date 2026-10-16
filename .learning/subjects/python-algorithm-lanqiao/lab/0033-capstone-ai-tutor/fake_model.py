"""fake_model.py · 假模型：把「调大模型」收成一道缝（lab 0033 · 两侧相同）

真模型要联网、要 key、要给钱、还会因为服务波动给出不同的结果。**这一课不要求你有 key**，
所以真正要写下来的不是「怎么调 API」，而是**缝在哪儿**：

    题面文本 + 重试标记 ──▶ call_model(prompt, retry=False) ──▶ 一段**文本**

那个返回值是**文本**，不是结构化数据——这一点是本课所有麻烦的源头，也是这一份要立住的前提：
围栏、前言、截断，一个都不少地按真实的样子来。

    本文件与参考解里那一份**逐字节相同**：学生不用改它。
    要接真 API 的时候，改的是调用处那一个参数（第三段「接上真调用」）：

        # 离线（这一课）：假模型按提示词的内容挑一份预置输出
        raw = call_model(prompt)
        # 联网（第三段）：换成真的，key 走环境变量
        # import os
        # from openai import OpenAI
        # client = OpenAI(api_key=os.environ['DEEPSEEK_API_KEY'],
        #                 base_url='https://api.deepseek.com')
        # raw = client.chat.completions.create(model='deepseek-chat',
        #         messages=[{'role': 'user', 'content': prompt}],
        #         response_format={'type': 'json_object'}).choices[0].message.content

换掉这一处，流水线上其余四段**一行都不用改**——这就是缝的意义。
"""

import copy

from tools import (CLEAN, FENCED, MODEL_ADVICE, PREFACED, PRESETS, TRUNCATED,
                   is_truncated_preset, pick_preset)

# 假模型的调用流水：每一次 (提示词, retry, 交回的文本) 都记下来。
# 判分就是靠它数「第一段到底调用了几次模型」——被截断那一次**必须调用两次**，
# 只调用一次就说明重试没做，模型那半截输出被静默吞掉了。
CALLS = []


def call_model(prompt, retry=False):
    """**那道缝**：提示词进、一段文本出。离线时接的就是这里。

    · retry=False 是第一次问；
    · retry=True 是「上一次的输出坏了，带着坏消息再问一次」——
      被截断那一份在 retry=True 时给出干净的那个，这就是重试能救回它的原因；
    · 交回的是**副本**：调用处如果就地改了返回值，不许把预置的那四份带坏。
    """
    raw = pick_preset(prompt, retry)
    CALLS.append((prompt, bool(retry), raw))
    return copy.deepcopy(raw)


def calls():
    """到现在为止调过几次模型。"""
    return len(CALLS)


def reset():
    """把记账清空（判分每次探针之前都会调一次，免得把上一轮的数记进来）。"""
    CALLS.clear()


def last_call():
    """最后一次调用是怎样的 → (提示词, retry, 交回的文本)；没调过就是 None。"""
    return CALLS[-1] if CALLS else None


def preset_names():
    """四份预置输出的名字（顺序就是课件里那四行）。"""
    return list(PRESETS)


def preset(name):
    """按名字取一份预置输出（交回副本）。名字不在那四个里就抛 KeyError。"""
    if name not in PRESETS:
        raise KeyError('没有这一份预置输出：' + str(name))
    return copy.deepcopy(PRESETS[name])


# 下面这几个名字是**给判分与脚本读的**：四份预置输出各自的原文。
_SAMPLES = {
    '干净 JSON': CLEAN,
    '带围栏': FENCED,
    '带前言': PREFACED,
    '被截断': TRUNCATED,
}


def samples():
    """四份预置输出：{名字: 原文}（交回副本）。"""
    return copy.deepcopy(_SAMPLES)


def advice():
    """第二段那份预置推荐（模型建议的算法族），原文交回。"""
    return copy.deepcopy(MODEL_ADVICE)


def truncated():
    """「被截断」那一份的原文——它的开头与干净那份一致，但括号没闭合。"""
    return TRUNCATED


def looks_truncated(raw):
    """这一份文本是不是「被截断」：与预置的那一份对得上，而且括号不闭合。"""
    return is_truncated_preset(raw)
