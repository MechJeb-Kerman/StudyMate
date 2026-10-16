"""probes/probe_task1.py · 任务 1 的判分探针（给好的，别改）

判分脚本另起一个进程跑这个文件：它 import 你的 task1_two_sum_sorted.py，
拿一组**判分自己的**小数据去试两个函数（含空数组、单个元素、两个相同的数、负数、
无解的那一组），以及三组规模上对撞版与暴力版是否一致。

最后一行以 PROBE 开头，后面是 JSON——判分脚本读的就是它。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import task1_two_sum_sorted as t
from tools import make_sorted_unique

cases = []
groups = [
    ([], 5), ([7], 14), ([3, 3], 6), ([-5, -1, 0, 2], -6),
    ([1, 4, 5, 9, 11], 10), ([1, 4, 5, 9, 11], 100), ([0, 0, 0], 0),
    ([2, 7, 11, 15], 9), ([1, 2, 3, 4, 5, 6], 11), ([1, 1, 1, 1], 2),
]
for arr, target in groups:
    cases.append([str(arr) + ' / ' + str(target),
                  t.two_sum_sorted(list(arr), target),
                  t.two_sum_brute(list(arr), target)])

scales = []
for n in [20, 200, 2000]:
    arr = make_sorted_unique(n)
    target = arr[n - 2] + arr[n - 1]
    scales.append([n, t.two_sum_sorted(arr, target), t.two_sum_brute(arr, target)])

print('PROBE ' + json.dumps([cases, scales], ensure_ascii=False))
