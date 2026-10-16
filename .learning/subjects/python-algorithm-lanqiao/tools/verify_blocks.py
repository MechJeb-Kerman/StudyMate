import io
import os
import re
import subprocess
import sys

# 自定位：工具跟着学科目录走（不写死绝对路径）。
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
PY = os.environ.get("STUDYMATE_PYTHON") or sys.executable
node = sys.argv[1]
MD = os.path.join(SP, "lessons", "%s.md" % node)
md = io.open(MD, encoding="utf-8").read()
seq = [(m.group(1), m.group(2)) for m in re.finditer(r"```(python|text)\n(.*?)```", md, re.S)]
npyt = 0
plan = []
for kind, body in seq:
    if kind == "python":
        npyt += 1
    else:
        plan.append((npyt, body))
cache = {}


def run(n):
    if n not in cache:
        blocks = [b for k, b in seq if k == "python"][:n]
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_last_blocks.py")
        io.open(p, "w", encoding="utf-8", newline="\n").write("\n\n".join(blocks))
        r = subprocess.run([PY, "-X", "utf8", "-B", p], capture_output=True, text=True, encoding="utf-8")
        cache[n] = (r.stdout or "") + (r.stderr or "")
    return cache[n]


allok = True
for i, (n, body) in enumerate(plan, 1):
    out = run(n)
    lines = [x for x in body.strip().splitlines() if x.strip()]
    miss = [x for x in lines if x not in out]
    ok = not miss
    allok = allok and ok
    print(("  OK   " if ok else "  不符 ") + "text 块%d（前 %d 段代码）" % (i, n) + ("" if ok else "\n        缺: %r" % (miss,)))
print()
print("python 块", npyt, " text 块", len(plan), " 全部一致:", allok)
print()
print("=== 完整输出 ===")
print(run(npyt).rstrip())
