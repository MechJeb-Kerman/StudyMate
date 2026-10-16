"""probes/probe_task5.py · 任务 5 的判分探针（给好的，别改）

判分脚本另起一个进程跑这个文件：它 import 你的 task5_merge_sorted.py，
拿一组**判分自己的**数据去试三个函数——

    · merge_sorted      五组（含空数组、一边为空、全是同一个值）结果必须与 sorted(a + b) 一致；
    · merge_into        原地合并的三组（b 比空位短、正好一样长、比空位长则按题目只要求
                        能装下的部分），比对合并后的整个数组；
    · merge_sorted_short 前 k 项：k 小于、等于、大于两个数组总长三种情形。

这样查是因为三个函数都可能在**课件的样例上碰巧对**：只看样例看不出
「收尾的那两个 while 漏了一个」「从后往前写成了从前往后」这类问题。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import task5_merge_sorted as t

merged = []
for a, b in [([], []), ([1], []), ([], [1]), ([5, 5, 5], [5, 5]),
             ([-3, 0, 4], [-2, 0, 9]), ([1, 3, 5, 7, 9], [2, 4])]:
    got = t.merge_sorted(list(a), list(b))
    merged.append([str(a) + ' + ' + str(b), got, sorted(a + b)])

inplace = []
for base, m, b in [([1, 4, 7, 0, 0, 0], 3, [2, 5, 6]),
                   ([1, 2, 3, 0, 0], 3, [0, 4]),
                   ([2, 3, 0, 0, 0], 2, [1, 2, 3]),
                   ([4, 5, 6, 0, 0, 0, 0], 3, [1, 2, 3, 7])]:
    arr = list(base)
    t.merge_into(arr, m, list(b))
    inplace.append([str(base) + ' <- ' + str(b), arr, sorted(base[:m] + b)])

short = []
for a, b, k in [([1, 4, 5, 9, 11], [2, 3, 8], 3),
                ([1, 4, 5, 9, 11], [2, 3, 8], 10),
                ([1, 4, 5, 9, 11], [2, 3, 8], 0),
                ([], [2, 3], 1)]:
    got = t.merge_sorted_short(list(a), list(b), k)
    short.append([str(a) + ' + ' + str(b) + ' k=' + str(k), got, sorted(a + b)[:k]])

print('PROBE ' + json.dumps([merged, inplace, short], ensure_ascii=False))
