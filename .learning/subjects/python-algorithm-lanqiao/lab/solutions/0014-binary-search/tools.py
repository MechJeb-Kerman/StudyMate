"""tools.py · lab 0014 的公共工具（给好的，别改）

四个任务都从这里取东西。里面是五类：

  1. 造数据：make_random(n) / make_sorted(n) / make_boundary(seed) …
      确定性数据生成——同一份数据每次跑出来都一样。

  2. 打印：show(section, index, name, value) / show_time(…) / show_error(…)
      打印固定格式的行，判分按行读它们。

  3. 计时：timed(func, *args) / best_of(func, *args, reps=3)
      与第 3 课一致：前后各取一次 perf_counter 相减。

  4. 接住报错：attempt(func, *args) 交回 Caught(值, 报错类型名或 None)
      二分查找本身不会报错（边界写错只会死循环），但函数定义里有语法错
      或用 attempt 保护的特殊情形。

  5. 另起一个进程去试：isolated_run(module, func, args_src)
      子进程怎么死都伤不到你这份脚本。

判分读的全是确定量。下面还有判分与探针共用的参照：

    bsearch_closed_canonical(a, x)   闭区间版的正确实现
    lower_bound_canonical(a, x)      左闭右开版（第一个 ≥ x 的位置）
    contains_canonical(a, x)         用 lower_bound 判断存在性
    bound_seqs()                     边界测试数据集
    max_rounds(n)                    二分查找在规模 n 上的最大轮数

本文件里出现的 time 是计时工具，subprocess 只出现在 isolated_run 里——
它们不是学生要写的部分。
"""

# ── 造数据：确定性生成器 ────────────────────────────────────────────────

def _lcg_next(x):
    """一步线性同余（取模 2^31）。写死参数，每台机器上跑出来都一样。"""
    return (1103515245 * x + 12345) % 2147483648


def _lcg(n, seed, mod):
    """n 个 [0, mod) 之间的整数（确定性）。"""
    x = seed
    out = []
    for _ in range(n):
        x = _lcg_next(x)
        out.append(x % mod)
    return out


def make_random(n):
    """n 个 0 到 10^9-1 之间的随机整数（确定性）。"""
    return _lcg(n, 20261013, 1000000000)


def make_sorted(n):
    """n 个**已经排好序**的整数（严格递增）。"""
    return sorted(make_random(n))


# ── 二分查找的边界测试数据集 ────────────────────────────────────────────

def bound_seqs():
    """返回一整套边界测试数据 → [(名字, 数组, 目标值, 期望行为)]。

    每条是一个四元组：
        name     描述
        arr      有序数组（二分前已经有序）
        x        要找的目标值
        expect   'hit' 表示 x 在 arr 里，'miss' 表示不在

    覆盖了最容易出问题的 8 个位置：
        空数组、单元素命中、单元素不中、全相同命中、
        全相同不中、目标在左端、目标在右端、目标不存在。
    """
    return [
        ('空', [], 1, 'miss'),
        ('单元素命中', [5], 5, 'hit'),
        ('单元素不中', [5], 3, 'miss'),
        ('全相同命中', [7] * 6, 7, 'hit'),
        ('全相同不中', [7] * 6, 8, 'miss'),
        ('目标在左端', [1, 3, 5, 7, 9], 1, 'hit'),
        ('目标在右端', [1, 3, 5, 7, 9], 9, 'hit'),
        ('目标不存在', [1, 3, 5, 7, 9], 4, 'miss'),
    ]


# ── 正确实现：判分与探针共用的参照 ─────────────────────────────────────

