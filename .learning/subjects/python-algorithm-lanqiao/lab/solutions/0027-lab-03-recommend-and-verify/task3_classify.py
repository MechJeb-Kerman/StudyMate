"""任务 3 · 关键词打分：题面映射到算法族（lab 0027）· 参考解

这一段**完全不靠模型**：拿题面里的关键词，给每个算法族打分。它不是主力，是**交叉检查**——
模型给了一个结论，关键词表给不出任何支持，就值得警惕。

它的定位要说准：

  · 它是**提示**，不是**判决**；
  · 它给出的是**排序的候选**，不是唯一答案；
  · 它最可靠的用法是当交叉检查。

所以交回的是排好序的候选列表。排序口径两级：先按命中数降序，再按族名字典序升序。

关键词表有一个必须**如实保留**的现象：假阳性。「合并果子」正确答案是堆，
但题面里有「重量」两个字，于是背包也以 1 个命中并列出现：

    题面「合并果子」首选 堆（命中 1 个：['每次取最小']）
         并列 背包（命中 1 个：['重量']）

**不许藏**：把「重量」从表里删掉、或者给堆加几个词把它顶下去，这一行的并列就没了，
而那正是这一段要暴露的东西——所以判分拿同一张表的另一个实现对拍。
表就是 tools.FAMILIES，逐字用它，别自己另写一份。

跑： py task3_classify.py
判： py run_tests.py
"""

from tools import (FAMILIES, PROBLEMS, canonical_scores, clamp, show_banner, show_line)


def classify(text):
    """按关键词命中数给算法族打分，交回排好序的候选 [(命中数, 族名, 命中词表), ...]。"""
    scores = []
    for family, keys in FAMILIES:
        hit = [k for k in keys if k in text]
        if hit:
            scores.append((len(hit), family, hit))
    scores.sort(key=lambda row: (-row[0], row[1]))
    return scores


def explain_problems():
    """六道题面各跑一遍 classify、逐条打印，交回 {题面名: 候选列表}。"""
    table = {}
    for title, text in PROBLEMS.items():
        got = classify(text)
        table[title] = got
        if not got:
            print('题面「' + title + '」：一个都没命中')
            continue
        hit, family, keys = got[0]
        print('题面「' + title + '」首选 ' + family + '（命中 ' + str(hit) + ' 个：'
              + repr(keys) + '）')
        if len(got) > 1:
            hit2, family2, keys2 = got[1]
            mark = '并列' if hit2 == hit else '次选'
            print('    ' + mark + ' ' + family2 + '（命中 ' + str(hit2) + ' 个：'
                  + repr(keys2) + '）')
    return table


def tied_rows(rows):
    """把候选表里与首选同分的那几个挑出来。"""
    if not rows:
        return []
    return [row for row in rows[1:] if row[0] == rows[0][0]]


if __name__ == '__main__':
    show_banner('0027 六道题面各跑一遍')
    got = explain_problems()

    show_banner('0027 假阳性：合并果子那一行的并列')
    merge = classify(PROBLEMS['合并果子'])
    show_line('首选', merge[0][1])
    show_line('首选命中数', merge[0][0])
    tied = tied_rows(merge)
    show_line('并列的族', '、'.join(row[1] for row in tied) if tied else '（没有并列）')
    for row in tied:
        show_line('并列族 ' + row[1] + ' 命中', '、'.join(row[2]))
    show_line('候选数', len(merge))

    show_banner('0027 族名表与判分用的是同一张')
    show_line('族名表大小', len(FAMILIES))
    show_line('木材加工候选数', len(classify(PROBLEMS['木材加工'])))
    show_line('区间调度候选数', len(classify(PROBLEMS['区间调度'])))
    island = classify(PROBLEMS['岛屿数量'])
    show_line('岛屿数量首选', island[0][1] if island else '（一个都没命中）')
