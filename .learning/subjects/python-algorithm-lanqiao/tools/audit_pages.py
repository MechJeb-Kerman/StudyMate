import glob
import io
import os
import re
import subprocess
import sys

# 自定位：这套工具跟着学科目录走，拷到哪台机器都能用（不写死绝对路径）。
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
PY = os.environ.get("STUDYMATE_PYTHON") or sys.executable


def _find_engine():
    """找引擎里的 check_lesson.py：先看环境变量，再从学科目录逐级往上找。"""
    env = os.environ.get("STUDYMATE_ENGINE")
    if env:
        return env
    d = SP
    for _ in range(8):
        parent = os.path.dirname(d)
        if not parent or parent == d:
            break
        d = parent
        cand = os.path.join(d, "dsh-home", "studymate", "engine", "scripts", "check_lesson.py")
        if os.path.isfile(cand):
            return cand
    raise SystemExit("找不到引擎的 check_lesson.py——请设 STUDYMATE_ENGINE 环境变量指向它")


ENG = _find_engine()

yama = io.open(SP + r"\curriculum.yaml", encoding="utf-8").read()
ids = re.findall(r"^\s*- id: '([^']+)'", yama, re.M)
kinds = dict(zip(ids, re.findall(r"^\s*kind: '([^']+)'", yama, re.M)))

rows = []
for path in sorted(glob.glob(SP + r"\lessons\*.html")):
    name = os.path.basename(path)
    m = re.match(r"^(\d{4})-(.+)\.html$", name)
    num, node = m.group(1), m.group(2)
    r = subprocess.run([PY, "-X", "utf8", "-B", ENG, path, "--subject", SP, "--node", node],
                       capture_output=True, text=True, encoding="utf-8")
    out = (r.stdout or "") + (r.stderr or "")
    fails = [l for l in out.splitlines() if l.startswith("FAIL")]
    opts = [l for l in out.splitlines() if "选项长度差" in l]
    rows.append((num, node, len(fails), len(opts), fails, opts))

clean = [r for r in rows if r[2] == 0 and r[3] == 0]
print("页面 %d 个，全干净 %d 个" % (len(rows), len(clean)))
print()
print("仍需处理：")
for num, node, nf, no, fails, opts in rows:
    if nf or no:
        tag = "缺 lab" if any("lab" in f for f in fails) else "其他"
        print("  %s %-32s FAIL %d 选项差 %d  [%s]" % (num, node, nf, no, tag))
        for f in fails:
            if "lab" not in f:
                print("        " + f[:150])

# check_lesson 只查 lab 目录在不在，不查里面的文件齐不齐——0021 少了 run_tests.py
# 却一直算「通过」，就是这么漏掉的。这里补一道完整性校验。
# 注意：tools.py 只在脚本真的 `from tools import` 时才要求（0003~0007、0016 不 import，
# 没有它是对的）；run_tests.py 则两侧都必须有，否则「从参考解目录直接跑」会失败。
print()
print("lab 完整性（两侧都要 run_tests.py；脚本 import tools 时才要 tools.py）：")
bad_lab = []


def wants_tools(d):
    pys = glob.glob(os.path.join(d, "*.py"))
    if not pys:
        return False
    for p in pys:
        if os.path.basename(p) == "tools.py":
            continue
        try:
            body = io.open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if re.search(r"^\s*(from tools import|import tools)", body, re.M):
            return True
    return False


for d in sorted(glob.glob(SP + r"\lab\0*")):
    base = os.path.basename(d)
    needs_tools = wants_tools(d)
    for side in (d, os.path.join(SP, "lab", "solutions", base)):
        label = "lab" if side == d else "solutions"
        if not os.path.isdir(side):
            bad_lab.append("%s %s/ 不存在" % (base, label))
            continue
        if not os.path.isfile(os.path.join(side, "run_tests.py")):
            bad_lab.append("%s %s/run_tests.py 缺失" % (base, label))
        if needs_tools and not os.path.isfile(os.path.join(side, "tools.py")):
            bad_lab.append("%s %s/tools.py 缺失（脚本里有 from tools import）" % (base, label))
if bad_lab:
    for line in bad_lab:
        print("  ！" + line)
else:
    print("  全部齐备")
print()
zs = sum(1 for p in glob.glob(SP + r"\lessons\*.quiz.json"))
print("正文 %d · 题库 %d · lab %d 套 · solutions %d 套" % (
    len(rows), zs,
    len(glob.glob(SP + r"\lab\0*")), len(glob.glob(SP + r"\lab\solutions\0*"))))
