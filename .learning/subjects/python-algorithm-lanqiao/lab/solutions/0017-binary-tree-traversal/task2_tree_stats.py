"""任务 2 · 递归返回值汇总子树信息：节点数、树高、对称性

参考解。与任务目录里的同名文件只差标着 TODO 的四段。

课件「递归返回值汇总子树」那一节：树函数的通用写法是**在每个结点上，
用两个孩子交回的答案算出自己的答案**。

    count(t)        空树 0；否则 1 + count(左) + count(右)
    height(t)       空树 0；否则 1 + max(height(左), height(右))
                    口径：树高 = 层数，单点树是 1，空树是 0
    is_mirror(a, b) 四个分支：都空 True、只有一个空 False、比值 + 左对右两个递归
    is_symmetric(t) 空树与单点树都算对称；否则问 is_mirror(t[1], t[2])

is_mirror 里两个递归调用的参数是**左对右、右对左**：is_mirror(a[1], b[2]) 与
is_mirror(a[2], b[1])。写成 a[1] 对 b[1] 判的就不是「对称」而是「两棵子树一模一样」，
例子里的 M1 / M2 会当场判错（它们形状相同，但互为镜像才怪）。

接口：文件名、函数名、造树那几行、带 print 的行都是判分接口，别改。

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
def count(t):
    """这棵子树有多少个结点。"""
    if t is None:
        return 0
    return 1 + count(t[1]) + count(t[2])


# ══ TODO 2 ═════════════════════════════════════════════════
def height(t):
    """这棵子树有多高（= 层数）。空树 0，单点 1。"""
    if t is None:
        return 0
    return 1 + max(height(t[1]), height(t[2]))


# ══ TODO 3 ═════════════════════════════════════════════════
def is_mirror(a, b):
    """以 a 为根的子树与以 b 为根的子树是否互为镜像。"""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return a[0] == b[0] and is_mirror(a[1], b[2]) and is_mirror(a[2], b[1])


# ══ TODO 4 ═════════════════════════════════════════════════
def is_symmetric(t):
    """整棵树是否左右对称。空树与单点树都算对称。"""
    return t is None or is_mirror(t[1], t[2])


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
