import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import json, math, sys
sys.path.insert(0, f'{ROOT}/voice')
from lines import LINES
V = json.load(open(f'{ROOT}/voice/voice.json'))
EV = json.load(open(f'{ROOT}/rec/events.json'))
FPS = 30
LIVE_FRAMES = int(sys.argv[1])
GAP = 0.35
fl = lambda x: math.floor(x * FPS) / FPS

starts = {}
t = 0.4
for k in ("i1", "i2", "i3", "i4"):
    starts[k] = t; t += V[k]["dur"] + GAP
TI = math.ceil((t + 0.2) * FPS) / FPS
LIVE = LIVE_FRAMES / FPS
for k, b in EV["beats"].items(): starts[k] = TI + b + 0.15
TC = TI + LIVE
t = TC + 0.4
for k in ("c1", "c2", "c3", "c4"):
    starts[k] = t; t += V[k]["dur"] + (0.6 if k == "c1" else GAP)
TOTAL = math.ceil((t + 1.0) * FPS) / FPS

order = [k for k, _ in LINES]
for a, b in zip(order, order[1:]):
    slack = starts[b] - (starts[a] + V[a]["dur"])
    print(a, "%.2f" % starts[a], "slack %.2f" % slack, "OVER" if slack < 0.1 else "")

def chunks(tokens):
    n = len(tokens)
    L = [len(x[2]) for x in tokens]
    total = sum(L) + n - 1
    m = max(1, math.ceil(total / 30))
    target = total / m
    best = {0: (0, [])}
    for j in range(1, n + 1):
        cand = None
        for i in range(max(0, j - 9), j):
            if i not in best: continue
            ln = sum(L[i:j]) + (j - i - 1)
            if ln > 34 and j - i > 1: continue
            cost = best[i][0] + (ln - target) ** 2
            if j < n and tokens[j - 1][2][-1] in ".,:": cost -= 60
            if j < n and tokens[j - 1][2].lower() in ("a", "the", "of", "to", "and", "her", "is", "one", "in"): cost += 40
            if cand is None or cost < cand[0]: cand = (cost, best[i][1] + [(i, j)])
        if cand: best[j] = cand
    return best[n][1]

subs, words = [], {}
for k in order:
    v = V[k]
    disp = v["text"].split()
    assert len(disp) == len(v["words"]), k
    toks = [[starts[k] + w[0], starts[k] + w[0] + w[1], d] for w, d in zip(v["words"], disp)]
    words[k] = [[x[0], x[2].strip(".,:").lower()] for x in toks]
    merged, i = [], 0
    while i < len(toks):
        if toks[i][2] == "eighty-four" and toks[i + 1][2] == "oh":
            tail = toks[i + 2][2][5:]
            merged.append([toks[i][0], toks[i + 2][1], "8403" + tail]); i += 3
        else:
            merged.append(toks[i]); i += 1
    for a, b in chunks(merged):
        subs.append({"t0": merged[a][0] - 0.12, "line": k, "words": merged[a:b]})
for a, b in zip(subs, subs[1:]): a["t1"] = b["t0"]
subs[-1]["t1"] = TOTAL
for s in subs: print("%6.2f" % s["t0"], " ".join(w[2] for w in s["words"]))

TL = {"TI": TI, "LIVE": LIVE, "TC": TC, "TOTAL": TOTAL, "starts": starts, "durs": {k: V[k]["dur"] for k in order},
      "subs": subs, "words": words, "cmd": EV["cmd"], "beats": EV["beats"], "roots": EV["roots"], "two": EV["two"], "window": EV["window"], "notes": dict(EV["notes"])}
json.dump(TL, open(f'{ROOT}/rec/timeline.json', 'w'))
print("TI %.3f LIVE %.3f TC %.3f TOTAL %.3f frames %d" % (TI, LIVE, TC, TOTAL, round(TOTAL * FPS)))
