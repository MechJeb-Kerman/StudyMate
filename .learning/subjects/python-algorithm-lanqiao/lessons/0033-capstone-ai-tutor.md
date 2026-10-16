---
title: 综合实战：把刷题助手做完
goal: 做出端到端可用的刷题助手：题目文本进、推荐算法出、验证过程留得下证据。
---

## 这次要做出什么

第 1 课你在纸上写了「想做什么」，答案是这个刷题助手。第 3 到 27 课把算法零件备齐了，第 28 到 32 课把工程习惯备齐了。**这一课把它做完。**

要交付的是一条**端到端能跑的流水线**：

::: note
**题目文本 → 提取题意（调模型） → 推荐候选算法 → 自动验证（对拍 + 样例） → 输出带证据的记录**

五段，逐段串起来。
:::

外加**一份说明**，讲清每个环节为什么这样设计、以及**你不放心的地方在哪**。

注意最后那半句。**「我不放心的地方在哪」比「我做了什么」更能说明你的水平。** 一个说得出「我的解析器遇到截断就废了，所以加了重试」的人，和一个说「我的助手能推荐算法」的人，做出来的东西可能一模一样，但对它的掌握完全不同。

::: quiz 应用 锚点：这次要交付的两样东西是什么
:::

## 把流程切成五段，每段定契约

流水线最常见的死法不是某一段写错，而是**段与段之间对不上**。防它的办法是把每段的**输入输出契约**写下来，而不只是写代码：

| 段 | 输入 | 输出（契约） |
| --- | --- | --- |
| 1 提取题意 | 题目文本（str） | `{title: str, constraints: {n_max: int, value_max: int}, ask: str}` |
| 2 推荐算法 | 第 1 段的 dict | `{candidates: [str], reasons: [str], picked: str}` |
| 3 写解法 | 第 2 段的 dict | `{code: str, entry: str, complexity: str}` |
| 4 验证 | 第 3 段的 dict + 数据 | `{passed: bool, evidence: [str], failing_case: str or None}` |
| 5 出记录 | 第 4 段的 dict | `{problem: str, picked: str, passed: bool, evidence: [str], seed: int, rerun: str}` |

**这张表本身就是这一课最值钱的产物之一。** 有了它，第 4 段和第 5 段就能分别开发、分别测；没有它，你只能在整条流水线跑起来的时候才发现字段名对不上——那时候你根本不知道是哪一段的问题。

::: quiz 理解 锚点：五段流程各自的契约怎么定
:::

## 模型输出不可信

第 1 段要调大模型（第 32 课后面给了 API 的用法）。**这里有一个必须一开始就承认的前提：模型返回的是一段文本，不是结构化数据。** 哪怕你在提示词里写了「只输出 JSON」，它也可能给你围栏、给你前言、或者因为长度限制被截断。

把四种真实会遇到的样子都试一遍：

```python
import json

F = '`' * 3
GOOD = '{"algorithm": "二分答案", "complexity": "O(n log C)"}'

SAMPLES = {
    '干净 JSON': GOOD,
    '带围栏': F + 'json\n' + GOOD + '\n' + F,
    '带前言': '好的，我来分析一下这道题。\n\n' + GOOD + '\n\n希望有帮助。',
    '被截断': GOOD[:40],
}


def parse_naive(raw):
    return json.loads(raw)


def parse_strip_fence(raw):
    s = raw.strip()
    if s.startswith(F):
        s = s[len(F):]
        if s.startswith('json'):
            s = s[4:]
        s = s.strip()
        if s.endswith(F):
            s = s[:-len(F)]
    return json.loads(s.strip())


def parse_extract(raw):
    """从任意位置找出第一个括号平衡的 {...} 再解析。"""
    start = raw.find('{')
    if start < 0:
        raise ValueError('没找到 {')
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == '{':
            depth += 1
        elif raw[i] == '}':
            depth -= 1
            if depth == 0:
                return json.loads(raw[start:i + 1])
    raise ValueError('括号不闭合')


print('   四种真实会遇到的模型输出：')
for k, v in SAMPLES.items():
    print(f'      {k:<10} {v[:52]!r}')
print()
print('   解析策略                       成功   失败的样本')
for name, fn in (('裸 json.loads', parse_naive),
                 ('先剥围栏', parse_strip_fence),
                 ('剥围栏 + 提取首个 JSON 对象', parse_extract)):
    ok, bad = [], []
    for k, v in SAMPLES.items():
        try:
            fn(v)
            ok.append(k)
        except Exception:
            bad.append(k)
    print(f'   {name:<30} {len(ok)}/4   {bad}')
