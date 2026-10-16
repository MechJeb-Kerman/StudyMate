#!/usr/bin/env python3
r"""lab 0031 · 判分数据生成器（与两侧逐字节相同的支持文件）

这一课的判分数据不是手写的一堆文件，而是**用固定种子现算出来的**：
同一份 `generate()` 在任何时候、任何机器上跑，交回的都是同一批数据。
所以 `problems/manifest.json` 里只写「每题几组、多大」，数据本身在这里。

`generate()` 交回 `一位题号 → [(组名, 输入文本, 这一组在考什么, 生成用的人话)]`，
`score.py` 与 `run_tests.py` 都只调它，谁都不另写一份数据。
"""

from __future__ import annotations

import random

# ── 小工具 ────────────────────────────────────────────────────────────

ALPHA_SMALL = 'abc'
ALPHA_TWO = 'ab'
DIGITS = '0123456789'


def rand_str(rng, size, alpha):
    return ''.join(rng.choice(alpha) for _ in range(size))


def rand_list(rng, size, low, high):
    return [rng.randint(low, high) for _ in range(size)]


def line(*values):
    return ' '.join(str(v) for v in values)


# ── p1 · 舞台高度（二分答案）──────────────────────────────────────────

def gen_p1():
    cases = []

    # 1) 样例 1：能透过二分看见答案怎么变的
    cases.append(('case01',
                  line(6, 4) + '\n' + line(9, 1, 1, 4, 4, 4) + '\n',
                  '样例 1：n = 6、k = 4，答案是 4',
                  '手算：h=4 → 2+0+0+1+1+1 = 5 ≥ 4，h=5 → 1 < 4'))

    # 2) 样例 2：k 只比「h = 1 时的座位数」少一点点，答案被压到最小高度 1
    cases.append(('case02',
                  line(5, 100) + '\n' + line(100, 3, 60, 25, 8) + '\n',
                  '样例 2：k = 100，而 h = 1 时刚好 194 个座位、h = 2 时只剩 97 个，答案是 1',
                  '手算：h=1 → 100+1+60+25+8 = 194 ≥ 100；h=2 → 50+1+30+12+4 = 97 < 100'))

    # 3) 只有一个人：答案就是他自己偏好的高度
    cases.append(('case03', line(1, 1) + '\n' + line(1000000000) + '\n',
                  '只有一个观众，答案 = 他的偏好高度 10^9',
                  '边界：n = 1，二分区间只有 10^9 一个候选'))

    # 4) 全部同值、k = n：答案 = 这个值本身
    cases.append(('case04', line(200, 200) + '\n' + line(*([1000000000] * 200)) + '\n',
                  '200 个观众偏好都是 10^9、k = 200，答案 = 10^9',
                  '边界：所有 a_i 相同，count(h) 只在 h = a_i 处跳变'))

    # 5) 随机中档：n = 2000，答案落在中间
    rng = random.Random(3101)
    a = rand_list(rng, 2000, 1, 10000)
    cases.append(('case05', line(2000, 1234) + '\n' + line(*a) + '\n',
                  'n = 2000 随机，k = 1234，看二分收敛对不对',
                  '数据本身是随机的，但种子固定 3101'))

    # 6) 大数据：n = 2×10^5、a_i ≤ 10^9 —— 「从 1 枚举到 max」那一版在这里超时
    rng = random.Random(3102)
    a = rand_list(rng, 200000, 1, 10 ** 9)
    k = sum(a) // 5
    cases.append(('case06', line(200000, k) + '\n' + line(*a) + '\n',
                  'n = 2×10^5、a_i ≤ 10^9：必须 O(n log V)，枚举高度做不完',
                  'k 取总座位数的五分之一，答案落在中高位'))
    return cases


# ── p2 · 四边形合并（区间 DP）────────────────────────────────────────

def gen_p2():
    cases = []

    cases.append(('case01', line(5) + '\n' + line(1, 2, 3, 4, 5) + '\n',
                  '样例 1：n = 5，答案是 21（唯一那条合并路线）',
                  '3+3+9+6 = 21'))

    cases.append(('case02', line(3) + '\n' + line(4, 1, 9) + '\n',
                  '样例 2：n = 3，一次合并，答案 = 三个数之和',
                  '边界：最小可合并规模'))

    cases.append(('case03', line(1) + '\n' + line(6) + '\n',
                  'n = 1：本来就是一堆，代价 0',
                  '边界：不合并'))

    cases.append(('case04', line(4) + '\n' + line(1, 2, 3, 4) + '\n',
                  'n 是偶数：每次少两堆，永远合不到一堆，输出 -1',
                  '边界：(n - 1) % 2 == 1'))

    rng = random.Random(3201)
    a = rand_list(rng, 41, 1, 10 ** 9)
    cases.append(('case05', line(41) + '\n' + line(*a) + '\n',
                  'n = 41，a_i ≤ 10^9：答案会超过 32 位',
                  '随机，种子 3201'))

    rng = random.Random(3202)
    a = rand_list(rng, 299, 1, 10 ** 9)
    cases.append(('case06', line(299) + '\n' + line(*a) + '\n',
                  'n = 299：区间 DP 的最大规模，O(n^3) 在这里是极限',
                  '随机，种子 3202；参考解约 1.6 秒（本机）'))
    return cases


