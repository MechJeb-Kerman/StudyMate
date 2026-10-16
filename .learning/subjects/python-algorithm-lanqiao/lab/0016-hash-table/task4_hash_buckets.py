"""任务 4 · 手工算一遍哈希值与桶号：冲突是怎么发生的

目标：拿七个字符串，自己算出「哈希值 → 桶号」，数一数有几个桶装了不止一个键；
再换成 16 个桶跑一遍，看冲突是变少还是消失。最后把「哈希值每次运行都不一样」的原因写一句。

桶号 = hash(键) % 桶数。课件里那张自己实现的表就是这么落位的。

这一份**要自己跑两遍**，对比两次的输出：

  py task4_hash_buckets.py          # 第一遍，把看到的哈希值记下来
  py task4_hash_buckets.py          # 第二遍，同样的键，哈希值不一样了

会看到：**哈希值跨进程变了，桶号也跟着变**——桶号是哈希值对桶数取余，哈希值一换它自然换。
变的只是「落到哪个桶」，**冲突有没有、有几个桶装了不止一个键**这件事就不好说了，
所以判分不跨进程比桶号，只看每一次运行内部「桶号 = 哈希值 % 桶数」成立，
以及哈希值跨进程确实不同。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。
"""

# ── 给好的部分：七个键（别改）──────────────────────────────
keys = ['apple', 'banana', 'cherry', 'date', 'fig', 'grape', 'kiwi']

# ── 第 1 步：8 个桶，打印每个键的哈希值与桶号 ───────────────
# TODO 1：算出 hv = hash(k) 与 slot = hv % buckets8，
#         把桶号 append 进 slots8，再照下面那行 print 打印（那行别改）。
buckets8 = 8
slots8 = []
print(f'桶数 {buckets8}')
for k in keys:
    hv = 0
    slot = 0
    print('键', k, '哈希值', hv, '桶号', slot)

# ── 第 2 步：数 8 个桶里有几个装了不止一个键 ────────────────
# TODO 2：拿第 1 步记下的 slots8 数一数：
#         装了几个键的桶有哪几个（用字典数每个桶号出现几次最省事）；
#         把「装了不止一个键的桶的个数」存进 conflict8，
#         再把「桶里键最多的那个桶装了几个」存进 max_bucket8。
conflict8 = 0
max_bucket8 = 0
print('8 个桶 装了不止一个键的桶数', conflict8)
print('8 个桶 桶里最多装了', max_bucket8, '个键')

# ── 第 3 步：换成 16 个桶，同一批键再跑一遍 ─────────────────
# TODO 3：桶数换成 16，和 TODO 1 同一个形状再算一遍，
#         照下面那行 print 打印（那一行是判分接口，别改）；
#         桶号记进 slots16，再想清楚为什么桶号会与 8 个桶时不同。
buckets16 = 16
slots16 = []
print(f'桶数 {buckets16}')
for k in keys:
    hv = 0
    slot = 0
    print('键', k, '哈希值', hv, '桶号', slot)

# ── 第 4 步：16 个桶的冲突情况 ──────────────────────────────
# TODO 4：和 TODO 2 同一个形状，数 16 个桶的情况，存进 conflict16 与 max_bucket16。
conflict16 = 0
max_bucket16 = 0
print('16 个桶 装了不止一个键的桶数', conflict16)
print('16 个桶 桶里最多装了', max_bucket16, '个键')

# ── 第 5 步：桶数与冲突的关系（别改这几行，判分按它们读结论）──
print('桶变多了 冲突没变多', conflict16 <= conflict8)
print('同进程内哈希值稳定', hash('apple') == hash('apple'))

# ── 给判分脚本的接口（别改函数名与参数）──────────────────────
def bucket_of(key, buckets):
    """算出 key 落在哪个桶：hash(key) % buckets。"""
    # TODO 5
    return 0


def conflicts(keys, buckets):
    """交回 (装了不止一个键的桶数, 桶里最多的键数)。没有冲突就是 (0, 0)。"""
    # TODO 6
    return (0, 0)


# ── 第 6 步：把「哈希值每次运行都不一样」的原因写在这一行 ─────
# TODO 7：把下面引号里换成一两句你自己的解释（理由写清即可，不必与参考解逐字相同）。
# 提示：想想 sys.hash_info 里的 algorithm 与 seed_bits，以及「为什么要有种子」。
reason = 'TODO 7：在这里写下哈希值跨进程不同的原因'
print('原因', reason)
