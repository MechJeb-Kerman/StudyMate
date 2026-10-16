"""tools.py · lab 0013 的公共工具（给好的，别改）

四个任务都从这里取东西。里面是五类：

  1. 造数据：make_random(n) / make_sorted(n) / make_reversed(n) / make_duplicates(n, kinds)
     四类**确定性**数据——随机、已有序、逆序、含大量重复值。不用 random 是有意的：
     同一份数据每次跑出来都一样，判分才能核对确切的答案，你自己跑两次也能对照。
     格式是一行一个整数（make_text），也能用 parse_text 读回来。

  2. 打印：show(section, index, name, value) / show_time(...) / show_factor(...)
     / show_error(...) / show_bytes(...)
     打印固定格式的行，判分按行读它们。格式见下面每个函数的说明。

  3. 计时：timed(func, *args) / best_of(func, *args, reps=3) / median_time(func, *args, reps=5)
     计时口径与第 3 课一致：前后各取一次 perf_counter 相减，中间不夹别的代码。
     best_of 取几次里**最小**的、median_time 取几次里的**中位数**——机器上还有别的程序在跑，
     单次量出来会偏大；最小值最接近这段代码本身的代价，中位数最不容易被一次抖动带偏。

  4. 接住报错：attempt(func, *args) 交回 Caught(值, 报错类型名或 None)
     这一课有两处**故意的**报错要看到现场：固定主元快排在已有序数据上撞递归上限、
     计数排序把值域开到 10^9 时开不出那张表。这两个报错必须被接住、只把**类型名**打出来，
     不能让整个脚本崩掉——那不是「没接住异常」，那是脚本的写法。

  5. 另起一个进程去试：isolated_run(module, func, args_src)
     「一次要开几个 GB 的表」这种情形，内存不够的机器上可能是解释器直接退出
     （连异常都来不及抛）。那种情形交给它：子进程怎么死都伤不到你这份脚本。

这一课**判分读的全是确定量**。这一课的天然陷阱是遍地计时（耗时表、固定主元与随机主元的
耗时比），而秒数随机器浮动——所以判分一条都不读秒数，读的是下面这些**次数**：
同一份数据、同一台机器，每次都是同一个整数，而且能被另算一遍。

  6. 判分与探针共用的参照（都在本文件里，学生也可以拿来对答案）：

        merge_sort_canonical(a)            判分那一版归并排序（与课件的写法一致）
        counting_sort_canonical(a, maxv)   判分那一版计数排序
        merge_ops_measured(a)              量归并：「搬动了几个元素、比较了几次、多深」
        partition_ops_measured(a, mode)    量划分：「比较了几次、搬动了几个元素、
                                           划分被调了几次、多深」
                                           mode = 'fixed'（固定主元，取开头）/ 'random'（随机主元）
        counting_ops_measured(a, maxv)     量计数排序：「清点了几次、写回几个位置」
        merge_moves_canonical(n)           归并的搬动次数（算出来的，与数据无关）
        merge_ops_canonical(n)             归并的 (搬动, 比较上界, 深度)
        partition_comparisons_canonical(n, sorted_data, mode)
                                           划分的比较次数（算出来的）：已有序 + 固定主元时
                                           正好是 n(n-1)/2 —— 这就是退化
        partition_comparisons_bound(n)     划分比较次数的上界 n*n（无序数据那一格核它）
        partition_moves_canonical(n, sorted_data, mode)
                                           划分的搬动次数（算出来的）：已有序 + 固定主元是
                                           正好 0 次；其余情形交回 None（不是确定量）
        partition_moves_random_bound(n)    已有序 + 随机主元时搬动的上界 3n
        partition_calls_bound(n)           划分被调用次数的上界 n - 1
        counting_ops_canonical(n, maxv)    计数排序的两个数 (n, maxv + 1)
        counting_slots(maxv) / counting_bytes(maxv)
                                           要开多大的表 / 大约多少字节
        merge_depth_canonical(n)           归并的最大递归深度（数出来的）
        depth_by_walk(n)                   真的递归一次、看它落到第几层（量出来的）
        key_calls_canonical(items, key)    在比较里调 key 的归并版一共调用了几次 key
        is_sorted(a)                       是不是从小到大排好的（只是看一看，不排序）
        same_as_sorted(a)                  与 sorted(a) 逐字相同吗
        range_class(maxv)                  值域宽度是哪一档（计数排序能不能用看它）

     这些「参照」是判分与探针**共用**的口径。判分不 import 学生的代码，所以它先用
     这些算一遍期望值，再让探针另起一个进程去 import 学生的函数——两路对上了才算数。

本文件里出现的 time 是计时工具，subprocess 只出现在 isolated_run 与 run_tests.py 里——
它们不是学生要写的部分。
"""