# ── p3 · 数颜色（离线 + 树状数组）────────────────────────────────────

def gen_p3():
    cases = []

    cases.append(('case01',
                  line(4, 3) + '\n' + line(1, 2, 1, 3) + '\n'
                  + line(2, 4) + '\n' + line(1, 1) + '\n' + line(1, 4) + '\n',
                  '样例：重复颜色只算一次',
                  '手算：3 / 1 / 3'))

    cases.append(('case02', line(1, 1) + '\n' + line(7) + '\n' + line(1, 1) + '\n',
                  'n = q = 1：只问一个位置',
                  '边界：单元素'))

    rng = random.Random(3301)
    a = rand_list(rng, 20, 1, 3)
    queries = [(1, 20), (1, 1), (20, 20), (5, 15)]
    body = '\n'.join(line(l, r) for l, r in queries)
    cases.append(('case03', line(20, 4) + '\n' + line(*a) + '\n' + body + '\n',
                  '颜色只有 3 种、n = 20：重复度极高，答案离「区间长度」很远',
                  '随机，种子 3301；四组询问都是固定的边界'))

    rng = random.Random(3302)
    a = rand_list(rng, 3000, 1, 3000)
    queries = []
    for _ in range(3000):
        left = rng.randint(1, 3000)
        right = rng.randint(left, 3000)
        queries.append((left, right))
    body = '\n'.join(line(l, r) for l, r in queries)
    cases.append(('case04', line(3000, 3000) + '\n' + line(*a) + '\n' + body + '\n',
                  'n = q = 3000：O(nq) 的现场数颜色在这里是 9×10^6 次起步',
                  '随机，种子 3302'))

    rng = random.Random(3303)
    a = rand_list(rng, 200000, 1, 300)
    queries = []
    for _ in range(200000):
        left = rng.randint(1, 200000)
        right = rng.randint(left, 200000)
        queries.append((left, right))
    body = '\n'.join(line(l, r) for l, r in queries)
    cases.append(('case05', line(200000, 200000) + '\n' + line(*a) + '\n' + body + '\n',
                  'n = q = 2×10^5、颜色只有 300 种：必须离线 + 树状数组',
                  '随机，种子 3303'))

    rng = random.Random(3304)
    a = rand_list(rng, 200000, 1, 10 ** 9)
    queries = [(1, 200000)]
    for _ in range(199999):
        left = rng.randint(1, 200000)
        right = rng.randint(left, 200000)
        queries.append((left, right))
    body = '\n'.join(line(l, r) for l, r in queries)
    cases.append(('case06', line(200000, 200000) + '\n' + line(*a) + '\n' + body + '\n',
                  '颜色范围到 10^9（要离散化）、并且带一个整段询问',
                  '随机，种子 3304'))
    return cases


# ── p4 · 最长公共子串（二分 + 双哈希）────────────────────────────────

def build_common(rng, size, alpha, common):
    """造一个长度为 size 的串，里面**恰好埋着** common 这一段。"""
    text = [rng.choice(alpha) for _ in range(size)]
    where = rng.randint(0, size - len(common))
    text[where:where + len(common)] = list(common)
    return ''.join(text), where


