import io
import json
import os
import sys

node = sys.argv[1]
sp = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
q = json.load(io.open(sp + r"\lessons\%s.quiz.json" % node, encoding="utf-8"))
for k, v in q.items():
    for it in v:
        L = [len(o) for o in it["opts"]]
        if max(L) - min(L) > 4:
            print("%s   差 %d" % (k, max(L) - min(L)))
            for o, n in zip(it["opts"], L):
                print("   %2d  %s" % (n, o))
            print()