```

```text
   四种真实会遇到的模型输出：
      干净 JSON    '{"algorithm": "二分答案", "complexity": "O(n log C)"}'
      带围栏        '```json\n{"algorithm": "二分答案", "complexity": "O(n log'
      带前言        '好的，我来分析一下这道题。\n\n{"algorithm": "二分答案", "complexity": "'
      被截断        '{"algorithm": "二分答案", "complexity": "O(n'

   解析策略                       成功   失败的样本
   裸 json.loads                   1/4   ['带围栏', '带前言', '被截断']
   先剥围栏                           2/4   ['带前言', '被截断']
   剥围栏 + 提取首个 JSON 对象             3/4   ['被截断']
```

**三档解析器，1/4 → 2/4 → 3/4。** 每加一层兜底就多救回一种。但要注意最后一档：

**「被截断」那一档，再聪明的解析器也救不回来**——因为括号根本没闭合，那不是格式问题，是**内容不完整**。救它只能靠另外两种办法：

- **让模型少说点。** 用 `response_format={"type": "json_object"}` 能让模型直接吐 JSON 对象；再让输出结构尽量扁平，别嵌套三层——**结构越短越不容易被截断**。
- **重试。** 解析失败就带着「上次输出被截断了」再问一次，或者把 `max_tokens` 调大。

**所以第 1 段的完整设计是三层，不是一层：** 提示词约束 → 解析兜底 → 失败重试。**只做第一层的人，会在某次输出变长时突然崩掉，而且不知道为什么。**

::: quiz 排错 锚点：为什么截断的 JSON 解析器救不回来
:::

## 对不上要当场喊，别静默

现在看第二种失败，它比崩掉更危险。我把五种「模块之间对不上」各注入一次，看流水线末端的报告会变成什么样：

```python
REC_SPEC = {'algorithm': str, 'complexity': str, 'passed': bool, 'evidence': list}


def check_contract(obj, spec, where):
    """字段名或类型不对就抛，并说清是哪个字段。"""
    if not isinstance(obj, dict):
        raise TypeError(f'{where}: 应该是 dict，实际是 {type(obj).__name__}')
    for k, t in spec.items():
        if k not in obj:
            raise TypeError(f'{where}: 缺字段 {k}')
        if not isinstance(obj[k], t):
            raise TypeError(f'{where}: 字段 {k} 应为 {t.__name__}，'
                            f'实际是 {type(obj[k]).__name__}')


def analyze(text):
    return {'algorithm': '二分答案', 'complexity': 'O(n log C)'}


def verify(analysis, samples):
    return {'algorithm': analysis['algorithm'],
            'complexity': analysis['complexity'],
            'passed': all(a == b for a, b in samples),
            'evidence': [f'样例{i + 1}: {a} vs {b}' for i, (a, b) in enumerate(samples)]}


def render(rec):
    return (f"{rec['algorithm']} / 复杂度 {rec['complexity']} / "
            f"验证 {'通过' if rec['passed'] else '未过'} / 证据 {len(rec['evidence'])} 条")


MUTATIONS = [
    ('字段名漂移', lambda r: {('algo' if k == 'algorithm' else k): v for k, v in r.items()}),
    ('少一个字段', lambda r: {k: v for k, v in r.items() if k != 'complexity'}),
    ('证据转字符串', lambda r: {**r, 'evidence': '；'.join(r['evidence'])}),
    ('布尔转字符串', lambda r: {**r, 'passed': str(r['passed'])}),
    ('整体换成列表', lambda r: [r['algorithm'], r['complexity'], r['passed'], r['evidence']]),
]
# 这一组样例里第二个对不上，所以正确答案是「未过」
SAMPLES2 = [('13', '13'), ('7', '8')]
RIGHT = render(verify(analyze('题目'), SAMPLES2))
print(f'   正确答案长这样：{RIGHT}')
print()
print('   错法            不查契约时           查契约时')
silent = crash = 0
for name, mut in MUTATIONS:
    rec = mut(verify(analyze('题目'), SAMPLES2))
    try:
        out = render(rec)
        if out == RIGHT:
            kind, shown = '没出错', out
        else:
            kind, shown = '静默错', out
            silent += 1
    except Exception as e:
        kind, shown = '当场崩', f'{type(e).__name__}'
        crash += 1
    try:
        check_contract(rec, REC_SPEC, 'record')
        verdict = '（契约也放过）'
    except TypeError as e:
        verdict = str(e).split('，')[0]
    print(f'   {name:<12} {kind}  {shown[:30]:<30} {verdict}')