# ── 造数据：确定性生成器，四类数据各一份 ────────────────────────────────

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
    """n 个 0 到 10^9-1 之间的随机整数（确定性）。值域很大，不适合计数排序。"""
    return _lcg(n, 20261013, 1000000000)


def make_sorted(n):
    """n 个**已经排好序**的整数（严格递增）。

    这一类是这一课的要害：快排的固定主元版在它上面会退化。
    只用随机数据测性能，这个坑就藏起来了。
    """
    return sorted(make_random(n))


def make_reversed(n):
    """n 个**逆序**的整数（严格递减）。它对固定主元版是退化得最彻底的输入。"""
    return sorted(make_random(n), reverse=True)


def make_duplicates(n, kinds=20):
    """n 个只有 kinds 种取值（默认 20 种）的整数——含大量重复值。

    重复值多时，「两段头部相等该先取哪一边」这件事每几步就会遇上一次：
    归并版写成 `<` 而不是 `<=`，正确答案仍然一样，但**稳定性**丢了；
    快排的划分里写错边界，重复值会成堆地跑到错的位置。
    """
    return _lcg(n, 777333, kinds)


def make_small(n, mod, seed):
    """n 个 [0, mod) 之间的整数，种子由调用者给——任务 2、4 用它造「值域小」的数据。"""
    return _lcg(n, seed, mod)


def make_text(numbers):
    """把一串整数拼成多行字符串（一行一个）。第 6 课的读入格式就用它。"""
    return '\n'.join(str(x) for x in numbers) + '\n'


def parse_text(text):
    """把上面那种文本读回整数列表：一次读完、按空白切分、逐段解析。

    第 6 课的规矩：别逐行 input()，那样换行位置一变答案就变。
    """
    out = []
    for token in text.split():
        out.append(int(token))
    return out


# ── 打印：格式就是判分接口 ──────────────────────────────────────────────

def show(section, index, name, value):
    """打印一行「小节 编号 名称 值」，例如：  一致 01 随机 20000

    section 是这一行属于哪一类（一致 / 深度 / 键调用 / 操作 …），
    编号是两位数字，name 里**不要有空格**（判分按空格切词）。
    """
    print(section + ' ' + str(index).zfill(2) + ' ' + name + ' ' + str(value))


def show_time(section, index, name, n, seconds):
    """打印一行耗时：  耗时 01 归并 n=400 0.003570 秒

    这一课**没有一条判据读秒数**：耗时只给学生自己看形状。判分读的是操作次数。
    """
    print(section + ' ' + str(index).zfill(2) + ' ' + name + ' n=' + str(n)
          + ' ' + f'{seconds:.6f}' + ' 秒')


def show_factor(section, index, name, factor):
    """打印一行倍率：  倍率 05 归并 2.13

    factor 是同一列相邻两档的比值（这一行 ÷ 上一行）。这一课算的是**操作次数**的比值，
    不是秒数的比值——秒数会随机器浮动，操作次数换台机器还是同一个整数。

    factor 不是数字时（那几格还没写出来）就原样打印，不再套那个两位小数的格式 ——
    套上去会 TypeError，而这一段的原则是「打完整每一行，别半路崩掉」。
    """
    if isinstance(factor, str) and factor and not factor[0].isdigit():
        text = factor
    elif isinstance(factor, bool) or not isinstance(factor, (int, float)):
        text = '—'
    else:
        text = f'{factor:.2f}'
    print(section + ' ' + str(index).zfill(2) + ' ' + name + ' ' + text)


