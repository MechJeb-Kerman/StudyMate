"""任务 1 · 造提示词，四样约束一个不少（lab 0027）· 参考解

这一课要做的助手是：题目文本进 → 判断它像哪一类算法 → 给出候选实现 → 自动跑验证 → 出结论。

第一段就是**提示词**。它看起来只是「把题目裹起来」，其实不是：既然下一步要用**程序**
解析返回的那段文本，提示词里就必须把**格式**钉死。四样东西缺一样后面就会出麻烦：

    1. 输出格式（格式固定为：…）——后面要按这个键名取值；
    2. 不许有别的文字、不许用代码块围栏——减少解析要处理的形态；
    3. 取值范围（可选的算法族：…）——不限定的话，模型可能给出项目里根本没有对应实现的名字；
    4. 转义的约定（字符串里的引号必须转义）——这是最难察觉的一条。

第 4 条为什么最难察觉：它是**唯一一条解析器救不了的**。围栏、前后解释这类格式浮动，
解析器多剥一层就处理掉了；而字符串内容里没转义的引号会让 JSON 本身不合法
（题目说"最小化最大值" 那对引号），括号配平、位置也对，找大括号的招数一条都用不上。

`call_model` 是**唯一**的联网点，它在离线环境里直接抛 NotImplementedError。
所有不可控的东西（网络、时间、随机）都收在这一处，其余部分就都成了纯逻辑，
可以反复跑、可以对拍——这就是课件里说的那道**缝**。

跑： py task1_prompt.py
判： py run_tests.py
"""

from tools import FAMILIES, FENCE, fence_line_count, show_banner


def build_prompt(problem):
    """把题面裹成一条有格式约束的提示词，交回一个字符串。"""
    return (
        '你是一个算法助教。读下面的题目，判断它最像哪一类算法。\n'
        '\n'
        '只输出一个 JSON 对象，不要输出任何别的文字，不要用代码块围栏。\n'
        '格式固定为：\n'
        '{"family": "<算法族名>", "confidence": "高|中|低", "why": "<一句话理由>"}\n'
        '字符串里的引号必须转义，写成 \\" 这个样子。\n'
        '\n'
        '可选的算法族：二分答案、并查集、堆、图的搜索、背包、贪心、前缀和、双指针。\n'
        '\n'
        '题目：\n' + problem.strip()
    )


def call_model(prompt):
    """真正跑的时候这里发一次 API 请求；离线测试时换成假的。

    这一课不联网：这里唯一的职责就是**明确地失败**。别写成悄悄交回空串——
    那样「忘了换掉这个函数」会静默地变成「模型返回空」，比直接报错难查得多。
    """
    raise NotImplementedError('离线环境不联网，测试时请换掉这个函数')


def fake_model(prompt):
    """假的模型：只认题目里有没有「木头」这个词，用来离线跑通链路。"""
    if '木头' in prompt:
        return '{"family": "二分答案", "confidence": "高", "why": "要让最小长度最大化"}'
    return '{"family": "贪心", "confidence": "中", "why": "没认出来，先猜一个"}'


def recommend(problem, model):
    """题目进、候选算法出。model 就是那道缝。

    到「拿到那段文本」为止，**不解析**——解析是任务 2 的事。
    模型必须是参数，不写默认值：判分就是拿它自己的假模型来试这条链通不通的。
    """
    prompt = build_prompt(problem)
    raw = model(prompt)
    return raw


if __name__ == '__main__':
    show_banner('0027 提示词长这样')
    problem = '有 n 根木头，要切成 k 段等长的小段。求每小段最长的长度，即让最小长度最大化。'
    prompt = build_prompt(problem)
    print('   —— 提示词长这样 ——')
    for line in prompt.splitlines():
        print('   | ' + line)
    print()

    show_banner('0027 接上假的模型，链路照样跑')
    try:
        real = recommend(problem, call_model)
        print('   真模型返回: ' + str(real))
    except NotImplementedError as exc:
        print('   真模型还没接: NotImplementedError ' + str(exc))
    print('   假模型返回: ' + str(recommend(problem, fake_model)))

    show_banner('0027 取值范围与围栏')
    print('   可选算法族共 ' + str(len(FAMILIES)) + ' 个: '
          + '、'.join(name for name, _ in FAMILIES))
    print('   围栏那一串的长度 ' + str(len(FENCE)) + ' 个反引号')
    print('   提示词里的围栏行 ' + str(fence_line_count(prompt)))