print(f'   合计：静默错 {silent} 种、当场崩 {crash} 种（共 {len(MUTATIONS)} 种注入）')
```

```text
   正确答案长这样：二分答案 / 复杂度 O(n log C) / 验证 未过 / 证据 2 条

   错法            不查契约时           查契约时
   字段名漂移        当场崩  KeyError                       record: 缺字段 algorithm
   少一个字段        当场崩  KeyError                       record: 缺字段 complexity
   证据转字符串       静默错  二分答案 / 复杂度 O(n log C) / 验证 未过  record: 字段 evidence 应为 list
   布尔转字符串       静默错  二分答案 / 复杂度 O(n log C) / 验证 通过  record: 字段 passed 应为 bool
   整体换成列表       当场崩  TypeError                      record: 应该是 dict
   合计：静默错 2 种、当场崩 3 种（共 5 种注入）
```

**五种注入，三种当场崩，两种静默错。** 静默的那两种才是要防的：

- **「证据转字符串」**：报告写「证据 2 条」，其实那一行是 `len()` 数了字符串的**字符数**。恰好 2 条的时候它连数字都对——因为 `"样例1: 13 vs 13；样例2: 7 vs 8"` 的字符数不是 2，所以这里露了。但如果证据只有一条、或者拼接方式不同，它可能一直是对的。
- **「布尔转字符串」**：报告写着**「验证 通过」**，而正确答案是**「未过」**。原因在 Python 里：`'False'` 是一个**非空字符串**，非空字符串在布尔语境里是 `True`。所以 `'通过' if 'False' else '未过'` 给出「通过」。**这一条没有任何异常、没有任何警告、日志干干净净，产物是错的。**

**这就是为什么契约检查要放在每两段之间**，而不是只在最后做一次总检查：

| 做法 | 崩掉的那 3 种 | 静默的那 2 种 |
| --- | --- | --- |
| 不查契约 | 在**下游深处**崩，错误信息指向用得最远的地方 | 完全查不出来 |
| 每段之间查 | 在**边界**就被点名「缺字段 algorithm」 | 在**边界**就被点名「字段 passed 应为 bool」 |

**契约检查的价值不在「能查出错误」，而在「在错误发生的那一层就把错误指出来」。** 崩在下游的时候，你要沿着调用链往回找五段才知道是谁写坏了；契约在边界，它直接告诉你哪一段的哪个字段不对。

::: quiz 理解 锚点：为什么静默错误比当场崩更危险
:::

## 留证：记种子还是记数据

最后一段要输出「可复现的记录」。第 15 课讲过对拍要固定种子，但**固定种子只保证了「同一个环境下可以复现」**：

```python
import random


def gen_v1(seed):
    rng = random.Random(seed)
    return sorted(rng.sample(range(1, 1000), 5))


def gen_v2(seed):
    """换了采样写法（模拟升级 Python 或重构）——同一个种子，不同的数据。"""
    rng = random.Random(seed)
    pool = list(range(1, 1000))
    rng.shuffle(pool)
    return sorted(pool[:5])


SEED = 20260301
print(f'   同一个种子 {SEED}，两种采样写法各给一批数据：')
print(f'      v1（现在用的 sample）      {gen_v1(SEED)}')
print(f'      v2（改成 shuffle 再切片）  {gen_v2(SEED)}')
print(f'   两版一致吗: {gen_v1(SEED) == gen_v2(SEED)}')
print()
print('   所以产物里到底该记什么：')
print(f'      只记 seed  → 换版本后照着重放，得到的是 v2 那批 {gen_v2(SEED)}，对不上')
print(f'      记下数据本身 → 无论什么版本，数据就是 {gen_v1(SEED)}，永远重放得出来')
print()


def run_careful(seed):
    """既存 seed 也存数据。"""
    rng = random.Random(seed)
    return {'seed': seed, 'cases': sorted(rng.sample(range(1, 1000), 5))}


def run_forgetful(seed):
    """用了种子，但没写进产物——事后无从知道这批数据是怎么来的。"""
    rng = random.Random(seed)
    return {'cases': sorted(rng.sample(range(1, 1000), 5))}


