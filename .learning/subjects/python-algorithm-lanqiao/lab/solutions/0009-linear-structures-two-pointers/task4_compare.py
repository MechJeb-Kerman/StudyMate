"""任务 4 · 对拍（参考解）"""

from task1_brute import count_brute
from task2_prefix import count_prefix
from task3_window import count_window
from tools import make_positive_array, make_mixed_array, show_count


def check_three(a, S):
    return (count_brute(a, S), count_prefix(a, S), count_window(a, S))


def find_counterexample(arrays, S):
    for arr in arrays:
        b = count_brute(arr, S)
        w = count_window(arr, S)
        if w != b:
            return arr
    return None


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

    print('小数组三版答案', check_three([4, 0, 0, 4, 0], 4))

    answer = 4
    arrays = []
    for t in CASES:
        for s in range(-4, 8):
            arrays.append(t)

    found = find_counterexample(arrays, answer)
    print('第一个反例', found)
    if found is not None:
        print('反例上三版答案', check_three(found, answer))

    agree = True
    for size in (50, 120, 300):
        arr = make_positive_array(size)
        got = check_three(arr, size)
        if not (got[0] == got[1] == got[2]):
            agree = False
    print('全正数上三版始终一致', agree)

    a2 = make_mixed_array(300)
    print('含负数上的三版答案', check_three(a2, 30))

    show_count(5, '反例总数', sum(1 for s in range(-4, 8)
                                  if count_window([4, 0, 0, 4, 0], s) != count_brute([4, 0, 0, 4, 0], s)))
