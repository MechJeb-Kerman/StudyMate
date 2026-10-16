"""任务 2 · 递归返回值汇总子树信息：节点数、树高、对称性

课件「递归返回值汇总子树」那一节：树函数的通用写法是**在每个结点上，
用两个孩子交回的答案算出自己的答案**。这一份的四个函数都是这个形状：

    count(t)        空树交回 0；否则 1 + count(左) + count(右)
    height(t)       空树交回 0；否则 1 + max(height(左), height(右))
                    注意口径：树高 = 层数，单点树的高度是 1，空树是 0
    is_mirror(a, b) 问「以 a 为根的子树与以 b 为根的子树是否互为镜像」
    is_symmetric(t) 空树与单点树都算对称；否则问 is_mirror(t[1], t[2])

is_mirror 的四个分支一个都不能少（都空 → True；只有一个空 → False；
都非空 → 比值 + 两个递归），两个递归调用的参数是**左对右、右对左**：
is_mirror(a[1], b[2]) 与 is_mirror(a[2], b[1])。写成 a[1] 对 b[1] 判的就不是
「对称」而是「两棵子树一模一样」，例子里的镜像树会当场判错。

这一份的输出是一张表：五种数据 × 四列（节点数、树高、对称、镜像）。
最后两行是给好的，拿两个树对象直接问 is_mirror。

接口：文件名、函数名、造树那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那几段。

跑： py task2_tree_stats.py
判： py run_tests.py
"""

from tools import node

# ── 给好的部分：五种数据（别改）──────────────────────────────
# 课件那棵示例树
T = node('A', node('B', node('D'), node('E')), node('C', None, node('F')))

# 课件那棵对称树：A 的左右两棵子树互为镜像
S = node('A', node('B', node('D')), node('B', None, node('D')))

# 给好的「只差一个值」的镜像对：形状完全一样，只有一片叶子的值不同
M1 = node('A', node('B', node('D')), node('B', node('D')))
M2 = node('A', node('B', node('D')), node('B', node('E')))


# ══ TODO 1 ═════════════════════════════════════════════════
# 补 count(t)：这棵子树有多少个结点。空树 0，否则 1 + 两个孩子交回的个数。
def count(t):
    # TODO 1
    return 0


# ══ TODO 2 ═════════════════════════════════════════════════
# 补 height(t)：这棵子树有多高（= 层数）。空树 0，否则 1 + 两个孩子里较大的那个。
# 单点树的高度是 1；示例树的高度是 3（A 一层、B/C 一层、D/E/F 一层）。
def height(t):
    # TODO 2
    return 0


# ══ TODO 3 ═════════════════════════════════════════════════
# 补 is_mirror(a, b)：两棵子树是否互为镜像。四个分支按顺序写：
#   a is None and b is None → True（两边都空）
#   a is None or  b is None → False（一边空一边不空；漏掉这一句就会去取 None[0] 而报错）
#   再比值：a[0] == b[0]，并且左对右、右对左两个递归都为真
def is_mirror(a, b):
    # TODO 3
    return False


# ══ TODO 4 ═════════════════════════════════════════════════
# 补 is_symmetric(t)：整棵树是否左右对称。
#   空树算对称（交回 True）；否则把两个孩子交给 is_mirror。
#   单点树的左右孩子都是 None，交给 is_mirror 也会得到 True。
def is_symmetric(t):
    # TODO 4
    return False


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声
    # ── 五种数据 × 四列，做成一张表（这几行别改）─────────────────
    rows = [('空树', None), ('单点', node('A')), ('对称树', S), ('示例树', T), ('只差一个值', M1)]   # 别改
    print('数据 节点数 树高 对称')                                        # 别改
    for name, t in rows:                       # 别改
        print(name, count(t), height(t), is_symmetric(t))              # 别改

    print()                                    # 别改
    print('镜像对 是不是镜像', is_mirror(M1, M2))                          # 别改：期望 False
    print('镜像树 自己是自己的镜像', is_mirror(S[1], S[2]))                # 别改：期望 True
    print('示例树 两棵子树是不是镜像', is_mirror(T[1], T[2]))              # 别改：期望 False