careful = [run_careful(SEED) for _ in range(3)]
forgetful = [run_forgetful(s) for s in (101, 202, 303)]
print('   对比两种产物的可复现性：')
print(f'      存了 seed 的那版，三次重放的数据一致吗: {careful[0] == careful[1] == careful[2]}')
print(f'      没存 seed 的那版，产物里能看出用了什么种子吗: {"seed" in forgetful[0]}')
print(f'      没存 seed 的那版，三次的数据一样吗: {forgetful[0] == forgetful[1] == forgetful[2]}')
print(f'      没存 seed 的那版，产物里有数据本身吗: {"cases" in forgetful[0]}')
```

```text
   同一个种子 20260301，两种采样写法各给一批数据：
      v1（现在用的 sample）      [146, 304, 688, 843, 854]
      v2（改成 shuffle 再切片）  [48, 444, 608, 719, 900]
   两版一致吗: False

   所以产物里到底该记什么：
      只记 seed  → 换版本后照着重放，得到的是 v2 那批 [48, 444, 608, 719, 900]，对不上
      记下数据本身 → 无论什么版本，数据就是 [146, 304, 688, 843, 854]，永远重放得出来

   对比两种产物的可复现性：
      存了 seed 的那版，三次重放的数据一致吗: True
      没存 seed 的那版，产物里能看出用了什么种子吗: False
      没存 seed 的那版，三次的数据一样吗: False
      没存 seed 的那版，产物里有数据本身吗: True