def bsearch_closed_canonical(a, x):
    """闭区间二分查找 → x 的下标（找不到返回 -1）。

    写法与课件完全一致：
        lo = 0, hi = len(a) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if a[mid] == x: return mid
            if a[mid] < x: lo = mid + 1
            else: hi = mid - 1
        return -1
    """
    lo = 0
    hi = len(a) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] == x:
            return mid
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def lower_bound_canonical(a, x):
    """左闭右开二分查找 → 第一个 >= x 的位置。

    写法与课件完全一致：
        lo = 0, hi = len(a)
        while lo < hi:
            mid = (lo + hi) // 2
            if a[mid] < x: lo = mid + 1
            else: hi = mid
        return lo
    """
    lo = 0
    hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def contains_canonical(a, x):
    """用 lower_bound 判断 x 是否在 a 里 → True/False。

    注意两步判断不能省：
        k = lower_bound(a, x)
        return k < len(a) and a[k] == x
    """
    k = lower_bound_canonical(a, x)
    return k < len(a) and a[k] == x


# ── max_rounds：二分查找在规模 n 上的最大轮数 ────────────────────────────

def max_rounds(n):
    """二分查找在规模 n 上的最大轮数：ceil(log2(n + 1))。

    每比较一次候选区间就减半，最坏情况要走到区间长度为 0 才停下。
    这个数是算出来的（不用真的跑二分），用于核对 task4 的轮数表。
    """
    if n <= 0:
        return 0
    rounds = 0
    lo, hi = 0, n
    while lo < hi:
        rounds += 1
        mid = (lo + hi) // 2
        # 最坏选针要在端点：lo = mid + 1（取不到），所以区间的长度
        # 从 hi - lo 减到 (hi - lo) // 2 以下再 +1 —— 但直接数即可
        lo = mid + 1  # 每次只削掉一个，模拟最坏情形
    return rounds


