"""任务 2 · 前缀和：把区间和变成两次取表相减

任务 1 的暴力版慢在「两个下标都要动」——区间个数本身就是 n 的平方那么多。
要把它降下来，得找一个只需要动一个下标的说法。

数列的前 i 项和叫**前缀和**，它的定义直接照字面写：

    pre[i] = a[0] + a[1] + ... + a[i-1],   pre[0] = 0

前 i 项和与「下标 i」的关系要看准：pre[i] 装的是 a[0] 到 a[i-1]。
这个约定多出了一个不装任何元素的 pre[0]，表的长度是 n + 1。

它的来历用递推式说清：

    pre[0] = 0,   pre[i] = pre[i-1] + a[i-1]

要让这个式子对 i = 0 也成立，就必须有 pre[0] = 0 这个起点。
于是区间 [l, r] 的和是：

    a[l] + ... + a[r] = pre[r+1] - pre[l]

两段前缀和相抵：pre[r+1] 比区间和多算了前 l 项，而 pre[l] 正好就是那多出来的前 l 项。
这个式子里 l 和 r 地位一样，l = 0 或 r = n-1 都不需要补特判。

接口：文件名、函数名、造数据那几行、带 print 的行都是判分接口，别改；
要写的是两个 TODO。

跑： py task2_prefix.py
判： py run_tests.py
"""

from task1_brute import count_brute
from tools import make_positive_array, make_mixed_array, show_count


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 build_pre(a)：照上面的约定建一张前缀和表，交回它。
#
# 要点：
#   pre = [0]                       先放好起点，这一位是「还没开始累加」
#   然后 for x in a:                 逐个元素往后接
#        pre.append(pre[-1] + x)     上一项加当前元素
#   交回的表长度是 len(a) + 1。
#   注意 pre[-1] 在这里是合法用法：Python 里它指「最后一个元素」，
#   也就是刚追加进去的那一项。
def build_pre(a):
    return [0]


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 count_prefix(a, S)：用前缀和加字典，一遍扫描数出答案。
#
# 把区间和公式代进「恰好等于 S」这个条件：
#     pre[r+1] - pre[l] = S   等价于   pre[l] = pre[r+1] - S
# S 是给定的、r 是正在扫到的位置，所以右边那个值完全确定：
# 要找的左端点 l，就是那些前缀和等于 pre[r+1] - S 的位置。
#
# 要点：
#   pre = build_pre(a)              先建表
#   seen = {0: 1}                   初值不能省（见下面的提示）
#   然后 for r in range(len(a)):
#        need = pre[r + 1] - S       这一步要找的值
#        count += seen.get(need, 0)  字典里记过几次，就说明有几个这样的 l
#        seen[pre[r + 1]] = seen.get(pre[r + 1], 0) + 1
#   最后 return count。
#
# 几处细节：
#   - seen 的键是「某个前缀和的值」、值是「它在此之前出现过几次」。
#   - 初值 {0: 1} 的含义是 pre[0] = 0 已经出现过一次，对应左端点 l = 0
#     （区间从数组开头算起）。少了这一项，所有从开头开始的区间都会漏掉。
#   - seen.get(need, 0) 在键不存在时给出 0，省掉一次判断。
#   - **每轮先查后记**。写反了，l = r + 1 这种空区间会被算进来。
def count_prefix(a, S):
    return 0


if __name__ == '__main__':
    SMALL = [4, 0, 0, 4, 0]                                  # 别改
    print('前缀和表', build_pre(SMALL))                        # 别改：期望 [0, 4, 4, 4, 8, 8]

    print('小数组', count_prefix(SMALL, 4))                    # 别改：期望 9
    print('与暴力一致', count_prefix(SMALL, 4) == count_brute(SMALL, 4))   # 别改：期望 True

    a1 = make_positive_array(2000)                           # 别改
    print('全正数 2000 个数', count_prefix(a1, 2000))          # 别改：期望 44

    a2 = make_mixed_array(300)                               # 别改
    print('含负数 300 个数', count_prefix(a2, 30))             # 别改：期望 106
    print('含负数时仍与暴力一致', count_prefix(a2, 30) == count_brute(a2, 30))   # 别改：期望 True

    # 单独取一段区间和，看公式怎么用（这一段是给好的，不用改）
    # 表还没建好时（留白版就是这样）下标会越界，这里接住它、打出「还没建好」，
    # 免得整份脚本在最后一行崩掉、前面已经填好的部分也看不到。
    pre = build_pre(a1)
    if len(pre) <= 101:
        print('区间和公式 还没建好：表长', len(pre))
        print('同一段逐项加', sum(a1[1:101]))                   # 别改：期望 4790
        print('公式与切片一致 还没建好')
    else:
        print('区间和公式', pre[101] - pre[1])                  # 别改：期望 4790
        print('同一段逐项加', sum(a1[1:101]))                   # 别改：期望 4790
        print('公式与切片一致', pre[101] - pre[1] == sum(a1[1:101]))   # 别改：期望 True

    show_count(2, '前缀和', count_prefix(SMALL, 4))            # 别改
