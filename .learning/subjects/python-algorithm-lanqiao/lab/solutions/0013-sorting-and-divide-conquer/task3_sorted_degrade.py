"""任务 3 · 已有序数据上的退化 + 随机主元把它修回来

课件第三件事：把「已有序」那一组单独留出来，用**固定主元**的快排跑一次，
把 `RecursionError` 的现场抄下来；再换成**随机主元**跑，记下两次的差别。

这一课量这件事有个坑：**不能拿秒数当判据**。固定主元在有序数据上要撞上限、
随机主元不撞，秒数当然差得远；可秒数随机器浮动，同一份代码会时过时不过。
所以这一段判的全是确定量：

  1. **机制**：先把递归上限显式设成一个固定的数（LIMIT = 800），
     再判「固定主元在同一份已有序数据上会抛 RecursionError、随机主元不会」。
     不判一个写死的深度边界 —— 那个数随调用位置浮动，换台机器就不一样。
  2. **计数器上的退化**：固定主元在同一份数据上比了几次（n(n-1)/2）、
     划分了几次（n 次），都长到 n 那么大；随机主元那两个数只有 n log n 量级。
  3. **搬动方向相反**：有序数据上固定主元一次都不搬（没有元素比主元小），
     随机主元却要搬 2(n-1) 次。一个「算得多、动得少」，一个「算得少、动得多」。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。

跑： py task3_sorted_degrade.py
判： py run_tests.py
"""

import sys

from tools import (
    make_random, make_sorted, show,
    quicksort_ops_measured,
)

# 判分要把「撞上限」这件事变成确定的，所以上限是**显式设成的一个固定数**：
# 固定主元在已有序数据上要落 SIZE 层，这个上限必然撑不住；随机主元只落 30 多层。
LIMIT = 800
# 这一段用的规模：20000 层深足够把固定主元那一版真的顶爆（不是差一点点）。
SIZE = 20000


def ordered_data(n=SIZE):
    """本段要盯的那一份数据：已经排好序的（确定性生成，每次跑出来都一样）。"""
    return make_sorted(n)


def random_data(n=SIZE):
    """对照组：同样规模的随机数据，值域很大。"""
    return make_random(n)


# ══ TODO 1 ═════════════════════════════════════════════════
# 写 degrade_fixed(a, limit=LIMIT)：用**固定主元**快排跑一份数据，把代价数出来。
#
#   return quicksort_ops_measured(a, 'fixed', limit)
#
# 交回的那本字典里有五个格：
#   cmp    比较了几次        move  搬动了几次（交换一次算两个元素各动一次）
#   jobs   划分被调了几次     depth 要递归多深
#   error  报错类型名；没报错时是 None（撞了上限时 depth 会是 None）
#
# 在已有序数据上它会是什么样：主元每次落在端点，两边是「空的」与「剩下全部」，
# 划分次数与深度都长到 SIZE，比较次数是 SIZE*(SIZE-1)//2 —— 那一段能跑完二十万次
# 比较、但要落两万层，所以它必然撞上 LIMIT 那条上限。这正是 RecursionError 的来源。
def degrade_fixed(a, limit=LIMIT):
    return quicksort_ops_measured(a, 'fixed', limit)


# ══ TODO 2 ═════════════════════════════════════════════════
# 写 degrade_random(a, limit=LIMIT)：同一份数据、同一条上限，主元改成随机的。
#
#   return quicksort_ops_measured(a, 'random', limit)
#
# 同一个固定的上限下，它**不该**抛 RecursionError：随机主元让划分不容易总落在端点上，
# 期望深度回到 log n 量级。判分核的就是这个对照 —— 同一份数据、同一条上限，
# 一个爆、一个不爆，这才是「随机主元把退化修回来了」的证据。
def degrade_random(a, limit=LIMIT):
    return quicksort_ops_measured(a, 'random', limit)


# ══ TODO 3 ═════════════════════════════════════════════════
# 写 pivot_moves(a, mode)：数一份数据上「划分把元素搬了几次」。
#
#   return quicksort_ops_measured(a, mode, LIMIT)['move']
#
# mode 是 'fixed' 或 'random'。搬动就是一交换算两个元素各动一次。
# 在已有序数据上这两个数会给出方向完全相反的两个答案：
#   · 固定主元：主元就是这一段最小的那一个，一个元素都不小于它 → **一次都不搬**
#   · 随机主元：每一层都要把随机挑中的那一个换到开头 → 至少 2(SIZE-1) 次
# 一个算得多、动得少，一个算得少、动得多 —— 这一对数字合起来，才是退化这件事的全貌。
def pivot_moves(a, mode):
    return quicksort_ops_measured(a, mode, LIMIT)['move']


# ── 给好的部分：主块与打印（别改）───────────────────────────────────────
if __name__ == '__main__':
    print('任务 3 · 已有序数据上的退化 + 随机主元把它修回来')

    # 显式设成一个固定的上限：这样「撞不撞上限」只由代码与这份数据决定，与机器无关。
    sys.setrecursionlimit(LIMIT)

    ordered = ordered_data(SIZE)

    fixed = degrade_fixed(ordered, LIMIT)
    rand = degrade_random(ordered, LIMIT)

    show('深比较', 1, '固定主元', fixed['cmp'])
    show('深比较', 2, '随机主元', rand['cmp'])
    show('深搬动', 3, '固定主元', pivot_moves(ordered, 'fixed'))
    show('深搬动', 4, '随机主元', pivot_moves(ordered, 'random'))
    show('深划分', 5, '固定主元', fixed['jobs'])
    show('深划分', 6, '随机主元', rand['jobs'])

    # 有值就打印那个数；撞了上限就没有值可打印 —— 与下面打印的报错类型对得上，
    # 「报错类型 + 撞的时候数到的划分次数」合起来就是要抄下来的那个现场。
    show('深深度', 7, '固定主元', '撞上限' if fixed['depth'] is None else fixed['depth'])
    show('深深度', 8, '随机主元', '撞上限' if rand['depth'] is None else rand['depth'])

    for index, (name, one) in enumerate((('固定主元', fixed), ('随机主元', rand)), 1):
        if one['error'] is None:
            print('异常 ' + str(index).zfill(2) + ' ' + name + ' 已有序 n=' + str(SIZE)
                  + ' 未抛')
        else:
            print('异常 ' + str(index).zfill(2) + ' ' + name + ' 已有序 n=' + str(SIZE)
                  + ' ' + one['error'] + ' 撞时已划分 ' + str(one['jobs']) + ' 次')

    # ── 耗时（照打印，判分不读它；判的是上面那些次数与那段报错）──────────
    print('耗时 03 固定主元 已有序 n=' + str(SIZE) + ' 无法量（撞了递归上限）')
    print('耗时 04 随机主元 已有序 n=' + str(SIZE) + ' 也就几十毫秒（参考，判分不读）')
