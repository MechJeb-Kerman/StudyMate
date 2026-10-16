"""任务 5 · 什么能当键：列表当键、浮点当键、哈希值稳不稳

字典与集合对键有要求：**可哈希**——哈希值一生不变，并且相等的对象哈希值相同。
这一份把三件常踩的事变成看得见的结果：

  1. 列表当键 → 报错（新版 Python 的措辞更长，多了一句 cannot use 'list' as a dict key）；
  2. 浮点当键 → 0.1 + 0.2 与 0.3 是两把不同的键，取不到；修法是先 round 到固定小数位；
  3. 哈希值的稳定性 → 同一个进程里同一个字符串算两次结果一致，换个进程就不同。

带 print 的行是判分接口，别改；要写的是标着 TODO 的那几段。

跑： py task5_key_rules.py
判： py run_tests.py
"""

# ── 第 1 步：列表当键会报什么错 ────────────────────────────
# TODO 1：用 try / except 接住 d[[1, 2]] 抛出的异常：
#         err_type 存异常类的名字（用 type(e).__name__），
#         err_msg 存异常的信息（用 str(e)）。
#         报错的那一行写在 try 里，别让它把整个脚本带崩。
d = {}
err_type = ''
err_msg = ''
try:
    d[[1, 2]] = 'x'
except TypeError as e:
    err_type = type(e).__name__
    err_msg = str(e)
print('列表当键 异常类型', err_type)
print('列表当键 报错说', err_msg)
print('列表当键 提到 dict key', 'dict key' in err_msg)

# ── 第 2 步：可哈希的键——元组可以，列表不行 ────────────────
# TODO 2 参考解：元组可哈希，能当键；取不存在的键用 get 交回默认值。
grid = {(1, 2): 'A', (3, 4): 'B'}
cell = grid.get((1, 2))
missing = grid.get((9, 9))
print('元组当键 取到', cell)
print('元组当键 键不存在时 get 交回', missing)

# ── 第 3 步：浮点当键 ──────────────────────────────────────
# TODO 3 参考解：0.1 + 0.2 与 0.3 是两把不同的键；先 round 到固定小数位再取。
price = {0.3: '零点三元'}
by_float = price.get(0.1 + 0.2)
by_round = price.get(round(0.1 + 0.2, 10))
print('浮点当键 0.1+0.2 取到', by_float)
print('浮点当键 先 round 再取到', by_round)
print('浮点当键 不相等', (0.1 + 0.2) != 0.3)

# ── 第 4 步：哈希值在同一个进程里稳不稳（别改这几行）────────
h1 = hash('abc')
h2 = hash('abc')
print('同进程内两次一致', h1 == h2)
print('相同内容不同对象也一致', hash('abc') == hash(''.join(['a', 'b', 'c'])))

# ── 第 5 步：相等的对象哈希值相同（别改这几行）─────────────
print('相等则哈希相同', hash(1) == hash(1.0))

# ── 第 6 步：跨进程交给判分脚本去比（别改这个函数）─────────
def hash_of(text):
    """交回 hash(text)。判分脚本会起两个进程分别调用它，比对结果。"""
    # TODO 4 参考解
    return hash(text)


if __name__ == '__main__':
    print('hash_of abc', hash_of('abc'))
