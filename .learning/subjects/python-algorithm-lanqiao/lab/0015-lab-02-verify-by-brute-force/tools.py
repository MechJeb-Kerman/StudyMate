"""tools.py · lab 0015 的公共工具（给好的，别改）

这里放五样东西，五个任务都从这里取：

  1. match_found(value, index)
     把「找到了」与「没找到」两种写法归成同一个数，用来核对你算出来的下标：
         -1 与 None 都算「没找到」→ 归成 -1；
         别的整数（含 0）→ 原样交回。
     归成同一个数是为了让下面这条判据成立：一个函数拿它当候选、又拿它当参照，
     两边得到的永远是同一个数，对拍不该报任何不一致。

  2. as_lists(candidate, reference, a, x)
     跑一次两边、把结果归成两个数 → (候选, 参照)。对拍、缩小、自检都用它。

  3. labels(rows) / is_one_row(row)
     把 stress 交回来的一组（或一组组）「第几次 + 那组数据 + 两个答案」排成固定格式的
     文本行，判分按行读这几行。格式就是课件「一个真跑出来的例子」那一行：
         第 2 次抓到：a=[63, 97] x=97 候选=-1 参照=1
     交回 None（一次都没抓到）时给一行说明。

  4. show_count(index, label, value) / show_pairs(index, label, rows)
     打印固定格式的判分行，判分按编号取。
         计数 NN <标签> <值>
         对 NN <标签> <组数>
     例： 计数 01 种子 1 抓到 2
          对 01 空数组 0

  5. load_buggy()
     读出 buggy.py 的源码行（从 1 开始数）→ 一张表，第 i 项是第 i 行。
     任务 5 要用它把「哪一行错了」打印成行号，别自己去数。

判分不 import 这份文件里任何「学生的实现」——它只 import 你自己的 stress.py、
再拿这里的工具核对结果。留白版原样跑时，计数行会打出占位值、对拍行会报
「还没抓到」——那是起点，不是 bug。
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))


# ── 1. 两种「没找到」的写法归成一个数 ────────────────────────────────────

def match_found(value, index):
    """把找到的下标或「没找到」归成同一个数：-1 与 None 都算没找到。"""
    if value is None:
        return -1
    if isinstance(value, int) and not isinstance(value, bool) and value == -1:
        return -1
    return value


# ── 2. 跑一次两边 ────────────────────────────────────────────────────────

def as_lists(candidate, reference, a, x):
    """跑一次候选解与参照解，把两个结果归成 (候选, 参照) 两个数。"""
    got = match_found(candidate(list(a), x), a)
    want = match_found(reference(list(a), x), a)
    return got, want


# ── 3. 固定格式的文本行 ──────────────────────────────────────────────────

def _one_row(prefix, data, x, got, want):
    return (prefix + '：a=' + repr(list(data)) + ' x=' + repr(x)
            + ' 候选=' + repr(got) + ' 参照=' + repr(want))


def is_one_row(row):
    """这一组是不是「第几次 + 那组数据 + 两个答案」的五元组。"""
    return (isinstance(row, tuple) and len(row) == 5
            and isinstance(row[1], list) and isinstance(row[2], int))


def labels(rows):
    """把 stress 的返回值排成要打印的文本行。

    交回 None（一次都没抓到）→ 一行说明；交回一组五元组 → 那一行；
    交回一组组五元组 → 每行一组的汇总。
    """
    if rows is None:
        return ['还没抓到：stress 交回 None（要么真的一次都没抓到，要么它还没在比对）']
    if is_one_row(rows):
        rows = [rows]
    if not rows:
        return ['（这一轮一组都没跑）']
    if len(rows) == 1:
        trial, data, x, got, want = rows[0]
        return [_one_row('第 ' + str(trial) + ' 次抓到', data, x, got, want)]
    return [str(len(rows)) + ' 组不一致：'
            + '、'.join('第 ' + str(trial) + ' 次 a=' + repr(list(data)) + ' x=' + repr(x)
                        + ' 候选=' + repr(got) + ' 参照=' + repr(want)
                        for trial, data, x, got, want in rows)]


# ── 4. 判分读的打印行 ────────────────────────────────────────────────────

def show_count(index, label, value):
    """打印一行计数。index 是两位编号，label 是中文标签。"""
    print('计数 ' + str(index).zfill(2) + ' ' + label + ' ' + str(value))


def show_pairs(index, label, rows):
    """打印一行「对拍/形态」统计：对 NN <标签> <值>。"""
    if rows is None:
        text = '还没数'
    else:
        text = str(len(rows))
    print('对 ' + str(index).zfill(2) + ' ' + label + ' ' + text)


# ── 5. 读 buggy.py 的源码行 ──────────────────────────────────────────────

def load_buggy():
    """把 buggy.py 的每一行读成一张表（第 1 项是第 1 行）。找不到文件交回 []。"""
    path = os.path.join(HERE, 'buggy.py')
    if not os.path.isfile(path):
        return []
    with open(path, encoding='utf-8') as handle:
        return handle.read().splitlines()
