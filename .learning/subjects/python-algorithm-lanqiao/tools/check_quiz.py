import io
import json
import os
import re
import sys

node = sys.argv[1]
sp = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
md = io.open(sp + r"\lessons\%s.md" % node, encoding="utf-8").read()
q = json.load(io.open(sp + r"\lessons\%s.quiz.json" % node, encoding="utf-8"))
a = re.findall(r"^::: quiz .*?锚点：(.+)$", md, re.M)
print("  锚点", len(a), "/ 键", len(q))
print("  缺失:", [x for x in a if x not in q] or "无")
print("  多余:", [k for k in q if k not in a] or "无")
bad = 0
for k, v in q.items():
    for it in v:
        if "`" in it["q"]:
            print("  q 里有反引号:", k)
            bad += 1
        L = [len(o) for o in it["opts"]]
        if max(L) - min(L) > 4:
            print("  长度差 %d: %s (%d/%d)" % (max(L) - min(L), k, max(L), min(L)))
            bad += 1
print("  违规", bad)
for lvl, h in re.findall(r"^(#{2,3}) (.+)$", md, re.M):
    if len(h) > 14:
        print("  标题过长:", h)
print("  引用块:", "有" if re.search(r"^> ", md, re.M) else "无")
print("  未教写法:", [w for w in ["lambda", "defaultdict", "Counter", "heapq", "itertools"] if w in md] or "无")
