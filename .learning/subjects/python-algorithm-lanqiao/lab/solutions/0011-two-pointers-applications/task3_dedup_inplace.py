"""任务 3 · 原地去重：快慢指针，一读一写

题目：数组已经排好序，把重复的值去掉、只留每个值一次，**不使用额外空间**，
函数交回去重后剩下的元素个数 k（只保证 a[:k] 是答案，a[k:] 里的旧值不用管）。

现成的删除操作（`remove` / `del`）都要把后面的元素整体往前搬一格，第 3 课的价格表里
那是 O(n)；删 k 个重复值就是 O(kn)，n = 10^5 时这条路走不通。

快慢指针把「找到重复」与「搬动元素」合成一趟扫描，两个下标的职责分得很清楚：

    fast 是**读位置**：从 1 开始，每轮往右走一格，保证 a[fast] 左边的每个位置都看过了；
    slow 是**写位置**：指向已经整理好的那一段的最后一个元素，
                    保证 [0, slow] 里的值互不相同、且相对顺序与原来一致。

判断规则只有一条：a[fast] 与 a[slow] 相同时这个值是重复的、丢掉；不同时它是第一个出现的值、
必须留下——**先把 slow 往前挪一格，再把 a[fast] 写到新的 a[slow] 上**。
这两步的先后顺序不能换：先写再挪，会把已整理部分的最后一个值覆盖掉。

接口：函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 两段（第二段是注释）。

跑： py task3_dedup_inplace.py
判： py run_tests.py
"""

from tools import make_sorted_with_dups, show_count


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 dedup_sorted(a)：有序数组原地去重，交回剩下的元素个数 k。
#
# 要点（这一课最要紧的几行，一行都不要少）：
#   if len(a) == 0:  return 0              空数组直接交回 0（不然 a[0] 会报错）
#   slow = 0                               已整理好的那一段的**最后一个**下标
#   for fast in range(1, len(a)):          读位置从 1 开始
#       if a[fast] != a[slow]:             与已整理部分的最后一个值不同 → 是新的值
#           slow += 1                      先挪写位置
#           a[slow] = a[fast]              再写进去（两步不能换顺序）
#   return slow + 1                        个数 = 最后一个有效下标 + 1
#
# 把 slow += 1 删掉的后果，课件里量过：[1, 1, 2, 3, 3, 5] 上它交回 1、
# 而数组被写成 [5, 1, 2, 3, 3, 5]。原因是所有值都往 a[0] 上写，
# 第 3 轮把 3 写进 a[0] 之后，第 4 轮再读 a[slow] 读到的就是自己刚写下去的那个 3。
def dedup_sorted(a):
    if len(a) == 0:
        return 0
    slow = 0                        # 已整理好的那一段的最后一个下标（写位置）
    for fast in range(1, len(a)):   # 读位置
        if a[fast] != a[slow]:
            slow += 1               # 先挪写位置
            a[slow] = a[fast]       # 再写进去
    return slow + 1


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 dedup_forget_write(a)：**故意的错版**——与上面只差一行：不写 slow += 1，
# slow 一直停在 0，所有不同的值都往 a[0] 上写。
#
# 要点：把它整段照抄，只把 `slow += 1` 那一行删掉。
#   它交回的是 1（只有一个「有效」元素），数组也被写花——这两个错互相解释，
#   任务文件下面的输出就是让你看这一组数字。
def dedup_forget_write(a):
    if len(a) == 0:
        return 0
    slow = 0
    for fast in range(1, len(a)):
        if a[fast] != a[slow]:
            a[slow] = a[fast]       # 故意漏掉 slow += 1：所有值都往 a[0] 上写
    return slow + 1


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声
    b = [1, 1, 2, 3, 3, 5]                     # 别改：课件那一组
    k = dedup_sorted(b)                        # 别改
    print('课件数据 个数', k)                                     # 别改：期望 4
    print('课件数据 前 k 项', b[:k])                              # 别改：期望 [1, 2, 3, 5]
    print('课件数据 整个数组', b)                                  # 别改：期望 [1, 2, 3, 5, 3, 5]（前 k 项有效）

    d = [1, 1, 2, 3, 3, 5]                     # 别改：同一组数据给错版单独用一份
    k_bad = dedup_forget_write(d)              # 别改
    print('错版 个数', k_bad)                                     # 别改：期望 1
    print('错版 整个数组', d)                                     # 别改：期望 [5, 1, 2, 3, 3, 5]

    # 边界：空数组、只有一个元素、全部相同
    edges = [[], [7], [4, 4, 4, 4]]            # 别改
    edge_rows = []                             # 别改
    for arr in edges:                          # 别改
        copy = arr[:]                          # 别改
        cnt = dedup_sorted(copy)               # 别改
        edge_rows.append((arr, cnt, copy[:cnt]))     # 别改
        print('边界', arr, '个数', cnt, '前 k 项', copy[:cnt])       # 别改

    print('空数组交回 0', edge_rows[0][1] == 0)                   # 别改：期望 True
    print('单个元素交回 1', edge_rows[1][1] == 1)                  # 别改：期望 True
    print('全部相同交回 1', edge_rows[2][1] == 1)                  # 别改：期望 True

    # 三组数据上：交回的个数与「去重后的内容」都要对
    cases = [[1, 1, 2, 3, 3, 5], [1, 2, 3, 4], [2, 2, 2, 2, 3, 3, 5, 5, 5, 9]]    # 别改
    want = [[1, 2, 3, 5], [1, 2, 3, 4], [2, 3, 5, 9]]                            # 别改：期望的前 k 项
    ok_count = 0                               # 别改
    for i in range(len(cases)):                # 别改
        arr = cases[i][:]                      # 别改
        cnt = dedup_sorted(arr)                # 别改
        good = (cnt == len(want[i])) and (arr[:cnt] == want[i])     # 别改
        if good:                               # 别改
            ok_count += 1                      # 别改
        print('数据', cases[i], '个数', cnt, '前 k 项', arr[:cnt], '对', good)   # 别改

    print('三组数据全部正确', ok_count == 3)                       # 别改：期望 True

    # 大一点的数据：20000 个数（约三分之一重复），看个数对不对
    big = make_sorted_with_dups(20000)         # 别改
    printed = 0                                # 别改
    last = None                                # 别改
    for x in big:                              # 别改
        if x != last:                          # 别改
            printed += 1                       # 别改
            last = x                           # 别改
    k_big = dedup_sorted(big)                  # 别改
    print('20000 个数 去重后个数', k_big, '参照个数', printed)      # 别改：两者应当相同
    print('20000 个数 前后两项', big[:2], big[k_big - 2:k_big])    # 别改：期望 [5, 8] [20096, 20101]

    show_count(1, '课件数据个数', k)                               # 别改：期望 4
    show_count(2, '课件数据前 k 项', b[:k] == [1, 2, 3, 5])         # 别改：期望 True
    show_count(3, '错版个数', k_bad)                               # 别改：期望 1
    show_count(4, '三组数据正确个数', ok_count)                     # 别改：期望 3
    show_count(5, '20000 个数个数一致', k_big == printed)           # 别改：期望 True
