"""任务 4 · 对拍：同一批数据上三个版本答案对不对得上

三个版本到齐，接下来是拿它们互相验。做法是**对拍**：
暴力版是只有两层循环的直白实现，正确性一眼能看清，就用它当参照——
同一批随机数据上跑三个版本，看另外两个的答案与它对不对得上。

对拍是最省力的查错手段，也是第 8 课「先把暴力写对」那个用法的落点。

接口：文件名、函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是两个 TODO。

跑： py task4_compare.py
判： py run_tests.py
"""

from task1_brute import count_brute
from task2_prefix import count_prefix
from task3_window import count_window
from tools import make_positive_array, make_mixed_array, show_count


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 check_three(a, S)：把三个版本在同一批数据上各跑一次，
# 交回 (暴力, 前缀和, 双指针) 三个答案组成的元组。
#
# 要点：
#   return (count_brute(a, S), count_prefix(a, S), count_window(a, S))
# 一行就能写完——三个函数名已经 import 进来了。
def check_three(a, S):
    return (0, 0, 0)


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 find_counterexample(arrays, S)：在一批数组里找出**第一个**让
# 双指针版与暴力版答案不同的数组，交回那个数组（都一致就交回 None）。
#
# 要点：
#   for arr in arrays:
#       b = count_brute(arr, S)
#       w = count_window(arr, S)
#       if w != b:   return arr          找到就立刻交回
#   return None                          一个都没有
#
# 这一份是任务 5 的素材：任务 4 负责把它找出来，
# 有了具体的数组，才有可观察的反例可看。
def find_counterexample(arrays, S):
    return None


# 一组**确定性**的小数组（别改）：造出来就是为了让三版答案分岔
if __name__ == '__main__':
    CASES = [
        [4, 0, 0, 4, 0],
        [3, -1, 1],
        [5, -2, -2, 7],
        [-1, 3],
        [1, 2, 3, 4],
        [2, 2, 2],
        [10, -5, 5],
    ]

    print('小数组三版答案', check_three([4, 0, 0, 4, 0], 4))      # 别改：期望 (9, 9, 4)

    answer = 4
    arrays = []
    for t in CASES:                                          # 别改
        for s in range(-4, 8):
            arrays.append(t)

    found = find_counterexample(arrays, answer)              # 别改
    print('第一个反例', found)                                # 别改：期望 [4, 0, 0, 4, 0]
    if found is not None:
        print('反例上三版答案', check_three(found, answer))     # 别改：期望 (9, 9, 4)

    # 全为正数的数组上，三个版本应当始终一致（这一段是给好的，别改）
    agree = True
    for size in (50, 120, 300):
        arr = make_positive_array(size)
        got = check_three(arr, size)
        if not (got[0] == got[1] == got[2]):
            agree = False
    print('全正数上三版始终一致', agree)                        # 别改：期望 True

    # 含负数的数组上，双指针版会分岔（这一段也是给好的，别改）
    a2 = make_mixed_array(300)
    print('含负数上的三版答案', check_three(a2, 30))           # 别改：期望 (106, 106, 4)

    show_count(5, '反例总数', sum(1 for s in range(-4, 8)
                                  if count_window([4, 0, 0, 4, 0], s) != count_brute([4, 0, 0, 4, 0], s)))
