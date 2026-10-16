<!-- archived by resource-scout
     title: Python 对自由线程的支持 free-threading（官方文档·中文）
     source: https://docs.python.org/zh-cn/3/howto/free-threading-python.html
-->

# Python 对自由线程的支持

从 3.13 发布版开始，CPython 支持 [free threading](https://docs.python.org/zh-cn/3/glossary.html#term-free-threading) 的 Python 构建，其禁用 [global interpreter lock](https://docs.python.org/zh-cn/3/glossary.html#term-global-interpreter-lock) (GIL)。自由线程化的执行允许在可用的 CPU 核心上并行运行线程，充分利用可用的处理能力。 尽管并非所有软件都能自动地从中受益，但是考虑到线程设计的程序在多核硬件上运行速度会更快。

某些第三方包，特别是带有 [extension module](https://docs.python.org/zh-cn/3/glossary.html#term-extension-module) 的包，可能尚不适用于自由线程构建版，并将重新启用 [GIL](https://docs.python.org/zh-cn/3/glossary.html#term-GIL)。

本文档描述了自由线程对 Python 代码的影响。请参阅 [自由线程的 C API 扩展支持](https://docs.python.org/zh-cn/3/howto/free-threading-extensions.html#freethreading-extensions-howto) 了解如何编写支持自由线程构建的 C 扩展。

参见

[**PEP 703**](https://peps.python.org/pep-0703/) —— 查阅《在 CPython 中使全局解释器锁成为可选项》以了解对自由线程 Python 的整体描述。

## 安装

从 Python 3.13 开始，官方 macOS 和 Windows 安装器提供了对可选安装自由线程 Python 二进制文件的支持。安装器可在 [https://www.python.org/downloads/](https://www.python.org/downloads/) 获取。

有关其他平台的信息，请参阅 [Installing a Free-Threaded Python](https://py-free-threading.github.io/installing-cpython/)，这是一份由社区维护的针对安装自由线程版 Python 的安装指南。

当从源码构建 CPython 时，应使用 [`--disable-gil`](https://docs.python.org/zh-cn/3/using/configure.html#cmdoption-disable-gil) 配置选项以构建自由线程 Python 解释器。

## 识别自由线程 Python

要判断当前解释器是否支持自由线程，可检查 [`python -VV`](https://docs.python.org/zh-cn/3/using/cmdline.html#cmdoption-V) 和 [`sys.version`](https://docs.python.org/zh-cn/3/library/sys.html#sys.version) 是否包含 "free-threading build"。新的 [`sys._is_gil_enabled()`](https://docs.python.org/zh-cn/3/library/sys.html#sys._is_gil_enabled) 函数可用于检查在运行进程中 GIL 是否确实被关闭。

`sysconfig.get_config_var("Py_GIL_DISABLED")` 配置变量可用于确定构建是否支持自由线程。 如果该变量设置为 `1`，则构建支持自由线程。这是与构建配置相关的决策的推荐机制。

## 自由线程版 Python 中的全局解释器锁

CPython 的自由线程构建版支持在运行时使用环境变量 [`PYTHON_GIL`](https://docs.python.org/zh-cn/3/using/cmdline.html#envvar-PYTHON_GIL) 或命令行选项 [`-X gil`](https://docs.python.org/zh-cn/3/using/cmdline.html#cmdoption-X) 选择性地启用 GIL。

GIL 也可能在导入未显式标记为支持自由线程模式的 C-API 扩展模块时被自动启用。在这种情况下将会打印一条警告。

在单独软件包的文档以外，还有下列网站在追踪热门软件包对自由线程模式的支持状态：

-

[https://py-free-threading.github.io/tracking/](https://py-free-threading.github.io/tracking/)

-

[https://hugovk.github.io/free-threaded-wheels/](https://hugovk.github.io/free-threaded-wheels/)

## 线程安全

The free-threaded build of CPython aims to provide similar thread-safety behavior at the Python level to the default GIL-enabled build.Built-in types like [`dict`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#dict), [`list`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#list), and [`set`](https://docs.python.org/zh-cn/3/builtins/stdtypes.html#set) use internal locks to protect against concurrent modifications in ways that behave similarly to the GIL.
See [Thread Safety Guarantees](https://docs.python.org/zh-cn/3/builtins/threadsafety.html#threadsafety) for the guarantees provided by built-in types.

备注

建议尽可能使用 [`threading.Lock`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Lock) 或其他同步原语，而不是依赖内置类型的内部锁。

## 已知的限制

本节介绍自由线程 CPython 构建的已知限制。

### 永生化

在自由线程构建中，某些对象属于 [immortal](https://docs.python.org/zh-cn/3/glossary.html#term-immortal) 对象。永生对象不会被释放且具有永远不会被修改的引用计数。 这样做是为了避免发生可能妨碍高效的多线程伸缩调整的引用计数争夺问题。

对于 3.14 发布版，永生对象只限于：

-

代码常量：数字字面值，字符串字面值，以及由其他常量组成的元组字面值。

-

由 [`sys.intern()`](https://docs.python.org/zh-cn/3/library/sys.html#sys.intern) 所内化的字符串。

### 帧对象

从一个 [帧对象](https://docs.python.org/zh-cn/3/reference/datamodel.html#frame-objects) 访问 [`frame.f_locals`](https://docs.python.org/zh-cn/3/reference/datamodel.html#frame.f_locals) 是不安全的，如果该帧目前是在另一个线程中执行的话，这样做可能会导致解释器崩溃。

### 迭代器

从多个线程并发地访问同一个迭代器对象通常不是线程安全的，可能导致各个线程中出现重复或丢失的元素。

### 单线程性能

自由线程构建在执行 Python 代码时相比默认启用 GIL 的构建会有额外的开销。具体的开销取决于工作量和硬件环境。在 pyperformance 基准测试套件中，平均开销增幅在 macOS aarch64 上约为 1% 而在 x86-64 Linux 系统上约为 8%。

## 行为的变化

本节描述 CPython 在自由线程构建时的行为变化。

### 上下文变量

在自由线程构建中，[`thread_inherit_context`](https://docs.python.org/zh-cn/3/library/sys.html#sys.flags.thread_inherit_context) 标志默认设置为 true，这会导致使用 [`threading.Thread`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Thread) 创建的线程以 [`start()`](https://docs.python.org/zh-cn/3/library/threading.html#threading.Thread.start) 的调用程序的 [`Context()`](https://docs.python.org/zh-cn/3/library/contextvars.html#contextvars.Context) 的副本启动。在默认启用 GIL 的构建中，该标志默认为 false，因此线程以空 `Context()` 启动。

### 警告过滤器

在自由线程构建中，[`context_aware_warnings`](https://docs.python.org/zh-cn/3/library/sys.html#sys.flags.context_aware_warnings) 标志默认设置为 true。在默认启用 GIL 的构建中，该标志默认设置为 false。如果该标志为 true，则 [`warnings.catch_warnings`](https://docs.python.org/zh-cn/3/library/warnings.html#warnings.catch_warnings) 上下文管理器使用上下文变量用于警告过滤器。如果该标志为 false，则 `catch_warnings` 修改全局过滤器列表，这不是线程安全的。详情请参阅 [`warnings`](https://docs.python.org/zh-cn/3/library/warnings.html#module-warnings) 模块。

### 增加的内存使用

自由线程构建版相比默认构建版通常会使用更多内存。 这有很多原因，大部分是由于设计上的决定。

#### 所有内生字符串都是永生对象

对于现代的 Python 版本（从 2.3 版开始），内生字符串 (例如通过 [`sys.intern()`](https://docs.python.org/zh-cn/3/library/sys.html#sys.intern)) 不会使它成为永生对象。 作为替代，如果对某字符串的最后一次引用消失，它将从内生字符串表中移除。 对于自由线程构建版来说则并非如此而是任何内生字符串都将成为永生对象，会保持存活直到解释器关闭。

#### 非 GC 对象具有更大的对象标头

The free-threaded build uses a different [`PyObject`](https://docs.python.org/zh-cn/3/c-api/structures.html#c.PyObject) structure. Instead of having the GC related information allocated before the `PyObject` structure, like in the default build, the GC related info is part of the normal object header. For example, on the AMD64 platform, `None` uses 32 bytes on the free-threaded build vs 16 bytes for the default build. GC objects (such as dicts and lists) are the same size for both builds since the free-threaded build does not use additional space for the GC info.

#### QSBR can delay freeing of memory

In order to safely implement lock-free data structures, a safe memory reclamation (SMR) scheme is used, known as quiescent state-based reclamation (QSBR).This means that the memory backing data structures allowing lock-free access will use QSBR, which defers the free operation, rather than immediately freeing the memory.Two examples of these data structures are the list object and the dictionary keys object.
See `InternalDocs/qsbr.md` in the CPython source tree for more details on how QSBR is implemented.Running [`gc.collect()`](https://docs.python.org/zh-cn/3/library/gc.html#gc.collect) should cause all memory being held by QSBR to be actually freed.Note that even when QSBR frees the memory, the underlying memory allocator may not immediately return that memory to the OS and so the resident set size (RSS) of the process might not decrease.

#### mimalloc allocator vs pymalloc

The default build will normally use the "pymalloc" memory allocator for small allocations (512 bytes or smaller). The free-threaded build does not use pymalloc and allocates all Python objects using the "mimalloc" allocator. The pymalloc allocator has the following properties that help keep memory usage low: small per-allocated-block overhead, effective memory fragmentation prevention, and quick return of free memory to the operating system. The mimalloc allocator does quite well in these respects as well but can have some more overhead.

In the free-threaded build, mimalloc manages memory in a number of separate heaps (currently four).For example, all GC supporting objects are allocated from their own heap.Using separate heaps means that free memory in one heap cannot be used for an allocation that uses another heap.Also, some heaps are configured to use QSBR (quiescent-state based reclamation) when freeing the memory that backs up the heap (known as "pages" in mimalloc terminology).
The use of QSBR creates a delay between all memory blocks for a page being freed and the memory page being released, either for new allocations or back to the OS.

The mimalloc allocator also defers returning freed memory back to the OS. You can reduce that delay by setting the environment variable `MIMALLOC_PURGE_DELAY` to `0`. Note that this will likely reduce the performance of the allocator.

#### Free-threaded reference counting can cause objects to live longer

In the default build, when an object's reference count reaches zero, it is normally deallocated. The free-threaded build uses "biased reference counting", with a fast-path for objects "owned" by the current thread and a slow path for other objects. See [**PEP 703**](https://peps.python.org/pep-0703/) for additional details. Any time an object's reference count ends up in a "queued" state, deallocation can be deferred. The queued state is cleared from the "eval breaker" section of the bytecode evaluator.

The free-threaded build also allows a different mode of reference counting, known as "deferred reference counting". This mode is enabled by setting a flag on a per-object basis. Deferred reference counting is enabled for the following types:

-

module objects

-

module top-level functions

-

class methods defined in the class scope

-

descriptor objects

-

thread-local objects, created by [`threading.local`](https://docs.python.org/zh-cn/3/library/threading.html#threading.local)

When deferred reference counting is enabled, references from Python function stacks are not added to the reference count.This scheme reduces the overhead of reference counting, especially for objects used from multiple threads.Because the stack references are not counted, objects with deferred reference counting are not immediately freed when their internal reference count goes to zero.Instead, they are examined by the next GC run and, if no stack references to them are found, they are freed.
This means these objects are freed by the GC and not when their reference count goes to zero, as is typical.

#### Per-thread reference counting can delay freeing objects

To avoid contention on the reference count fields of frequently shared objects, the free-threaded build also uses "per-thread reference counting" for a few selected object types. Rather than updating a single shared reference count, each thread maintains its own local reference count array, indexed by a unique id assigned to the object. The true reference count is only computed by summing the per-thread counts when the object's local count drops to zero. Per-thread reference counting is currently used for:

-

heap type objects (classes created in Python)

-

代码对象

-

模块对象的 `__dict__`

由于对象的每线程计数必须在释放前合并回对象，使用每线程引用计数的对象通常会比在默认构建中更晚被释放。 具体而言，这样的对象往往要等到引用它的线程处于安全点位（例如，在字节码求值器的 "eval breaker" 节中）或退出时才会被释放。 运行 [`gc.collect()`](https://docs.python.org/zh-cn/3/library/gc.html#gc.collect) 将合并每线程计数并允许这些对象被释放。
