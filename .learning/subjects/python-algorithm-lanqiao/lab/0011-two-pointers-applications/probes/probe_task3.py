"""probes/probe_task3.py · 任务 3 的判分探针（给好的，别改）

判分脚本另起一个进程跑这个文件：它 import 你的 task3_dedup_inplace.py，
拿一组**判分自己的**数据去试原地去重：每一步都要看两件事——
交回的个数 k 对不对，以及**前 k 项**是不是去重后的结果。

原地改写的函数没法只看返回值：返回值是「个数」，内容在数组里。所以这里每组都
打印 (k, a[:k])，两段都要对上才算过。五组里有一组是空数组（交回 0、数组还是空的）。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import task3_dedup_inplace as t

cases = []
groups = [
    ([1, 1, 2, 3, 3, 5], [1, 2, 3, 5]),
    ([1, 1, 1, 1], [1]),
    ([1, 2, 3], [1, 2, 3]),
    ([], []),
    ([7], [7]),
    ([-3, -3, -1, 0, 0, 0], [-3, -1, 0]),
]
for data, want in groups:
    arr = list(data)
    k = t.dedup_sorted(arr)
    cases.append([str(data), k, arr[:k] if isinstance(k, int) and k >= 0 else None, want])

bad_arr = [1, 1, 2, 3, 3, 5]
k_bad = t.dedup_forget_write(bad_arr)
cases.append(['错版 ' + str([1, 1, 2, 3, 3, 5]), k_bad, bad_arr, 'expect-1-and-written-over'])

print('PROBE ' + json.dumps(cases, ensure_ascii=False))