def gen_p4():
    cases = []

    cases.append(('case01', 'ababc\nbabc\n',
                  '样例 1：公共子串是 bab / abc，长度 3',
                  '手算：3'))

    cases.append(('case02', 'abcde\nfghij\n',
                  '样例 2：一个字符都不重合，答案 0',
                  '边界：没有公共子串'))

    cases.append(('case03', 'aaaaa\naaa\n',
                  '一个串是另一个的前缀：答案是最短的那个的长度',
                  '边界：答案 = min(n, m)'))

    rng = random.Random(3401)
    base = rand_str(rng, 2000, ALPHA_SMALL)
    common = base[700:1300]
    s, where_a = build_common(rng, 2000, ALPHA_SMALL, common)
    t, where_b = build_common(rng, 2000, ALPHA_SMALL, common)
    cases.append(('case04', s + '\n' + t + '\n',
                  'n = m = 2000：埋进一段长度 600 的公共子串；三个字母的随机串还会'
                  '自己撞出更长的重复，所以答案由参考解现算',
                  '随机，种子 3401；埋进去的位置是 ' + str(where_a) + ' 与 ' + str(where_b)))

    rng = random.Random(3402)
    base = rand_str(rng, 600, 'ab')
    common = base[:600]
    s, _ = build_common(rng, 100000, 'ab', common)
    t, _ = build_common(rng, 100000, 'ab', common)
    cases.append(('case05', s + '\n' + t + '\n',
                  'n = m = 10^5、字母表只有两个字符：公共子串会比自己埋的那段还长，'
                  '必须 O((n+m) log) 才跑得动',
                  '随机，种子 3402；埋进长度 600 的一段，答案由参考解现算'))

    rng = random.Random(3403)
    base = rand_str(rng, 5000, ALPHA_TWO)
    common = base[1000:5000]
    s, _ = build_common(rng, 100000, ALPHA_TWO, common)
    t, _ = build_common(rng, 100000, ALPHA_TWO, common)
    cases.append(('case06', s + '\n' + t + '\n',
                  'n = m = 10^5、字母表只有两个字符、公共子串长度 4000',
                  '随机，种子 3403；答案大，哈希滚动不能出错'))
    return cases


# ── p5 · 雨天迷宫（0-1 BFS）──────────────────────────────────────────

def gen_p5():
    cases = []

    cases.append(('case01', '1 1\n.\n',
                  '样例 1：起点就是终点，代价 0',
                  '边界：n = m = 1'))

    cases.append(('case02', '3 3\n.bb\nb.b\nbb.\n',
                  '样例 2：这个网格里没有裂冰也没有墙，每步都是 1，最短 4 步',
                  '手算：只有 ' + "'b'" + '，按步数算'))

    cases.append(('case03', '3 3\n.#b\n#b.\nb.b\n',
                  '起点被墙封住（两个邻格都是 #，对角走不过去）——输出 -1',
                  '边界：不可达'))

    cases.append(('case04', '2 3\n.--\nbb.\n',
                  '样例 3：绕开完整冰走那两格连着的裂冰，代价 2',
                  '手算：(0,1) 与 (0,2) 都是裂冰，从它们之间穿过去不要钱'))

    rng = random.Random(3501)
    rows = [''.join(rng.choice('.bb') for _ in range(60)) for _ in range(60)]
    rows[0] = '.' + rows[0][1:]
    rows[-1] = rows[-1][:-1] + '.'
    cases.append(('case05', line(60, 60) + '\n' + '\n'.join(rows) + '\n',
                  '60×60 随机网格、没有裂冰也没有墙：每步都是 1，'
                  '答案就是最短路的步数',
                  '随机，种子 3501'))

    rng = random.Random(3502)
    n = m = 600
    # 先铺满 '.'，再撒完整冰（四分之一）；然后沿第 0 列与第 k 行挖一条 L 形裂冰走廊。
    # 走廊内部的每一步都是「裂冰 → 裂冰」，代价 0；只有两端那两步要付钱，
    # 所以答案确定是 2，而把每步都当 1 的写法会算成 1198。
    rows = [['.'] * m for _ in range(n)]
    for r in range(n):
        for c in range(m):
            if rng.random() < 0.25:
                rows[r][c] = 'b'
    k = n // 2
    for r in range(1, k + 1):
        rows[r][0] = '-'
    for c in range(1, m):
        rows[k][c] = '-'
    rows[0][0] = '.'
    rows[0][1] = '.'
    rows[n - 1][m - 1] = '.'
    body = '\n'.join(''.join(row) for row in rows)
    cases.append(('case06', line(n, m) + '\n' + body + '\n',
                  '600×600：36 万个格子、四分之一是完整冰，沿第 0 列与第 k 行有一条'
                  'L 形裂冰走廊——整条路 1198 步里有 1197 步免费，最小代价只有 300'
                  '（走廊两端各付 1），把每步都当 1 会算成 1198',
                  '随机，种子 3502；L 形走廊挖成裂冰，期望值由参考解现算'))
    return cases


GENERATORS = {
    'p1': gen_p1,
    'p2': gen_p2,
    'p3': gen_p3,
    'p4': gen_p4,
    'p5': gen_p5,
}


def generate():
    """现算全部判分数据 → {题号: [(组名, 输入文本, 考什么, 怎么造的)]}。"""
    return {pid: maker() for pid, maker in GENERATORS.items()}
