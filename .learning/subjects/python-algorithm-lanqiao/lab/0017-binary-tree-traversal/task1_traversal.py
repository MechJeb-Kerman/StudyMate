"""任务 1 · 四种遍历：三个递归版 + 一个队列版

这一课的表示约定（课件「用嵌套列表表示树」那一节）：

    空树用 None 表示；
    一个结点写成 [值, 左子树, 右子树]，由 tools.py 的 node(v, l, r) 搭出来。

这一份要写四个函数：preorder / inorder / postorder / level_order。

四个都用**累加器**写法，不是拼接写法：

    拼接版：  return [t[0]] + preorder(t[1]) + preorder(t[2])
    累加器版：out.append(t[0]); 再递归进两个孩子; 最后 return out

累加器版的签名是 (t, out=None)：out 是收结果的列表，第一层不给就自己新建一个。
out=None 写在默认值上，所以下面那些 `preorder(T)` 的调用照样能用。
理由在课件「拼接结果的隐藏代价」那一节：拼接版每层都要复制一遍子树的结果，
链状树上的代价是平方级；任务 4 会把两个版本放在一起量给你看。

层序遍历不能用递归（它是「一层一层」的走法），要用第 10 课的队列：
collections.deque 的 append 进队、popleft 出队，队列里存的是**子树**而不是单个值。

接口：文件名、函数名、造树那几行、带 print 的行都是判分接口，别改；
要写的是标着 TODO 的那几段。

跑： py task1_traversal.py
判： py run_tests.py
"""

from collections import deque

from tools import node, show_count

# ── 给好的部分：课件那棵示例树（别改）────────────────────────
#        A
#      /   \
#     B     C
#    / \     \
#   D   E     F
T = node('A', node('B', node('D'), node('E')), node('C', None, node('F')))

# 另一棵给好的树：每个结点都挂满两个孩子，四层共 15 个结点
B15 = node(1,
           node(2, node(4, node(8), node(9)), node(5, node(10), node(11))),
           node(3, node(6, node(12), node(13)), node(7, node(14), node(15))))


# ══ TODO 1 ═════════════════════════════════════════════════
# 补 preorder(t, out=None)：前序 = 根 → 左子树 → 右子树。
#   第一句永远是基例：if t is None: return out（空树直接交回 out，什么也不收）；
#   然后 out.append(t[0]) 把根的值收进去，再依次递归左孩子、右孩子，最后 return out。
#   漏掉基例的后果在课件里写过：走到叶子那个不存在的孩子时会去执行 None[0]，
#   报 TypeError: 'NoneType' object is not subscriptable。
def preorder(t, out=None):
    # TODO 1
    if out is None:
        out = []
    return out


# ══ TODO 2 ═════════════════════════════════════════════════
# 补 inorder(t, out=None)：中序 = 左子树 → 根 → 右子树。
#   与 TODO 1 只差一句话的位置：递归左孩子、append 根、递归右孩子。
def inorder(t, out=None):
    # TODO 2
    if out is None:
        out = []
    return out


# ══ TODO 3 ═════════════════════════════════════════════════
# 补 postorder(t, out=None)：后序 = 左子树 → 右子树 → 根。
#   先递归两个孩子、最后 append 根。
def postorder(t, out=None):
    # TODO 3
    if out is None:
        out = []
    return out


# ══ TODO 4 ═════════════════════════════════════════════════
# 补 level_order(t)：层序遍历，一层一层从左到右。
#   空树交回 []；否则 q = deque([t])，然后 while q：
#     x = q.popleft()；把 x[0] 收进 out；
#     x[1] is not None 就 q.append(x[1])，x[2] is not None 就 q.append(x[2])。
#   注意比较写 is not None，不要写 if x[1]——值是 0 或 '' 时那种写法会漏结点。
def level_order(t):
    # TODO 4
    return []


# ══ TODO 5、TODO 6 ═════════════════════════════════════════
# 照示例树的样子再搭两棵树（都用给好的 node）：
#   TODO 5 · CHAIN5：链状树，只有左孩子，一直往下五层，值依次 1 2 3 4 5。
#              搭出来是 node(1, node(2, node(3, node(4, node(5)))))，别补右孩子。
#   TODO 6 · BAL5：平衡树，四层都挂满、共 15 个结点，值按层从上到下、从左到右编号：
#              第 1 层 1；第 2 层 2 3；第 3 层 4 5 6 7；第 4 层 8 9 10 11 12 13 14 15。
#              （给好的 B15 就是这个编号，照它再写一棵即可。）
CHAIN5 = None
BAL5 = None


if __name__ == '__main__':                     # 别改：这层守卫让判分 import 它时不出声
    trees = [('示例树', T), ('链状树', CHAIN5), ('平衡树', BAL5)]      # 别改

    for i, pair in enumerate(trees):            # 别改
        name, t = pair                         # 别改
        print(name, '前序', preorder(t))                       # 别改：期望与课件逐字一致
        print(name, '中序', inorder(t))                        # 别改
        print(name, '后序', postorder(t))                      # 别改
        print(name, '层序', level_order(t))                    # 别改
        show_count(i + 1, name + ' 前序', len(preorder(t)))     # 别改
        print()                                # 别改

    # 课件那三行，逐字对照（别改）
    print('课件 前序', ['A', 'B', 'D', 'E', 'C', 'F'])             # 别改
    print('课件 中序', ['D', 'B', 'E', 'A', 'C', 'F'])             # 别改
    print('课件 后序', ['D', 'E', 'B', 'F', 'C', 'A'])             # 别改
    print('课件 层序', ['A', 'B', 'C', 'D', 'E', 'F'])             # 别改

    # 边界：空树与单点树各跑一遍（别改，判分按这两行看基例）
    print('空树 四种', preorder(None), inorder(None), postorder(None), level_order(None))   # 别改
    print('单点 四种', preorder(node('A')), inorder(node('A')),
          postorder(node('A')), level_order(node('A')))                                     # 别改
