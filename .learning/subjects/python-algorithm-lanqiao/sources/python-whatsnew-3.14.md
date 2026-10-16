<!-- archived by resource-scout
     title: Python 3.14 有什么新变化（官方文档·中文）
     source: https://docs.python.org/zh-cn/3/whatsnew/3.14.html
-->

# Python 3.14 有什么新变化

编者:

Adam Turner 和 Hugo van Kemenade

本文介绍了 Python 3.14 相比 3.13 增加的新特性。 Python 3.14 发布于 2025 年 10 月 7 日。 要了解详细信息，请参阅 [更新日志](https://docs.python.org/zh-cn/3/whatsnew/changelog.html#changelog)。

参见

[**PEP 745**](https://peps.python.org/pep-0745/) -- Python 3.14 发布计划

## 摘要 -- 发布重点

Python 3.14 是 Python 编程语言的最新稳定发布版，包含多项针对语言、实现和标准库的改变。 最大的变化包括 模板字符串字面值, 标注的迟延求值，以及在标准库中对 子解释器 的支持。

标准库的变化包括大幅改进 在 asyncio 中的内省 的功能，新增 [`compression.zstd`](https://docs.python.org/zh-cn/3/library/compression.zstd.html#module-compression.zstd) 模块以 支持 Zstandard，REPL 中的语法高亮，还有用户友好度和正确性方面的改进。

本文并不试图提供所有新特性的完整规范说明，只是给出一个便捷的概览。 要了解完整细节请参阅相应文档，如 [标准库参考](https://docs.python.org/zh-cn/3/library/index.html#library-index) 和 [语言参考](https://docs.python.org/zh-cn/3/reference/index.html#reference-index)。 要了解某项改变的完整实现和设计理念，请参阅相应新特性的 PEP；但请注意一旦某项特性已完全实现则相应 PEP 通常不会再持续更新。 请参阅 移植到 Python 3.14 了解如何从较早的 Python 版本进行升级的指导。

---

解释器的改进:

-

[**PEP 649**](https://peps.python.org/pep-0649/) 和 [**PEP 749**](https://peps.python.org/pep-0749/): 标注的迟延求值

-

[**PEP 734**](https://peps.python.org/pep-0734/): 标准库中的多解释器

-

[**PEP 750**](https://peps.python.org/pep-0750/): 模板字符串

-

[**PEP 758**](https://peps.python.org/pep-0758/): 允许不带圆括号的 except 和 except* 表达式

-

[**PEP 765**](https://peps.python.org/pep-0765/): finally 代码块中的控制流

-

[**PEP 768**](https://peps.python.org/pep-0768/): 安全的 CPython 外部调试器接口

-

一种新的解释器类型

-

自由线程模式的改进

-

改进的错误消息

-

增量式垃圾回收

标准库中的重大改进：

-

[**PEP 784**](https://peps.python.org/pep-0784/): 标准库中的 Zstandard 支持

-

asyncio 内省能力

-

并发安全的警告控制

-

默认交互式 shell 中的语法高亮，以及多个标准库 CLI 中的彩色输出

C API 的改进：

-

[**PEP 741**](https://peps.python.org/pep-0741/): Python 配置 C API

平台支持：

-

[**PEP 776**](https://peps.python.org/pep-0776/): 现在 Emscripten 是 官方支持的平台，处于 [**第 3 层级**](https://peps.python.org/pep-0011/#tier-3)。

发布包的变更：

-

[**PEP 779**](https://peps.python.org/pep-0779/): 自由线程 Python 已获官方支持

-

[**PEP 761**](https://peps.python.org/pep-0761/): 官方发布包已停止使用 PGP 签名

-

Windows 和 macOS 二进制发布包现已支持实验性的即时编译器

-

现已提供针对 Android 的二进制发布包

## 新的特性

### [**PEP 649**](https://peps.python.org/pep-0649/) & [**PEP 749**](https://peps.python.org/pep-0749/): 标注的迟延求值

在函数、类和模块上的 [标注](https://docs.python.org/zh-cn/3/glossary.html#term-annotation) 将不再被立即求值。 相反，标注会被存储在专门的 [标注函数](https://docs.python.org/zh-cn/3/glossary.html#term-annotate-function) 中并仅在必要时进行求值 (除非使用了 `from __future__ import annotations`)。

这一改进旨在使得 Python 中的标注在大多数情况下具有更好的性能和可用性。 定义标注的运行时开销被最小化，但仍可在运行时对标注进行内省。 当标注包含前向引用时也不再需要将其包裹在字符串中。

新引入的 [`annotationlib`](https://docs.python.org/zh-cn/3/library/annotationlib.html#module-annotationlib) 模块提供了检查延迟注解的工具。注解可以通过以下格式进行求值：[`VALUE`](https://docs.python.org/zh-cn/3/library/annotationlib.html#annotationlib.Format.VALUE) 格式（将注解求值为运行时值，类似于早期Python版本的行为）、[`FORWARDREF`](https://docs.python.org/zh-cn/3/library/annotationlib.html#annotationlib.Format.FORWARDREF) 格式（用特殊标记替换未定义名称）、[`STRING`](https://docs.python.org/zh-cn/3/library/annotationlib.html#annotationlib.Format.STRING) 格式（以字符串形式返回注解）。

以下示例展示了这些格式的具体行为：

```
>>> from annotationlib import get_annotations, Format
>>> def func(arg: Undefined):
...     pass
>>> get_annotations(func, format=Format.VALUE)
Traceback (most recent call last):
  ...
NameError: name 'Undefined' is not defined
>>> get_annotations(func, format=Format.FORWARDREF)
{'arg': ForwardRef('Undefined', owner=<function func at 0x...>)}
>>> get_annotations(func, format=Format.STRING)
{'arg': 'Undefined'}
```

移植 一节包含了有关因这些改变而可能需要的修改指导，不过大大部分情况下，原来的代码将可继续工作。

（由 Jelle Zijlstra 在 [**PEP 749**](https://peps.python.org/pep-0749/) 和 [gh-119180](https://github.com/python/cpython/issues/119180) 中贡献；[**PEP 649**](https://peps.python.org/pep-0649/) 由 Larry Hastings 编写。）

参见

[**PEP 649**](https://peps.python.org/pep-0649/)

使用描述器进行标注的迟延求值

[**PEP 749**](https://peps.python.org/pep-0749/)

实现 PEP 649

### [**PEP 734**](https://peps.python.org/pep-0734/): 标准库中的多解释器

CPython 运行时支持在同一个进程中同时运行多个 Python 的副本并且已经这样做了 20 多年。 每个这样的副本被称为‘解释器’。 不过，该特性过去只能通过 [C-API](https://docs.python.org/zh-cn/3/c-api/subinterpreters.html#sub-interpreter-support) 来使用。.

由于新增的 [`concurrent.interpreters`](https://docs.python.org/zh-cn/3/library/concurrent.interpreters.html#module-concurrent.interpreters) 模块，此限制已在 Python 3.14 中被移除。

至少有两个重要理由能说明为何使用多解释器可以带来显著的益处：

-

它们支持（对 Python 来说）全新的、用户友好的并发模型

-

真正的多核心并行

对于某些用例来说，软件中的并发机制能够在更高的层级上提升效率并简化设计。 与此同时，实现和维护除最简单形式以外的并发逻辑对人脑来说常常是很困难的。 这一点尤其适用于普通线程 (例如 [`threading`](https://docs.python.org/zh-cn/3/library/threading.html#module-threading))，其中所有的线程之间会共享所有的内存。

通过多个相互隔离的解释器，你可以利用一类在其他编程语言如 Smalltalk, Erlang, Haskell, 和 Go 中已得到成功运用的并发模型，如通信顺序进程 (CSP) 或表演者模型等。 可以将多个解释器视为具有可远择共享资源的线程。

关于多核并行：从 Python 3.12 开始，各个解释器彼此已实现足够的隔离从而可以并行使用 (参见 [**PEP 684**](https://peps.python.org/pep-0684/))。 这使得 Python 能够解锁许多曾经受限于 [GIL](https://docs.python.org/zh-cn/3/glossary.html#term-GIL) 的 CPU 密集型应用场景。

使用多个解释器在许多方面与 [`multiprocessing`](https://docs.python.org/zh-cn/3/library/multiprocessing.html#module-multiprocessing) 类似，因为它们都提供了相互隔离的逻辑“进程”，在默认情况下不共享资源并可并行运行。 然而，在使用多个解释器时，应用程序将使用更少的系统资源并具有更高的运行效率（因为它们仍处于同一个进程内）。 可以将多个解释器视为即具有进程级别的隔离性又具有线程级别的高效率。

尽管此特性已存在了数十年，但由于知名度较低且缺少标准库模块支持，多解释器并未被广泛使用。 因此，目前其仍存在一些明显的限制，但现在此特性正走向主流并预期会获得迅速的改进。

当前限制：

-

启动每个解释器尚未经过优化。

-

每个解释器会占用超出实际需要的内存（正在持续努力实现解释器之间充分的内部共享）

-

解释器之间真正实现对象或其他数据共享的选项还很有限 (除了 [`memoryview`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#memoryview))。

-

PyPI 上的许多第三方扩展模块尚未与多解释器实现兼容（所有标准库扩展模块 *已经* 兼容）

-

目前，针对使用多个隔离解释器编写应用程序的方法，对大多数 Python 用户来说仍较为陌生。

这些限制的影响将取决于未来 CPython 的改进、解释器的使用方式，以及社区通过 PyPI 软件包能解决哪些问题。 根据具体应用场景，这些限制可能并不会有太大影响，因此不妨尝试一下！

此外，未来的 CPython 发布版将进一步减少甚至消除这种开销并提供一些不太适合放到 PyPI 上的工具，大多数限制也可以通过扩展模块来解决，这意味着 PyPI 包可以为 3.14 填补各种功能缺口，甚至能上溯到 3.12 即解释器最终实现真正的隔离并停止共享 [GIL](https://docs.python.org/zh-cn/3/glossary.html#term-GIL) 的时候。 同样地，预计在 PyPI 上将产生基于多解释器的高层级抽象库。

关于扩展模块，已在推进一些 PyPI 项目的更新，还有如 Cython, pybind11, nanobind 和 PyO3 这样的工具。 有关隔离扩展模块的具体步骤可参看 [隔离扩展模块](https://docs.python.org/zh-cn/3/howto/isolating-extensions.html#isolating-extensions-howto)。 隔离模块与支持 自由线程 所需的工作有大量重叠，因此社区在该领域的持续努力将有助于加快对多解释器的支持进程。

在 3.14 中还增加了：concurrent.futures.InterpreterPoolExecutor。

（由 Eric Snow 在 [gh-134939](https://github.com/python/cpython/issues/134939) 中贡献。）

参见

[**PEP 734**](https://peps.python.org/pep-0734/)

### [**PEP 750**](https://peps.python.org/pep-0750/): 模板字符串字面值

模板字符串是一种用于定制字符串处理的新机制。 它们共享与 f-字符串类似的语法，但与 f-字符串不同，它们返回一个代表字符串的静态和插值部分的对象，而不是简单的 [`str`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#str)。

要编写 t-字符串，应使用 `'t'` 前缀而不是 `'f'`:

```
>>> variety = 'Stilton'
>>> template = t'Try some {variety} cheese!'
>>> type(template)
<class 'string.templatelib.Template'>
```

[`Template`](https://docs.python.org/zh-cn/3/library/string.templatelib.html#string.templatelib.Template) 对象在字符串的静态和插值（以花括号标示）在被组合 *之前* 提供对它们的访问。 迭代 `Template` 实例可以按顺序访问其的各个部分：

```
>>> list(template)
['Try some ', Interpolation('Stilton', 'variety', None, ''), ' cheese!']
```

编写（或调用）代码对 `Template` 实例进行处理是很容易的。 例如，下面的函数可将静态部分转为小写而将 [`Interpolation`](https://docs.python.org/zh-cn/3/library/string.templatelib.html#string.templatelib.Interpolation) 实例转为大写：

```
from string.templatelib import Interpolation

def lower_upper(template):
    """Render static parts lowercase and interpolations uppercase."""
    parts = []
    for part in template:
        if isinstance(part, Interpolation):
            parts.append(str(part.value).upper())
        else:
            parts.append(part.lower())
    return ''.join(parts)

name = 'Wenslydale'
template = t'Mister {name}'
assert lower_upper(template) == 'mister WENSLYDALE'
```

因为 `Template` 实例会在运行时区分静态和插值部分，它们在无害化用户输入时将很有用处。 这里给读者留一个编写对用户输入的 HTML 进行转义的 `html()` 函数的作业！ 模板处理代码可以提供更高的灵活性。 举例来说，进阶版 `html()` 函数可以直接在模板中接受一个 HTML 属性的 `dict`:

```
attributes = {'src': 'limburger.jpg', 'alt': 'lovely cheese'}
template = t'<img {attributes}>'
assert html(template) == '<img src="limburger.jpg" alt="lovely cheese" />'
```

当然，模板处理代码不一定要返回字符串结果。 一个 *更为* 进阶的 `html()` 可以返回一个代表类似 DOM 结构的自定义类型。

有了 t-字符串，开发者可以编写专用系统来无害化 SQL，执行安全的 shell 操作，改进日志记录，处理 Web 开发中的现代概念（HTML, CSS 等等），以及实现轻量级的自定义业务 DSL。

（由 Jim Baker、Guido van Rossum、Paul Everitt、Koudai Aono、Lysandros Nikolaou、Dave Peck、Adam Turner、Jelle Zijlstra、Bénédikt Tran 和 Pablo Galindo Salgado 在 [gh-132661](https://github.com/python/cpython/issues/132661) 中贡献。）

参见

[**PEP 750**](https://peps.python.org/pep-0750/)。

### [**PEP 768**](https://peps.python.org/pep-0768/): 安全的外部调试器接口

Python 3.14 引入了一个零开销的调试接口，它允许调试器和性能分析工具安全地附加到正在运行的 Python 进程而不会停止或重启它们。 这显著加强了 Python 的调试能力，意味着不安全的替代方案已不再需要。

新的接口为附加调试器代码提供了安全的执行点而无需修改解释器的正常执行路径或增加任何运行时开销。 因此，相关工具现在可以实时地对 Python 应用程序进行检查和交互，这对于高可用性系统和生产环境来说是非常关键的能力。

出于便捷性考虑，本接口是在 [`sys.remote_exec()`](https://docs.python.org/zh-cn/3/library/sys.html#sys.remote_exec) 函数中实现的。 例如：

```
import sys
from tempfile import NamedTemporaryFile

with NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    script_path = f.name
    f.write(f'import my_debugger; my_debugger.connect({os.getpid()})')

# 在进程 PID 1234 中执行
print('Behold! An offering:')
sys.remote_exec(1234, script_path)
```

此函数允许发送 Python 代码以便在目标进程中的下一个安全执行点上执行。 不过，工具作者也可以直接实现在 PEP 中描述的协议，它详细讲解了用于安全附加到运行进程的底层机制。

该调试接口在设计时已充分考虑安全性，并包含多种访问控制机制：

-

[`PYTHON_DISABLE_REMOTE_DEBUG`](https://docs.python.org/zh-cn/3/using/cmdline.html#envvar-PYTHON_DISABLE_REMOTE_DEBUG) 环境变量。

-

[`-X disable-remote-debug`](https://docs.python.org/zh-cn/3/using/cmdline.html#cmdoption-X) 命令行选项。

-

[`--without-remote-debug`](https://docs.python.org/zh-cn/3/using/configure.html#cmdoption-without-remote-debug) 配置标志，用于在构建时完全禁用此功能。

（由 Pablo Galindo Salgado，Matt Wozniski 和 Ivona Stojanovic 在 [gh-131591](https://github.com/python/cpython/issues/131591) 中贡献）

参见

[**PEP 768**](https://peps.python.org/pep-0768/)。

### 一种新型的解释器

CPython 新增了一种解释器类型。 它在实现各个 Python 操作码的小型 C 函数之间使用尾调用，而不是使用一个庞大的 C `case` 语句。 对于某些较新的编译器，这种解释器提供了显著的性能提升。 初步测试数据显示在标准的 `pyperformance` 基准测试套件上提速幅度的几何平均值为 3-5%，取决于具体平台和架构。 作为对比的基线是使用 Clang 19 编译，未使用此新解释器的 Python 3.14。

此解释器目前仅适用于 x86-64 和 AArch64 架构上的 Clang 19 及更高版本。 不过，预计 GCC 的未来版本也将支持此特性。

此特性目前为可选功能。 强烈建议在使用新解释器时启用配置文件引导优化因为这是经过测试和验证可提升性能的唯一配置。 要获取更多信息，请参阅 [`--with-tail-call-interp`](https://docs.python.org/zh-cn/3/using/configure.html#cmdoption-with-tail-call-interp)。

备注

这不应与Python函数的 [尾调用优化](https://en.wikipedia.org/wiki/Tail_call) 相混淆，该特性目前在CPython中尚未实现。

这一新型解释器属于CPython解释器的内部实现细节，完全不会改变Python程序的可见行为。它能提升程序性能，但不会引发任何其他变更。

（由 Ken Jin 在 [gh-128563](https://github.com/python/cpython/issues/128563) 中贡献，CPython实现方案融合了Mark Shannon、Garrett Gu、Haoran Xu和Josh Haberman的设计理念。）

### 自由线程模式的改进

CPython 的自由线程模式 ([**PEP 703**](https://peps.python.org/pep-0703/))，最初在 3.13 中加入，已在 Python 3.14 中得到显著改进。 PEP 703 所描述的实现已经全部完成，包括 C API 变量，并且解释器中的临时处理措施已被替换为更具持久性的方案。 专门化自适应解释器 ([**PEP 659**](https://peps.python.org/pep-0659/)) 现已在自由线程模块中启用，并与其他许多优化措施一起大幅度提升了性能。 在自由线程模式中对单线程代码的性能影响目前约为 5-10%，具体取决于平台和所使用的 C 编译器。

自 Python 3.14 开始，在 Windows 上为 CPython 的自由线程构建版编译扩展模块时，预处理器变量 `Py_GIL_DISABLED` 现在需要由构建后端来指定，因为它将不再由 C 编译器自由确定。 对于运行中的解释器，可使用 [`sysconfig.get_config_var()`](https://docs.python.org/zh-cn/3/library/sysconfig.html#sysconfig.get_config_var) 来查询在编译时使用的设置。

新增的 [`-X context_aware_warnings`](https://docs.python.org/zh-cn/3/using/cmdline.html#cmdoption-X) 旗标控制是否要启用 并发安全警告控制。 默认该旗标对自由线程构建版为真值而对启用 GIL 的构建版为假值。

新增了 [`thread_inherit_context`](https://docs.python.org/zh-cn/3/library/sys.html#sys.flags.thread_inherit_context) 旗标，如果启用则表示使用 [`threading.Thread`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Thread) 创建的线程将带有 [`start()`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Thread.start) 调用方的 [`Context()`](https://docs.python.org/zh-cn/3/library/contextvars.html#contextvars.
Context) 副本。最重要的是，这使得由 [`catch_warnings`](https://docs.python.org/zh-cn/3/library/warnings.html#warnings.catch_warnings) 建立的警告过滤上下文能被在该上下文中启动的线程（或 asyncio 任务）所“继承”。它还会影响使用上下文变量的其他模块，如 [`decimal`](https://docs.python.org/zh-cn/3/library/decimal.html#module-decimal) 上下文管理器。默认该旗标对自由线程构建版为真值而对启用 GIL 的构建版为假值。

（贡献来自 Sam Gross, Matt Page, Neil Schemenauer, Thomas Wouters, Donghee Na, Kirill Podoprigora, Ken Jin, Itamar Oren, Brett Simmers, Dino Viehland, Nathan Goldbaum, Ralf Gommers, Lysandros Nikolaou, Kumar Aditya, Edgar Margffoy 以及其他很多人。 这些贡献者有几位是 Meta 的雇员，该公司持续提供了大量工程资源来支持此项目。）

### 改进的错误消息

-

解释器现在能在检测到Python关键字拼写错误时提供有用的建议。当遇到与Python关键字高度相似的单词时，解释器将在错误信息中建议正确的关键字。该功能可帮助程序员快速识别和修复常见的输入错误。例如：

```
>>> whille True:
...     pass
Traceback (most recent call last):
  File "<stdin>", line 1
    whille True:
    ^^^^^^
SyntaxError: invalid syntax. Did you mean 'while'?
```

虽然该功能主要针对最常见的拼写错误情况，但某些变体的拼写错误仍可能导致常规语法错误。（由 Pablo Galindo 在 [gh-132449](https://github.com/python/cpython/issues/132449) 中贡献。）

-

跟在 [`else`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#else) 块后的 [`elif`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#elif) 语句现在会触发特定的错误提示。（由 Steele Farnsworth 在 [gh-129902](https://github.com/python/cpython/issues/129902) 中贡献。）

```
>>> if who == "me":
...     print("It's me!")
... else:
...     print("It's not me!")
... elif who is None:
...     print("Who is it?")
File "<stdin>", line 5
  elif who is None:
  ^^^^
SyntaxError: 'elif' block follows an 'else' block
```

-

如果一条语句被传到 [`else`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#else) 之后的 [条件表达式](https://docs.python.org/zh-cn/3/reference/expressions.html#if-expr)，或者 [`pass`](https://docs.python.org/zh-cn/3/reference/simple_stmts.html#pass), [`break`](https://docs.python.org/zh-cn/3/reference/simple_stmts.html#break) 或 [`continue`](https://docs.python.org/zh-cn/3/reference/simple_stmts.html#continue) 之一被传到 [`if`](https://docs.
python.org/zh-cn/3/reference/compound_stmts.html#if) 之前，那么错误消息会高亮需要 [`expression`](https://docs.python.org/zh-cn/3/reference/expressions.html#grammar-token-python-grammar-expression) 的位置。（由 Sergey Miryanov 在 [gh-129515](https://github.com/python/cpython/issues/129515) 中贡献。）（.)

```
>>> x = 1 if True else pass
Traceback (most recent call last):
  File "<string>", line 1
    x = 1 if True else pass
                       ^^^^
SyntaxError: expected expression after 'else', but statement is given

>>> x = continue if True else break
Traceback (most recent call last):
  File "<string>", line 1
    x = continue if True else break
        ^^^^^^^^
SyntaxError: expected expression before 'if', but statement is given
```

-

当检测到未正确闭合的字符串时，错误消息会提示该字符串可能是字符串的一部分。（由 Pablo Galindo 在 [gh-88535](https://github.com/python/cpython/issues/88535) 中贡献。）

```
>>> "The interesting object "The important object" is very important"
Traceback (most recent call last):
SyntaxError: invalid syntax. Is this intended to be part of the string?
```

-

当字符串前缀不兼容时，错误提示现在会明确显示哪些前缀存在冲突。（由 Nikita Sobolev 在 [gh-133197](https://github.com/python/cpython/issues/133197) 中贡献。）

```
>>> ub'abc'
  File "<python-input-0>", line 1
    ub'abc'
    ^^
SyntaxError: 'u' and 'b' prefixes are incompatible
```

-

在以下场景中使用不兼容目标的 as 语句时，错误提示已得到改进：

-

导入：`import ... as ...`

-

From 导入：`from ... import ... as ...`

-

Except 处理器：`except ... as ...`

-

模式匹配 case 语句：`case ... as ...`

（由 Nikita Sobolev 在 [gh-123539](https://github.com/python/cpython/issues/123539)、[gh-123562](https://github.com/python/cpython/issues/123562) 和 [gh-123440](https://github.com/python/cpython/issues/123440) 中贡献。）

-

尝试向 [`dict`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#dict) 或 [`set`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#set) 添加不可哈希类型的实例时，错误提示信息已改进。（由 CF Bolz-Tereick 和 Victor Stinner 在 [gh-132828](https://github.com/python/cpython/issues/132828) 中贡献。）

```
>>> s = set()
>>> s.add({'pages': 12, 'grade': 'A'})
Traceback (most recent call last):
  File "<python-input-1>", line 1, in <module>
    s.add({'pages': 12, 'grade': 'A'})
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: cannot use 'dict' as a set element (unhashable type: 'dict')
>>> d = {}
>>> l = [1, 2, 3]
>>> d[l] = 12
Traceback (most recent call last):
  File "<python-input-4>", line 1, in <module>
    d[l] = 12
    ~^^^
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')
```

-

当使用 [`async with`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#async-with) 而非 [`with`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#with) 进入支持同步上下文管理器协议的对象时，错误提示信息已改进。反之，对于异步上下文管理器协议的情况也做了相应优化。（由 Bénédikt Tran 在 [gh-128398](https://github.com/python/cpython/issues/128398) 中贡献。）

### [**PEP 784**](https://peps.python.org/pep-0784/): 标准库中的 Zstandard 支持support in the standard library

The new [`compression`](https://docs.python.org/zh-cn/3/library/compression.html#module-compression) package contains modules `compression.lzma`, `compression.bz2`, `compression.gzip` and `compression.zlib` which re-export the [`lzma`](https://docs.python.org/zh-cn/3/library/lzma.html#module-lzma), [`bz2`](https://docs.python.org/zh-cn/3/library/bz2.html#module-bz2), [`gzip`](https://docs.python.org/zh-cn/3/library/gzip.
html#module-gzip) and [`zlib`](https://docs.python.org/zh-cn/3/library/zlib.html#module-zlib) modules respectively.The new import names under `compression` are the preferred names for importing these compression modules from Python 3.14.However, the existing modules names have not been deprecated.Any deprecation or removal of the existing compression modules will occur no sooner than five years after the release of 3.
14.

The new [`compression.zstd`](https://docs.python.org/zh-cn/3/library/compression.zstd.html#module-compression.zstd) module provides compression and decompression APIs for the Zstandard format via bindings to [Meta's zstd library](https://facebook.github.io/zstd/).Zstandard is a widely adopted, highly efficient, and fast compression format.In addition to the APIs introduced in `compression.zstd`, support for reading and writing Zstandard compressed archives has been added to the [`tarfile`](https://docs.
python.org/zh-cn/3/library/tarfile.html#module-tarfile), [`zipfile`](https://docs.python.org/zh-cn/3/library/zipfile.html#module-zipfile), and [`shutil`](https://docs.python.org/zh-cn/3/library/shutil.html#module-shutil) modules.

下面是一个使用新模块压缩数据的示例：

```
from compression import zstd
import math

data = str(math.pi).encode() * 20
compressed = zstd.compress(data)
ratio = len(compressed) / len(data)
print(f"Achieved compression ratio of {ratio}")
```

可以看出，该API与 `lzma` 和 `bz2` 模块的API类似。

（由 Emma Harper Smith、Adam Turner、Gregory P. Smith、Tomas Roun、Victor Stinner 和 Rogdham 在 [gh-132983](https://github.com/python/cpython/issues/132983) 中贡献。）

参见

[**PEP 784**](https://peps.python.org/pep-0784/)。

### asyncio 内省能力

新增了一个使用异步任务来检查正在运行的 Python 进程的命令行界面，可通过 `python -m asyncio ps PID` 或 `python -m asyncio pstree PID` 来使用。

`ps` 子命令会检查给定的进程 ID (PID) 并显示有关当前运行的 asyncio 任务的信息。 它将输出一个任务表格：以扁平列表显示所有任务、任务名称、任务协程栈以及有哪些任务正在等待它们。

`pstree` 子命令获取同样的信息，但改用可视化的 async 调用树形式渲染，以层级格式显示协程关系。 此命令特别适用于调试长时间运行的或卡住的异步程序。 它能帮助开发者快速识别程序阻塞位置、待处理的任务以及协程是如何链接起来的。

例如给定以下代码：

```
import asyncio

async def play_track(track):
    await asyncio.sleep(5)
    print(f'🎵 Finished: {track}')

async def play_album(name, tracks):
    async with asyncio.TaskGroup() as tg:
        for track in tracks:
            tg.create_task(play_track(track), name=track)

async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(
          play_album('Sundowning', ['TNDNBTG', 'Levitate']),
          name='Sundowning')
        tg.create_task(
          play_album('TMBTE', ['DYWTYLM', 'Aqua Regia']),
          name='TMBTE')

if __name__ == '__main__':
    asyncio.run(main())
```

在运行中的进程上执行该新工具将生成如下表格：

```
python -m asyncio ps 12345

tid        task id              task name            coroutine stack                                    awaiter chain                                      awaiter name    awaiter id
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
1935500    0x7fc930c18050       Task-1               TaskGroup._aexit -> TaskGroup.__aexit__ -> main                                                                       0x0
1935500    0x7fc930c18230       Sundowning           TaskGroup._aexit -> TaskGroup.__aexit__ -> album   TaskGroup._aexit -> TaskGroup.__aexit__ -> main    Task-1          0x7fc930c18050
1935500    0x7fc93173fa50       TMBTE                TaskGroup._aexit -> TaskGroup.__aexit__ -> album   TaskGroup._aexit -> TaskGroup.__aexit__ -> main    Task-1          0x7fc930c18050
1935500    0x7fc93173fdf0       TNDNBTG              sleep -> play                                      TaskGroup._aexit -> TaskGroup.__aexit__ -> album   Sundowning      0x7fc930c18230
1935500    0x7fc930d32510       Levitate             sleep -> play                                      TaskGroup._aexit -> TaskGroup.__aexit__ -> album   Sundowning      0x7fc930c18230
1935500    0x7fc930d32890       DYWTYLM              sleep -> play                                      TaskGroup._aexit -> TaskGroup.__aexit__ -> album   TMBTE           0x7fc93173fa50
1935500    0x7fc93161ec30       Aqua Regia           sleep -> play                                      TaskGroup._aexit -> TaskGroup.__aexit__ -> album   TMBTE           0x7fc93173fa50
```

或生成如下树状结构：

```
python -m asyncio pstree 12345

└── (T) Task-1
    └──  main example.py:13
        └──  TaskGroup.__aexit__ Lib/asyncio/taskgroups.py:72
            └──  TaskGroup._aexit Lib/asyncio/taskgroups.py:121
                ├── (T) Sundowning
                │   └──  album example.py:8
                │       └──  TaskGroup.__aexit__ Lib/asyncio/taskgroups.py:72
                │           └──  TaskGroup._aexit Lib/asyncio/taskgroups.py:121
                │               ├── (T) TNDNBTG
                │               │   └──  play example.py:4
                │               │       └──  sleep Lib/asyncio/tasks.py:702
                │               └── (T) Levitate
                │                   └──  play example.py:4
                │                       └──  sleep Lib/asyncio/tasks.py:702
                └── (T) TMBTE
                    └──  album example.py:8
                        └──  TaskGroup.__aexit__ Lib/asyncio/taskgroups.py:72
                            └──  TaskGroup._aexit Lib/asyncio/taskgroups.py:121
                                ├── (T) DYWTYLM
                                │   └──  play example.py:4
                                │       └──  sleep Lib/asyncio/tasks.py:702
                                └── (T) Aqua Regia
                                    └──  play example.py:4
                                        └──  sleep Lib/asyncio/tasks.py:702
```

当检测到异步等待图中存在循环引用（可能表明存在编程问题）时，该工具将报错并列出阻碍树形结构构建的循环路径：

```
python -m asyncio pstree 12345

ERROR: await-graph contains cycles - cannot print a tree!

cycle: Task-2 → Task-3 → Task-2
```

（由 Pablo Galindo、 Łukasz Langa、 Yury Selivanov 和 Marta Gomez Macias 在 [gh-91048](https://github.com/python/cpython/issues/91048) 中贡献。）

### 并发安全的警告控制

现在 [`warnings.catch_warnings`](https://docs.python.org/zh-cn/3/library/warnings.html#warnings.catch_warnings) 上下文管理器将可选择使用一个上下文变量作为警告过滤器。 此特性是通过设置 [`context_aware_warnings`](https://docs.python.org/zh-cn/3/library/sys.html#sys.flags.context_aware_warnings) 旗标来启用的，使用 `-X` 命令行选项或环境变量均可。 当使用 `catch_warnings` 配合多线程或异步任务时将能给出可预测的警告控制。 该旗标默认在自由线程构建版中为真值而在启用 GIL 的构建版中为假值。

（由 Neil Schemenauer 和 Kumar Aditya 在 [gh-130010](https://github.com/python/cpython/issues/130010) 中贡献。）

## 其他语言特性修改

-

现在Windows平台已支持所有Windows代码页作为 ‘cpXXX’ 编解码器使用。（由 Serhiy Storchaka 在 [gh-123803](https://github.com/python/cpython/issues/123803) 中贡献。）

-

实现了符合C99以来C标准规范的实数与复数混合运算规则。（由 Sergey B Kirpichev 在 [gh-69639](https://github.com/python/cpython/issues/69639) 中贡献。）

-

现在将有更多语法错误被检测出来而不受优化和 [`-O`](https://docs.python.org/zh-cn/3/using/cmdline.html#cmdoption-O) 命令行选项的影响。 这包括向 `__debug__` 写入，[`await`](https://docs.python.org/zh-cn/3/reference/expressions.html#await) 的不正确使用，以及在异步函数之外的异步推导式。 例如，`python -O -c 'assert (__debug__ := 1)'` 或 `python -O -c 'assert await 1'` 现在将产生 [`SyntaxError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#SyntaxError)。 （由 Irit Katriel 和 Jelle Zijlstra 在 [gh-122245](https://github.com/python/cpython/issues/122245) 和 [gh-121637](https://github.com/python/cpython/issues/121637) 中贡献。）.)

-

当纯C类型派生子类时，若子类未显式重写相关方法，新建类型的C槽位将不再被替换为封装版本。（由 Tomasz Pytel 在 [gh-132284](https://github.com/python/cpython/issues/132284) 中贡献。）

### 内置

-

[`bytes.fromhex()`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#bytes.fromhex) 和 [`bytearray.fromhex()`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#bytearray.fromhex) 方法现在支持 ASCII 格式的 [`bytes`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#bytes) 及 [字节型对象](https://docs.python.org/zh-cn/3/glossary.html#term-bytes-like-object) 作为输入参数。（由 Daniel Pope 在 [gh-129349](https://github.com/python/cpython/issues/129349) 中贡献。）

-

新增类方法 [`float.from_number()`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#float.from_number) 和 [`complex.from_number()`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#complex.from_number)，用于将数值分别转换为 [`float`](https://docs.python.org/zh-cn/3/builtins/functions.html#float) 或 [`complex`](https://docs.python.org/zh-cn/3/builtins/functions.html#complex) 类型。若参数不是一个实数则会引发 [`TypeError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#TypeError)。（由 Serhiy Storchaka 在 [gh-84978](https://github.com/python/cpython/issues/84978) 中贡献。）

-

在新式字符串格式化（通过 [`format()`](https://docs.python.org/zh-cn/3/builtins/functions.html#format) 或 [f-字符串](https://docs.python.org/zh-cn/3/reference/lexical_analysis.html#f-strings) 实现）的浮点数表示类型中，现支持使用下划线和逗号作为小数部分的千位分隔符。（由 Sergey B Kirpichev 在 [gh-87790](https://github.com/python/cpython/issues/87790) 中贡献。）

-

[`int()`](https://docs.python.org/zh-cn/3/builtins/functions.html#int) 函数不再委托给 [`__trunc__()`](https://docs.python.org/zh-cn/3/reference/datamodel.html#object.__trunc__)。 希望支持转换为 `int()` 的类必须实现 [`__int__()`](https://docs.python.org/zh-cn/3/reference/datamodel.html#object.__int__) 或 [`__index__()`](https://docs.python.org/zh-cn/3/reference/datamodel.html#object.__index__)。 （由 Mark Dickinson 在 [gh-119743](https://github.com/python/cpython/issues/119743) 中贡献。）

-

[`map()`](https://docs.python.org/zh-cn/3/builtins/functions.html#map) 函数现在新增了一个可选的仅限关键字参数 *strict* （与 [`zip()`](https://docs.python.org/zh-cn/3/builtins/functions.html#zip) 类似），用于校验所有可迭代对象长度是否一致。（由 Wannes Boeykens 在 [gh-119793](https://github.com/python/cpython/issues/119793) 中贡献。）

-

[`memoryview`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#memoryview) 类型现已支持下标，使其成为 [generic type](https://docs.python.org/zh-cn/3/glossary.html#term-generic-type)。 （由 Brian Schubert 在 [gh-126012](https://github.com/python/cpython/issues/126012) 中贡献。）

-

在布尔上下文中使用 [`NotImplemented`](https://docs.python.org/zh-cn/3/builtins/constants.html#NotImplemented) 现在会引发 [`TypeError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#TypeError) 异常。该用法自 Python 3.9 起已引发 [`DeprecationWarning`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#DeprecationWarning) 弃用警告。（由 Jelle Zijlstra 在 [gh-118767](https://github.com/python/cpython/issues/118767) 中贡献。）

-

三参数 [`pow()`](https://docs.python.org/zh-cn/3/builtins/functions.html#pow) 现在会在必要时尝试调用 [`__rpow__()`](https://docs.python.org/zh-cn/3/reference/datamodel.html#object.__rpow__) 方法。此前该方法仅在双参数 `pow()` 和二元幂运算符中被调用。（由 Serhiy Storchaka 在 [gh-130104](https://github.com/python/cpython/issues/130104) 中贡献。）

-

[`super`](https://docs.python.org/zh-cn/3/builtins/functions.html#super) 对象现在支持 [`复制`](https://docs.python.org/zh-cn/3/library/copy.html#module-copy) 和 [`序列化`](https://docs.python.org/zh-cn/3/library/pickle.html#module-pickle) 操作。（由 Serhiy Storchaka 在 [gh-125767](https://github.com/python/cpython/issues/125767) 中贡献。）

### 命令行与环境

-

导入时间分析标志现可通过新增的 [`-X importtime=2`](https://docs.python.org/zh-cn/3/using/cmdline.html#cmdoption-X) 选项追踪已加载（'缓存'）模块。当导入此类模块时，`self` 和 `cumulative` 时间值将被替换为字符串 `cached`。

对 `-X importtime` 取大于 `2` 的值被保留供未来使用。

（由 Noah Kim 和 Adam Turner 在 [gh-118655](https://github.com/python/cpython/issues/118655) 中贡献。）

-

命令行选项 [`-c`](https://docs.python.org/zh-cn/3/using/cmdline.html#cmdoption-c) 现在会在执行前自动对其代码参数进行去缩进处理，该行为与 [`textwrap.dedent()`](https://docs.python.org/zh-cn/3/library/textwrap.html#textwrap.dedent) 函数保持一致。（由 Jon Crall 和 Steven Sun 在 [gh-103998](https://github.com/python/cpython/issues/103998) 中贡献。）

-

`-J` 不再是 [Jython](https://www.jython.org/) 的保留标志，目前不具任何特殊含义。（由 Adam Turner 在 [gh-133336](https://github.com/python/cpython/issues/133336) 中贡献。）

### PEP 758: 允许不带圆括号的 `except` 和 `except*` 表达式

现在 [`except`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#except) 和 [`except*`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#except-star) 表达式允许存在多个异常类型且未使用 `as` 子句时省略圆括号。 例如：

```
try:
    connect_to_server()
except TimeoutError, ConnectionRefusedError:
    print('The network has ceased to be!')
```

（由 Pablo Galindo 和 Brett Cannon 在 [**PEP 758**](https://peps.python.org/pep-0758/) 和 [gh-131831](https://github.com/python/cpython/issues/131831) 中贡献。）

### PEP 765: [`finally`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#finally) 代码块中的控制流

编译器在检测到 [`return`](https://docs.python.org/zh-cn/3/reference/simple_stmts.html#return)、[`break`](https://docs.python.org/zh-cn/3/reference/simple_stmts.html#break) 或 [`continue`](https://docs.python.org/zh-cn/3/reference/simple_stmts.html#continue) 语句跳出 [`finally`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#finally) 代码块时，现在将触发 [`SyntaxWarning`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#SyntaxWarning)。此项变更遵循 [**PEP 765**](https://peps.python.org/pep-0765/) 规范。

在不方便修改的情况下（例如由于代码语法检查导致警告的冗余），可以使用 [警告过滤器](https://docs.python.org/zh-cn/3/library/warnings.html#warning-filter) 通过添加 `ignore::SyntaxWarning` 作为过滤器来关闭所有语法警告。 这可以配合一个将其他警告转换为错误的过滤器来指明（例如，传递 `-Werror -Wignore::SyntaxWarning` 作为 CLI 选项，或者设置 `PYTHONWARNINGS=error,ignore::SyntaxWarning` 等）。

请注意在运行时使用 [`warnings`](https://docs.python.org/zh-cn/3/library/warnings.html#module-warnings) 模块应用这样的过滤器仅会屏蔽在过滤器调整 *之后* 编译的代码中的警告。 在过滤器调整之前编译的代码（例如，当模块被导入时）仍然会发出语法警告。

（由 Irit Katriel 在 [gh-130080](https://github.com/python/cpython/issues/130080) 中贡献。）

### 垃圾收集

**自 Python 3.14.5 开始:**

垃圾收集器 (GC) 在 Python 3.14.5 中有所变化。

Python 3.14.0-3.14.4 发行版带有新的增量式 GC。 不过，由于大量在生产环境中出现显著内存压力的 [报告](https://github.com/python/cpython/issues/142516)，它已被更改回 3.13 中的世代式 GC。 这是 Python 3.14.5 及之后版本在使用的 GC。

**在之前的 Python 3.14.0-3.14.4 中:**

循环垃圾回收器现在采用增量式处理。这意味着对于较大的堆内存，最大暂停时间将减少一个数量级或更多。

现在垃圾回收机制仅包含两个代际：新生代和老年代。当未直接调用 [`gc.collect()`](https://docs.python.org/zh-cn/3/library/gc.html#gc.collect) 函数时，垃圾回收器的触发频率会稍有降低。而在调用时，它会回收新生代以及部分老年代对象（即增量回收），而非一次性回收一个或多个完整的代际。

`gc.collect()` 函数的行为略有变化：

-

`gc.collect(1)`：执行一次增量式垃圾回收，而非专门回收第1代对象。

-

对 `gc.collect()` 的其他调用保持不变。

（由 Mark Shannon 在 [gh-108362](https://github.com/python/cpython/issues/108362) 中贡献。）

### 默认的交互式 shell

-

默认的 [interactive](https://docs.python.org/zh-cn/3/glossary.html#term-interactive) shell 现已支持 Python 语法高亮。 此特性默认启用，除非设置了 [`PYTHON_BASIC_REPL`](https://docs.python.org/zh-cn/3/using/cmdline.html#envvar-PYTHON_BASIC_REPL) 或任何其他禁用颜色的环境变量。 请参阅 [控制颜色](https://docs.python.org/zh-cn/3/using/cmdline.html#using-on-controlling-color) 了解详情。

语法高亮的默认配色主题追求高对比度并仅使用 4 位 VGA 标准 ANSI 颜色代码以保证全大兼容性。 可以使用实验性的 API `_colorize.set_theme()` 来自定义配色主题。 此函数可以交互式地调用或是在 [`PYTHONSTARTUP`](https://docs.python.org/zh-cn/3/using/cmdline.html#envvar-PYTHONSTARTUP) 脚本中调用。 请注意此函数没有稳定性保证，可能被修改或者移除。

（由 Łukasz Langa 在 [gh-131507](https://github.com/python/cpython/issues/131507) 中贡献。）

-

默认的 [interactive](https://docs.python.org/zh-cn/3/glossary.html#term-interactive) shell 现已支持导入自动补全。 这意味着当键入 `import co` 并按下 <Tab> 时将会提示以 `co` 打头的模块。 类似地，键入 `from concurrent import i` 将会提示以 `i` 打头的 `concurrent` 子模块。 请注意模块属性的自动补全目前尚未受到支持。 （由 Tomas Roun 在 [gh-69605](https://github.com/python/cpython/issues/69605) 中贡献。）.)

## 新增模块

-

[`annotationlib`](https://docs.python.org/zh-cn/3/library/annotationlib.html#module-annotationlib): 用于对 [标注](https://docs.python.org/zh-cn/3/glossary.html#term-annotation) 进行内省。 请参阅 PEP 749 了解详情。 （由 Jelle Zijlstra 在 [gh-119180](https://github.com/python/cpython/issues/119180) 中贡献。）

-

[`compression`](https://docs.python.org/zh-cn/3/library/compression.html#module-compression) (包括 [`compression.zstd`](https://docs.python.org/zh-cn/3/library/compression.zstd.html#module-compression.zstd)): 针对压缩相关模块的包，包括一个支持 Zstandard 压缩格式的新模块。 请参阅 PEP 784 了解详情。 （由 Emma Harper Smith, Adam Turner, Gregory P. Smith, Tomas Roun, Victor Stinner 和 Rogdham 在 [gh-132983](https://github.com/python/cpython/issues/132983) 中贡献。）

-

[`concurrent.interpreters`](https://docs.python.org/zh-cn/3/library/concurrent.interpreters.html#module-concurrent.interpreters): 在标准库中支持多解释器。 请参阅 PEP 734 了解详情。 （由 Eric Snow 在 [gh-134939](https://github.com/python/cpython/issues/134939) 中贡献。）

-

[`string.templatelib`](https://docs.python.org/zh-cn/3/library/string.templatelib.html#module-string.templatelib): 对模板字符串字面值（t-字符串）的支持。 详情参见 PEP 750。 （由 Jim Baker, Guido van Rossum, Paul Everitt, Koudai Aono, Lysandros Nikolaou, Dave Peck, Adam Turner, Jelle Zijlstra, Bénédikt Tran 和 Pablo Galindo Salgado 在 [gh-132661](https://github.com/python/cpython/issues/132661) 中贡献。）

## 改进的模块

### argparse

-

[`argparse.ArgumentParser`](https://docs.python.org/zh-cn/3/library/argparse.html#argparse.ArgumentParser) 的 [程序名称](https://docs.python.org/zh-cn/3/library/argparse.html#prog) 默认值现在会反映 Python 解释器定位 `__main__` 模块代码的方式。（由 Serhiy Storchaka 和 Alyssa Coghlan 在 [gh-66436](https://github.com/python/cpython/issues/66436) 中贡献。）

-

[`argparse.ArgumentParser`](https://docs.python.org/zh-cn/3/library/argparse.html#argparse.ArgumentParser) 新增可选形参 *suggest_on_error*，可在用户输入错误时提供参数选项及子解析器名称的建议。（由 Savannah Ostrowski 在 [gh-124456](https://github.com/python/cpython/issues/124456) 中贡献。）

-

为帮助文本启用颜色显示，你可以通过向 [`argparse.ArgumentParser`](https://docs.python.org/zh-cn/3/library/argparse.html#argparse.ArgumentParser) 传递可选的 *color* 形参来禁用此功能。此外，该功能还可以通过 [环境变量](https://docs.python.org/zh-cn/3/using/cmdline.html#using-on-controlling-color) 进行控制。（由 Hugo van Kemenade 在 [gh-130645](https://github.com/python/cpython/issues/130645) 中贡献。）

### ast（抽象语法树）

-

增加 [`compare()`](https://docs.python.org/zh-cn/3/library/ast.html#ast.compare) 函数用于比较两个 AST。 （由 Batuhan Taskaya 和 Jeremy Hylton 在 [gh-60191](https://github.com/python/cpython/issues/60191) 中贡献。）

-

新增对AST节点 [`copy.replace()`](https://docs.python.org/zh-cn/3/library/copy.html#copy.replace) 操作的支持。（由 Bénédikt Tran 在 [gh-121141](https://github.com/python/cpython/issues/121141) 中贡献。）

-

在优化级别为2时，文档字符串现会从优化后的AST中移除。（由 Irit Katriel 在 [gh-123958](https://github.com/python/cpython/issues/123958) 中贡献。）

-

现在 AST 节点的 [`repr()`](https://docs.python.org/zh-cn/3/builtins/functions.html#repr) 输出会包含更多信息。 （由 Tomas Roun 在 [gh-116022](https://github.com/python/cpython/issues/116022) 中贡献。）

-

在调用时附带 AST 作为输入时，[`parse()`](https://docs.python.org/zh-cn/3/library/ast.html#ast.parse) 函数现在总是会验证根节点类型是否合规。 （由 Irit Katriel 在 [gh-130139](https://github.com/python/cpython/issues/130139) 中贡献。）

-

为命令行界面添加新的选项: [`--feature-version`](https://docs.python.org/zh-cn/3/library/ast.html#cmdoption-ast-feature-version), [`--optimize`](https://docs.python.org/zh-cn/3/library/ast.html#cmdoption-ast-optimize) 和 [`--show-empty`](https://docs.python.org/zh-cn/3/library/ast.html#cmdoption-ast-show-empty)。 （由 Semyon Moroz 在 [gh-133367](https://github.com/python/cpython/issues/133367) 中贡献。）

### asyncio

-

名为 `create_task()` 的函数及方法现在接受任意关键字参数列表，所有关键字参数都将传递给 [`Task`](https://docs.python.org/zh-cn/3/library/asyncio-task.html#asyncio.Task) 构造器或自定义任务工厂 (详见 [`set_task_factory()`](https://docs.python.org/zh-cn/3/library/asyncio-eventloop.html#asyncio.loop.set_task_factory))。 `name` 和 `context` 关键字参数不再具有特殊处理逻辑 —— 名称现在应通过工厂的 `name` 关键字参数设置，而 `context` 可设为 `None`。

这会影响下列函数和方法: [`asyncio.create_task()`](https://docs.python.org/zh-cn/3/library/asyncio-task.html#asyncio.create_task), [`asyncio.loop.create_task()`](https://docs.python.org/zh-cn/3/library/asyncio-eventloop.html#asyncio.loop.create_task), [`asyncio.TaskGroup.create_task()`](https://docs.python.org/zh-cn/3/library/asyncio-task.html#asyncio.TaskGroup.create_task)。

（由 Thomas Grainger 在 [gh-128307](https://github.com/python/cpython/issues/128307) 中贡献。）

-

新增两个工具函数用于内省和打印程序的调用图: [`capture_call_graph()`](https://docs.python.org/zh-cn/3/library/asyncio-graph.html#asyncio.capture_call_graph) 和 [`print_call_graph()`](https://docs.python.org/zh-cn/3/library/asyncio-graph.html#asyncio.print_call_graph)。 请参阅 Asyncio 内省功能 了解详情。 （由 Yury Selivanov, Pablo Galindo Salgado 和 Łukasz Langa 在 [gh-91048](https://github.com/python/cpython/issues/91048) 中贡献。）

### calendar（日历）

-

默认情况下，[`calendar`](https://docs.python.org/zh-cn/3/library/calendar.html#module-calendar) 模块的 [命令行](https://docs.python.org/zh-cn/3/library/calendar.html#calendar-cli) 文本输出会以彩色高亮显示当日日期，该功能可通过 [环境变量](https://docs.python.org/zh-cn/3/using/cmdline.html#using-on-controlling-color) 控制。（由 Hugo van Kemenade 在 [gh-128317](https://github.com/python/cpython/issues/128317) 中贡献。）

### concurrent.futures

-

新增一个执行器类 [`InterpreterPoolExecutor`](https://docs.python.org/zh-cn/3/library/concurrent.futures.html#concurrent.futures.InterpreterPoolExecutor)，它会将同一个进程中的多个 Python 解释器 ('子解释器') 暴露给 Python 代码。 它会使用一个独立的 Python 解释器池来异步地执行调用。

此特性是从 PEP 734 引入的新增模块 [`interpreters`](https://docs.python.org/zh-cn/3/library/concurrent.interpreters.html#module-concurrent.interpreters) 中分离出来的。 （由 Eric Snow 在 [gh-124548](https://github.com/python/cpython/issues/124548) 中贡献。）

-

在 macOS 以外的 Unix 平台上，['forkserver'](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-start-method-forkserver) 现在是用于 [`ProcessPoolExecutor`](https://docs.python.org/zh-cn/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor) 的默认 [启动方法](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-start-methods) (替代 ['fork'](https://docs.
python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-start-method-fork))。此项更改不会影响 Windows 或 macOS，在这两个平台上 ['spawn'](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-start-method-spawn) 仍是默认启动方法。

如需使用与线程不兼容的 *fork* 启动方法，必须通过向 [`ProcessPoolExecutor`](https://docs.python.org/zh-cn/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor) 提供 *mp_context* 多进程上下文参数来显式指定。

请参阅 [forkserver 限制说明](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-programming-forkserver) 了解与 *fork* 方法的差异信息，以及此项变更对存在以下情况的现有代码可能产生的影响：(1) 使用可变全局共享变量 (2) 包含无法被 [`pickle`](https://docs.python.org/zh-cn/3/library/pickle.html#module-pickle) 自动序列化的共享对象。

（由 Gregory P. Smith 在 [gh-84559](https://github.com/python/cpython/issues/84559) 中贡献）

-

为 [`ProcessPoolExecutor`](https://docs.python.org/zh-cn/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor) 增加两个新方法，[`terminate_workers()`](https://docs.python.org/zh-cn/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor.terminate_workers) 和 [`kill_workers()`](https://docs.python.org/zh-cn/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor.kill_workers)，作为终结或杀掉给定进程池中所有存活工作进程的方法。 （由 Charles Machalow 在 [gh-130849](https://github.com/python/cpython/issues/130849) 中贡献。）

-

为 [`Executor.map`](https://docs.python.org/zh-cn/3/library/concurrent.futures.html#concurrent.futures.Executor.map) 增加可选的 *buffersize* 形参用来限制已提交但尚未产生结果的任务数量。 如果缓冲区已满，对 *iterables* 的迭代将暂停直到缓冲区产生一个结果。 （由 Enzo Bonnal 和 Josh Rosenberg 在 [gh-74028](https://github.com/python/cpython/issues/74028) 中贡献。）.)

### configparser

-

`configparser` 将不再写入它无法读取的配置文件，以提升安全性。 尝试使用 [`write()`](https://docs.python.org/zh-cn/3/library/configparser.html#configparser.ConfigParser.write) 写入包含定界符或以节标头模式开头的键将会引发 [`InvalidWriteError`](https://docs.python.org/zh-cn/3/library/configparser.html#configparser.InvalidWriteError)。 （由 Jacob Lincoln 在 [gh-129270](https://github.com/python/cpython/issues/129270) 中贡献。）

### contextvars

-

已为 [`Token`](https://docs.python.org/zh-cn/3/library/contextvars.html#contextvars.Token) 对象提供 [context manager](https://docs.python.org/zh-cn/3/glossary.html#term-context-manager) 协议支持。 （由 Andrew Svetlov 在 [gh-129889](https://github.com/python/cpython/issues/129889) 中贡献。）

### ctypes

-

现在 [`Structure`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.Structure) 和 [`Union`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.Union) 对象中的 [位字段](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes-bit-fields-in-structures-unions) 现在将更紧密地匹配平台默认值 (GCC/Clang 或 MSVC)。 具体而言，字段间不会再出现重叠。 （由 Matthias Görgens 在 [gh-97702](https://github.com/python/cpython/issues/97702) 中贡献。）

-

现在可通过设置 [`Structure._layout_`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.Structure._layout_) 类属性来匹配非默认ABI。（由 Petr Viktorin 在 [gh-97702](https://github.com/python/cpython/issues/97702) 中贡献。）

-

[`Structure`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.Structure)/[`Union`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.Union) 的字段描述符类现以 [`CField`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.CField) 形式提供，并新增了辅助调试和内省的属性。（由 Petr Viktorin 在 [gh-128715](https://github.com/python/cpython/issues/128715) 中贡献。）

-

在Windows平台上，[`COMError`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.COMError) 异常现已公开。（由 Jun Komoda 在 [gh-126686](https://github.com/python/cpython/issues/126686) 中贡献。）

-

在Windows平台上，[`CopyComPointer()`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.CopyComPointer) 函数现已公开。（由 Jun Komoda 在 [gh-127275](https://github.com/python/cpython/issues/127275) 中贡献。）

-

增加 [`memoryview_at()`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.memoryview_at) 函数，用于创建一个引用指定的指针和长度的 [`memoryview`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#memoryview) 对象。 该函数功能类似于 [`ctypes.string_at()`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.string_at) 但它避免了缓冲区复制，通常适用于实现接受动态大小缓冲区的纯 Python 回调函数。 （由 Rian Hunter 在 [gh-112018](https://github.com/python/cpython/issues/112018) 中贡献。）

-

复数类型，[`c_float_complex`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.c_float_complex), [`c_double_complex`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.c_double_complex) 和 [`c_longdouble_complex`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.c_longdouble_complex) 现已在编译器和 `libffi` 库支持复数 complex C 类型时可用。 （由 Sergey B Kirpichev 在 [gh-61103](https://github.com/python/cpython/issues/61103) 中贡献。）

-

新增 [`ctypes.util.dllist()`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.util.dllist) 函数，用于列出当前进程已加载的共享库。（由 Brian Ward 在 [gh-119349](https://github.com/python/cpython/issues/119349) 中贡献。）

-

将 [`ctypes.POINTER()`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.POINTER) 类型缓存从全局内部缓存 (`_pointer_type_cache`) 移至对应 `ctypes` 类型的 [`_CData.__pointer_type__`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes._CData.__pointer_type__) 属性。 这将防止在某些情况下缓存的无限增长。 （由 Sergey Miryanov 在 [gh-100926](https://github.com/python/cpython/issues/100926) 中贡献。）

-

现在 [`py_object`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.py_object) 类型已支持下标，使其成为 [generic type](https://docs.python.org/zh-cn/3/glossary.html#term-generic-type)。 （由 Brian Schubert 在 [gh-132168](https://github.com/python/cpython/issues/132168) 中贡献。）

-

现在 `ctypes` 已支持 [自由线程构建版](https://docs.python.org/zh-cn/3/glossary.html#term-free-threading)。 （由 Kumar Aditya 和 Peter Bierma 在 [gh-127945](https://github.com/python/cpython/issues/127945) 中贡献。）

### curses

-

增加 [`assume_default_colors()`](https://docs.python.org/zh-cn/3/library/curses.html#curses.assume_default_colors) 函数，是将 [`use_default_colors()`](https://docs.python.org/zh-cn/3/library/curses.html#curses.use_default_colors) 函数改进为允许修改颜色对 `0`。 （由 Serhiy Storchaka 在 [gh-133139](https://github.com/python/cpython/issues/133139) 中贡献。）

### datetime

-

为 [`datetime.date`](https://docs.python.org/zh-cn/3/library/datetime.html#datetime.date) 和 and [`datetime.time`](https://docs.python.org/zh-cn/3/library/datetime.html#datetime.time) 类增加 [`strptime()`](https://docs.python.org/zh-cn/3/library/datetime.html#datetime.date.strptime) 方法。 （由 Wannes Boeykens 在 [gh-41431](https://github.com/python/cpython/issues/41431) 中贡献。）

### decimal

-

增加 [`Decimal.from_number()`](https://docs.python.org/zh-cn/3/library/decimal.html#decimal.Decimal.from_number) 作为 [`Decimal`](https://docs.python.org/zh-cn/3/library/decimal.html#decimal.Decimal) 的替代性构造器。 （由 Serhiy Storchaka 在 [gh-121798](https://github.com/python/cpython/issues/121798) 中贡献。）

-

对外公开 [`IEEEContext()`](https://docs.python.org/zh-cn/3/library/decimal.html#decimal.IEEEContext) 以支持创建对应与 IEEE 754 (2008) 十进制交换格式的上下文。 （由 Sergey B Kirpichev 在 [gh-53032](https://github.com/python/cpython/issues/53032) 中贡献。）

### difflib

-

由 [`HtmlDiff`](https://docs.python.org/zh-cn/3/library/difflib.html#difflib.HtmlDiff) 类生成的高亮显示更改的比较页面现在支持 '黑暗模式'。 （由李佳昊在 [gh-129939](https://github.com/python/cpython/issues/129939) 中贡献。）

### dis

-

新增对 [`指令`](https://docs.python.org/zh-cn/3/library/dis.html#dis.Instruction) 完整源码位置信息（而非仅行号）的渲染支持，该特性通过 *show_positions* 关键字参数添加到以下接口：

-

[`dis.Bytecode`](https://docs.python.org/zh-cn/3/library/dis.html#dis.Bytecode)

-

[`dis.dis()`](https://docs.python.org/zh-cn/3/library/dis.html#dis.dis)

-

[`dis.distb()`](https://docs.python.org/zh-cn/3/library/dis.html#dis.distb)

-

[`dis.disassemble()`](https://docs.python.org/zh-cn/3/library/dis.html#dis.disassemble)

该特性同时通过 [`dis --show-positions`](https://docs.python.org/zh-cn/3/library/dis.html#cmdoption-dis-P) 命令行选项提供。（由 Bénédikt Tran 在 [gh-123165](https://github.com/python/cpython/issues/123165) 中贡献。）

-

新增 [`dis --specialized`](https://docs.python.org/zh-cn/3/library/dis.html#cmdoption-dis-S) 命令行选项，用于显示特化字节码。（由 Bénédikt Tran 在 [gh-127413](https://github.com/python/cpython/issues/127413) 中贡献。）

### errno

-

增加了 [`EHWPOISON`](https://docs.python.org/zh-cn/3/library/errno.html#errno.EHWPOISON) 错误码常量。 （由 James Roy 在 [gh-126585](https://github.com/python/cpython/issues/126585) 中贡献。）

### faulthandler

-

通过新的 [`dump_c_stack()`](https://docs.python.org/zh-cn/3/library/faulthandler.html#faulthandler.dump_c_stack) 函数或通过 [`faulthandler.enable()`](https://docs.python.org/zh-cn/3/library/faulthandler.html#faulthandler.enable) 中的 *c_stack* 参数添加在 [支持 C 栈回溯](https://docs.python.org/zh-cn/3/library/faulthandler.html#c-stack-compatibility) 的系统上增加打印相应信息的支持。 （由 Peter Bierma 在 [gh-127604](https://github.com/python/cpython/issues/127604) 中贡献。）

### fnmatch

-

增加了 [`filterfalse()`](https://docs.python.org/zh-cn/3/library/fnmatch.html#fnmatch.filterfalse) 函数用于拒绝匹配给定模式的名称。 （由 Bénédikt Tran 在 [gh-74598](https://github.com/python/cpython/issues/74598) 中贡献。）

### fractions

-

现在可以基于任何具有 `as_integer_ratio()` 方法的对象构造 [`Fraction`](https://docs.python.org/zh-cn/3/library/fractions.html#fractions.Fraction) 对象。 （由 Serhiy Storchaka 在 [gh-82017](https://github.com/python/cpython/issues/82017) 中贡献。）.)

-

增加 [`Fraction.from_number()`](https://docs.python.org/zh-cn/3/library/fractions.html#fractions.Fraction.from_number) 作为 [`Fraction`](https://docs.python.org/zh-cn/3/library/fractions.html#fractions.Fraction) 的替代性构造器。 （由 Storchaka 在 [gh-121797](https://github.com/python/cpython/issues/121797) 中贡献。）

### functools

-

增加 [`Placeholder`](https://docs.python.org/zh-cn/3/library/functools.html#functools.Placeholder) 哨兵对象。 这可与 [`partial()`](https://docs.python.org/zh-cn/3/library/functools.html#functools.partial) 或 [`partialmethod()`](https://docs.python.org/zh-cn/3/library/functools.html#functools.partialmethod) 函数一起使用以便在返回的 [partial 对象](https://docs.python.org/zh-cn/3/library/functools.html#partial-objects) 保留位置参数的位置。 （由 Dominykas Grigonis 在 [gh-119127](https://github.com/python/cpython/issues/119127) 中贡献。）

-

允许将 [`reduce()`](https://docs.python.org/zh-cn/3/library/functools.html#functools.reduce) 的 *initial* 形参作为关键字参数传递。 （由 Sayandip Dutta 在 [gh-125916](https://github.com/python/cpython/issues/125916) 中贡献。）

### getopt

-

新增对可选参数选项的支持。（由 Serhiy Storchaka 在 [gh-126374](https://github.com/python/cpython/issues/126374) 中贡献。）

-

新增对按顺序返回混合选项和非选项参数的支持。（由 Serhiy Storchaka 在 [gh-126390](https://github.com/python/cpython/issues/126390) 中贡献。）

### getpass

-

在 [`getpass()`](https://docs.python.org/zh-cn/3/library/getpass.html#getpass.getpass) 函数中通过可选的仅限关键字参数 *echo_char* 支持键盘反馈。 每当输入字符时会显示占位符，并在删除字符时将其移除。 （由 Semyon Moroz 在 [gh-77065](https://github.com/python/cpython/issues/77065) 中贡献。）.)

### graphlib

-

允许在排序尚未开始的情况下多次调用 [`TopologicalSorter.prepare()`](https://docs.python.org/zh-cn/3/library/graphlib.html#graphlib.TopologicalSorter.prepare)。 （由 Daniel Pope 在 [gh-130914](https://github.com/python/cpython/issues/130914) 中贡献。）

### heapq

-

通过下列新增函数，`heapq` 模块改进了对最大堆的支持：

-

[`heapify_max()`](https://docs.python.org/zh-cn/3/library/heapq.html#heapq.heapify_max)

-

[`heappush_max()`](https://docs.python.org/zh-cn/3/library/heapq.html#heapq.heappush_max)

-

[`heappop_max()`](https://docs.python.org/zh-cn/3/library/heapq.html#heapq.heappop_max)

-

[`heapreplace_max()`](https://docs.python.org/zh-cn/3/library/heapq.html#heapq.heapreplace_max)

-

[`heappushpop_max()`](https://docs.python.org/zh-cn/3/library/heapq.html#heapq.heappushpop_max)

### hmac

-

新增基于 [HACL*](https://github.com/hacl-star/hacl-star/) 项目形式化验证代码的 HMAC ([**RFC 2104**](https://datatracker.ietf.org/doc/html/rfc2104.html)) 内置实现。当 OpenSSL 的 HMAC 实现不可用时，该实现将作为备用方案。（由 Bénédikt Tran 在 [gh-99108](https://github.com/python/cpython/issues/99108) 中贡献。）

### http

-

由 [`http.server`](https://docs.python.org/zh-cn/3/library/http.server.html#module-http.server) 模块生成的目录列表和错误页面允许浏览器应用其默认暗模式。（由 Yorik Hansen 在 [gh-123430](https://github.com/python/cpython/issues/123430) 中贡献。）

-

[`http.server`](https://docs.python.org/zh-cn/3/library/http.server.html#module-http.server) 模块现在支持使用 [`http.server.HTTPSServer`](https://docs.python.org/zh-cn/3/library/http.server.html#http.server.HTTPSServer) 类通过 HTTPS 提供服务。此功能通过命令行界面 (`python -m http.server`) 通过以下选项公开：

-

[`--tls-cert <path>`](https://docs.python.org/zh-cn/3/library/http.server.html#cmdoption-http.server-tls-cert): TLS 证书文件的路径。

-

[`--tls-key <path>`](https://docs.python.org/zh-cn/3/library/http.server.html#cmdoption-http.server-tls-key): 可选的私钥文件路径。

-

[`--tls-password-file <path>`](https://docs.python.org/zh-cn/3/library/http.server.html#cmdoption-http.server-tls-password-file): 可选的私钥密码文件路径。

（由 Semyon Moroz 在 [gh-85162](https://github.com/python/cpython/issues/85162) 中贡献。）

### imaplib

-

增加 [`IMAP4.idle()`](https://docs.python.org/zh-cn/3/library/imaplib.html#imaplib.IMAP4.idle)，实现了在 [**RFC 2177**](https://datatracker.ietf.org/doc/html/rfc2177.html) 中定义的 IMAP4 `IDLE` 命令。 （由 Forest 在 [gh-55454](https://github.com/python/cpython/issues/55454) 中贡献。）

### inspect

-

[`signature()`](https://docs.python.org/zh-cn/3/library/inspect.html#inspect.signature) 接受一个新参数 *annotation_format* 用于控制表示标注所使用的 [`annotationlib.Format`](https://docs.python.org/zh-cn/3/library/annotationlib.html#annotationlib.Format)。 （由 Jelle Zijlstra 在 [gh-101552](https://github.com/python/cpython/issues/101552) 中贡献。）

-

[`Signature.format()`](https://docs.python.org/zh-cn/3/library/inspect.html#inspect.Signature.format) 接受一个新参数 *unquote_annotations*。 如其为真值，字符串 [标注](https://docs.python.org/zh-cn/3/glossary.html#term-annotation) 将不带引号地显示。 （由 Jelle Zijlstra 在 [gh-101552](https://github.com/python/cpython/issues/101552) 中贡献。）.)

-

增加 [`ispackage()`](https://docs.python.org/zh-cn/3/library/inspect.html#inspect.ispackage) 函数用于确定一个对象是否为 [package](https://docs.python.org/zh-cn/3/glossary.html#term-package)。 （由 Zhikang Yan 在 [gh-125634](https://github.com/python/cpython/issues/125634) 中贡献。）.)

### io

-

使用 `read` 从非阻塞流读取文本时，如果操作无法立即返回字节，现在可能会引发 [`BlockingIOError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#BlockingIOError)。（由 Giovanni Siragusa 在 [gh-109523](https://github.com/python/cpython/issues/109523) 中贡献。）

-

添加 [`Reader`](https://docs.python.org/zh-cn/3/library/io.html#io.Reader) 和 [`Writer`](https://docs.python.org/zh-cn/3/library/io.html#io.Writer) 协议作为 [`typing.IO`](https://docs.python.org/zh-cn/3/library/typing.html#typing.IO), [`typing.TextIO`](https://docs.python.org/zh-cn/3/library/typing.html#typing.TextIO) 和 [`typing.BinaryIO`](https://docs.python.org/zh-cn/3/library/typing.html#typing.BinaryIO) 等伪协议的最简单替代。 （由 Sebastian Rittau 在 [gh-127648](https://github.com/python/cpython/issues/127648) 中贡献。）

### json

-

为 JSON 序列化错误添加异常说明以允许标识错误来源。 （由 Serhiy Storchaka 在 [gh-122163](https://github.com/python/cpython/issues/122163) 中贡献。）

-

通过 [`-m`](https://docs.python.org/zh-cn/3/using/cmdline.html#cmdoption-m) 开关来允许将 [`json`](https://docs.python.org/zh-cn/3/library/json.html#module-json) 模块作为脚本使用: **python -m json**。 现在推荐以此用法替代 **python -m json.tool**，后者已处于 [soft deprecated](https://docs.python.org/zh-cn/3/glossary.html#term-soft-deprecated) 状态。 参见 [JSON 命令行界面](https://docs.python.org/zh-cn/3/library/json.html#json-commandline) 文档。 （由 Trey Hunner 在 [gh-122873](https://github.com/python/cpython/issues/122873) 中贡献。）

-

默认情况下，[JSON 命令行界面](https://docs.python.org/zh-cn/3/library/json.html#json-commandline) 的输出会以彩色突出显示。这可以通过 [环境变量](https://docs.python.org/zh-cn/3/using/cmdline.html#using-on-controlling-color) 进行控制。（由 Tomas Roun 在 [gh-131952](https://github.com/python/cpython/issues/131952) 中贡献。）

### linecache

-

现在 [`getline()`](https://docs.python.org/zh-cn/3/library/linecache.html#linecache.getline) 可以获取冻结模块的源代码。 （由 Tian Gao 在 [gh-131638](https://github.com/python/cpython/issues/131638) 中贡献。）

### logging.handlers

-

现在 [`QueueListener`](https://docs.python.org/zh-cn/3/library/logging.handlers.html#logging.handlers.QueueListener) 对象可支持 [context manager](https://docs.python.org/zh-cn/3/glossary.html#term-context-manager) 协议。 （由 Charles Machalow 在 [gh-132106](https://github.com/python/cpython/issues/132106) 中贡献。）

-

[`QueueListener.start`](https://docs.python.org/zh-cn/3/library/logging.handlers.html#logging.handlers.QueueListener.start) 现在如果监听器已启动，会引发 [`RuntimeError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#RuntimeError)。（由 Charles Machalow 在 [gh-132106](https://github.com/python/cpython/issues/132106) 中贡献。）

### math

-

为模块中的域错误添加了更详细的错误消息。（由 Charlie Zhao 和 Sergey B Kirpichev 在 [gh-101410](https://github.com/python/cpython/issues/101410) 中贡献。）

### mimetypes

-

为模块增加公有的 [命令行界面](https://docs.python.org/zh-cn/3/library/mimetypes.html#mimetypes-cli)，通过 **python -m mimetypes** 唤起。 （由 Oleg Iarygin 和 Hugo van Kemenade 在 [gh-93096](https://github.com/python/cpython/issues/93096) 中贡献。）

-

增加了一些基于 RFC 和通常用例的新 MIME 类型：

用于字体的 Microsoft 和 [**RFC 8081**](https://datatracker.ietf.org/doc/html/rfc8081.html) MIME 类型

-

嵌入式 OpenType： `application/vnd.ms-fontobject`

-

OpenType 布局(OTF) `font/otf`

-

TrueType: `font/ttf`

-

WOFF 1.0 `font/woff`

-

WOFF 2.0 `font/woff2`

用于 Matroska 音视频数据容器结构的 [**RFC 9559**](https://datatracker.ietf.org/doc/html/rfc9559.html) MIME 类型

-

仅有音频，无视频： `audio/matroska` (`.mka`)

-

视频：`video/matroska` (`.mkv`)

-

立体视频: `video/matroska-3d` (`.mk3d`)

基于 RFC 的图像

-

[**RFC 1494**](https://datatracker.ietf.org/doc/html/rfc1494.html): CCITT Group 3 (`.g3`)

-

[**RFC 3362**](https://datatracker.ietf.org/doc/html/rfc3362.html): Real-time Facsimile, T.38 (`.t38`)

-

[**RFC 3745**](https://datatracker.ietf.org/doc/html/rfc3745.html): JPEG 2000 (`.jp2`)、扩展格式 (`.jpx`) 和复合格式 (`.jpm`)

-

[**RFC 3950**](https://datatracker.ietf.org/doc/html/rfc3950.html): 标签图像文件格式传真扩展，TIFF-FX (`.tfx`)

-

[**RFC 4047**](https://datatracker.ietf.org/doc/html/rfc4047.html): 灵活图像传输系统 (`.fits`)

-

[**RFC 7903**](https://datatracker.ietf.org/doc/html/rfc7903.html): 增强型图元文件 (`.emf`) 和 Windows 图元文件 (`.wmf`)

其他 MIME 类型的增加和改变

-

[**RFC 2361**](https://datatracker.ietf.org/doc/html/rfc2361.html): 将 `.avi` 的类型更改为 `video/vnd.avi`，将 `.wav` 的类型更改为 `audio/vnd.wave`

-

[**RFC 4337**](https://datatracker.ietf.org/doc/html/rfc4337.html)：添加 MPEG-4 `audio/mp4` (`.m4a`)

-

[**RFC 5334**](https://datatracker.ietf.org/doc/html/rfc5334.html)：添加 Ogg 媒体 (`.oga`，`.ogg` 和 `.ogx`)

-

[**RFC 6713**](https://datatracker.ietf.org/doc/html/rfc6713.html)：添加 `application/gzip` (`.gz`)

-

[**RFC 9639**](https://datatracker.ietf.org/doc/html/rfc9639.html): 添加 FLAC 格式的 `audio/flac` (`.flac`)

-

[**RFC 9512**](https://datatracker.ietf.org/doc/html/rfc9512.html) 针对 YAML 文件 (`.yaml` 和 `.yml`) 的 `application/yaml` MIME 类型

-

添加 7z `application/x-7z-compressed` (`.7z`)

-

非严格模式下，添加Android安装包 `application/vnd.android.package-archive` (`.apk`)

-

添加 deb `application/x-debian-package` (`.deb`)

-

添加 glTF 二进制格式 `model/gltf-binary` (`.glb`)

-

添加glTF JSON/ASCII格式 `model/gltf+json` (`.gltf`)

-

添加 M4V `video/x-m4v` (`.m4v`)

-

添加 PHP `application/x-httpd-php` (`.php`)

-

添加 RAR `application/vnd.rar` (`.rar`)

-

添加 RPM `application/x-rpm` (`.rpm`)

-

添加STL格式 `model/stl` (`.stl`)

-

添加 Windows 媒体视频 `video/x-ms-wmv` (`.wmv`)

-

事实上：添加WebM格式 `audio/webm` (`.weba`)

-

[ECMA-376](https://ecma-international.org/publications-and-standards/standards/ecma-376/): 添加 `.docx`、`.pptx` 和 `.xlsx` 类型

-

[OASIS](https://docs.oasis-open.org/office/v1.2/cs01/OpenDocument-v1.2-cs01-part1.html#Appendix_C): 添加 OpenDocument 格式的 `.odg`、`.odp`、`.ods` 和 `.odt` 类型

-

[W3C](https://www.w3.org/TR/epub-33/#app-media-type): 添加 EPUB 格式的 `application/epub+zip` (`.epub`)

（由Contributed by Sahil Prajapati 和 Hugo van Kemenade 在 [gh-84852](https://github.com/python/cpython/issues/84852) 中，由 Sasha "Nelie" Chernykh 和 Hugo van Kemenade 在 [gh-132056](https://github.com/python/cpython/issues/132056) 中，以及由 Hugo van Kemenade 在 [gh-89416](https://github.com/python/cpython/issues/89416), [gh-85957](https://github.com/python/cpython/issues/85957) 和 [gh-129965](https://github.com/python/cpython/issues/129965) 中贡献。）

### multiprocessing

-

在 macOS 以外的 Unix 平台上，['forkserver'](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-start-method-forkserver) 现在是默认的 [启动方法](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-start-methods) (替代 ['fork'](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-start-method-fork))。 此项更改不会影响 Windows 或 macOS，在这两个平台上 ['spawn'](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-start-method-spawn) 仍是默认的启动方法。

如果需要使用不兼容线程的 *fork* 方法，你必须通过来自 [`get_context()`](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing.get_context) 的上下文显式地发起请求（推荐方式）或通过 [`set_start_method()`](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing.set_start_method) 更改默认方法。

请参阅 [forkserver 限制说明](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-programming-forkserver) 了解与 *fork* 方法的差异信息，以及此项变更对存在以下情况的现有代码可能产生的影响：(1) 使用可变全局共享变量 (2) 包含无法被 [`pickle`](https://docs.python.org/zh-cn/3/library/pickle.html#module-pickle) 自动序列化的共享对象。

（由 Gregory P. Smith 在 [gh-84559](https://github.com/python/cpython/issues/84559) 中贡献）

-

现在 [`multiprocessing`](https://docs.python.org/zh-cn/3/library/multiprocessing.html#module-multiprocessing) 的 `'forkserver'` 启动方法会验证其控制套接字以避免单纯依赖文件系统权限来限制其他进程可能导致 forkserver 产生工作进程并运行代码。 （由 Gregory P. Smith 在 [gh-97514](https://github.com/python/cpython/issues/97514) 中贡献。）

-

针对 *list* 和 *dict* 类型的 [多进程代理对象](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-proxy-objects) 增加了此前被忽略的缺失方法：

> `clear()` 和 `copy()` 用于 [`list`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#list) 的代理 [`fromkeys()`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#dict.fromkeys)、`reversed(d)`、`d | {}`、`{} | d`、`d |= {'b': 2}` 用于 [`dict`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#dict) 的代理

（由 Roy Hyunjin Han 在 [gh-103134](https://github.com/python/cpython/issues/103134) 中贡献。）

-

通过 [`SyncManager.set()`](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing.managers.SyncManager.set) 增加对共享 [`set`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#set) 对象的支持。 [`Manager()`](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing.Manager) 方法中的 [`set()`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#set) 现已可用。 （由 Mingyu Park 在 [gh-129949](https://github.com/python/cpython/issues/129949) 中贡献。）

-

为 [`multiprocessing.Process`](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing.Process) 对象增加 [`interrupt()`](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing.Process.interrupt)，该方法通过发送 [`SIGINT`](https://docs.python.org/zh-cn/3/library/signal.html#signal.SIGINT) 来终结子进程。 这使得 [`finally`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#finally) 子句能为被终止的进程打印栈回溯信息。 （由 Artem Pulkin 在 [gh-131913](https://github.com/python/cpython/issues/131913) 中贡献。）

### operator

-

增加 [`is_none()`](https://docs.python.org/zh-cn/3/library/operator.html#operator.is_none) 和 [`is_not_none()`](https://docs.python.org/zh-cn/3/library/operator.html#operator.is_not_none) 函数对，其中 `operator.is_none(obj)` 等价于 `obj is None` 而 `operator.is_not_none(obj)` 等价于 `obj is not None`。 （由 Raymond Hettinger 和 Nico Mexis 在 [gh-115808](https://github.com/python/cpython/issues/115808) 中贡献。）

### os

-

增加 [`reload_environ()`](https://docs.python.org/zh-cn/3/library/os.html#os.reload_environ) 函数用于根据 [`os.putenv()`](https://docs.python.org/zh-cn/3/library/os.html#os.putenv), by [`os.unsetenv()`](https://docs.python.org/zh-cn/3/library/os.html#os.unsetenv) 或同一进程中在 Python 外部所做的环境变量来更新 [`os.environ`](https://docs.python.org/zh-cn/3/library/os.html#os.environ) 和 [`os.environb`](https://docs.python.org/zh-cn/3/library/os.html#os.environb)。 （由 Victor Stinner 在 [gh-120057](https://github.com/python/cpython/issues/120057) 中贡献。）

-

为 `os` 模块增加 [`SCHED_DEADLINE`](https://docs.python.org/zh-cn/3/library/os.html#os.SCHED_DEADLINE) 和 [`SCHED_NORMAL`](https://docs.python.org/zh-cn/3/library/os.html#os.SCHED_NORMAL) 常量。 （由 James Roy 在 [gh-127688](https://github.com/python/cpython/issues/127688) 中贡献。）.)

-

增加 [`readinto()`](https://docs.python.org/zh-cn/3/library/os.html#os.readinto) 函数用于从文件描述符读取数据到 [缓冲区对象](https://docs.python.org/zh-cn/3/c-api/buffer.html#bufferobjects)。 （由 Cody Maloney 在 [gh-129205](https://github.com/python/cpython/issues/129205) 中贡献。）.)

### os.path

-

传给 [`realpath()`](https://docs.python.org/zh-cn/3/library/os.path.html#os.path.realpath) 的 *strict* 形参接受一个新值 [`ALLOW_MISSING`](https://docs.python.org/zh-cn/3/library/os.path.html#os.path.ALLOW_MISSING)。 如果使用该值，则 [`FileNotFoundError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#FileNotFoundError) 以外的错误将被重新引发；结果路径可能会缺失但它将不会有符号链接。 （由 Petr Viktorin 为 [**CVE 2025-4517**](https://www.cve.org/CVERecord?id=CVE-2025-4517) 贡献。）

### pathlib

-

为 [`pathlib.Path`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.Path) 新增递归复制/移动文件和目录的方法：

-

[`copy()`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.Path.copy) 将一个文件或目录树复制到目标位置。

-

[`copy_into()`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.Path.copy_into) 会将内容复制 *到* 目标目录中。

-

[`move()`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.Path.move) 将一个文件或目录树移动到目标位置。

-

[`move_into()`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.Path.move_into) 会将内容移动 *到* 目标目录中。

（由 Barney Gale 在 [gh-73991](https://github.com/python/cpython/issues/73991) 中贡献。）

-

增加 [`info`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.Path.info) 属性，该属性将存储一个实现了新的 [`pathlib.types.PathInfo`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.types.PathInfo) 协议的对象。 此对象支持查询文件类型并会在内部缓存 [`stat()`](https://docs.python.org/zh-cn/3/library/os.html#os.stat) 的结果。 通过 [`iterdir()`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.Path.iterdir) 创建的 Path 对象会根据扫描父目录时收集到的文件类型信息进行初始化。 （由 Barney Gale 在 [gh-125413](https://github.com/python/cpython/issues/125413) 中贡献。）

### pdb

-

现在 [`pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#module-pdb) 模块支持使用新的 [`-p PID`](https://docs.python.org/zh-cn/3/library/pdb.html#cmdoption-pdb-p) 命令行选项远程附加到正在运行的 Python 进程：

```
python -m pdb -p 1234
```

该操作将连接到指定PID的Python进程，并允许您进行交互式调试。请注意，由于Python解释器的工作原理，当附加到阻塞在系统调用或等待I/O的远程进程时，调试功能只有在执行下一条字节码指令或进程收到信号时才会生效。

此特性使用 PEP 768 和新的 [`sys.remote_exec()`](https://docs.python.org/zh-cn/3/library/sys.html#sys.remote_exec) 函数来附加到远程进程并向其发送 PDB 命令。commands to it.

（由 Matt Wozniski 和 Pablo Galindo 在 [gh-131591](https://github.com/python/cpython/issues/131591) 中贡献。）

-

硬编码的断点 ([`breakpoint()`](https://docs.python.org/zh-cn/3/builtins/functions.html#breakpoint) 和 [`set_trace()`](https://docs.python.org/zh-cn/3/library/pdb.html#pdb.set_trace)) 现在会重用最近一次调用 [`set_trace()`](https://docs.python.org/zh-cn/3/library/pdb.html#pdb.Pdb.set_trace) 的 [`Pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#pdb.Pdb) 实例，而不是每次都新建一个实例。因此，所有实例特定的数据如 [`display`](https://docs.python.
org/zh-cn/3/library/pdb.html#pdbcommand-display) 和 [`commands`](https://docs.python.org/zh-cn/3/library/pdb.html#pdbcommand-commands) 在硬编码的断点之间都会被保留。（由 Tian Gao 在 [gh-121450](https://github.com/python/cpython/issues/121450) 中贡献。）

-

为 [`pdb.Pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#pdb.Pdb) 新增一个 *mode* 参数。当 [`pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#module-pdb) 处于 `inline` 模式时，禁用 `restart` 命令。（由 Tian Gao 在 [gh-123757](https://github.com/python/cpython/issues/123757) 中贡献。）

-

当用户尝试在 `inline` 模式下退出 [`pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#module-pdb) 时，会显示一个确认提示。输入 `y`、`Y`、按 `<Enter>` 或 `EOF` 将确认退出并调用 [`sys.exit()`](https://docs.python.org/zh-cn/3/library/sys.html#sys.exit)，而非引发 [`bdb.BdbQuit`](https://docs.python.org/zh-cn/3/library/bdb.html#bdb.BdbQuit)。（由 Tian Gao 在 [gh-124704](https://github.com/python/cpython/issues/124704) 中贡献。）

-

像 [`breakpoint()`](https://docs.python.org/zh-cn/3/builtins/functions.html#breakpoint) 或 [`pdb.set_trace()`](https://docs.python.org/zh-cn/3/library/pdb.html#pdb.set_trace) 这样的内联断点将始终在调用帧处暂停程序，而忽略 `skip` 模式（如果有的话）。（由 Tian Gao 在 [gh-130493](https://github.com/python/cpython/issues/130493) 中贡献。）

-

在 [`pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#module-pdb) 的多行输入中，行首的 `<tab>` 键现在会填充 4 个空格的缩进，而不是插入 `\t` 字符。（由 Tian Gao 在 [gh-130471](https://github.com/python/cpython/issues/130471) 中贡献。）

-

[`pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#module-pdb) 的多行输入中引入了自动缩进功能。当检测到新的代码块时，它会要么保持上一行的缩进，要么插入 4 个空格的缩进。（由 Tian Gao 在 [gh-133350](https://github.com/python/cpython/issues/133350) 中贡献。）

-

新增 `$_asynctask` 以在适用情况下访问当前的 asyncio 任务。（由 Tian Gao 在 [gh-124367](https://github.com/python/cpython/issues/124367) 中贡献。）

-

新增 [`pdb.set_trace_async()`](https://docs.python.org/zh-cn/3/library/pdb.html#pdb.set_trace_async) 以支持调试 asyncio 协程。此函数支持 [`await`](https://docs.python.org/zh-cn/3/reference/expressions.html#await) 语句。（由 Tian Gao 在 [gh-132576](https://github.com/python/cpython/issues/132576) 中贡献。）

-

在Source code displayed in [`pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#module-pdb) 中显示的源代码将有语法高亮。 除了 [`pdb.Pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#pdb.Pdb) 新增加的 `colorize` 参数，此特性还可使用与默认的 [interactive](https://docs.python.org/zh-cn/3/glossary.html#term-interactive) shell 相同的方法来控制。 （由 Tian Gao 和 Łukasz Langa 在 [gh-133355](https://github.com/python/cpython/issues/133355) 中贡献。）

### pickle

-

将 [`pickle`](https://docs.python.org/zh-cn/3/library/pickle.html#module-pickle) 模块的默认协议版本设置为 5。更多详细信息，请参见 [pickle protocols](https://docs.python.org/zh-cn/3/library/pickle.html#pickle-protocols)。

-

为 pickle 序列化错误添加异常说明以允许标识错误来源。 （由 Serhiy Storchaka 在 [gh-122213](https://github.com/python/cpython/issues/122213) 中贡献。）

### platform

-

增加 [`invalidate_caches()`](https://docs.python.org/zh-cn/3/library/platform.html#platform.invalidate_caches) 函数，用于使 `platform` 模块中的缓存结果失效。 （由 Bénédikt Tran 在 [gh-122549](https://github.com/python/cpython/issues/122549) 中贡献。）

### pydoc

-

帮助输出中的 [注解](https://docs.python.org/zh-cn/3/glossary.html#term-annotation) 现在通常以更接近原始源代码中的格式显示。（由 Jelle Zijlstra 在 [gh-101552](https://github.com/python/cpython/issues/101552) 中贡献。）

### re

-

在 [`正则表达式`](https://docs.python.org/zh-cn/3/library/re.html#module-re) 中，现支持将 `\z` 作为 `\Z` 的同义符使用。与行为存在微妙差异的 `\Z` 不同，`\z` 在其他多种正则表达式引擎中具有明确无歧义的解析方式。（由 Serhiy Storchaka 在 [gh-133306](https://github.com/python/cpython/issues/133306) 中贡献。）

-

现在 [`正则表达式`](https://docs.python.org/zh-cn/3/library/re.html#module-re) 中的 `\B` 将匹配空的输入字符串，这意味着它现在的行为总是与 `\b` 相反。 （由 Serhiy Storchaka 在 [gh-124130](https://github.com/python/cpython/issues/124130) 中贡献。）

### socket

-

改进并修复对蓝牙套接字的支持。

-

修复了 NetBSD 和 DragonFly BSD 系统上对蓝牙套接字的支持。（由 Serhiy Storchaka 在 [gh-132429](https://github.com/python/cpython/issues/132429) 中贡献。）

-

修复了 FreeBSD 系统上对 [`BTPROTO_HCI`](https://docs.python.org/zh-cn/3/library/socket.html#socket.BTPROTO_HCI) 的支持。（由 Victor Stinner 在 [gh-111178](https://github.com/python/cpython/issues/111178) 中贡献。）

-

新增对 FreeBSD 系统上 [`BTPROTO_SCO`](https://docs.python.org/zh-cn/3/library/socket.html#socket.BTPROTO_SCO) 的支持。（由 Serhiy Storchaka 在 [gh-85302](https://github.com/python/cpython/issues/85302) 中贡献。）

-

新增对 FreeBSD 系统上 [`BTPROTO_L2CAP`](https://docs.python.org/zh-cn/3/library/socket.html#socket.BTPROTO_L2CAP) 地址中 *cid* 和 *bdaddr_type* 的支持。（由 Serhiy Storchaka 在 [gh-132429](https://github.com/python/cpython/issues/132429) 中贡献。）

-

新增对 Linux 系统上 [`BTPROTO_HCI`](https://docs.python.org/zh-cn/3/library/socket.html#socket.BTPROTO_HCI) 地址中 *channel* 的支持。（由 Serhiy Storchaka 在 [gh-70145](https://github.com/python/cpython/issues/70145) 中贡献。）

-

在 Linux 系统上，允许将整数作为 [`BTPROTO_HCI`](https://docs.python.org/zh-cn/3/library/socket.html#socket.BTPROTO_HCI) 的地址。（由 Serhiy Storchaka 在 [gh-132099](https://github.com/python/cpython/issues/132099) 中贡献。）

-

在 [`BTPROTO_L2CAP`](https://docs.python.org/zh-cn/3/library/socket.html#socket.BTPROTO_L2CAP) 中，[`getsockname()`](https://docs.python.org/zh-cn/3/library/socket.html#socket.socket.getsockname) 会返回 *cid*。（由 Serhiy Storchaka 在 [gh-132429](https://github.com/python/cpython/issues/132429) 中贡献。）

-

新增了许多常量。（由 Serhiy Storchaka 在 [gh-132734](https://github.com/python/cpython/issues/132734) 中贡献。）

### ssl

-

通过 [`HAS_PHA`](https://docs.python.org/zh-cn/3/library/ssl.html#ssl.HAS_PHA) 布尔值指明 `ssl` 模块是否支持 TLSv1.3 握手后客户端认证 (PHA)。 （由 Will Childs-Klein 在 [gh-128036](https://github.com/python/cpython/issues/128036) 中贡献。）

### struct

-

在 [`struct`](https://docs.python.org/zh-cn/3/library/struct.html#module-struct) 模块中支持 float complex 和 double complex 这两种 C 类型 (分别对应格式字符 `'F'` 和 `'D'`)。 （由 Sergey B Kirpichev 在 [gh-121249](https://github.com/python/cpython/issues/121249) 中贡献。）

### symtable

-

对外暴露下列 [`Symbol`](https://docs.python.org/zh-cn/3/library/symtable.html#symtable.Symbol) 方法：

-

[`is_comp_cell()`](https://docs.python.org/zh-cn/3/library/symtable.html#symtable.Symbol.is_comp_cell)

-

[`is_comp_iter()`](https://docs.python.org/zh-cn/3/library/symtable.html#symtable.Symbol.is_comp_iter)

-

[`is_free_class()`](https://docs.python.org/zh-cn/3/library/symtable.html#symtable.Symbol.is_free_class)

（由 Bénédikt Tran 在 [gh-120029](https://github.com/python/cpython/issues/120029) 中贡献。）

### sys

-

之前未写入文档的特殊函数 [`sys.getobjects()`](https://docs.python.org/zh-cn/3/library/sys.html#sys.getobjects)，它仅存在于某些专用的 Python 构建版，现在可以从其他解释器而非调用它的解释器返回对象。 （由 Eric Snow 在 [gh-125286](https://github.com/python/cpython/issues/125286) 中贡献。）.)

-

新增 [`sys._is_immortal()`](https://docs.python.org/zh-cn/3/library/sys.html#sys._is_immortal) 函数，用于判断一个对象是否为 [immortal](https://docs.python.org/zh-cn/3/glossary.html#term-immortal)。 （由 Peter Bierma 在 [gh-128509](https://github.com/python/cpython/issues/128509) 中贡献。）

-

在 FreeBSD 上，[`sys.platform`](https://docs.python.org/zh-cn/3/library/sys.html#sys.platform) 将不再包含主版本号。 它将始终为 `'freebsd'`，而不是 `'freebsd13'` 或 `'freebsd14'`。 （由 Michael Osipov 在 [gh-129393](https://github.com/python/cpython/issues/129393) 中贡献。）

-

为 [`sys._clear_type_cache()`](https://docs.python.org/zh-cn/3/library/sys.html#sys._clear_type_cache) 函数引发 [`DeprecationWarning`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#DeprecationWarning) 警告。该函数在 Python 3.13 中已被弃用，但此前并未引发运行时警告。

-

增加 [`sys.remote_exec()`](https://docs.python.org/zh-cn/3/library/sys.html#sys.remote_exec) 以实现新的外部调试器接口。 请参阅 PEP 768 了解详情。 （由 Pablo Galindo Salgado, Matt Wozniski 和 Ivona Stojanovic 在 [gh-131591](https://github.com/python/cpython/issues/131591) 中贡献。）

-

增加 [`sys._jit`](https://docs.python.org/zh-cn/3/library/sys.html#sys._jit) 命名空间，包含用于内省即时编译的工具。 （由 Brandt Bucher 在 [gh-133231](https://github.com/python/cpython/issues/133231) 中贡献。）

### sys.monitoring

-

新增两个监视事件 [`BRANCH_LEFT`](https://docs.python.org/zh-cn/3/library/sys.monitoring.html#monitoring-event-BRANCH_LEFT) 和 [`BRANCH_RIGHT`](https://docs.python.org/zh-cn/3/library/sys.monitoring.html#monitoring-event-BRANCH_RIGHT)。 它们将替代并弃用 `BRANCH` 事件。 （由 Mark Shannon 在 [gh-122548](https://github.com/python/cpython/issues/122548) 中贡献。）.)

-

Add [`sys.monitoring.clear_tool_id()`](https://docs.python.org/zh-cn/3/library/sys.monitoring.html#sys.monitoring.clear_tool_id) to unregister all events and callback functions associated with a tool identifier. [`sys.monitoring.free_tool_id()`](https://docs.python.org/zh-cn/3/library/sys.monitoring.html#sys.monitoring.free_tool_id) now calls it before releasing the tool identifier, instead of leaving its events and callbacks registered. (Contributed by Tian Gao in [gh-116750](https://github.com/python/cpython/issues/116750).)

### sysconfig

-

在 Windows 上为 [`get_config_vars()`](https://docs.python.org/zh-cn/3/library/sysconfig.html#sysconfig.get_config_vars) 增加 `ABIFLAGS` 键。 （由 Xuehai Pan 在 [gh-131799](https://github.com/python/cpython/issues/131799) 中贡献。）

### tarfile

-

[`data_filter()`](https://docs.python.org/zh-cn/3/library/tarfile.html#tarfile.data_filter) 现在会对符号链接目标进行规范化处理，以避免路径遍历攻击。（由 Petr Viktorin 在 [gh-127987](https://github.com/python/cpython/issues/127987) 和 [**CVE 2025-4138**](https://www.cve.org/CVERecord?id=CVE-2025-4138) 中贡献。）

-

[`extractall()`](https://docs.python.org/zh-cn/3/library/tarfile.html#tarfile.TarFile.extractall) 现在在目录被移除或被其他类型的文件替换时，会跳过对目录属性的修复。（由 Petr Viktorin 在 [gh-127987](https://github.com/python/cpython/issues/127987) 和 [**CVE 2024-12718**](https://www.cve.org/CVERecord?id=CVE-2024-12718) 中贡献。）

-

[`extract()`](https://docs.python.org/zh-cn/3/library/tarfile.html#tarfile.TarFile.extract) 和 [`extractall()`](https://docs.python.org/zh-cn/3/library/tarfile.html#tarfile.TarFile.extractall) 现在在以下两种情况会（重新）应用提取过滤器：一是用另一个归档成员的副本替换链接（硬链接或符号链接）时，二是修复目录属性时。前者会引发一个新异常 [`LinkFallbackError`](https://docs.python.org/zh-cn/3/library/tarfile.html#tarfile.LinkFallbackError)。（由 Petr Viktorin 针对 [**CVE 2025-4330**](https://www.cve.org/CVERecord?id=CVE-2025-4330) 和 [**CVE 2024-12718**](https://www.cve.org/CVERecord?id=CVE-2024-12718) 贡献。）

-

[`extract()`](https://docs.python.org/zh-cn/3/library/tarfile.html#tarfile.TarFile.extract) 和 [`extractall()`](https://docs.python.org/zh-cn/3/library/tarfile.html#tarfile.TarFile.extractall) 在 [`errorlevel()`](https://docs.python.org/zh-cn/3/library/tarfile.html#tarfile.TarFile.errorlevel) 为 0 时，不再提取被拒绝的成员。（由 Matt Prodani 和 Petr Viktorin 在 [gh-112887](https://github.com/python/cpython/issues/112887) 以及 [**CVE 2025-4435**](https://www.cve.org/CVERecord?id=CVE-2025-4435) 中贡献。）

### threading

-

[`threading.Thread.start()`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Thread.start) 现在会将操作系统线程名称设置为 [`threading.Thread.name`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Thread.name)。（由 Victor Stinner 在 [gh-59705](https://github.com/python/cpython/issues/59705) 中贡献。）

### tkinter

-

让 [`tkinter`](https://docs.python.org/zh-cn/3/library/tkinter.html#module-tkinter) 控件的 `after()` 和 `after_idle()` 方法接受关键字参数。 （由 Zhikang Yan 在 [gh-126899](https://github.com/python/cpython/issues/126899) 中贡献。）.)

-

增加为 `tkinter.OptionMenu` 和 `tkinter.ttk.OptionMenu` 指定名称的功能。 （由 Zhikang Yan 在 [gh-130482](https://github.com/python/cpython/issues/130482) 中贡献。）

### turtle（海龟绘图）

-

为 [`turtle.fill()`](https://docs.python.org/zh-cn/3/library/turtle.html#turtle.fill), [`turtle.poly()`](https://docs.python.org/zh-cn/3/library/turtle.html#turtle.poly) 和 [`turtle.no_animation()`](https://docs.python.org/zh-cn/3/library/turtle.html#turtle.no_animation) 增加上下文管理器。 （由 Marie Roald 和 Yngve Mardal Moe 在 [gh-126350](https://github.com/python/cpython/issues/126350) 中贡献。）

### types（类型）

-

[`types.UnionType`](https://docs.python.org/zh-cn/3/library/types.html#types.UnionType) 现在是 [`typing.Union`](https://docs.python.org/zh-cn/3/library/typing.html#typing.Union) 的别名。更多详情请参见 下方。（由 Jelle Zijlstra 在 [gh-105499](https://github.com/python/cpython/issues/105499) 中贡献。）

### typing

-

现在 [`types.UnionType`](https://docs.python.org/zh-cn/3/library/types.html#types.UnionType) 和 [`typing.Union`](https://docs.python.org/zh-cn/3/library/typing.html#typing.Union) 类型互为别名，这意味着旧式联合（通过 `Union[int, str]` 创建）和新式联合（通过 `int | str` 创建）现在都会创建相同的运行时类型的实例。 这统一了两种语法形式的行为，但也导致了一些行为差异并可能影响在运行时对类型进行内省的用户：

-

两种创建联合的语法现在将在 [`repr()`](https://docs.python.org/zh-cn/3/builtins/functions.html#repr) 中产生相同的字符串表示形式。 例如，`repr(Union[int, str])` 现在将为 `"int | str"` 而不是 `"typing.Union[int, str]"`。

-

使用旧语法创建的联合将不再被缓存。 在之前版本中，多次运行 `Union[int, str]` 会返回同一个对象 (`Union[int, str] is Union[int, str]` 将为 `True`)，但现在会返回两个不同的对象。 请使用 `==` 来比较联合是否相等，而不要用 `is`。 新式联合从未以这种方式进行缓存。 这一变化可能会增加某些程序的内存占用，这些程序会通过下标 `typing.Union` 创建大量联合。 不过，有几个因素会缓解这种开销：由于 [**PEP 649**](https://peps.python.org/pep-0649/) 的引入在 Python 3.14 中默认不再对标注中使用的联合进行求值；[`types.UnionType`](https://docs.python.org/zh-cn/3/library/types.html#types.UnionType) 的实例本身要比之前 Python 版本中 `Union[]` 返回的对象小得多；并且移除缓存也节省了部分空间。 因此对于大多数用户来说这一变化不太可能导致内存占用的显著增加。

-

在之前版本中，旧式联合是使用私有类 `typing._UnionGenericAlias` 来实现的。 该类对当前的实现来说已不再需要，但它仍被保留用于向下兼容，计划在 Python 3.17 中移除。 用户应当使用写入文档的内省辅助函数如 [`get_origin()`](https://docs.python.org/zh-cn/3/library/typing.html#typing.get_origin) 和 [`typing.get_args()`](https://docs.python.org/zh-cn/3/library/typing.html#typing.get_args) 而不是依赖私有的实现细节。

-

现在可以在 [`isinstance()`](https://docs.python.org/zh-cn/3/builtins/functions.html#isinstance) 检查中使用 [`typing.Union`](https://docs.python.org/zh-cn/3/library/typing.html#typing.Union) 本身。例如，`isinstance(int | str, typing.Union)` 将返回 `True`；而此前这会引发 [`TypeError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#TypeError)。

-

[`typing.Union`](https://docs.python.org/zh-cn/3/library/typing.html#typing.Union) 对象的 `__args__` 属性已不再可写。

-

现在已无法设置 [`Union`](https://docs.python.org/zh-cn/3/library/typing.html#typing.Union) 对象的任何属性。 在之前版本中设置操作只对双下划线属性有效，从未在文档中写明，并且在许多情况下也有潜在问题。

（由 Jelle Zijlstra 在 [gh-105499](https://github.com/python/cpython/issues/105499) 中贡献。）

-

[`TypeAliasType`](https://docs.python.org/zh-cn/3/library/typing.html#typing.TypeAliasType) 现在支持星号解包操作。

### unicodedata

-

Unicode 数据库已更新到 16.0.0 版本。

### unittest

-

[`unittest`](https://docs.python.org/zh-cn/3/library/unittest.html#module-unittest) 模块的输出现在默认启用彩色显示，可通过 [环境变量](https://docs.python.org/zh-cn/3/using/cmdline.html#using-on-controlling-color) 进行控制。（由 Hugo van Kemenade 在 [gh-127221](https://github.com/python/cpython/issues/127221) 中贡献。）

-

unittest 发现机制重新支持将 [namespace package](https://docs.python.org/zh-cn/3/glossary.html#term-namespace-package) 作为起始目录，该功能曾在 Python 3.11 中被移除。 （由 Jacob Walls 在 [gh-80958](https://github.com/python/cpython/issues/80958) 中贡献。）

-

在 [`TestCase`](https://docs.python.org/zh-cn/3/library/unittest.html#unittest.TestCase) 类中新增了多个方法，这些方法可提供更专门化的测试。

-

[`assertHasAttr()`](https://docs.python.org/zh-cn/3/library/unittest.html#unittest.TestCase.assertHasAttr) and [`assertNotHasAttr()`](https://docs.python.org/zh-cn/3/library/unittest.html#unittest.TestCase.assertNotHasAttr) check whether the object has a particular attribute.

-

[`assertIsSubclass()`](https://docs.python.org/zh-cn/3/library/unittest.html#unittest.TestCase.assertIsSubclass) 和 [`assertNotIsSubclass()`](https://docs.python.org/zh-cn/3/library/unittest.html#unittest.TestCase.assertNotIsSubclass) 用于检查对象是否是某个特定类的子类，或者是否是某个类元组中任一类的子类。

-

[`assertStartsWith()`](https://docs.python.org/zh-cn/3/library/unittest.html#unittest.TestCase.assertStartsWith)、[`assertNotStartsWith()`](https://docs.python.org/zh-cn/3/library/unittest.html#unittest.TestCase.assertNotStartsWith)、[`assertEndsWith()`](https://docs.python.org/zh-cn/3/library/unittest.html#unittest.TestCase.assertEndsWith) 和 [`assertNotEndsWith()`](https://docs.python.org/zh-cn/3/library/unittest.html#unittest.TestCase.assertNotEndsWith) 用于检查 Unicode 字符串或字节串是否以特定字符串开头或结尾。

（由 Serhiy Storchaka 在 [gh-71339](https://github.com/python/cpython/issues/71339) 中贡献。）

### urllib

-

升级 [`urllib.request`](https://docs.python.org/zh-cn/3/library/urllib.request.html#module-urllib.request) 的 HTTP 摘要认证算法，支持 [**RFC 7616**](https://datatracker.ietf.org/doc/html/rfc7616.html) 中规定的 SHA-256 摘要认证。（由 Calvin Bui 在 [gh-128193](https://github.com/python/cpython/issues/128193) 中贡献。）

-

改进解析和生成 `file:` URL 时的易用性和标准合规性。

在 [`url2pathname()`](https://docs.python.org/zh-cn/3/library/urllib.request.html#urllib.request.url2pathname) 中：

-

当新的 *require_scheme* 参数设为 true 时，接受完整的 URL。

-

如果 URL 的权限部分与本地主机名匹配，则舍弃该部分。

-

当新的 *resolve_host* 参数设为 true 时，若 URL 的权限部分解析为本地 IP 地址，则舍弃该部分。

-

丢弃 URL 查询和片段组件。

-

如果 URL 的权限部分不是本地的，则引发 [`URLError`](https://docs.python.org/zh-cn/3/library/urllib.error.html#urllib.error.URLError)，但在 Windows 系统上，仍会像以前一样返回 UNC 路径。

在 [`pathname2url()`](https://docs.python.org/zh-cn/3/library/urllib.request.html#urllib.request.pathname2url) 中：

-

当新的 *add_scheme* 参数设为 true 时，返回完整的 URL。

-

当路径以斜杠开头时，包含一个空的 URL 权限部分。例如，路径 `/etc/hosts` 会被转换为 URL `///etc/hosts`。

在 Windows 系统上，盘符不再转换为大写，且非紧跟在驱动器号后的 `:` 字符不再引发 [`OSError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#OSError) 异常。

（由 Barney Gale 在 [gh-125866](https://github.com/python/cpython/issues/125866) 中贡献。）

### uuid

-

通过 [`uuid6()`](https://docs.python.org/zh-cn/3/library/uuid.html#uuid.uuid6), [`uuid7()`](https://docs.python.org/zh-cn/3/library/uuid.html#uuid.uuid7) 和 [`uuid8()`](https://docs.python.org/zh-cn/3/library/uuid.html#uuid.uuid8) 分别添加对 UUID 第 6, 7 和 8 版的支持，具体规范见 [**RFC 9562**](https://datatracker.ietf.org/doc/html/rfc9562.html)。 （由 Bénédikt Tran 在 [gh-89083](https://github.com/python/cpython/issues/89083) 中贡献。）

-

[`NIL`](https://docs.python.org/zh-cn/3/library/uuid.html#uuid.NIL) 和 [`MAX`](https://docs.python.org/zh-cn/3/library/uuid.html#uuid.MAX) 现已可用于表示 [**RFC 9562**](https://datatracker.ietf.org/doc/html/rfc9562.html) 中定义的 Nil 和 Max UUID 格式。 （由 Nick Pope 在 [gh-128427](https://github.com/python/cpython/issues/128427) 中贡献。）

-

允许通过 [`python -m uuid --count`](https://docs.python.org/zh-cn/3/library/uuid.html#cmdoption-uuid-count) 在命令行中同时生成多个 UUID。 （由 Simon Legner 在 [gh-131236](https://github.com/python/cpython/issues/131236) 中贡献。）

### webbrowser

-

`BROWSER` 环境变量中的名称现在可以引用 [`webbrowser`](https://docs.python.org/zh-cn/3/library/webbrowser.html#module-webbrowser) 模块中已注册的浏览器，而不必总是生成新的浏览器命令。

这使得可以将 `BROWSER` 设置为 macOS 上受支持的浏览器之一的值。

### zipfile

-

增加 [`ZipInfo._for_archive`](https://docs.python.org/zh-cn/3/library/zipfile.html#zipfile.ZipInfo._for_archive) 方法，用于为 [`ZipInfo`](https://docs.python.org/zh-cn/3/library/zipfile.html#zipfile.ZipInfo) 对象解析适当的默认值并由 [`ZipFile.writestr`](https://docs.python.org/zh-cn/3/library/zipfile.html#zipfile.ZipFile.writestr) 使用。 （由 Bénédikt Tran 在 [gh-123424](https://github.com/python/cpython/issues/123424) 中贡献。）

-

[`ZipFile.writestr()`](https://docs.python.org/zh-cn/3/library/zipfile.html#zipfile.ZipFile.writestr) 现在会遵从 `SOURCE_DATE_EPOCH` 环境变量设置以便更好地支持可复现的构建。 （由李佳昊在 [gh-91279](https://github.com/python/cpython/issues/91279) 中贡献。）

## 性能优化

-

几个标准库模块的导入时间已得到改进，包括 [`annotationlib`](https://docs.python.org/zh-cn/3/library/annotationlib.html#module-annotationlib)、[`ast`](https://docs.python.org/zh-cn/3/library/ast.html#module-ast)、[`asyncio`](https://docs.python.org/zh-cn/3/library/asyncio.html#module-asyncio)、[`base64`](https://docs.python.org/zh-cn/3/library/base64.html#module-base64)、[`cmd`](https://docs.python.org/zh-cn/3/library/cmd.html#module-cmd)、[`csv`](https://docs.
python.org/zh-cn/3/library/csv.html#module-csv)、[`gettext`](https://docs.python.org/zh-cn/3/library/gettext.html#module-gettext)、[`importlib.util`](https://docs.python.org/zh-cn/3/library/importlib.html#module-importlib.util)、[`locale`](https://docs.python.org/zh-cn/3/library/locale.html#module-locale)、[`mimetypes`](https://docs.python.org/zh-cn/3/library/mimetypes.html#module-mimetypes)、[`optparse`](https://docs.
python.org/zh-cn/3/library/optparse.html#module-optparse)、[`pickle`](https://docs.python.org/zh-cn/3/library/pickle.html#module-pickle)、[`pprint`](https://docs.python.org/zh-cn/3/library/pprint.html#module-pprint)、[`pstats`](https://docs.python.org/zh-cn/3/library/profile.html#module-pstats)、[`shlex`](https://docs.python.org/zh-cn/3/library/shlex.html#module-shlex)、[`socket`](https://docs.python.org/zh-cn/3/library/socket.
html#module-socket)、[`string`](https://docs.python.org/zh-cn/3/library/string.html#module-string)、[`subprocess`](https://docs.python.org/zh-cn/3/library/subprocess.html#module-subprocess)、[`threading`](https://docs.python.org/zh-cn/3/library/threading.html#module-threading)、[`tomllib`](https://docs.python.org/zh-cn/3/library/tomllib.html#module-tomllib)、[`types`](https://docs.python.org/zh-cn/3/library/types.
html#module-types) 和 [`zipfile`](https://docs.python.org/zh-cn/3/library/zipfile.html#module-zipfile)。

（由 Adam Turner、Bénédikt Tran、Chris Markiewicz、Eli Schwartz、Hugo van Kemenade、Jelle Zijlstra 等人在 [gh-118761](https://github.com/python/cpython/issues/118761) 中贡献。）

-

现在解释器会在确保安全时避免某些引用计数修改。 这可能导致从 [`sys.getrefcount()`](https://docs.python.org/zh-cn/3/library/sys.html#sys.getrefcount) 和 [`Py_REFCNT()`](https://docs.python.org/zh-cn/3/c-api/refcounting.html#c.Py_REFCNT) 返回的值相比之前的 Python 版本出现差异。 请参阅 下文 了解详情。

### asyncio

-

在为 [`原生任务`](https://docs.python.org/zh-cn/3/library/asyncio-task.html#asyncio.Task) 实现新的每线程双链表之后标准的基准测试结果有 10-20% 的提升，同时还减少了内存使用。 这使得外部内省工具如 python -m asyncio pstree 能够对在所有线程中运行的 asyncio 任务的调用图进行内省。 （由 Kumar Aditya 在 [gh-107803](https://github.com/python/cpython/issues/107803) 中贡献。）

-

该模块现在对 [自由线程构建](https://docs.python.org/zh-cn/3/glossary.html#term-free-threading) 提供了一流的支持。这使得多个事件循环可以在不同线程中并行执行，并且随着线程数量的增加线性扩展。（由 Kumar Aditya 在 [gh-128002](https://github.com/python/cpython/issues/128002) 中贡献。）

### base64

-

[`b16decode()`](https://docs.python.org/zh-cn/3/library/base64.html#base64.b16decode) 的速度现在提升了高达六倍。（由 Bénédikt Tran、Chris Markiewicz 和 Adam Turner 在 [gh-118761](https://github.com/python/cpython/issues/118761) 中贡献。）

### bdb

-

基本调试器现在有了基于 [`sys.monitoring`](https://docs.python.org/zh-cn/3/library/sys.monitoring.html#module-sys.monitoring) 的后端，可以通过将 `'monitoring'` 传递给 [`Bdb`](https://docs.python.org/zh-cn/3/library/bdb.html#bdb.Bdb) 类的新 *backend* 参数来选择。（由 Tian Gao 在 [gh-124533](https://github.com/python/cpython/issues/124533) 中贡献。）

### difflib

-

[`IS_LINE_JUNK()`](https://docs.python.org/zh-cn/3/library/difflib.html#difflib.IS_LINE_JUNK) 函数的速度现在提升了一倍。（由 Adam Turner 和 Semyon Moroz 在 [gh-130167](https://github.com/python/cpython/issues/130167) 中贡献。）

### gc

-

**自 Python 3.14.5 开始:**

Python 3.14.0-3.14.4 发行版带有新的增量式垃圾收集器。 不过，由于大量在生产环境中出现显著内存压力的 [报告](https://github.com/python/cpython/issues/142516)，它已被更改回 3.13 中的世代式 GC。 这是 Python 3.14.5 及之后版本在使用的 GC。

-

**在之前的 Python 3.14.0-3.14.4 中:**

新的 增量垃圾回收器 意味着对于较大的堆，最大暂停时间减少了至少一个数量级。

由于这种优化，[`get_threshold()`](https://docs.python.org/zh-cn/3/library/gc.html#gc.get_threshold) 和 [`set_threshold()`](https://docs.python.org/zh-cn/3/library/gc.html#gc.set_threshold) 的结果含义发生了变化，同时还有 [`get_count()`](https://docs.python.org/zh-cn/3/library/gc.html#gc.get_count) 和 [`get_stats()`](https://docs.python.org/zh-cn/3/library/gc.html#gc.get_stats)。

-

为了向后兼容，[`get_threshold()`](https://docs.python.org/zh-cn/3/library/gc.html#gc.get_threshold) 继续返回一个三项元组。第一个值是年轻代回收的阈值，与之前相同；第二个值决定了老年代回收的扫描速率（默认值为10，值越高意味着老年代回收扫描越慢）。第三个值现在没有意义，总是为零。

-

[`set_threshold()`](https://docs.python.org/zh-cn/3/library/gc.html#gc.set_threshold) 现在会忽略第二个之后的任何项。

-

[`get_count()`](https://docs.python.org/zh-cn/3/library/gc.html#gc.get_count) 和 [`get_stats()`](https://docs.python.org/zh-cn/3/library/gc.html#gc.get_stats) 方法仍返回相同格式的结果。唯一的区别在于，结果不再分别对应新生代、老化代和老年代，而是对应新生代以及老年代的待老化空间和回收空间。

总之，尝试操控循环垃圾回收器行为的代码可能无法完全按预期工作，但几乎不会造成危害。其他所有代码都将正常运行。

（由 Mark Shannon 在 [gh-108362](https://github.com/python/cpython/issues/108362) 中贡献。）

### io

-

打开和读取文件现在执行更少的系统调用。完整读取一个小型操作系统缓存文件的速度提高了最多15%。（由 Cody Maloney 和 Victor Stinner 在 [gh-120754](https://github.com/python/cpython/issues/120754) 和 [gh-90102](https://github.com/python/cpython/issues/90102) 中贡献。）

### pathlib

-

[`Path.read_bytes`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.Path.read_bytes) 现在使用无缓冲模式打开文件，完整读取的速度提高了 9% 到 17%。（由 Cody Maloney 在 [gh-120754](https://github.com/python/cpython/issues/120754) 中贡献。）

### pdb

-

[`pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#module-pdb) 现在支持两种后端，基于 [`sys.settrace()`](https://docs.python.org/zh-cn/3/library/sys.html#sys.settrace) 或 [`sys.monitoring`](https://docs.python.org/zh-cn/3/library/sys.monitoring.html#module-sys.monitoring)。使用 [pdb CLI](https://docs.python.org/zh-cn/3/library/pdb.html#pdb-cli) 或 [`breakpoint()`](https://docs.python.org/zh-cn/3/builtins/functions.
html#breakpoint) 将始终使用 `sys.monitoring` 后端。显式实例化 [`pdb.Pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#pdb.Pdb) 及其派生类将默认使用 `sys.settrace()` 后端，这是可配置的。（由 Tian Gao 在 [gh-124533](https://github.com/python/cpython/issues/124533) 中贡献。）

### textwrap

-

优化 [`dedent()`](https://docs.python.org/zh-cn/3/library/textwrap.html#textwrap.dedent) 函数，可达到平均 2.4x 的性能提升，对于大量输入提升效果更大，并修复对于使用空格和制表符以外的空白符的空行执行规范化不完整的程序缺陷。

### uuid

-

[`uuid3()`](https://docs.python.org/zh-cn/3/library/uuid.html#uuid.uuid3) 和 [`uuid5()`](https://docs.python.org/zh-cn/3/library/uuid.html#uuid.uuid5) 对于16字节名称的速度现在大约提高了40%，对于1024字节名称的速度提高了20%。更长名称的性能保持不变。（由 Bénédikt Tran 在 [gh-128150](https://github.com/python/cpython/issues/128150) 中贡献。）

-

[`uuid4()`](https://docs.python.org/zh-cn/3/library/uuid.html#uuid.uuid4) 的速度现在提高了约30%。（由 Bénédikt Tran 在 [gh-128150](https://github.com/python/cpython/issues/128150) 中贡献。）

### zlib

-

在 Windows 上，[zlib-ng](https://github.com/zlib-ng/zlib-ng) 现在用作默认二进制文件中 [`zlib`](https://docs.python.org/zh-cn/3/library/zlib.html#module-zlib) 模块的实现。已知 `zlib-ng` 与之前使用的 `zlib` 实现之间没有不兼容性。这应在所有压缩级别上带来更好的性能。

值得注意的是，`zlib.Z_BEST_SPEED` (`1`) 可能会导致比之前的实现显著更低的压缩率，同时显著减少压缩所需的时间。

（由 Steve Dower 在 [gh-91349](https://github.com/python/cpython/issues/91349) 中贡献。）

## 移除

### argparse

-

移除 `BooleanOptionalAction` 的 *type*、 *choices* 和 *metavar* 形参。 它们自 Python 3.12 起已被弃用。 （由 Nikita Sobolev 在 [gh-118805](https://github.com/python/cpython/issues/118805) 中贡献。）

-

在参数组上调用 [`add_argument_group()`](https://docs.python.org/zh-cn/3/library/argparse.html#argparse.ArgumentParser.add_argument_group) 现在会引发 [`ValueError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#ValueError)。 类似地，在互斥组上调用 `add_argument_group()` 或 [`add_mutually_exclusive_group()`](https://docs.python.org/zh-cn/3/library/argparse.html#argparse.ArgumentParser.add_mutually_exclusive_group) 现在都会引发 `ValueError`。 这种“嵌套调用”从未被支持，经常无法正常工作，且通过继承关系被意外暴露。 该功能自 Python 3.11 起已被弃用。 （由 Savannah Ostrowski 在 [gh-127186](https://github.com/python/cpython/issues/127186) 中贡献。）

### ast（抽象语法树）

-

移除以下自 Python 3.8 起作为 [`Constant`](https://docs.python.org/zh-cn/3/library/ast.html#ast.Constant) 的已弃用别名，且自 Python 3.12 起已发出弃用警告的类：

-

`Bytes`

-

`Ellipsis`

-

`NameConstant`

-

`Num`

-

`Str`

由于这些移除操作，当自定义的 [`NodeVisitor`](https://docs.python.org/zh-cn/3/library/ast.html#ast.NodeVisitor) 子类访问抽象语法树（AST）时，用户定义的 `visit_Num`、`visit_Str`、`visit_Bytes`、`visit_NameConstant` 和 `visit_Ellipsis` 方法将不再被调用。请改用定义 `visit_Constant` 方法。

（由 Alex Waygood 在 [gh-119562](https://github.com/python/cpython/issues/119562) 中贡献。）

-

移除以下 [`ast.Constant`](https://docs.python.org/zh-cn/3/library/ast.html#ast.Constant) 为兼容现已移除的 AST 类而保留的已弃用属性：

-

`Constant.n`

-

`Constant.s`

改用 `Constant.value`。 （由 Alex Waygood 在 [gh-119562](https://github.com/python/cpython/issues/119562) 中贡献。）

### asyncio

-

移除以下自 Python 3.12 起已被弃用的类、方法和函数：

-

`AbstractChildWatcher`

-

`FastChildWatcher`

-

`MultiLoopChildWatcher`

-

`PidfdChildWatcher`

-

`SafeChildWatcher`

-

`ThreadedChildWatcher`

-

`AbstractEventLoopPolicy.get_child_watcher()`

-

`AbstractEventLoopPolicy.set_child_watcher()`

-

`get_child_watcher()`

-

`set_child_watcher()`

（由 Kumar Aditya 在 [gh-120804](https://github.com/python/cpython/issues/120804) 中贡献。）

-

[`asyncio.get_event_loop()`](https://docs.python.org/zh-cn/3/library/asyncio-eventloop.html#asyncio.get_event_loop) 现在如果没有当前事件循环，会引发 [`RuntimeError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#RuntimeError) 异常，且不再隐式创建事件循环。

（由 Kumar Aditya 在 [gh-126353](https://github.com/python/cpython/issues/126353) 中贡献。）

当前存在几种使用 [`asyncio.get_event_loop()`](https://docs.python.org/zh-cn/3/library/asyncio-eventloop.html#asyncio.get_event_loop) 的模式，其中大多数可替换为 [`asyncio.run()`](https://docs.python.org/zh-cn/3/library/asyncio-runner.html#asyncio.run)。

如果正在运行异步函数，直接使用 [`asyncio.run()`](https://docs.python.org/zh-cn/3/library/asyncio-runner.html#asyncio.run) 即可。

之前：

```
async def main():
    ...

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
finally:
    loop.close()
```

之后：

```
async def main():
    ...

asyncio.run(main())
```

如果需要启动某些持续运行的服务，例如监听套接字的服务器，请使用 [`asyncio.run()`](https://docs.python.org/zh-cn/3/library/asyncio-runner.html#asyncio.run) 配合 [`asyncio.Event`](https://docs.python.org/zh-cn/3/library/asyncio-sync.html#asyncio.Event) 实现。

之前：

```
def start_server(loop): ...

loop = asyncio.get_event_loop()
try:
    start_server(loop)
    loop.run_forever()
finally:
    loop.close()
```

之后：

```
def start_server(loop): ...

async def main():
    start_server(asyncio.get_running_loop())
    await asyncio.Event().wait()

asyncio.run(main())
```

如果需要在事件循环中运行某些任务，同时在其前后执行阻塞代码，请使用 [`asyncio.Runner`](https://docs.python.org/zh-cn/3/library/asyncio-runner.html#asyncio.Runner)。

之前：

```
async def operation_one(): ...
def blocking_code(): ...
async def operation_two(): ...

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(operation_one())
    blocking_code()
    loop.run_until_complete(operation_two())
finally:
    loop.close()
```

之后：

```
async def operation_one(): ...
def blocking_code(): ...
async def operation_two(): ...

with asyncio.Runner() as runner:
    runner.run(operation_one())
    blocking_code()
    runner.run(operation_two())
```

### email

-

移除 [`email.utils.localtime()`](https://docs.python.org/zh-cn/3/library/email.utils.html#email.utils.localtime) 函数的 *isdst* 形参。该参数自 Python 3.12 起已被弃用且一直被忽略。（由 Hugo van Kemenade 在 [gh-118798](https://github.com/python/cpython/issues/118798) 中贡献。）

### importlib.abc

-

移除已弃用的 [`importlib.abc`](https://docs.python.org/zh-cn/3/library/importlib.html#module-importlib.abc) 类：

-

`ResourceReader` (使用 [`TraversableResources`](https://docs.python.org/zh-cn/3/library/importlib.resources.abc.html#importlib.resources.abc.TraversableResources))

-

`Traversable` (使用 [`Traversable`](https://docs.python.org/zh-cn/3/library/importlib.resources.abc.html#importlib.resources.abc.Traversable))

-

`TraversableResources` (使用 [`TraversableResources`](https://docs.python.org/zh-cn/3/library/importlib.resources.abc.html#importlib.resources.abc.TraversableResources))

（由 Jason R. Coombs 和 Hugo van Kemenade 在 [gh-93963](https://github.com/python/cpython/issues/93963) 中贡献。）

### itertools

-

移除 [`itertools`](https://docs.python.org/zh-cn/3/library/itertools.html#module-itertools) 迭代器对复制（copy）、深度复制（deepcopy）和序列化（pickle）操作的支持。自 Python 3.12 起，这些操作已触发 [`DeprecationWarning`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#DeprecationWarning) 警告。（由 Raymond Hettinger 在 [gh-101588](https://github.com/python/cpython/issues/101588) 中贡献。）

### pathlib

-

移除向 [`Path`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.Path) 传递额外关键字参数的支持。在先前版本中，此类参数均会被忽略。（由 Barney Gale 在 [gh-74033](https://github.com/python/cpython/issues/74033) 中贡献。）

-

移除向 [`PurePath.relative_to()`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.PurePath.relative_to) 和 [`is_relative_to()`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.PurePath.is_relative_to) 方法传递额外位置参数的支持。在先前版本中，此类参数会被拼接到 *other* 参数上。（由 Barney Gale 在 [gh-78707](https://github.com/python/cpython/issues/78707) 中贡献。）

### pkgutil

-

移除 `get_loader()` 和 `find_loader()` 函数，这两个函数自 Python 3.12 起已被弃用。（由 Bénédikt Tran 在 [gh-97850](https://github.com/python/cpython/issues/97850) 中贡献。）

### pty

-

移除 `master_open()` 和 `slave_open()` 函数，这两个函数自 Python 3.12 起已被弃用。请改用 [`pty.openpty()`](https://docs.python.org/zh-cn/3/library/pty.html#pty.openpty) 函数。（由 Nikita Sobolev 在 [gh-118824](https://github.com/python/cpython/issues/118824) 中贡献。）

### sqlite3

-

从 [`sqlite3`](https://docs.python.org/zh-cn/3/library/sqlite3.html#module-sqlite3) 模块中移除 `version` 和 `version_info`；请使用 [`sqlite_version`](https://docs.python.org/zh-cn/3/library/sqlite3.html#sqlite3.sqlite_version) 和 [`sqlite_version_info`](https://docs.python.org/zh-cn/3/library/sqlite3.html#sqlite3.sqlite_version_info) 来获取运行时 SQLite 库的实际版本号。（由 Hugo van Kemenade 在 [gh-118924](https://github.com/python/cpython/issues/118924) 中贡献。）

-

现在，使用带具名占位符的形参序列会引发 [`ProgrammingError`](https://docs.python.org/zh-cn/3/library/sqlite3.html#sqlite3.ProgrammingError) 异常，该用法自 Python 3.12 起已被弃用。（由 Erlend E. Aasland 在 [gh-118928](https://github.com/python/cpython/issues/118928) 和 [gh-101693](https://github.com/python/cpython/issues/101693) 中贡献。）

### urllib

-

从 [`urllib.parse`](https://docs.python.org/zh-cn/3/library/urllib.parse.html#module-urllib.parse) 模块中移除 `Quoter` 类，该类自 Python 3.11 起已被弃用。（由 Nikita Sobolev 在 [gh-118827](https://github.com/python/cpython/issues/118827) 中贡献。）

-

从 [`urllib.request`](https://docs.python.org/zh-cn/3/library/urllib.request.html#module-urllib.request) 模块中移除 `URLopener` 和 `FancyURLopener` 类，这两个类自 Python 3.3 起已被弃用。

`myopener.open()` 可以替换为 [`urlopen()`](https://docs.python.org/zh-cn/3/library/urllib.request.html#urllib.request.urlopen)。`myopener.retrieve()` 可以替换为 [`urlretrieve()`](https://docs.python.org/zh-cn/3/library/urllib.request.html#urllib.request.urlretrieve)。对 opener 类的自定义操作可以通过向 [`build_opener()`](https://docs.python.org/zh-cn/3/library/urllib.request.html#urllib.request.build_opener) 传递定制化的处理程序来实现替换。（由 Barney Gale 在 [gh-84850](https://github.com/python/cpython/issues/84850) 中贡献。）

## 弃用

### 新的弃用

-

传入一个复数作为 [`complex()`](https://docs.python.org/zh-cn/3/builtins/functions.html#complex) 构造器中的 *real* 或 *imag* 参数的做法现已被弃用；复数应当仅作为单个位置参数被传入。 （由 Serhiy Storchaka 在 [gh-109218](https://github.com/python/cpython/issues/109218) 中贡献。）

-

[`argparse`](https://docs.python.org/zh-cn/3/library/argparse.html#module-argparse)：

-

将未写入文档的关键字参数 *prefix_chars* 传给 [`add_argument_group()`](https://docs.python.org/zh-cn/3/library/argparse.html#argparse.ArgumentParser.add_argument_group) 方法的做法现已被弃用。 （由 Savannah Ostrowski 在 [gh-125563](https://github.com/python/cpython/issues/125563) 中贡献。）

-

已弃用 [`argparse.FileType`](https://docs.python.org/zh-cn/3/library/argparse.html#argparse.FileType) 类型转换器。 任何涉及资源管理的操作都应在参数解析完成之后在下游进行处理。 （由 Serhiy Storchaka 在 [gh-58032](https://github.com/python/cpython/issues/58032) 中贡献。）

-

[`asyncio`](https://docs.python.org/zh-cn/3/library/asyncio.html#module-asyncio):

-

现在 `asyncio.iscoroutinefunction()` 已被弃用并将在 Python 3.16 中移除；请改用 [`inspect.iscoroutinefunction()`](https://docs.python.org/zh-cn/3/library/inspect.html#inspect.iscoroutinefunction)。 （由李佳昊和 Kumar Aditya 在 [gh-122875](https://github.com/python/cpython/issues/122875) 中贡献。）

-

[`asyncio`](https://docs.python.org/zh-cn/3/library/asyncio.html#module-asyncio) 策略系统已被弃用并将在 Python 3.16 中移除。 具体而言，是弃用了下列类和函数：

-

[`asyncio.AbstractEventLoopPolicy`](https://docs.python.org/zh-cn/3/library/asyncio-policy.html#asyncio.AbstractEventLoopPolicy)

-

[`asyncio.DefaultEventLoopPolicy`](https://docs.python.org/zh-cn/3/library/asyncio-policy.html#asyncio.DefaultEventLoopPolicy)

-

[`asyncio.WindowsSelectorEventLoopPolicy`](https://docs.python.org/zh-cn/3/library/asyncio-policy.html#asyncio.WindowsSelectorEventLoopPolicy)

-

[`asyncio.WindowsProactorEventLoopPolicy`](https://docs.python.org/zh-cn/3/library/asyncio-policy.html#asyncio.WindowsProactorEventLoopPolicy)

-

[`asyncio.get_event_loop_policy()`](https://docs.python.org/zh-cn/3/library/asyncio-policy.html#asyncio.get_event_loop_policy)

-

[`asyncio.set_event_loop_policy()`](https://docs.python.org/zh-cn/3/library/asyncio-policy.html#asyncio.set_event_loop_policy)

用户应当使用 [`asyncio.run()`](https://docs.python.org/zh-cn/3/library/asyncio-runner.html#asyncio.run) 或 [`asyncio.Runner`](https://docs.python.org/zh-cn/3/library/asyncio-runner.html#asyncio.Runner) 并附带 *loop_factory* 参数以使用想要的事件循环实现。

例如，在 Windows 上使用 [`asyncio.SelectorEventLoop`](https://docs.python.org/zh-cn/3/library/asyncio-eventloop.html#asyncio.SelectorEventLoop):

```
import asyncio

async def main():
    ...

asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)
```

（由 Kumar Aditya 在 [gh-127949](https://github.com/python/cpython/issues/127949) 中贡献。）

-

[`codecs`](https://docs.python.org/zh-cn/3/library/codecs.html#module-codecs): [`codecs.open()`](https://docs.python.org/zh-cn/3/library/codecs.html#codecs.open) 函数现已被弃用，并将在未来的 Python 版本中移除。 请改用 [`open()`](https://docs.python.org/zh-cn/3/builtins/functions.html#open)。 （由 Inada Naoki 在 [gh-133036](https://github.com/python/cpython/issues/133036) 中贡献。）

-

[`ctypes`](https://docs.python.org/zh-cn/3/library/ctypes.html#module-ctypes):

-

在非 Windows 平台上，设置 [`Structure._pack_`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.Structure._pack_) 以使用 MSVC 兼容的默认内存布局的做法现已被弃用而应改为设置 [`Structure._layout_`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.Structure._layout_) to `'ms'`，并将在 Python 3.19 中移除。 （由 Petr Viktorin 在 [gh-131747](https://github.com/python/cpython/issues/131747) 中贡献。）

-

在字符串上调用 [`ctypes.POINTER()`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.POINTER) 的做法现已被弃用。 对于自引用的结构体请使用 [不完整类型](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes-incomplete-types)。 此外，内部的 `ctypes._pointer_type_cache` 也已被弃用。 请参阅 `ctypes.POINTER()` 了解更新的实现细节。 （由 Sergey Myrianov 在 [gh-100926](https://github.com/python/cpython/issues/100926) 中贡献。）

-

[`functools`](https://docs.python.org/zh-cn/3/library/functools.html#module-functools): 调用 [`functools.reduce()`](https://docs.python.org/zh-cn/3/library/functools.html#functools.reduce) 的 Python 实现时以关键字参数形式传入 *function* 或 *sequence* 的做法现已被弃用；这两个形参将在 Python 3.16 中改为仅限位置形参。 （由 Kirill Podoprigora 在 [gh-121676](https://github.com/python/cpython/issues/121676) 中贡献。）

-

[`logging`](https://docs.python.org/zh-cn/3/library/logging.html#module-logging): 对使用 *strm* 参数的自定义日志处理器的支持现已被弃用并计划在 Python 3.16 中移除。 请改为定义伤脑筋 *stream* 参数的处理器。 （由 Mariusz Felisiak 在 [gh-115032](https://github.com/python/cpython/issues/115032) 中贡献。）

-

[`mimetypes`](https://docs.python.org/zh-cn/3/library/mimetypes.html#module-mimetypes): 对于 [`mimetypes.MimeTypes.add_type()`](https://docs.python.org/zh-cn/3/library/mimetypes.html#mimetypes.MimeTypes.add_type) 有效的扩展名应为空或者必须以 '.' 打头。 不带点号的扩展名已被弃用并将在 Python 3.16 中引发 [`ValueError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#ValueError)。 （由 Hugo van Kemenade 在 [gh-75223](https://github.com/python/cpython/issues/75223) 中贡献。）

-

`nturl2path`: 该模块现已弃用，请改用 [`urllib.request.url2pathname()`](https://docs.python.org/zh-cn/3/library/urllib.request.html#urllib.request.url2pathname) 和 [`pathname2url()`](https://docs.python.org/zh-cn/3/library/urllib.request.html#urllib.request.pathname2url)。（由 Barney Gale 在 [gh-125866](https://github.com/python/cpython/issues/125866) 中贡献。）

-

[`os`](https://docs.python.org/zh-cn/3/library/os.html#module-os): 现在 [`os.popen()`](https://docs.python.org/zh-cn/3/library/os.html#os.popen) 和 [`os.spawn*`](https://docs.python.org/zh-cn/3/library/os.html#os.spawnl) 函数都被设为 [soft deprecated](https://docs.python.org/zh-cn/3/glossary.html#term-soft-deprecated)。 它们不应再用于编写新的代码。 建议改用 [`subprocess`](https://docs.python.org/zh-cn/3/library/subprocess.html#module-subprocess) 模块。 （由 Victor Stinner 在 [gh-120743](https://github.com/python/cpython/issues/120743) 中贡献。）

-

[`pathlib`](https://docs.python.org/zh-cn/3/library/pathlib.html#module-pathlib): 现在 `pathlib.PurePath.as_uri()` 已被弃用将计划在 Python 3.19 中移除。 请改用 [`pathlib.Path.as_uri()`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.Path.as_uri)。 （由 Barney Gale 在 [gh-123599](https://github.com/python/cpython/issues/123599) 中贡献。）

-

[`pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#module-pdb): 未写入文档的 `pdb.Pdb.curframe_locals` 属性现在成为已弃用的只读特性属性，它将在未来的 Python 版本中被移除。 通过 [**PEP 667**](https://peps.python.org/pep-0667/) 在 Python 3.13 中添加的低开销动态帧局部变量访问机制使得之前存储在该属性中的帧局部变量缓存引用已不再需要。 派生的调试器在 Python 3.13 及更高版本中应当直接访问 `pdb.Pdb.curframe.f_locals`。 （由 Tian Gao 在 [gh-124369](https://github.com/python/cpython/issues/124369) 和 [gh-125951](https://github.com/python/cpython/issues/125951) 中贡献。）

-

[`symtable`](https://docs.python.org/zh-cn/3/library/symtable.html#module-symtable): 由于缺少兴趣 [`symtable.Class.get_methods()`](https://docs.python.org/zh-cn/3/library/symtable.html#symtable.Class.get_methods) 已被弃用，计划在 Python 3.16 中移除。 （由 Bénédikt Tran 在 [gh-119698](https://github.com/python/cpython/issues/119698) 中贡献。）

-

[`tkinter`](https://docs.python.org/zh-cn/3/library/tkinter.html#module-tkinter)：`tkinter.Variable` 的方法 `trace_variable()`、`trace_vdelete()` 和 `trace_vinfo()` 现已被弃用。请改用 `trace_add()`、`trace_remove()` 和 `trace_info()`。（由 Serhiy Storchaka 在 [gh-120220](https://github.com/python/cpython/issues/120220) 中贡献。）

-

[`urllib.parse`](https://docs.python.org/zh-cn/3/library/urllib.parse.html#module-urllib.parse): 在 [`parse_qsl()`](https://docs.python.org/zh-cn/3/library/urllib.parse.html#urllib.parse.parse_qsl) 和 [`parse_qs()`](https://docs.python.org/zh-cn/3/library/urllib.parse.html#urllib.parse.parse_qs) 中接受除空字符串、字节型对象以及 `None` 之外的假值 (如 `0` 和 `[]`) 的做法现已被弃用。 （由 Serhiy Storchaka 在 [gh-116897](https://github.com/python/cpython/issues/116897) 中贡献。）

### 计划在 Python 3.15 中移除

-

导入系统：

-

当设置 [`__spec__.cached`](https://docs.python.org/zh-cn/3/library/importlib.html#importlib.machinery.ModuleSpec.cached) 失败时在模块上设置 [`__cached__`](https://docs.python.org/zh-cn/3/reference/datamodel.html#module.__cached__) 的做法已被弃用。 在 Python 3.15 中，`__cached__` 将不会再被导入系统或标准库纳入考虑。 ([gh-97879](https://github.com/python/cpython/issues/97879))

-

当设备 [`__spec__.parent`](https://docs.python.org/zh-cn/3/library/importlib.html#importlib.machinery.ModuleSpec.parent) 失败时在模块上设置 [`__package__`](https://docs.python.org/zh-cn/3/reference/datamodel.html#module.__package__) 的做法已被弃用。 在 Python 3.15 中，`__package__` 将不会再被导入系统或标准库纳入考虑。 ([gh-97879](https://github.com/python/cpython/issues/97879))

-

[`ctypes`](https://docs.python.org/zh-cn/3/library/ctypes.html#module-ctypes):

-

未写入文档的 `ctypes.SetPointerType()` 函数自 Python 3.13 起已被弃用。

-

[`http.server`](https://docs.python.org/zh-cn/3/library/http.server.html#module-http.server):

-

过时且很少被使用的 [`CGIHTTPRequestHandler`](https://docs.python.org/zh-cn/3/library/http.server.html#http.server.CGIHTTPRequestHandler) 自 Python 3.13 起已被弃用。 不存在直接的替代品。 对于建立带有请求处理器的 Web 服务程序来说 *任何东西* 都比 CGI 要好。

-

用于 **python -m http.server** 命令行界面的 `--cgi` 旗标自 Python 3.13 起已被弃用。

-

[`importlib`](https://docs.python.org/zh-cn/3/library/importlib.html#module-importlib):

-

`load_module()` 方法：改用 `exec_module()`。

-

[`pathlib`](https://docs.python.org/zh-cn/3/library/pathlib.html#module-pathlib):

-

[`PurePath.is_reserved()`](https://docs.python.org/zh-cn/3/library/pathlib.html#pathlib.PurePath.is_reserved) 自 Python 3.13 起已被弃用。 请使用 [`os.path.isreserved()`](https://docs.python.org/zh-cn/3/library/os.path.html#os.path.isreserved) 来检测 Windows 上的保留路径。

-

[`platform`](https://docs.python.org/zh-cn/3/library/platform.html#module-platform):

-

[`java_ver()`](https://docs.python.org/zh-cn/3/library/platform.html#platform.java_ver) 自 Python 3.13 起已被弃用。 此函数仅对 Jython 支持有用，具有令人困惑的 API，并且大部分未经测试。

-

[`sysconfig`](https://docs.python.org/zh-cn/3/library/sysconfig.html#module-sysconfig):

-

[`sysconfig.is_python_build()`](https://docs.python.org/zh-cn/3/library/sysconfig.html#sysconfig.is_python_build) 的 *check_home* 参数自 Python 3.12 起已被弃用。

-

[`threading`](https://docs.python.org/zh-cn/3/library/threading.html#module-threading):

-

[`RLock()`](https://docs.python.org/zh-cn/3/library/threading.html#threading.RLock) will take no arguments in Python 3.15. Passing any arguments has been deprecated since Python 3.14, as the Python version does not permit any arguments, but the C version allows any number of positional or keyword arguments, ignoring every argument.

-

[`types`](https://docs.python.org/zh-cn/3/library/types.html#module-types):

-

[`types.CodeType`](https://docs.python.org/zh-cn/3/library/types.html#types.CodeType): 访问 [`co_lnotab`](https://docs.python.org/zh-cn/3/reference/datamodel.html#codeobject.co_lnotab) 的做法自 3.10 起已根据 [**PEP 626**](https://peps.python.org/pep-0626/) 被弃用并曾计划在 3.12 中移除，但在 3.12 中实际仅设置了 [`DeprecationWarning`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#DeprecationWarning)。 可能会在 3.15 中移除。 （由 Nikita Sobolev 在 [gh-101866](https://github.com/python/cpython/issues/101866) 中贡献。）

-

[`typing`](https://docs.python.org/zh-cn/3/library/typing.html#module-typing):

-

未写入文档的用于创建 [`NamedTuple`](https://docs.python.org/zh-cn/3/library/typing.html#typing.NamedTuple) 类的关键字参数语法 (例如 `Point = NamedTuple("Point", x=int, y=int)`) 自 Python 3.13 起已被弃用。 请改用基于类的语法或函数语法。

-

当使用 [`TypedDict`](https://docs.python.org/zh-cn/3/library/typing.html#typing.TypedDict) 的函数式语法时，不向 *fields* 形参传递值 (`TD = TypedDict("TD")`) 或传递 `None` (`TD = TypedDict("TD", None)`) 的做法自 Python 3.13 起已被弃用。 请改用 `class TD(TypedDict): pass` 或 `TD = TypedDict("TD", {})` 来创建一个零字段的 TypedDict。

-

The [`@typing.no_type_check_decorator`](https://docs.python.org/zh-cn/3/library/typing.html#typing.no_type_check_decorator) decorator function has been deprecated since Python 3.13. After eight years in the [`typing`](https://docs.python.org/zh-cn/3/library/typing.html#module-typing) module, it has yet to be supported by any major type checker.

-

[`wave`](https://docs.python.org/zh-cn/3/library/wave.html#module-wave)：

-

[`Wave_read`](https://docs.python.org/zh-cn/3/library/wave.html#wave.Wave_read) 和 [`Wave_write`](https://docs.python.org/zh-cn/3/library/wave.html#wave.Wave_write) 类的 [`getmark()`](https://docs.python.org/zh-cn/3/library/wave.html#wave.Wave_read.getmark), `setmark()` 和 [`getmarkers()`](https://docs.python.org/zh-cn/3/library/wave.html#wave.Wave_read.getmarkers) 方法自 Python 3.13 起已被弃用。

-

[`zipimport`](https://docs.python.org/zh-cn/3/library/zipimport.html#module-zipimport):

-

[`load_module()`](https://docs.python.org/zh-cn/3/library/zipimport.html#zipimport.zipimporter.load_module) 自 Python 3.10 起已被弃用。请改用 [`exec_module()`](https://docs.python.org/zh-cn/3/library/zipimport.html#zipimport.zipimporter.exec_module) 。 （由李佳昊在 [gh-125746](https://github.com/python/cpython/issues/125746) 中贡献。）

### 计划在 Python 3.16 中移除

-

导入系统：

-

当设置 [`__spec__.loader`](https://docs.python.org/zh-cn/3/library/importlib.html#importlib.machinery.ModuleSpec.loader) 失败时在模块上设置 [`__loader__`](https://docs.python.org/zh-cn/3/reference/datamodel.html#module.__loader__) 的做法已被弃用。 在 Python 3.16 中，`__loader__` 将不会再被设置或是被导入系统或标准库纳入考虑。

-

[`array`](https://docs.python.org/zh-cn/3/library/array.html#module-array):

-

`'u'` 格式代码 (`wchar_t`) 自 Python 3.3 起已在文档中弃用并自 Python 3.13 起在运行时弃用。 对于 Unicode 字符请改用 `'w'` 格式代码 ([`Py_UCS4`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.Py_UCS4))。

-

[`asyncio`](https://docs.python.org/zh-cn/3/library/asyncio.html#module-asyncio):

-

`asyncio.iscoroutinefunction()` 已被弃用并将在 Python 3.16 中移除，请改用 [`inspect.iscoroutinefunction()`](https://docs.python.org/zh-cn/3/library/inspect.html#inspect.iscoroutinefunction)。 （由李佳昊和 Kumar Aditya 在 [gh-122875](https://github.com/python/cpython/issues/122875) 中贡献。）

-

[`asyncio`](https://docs.python.org/zh-cn/3/library/asyncio.html#module-asyncio) 策略系统已被弃用并将在 Python 3.16 中移除。 具体而言，是弃用了下列类和函数：

-

[`asyncio.AbstractEventLoopPolicy`](https://docs.python.org/zh-cn/3/library/asyncio-policy.html#asyncio.AbstractEventLoopPolicy)

-

[`asyncio.DefaultEventLoopPolicy`](https://docs.python.org/zh-cn/3/library/asyncio-policy.html#asyncio.DefaultEventLoopPolicy)

-

[`asyncio.WindowsSelectorEventLoopPolicy`](https://docs.python.org/zh-cn/3/library/asyncio-policy.html#asyncio.WindowsSelectorEventLoopPolicy)

-

[`asyncio.WindowsProactorEventLoopPolicy`](https://docs.python.org/zh-cn/3/library/asyncio-policy.html#asyncio.WindowsProactorEventLoopPolicy)

-

[`asyncio.get_event_loop_policy()`](https://docs.python.org/zh-cn/3/library/asyncio-policy.html#asyncio.get_event_loop_policy)

-

[`asyncio.set_event_loop_policy()`](https://docs.python.org/zh-cn/3/library/asyncio-policy.html#asyncio.set_event_loop_policy)

用户应当使用 [`asyncio.run()`](https://docs.python.org/zh-cn/3/library/asyncio-runner.html#asyncio.run) 或 [`asyncio.Runner`](https://docs.python.org/zh-cn/3/library/asyncio-runner.html#asyncio.Runner) 并附带 *loop_factory* 以使用想要的事件循环实现。

例如，在 Windows 上使用 [`asyncio.SelectorEventLoop`](https://docs.python.org/zh-cn/3/library/asyncio-eventloop.html#asyncio.SelectorEventLoop):

```
import asyncio

async def main():
    ...

asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)
```

（由 Kumar Aditya 在 [gh-127949](https://github.com/python/cpython/issues/127949) 中贡献。）

-

[`builtins`](https://docs.python.org/zh-cn/3/library/builtins.html#module-builtins):

-

对布尔类型 `~True` 或 `~False` 执行按位取反的操作自 Python 3.12 起已被弃用，因为它会产生奇怪和不直观的结果 (`-2` and `-1`)。 请改用 `not x` 来对布尔值执行逻辑否操作。 对于需要对下层整数执行按位取反操作的少数场合，请显式地将其转换为 `int` (`~int(x)`)。

-

[`functools`](https://docs.python.org/zh-cn/3/library/functools.html#module-functools)：

-

调用 [`functools.reduce()`](https://docs.python.org/zh-cn/3/library/functools.html#functools.reduce) 的 Python 实现并传入 *function* 或 *sequence* 作为关键字参数的做法自 Python 3.14 起已被弃用。

-

[`logging`](https://docs.python.org/zh-cn/3/library/logging.html#module-logging)：

使用 *strm* 参数对自定义日志记录处理器提供支持的做法已被弃用并计划在 Python 3.16 中移除。 改为使用 *stream* 参数定义处理器。 （由 Mariusz Felisiak 在 [gh-115032](https://github.com/python/cpython/issues/115032) 中贡献。）

-

[`mimetypes`](https://docs.python.org/zh-cn/3/library/mimetypes.html#module-mimetypes):

-

有效扩展以 ". " 开头或在 [`mimetypes.MimeTypes.add_type()`](https://docs.python.org/zh-cn/3/library/mimetypes.html#mimetypes.MimeTypes.add_type) 为空。 未加点的扩展已弃用，在 Python 3.16 中将引发 [`ValueError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#ValueError)。 （由 Hugo van Kemenade 在 [gh-75223](https://github.com/python/cpython/issues/75223) 中贡献。）

-

[`shutil`](https://docs.python.org/zh-cn/3/library/shutil.html#module-shutil):

-

`ExecError` 异常自 Python 3.14 起已被弃用。 它自 Python 3.4 起就未被 `shutil` 中的任何函数所使用，现在是 [`RuntimeError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#RuntimeError) 的一个别名。

-

[`symtable`](https://docs.python.org/zh-cn/3/library/symtable.html#module-symtable):

-

[`Class.get_methods`](https://docs.python.org/zh-cn/3/library/symtable.html#symtable.Class.get_methods) 方法自 Python 3.14 起被弃用。

-

[`sys`](https://docs.python.org/zh-cn/3/library/sys.html#module-sys):

-

[`_enablelegacywindowsfsencoding()`](https://docs.python.org/zh-cn/3/library/sys.html#sys._enablelegacywindowsfsencoding) 函数自 Python 3.13 起被弃用。 请改用 [`PYTHONLEGACYWINDOWSFSENCODING`](https://docs.python.org/zh-cn/3/using/cmdline.html#envvar-PYTHONLEGACYWINDOWSFSENCODING) 环境变量。

-

[`sysconfig`](https://docs.python.org/zh-cn/3/library/sysconfig.html#module-sysconfig):

-

自Python 3.14 起，`sysconfig.expand_makefile_vars()` 函数已被弃用。请使用 [`sysconfig.get_paths()`](https://docs.python.org/zh-cn/3/library/sysconfig.html#sysconfig.get_paths) 的 `vars` 参数代替。

-

[`tarfile`](https://docs.python.org/zh-cn/3/library/tarfile.html#module-tarfile):

-

未写入文档也未被使用的 `TarFile.tarfile` 属性自 Python 3.13 起被弃用。

### 计划在 Python 3.17 中移除

-

[`collections.abc`](https://docs.python.org/zh-cn/3/library/collections.abc.html#module-collections.abc):

-

[`collections.abc.ByteString`](https://docs.python.org/zh-cn/3/library/collections.abc.html#collections.abc.ByteString) 计划在 Python 3.17 中移除。

使用 `isinstance(obj, collections.abc.Buffer)` 来测试 `obj` 是否在运行时实现了 [缓冲区协议](https://docs.python.org/zh-cn/3/c-api/buffer.html#bufferobjects)。 要用于类型标注，则使用 [`Buffer`](https://docs.python.org/zh-cn/3/library/collections.abc.html#collections.abc.Buffer) 或是显式指明你的代码所支持类型的并集 (例如 `bytes | bytearray | memoryview`)。

`ByteString` 原本是想作为 [`bytes`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#bytes) 和 [`bytearray`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#bytearray) 的超类型的抽象基类提供。 不过，由于 ABC 不能有任何方法，知道一个对象是 `ByteString` 的实例并不能真正告诉你有关该对象的任何有用信息。 其他常见缓冲区类型如 [`memoryview`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#memoryview) 同样不能被当作是 `ByteString` 的子类型（无论是在运行时还是对于静态类型检查器）。

请参阅 [**PEP 688**](https://peps.python.org/pep-0688/#current-options) 了解详情。 （由 Shantanu Jain 在 [gh-91896](https://github.com/python/cpython/issues/91896) 中贡献。）

-

[`typing`](https://docs.python.org/zh-cn/3/library/typing.html#module-typing):

-

在 Python 3.14 之前，旧式的联合是通过私有类 `typing._UnionGenericAlias` 实现的。实现已不再需要该类，但为向后兼容性保留了该类，并计划在 Python 3.17 中删除。 用户应使用记录在案的内省助手函数，如 [`typing.get_origin()`](https://docs.python.org/zh-cn/3/library/typing.html#typing.get_origin) 和 [`typing.get_args()`](https://docs.python.org/zh-cn/3/library/typing.html#typing.get_args)，而不是依赖于私有的实现细节。

-

[`typing.ByteString`](https://docs.python.org/zh-cn/3/library/typing.html#typing.ByteString) 自 Python 3.9 起已被弃用，计划在 Python 3.17 中移除。

使用 `isinstance(obj, collections.abc.Buffer)` 来测试 `obj` 是否在运行时实现了 [缓冲区协议](https://docs.python.org/zh-cn/3/c-api/buffer.html#bufferobjects)。 要用于类型标注，则使用 [`Buffer`](https://docs.python.org/zh-cn/3/library/collections.abc.html#collections.abc.Buffer) 或是显式指明你的代码所支持类型的并集 (例如 `bytes | bytearray | memoryview`)。

`ByteString` 原本是想作为 [`bytes`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#bytes) 和 [`bytearray`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#bytearray) 的超类型的抽象基类提供。 不过，由于 ABC 不能有任何方法，知道一个对象是 `ByteString` 的实例并不能真正告诉你有关该对象的任何有用信息。 其他常见缓冲区类型如 [`memoryview`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#memoryview) 同样不能被当作是 `ByteString` 的子类型（无论是在运行时还是对于静态类型检查器）。

请参阅 [**PEP 688**](https://peps.python.org/pep-0688/#current-options) 了解详情。 （由 Shantanu Jain 在 [gh-91896](https://github.com/python/cpython/issues/91896) 中贡献。）

### 计划在 Python 3.18 中移除

-

[`decimal`](https://docs.python.org/zh-cn/3/library/decimal.html#module-decimal):

-

非标准且未写入文档的 [`Decimal`](https://docs.python.org/zh-cn/3/library/decimal.html#decimal.Decimal) 格式说明符 `'N'`，它仅在 `decimal` 模块的 C 实现中受到支持，自 Python 3.13 起已被弃用。 （由 Serhiy Storchaka 在 [gh-89902](https://github.com/python/cpython/issues/89902) 中贡献。）

### 计划在 Python 3.19 中移除

-

[`ctypes`](https://docs.python.org/zh-cn/3/library/ctypes.html#module-ctypes):

-

在非 Windows 平台上，通过设置 [`_pack_`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.Structure._pack_) 而非 [`_layout_`](https://docs.python.org/zh-cn/3/library/ctypes.html#ctypes.Structure._layout_) ，隐式切换到与 MSVC 兼容的结构布局。

### 计划在未来版本中移除

以下API将会被移除，尽管具体时间还未确定。

-

[`argparse`](https://docs.python.org/zh-cn/3/library/argparse.html#module-argparse)：

-

嵌套参数组和嵌套互斥组已被弃用 。

-

将未写入文档的关键字参数 *prefix_chars* 传递给 [`add_argument_group()`](https://docs.python.org/zh-cn/3/library/argparse.html#argparse.ArgumentParser.add_argument_group) 的做法现在已被弃用。

-

[`argparse.FileType`](https://docs.python.org/zh-cn/3/library/argparse.html#argparse.FileType) 类型转换器已弃用 。

-

[`builtins`](https://docs.python.org/zh-cn/3/library/builtins.html#module-builtins):

-

生成器: `throw(type, exc, tb)` 和 `athrow(type, exc, tb)` 签名已被弃用：请改用 `throw(exc)` 和 `athrow(exc)`，即单参数签名。

-

目前 Python 接受数字类字面值后面紧跟关键字的写法，例如 `0in x`, `1or x`, `0if 1else 2`。它允许像 `[0x1for x in y]` 这样令人困惑且有歧义的表达式 (它可以被解读为 `[0x1 for x in y]` 或者 `[0x1f or x in y]`)。如果数字类字面值后面紧跟关键字 [`and`](https://docs.python.org/zh-cn/3/reference/expressions.html#and), [`else`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#else), [`for`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#for), [`if`](https://docs.
python.org/zh-cn/3/reference/compound_stmts.html#if), [`in`](https://docs.python.org/zh-cn/3/reference/expressions.html#in), [`is`](https://docs.python.org/zh-cn/3/reference/expressions.html#is) 和 [`or`](https://docs.python.org/zh-cn/3/reference/expressions.html#or) 中的一个将会引发语法警告。在未来的版本中它将改为语法错误。([gh-87999](https://github.com/python/cpython/issues/87999))

-

对 `__index__()` 和 `__int__()` 方法返回非 int 类型的支持：将要求这些方法必须返回 [`int`](https://docs.python.org/zh-cn/3/builtins/functions.html#int) 的子类的实例。

-

对 `__float__()` 方法返回 [`float`](https://docs.python.org/zh-cn/3/builtins/functions.html#float) 的子类的支持：将要求这些方法必须返回 `float` 的实例。

-

对 `__complex__()` 方法返回 [`complex`](https://docs.python.org/zh-cn/3/builtins/functions.html#complex) 的子类的支持：将要求这些方法必须返回 `complex` 的实例。

-

传入一个复数作为 [`complex()`](https://docs.python.org/zh-cn/3/builtins/functions.html#complex) 构造器中的 *real* 或 *imag* 参数的做法现在已被弃用；它应当仅作为单个位置参数被传入。 （由 Serhiy Storchaka 在 [gh-109218](https://github.com/python/cpython/issues/109218) 中贡献。）.)

-

[`calendar`](https://docs.python.org/zh-cn/3/library/calendar.html#module-calendar): `calendar.January` 和 `calendar.February` 常量已被弃用并由 [`calendar.JANUARY`](https://docs.python.org/zh-cn/3/library/calendar.html#calendar.JANUARY) 和 [`calendar.FEBRUARY`](https://docs.python.org/zh-cn/3/library/calendar.html#calendar.FEBRUARY) 替代。 （由 Prince Roshan 在 [gh-103636](https://github.com/python/cpython/issues/103636) 中贡献。）

-

[`codecs`](https://docs.python.org/zh-cn/3/library/codecs.html#module-codecs)：[`codecs.open()`](https://docs.python.org/zh-cn/3/library/codecs.html#codecs.open) 请改用 [`open()`](https://docs.python.org/zh-cn/3/builtins/functions.html#open) 。 ([gh-133038](https://github.com/python/cpython/issues/133038))

-

[`codeobject.co_lnotab`](https://docs.python.org/zh-cn/3/reference/datamodel.html#codeobject.co_lnotab): 改用 [`codeobject.co_lines()`](https://docs.python.org/zh-cn/3/reference/datamodel.html#codeobject.co_lines) 方法。

-

[`datetime`](https://docs.python.org/zh-cn/3/library/datetime.html#module-datetime):

-

[`utcnow()`](https://docs.python.org/zh-cn/3/library/datetime.html#datetime.datetime.utcnow): 使用 `datetime.datetime.now(tz=datetime.UTC)`。

-

[`utcfromtimestamp()`](https://docs.python.org/zh-cn/3/library/datetime.html#datetime.datetime.utcfromtimestamp): 使用 `datetime.datetime.fromtimestamp(timestamp, tz=datetime.UTC)`。

-

[`gettext`](https://docs.python.org/zh-cn/3/library/gettext.html#module-gettext): 复数值必须是一个整数。

-

[`importlib`](https://docs.python.org/zh-cn/3/library/importlib.html#module-importlib):

-

[`cache_from_source()`](https://docs.python.org/zh-cn/3/library/importlib.html#importlib.util.cache_from_source) *debug_override* 形参已被弃用：改用 *optimization* 形参。

-

[`importlib.metadata`](https://docs.python.org/zh-cn/3/library/importlib.metadata.html#module-importlib.metadata):

-

`EntryPoints` 元组接口。

-

返回值中隐式的 `None`。

-

[`logging`](https://docs.python.org/zh-cn/3/library/logging.html#module-logging): `warn()` 方法自 Python 3.3 起已被弃用，请改用 [`warning()`](https://docs.python.org/zh-cn/3/library/logging.html#logging.warning)。

-

[`mailbox`](https://docs.python.org/zh-cn/3/library/mailbox.html#module-mailbox): 对 StringIO 输入和文本模式的使用已被弃用，改用 BytesIO 和二进制模式。

-

[`os`](https://docs.python.org/zh-cn/3/library/os.html#module-os): 在多线程的进程中调用 [`os.register_at_fork()`](https://docs.python.org/zh-cn/3/library/os.html#os.register_at_fork)。

-

`pydoc.ErrorDuringImport`: 使用元组值作为 *exc_info* 形参的做法已被弃用，应使用异常实例。

-

[`re`](https://docs.python.org/zh-cn/3/library/re.html#module-re): 现在对于正则表达式中的数字分组引用和分组名称将应用更严格的规则。 现在只接受 ASCII 数字序列作为数字引用。 字节串模式和替换字符串中的分组名称现在只能包含 ASCII 字母和数字以及下划线。 （由 Serhiy Storchaka 在 [gh-91760](https://github.com/python/cpython/issues/91760) 中贡献。）

-

`sre_compile`, `sre_constants` 和 `sre_parse` 模块。

-

[`shutil`](https://docs.python.org/zh-cn/3/library/shutil.html#module-shutil): [`rmtree()`](https://docs.python.org/zh-cn/3/library/shutil.html#shutil.rmtree) 的 *onerror* 形参在 Python 3.12 中已被弃用；请改用 *onexc* 形参。

-

[`ssl`](https://docs.python.org/zh-cn/3/library/ssl.html#module-ssl) 选项和协议：

-

[`ssl.SSLContext`](https://docs.python.org/zh-cn/3/library/ssl.html#ssl.SSLContext) 不带 protocol 参数的做法已被弃用。

-

[`ssl.SSLContext`](https://docs.python.org/zh-cn/3/library/ssl.html#ssl.SSLContext): [`set_npn_protocols()`](https://docs.python.org/zh-cn/3/library/ssl.html#ssl.SSLContext.set_npn_protocols) 和 `selected_npn_protocol()` 已被弃用：请改用 ALPN。

-

`ssl.OP_NO_SSL*` 选项

-

`ssl.OP_NO_TLS*` 选项

-

`ssl.PROTOCOL_SSLv3`

-

`ssl.PROTOCOL_TLS`

-

`ssl.PROTOCOL_TLSv1`

-

`ssl.PROTOCOL_TLSv1_1`

-

`ssl.PROTOCOL_TLSv1_2`

-

`ssl.TLSVersion.SSLv3`

-

`ssl.TLSVersion.TLSv1`

-

`ssl.TLSVersion.TLSv1_1`

-

[`threading`](https://docs.python.org/zh-cn/3/library/threading.html#module-threading) 的方法：

-

`threading.Condition.notifyAll()`: 使用 [`notify_all()`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Condition.notify_all)。

-

`threading.Event.isSet()`: 使用 [`is_set()`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Event.is_set)。

-

`threading.Thread.isDaemon()`, [`threading.Thread.setDaemon()`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Thread.setDaemon): 使用 [`threading.Thread.daemon`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Thread.daemon) 属性。

-

`threading.Thread.getName()`, [`threading.Thread.setName()`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Thread.setName): 使用 [`threading.Thread.name`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Thread.name) 属性。

-

`threading.currentThread()`: 使用 [`threading.current_thread()`](https://docs.python.org/zh-cn/3/library/threading.html#threading.current_thread)。

-

`threading.activeCount()`: 使用 [`threading.active_count()`](https://docs.python.org/zh-cn/3/library/threading.html#threading.active_count)。

-

[`typing.Text`](https://docs.python.org/zh-cn/3/library/typing.html#typing.Text) ([gh-92332](https://github.com/python/cpython/issues/92332))。

-

内部类 `typing._UnionGenericAlias` 不再用于实现 [`typing.Union`](https://docs.python.org/zh-cn/3/library/typing.html#typing.Union)。为了保护使用该私有类的用户的兼容性 ，将至少在 Python 3.17 之前提供兼容性。 （由 Jelle Zijlstra 在 [gh-105499](https://github.com/python/cpython/issues/105499) 中贡献。）

-

[`unittest.IsolatedAsyncioTestCase`](https://docs.python.org/zh-cn/3/library/unittest.html#unittest.IsolatedAsyncioTestCase): 从测试用例返回不为 `None` 的值的做法已被弃用。

-

[`urllib.parse`](https://docs.python.org/zh-cn/3/library/urllib.parse.html#module-urllib.parse) 函数已被弃用：改用 [`urlparse()`](https://docs.python.org/zh-cn/3/library/urllib.parse.html#urllib.parse.urlparse)

-

`splitattr()`

-

`splithost()`

-

`splitnport()`

-

`splitpasswd()`

-

`splitport()`

-

`splitquery()`

-

`splittag()`

-

`splittype()`

-

`splituser()`

-

`splitvalue()`

-

`to_bytes()`

-

[`wsgiref`](https://docs.python.org/zh-cn/3/library/wsgiref.html#module-wsgiref): `SimpleHandler.stdout.write()` 不应执行部分写入。

-

[`xml.etree.ElementTree`](https://docs.python.org/zh-cn/3/library/xml.etree.elementtree.html#module-xml.etree.ElementTree): 对 [`Element`](https://docs.python.org/zh-cn/3/library/xml.etree.elementtree.html#xml.etree.ElementTree.Element) 的真值测试已被弃用。 在未来的发布版中它将始终返回 `True`。 建议改用显式的 `len(elem)` 或 `elem is not None` 测试。

-

[`sys._clear_type_cache()`](https://docs.python.org/zh-cn/3/library/sys.html#sys._clear_type_cache) 已弃用，请改用 [`sys._clear_internal_caches()`](https://docs.python.org/zh-cn/3/library/sys.html#sys._clear_internal_caches) 。

## CPython 字节码的改变

-

将操作码 `BINARY_SUBSCR` 替换为附带操作数 `NB_SUBSCR` 的 [`BINARY_OP`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-BINARY_OP) 操作码。 （由 Irit Katriel 在 [gh-100239](https://github.com/python/cpython/issues/100239) 中贡献。）

-

增加 [`BUILD_INTERPOLATION`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-BUILD_INTERPOLATION) 和 [`BUILD_TEMPLATE`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-BUILD_TEMPLATE) 操作码分别用于构造新的 [`Interpolation`](https://docs.python.org/zh-cn/3/library/string.templatelib.html#string.templatelib.Interpolation) 和 [`Template`](https://docs.python.org/zh-cn/3/library/string.templatelib.html#string.templatelib.Template) 实例。 （由 Lysandros Nikolaou 等人在 [gh-132661](https://github.com/python/cpython/issues/132661) 中贡献；另请参阅 PEP 750: Template strings。）

-

移除了 `BUILD_CONST_KEY_MAP` 操作码。 改用 [`BUILD_MAP`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-BUILD_MAP)。 （由 Mark Shannon 在 [gh-122160](https://github.com/python/cpython/issues/122160) 中贡献。）

-

将 `LOAD_ASSERTION_ERROR` 操作码替换为 [`LOAD_COMMON_CONSTANT`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-LOAD_COMMON_CONSTANT) 并添加对载入 [`NotImplementedError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#NotImplementedError) 的支持。

-

增加 [`LOAD_FAST_BORROW`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-LOAD_FAST_BORROW) 和 [`LOAD_FAST_BORROW_LOAD_FAST_BORROW`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-LOAD_FAST_BORROW_LOAD_FAST_BORROW) 操作码用于在解释器能证明帧内引用的生命期长于载入到栈的引用时减少引用计数开销。 （由 Matt Page 在 [gh-130704](https://github.com/python/cpython/issues/130704) 中贡献。）.)

-

增加 [`LOAD_SMALL_INT`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-LOAD_SMALL_INT) 操作码，它会将一个等于 `oparg` 的小整数推入栈。 `RETURN_CONST` 操作码已被移除因为它已不再被使用。 （由 Mark Shannon 在 [gh-125837](https://github.com/python/cpython/issues/125837) 中贡献。）.)

-

新增 [`LOAD_SPECIAL`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-LOAD_SPECIAL) 指令。 为 [`with`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#with) 和 [`async with`](https://docs.python.org/zh-cn/3/reference/compound_stmts.html#async-with) 语句生成代码将使用此新指令。 移除了 `BEFORE_WITH` 和 `BEFORE_ASYNC_WITH` 指令。 （由 Mark Shannon 在 [gh-120507](https://github.com/python/cpython/issues/120507) 中贡献。）

-

增加 [`POP_ITER`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-POP_ITER) 指令以支持 '虚拟' 迭代器。 （由 Mark Shannon 在 [gh-132554](https://github.com/python/cpython/issues/132554) 中贡献。）

### 伪指令

-

增加 `ANNOTATIONS_PLACEHOLDER` 伪指令以支持部分执行的使用 标注迟延求值 的模块级标注。 （由 Jelle Zijlstra 在 [gh-130907](https://github.com/python/cpython/issues/130907) 中贡献。）

-

增加 `BINARY_OP_EXTEND` 伪指令，它会执行从内联缓存中访问的一对函数（守卫函数和特化函数）。 （由 Irit Katriel 在 [gh-100239](https://github.com/python/cpython/issues/100239) 中贡献。）

-

增加 [`CALL_KW`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-CALL_KW) 的三个特化版本； `CALL_KW_PY` 用于对 Python 函数的调用，`CALL_KW_BOUND_METHOD` 用于对绑定方法的调用，而 `CALL_KW_NON_PY` 用于所有其他调用。 （由 Mark Shannon 在 [gh-118093](https://github.com/python/cpython/issues/118093) 中贡献。）

-

增加 [`JUMP_IF_TRUE`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-JUMP_IF_TRUE) 和 [`JUMP_IF_FALSE`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-JUMP_IF_FALSE) 伪指令，即不影响栈的条件跳转。 由序列 `COPY 1`, `TO_BOOL`, `POP_JUMP_IF_TRUE/FALSE` 替换。 （由 Irit Katriel 在 [gh-124285](https://github.com/python/cpython/issues/124285) 中贡献。）

-

增加 `LOAD_CONST_MORTAL` 伪指令。 （由 Mark Shannon 在 [gh-128685](https://github.com/python/cpython/issues/128685) 中贡献。）

-

增加 [`LOAD_CONST_IMMORTAL`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-LOAD_CONST_IMMORTAL) 伪指令，它会执行与 `LOAD_CONST` 相同的操作，但对永生对象更有效率。 （由 Mark Shannon 在 [gh-125837](https://github.com/python/cpython/issues/125837) 中贡献。）

-

增加 [`NOT_TAKEN`](https://docs.python.org/zh-cn/3/library/dis.html#opcode-NOT_TAKEN) 伪指令，由 [`sys.monitoring`](https://docs.python.org/zh-cn/3/library/sys.monitoring.html#module-sys.monitoring) 用来记录分支事件 (如 [`BRANCH_LEFT`](https://docs.python.org/zh-cn/3/library/sys.monitoring.html#monitoring-event-BRANCH_LEFT))。 （由 Mark Shannon 在 [gh-122548](https://github.com/python/cpython/issues/122548) 中贡献。）

## C API 的变化

### Python 配置 C API

新增 [PyInitConfig C API](https://docs.python.org/zh-cn/3/c-api/init_config.html#pyinitconfig-api) 用于配置 Python 初始化过程，无需依赖 C 结构体，同时支持未来进行 ABI 兼容性变更。

通过添加 [`PyInitConfig_AddModule()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_AddModule) 来完成 [**PEP 587**](https://peps.python.org/pep-0587/) [PyConfig C API](https://docs.python.org/zh-cn/3/c-api/init_config.html#pyconfig-api)，它可被用于添加内置扩展模块；该特性此前被称为 "inittab"。

新增 [`PyConfig_Get()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 和 [`PyConfig_Set()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Set) 函数，用于获取和设置当前运行时配置。

[**PEP 587**](https://peps.python.org/pep-0587/) 'Python 初始化配置' 统一了所有配置 Python 初始化的方式。 这个 PEP 还将 Python 的预初始化和初始化配置整合至单个 API 中。 此外，这个 PEP 只提供了单个选项用于嵌入 Python，而不是有 'Python' 和 '隔离' 两种选项 (PEP 587)，以进一步简化 API。

较低层级的 PEP 587 PyConfig API 仍然保留用于需要有与 CPython 实现细节较高耦合度的使用场景（如模拟 CPython 的 CLI 的完整功能，包括其配置机制）。

（由 Victor Stinner 在 [gh-107954](https://github.com/python/cpython/issues/107954) 中贡献。）

参见

[**PEP 741**](https://peps.python.org/pep-0741/) 和 [**PEP 587**](https://peps.python.org/pep-0587/)

### C API 中的新特性

-

增加 [`Py_PACK_VERSION()`](https://docs.python.org/zh-cn/3/c-api/apiabiversion.html#c.Py_PACK_VERSION) 和 [`Py_PACK_FULL_VERSION()`](https://docs.python.org/zh-cn/3/c-api/apiabiversion.html#c.Py_PACK_FULL_VERSION)，两个用于对 Python 版本号进行位打包操作的新宏。 这在比较 [`Py_Version`](https://docs.python.org/zh-cn/3/c-api/apiabiversion.html#c.Py_Version) 或 [`PY_VERSION_HEX`](https://docs.python.org/zh-cn/3/c-api/apiabiversion.html#c.PY_VERSION_HEX) 时很有用处。 （由 Petr Viktorin 在 [gh-128629](https://github.com/python/cpython/issues/128629) 中贡献。）

-

新增 [`PyBytes_Join(sep, iterable)`](https://docs.python.org/zh-cn/3/c-api/bytes.html#c.PyBytes_Join) 函数，其功能类似于Python中的 `sep.join(iterable)` 操作。（由Victor Stinner在 [gh-121645](https://github.com/python/cpython/issues/121645) 中贡献。）

-

增加了用于操作当前运行时 Python 解释器的配置的函数 (PEP 741: Python configuration C API):

-

[`PyConfig_Get()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get)

-

[`PyConfig_GetInt()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_GetInt)

-

[`PyConfig_Set()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Set)

-

[`PyConfig_Names()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Names)

（由 Victor Stinner 在 [gh-107954](https://github.com/python/cpython/issues/107954) 中贡献。）

-

增加了用于配置 Python 初始化的函数 (PEP 741: Python configuration C API):

-

[`Py_InitializeFromInitConfig()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.Py_InitializeFromInitConfig)

-

[`PyInitConfig_AddModule()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_AddModule)

-

[`PyInitConfig_Create()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_Create)

-

[`PyInitConfig_Free()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_Free)

-

[`PyInitConfig_FreeStrList()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_FreeStrList)

-

[`PyInitConfig_GetError()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_GetError)

-

[`PyInitConfig_GetExitCode()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_GetExitCode)

-

[`PyInitConfig_GetInt()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_GetInt)

-

[`PyInitConfig_GetStr()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_GetStr)

-

[`PyInitConfig_GetStrList()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_GetStrList)

-

[`PyInitConfig_HasOption()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_HasOption)

-

[`PyInitConfig_SetInt()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_SetInt)

-

[`PyInitConfig_SetStr()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_SetStr)

-

[`PyInitConfig_SetStrList()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyInitConfig_SetStrList)

（由 Victor Stinner 在 [gh-107954](https://github.com/python/cpython/issues/107954) 中贡献。）

-

增加 [`Py_fopen()`](https://docs.python.org/zh-cn/3/c-api/sys.html#c.Py_fopen) 函数用于打开文件。 该函数功能类似于标准 C `fopen()` 函数，但它接受一个 Python 对象作为 *path* 形参并会在出错时设置异常。 对应的新增函数 [`Py_fclose()`](https://docs.python.org/zh-cn/3/c-api/sys.html#c.Py_fclose) 函数应当用来关闭文件。 （由 Victor Stinner 在 [gh-127350](https://github.com/python/cpython/issues/127350) 中贡献。）

-

新增 [`Py_HashBuffer()`](https://docs.python.org/zh-cn/3/c-api/hash.html#c.Py_HashBuffer) 函数用于计算并返回缓冲区的哈希值。（由 Antoine Pitrou 和 Victor Stinner 在 [gh-122854](https://github.com/python/cpython/issues/122854) 中贡献。）

-

新增 [`PyImport_ImportModuleAttr()`](https://docs.python.org/zh-cn/3/c-api/import.html#c.PyImport_ImportModuleAttr) 和 [`PyImport_ImportModuleAttrString()`](https://docs.python.org/zh-cn/3/c-api/import.html#c.PyImport_ImportModuleAttrString) 辅助函数，用于导入模块并获取该模块的属性。（由 Victor Stinner 在 [gh-128911](https://github.com/python/cpython/issues/128911) 中贡献。）

-

新增 [`PyIter_NextItem()`](https://docs.python.org/zh-cn/3/c-api/iter.html#c.PyIter_NextItem) 函数以替代返回值含义模糊的 [`PyIter_Next()`](https://docs.python.org/zh-cn/3/c-api/iter.html#c.PyIter_Next) 函数。（由 Irit Katriel 和 Erlend Aasland 在 [gh-105201](https://github.com/python/cpython/issues/105201) 中贡献。）

-

新增 [`PyLong_GetSign()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_GetSign) 函数用于获取 [`int`](https://docs.python.org/zh-cn/3/builtins/functions.html#int) 对象的符号位。（由 Sergey B Kirpichev 在 [gh-116560](https://github.com/python/cpython/issues/116560) 中贡献。）

-

新增 [`PyLong_IsPositive()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_IsPositive)、[`PyLong_IsNegative()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_IsNegative) 和 [`PyLong_IsZero()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_IsZero) 三个函数，分别用于检查 [`PyLongObject`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLongObject) 是否为正数、负数或零。（由 James Roy 和 Sergey B Kirpichev 在 [gh-126061](https://github.com/python/cpython/issues/126061) 中贡献。）

-

新增用于在 C `<stdint.h>` 数字类型与 Python [`int`](https://docs.python.org/zh-cn/3/builtins/functions.html#int) 对象之间进行转换的新函数：

-

[`PyLong_AsInt32()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_AsInt32)

-

[`PyLong_AsInt64()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_AsInt64)

-

[`PyLong_AsUInt32()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_AsUInt32)

-

[`PyLong_AsUInt64()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_AsUInt64)

-

[`PyLong_FromInt32()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_FromInt32)

-

[`PyLong_FromInt64()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_FromInt64)

-

[`PyLong_FromUInt32()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_FromUInt32)

-

[`PyLong_FromUInt64()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_FromUInt64)

（由 Victor Stinner 在 [gh-120389](https://github.com/python/cpython/issues/120389) 中贡献。）

-

新增用于 Python [`int`](https://docs.python.org/zh-cn/3/builtins/functions.html#int) 对象的导入导出 API (参见 [**PEP 757**](https://peps.python.org/pep-0757/))：

-

[`PyLong_GetNativeLayout()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_GetNativeLayout)

-

[`PyLong_Export()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_Export)

-

[`PyLong_FreeExport()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_FreeExport)

-

[`PyLongWriter_Create()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLongWriter_Create)

-

[`PyLongWriter_Finish()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLongWriter_Finish)

-

[`PyLongWriter_Discard()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLongWriter_Discard)

（由 Sergey B Kirpichev 和 Victor Stinner 在 [gh-102471](https://github.com/python/cpython/issues/102471) 中贡献。）

-

增加 [`PyMonitoring_FireBranchLeftEvent()`](https://docs.python.org/zh-cn/3/c-api/monitoring.html#c.PyMonitoring_FireBranchLeftEvent) 和 [`PyMonitoring_FireBranchRightEvent()`](https://docs.python.org/zh-cn/3/c-api/monitoring.html#c.PyMonitoring_FireBranchRightEvent) 分别用于生成 [`BRANCH_LEFT`](https://docs.python.org/zh-cn/3/library/sys.monitoring.html#monitoring-event-BRANCH_LEFT) 和 [`BRANCH_RIGHT`](https://docs.python.org/zh-cn/3/library/sys.monitoring.html#monitoring-event-BRANCH_RIGHT) 事件。 （由 Mark Shannon 在 [gh-122548](https://github.com/python/cpython/issues/122548) 中贡献。）

-

新增 [`PyType_Freeze()`](https://docs.python.org/zh-cn/3/c-api/type.html#c.PyType_Freeze) 函数用于将类型设为不可变。（由 Victor Stinner 在 [gh-121654](https://github.com/python/cpython/issues/121654) 中贡献。）

-

增加 [`PyType_GetBaseByToken()`](https://docs.python.org/zh-cn/3/c-api/type.html#c.PyType_GetBaseByToken) 和 [`Py_tp_token`](https://docs.python.org/zh-cn/3/c-api/type.html#c.Py_tp_token) 槽位用于简化超类的标识，该特性尝试解决在 [**PEP 630**](https://peps.python.org/pep-0630/#type-checking) 中提到的类型检查问题。 （在 [gh-124153](https://github.com/python/cpython/issues/124153) 中贡献。）

-

新增 [`PyUnicode_Equal()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicode_Equal) 函数用于测试两个字符串是否相等。 此函数也被加入到受限 C API 中。 （由 Victor Stinner 在 [gh-124502](https://github.com/python/cpython/issues/124502) 中贡献。）

-

新增 [`PyUnicodeWriter`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter) API 用于创建 Python [`str`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#str) 对象，具有下列函数：

-

[`PyUnicodeWriter_Create()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_Create)

-

[`PyUnicodeWriter_DecodeUTF8Stateful()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_DecodeUTF8Stateful)

-

[`PyUnicodeWriter_Discard()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_Discard)

-

[`PyUnicodeWriter_Finish()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_Finish)

-

[`PyUnicodeWriter_Format()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_Format)

-

[`PyUnicodeWriter_WriteASCII()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteASCII)

-

[`PyUnicodeWriter_WriteChar()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteChar)

-

[`PyUnicodeWriter_WriteRepr()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteRepr)

-

[`PyUnicodeWriter_WriteStr()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteStr)

-

[`PyUnicodeWriter_WriteSubstring()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteSubstring)

-

[`PyUnicodeWriter_WriteUCS4()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteUCS4)

-

[`PyUnicodeWriter_WriteUTF8()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteUTF8)

-

[`PyUnicodeWriter_WriteWideChar()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteWideChar)

（由 Victor Stinner 在 [gh-119182](https://github.com/python/cpython/issues/119182) 中贡献。）

-

在 [`PyArg_ParseTuple()`](https://docs.python.org/zh-cn/3/c-api/arg.html#c.PyArg_ParseTuple) 及相关函数中，`k` 和 `K` 格式现在会优先使用 [`__index__()`](https://docs.python.org/zh-cn/3/reference/datamodel.html#object.__index__) 方法（如果可用），与其他整数格式的处理方式保持一致。（由 Serhiy Storchaka 在 [gh-112068](https://github.com/python/cpython/issues/112068) 中贡献。）

-

在 [`Py_BuildValue()`](https://docs.python.org/zh-cn/3/c-api/arg.html#c.Py_BuildValue) 中增加对新的 `p` 格式单元的支持，它可根据 C 整数产生 Python [`bool`](https://docs.python.org/zh-cn/3/builtins/functions.html#bool) 对象。 （由 Pablo Galindo 在 [bpo-45325](https://bugs.python.org/issue?@action=redirect&bpo=45325) 中贡献。）.)

-

增加 [`PyUnstable_IsImmortal()`](https://docs.python.org/zh-cn/3/c-api/object.html#c.PyUnstable_IsImmortal) 以确定一个对象是否为 [immortal](https://docs.python.org/zh-cn/3/glossary.html#term-immortal)，用于调试目的。 （由 Peter Bierma 在 [gh-128509](https://github.com/python/cpython/issues/128509) 中贡献。）

-

新增 [`PyUnstable_Object_EnableDeferredRefcount()`](https://docs.python.org/zh-cn/3/c-api/object.html#c.PyUnstable_Object_EnableDeferredRefcount) 函数用于启用延迟引用计数功能，该功能如 [**PEP 703**](https://peps.python.org/pep-0703/) 所述。

-

新增 [`PyUnstable_Object_IsUniquelyReferenced()`](https://docs.python.org/zh-cn/3/c-api/object.html#c.PyUnstable_Object_IsUniquelyReferenced) 函数，作为 [自由线程](https://docs.python.org/zh-cn/3/glossary.html#term-free-threading) 构建环境下 `Py_REFCNT(op) == 1` 的替代方案。（由 Peter Bierma 在 [gh-133140](https://github.com/python/cpython/issues/133140) 中贡献）

-

增加 [`PyUnstable_Object_IsUniqueReferencedTemporary()`](https://docs.python.org/zh-cn/3/c-api/object.html#c.PyUnstable_Object_IsUniqueReferencedTemporary) 用于确定一个对象是否为解释器操作数栈上的唯一临时对象。 该函数在某些情况下可被用作通过检查 [`Py_REFCNT()`](https://docs.python.org/zh-cn/3/c-api/refcounting.html#c.Py_REFCNT) 是否为 `1` 来判断作为参数传给 C API 函数的 Python 对象的替代方案。 （由 Sam Gross 在 [gh-133164](https://github.com/python/cpython/issues/133164) 中贡献。）

### 受限 C API 的变化

-

在受限 C API 3.14 及更新版本中，[`Py_TYPE()`](https://docs.python.org/zh-cn/3/c-api/structures.html#c.Py_TYPE) 和 [`Py_REFCNT()`](https://docs.python.org/zh-cn/3/c-api/refcounting.html#c.Py_REFCNT) 现在被实现为不透明函数来隐藏实现细节。 （由 Victor Stinner 在 [gh-120600](https://github.com/python/cpython/issues/120600) 和 [gh-124127](https://github.com/python/cpython/issues/124127) 中贡献。）

-

从受限 C API 移除了 [`PySequence_Fast_GET_SIZE`](https://docs.python.org/zh-cn/3/c-api/sequence.html#c.PySequence_Fast_GET_SIZE), [`PySequence_Fast_GET_ITEM`](https://docs.python.org/zh-cn/3/c-api/sequence.html#c.PySequence_Fast_GET_ITEM) 和 [`PySequence_Fast_ITEMS`](https://docs.python.org/zh-cn/3/c-api/sequence.html#c.PySequence_Fast_ITEMS) 宏，因为它们在受限 C API 始终是不可用的。 （由 Victor Stinner 在 [gh-91417](https://github.com/python/cpython/issues/91417) 中贡献。）

### 被移除的 C API

-

使用可变基类创建 [`不可变类型`](https://docs.python.org/zh-cn/3/c-api/typeobj.html#c.Py_TPFLAGS_IMMUTABLETYPE) 的做法自 Python 3.12 起已被弃用，现在将会引发 [`TypeError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#TypeError)。 （由 Nikita Sobolev 在 [gh-119775](https://github.com/python/cpython/issues/119775) 中贡献。）

-

移除在 Python 3.12 中已被弃用的 `PyDictObject.ma_version_tag` 成员。 请改用 [`PyDict_AddWatcher()`](https://docs.python.org/zh-cn/3/c-api/dict.html#c.PyDict_AddWatcher) API。 （由 Sam Gross 在 [gh-124296](https://github.com/python/cpython/issues/124296) 中贡献。）

-

移除私有函数 `_Py_InitializeMain()`。该函数是 [**PEP 587**](https://peps.python.org/pep-0587/) 在 Python 3.8 中引入的 [provisional API](https://docs.python.org/zh-cn/3/glossary.html#term-provisional-API)。 （由 Victor Stinner 在 [gh-129033](https://github.com/python/cpython/issues/129033) 中贡献。）

-

移除了未写入文档的 API `Py_C_RECURSION_LIMIT` 和 `PyThreadState.c_recursion_remaining`。 它们在 3.13 中增加并且未宣布弃用即被移除。 请在 C 代码中使用 [`Py_EnterRecursiveCall()`](https://docs.python.org/zh-cn/3/c-api/exceptions.html#c.Py_EnterRecursiveCall) 来防范无限递归问题。 （由 Petr Viktorin 在 [gh-133079](https://github.com/python/cpython/issues/133079) 中移除，另请参阅 [gh-130396](https://github.com/python/cpython/issues/130396)。）

### 已弃用的 C API

-

现在 `Py_HUGE_VAL` 宏已被设为 [soft deprecated](https://docs.python.org/zh-cn/3/glossary.html#term-soft-deprecated)。 请改用 `Py_INFINITY`。 （由 Sergey B Kirpichev 在 [gh-120026](https://github.com/python/cpython/issues/120026) 中贡献。）

-

现在 `Py_IS_NAN`, `Py_IS_INFINITY` 和 `Py_IS_FINITE` 等宏已被设为 [soft deprecated](https://docs.python.org/zh-cn/3/glossary.html#term-soft-deprecated)。 请改用 `isnan`, `isinf` 和 `isfinite`，它们自 C99 起在 `math.h` 中可用。 （由 Sergey B Kirpichev 在 [gh-119613](https://github.com/python/cpython/issues/119613) 中贡献。）

-

非元组序列当 *items* 包含存储 [借入缓冲区](https://docs.python.org/zh-cn/3/c-api/arg.html#c-arg-borrowed-buffer) 或 [borrowed reference](https://docs.python.org/zh-cn/3/glossary.html#term-borrowed-reference) 的格式单元的情况下在 [`PyArg_ParseTuple()`](https://docs.python.org/zh-cn/3/c-api/arg.html#c.PyArg_ParseTuple) 和其他 [参数解析](https://docs.python.org/zh-cn/3/c-api/arg.html#arg-parsing) 函数中用作 `(items)` 格式单元参数的做法现在已被弃用。 （由 Serhiy Storchaka 在 [gh-50333](https://github.com/python/cpython/issues/50333) 中贡献。）

-

现在 `_PyMonitoring_FireBranchEvent` 函数已被弃用并应当替换为对 [`PyMonitoring_FireBranchLeftEvent()`](https://docs.python.org/zh-cn/3/c-api/monitoring.html#c.PyMonitoring_FireBranchLeftEvent) 和 [`PyMonitoring_FireBranchRightEvent()`](https://docs.python.org/zh-cn/3/c-api/monitoring.html#c.PyMonitoring_FireBranchRightEvent) 的调用。

-

之前未写入文档的函数 [`PySequence_In()`](https://docs.python.org/zh-cn/3/c-api/sequence.html#c.PySequence_In) 现在被设为 [soft deprecated](https://docs.python.org/zh-cn/3/glossary.html#term-soft-deprecated)。 请改用 [`PySequence_Contains()`](https://docs.python.org/zh-cn/3/c-api/sequence.html#c.PySequence_Contains)。 （由 Yuki Kobayashi 在 [gh-127896](https://github.com/python/cpython/issues/127896) 中贡献。）

#### 计划在 Python 3.15 中移除

-

The [`PyImport_ImportModuleNoBlock()`](https://docs.python.org/zh-cn/3/c-api/import.html#c.PyImport_ImportModuleNoBlock): 改用 [`PyImport_ImportModule()`](https://docs.python.org/zh-cn/3/c-api/import.html#c.PyImport_ImportModule)。

-

[`PyWeakref_GetObject()`](https://docs.python.org/zh-cn/3/c-api/weakref.html#c.PyWeakref_GetObject) 和 [`PyWeakref_GET_OBJECT()`](https://docs.python.org/zh-cn/3/c-api/weakref.html#c.PyWeakref_GET_OBJECT): 改用 [`PyWeakref_GetRef()`](https://docs.python.org/zh-cn/3/c-api/weakref.html#c.PyWeakref_GetRef)。 在 Python 3.12 及更旧的版本中可以使用 [pythoncapi-compat 项目](https://github.com/python/pythoncapi-compat/) 来获取 `PyWeakref_GetRef()`。

-

[`Py_UNICODE`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.Py_UNICODE) 类型和 `Py_UNICODE_WIDE` 宏：改用 `wchar_t`。

-

`PyUnicode_AsDecodedObject()`: 改用 [`PyCodec_Decode()`](https://docs.python.org/zh-cn/3/c-api/codec.html#c.PyCodec_Decode)。

-

`PyUnicode_AsDecodedUnicode()`: 改用 [`PyCodec_Decode()`](https://docs.python.org/zh-cn/3/c-api/codec.html#c.PyCodec_Decode)；请注意某些编解码器 (例如 "base64") 可能返回 [`str`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#str) 以外的类型，比如 [`bytes`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#bytes)。

-

`PyUnicode_AsEncodedObject()`: 改用 [`PyCodec_Encode()`](https://docs.python.org/zh-cn/3/c-api/codec.html#c.PyCodec_Encode)。

-

`PyUnicode_AsEncodedUnicode()`: 使用 [`PyCodec_Encode()`](https://docs.python.org/zh-cn/3/c-api/codec.html#c.PyCodec_Encode) 代替；请注意，某些编解码器（如 "base64"）可能返回 [`bytes`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#bytes) 之外的类型，如 [`str`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#str)。

-

Python 初始化函数， Python 3.13 中弃用：

-

[`Py_GetPath()`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_GetPath):使用 [`PyConfig_Get("module_search_paths")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) ([`sys.path`](https://docs.python.org/zh-cn/3/library/sys.html#sys.path)) 代替。

-

[`Py_GetPrefix()`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_GetPrefix):使用 [`PyConfig_Get("base_prefix")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) ([`sys.base_prefix`](https://docs.python.org/zh-cn/3/library/sys.html#sys.base_prefix)) 代替。如果需要处理 [virtual environments](https://docs.python.org/zh-cn/3/library/venv.html#venv-def) ，请使用 `PyConfig_Get("prefix")` ([`sys.prefix`](https://docs.python.org/zh-cn/3/library/sys.html#sys.prefix)) 。

-

[`Py_GetExecPrefix()`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_GetExecPrefix):使用 [`PyConfig_Get("base_exec_prefix")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) ([`sys.base_exec_prefix`](https://docs.python.org/zh-cn/3/library/sys.html#sys.base_exec_prefix)) 代替。如果需要处理 [virtual environments](https://docs.python.org/zh-cn/3/library/venv.html#venv-def) ，请使用 `PyConfig_Get("exec_prefix")` ([`sys.exec_prefix`](https://docs.python.org/zh-cn/3/library/sys.html#sys.exec_prefix)) 。

-

[`Py_GetProgramFullPath()`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_GetProgramFullPath):使用 [`PyConfig_Get("executable")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) ([`sys.executable`](https://docs.python.org/zh-cn/3/library/sys.html#sys.executable)) 代替。

-

[`Py_GetProgramName()`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_GetProgramName):使用 [`PyConfig_Get("executable")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) ([`sys.executable`](https://docs.python.org/zh-cn/3/library/sys.html#sys.executable)) 代替。

-

[`Py_GetPythonHome()`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_GetPythonHome): 使用 [`PyConfig_Get("home")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 或 [`PYTHONHOME`](https://docs.python.org/zh-cn/3/using/cmdline.html#envvar-PYTHONHOME) 环境变量代替。

在 Python 3.13 和更旧的版本中可以使用 [pythoncapi-compat 项目](https://github.com/python/pythoncapi-compat/) 来获取 [`PyConfig_Get()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 。

-

用于配置 Python 的初始化的函数，在 Python 3.11 中已弃用：

-

`PySys_SetArgvEx()`: 改为设置 [`PyConfig.argv`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.argv)。

-

`PySys_SetArgv()`: 改为设置 [`PyConfig.argv`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.argv)。

-

`Py_SetProgramName()`: 改为设置 [`PyConfig.program_name`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.program_name)。

-

`Py_SetPythonHome()`: 改为设置 [`PyConfig.home`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.home)。

-

[`PySys_ResetWarnOptions()`](https://docs.python.org/zh-cn/3/c-api/sys.html#c.PySys_ResetWarnOptions): 改为清除 [`sys.warnoptions`](https://docs.python.org/zh-cn/3/library/sys.html#sys.warnoptions) 和 `warnings.filters`。

[`Py_InitializeFromConfig()`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_InitializeFromConfig) API 应与 [`PyConfig`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig) 一起使用。

-

全局配置变量：

-

[`Py_DebugFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_DebugFlag): 改用 [`PyConfig.parser_debug`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.parser_debug) 或 [`PyConfig_Get("parser_debug")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get)。

-

[`Py_VerboseFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_VerboseFlag): 改用 [`PyConfig.verbose`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.verbose) 或 [`PyConfig_Get("verbose")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get)。

-

[`Py_QuietFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_QuietFlag): 改用 [`PyConfig.quiet`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.quiet) 或 [`PyConfig_Get("quiet")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get)。

-

[`Py_InteractiveFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_InteractiveFlag): 改用 [`PyConfig.interactive`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.interactive) 或 [`PyConfig_Get("interactive")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get)。

-

[`Py_InspectFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_InspectFlag): 改用 [`PyConfig.inspect`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.inspect) 或 [`PyConfig_Get("inspect")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get)。

-

[`Py_OptimizeFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_OptimizeFlag): 改用 [`PyConfig.optimization_level`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.optimization_level) 或 [`PyConfig_Get("optimization_level")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get)。

-

[`Py_NoSiteFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_NoSiteFlag): 改用 [`PyConfig.site_import`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.site_import) 或 [`PyConfig_Get("site_import")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get)。

-

[`Py_BytesWarningFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_BytesWarningFlag): 改用 [`PyConfig.bytes_warning`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.bytes_warning) 或 [`PyConfig_Get("bytes_warning")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get)。

-

[`Py_FrozenFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_FrozenFlag): 使用 [`PyConfig.pathconfig_warnings`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.pathconfig_warnings) 或 [`PyConfig_Get("pathconfig_warnings")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 代替。

-

[`Py_IgnoreEnvironmentFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_IgnoreEnvironmentFlag): 使用 [`PyConfig.use_environment`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.use_environment) 或 [`PyConfig_Get("use_environment")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 代替。

-

[`Py_DontWriteBytecodeFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_DontWriteBytecodeFlag): 使用 [`PyConfig.write_bytecode`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.write_bytecode) 或 [`PyConfig_Get("write_bytecode")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 代替。

-

[`Py_NoUserSiteDirectory`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_NoUserSiteDirectory): 使用 [`PyConfig.user_site_directory`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.user_site_directory) 或 [`PyConfig_Get("user_site_directory")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 代替。

-

[`Py_UnbufferedStdioFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_UnbufferedStdioFlag): 使用 [`PyConfig.buffered_stdio`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.buffered_stdio) 或 [`PyConfig_Get("buffered_stdio")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 代替。

-

[`Py_HashRandomizationFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_HashRandomizationFlag): 使用 [`PyConfig.use_hash_seed`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.use_hash_seed) 和 [`PyConfig.hash_seed`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.hash_seed) 或 [`PyConfig_Get("hash_seed")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 代替。

-

[`Py_IsolatedFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_IsolatedFlag): 使用 [`PyConfig.isolated`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.isolated) 或 [`PyConfig_Get("isolated")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 代替。

-

[`Py_LegacyWindowsFSEncodingFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_LegacyWindowsFSEncodingFlag): 使用 [`PyPreConfig.legacy_windows_fs_encoding`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyPreConfig.legacy_windows_fs_encoding) 或 [`PyConfig_Get("legacy_windows_fs_encoding")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 代替。

-

[`Py_LegacyWindowsStdioFlag`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_LegacyWindowsStdioFlag): 使用 [`PyConfig.legacy_windows_stdio`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.legacy_windows_stdio) 或 [`PyConfig_Get("legacy_windows_stdio")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 代替。

-

`Py_FileSystemDefaultEncoding`, `Py_HasFileSystemDefaultEncoding`: 使用 [`PyConfig.filesystem_encoding`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.filesystem_encoding) 或 [`PyConfig_Get("filesystem_encoding")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 代替。

-

`Py_FileSystemDefaultEncodeErrors`: 使用 [`PyConfig.filesystem_errors`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig.filesystem_errors) 或 [`PyConfig_Get("filesystem_errors")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 代替。

-

`Py_UTF8Mode`: 使用 [`PyPreConfig.utf8_mode`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyPreConfig.utf8_mode) 或 [`PyConfig_Get("utf8_mode")`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 代替。 (参见 [`Py_PreInitialize()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.Py_PreInitialize))。

[`Py_InitializeFromConfig()`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_InitializeFromConfig) API 应与 [`PyConfig`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig) 一起使用，以设置这些选项。或者使用 [`PyConfig_Get()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 在运行时获取这些选项。

#### 计划在 Python 3.16 中移除

-

捆绑的 `libmpdec` 副本。

#### 计划在 Python 3.18 中移除

-

以下私有函数已被弃用，并计划在 Python 3.18 中移除：

-

`_PyBytes_Join()`：使用 [`PyBytes_Join()`](https://docs.python.org/zh-cn/3/c-api/bytes.html#c.PyBytes_Join)。

-

`_PyDict_GetItemStringWithError()`: 使用 [`PyDict_GetItemStringRef()`](https://docs.python.org/zh-cn/3/c-api/dict.html#c.PyDict_GetItemStringRef)。

-

`_PyDict_Pop()`: 使用 [`PyDict_Pop()`](https://docs.python.org/zh-cn/3/c-api/dict.html#c.PyDict_Pop).

-

`_PyLong_Sign()`：使用 [`PyLong_GetSign()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_GetSign)。

-

`_PyLong_FromDigits()` 和 `_PyLong_New()`：使用 [`PyLongWriter_Create()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLongWriter_Create).

-

`_PyThreadState_UncheckedGet()`：使用 [`PyThreadState_GetUnchecked()`](https://docs.python.org/zh-cn/3/c-api/threads.html#c.PyThreadState_GetUnchecked)。

-

`_PyUnicode_AsString()`：使用 [`PyUnicode_AsUTF8()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicode_AsUTF8)。

-

`_PyUnicodeWriter_Init()`: 将 `_PyUnicodeWriter_Init(&writer)` 替换为 [`writer = PyUnicodeWriter_Create(0)`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_Create)。

-

`_PyUnicodeWriter_Finish()`: 将 `_PyUnicodeWriter_Finish(&writer)` 替换为 [`PyUnicodeWriter_Finish(writer)`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_Finish)。

-

`_PyUnicodeWriter_Dealloc()`: 将 `_PyUnicodeWriter_Dealloc(&writer)` 替换为 [`PyUnicodeWriter_Discard(writer)`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_Discard)。

-

`_PyUnicodeWriter_WriteChar()`: 将 `_PyUnicodeWriter_WriteChar(&writer, ch)` 替换为 [`PyUnicodeWriter_WriteChar(writer, ch)`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteChar).

-

`_PyUnicodeWriter_WriteStr()`: 将 `_PyUnicodeWriter_WriteStr(&writer, str)` 替换为 [`PyUnicodeWriter_WriteStr(writer, str)`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteStr)。

-

`_PyUnicodeWriter_WriteSubstring()`: 将 `_PyUnicodeWriter_WriteSubstring(&writer, str, start, end)` 替换为 [`PyUnicodeWriter_WriteSubstring(writer, str, start, end)`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteSubstring)。

-

`_PyUnicodeWriter_WriteASCIIString()`: 请将 `_PyUnicodeWriter_WriteASCIIString(&writer, str)` 替换为 [`PyUnicodeWriter_WriteASCII(writer, str)`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteASCII)。

-

`_PyUnicodeWriter_WriteLatin1String()`: 将 `_PyUnicodeWriter_WriteLatin1String(&writer, str)` 替换为 [`PyUnicodeWriter_WriteUTF8(writer, str)`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteUTF8)。

-

`_PyUnicodeWriter_Prepare()`: (无替代)。

-

`_PyUnicodeWriter_PrepareKind()`: (无替代)。

-

`_Py_HashPointer()`：使用 [`Py_HashPointer()`](https://docs.python.org/zh-cn/3/c-api/hash.html#c.Py_HashPointer)。

-

`_Py_fopen_obj()`：使用 [`Py_fopen()`](https://docs.python.org/zh-cn/3/c-api/sys.html#c.Py_fopen)。

[pythoncapi-compat 项目](https://github.com/python/pythoncapi-compat/) 可被用于在 Python 3.13 及更早版本中获取这些新的公有函数。 （由 Victor Stinner 在 [gh-128863](https://github.com/python/cpython/issues/128863) 中贡献。）

#### 计划在未来版本中移除

以下 API 已被弃用，将被移除，但目前尚未确定移除日期。

-

[`Py_TPFLAGS_HAVE_FINALIZE`](https://docs.python.org/zh-cn/3/c-api/typeobj.html#c.Py_TPFLAGS_HAVE_FINALIZE): 自 Python 3.8 起不再需要。

-

[`PyErr_Fetch()`](https://docs.python.org/zh-cn/3/c-api/exceptions.html#c.PyErr_Fetch): 改用 [`PyErr_GetRaisedException()`](https://docs.python.org/zh-cn/3/c-api/exceptions.html#c.PyErr_GetRaisedException)。

-

[`PyErr_NormalizeException()`](https://docs.python.org/zh-cn/3/c-api/exceptions.html#c.PyErr_NormalizeException): 改用 [`PyErr_GetRaisedException()`](https://docs.python.org/zh-cn/3/c-api/exceptions.html#c.PyErr_GetRaisedException)。

-

[`PyErr_Restore()`](https://docs.python.org/zh-cn/3/c-api/exceptions.html#c.PyErr_Restore): 改用 [`PyErr_SetRaisedException()`](https://docs.python.org/zh-cn/3/c-api/exceptions.html#c.PyErr_SetRaisedException)。

-

[`PyModule_GetFilename()`](https://docs.python.org/zh-cn/3/c-api/module.html#c.PyModule_GetFilename): 改用 [`PyModule_GetFilenameObject()`](https://docs.python.org/zh-cn/3/c-api/module.html#c.PyModule_GetFilenameObject)。

-

[`PyOS_AfterFork()`](https://docs.python.org/zh-cn/3/c-api/sys.html#c.PyOS_AfterFork): 改用 [`PyOS_AfterFork_Child()`](https://docs.python.org/zh-cn/3/c-api/sys.html#c.PyOS_AfterFork_Child)。

-

[`PySlice_GetIndicesEx()`](https://docs.python.org/zh-cn/3/c-api/slice.html#c.PySlice_GetIndicesEx): 改用 [`PySlice_Unpack()`](https://docs.python.org/zh-cn/3/c-api/slice.html#c.PySlice_Unpack) and [`PySlice_AdjustIndices()`](https://docs.python.org/zh-cn/3/c-api/slice.html#c.PySlice_AdjustIndices)。

-

[`PyUnicode_READY()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicode_READY): 自 Python 3.12 起不再需要

-

`PyErr_Display()`: 改用 [`PyErr_DisplayException()`](https://docs.python.org/zh-cn/3/c-api/exceptions.html#c.PyErr_DisplayException)。

-

`_PyErr_ChainExceptions()`: 改用 `_PyErr_ChainExceptions1()`。

-

`PyBytesObject.ob_shash` 成员：改为调用 [`PyObject_Hash()`](https://docs.python.org/zh-cn/3/c-api/object.html#c.PyObject_Hash)。

-

线程本地存储 (TLS) API：

-

[`PyThread_create_key()`](https://docs.python.org/zh-cn/3/c-api/tls.html#c.PyThread_create_key): 改用 [`PyThread_tss_alloc()`](https://docs.python.org/zh-cn/3/c-api/tls.html#c.PyThread_tss_alloc)。

-

[`PyThread_delete_key()`](https://docs.python.org/zh-cn/3/c-api/tls.html#c.PyThread_delete_key): 改用 [`PyThread_tss_free()`](https://docs.python.org/zh-cn/3/c-api/tls.html#c.PyThread_tss_free)。

-

[`PyThread_set_key_value()`](https://docs.python.org/zh-cn/3/c-api/tls.html#c.PyThread_set_key_value): 改用 [`PyThread_tss_set()`](https://docs.python.org/zh-cn/3/c-api/tls.html#c.PyThread_tss_set)。

-

[`PyThread_get_key_value()`](https://docs.python.org/zh-cn/3/c-api/tls.html#c.PyThread_get_key_value): 改用 [`PyThread_tss_get()`](https://docs.python.org/zh-cn/3/c-api/tls.html#c.PyThread_tss_get)。

-

[`PyThread_delete_key_value()`](https://docs.python.org/zh-cn/3/c-api/tls.html#c.PyThread_delete_key_value): 改用 [`PyThread_tss_delete()`](https://docs.python.org/zh-cn/3/c-api/tls.html#c.PyThread_tss_delete)。

-

[`PyThread_ReInitTLS()`](https://docs.python.org/zh-cn/3/c-api/tls.html#c.PyThread_ReInitTLS): 自 Python 3.7 起不再需要。

## 构建的改变

-

[**PEP 776**](https://peps.python.org/pep-0776/): Emscripten 现在是官方支持的 [**第 3 层级**](https://peps.python.org/pep-0011/#tier-3) 平台。作为此项工作的一部分，在 [Emscripten libc](https://emscripten.org/docs/porting/emscripten-runtime-environment.html) 中有超过 25 个程序缺陷被修复。Emscripten 现在包括了对 [`ctypes`](https://docs.python.org/zh-cn/3/library/ctypes.html#module-ctypes), [`termios`](https://docs.python.org/zh-cn/3/library/termios.
html#module-termios) 和 [`fcntl`](https://docs.python.org/zh-cn/3/library/fcntl.html#module-fcntl) 的支持，以及对新的 [默认交互式 shell](https://docs.python.org/zh-cn/3/tutorial/interpreter.html#tut-interactive) 的实验性支持。（由 R.Hood Chatham 在 [gh-127146](https://github.com/python/cpython/issues/127146), [gh-127683](https://github.com/python/cpython/issues/127683) 和 [gh-136931](https://github.com/python/cpython/issues/136931) 中贡献。
）

-

现在 [python.org](https://www.python.org/downloads/android/) 提供了官方 Android 二进制发布包。

-

生成 `configure` 文件现在需要 GNU Autoconf 2.72 版本。（由 Erlend Aasland 在 [gh-115765](https://github.com/python/cpython/issues/115765) 中贡献。）

-

`wasm32-unknown-emscripten` 现已成为 [**PEP 11**](https://peps.python.org/pep-0011/) 标准中的第三级（Tier 3）支持平台。（由 R. Hood Chatham 在 [gh-127146](https://github.com/python/cpython/issues/127146)、[gh-127683](https://github.com/python/cpython/issues/127683) 和 [gh-136931](https://github.com/python/cpython/issues/136931) 中贡献。）

-

现在可以通过 [Py_NO_LINK_LIB](https://docs.python.org/zh-cn/3/extending/windows.html#c.Py_NO_LINK_LIB) 关闭基于 `#pragma` 与 `python3*.lib` 的链接。（由 Jean-Christophe Fillion-Robin 在 [gh-82909](https://github.com/python/cpython/issues/82909) 中贡献。）

-

CPython 现在默认启用了一组推荐的编译器选项以增强安全性。如需禁用这些选项，可使用 [`--disable-safety`](https://docs.python.org/zh-cn/3/using/configure.html#cmdoption-disable-safety) `configure` 选项；若希望启用更大范围的编译器安全选项（但会牺牲性能），则可使用 [`--enable-slower-safety`](https://docs.python.org/zh-cn/3/using/configure.html#cmdoption-enable-slower-safety) 选项。

-

`WITH_FREELISTS` 宏和 `--without-freelists` `configure` 选项已被移除。

-

新的 `configure` 选项 [`--with-tail-call-interp`](https://docs.python.org/zh-cn/3/using/configure.html#cmdoption-with-tail-call-interp) 可被用来启用实验性的尾调用解释器。 请参阅 一种新型的解释器 了解详情。

-

要禁用新的远程调试支持，请使用 [`--without-remote-debug`](https://docs.python.org/zh-cn/3/using/configure.html#cmdoption-without-remote-debug) `configure` 选项。 出于安全原因，这可能会有用。

-

iOS 和 macOS 应用程序现在可配置为将 `stdout` 和 `stderr` 输出内容重定向至系统日志。（由 Russell Keith-Magee 在 [gh-127592](https://github.com/python/cpython/issues/127592) 中贡献。）

-

iOS 测试平台现已支持在测试运行时实时流式传输测试输出，并可用于运行除 CPython 之外的其他项目测试套件。（由 Russell Keith-Magee 在 [gh-127592](https://github.com/python/cpython/issues/127592) 中贡献。）

### `build-details.json`

现在的 Python 安装包中包含一个新文件：`build-details.json`。这是一个静态的 JSON 文档，包含 CPython 的构建详情，无需运行代码即可进行内省。这对于 Python 启动器、交叉编译等使用场景很有帮助。

`build-details.json` 必须安装在与平台无关的标准库目录中。这对应于 ['stdlib'](https://docs.python.org/zh-cn/3/library/sysconfig.html#installation-paths) [`sysconfig`](https://docs.python.org/zh-cn/3/library/sysconfig.html#module-sysconfig) 安装路径，可通过运行 `sysconfig.get_path('stdlib')` 找到该路径。

参见

[**PEP 739**](https://peps.python.org/pep-0739/) —— `build-details.json` 1.0——Python 构建详情的静态描述文件

### PGP 签名的停用

Python 3.14 及未来的版本将不再提供 PGP (Pretty Good Privacy) 签名。 要验证 CPython 制品，用户必须使用 [Sigstore 验证材料](https://www.python.org/downloads/metadata/sigstore/)。 自 Python 3.11 起的发布版就已采用 [Sigstore](https://www.sigstore.dev/) 进行签名。

发布流程中的这一变更已在 [**PEP 761**](https://peps.python.org/pep-0761/) 中明确规定。

### 自由线程版 Python 已获官方支持

自由线程的 Python 构建版现在已被支持而不再是实验性的。 这是自由线程 Python 获得官方支持但仍为可选项的 [第二阶段](https://discuss.python.org/t/37075) 的开始。

自由线程团队相信此项目走在正确的路径上，并赞赏各位持续努力的贡献使得自由线程特性已准备好在 Python 社区获得更广泛的接受。

随着这个 PEP 被提议和被接受，Python 开发者社区应当广泛宣传自由线程已成为受支持的 Python 构建选项并将在未来继续发展，它不会在没有适当弃用计划的情况下被移除。

任何过渡到 [第三阶段](https://discuss.python.org/t/37075)，即将自由线程作为 Python 默认或唯一的构建版的决定尚未明确作出，这取决于 CPython 本身和社区内部的许多因素。 这个决定会留给未来。

参见

[**PEP 779**](https://peps.python.org/pep-0779/)

[PEP 779 的接受](https://discuss.python.org/t/84319/123)

### 实验性即时编译器（JIT）的二进制发布版本

官方 macOS 和 Windows 发布版二进制文件现已包含 *实验性* 即时编译（JIT）器。虽然不建议在生产环境中使用，但可通过设置环境变量 [`PYTHON_JIT=1`](https://docs.python.org/zh-cn/3/using/cmdline.html#envvar-PYTHON_JIT) 进行测试。下游源码构建和再分发方可使用配置选项 [`--enable-experimental-jit=yes-off`](https://docs.python.org/zh-cn/3/using/configure.html#cmdoption-enable-experimental-jit) 实现类似行为。

该JIT编译器尚处于早期开发阶段，性能表现存在波动：启用后根据工作负载不同，可能产生10%的性能下降至20%的性能提升。为便于测试评估，[`sys._jit`](https://docs.python.org/zh-cn/3/library/sys.html#sys._jit) 命名空间提供了一组内省函数：[`sys._jit.is_available()`](https://docs.python.org/zh-cn/3/library/sys.html#sys._jit.is_available) 用于检测当前可执行文件是否支持JIT编译，而 [`sys._jit.is_enabled()`](https://docs.python.org/zh-cn/3/library/sys.html#sys._jit.is_enabled) 则可判断当前进程是否已启用JIT编译功能。

目前，最明显的功能缺失是原生调试器和性能分析器如 `gdb` 和 `perf` 无法展开 JIT 帧（而 Python 调试器和性能分析器如 [`pdb`](https://docs.python.org/zh-cn/3/library/pdb.html#module-pdb) 或 [`profile`](https://docs.python.org/zh-cn/3/library/profile.html#module-profile) 则无需修改即可继续工作）。 自由线程构建不支持 JIT 编译。

如遇任何错误或严重性能退化问题，请务必提交报告！

参见

[**PEP 744**](https://peps.python.org/pep-0744/)

## 移植到 Python 3.14

本节列出了先前描述的更改以及可能需要更改代码的其他错误修正.

### Python API 的变化

-

在 macOS 以外的 Unix 平台上，*forkserver* 现在是用于 [`multiprocessing`](https://docs.python.org/zh-cn/3/library/multiprocessing.html#module-multiprocessing) 和 [`ProcessPoolExecutor`](https://docs.python.org/zh-cn/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor) 的默认 [启动方法](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-start-methods)，代替了 *fork*。

请参阅 (1) 和 (2) 了解详情。

如果你在 [`multiprocessing`](https://docs.python.org/zh-cn/3/library/multiprocessing.html#module-multiprocessing) 或 [`concurrent.futures`](https://docs.python.org/zh-cn/3/library/concurrent.futures.html#module-concurrent.futures) 中遇到 [`NameError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#NameError) 或 pickle 错误，请参阅 [forkserver 的限制](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-programming-forkserver)。

这一更改不会影响 Windows 或 macOS，在这两个平台上 ['spawn'](https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing-start-method-spawn) 仍是默认的启动方法。remains the default start method.

-

[`functools.partial`](https://docs.python.org/zh-cn/3/library/functools.html#functools.partial) 现在是一个方法描述符。若需保持原有行为，请将其包装在 [`staticmethod()`](https://docs.python.org/zh-cn/3/builtins/functions.html#staticmethod) 中。（由 Serhiy Storchaka 和 Dominykas Grigonis 在 [gh-121027](https://github.com/python/cpython/issues/121027) 中贡献。）

-

垃圾回收器现在是增量式的，这意味着 [`gc.collect()`](https://docs.python.org/zh-cn/3/library/gc.html#gc.collect) 的行为有轻微改变：

-

`gc.collect(1)`：执行一次增量式垃圾回收，而非专门回收第1代对象。

-

对 `gc.collect()` 的其他调用保持不变。

-

[`locale.nl_langinfo()`](https://docs.python.org/zh-cn/3/library/locale.html#locale.nl_langinfo) 函数现在会在某些情况下临时设置 `LC_CTYPE` 区域设置。这种临时修改会影响其他线程。（由 Serhiy Storchaka 在 [gh-69998](https://github.com/python/cpython/issues/69998) 中贡献。）

-

[`pickle.dump()`](https://docs.python.org/zh-cn/3/library/pickle.html#pickle.dump) and [`pickle.dumps()`](https://docs.python.org/zh-cn/3/library/pickle.html#pickle.dumps) now raise [`PicklingError`](https://docs.python.org/zh-cn/3/library/pickle.html#pickle.PicklingError) for some failures that previously raised [`AttributeError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#AttributeError), [`ImportError`](https://docs.
python.org/zh-cn/3/builtins/exceptions.html#ImportError), [`ValueError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#ValueError), [`UnicodeEncodeError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#UnicodeEncodeError) or `PicklingError`, depending on the implementation (for example, pickling a local object, or an object whose module cannot be imported).The original exception is chained to the `PicklingError`.
Code that caught these exceptions should also catch `PicklingError`.(Contributed by Serhiy Storchaka in [gh-122311](https://github.com/python/cpython/issues/122311).)

-

[`types.UnionType`](https://docs.python.org/zh-cn/3/library/types.html#types.UnionType) 现在是 [`typing.Union`](https://docs.python.org/zh-cn/3/library/typing.html#typing.Union) 的别名，这会导致部分行为发生变化。更多细节请参见 上文。（由 Jelle Zijlstra 在 [gh-105499](https://github.com/python/cpython/issues/105499) 中贡献。）

-

标注的运行时行为在多个方面发生了改变；请参阅 上文 了解详情。 虽然大多数与标注交互的代码应该能继续工作，但某些未写入文档的细节行为可能有所不同。for details. While most code that interacts with annotations should continue to work, some undocumented details may behave differently.

-

由于要将 [`mimetypes`](https://docs.python.org/zh-cn/3/library/mimetypes.html#module-mimetypes) CLI 对外公开，现在当它执行失败时的退出码将为 `1` 而不是 `0`，当有不正确的命令行形参时的退出码为 `2` 而不是 `1`。 错误消息现在将被打印到 stderr。

-

现在当作为整个模式给出时正则表达式中的 `\B` 模式将会匹配空字符串，这可能导致行为上的变化。

-

在 FreeBSD 上，[`sys.platform`](https://docs.python.org/zh-cn/3/library/sys.html#sys.platform) 不再包含主版本号。

### 标注中的变化 ([**PEP 649**](https://peps.python.org/pep-0649/) 和 [**PEP 749**](https://peps.python.org/pep-0749/))

本节包含因为与 标注的迟延求值 相关的变化而可能需要对标注或者与标注内省交互的 Python 代码进行的修改的指导。

在大部分情况下，来自较旧 Python 版本的可用代码将不需要任何修改。

#### 注解代码的影响

如果在代码中定义注解（例如用于静态类型检查器），那么这一变更可能不会产生影响：你可以继续保持与之前Python版本相同的注解书写方式。

你很可能可以移除注解中的引号字符串（这些通常用于前向引用）。同样地，如果使用 `from __future__ import annotations` 来避免在注解中书写字符串，当你仅支持 Python 3.14 及更新版本时，很可能可以移除该导入。不过，如果依赖读取注解的第三方库，这些库可能需要相应修改以支持无引号注解，才能正常工作。

#### 访问 `__annotations__` 的影响

如果你的代码会读取对象的 [`__annotations__`](https://docs.python.org/zh-cn/3/reference/datamodel.html#object.__annotations__) 属性，你可能需要进行修改以支持依赖于标注的迟延求值的代码。 例如，你可以使用 [`annotationlib.get_annotations()`](https://docs.python.org/zh-cn/3/library/annotationlib.html#annotationlib.get_annotations) 并附带 [`FORWARDREF`](https://docs.python.org/zh-cn/3/library/annotationlib.html#annotationlib.Format.FORWARDREF) 格式，就像 [`dataclasses`](https://docs.python.org/zh-cn/3/library/dataclasses.html#module-dataclasses) 模块现在所做的那样。

外部包 [typing_extensions](https://pypi.org/project/typing_extensions/) 提供了 [`annotationlib`](https://docs.python.org/zh-cn/3/library/annotationlib.html#module-annotationlib) 模块部分功能的向后兼容实现，包括 [`Format`](https://docs.python.org/zh-cn/3/library/annotationlib.html#annotationlib.Format) 枚举和 [`get_annotations()`](https://docs.python.org/zh-cn/3/library/annotationlib.html#annotationlib.get_annotations) 函数。这些可用于编写跨版本代码，以利用 Python 3.14 中的新行为。

#### 相关变更

Python 3.14 中的改变的设计思路是对于 `__annotations__` 在运行时的工作方式进行调整的同时最小化对于在源代码中包含标注的代码和读取 `__annotations__` 的代码的破坏性影响。 不过，如果你依赖于标注行为未写入文档的细节或标准库中的私有函数，那么你的代码可能出于多种原因而无法在 Python 3.14 中正常工作。 为保证你的代码不受未来变化的影响，请仅使用 [`annotationlib`](https://docs.python.org/zh-cn/3/library/annotationlib.html#module-annotationlib) 模块已写入文档的功能。

特别需要注意的是，不要直接从类型对象的命名空间字典属性中读取注解。在类构造期间应使用 [`annotationlib.get_annotate_from_class_namespace()`](https://docs.python.org/zh-cn/3/library/annotationlib.html#annotationlib.get_annotate_from_class_namespace) 函数，之后则使用 [`annotationlib.get_annotations()`](https://docs.python.org/zh-cn/3/library/annotationlib.html#annotationlib.get_annotations) 函数。

在之前的版本中，有时可以通过带注解类的实例访问类注解。这种行为属于未文档化的意外实现，在 Python 3.14 中将不再有效。

#### `from __future__ import annotations`

在 Python 3.7 中，[**PEP 563**](https://peps.python.org/pep-0563/) 引入了 `from __future__ import annotations` [future 语句](https://docs.python.org/zh-cn/3/reference/simple_stmts.html#future)，这会将所有标注转为字符串。

不过，这条语句现在已被弃用并预计会在未来的 Python 中移除。 此项移除将不会立即执行而是直到 2029 年 Python 3.13 的生命期结束之后，它是不支持标注迟延求值的最后一个 Python 版本。

在 Python 3.14 中，使用 `from __future__ import annotations` 的代码的行为将没有变化。

### C API 的变化

-

[`Py_Finalize()`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_Finalize) 现在会删除所有已驻留字符串。 这一变更将不向下兼容任何在调用 `Py_Finalize()` 后仍拥有驻留字符串并在后续调用 [`Py_Initialize()`](https://docs.python.org/zh-cn/3/c-api/interp-lifecycle.html#c.Py_Initialize) 时重复使用的 C 扩展模块。 此行为引发的任何问题通常会导致在后续 `Py_Initialize()` 调用执行期间因访问未初始化内存而引发崩溃。 要修复此问题，应使用地址静化器来标识任何来自驻留字符串的释放后使用并在模块关闭期间释放它。 （由 Eddie Elizondo 在 [gh-113601](https://github.com/python/cpython/issues/113601) 中贡献。）

-

[Unicode异常对象](https://docs.python.org/zh-cn/3/c-api/exceptions.html#unicodeexceptions) C API现会在异常参数不是 [`UnicodeError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#UnicodeError) 对象时抛出 [`TypeError`](https://docs.python.org/zh-cn/3/builtins/exceptions.html#TypeError) 异常。（由Bénédikt Tran在 [gh-127691](https://github.com/python/cpython/issues/127691) 中贡献）

-

解释器在将对象加载到操作数栈时，会通过尽可能 [借用](https://docs.python.org/zh-cn/3/glossary.html#term-borrowed-reference) 引用来避免部分引用计数的修改。 这可能导致引用计数值比先前 Python 版本更小。 之前通过检查 [`Py_REFCNT()`](https://docs.python.org/zh-cn/3/c-api/refcounting.html#c.Py_REFCNT) 是否为 `1` 来判断函数参数是否未被其他代码引用的 C 扩展 API，现在应改用更安全的替代方案 [`PyUnstable_Object_IsUniqueReferencedTemporary()`](https://docs.python.org/zh-cn/3/c-api/object.html#c.PyUnstable_Object_IsUniqueReferencedTemporary)。

-

以下私有函数已提升为公开 C API：

-

`_PyBytes_Join()`：[`PyBytes_Join()`](https://docs.python.org/zh-cn/3/c-api/bytes.html#c.PyBytes_Join)

-

`_PyLong_IsNegative()`：[`PyLong_IsNegative()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_IsNegative)

-

`_PyLong_IsPositive()`：[`PyLong_IsPositive()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_IsPositive)

-

`_PyLong_IsZero()`：[`PyLong_IsZero()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_IsZero)

-

`_PyLong_Sign()`：[`PyLong_GetSign()`](https://docs.python.org/zh-cn/3/c-api/long.html#c.PyLong_GetSign)

-

`_PyUnicodeWriter_Dealloc()`：[`PyUnicodeWriter_Discard()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_Discard)

-

`_PyUnicodeWriter_Finish()`：[`PyUnicodeWriter_Finish()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_Finish)

-

`_PyUnicodeWriter_Init()`: 使用 [`PyUnicodeWriter_Create()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_Create)

-

`_PyUnicodeWriter_Prepare()`: (无替代)

-

`_PyUnicodeWriter_PrepareKind()`: (无替代)

-

`_PyUnicodeWriter_WriteChar()`：[`PyUnicodeWriter_WriteChar()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteChar)

-

`_PyUnicodeWriter_WriteStr()`：[`PyUnicodeWriter_WriteStr()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteStr)

-

`_PyUnicodeWriter_WriteSubstring()`：[`PyUnicodeWriter_WriteSubstring()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicodeWriter_WriteSubstring)

-

`_PyUnicode_EQ()`：[`PyUnicode_Equal()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicode_Equal)

-

`_PyUnicode_Equal()`：[`PyUnicode_Equal()`](https://docs.python.org/zh-cn/3/c-api/unicode.html#c.PyUnicode_Equal)

-

`_Py_GetConfig()`: [`PyConfig_Get()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_Get) 和 [`PyConfig_GetInt()`](https://docs.python.org/zh-cn/3/c-api/init_config.html#c.PyConfig_GetInt)

-

`_Py_HashBytes()`: [`Py_HashBuffer()`](https://docs.python.org/zh-cn/3/c-api/hash.html#c.Py_HashBuffer)

-

`_Py_fopen_obj()`：[`Py_fopen()`](https://docs.python.org/zh-cn/3/c-api/sys.html#c.Py_fopen)

-

`PyMutex_IsLocked()` : [`PyMutex_IsLocked()`](https://docs.python.org/zh-cn/3/c-api/synchronization.html#c.PyMutex_IsLocked)

在 Python 3.13 和更早的版本中可以使用 [pythoncapi-compat project](https://github.com/python/pythoncapi-compat/) 来充分利用这些新函数。

## 3.14.1 中的重要变化

-

增加 [`PyUnstable_ThreadState_SetStackProtection()`](https://docs.python.org/zh-cn/3/c-api/threads.html#c.PyUnstable_ThreadState_SetStackProtection) 和 [`PyUnstable_ThreadState_ResetStackProtection()`](https://docs.python.org/zh-cn/3/c-api/threads.html#c.PyUnstable_ThreadState_ResetStackProtection) 函数用于设置 Python 线程状态的栈保护基准地址和栈保护大小。 （由 Victor Stinner 在 [gh-139653](https://github.com/python/cpython/issues/139653) 中贡献。）

## 3.14.5 中的重要变化

### gc

-

The incremental garbage collector shipped in Python 3.14.0-3.14.4 has been reverted back to the generational garbage collector from 3.13, due to a number of [reports](https://github.com/python/cpython/issues/142516) of significant memory pressure in production environments. See 垃圾收集 for details.
