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
    hv = hash(k)
    slot = hv % buckets8
    slots8.append(slot)
    print('键', k, '哈希值', hv, '桶号', slot)

# ── 第 2 步：数 8 个桶里有几个装了不止一个键 ────────────────
# TODO 2 参考解：先用字典数每个桶号出现几次，再各取一个统计量。
conflict8 = 0
max_bucket8 = 0
count8 = {}
for slot in slots8:
    count8[slot] = count8.get(slot, 0) + 1
for slot in count8:
    if count8[slot] > 1:
        conflict8 += 1
    if count8[slot] > max_bucket8:
        max_bucket8 = count8[slot]
print('8 个桶 装了不止一个键的桶数', conflict8)
print('8 个桶 桶里最多装了', max_bucket8, '个键')

# ── 第 3 步：换成 16 个桶，同一批键再跑一遍 ─────────────────
# TODO 3 参考解：只把桶数换成 16，其余形状与第 1 步一样。
buckets16 = 16
slots16 = []
print(f'桶数 {buckets16}')
for k in keys:
    hv = hash(k)
    slot = hv % buckets16
    slots16.append(slot)
    print('键', k, '哈希值', hv, '桶号', slot)

# ── 第 4 步：16 个桶的冲突情况 ──────────────────────────────
# TODO 4 参考解
conflict16 = 0
max_bucket16 = 0
count16 = {}
for slot in slots16:
    count16[slot] = count16.get(slot, 0) + 1
for slot in count16:
    if count16[slot] > 1:
        conflict16 += 1
    if count16[slot] > max_bucket16:
        max_bucket16 = count16[slot]
print('16 个桶 装了不止一个键的桶数', conflict16)
print('16 个桶 桶里最多装了', max_bucket16, '个键')

# ── 第 5 步：桶数与冲突的关系（别改这几行，判分按它们读结论）──
print('桶变多了 冲突没变多', conflict16 <= conflict8)
print('同进程内哈希值稳定', hash('apple') == hash('apple'))

# ── 给判分脚本的接口（别改函数名与参数）──────────────────────
def bucket_of(key, buckets):
    """算出 key 落在哪个桶：hash(key) % buckets。"""
    # TODO 5 参考解
    return hash(key) % buckets


def conflicts(keys, buckets):
    """交回 (装了不止一个键的桶数, 桶里最多的键数)。没有冲突就是 (0, 0)。"""
    # TODO 6 参考解：先数桶，再统计。
    counts = {}
    for k in keys:
        slot = bucket_of(k, buckets)
        counts[slot] = counts.get(slot, 0) + 1
    more = 0
    most = 0
    for slot in counts:
        if counts[slot] > 1:
            more += 1
        if counts[slot] > most:
            most = counts[slot]
    return (more, most)


# ── 第 6 步：把「哈希值每次运行都不一样」的原因写在这一行 ─────
# TODO 7 参考解（意思到了就行，不必逐字相同）：
reason = ('字符串哈希带随机种子：进程启动时随机选一个种子，'
          '本机 sys.hash_info 显示 siphash13、seed_bits 128，所以同一个串在不同进程里'
          '算出的哈希值不同，同一个进程内不变。加种子是为了防人预先构造一大批'
          '落进同一个桶的键，把字典拖成最坏 O(n)。')
print('原因', reason)