```

**同一个种子，两种写法给出完全不同的两批数据。** 所以：

- **只记 seed 不够。** 你换了 Python 版本、改了随机调用的顺序、或者只是把 `sample` 改成 `shuffle` 再切片，同一个种子的含义就变了。**记种子的复现能力绑在实现细节上。**
- **记数据本身才稳。** 产物里把**实际用到的测试数据**原样存下来，无论什么版本、什么实现，翻出这份数据就能重放。**这是「留证」这个词的字面意思：留的应该是证据，不是产生证据的过程。**

**实用做法是两个都记**：`seed` 用来快速重跑一遍（方便），`cases` 用来应付「别人拿着你的记录要复现」（可靠）。**第 15 课让你固定种子是对的，这一课要再往前一步：种子是方便的复现手段，数据才是可靠的复现依据。**

::: quiz 理解 锚点：留证为什么要记数据而不只记种子
:::

## 怎么算过

这一课判五件事：

1. **端到端能跑。** 给一段题目文本，能一路跑到出记录，中途不用手工改文件、不用手工贴数据。
2. **五段的契约都写下来了**，并且每两段之间有检查。**注入一个类型错误，报错要指向出错的那一段**，而不是指向五层之外。
3. **记录里有证据。** 至少包含：用到的测试数据、每组的通过情况、以及**不合格时的第一个反例**。光写一个「通过」不算。
4. **可复现。** 拿着记录里的东西（seed 和数据），**在另一台机器或另一次运行里能重放出同样的结论**。
5. **说明里写了「我不放心的地方」。** 至少一条，并且说清它的触发条件。**这一条是硬要求**——一份没有「不确定」的说明，说明你没真正检查过自己的东西。

## 怎么跑

```sh
# 1) 先跑通最简的一条线：写死一段题目文本，一路跑到出记录
# 2) 换成真实调用：接上 API，把 key 放进环境变量，不要写进代码
# 3) 把四种模型输出（干净 / 围栏 / 前言 / 截断）各灌一次，确认三层兜底都生效
# 4) 故意注入一个字段名漂移，确认契约检查在边界就点名
# 5) 跑两遍完整流程，对比记录——确认能重放出同样的结论
# 6) 写说明，点名至少一处你不放心的地方
```

::: practice 上手做 | 六步把助手做完

这一课的动手部分落在 lab 里（任务与断言见 [lab/0033-capstone-ai-tutor/](../lab/0033-capstone-ai-tutor/)，做完对照 [lab/solutions/](../lab/solutions/)）。要做的是六件事。

1. **先把契约表写出来。** 照第 2 节那张五行表，**写下你自己这五段的输入输出**。字段名、类型、哪一段可以返回 `None`。**这一步在写代码之前做完。**
2. **跑通最简的一条线。** 题目文本写死在代码里，模型调用先写成一个固定返回的函数（**先不接真 API**），一路跑到出记录。目的是先把接口对齐，别把「接口不对」和「模型不听话」两个问题混在一起。
3. **接上真实调用。** 用 [DeepSeek API](https://api.deepseek.com) 那套接口，key 放环境变量。**这一步才第一次面对真实的模型输出**——照着第 3 节那三层做兜底。
4. **灌四种输出。** 干净 JSON、带围栏、带前言、被截断，各灌一次，记录你的解析器分别怎么处理。**「被截断」那一次必须走重试，不能悄悄吞掉。**
5. **注入契约错误。** 故意把某一段的字段名改一个字，确认报错**指向那一层**并说清是哪个字段。改回来。
6. **跑两遍并留证。** 两遍完整流程的记录要能对比出「结论一致」。记录里要有数据本身，不只是 seed。

:::

## 自查清单

- 五段契约都写下来了，每两段之间有检查。
- 模型输出的四层兜底都试过，截断走重试而不是静默吞掉。
- 记录里有**用到的数据本身**，不只是 seed。
- 两遍完整流程能得出同一个结论。
- 记录里有「不合格时的第一个反例」，不是一个光秃秃的「通过」。
- 说明里点名了至少一处**你不放心的地方**，并写了触发条件。
- API key 没有写进代码，走的是环境变量。
- 提交前用第 30 课那份清单过了一遍。

## 最可能卡在哪

- **接口不对和模型不听话混在一起查。** 先用固定返回的函数跑通（第 2 步），再接真 API（第 3 步）。这两件事分开查，各自都简单。
- **只做提示词约束，不做解析兜底。** 提示词说「只输出 JSON」在大多数时候有效，所以你会以为它总是有效。灌一次带围栏的输出就知道了。
- **把 `passed` 写成字符串。** `'False'` 是非空字符串，在布尔语境里是 `True`。这类错**不报错、日志干净、产物是错的**——本课块 2 那个「验证 通过」就是它。
- **只记 seed 就以为可复现。** 换版本、改调用顺序都会让种子变意思。**记数据。**
- **只追求跑通，讲不清取舍。** 这一课的说明里要写「为什么这么设计」和「哪里不放心」，写不出来说明那些决定是抄来的。
- **API key 写进代码。** 走环境变量。这条没有例外。

::: quiz 排错 锚点：为什么模型输出的 JSON 不能直接解析
:::

## 卡壳顺序

1. **先分清是接口问题还是模型问题。** 换成固定返回的函数，还错就是接口；不错了就是模型侧。
2. **错在最后一段，先往上游找契约。** 五段流水线里，报错位置几乎总是下游。
3. **模型返回的内容先原样打出来看。** 别看解析后的结果——`json.loads` 报的错从来不告诉你原文长什么样。
4. **解析失败先判断是格式还是截断。** 找得到 `{` 找不到配对的 `}` 就是截断，去调 `max_tokens` 或缩短输出结构。
5. **结论对不上，先查证据够不够。** 记录里没有实际用到的数据，你连「哪一组错了」都不知道。
6. **说明写不出来，说明这个决定不是你做的。** 回到对应那一课重看设计理由。

## 做完之后

这就是从第 1 课「能跑一道题」长成的最终形态。**回头看一遍这 33 课，你手上多了三样东西：**

- **一套算法知识**（第 3 到 26 课），而且每一项都能讲清它什么时候失效（第 32 课）。
- **一套工程习惯**：看规模挑算法（第 28 课）、量出来再优化（第 29 课）、提交前自检（第 30 课）、限时选题（第 31 课）。
- **一个能用的工具**——它不只是作业，是你以后刷题时真会打开的东西。

::: tip
第 1 课那份「想学什么」还留着的话，翻出来对一遍。**当时写下的目标，现在做到了几条？** 没做到的不用急着补，先写下来它为什么没做到——那通常比做到的那几条更有信息量。
:::

::: resources
- [DeepSeek API 文档](https://api.deepseek.com) | 官方 · 本课第 1 段用的接口，含 `response_format` 与重试相关说明
- [Python 官方文档 · json](https://docs.python.org/3/library/json.html) | 官方 · `json.loads` 的报错种类，判断格式问题还是截断问题
- [Python 官方文档 · random](https://docs.python.org/3/library/random.html) | 官方 · 种子的语义与「同一版本内可复现」这个前提
- [第 15 课：实验二：用暴力解验证你的答案](0015-lab-02-verify-by-brute-force.html) | 本课第 4 段「验证」的全部内容
- [第 27 课：实验三：让助手推荐并验证](0027-lab-03-recommend-and-verify.html) | 这个助手的前一版，本课把它收成完整流水线
- [第 30 课：交卷之前你要检查什么](0030-stress-test-and-review.html) | 本课「留证」与自检清单的出处
- [第 32 课：把算法讲给别人听](0032-explain-like-a-teacher.html) | 本课说明里「讲清设计取舍」那一条的标准
:::