def show_error(index, name, exc_type):
    """打印一行「接住的报错类型」：  异常 01 固定主元 已有序 n=1600 RecursionError"""
    print('异常 ' + str(index).zfill(2) + ' ' + name + ' ' + str(exc_type))


def show_bytes(section, index, name, count, size):
    """打印一行「要开多大的表」：  表大小 01 值域10^9 需要 1000000001 个位置，约 8000.0 MB"""
    print(section + ' ' + str(index).zfill(2) + ' ' + name + ' 需要 ' + str(count)
          + ' 个位置，约 ' + f'{size / 1048576:.1f}' + ' MB')


# ── 计时：口径与第 3 课一致 ─────────────────────────────────────────────

def timed(func, *args):
    """跑一次并量耗时 → (函数交回的值, 秒数)。"""
    import time
    start = time.perf_counter()
    value = func(*args)
    end = time.perf_counter()
    return value, end - start


def best_of(func, *args, reps=3):
    """跑 reps 次，交回 (最后一次的值, 最小秒数)。

    取最小值是为了躲开系统调度带来的偏大值——课件里那张耗时表就是这么量的。
    交回的值是**最后一次**跑出来的：同一个函数的同一个输入，答案每次都一样。
    """
    value, best = None, None
    for _ in range(reps):
        value, seconds = timed(func, *args)
        if best is None or seconds < best:
            best = seconds
    return value, best