def max_rounds_simulated(n):
    """真的跑一遍二分，数出最坏轮数（比公式更有说服力）。

    对几个关键位置（端点、中点、不存在的位置）各跑一遍，
    取最大值。这就是 task4 要做的事。
    """
    if n <= 0:
        return 0
    a = list(range(n))
    worst = 0
    for x in (0, n // 3, n // 2, n * 3 // 4, n - 1, n + 5):
        lo, hi = 0, n
        c = 0
        while lo < hi:
            c += 1
            mid = (lo + hi) // 2
            if a[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        if c > worst:
            worst = c
    return worst


# ── 打印：格式就是判分接口 ──────────────────────────────────────────────

def show(section, index, name, value):
    """打印一行「小节 编号 名称 值」，例如：  一致 01 随机 20000

    section 是这一行属于哪一类，
    编号是两位数字，name 里**不要有空格**（判分按空格切词）。
    """
    print(section + ' ' + str(index).zfill(2) + ' ' + name + ' ' + str(value))


def show_time(section, index, name, n, seconds):
    """打印一行耗时：  耗时 01 线性 n=2000000 0.076244 秒

    判分不读秒数，只给学生自己看形状。
    """
    print(section + ' ' + str(index).zfill(2) + ' ' + name + ' n=' + str(n)
          + ' ' + f'{seconds:.6f}' + ' 秒')


def show_error(index, name, exc_type):
    """打印一行「接住的报错类型」：  异常 01 无收缩死循环 RecursionError"""
    print('异常 ' + str(index).zfill(2) + ' ' + name + ' ' + str(exc_type))


# ── 计时：口径与第 3 课一致 ─────────────────────────────────────────────

def timed(func, *args):
    """跑一次并量耗时 → (函数交回的值, 秒数)。"""
    import time
    start = time.perf_counter()
    value = func(*args)
    end = time.perf_counter()
    return value, end - start


def best_of(func, *args, reps=3):
    """跑 reps 次，交回 (最后一次的值, 最小秒数)。"""
    value, best = None, None
    for _ in range(reps):
        value, seconds = timed(func, *args)
        if best is None or seconds < best:
            best = seconds
    return value, best


# ── 接住报错 ────────────────────────────────────────────────────────────

class Caught:
    """attempt 的返回值：要么有 value，要么有 error（报错类型名）。"""

    def __init__(self, value, error):
        self.value = value
        self.error = error

    @property
    def ok(self):
        return self.error is None

    def __repr__(self):
        if self.ok:
            return 'Caught(ok)'
        return 'Caught(' + self.error + ')'


def attempt(func, *args):
    """跑一次，把报错接住 → Caught(值, 报错类型名)。"""
    try:
        return Caught(func(*args), None)
    except Exception as exc:
        return Caught(None, type(exc).__name__)


# ── 另起一个进程去试 ────────────────────────────────────────────────────

def _isolated(module, func, args_src, mode, want_src='None', timeout=120):
    """起一个子进程跑 `module.func(*args)` → (结果词, 报错类型名)。"""
    import os
    import subprocess
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    command = [sys.executable, '-B', '-c', _CHILD_SOURCE, here, module, func,
               args_src, mode, want_src]
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    try:
        done = subprocess.run(command, cwd=here, env=env, timeout=timeout,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, encoding='utf-8', errors='replace')
    except subprocess.TimeoutExpired:
        return 'timeout', None
    for line in (done.stdout or '').splitlines():
        if line.startswith('RESULT '):
            words = line[len('RESULT '):].split()
            return words[0], (words[1] if len(words) > 1 else None)
    return 'hard-crash', None


_CHILD_SOURCE = r'''
import sys
sys.path.insert(0, sys.argv[1])
module, func, args_src, mode, want_src = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
try:
    mod = __import__(module)
except Exception as exc:
    print('RESULT error ' + type(exc).__name__)
    raise SystemExit(0)
target = getattr(mod, func, None)
if target is None:
    print('RESULT missing')
    raise SystemExit(0)
args = eval(args_src)
try:
    value = target(*args)
except Exception as exc:
    print('RESULT error ' + type(exc).__name__)
    raise SystemExit(0)
if mode == 'run':
    print('RESULT ok')
    raise SystemExit(0)
try:
    want = eval(want_src)
except Exception as exc:
    print('RESULT error ' + type(exc).__name__)
    raise SystemExit(0)
print('RESULT ' + ('equal' if value == want else 'different'))
'''


def isolated_run(module, func, args_src, timeout=120):
    """另起一个进程跑 `module.func(*args)`，只关心「跑完了没有」。

    交回一个词：ok（跑完）/ error:TYPE（抛了异常）/ missing（没有这个函数）/
    hard-crash（进程直接没了）/ timeout（超时）。
    """
    word, exc_type = _isolated(module, func, args_src, 'run', timeout=timeout)
    if word == 'error' and exc_type:
        return 'error:' + exc_type
    return word


# ── 三种错法的参照 ──────────────────────────────────────────────────────

def bug_no_shrink(a, x):
    """错法一：`lo = mid` 而不是 `lo = mid + 1`，区间不收缩 → 死循环。"""
    lo = 0
    hi = len(a)
    steps = 0
    while lo < hi:
        steps += 1
        if steps > 50:
            return '步数超限，死循环', steps
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid      # ← 故意写成 mid 而不是 mid + 1
        else:
            hi = mid
    return lo, steps


def bug_lose_last(a, x):
    """错法二：闭区间 'while lo < hi' 而不是 'lo <= hi'，漏最后一个元素。"""
    lo = 0
    hi = len(a) - 1
    while lo < hi:          # ← 故意写成 < 而不是 <=
        mid = (lo + hi) // 2
        if a[mid] == x:
            return mid
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def bug_no_check(a, x):
    """错法三：直接用 lower_bound 返回的下标作为答案，不检查越界与值是否相等。

    返回插入位置但不验证 `k < len(a) and a[k] == x`。
    目标不存在时会返回错误的「下标」。
    """
    lo = 0
    hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo               # ← 少了 a[k] == x 与越界检查


# ── 判断已排序 ──────────────────────────────────────────────────────────

def is_sorted(a):
    """从小到大排好了吗——只是**看**一遍，不排序、不新建表。"""
    for i in range(len(a) - 1):
        if a[i] > a[i + 1]:
            return False
    return True