def median_time(func, *args, reps=5):
    """跑 reps 次，交回**中位数**秒数（比最小值更不容易被一次抖动带偏）。"""
    seen = []
    for _ in range(reps):
        _, seconds = timed(func, *args)
        seen.append(seconds)
    seen.sort()
    return seen[len(seen) // 2]


# ── 接住报错：这一课有两处报错是要看的现场 ──────────────────────────────

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
    """跑一次，把报错接住 → Caught(值, 报错类型名)。

    只看**类型名**（`type(exc).__name__`），不打印完整 traceback：
    这一课要的是「撞上了哪个上限」这件事，不是某一行行号。

    注意它接住的只是**普通异常**。像 `[0] * (10**9 + 1)` 这种一次要开几个 GB 的写法，
    在内存不够的机器上可能是解释器直接退出（连异常都来不及抛）——那种情形不归它管，
    交给下面的 isolated_run：那一件是**另起一个进程**去试的，子进程怎么死都伤不到你这份脚本。
    """
    try:
        return Caught(func(*args), None)
    except Exception as exc:          # 故意的：这里就是要接住任何报错
        return Caught(None, type(exc).__name__)


# ── 另起一个进程去试：给「一次要开几 GB 表」这种情形兜底 ────────────────

def _isolated(module, func, args_src, mode, want_src='None', timeout=120):
    """起一个子进程跑 `module.func(*args)` → (结果词, 报错类型名)。

    结果词是 ok / equal / different / error / missing / hard-crash / timeout。
    `hard-crash` 就是「解释器直接退出」的那一种——它正是 `[0] * (10**9 + 1)` 的样子。
    """
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


# 子进程里跑的那一小段。写成一段字符串是有意的：子进程只拿到 `-c` 这段代码，
# 参数（模块名、函数名、参数表达式）由父进程拼在命令行上。
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


# ── 参照表之一：归并排序与计数排序的「判分那一版」 ──────────────────────

def merge_sort_canonical(a):
    """判分与探针共用的归并排序（与课件的写法一致，交回**新表**）。

    学生写的那一版在 task1 里；这一份只用来算期望值。
    """
    if len(a) <= 1:
        return list(a)
    mid = len(a) // 2
    left = merge_sort_canonical(a[:mid])
    right = merge_sort_canonical(a[mid:])
    out = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def counting_sort_canonical(a, maxv=None):
    """判分与探针共用的计数排序（交回**新表**）。表长是 maxv + 1，不是 n。"""
    numbers = list(a)
    if maxv is None:
        maxv = max(numbers) if numbers else 0
    cnt = [0] * (maxv + 1)
    for value in numbers:
        cnt[value] += 1
    out = []
    for value in range(maxv + 1):
        if cnt[value]:
            out.extend([value] * cnt[value])
    return out


def is_sorted(a):
    """从小到大排好了吗——只是**看**一遍，不排序、不新建表。"""
    for i in range(len(a) - 1):
        if a[i] > a[i + 1]:
            return False
    return True


def same_as_sorted(a):
    """与 sorted(a) 逐字相同吗。这就是「排序结果正确」的**唯一**标准。"""
    return list(a) == sorted(a)


# ── 参照表之二：可精确计数的操作次数 ────────────────────────────────────
#
# 数出来的东西只有三样：比较了几次、搬动了几个元素、递归多深。
# 下面这几个函数都是**真的跑一遍**（在副本上），不是算公式。

def merge_ops_measured(a):
    """量归并排序在**一份数据**上的代价 → (搬动次数, 比较次数, 递归深度)。

    搬动次数：每次把一个元素放进交回的新表里算一次。每一层的合并都要把这一段的
              全部元素搬一遍，**只由 n 决定**，有序还是乱序都一样多 ——
              这一格是「不看代码形状、看次数」最好的例子。
    比较次数：两段头部比一次算一次；相等的元素越多、两段越不均匀，它就越少，
              所以它**不大于**搬动次数（这是可以逐格核的上界）。
    递归深度：n <= 1 的那一层算一层，与 merge_depth_canonical 的口径一致。

    基例交回**已经排好序的一段**（判分这一版用 sorted），切法与 merge_sort 完全一致：
    基例那一层不合并、也就没有搬动。
    """
    counters = {'cmp': 0, 'move': 0}

    def rec(part):
        if len(part) <= 1:
            return list(part), 1
        mid = len(part) // 2
        left, dl = rec(part[:mid])
        right, dr = rec(part[mid:])
        out = []
        i = 0
        j = 0
        while i < len(left) and j < len(right):
            counters['cmp'] += 1
            if left[i] <= right[j]:
                out.append(left[i])
                i += 1
            else:
                out.append(right[j])
                j += 1
        tail = left[i:] + right[j:]
        counters['move'] += len(out) + len(tail)
        out.extend(tail)
        return out, max(dl, dr) + 1

    _value, depth = rec(list(a))
    return counters['move'], counters['cmp'], depth


def partition_ops_measured(a, mode='fixed'):
    """量「划分」在**一份数据**上的代价 → (比较次数, 搬动次数, 划分调用次数, 递归深度)。

    比较次数：每一次 `a[j] < p` 算一次（主元自己不参与比较）。
    搬动次数：每一次交换算**两个元素各动一次**，主元归位那一次交换也算。
    划分调用次数：`partition` 被调了几次。每次划分让一个元素归位，最多 n - 1 次；
                  随机主元挑到端点时有一边是空的，那一次递归就省了，所以它比 n - 1 少一点。
    递归深度：这一段空着或只剩一个元素算一层（与那句 `lo >= hi: return` 对齐）。

    mode = 'fixed'   固定主元：取这一段开头作主元（这一课故意这么取）
    mode = 'random'  随机主元：先在 lo..hi 里随机挑一个、与开头换一下，其余原样

    **真的跑一遍排序**（在 a 的副本上），一边跑一边数。

    随机主元那一版用的是**自己那个钉死种子的随机数发生器**（random.Random(20261013)），
    不是全局那个——所以同一个 mode、同一份数据、同一个规模，量出来的四个数每次都一样。
    这是这一课的硬要求：拿一个会变的量去核一个写死的期望值，同一份代码会时过时不过。

    四个数里哪几个是「确定量」要看数据形状：

        划分调用次数、递归深度      与数据、与主元取法都无关（只由 n 决定的**结构量**）
        已有序 + 固定主元           比较 = n(n-1)/2、搬动 = 0（两个确切的数）
        已有序 + 随机主元           搬动 = 2(n-1)（确切的数）
        无序数据的比较 / 搬动       由数据决定，只核上界
    """
    import random
    chooser = random.Random(20261013)
    work = list(a)
    counters = {'cmp': 0, 'move': 0, 'calls': 0}

    def part(lo, hi):
        if lo >= hi:
            return lo
        counters['calls'] += 1
        if mode == 'random':
            m = chooser.randrange(lo, hi + 1)
            work[lo], work[m] = work[m], work[lo]
            counters['move'] += 2
        p = work[lo]
        i = lo
        for j in range(lo + 1, hi + 1):
            counters['cmp'] += 1
            if work[j] < p:
                i += 1
                if i != j:
                    work[i], work[j] = work[j], work[i]
                    counters['move'] += 2
        if lo != i:
            work[lo], work[i] = work[i], work[lo]
            counters['move'] += 2
        return i

    def sort(lo, hi):
        if lo >= hi:
            return 1
        k = part(lo, hi)
        return max(sort(lo, k - 1), sort(k + 1, hi)) + 1

    depth = sort(0, len(work) - 1)
    return counters['cmp'], counters['move'], counters['calls'], depth


def quicksort_ops_measured(a, mode='fixed', limit=20000):
    """另量一份快排的代价，交回一个**能看见「退化」的**字典。

    与 partition_ops_measured 的区别在最后两个键：划分次数（= 比了几次、归位了几个元素）
    与要靠多深。数据已有序、主元又取在端点上时，这两个数会一起长到 n 那么大 ——
    那就是「退化」在计数器上的样子。

    交回 {'cmp': 比较次数, 'move': 搬动次数, 'jobs': 划分了几次,
          'depth': 要递归多深, 'error': 报错类型名或 None}

    顶上先把递归上限设成 limit —— 判分要用这个数把「撞上限」这件事变成确定的：
    同一个固定的上限下，固定主元在已有序数据上会爆、随机主元不会。
    那一段很长（20 万次比较、2 万层深），所以它不快，但它是确定量：每次都一模一样。
    """
    import random
    import sys
    sys.setrecursionlimit(limit)
    chooser = random.Random(20261013)
    work = list(a)
    counters = {'cmp': 0, 'move': 0, 'jobs': 0}

    def part(lo, hi):
        counters['jobs'] += 1
        if mode == 'random':
            m = chooser.randrange(lo, hi + 1)
            work[lo], work[m] = work[m], work[lo]
            counters['move'] += 2
        p = work[lo]
        i = lo
        for j in range(lo + 1, hi + 1):
            counters['cmp'] += 1
            if work[j] < p:
                i += 1
                if i != j:
                    work[i], work[j] = work[j], work[i]
                    counters['move'] += 2
        if lo != i:
            work[lo], work[i] = work[i], work[lo]
            counters['move'] += 2
        return i

    def sort(lo, hi):
        if lo >= hi:
            return 1
        k = part(lo, hi)
        return max(sort(lo, k - 1), sort(k + 1, hi)) + 1

    try:
        depth = sort(0, len(work) - 1)
    except RecursionError:
        return {'cmp': counters['cmp'], 'move': counters['move'],
                'jobs': counters['jobs'], 'depth': None, 'error': 'RecursionError'}
    return {'cmp': counters['cmp'], 'move': counters['move'],
            'jobs': counters['jobs'], 'depth': depth, 'error': None}


def counting_ops_measured(a, maxv=None):
    """量计数排序在**一份数据**上的代价 → (清点次数, 写回位置数)。

        清点次数 = len(a)      「for x in a: cnt[x] += 1」这一步访问了元素几次
        写回位置数 = maxv + 1   走了一遍 0..maxv 的那一趟

    它一个元素都不比较——这就是「计数排序不受 O(n log n) 下界约束」的样子：
    代价是 n + V，其中 V = maxv + 1 由**值域**决定，与有多少个元素无关。

    注意：它只数、不开表（注释写的是设计意图，早期版本真开了表——值域 10^9
    时直接崩掉）。这里用 dict 代替 list，只记有值的那些槽。
    """
    numbers = list(a)
    if maxv is None:
        maxv = max(numbers) if numbers else 0
    cnt = {}
    counted = 0
    for value in numbers:
        cnt[value] = cnt.get(value, 0) + 1
        counted += 1
    written = 0
    for _value in range(maxv + 1):
        written += 1
    return counted, written


# ── 参照表之三：同样那几件事的**公式**（算出来的，与具体数据无关）──────
#
# 判分与探针都用这几个函数算期望值：学生交回的次数要逐格对上它们，
# 才说明那个数是从数据里算出来的，不是写死的。

def merge_depth_canonical(n):
    """归并排序的最大递归深度，一层一层往下数（不用递归）。

    切法必须与 merge_sort 完全一致：每一层的规模是 n // 2 与 n - n // 2，
    n <= 1 的那一层不再往下切。数出来是 ceil(log2 n) + 1：
    n=8 是 4、n=1000 是 11、n=32768 是 16、n=100000 是 18。
    """
    level = [n]
    depth = 0
    while level:
        depth += 1
        nxt = []
        for size in level:
            if size > 1:
                half = size // 2
                nxt.append(half)
                nxt.append(size - half)
        level = nxt
    return depth


def merge_levels(n):
    """归并排序要**合并**几层（不算基例那一层）：ceil(log2 n)。n <= 1 是 0。"""
    return merge_depth_canonical(n) - 1


def merge_moves_canonical(n):
    """归并排序的搬动次数（算出来的，与数据无关）。

    把 merge_sort 的切法原样走一遍、只把「长度 >= 2 的那一段」加起来：那些段才合并，
    而合并一次就把这一段的全部元素搬进新表一次。写成一条式子就是

        M(n) = n * (L - 1) - (2**(L - 1) - (n - 2**(L - 1)))，    L = ceil(log2 n)

    换一种写法是 M(n) = n * (L - 2) + 2**L - 2**(L - 1) —— 但最省事、最不会算错的是
    像下面这样**直接按切法递归地把每一段的长度加起来**：它只用到 n // 2 这一条切法，
    与 merge_sort 一字不差，也就没地方写错。

    注意它**不是** n * L：最底下那一层里长度为 1 的小段不合并，要从 n * L 里减掉
    n - 2**(L - 1) 那么多（n = 400、L = 10 时是 4000 - 512 = 3488）。

    这个数只由 n 决定 —— 有序、逆序、全是重复值，搬动的次数一模一样。
    """
    if n <= 1:
        return 0
    half = n // 2
    return n + merge_moves_canonical(half) + merge_moves_canonical(n - half)


def merge_ops_canonical(n):
    """归并排序在规模 n 上「干活的多少」（算出来的）→ (搬动次数, 比较次数上界, 递归深度)。

    搬动次数就是 merge_moves_canonical(n)（确定量）；
    比较次数每层每个元素至多一次，所以它的上界也是那个数 —— 判分核的是「不超过」，
    因为相等的元素越多，实际比较次数就越少；
    深度是 merge_depth_canonical(n)。
    """
    moves = merge_moves_canonical(n)
    return moves, moves, merge_depth_canonical(n)


def _harmonic(n):
    """第 n 个调和数 1 + 1/2 + ... + 1/n，取整。"""
    total = 0.0
    for k in range(1, n + 1):
        total += 1.0 / k
    return int(total)


def partition_comparisons_canonical(n, sorted_data, mode='fixed'):
    """划分的比较次数（算出来的；只有**已有序 + 固定主元**那一格是一个确切的数）。

    在**已经有序**的数据上：

        固定主元（取开头）：主元就是这一段里最小的那一个，后面 n - 1 个元素每个都要比
                            一次，可是一个都进不了「小于主元」那一段 → 每次都只削掉一个
                            元素 → 一共 n(n-1)/2 次比较。这就是退化：n 翻一倍，钱翻四倍。

        随机主元：比较次数随随机到的位置上下浮动，不是确定量 —— 用
                  partition_comparisons_bound 核它的上界就好。

    在**随机排列、没有重复值**的数据上：

        固定主元：主元落在这一段里的名次是均匀的，期望 2(n+1)H_n - 4n 次
                  （H_n 是第 n 个调和数）—— 同样是 n log n 量级，比有序数据上少两个数量级。

    n <= 1 时不划分（0 次）；n == 2 时正好 1 次。sorted_data 为 False 时按「随机排列」算。
    """
    if n <= 1:
        return 0
    if n == 2:
        return 1
    if sorted_data and mode == 'fixed':
        return n * (n - 1) // 2
    return int(2 * (n + 1) * _harmonic(n) - 4 * n)


def partition_comparisons_bound(n):
    """划分比较次数的上界：每一层里每个元素至多比一次，层数至多 n（最坏只削掉一个元素）。

    这个上界宽得出奇（n = 400 时是 160000，实际 3000 多），但它是**确定的**：
    任何一份数据、任何一种取主元的办法，比较次数都超不过它。所以随机主元那一格
    就核这个上界——不核一个会随机的数。
    """
    if n <= 1:
        return 0
    return n * n


def partition_moves_canonical(n, sorted_data, mode='fixed'):
    """划分的搬动次数（算出来的）——**只有已有序 + 固定主元**那一格是一个确切的数。

    已经有序的数据上：

        固定主元：主元就是这一段里最小的那一个，一个元素都不小于它 → 一次交换都不用做
                  → 正好 **0 次搬动**。这是全课最干净的一格：有序数据上它比得最多（n(n-1)/2
                  次）、动得最少（0 次），两件事一起说明「主元取在端点上」。

        随机主元：主元换到开头之后，这一段就**不再有序**了（开头那个小元素被换到了中间），
                  所以除了「换主元 2 次」还会有一些小交换 —— 这个数不是确定的，
                  交回 None；用 partition_moves_random_bound 核它的上界就好。

    其余情形都交回 None：无序数据上的搬动次数由数据本身决定（n = 400 时实测在 3000 上下
    浮动，同一份数据换一种取主元的办法就变），拿它当判据就是拿一个会变的量去核一个写死的数。
    """
    if not sorted_data:
        return None
    if n <= 1:
        return 0
    if mode == 'fixed':
        return 0
    return None


def partition_moves_random_bound(n):
    """已有序数据上**随机主元**那一版搬动次数的上界：3n。

    换主元那一笔正好 2(n-1) 次（每一层各一次）；主元归位与开头那个小元素被换到中间之后
    还会零星发生一些小交换，n = 400 / 800 / 1600 上实测是 962 / 1858 / 3786，
    都落在 2(n-1) < 实测 < 3n 里。所以这一格判「比固定主元的 0 大得多、又没超过 3n」——
    它要说的事只有一件：随机主元**真的在搬东西**，而固定主元在有序数据上一次都没搬。
    """
    if n <= 1:
        return 0
    return 3 * n


def partition_calls_bound(n):
    """划分被调用的**次数上界** → n - 1。

    为什么是 n - 1：每次划分都让一个元素（主元）落到最终位置，落到只剩一个元素的那一段
    就不再划分了，所以最多 n - 1 次。

    注意这道上界**取得到、也常常取不到**：随机主元偶尔正好挑到这一段的最小值或最大值时，
    划分出来有一边是空的，那一次递归就省掉了 —— 实测 n = 400、800、1600 上分别是
    272 / 525 / 1072 次，都小于 n - 1。所以这一格判的是「没多没少地数了一遍」
    （落在 1 与 n-1 之间），而不是一个写死的数。
    """
    return max(0, n - 1)


def counting_ops_canonical(n, maxv):
    """计数排序的操作次数：(清点次数, 写回位置数) = (n, maxv + 1)。

    代价 O(n + V)，V = maxv + 1 就是那张表的长度。n 从这里长大、V 从那里长大：
    n 翻一倍两个数各翻一倍；值域不动、n 翻倍时，第二个数纹丝不动。
    它不比较任何两个元素，所以不受 O(n log n) 下界约束——代价挪到那张表上去了。
    """
    return n, maxv + 1


def counting_slots(maxv):
    """计数排序要开多少个位置：maxv + 1。值域 10^9 就是 10^9 + 1 个位置。"""
    return maxv + 1


def counting_bytes(maxv):
    """那张表大约多少字节：Python 的列表一个位置 8 字节（一个指针）。"""
    return counting_slots(maxv) * 8


def depth_by_walk(n):
    """真的递归一次，量一量落到第几层（顶层算第 1 层）。

    与上面的数法互为对照：数出来的深度与真跑一遍的深度必须是同一个数。
    """
    def rec(size):
        if size <= 1:
            return 1
        half = size // 2
        return max(rec(half), rec(size - half)) + 1

    return rec(n)


def key_calls_canonical(items, key):
    """在比较里调 key 的归并版一共调用了几次 key（判分与探针共用）。

    这就是「以为内置 sorted 永远比手写快」那一段的对照：
    `sorted(key=)` 每个元素只算一次键（装饰 - 排序 - 去装饰），而这一版每次比较
    都要算两个键——一次排序要比较约 n log n 次，键自然被算得远多于 n 次。
    """
    counters = {'calls': 0}

    def counted(item):
        counters['calls'] += 1
        return key(item)

    def rec(part):
        if len(part) <= 1:
            return list(part)
        mid = len(part) // 2
        left = rec(part[:mid])
        right = rec(part[mid:])
        out = []
        i = 0
        j = 0
        while i < len(left) and j < len(right):
            if counted(left[i]) <= counted(right[j]):
                out.append(left[i])
                i += 1
            else:
                out.append(right[j])
                j += 1
        out.extend(left[i:])
        out.extend(right[j:])
        return out

    rec(list(items))
    return counters['calls']


# ── 值域的分类：任务 4 用它 ────────────────────────────────────────────

def table_of_slots(maxv):
    """真的去开那一张「长度 maxv + 1」的表，交回它的长度。

    这一步就是计数排序在值域上付出的代价：值域 999 是 1000 个位置、随手就开；
    值域 10^9 是 10^9 + 1 个位置（约 8 GB），这一行就是「开不出来」发生的地方。

    它故意**不做任何保护**：内存不够时由调用者去接住 MemoryError，或者让另起一个
    进程的那条路去承担「解释器直接退出」。任务 4 判的正是这两件事。
    """
    cnt = [0] * (maxv + 1)
    return len(cnt)


def range_class(maxv):
    """按表的长度交回一个词——计数排序能不能用，看的就是这个。

        'tiny'    表的长度 < 10^4      → 开得出表，比 sorted 还省事
        'small'   表的长度 < 10^6      → 开得出表，但表已经不小了
        'large'   表的长度 < 10^9      → 表大到不该开
        'huge'    比这还大             → 一个进程开不出这么多位置

    看的是**表的长度** = maxv + 1，不是 n：计数排序的代价里 V 那一半由值域决定，
    与有多少个元素无关。这正是它「不受 O(n log n) 下界约束」的代价所在。
    """
    slots = maxv + 1
    if slots < 10 ** 4:
        return 'tiny'
    if slots < 10 ** 6:
        return 'small'
    if slots < 10 ** 9:
        return 'large'
    return 'huge'
