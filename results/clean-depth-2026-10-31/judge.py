"""Judgement of clean_depth_note.md: L* at n = 40, 72 against the same day's n = 20, per hz (REACHED within 2 SE)."""
import json, math, os, sys
d = os.path.dirname(os.path.abspath(__file__))
s = json.load(open(os.path.join(d, "job", "echo_score.json")))
out = {}
for hz, w in sorted(s["walls"].items()):
    f = {x["n"]: (x["L_star"], x["se"]) for x in w["fits"]}
    l20, s20 = f[20]
    for n in (40, 72):
        L, se = f[n]
        v = "REACHED" if L >= l20 - 2 * math.sqrt(se ** 2 + s20 ** 2) else "SHORTER"
        out[f"hz{hz}_n{n}"] = dict(L_star=L, se=se, L_star_20=l20, se_20=s20, verdict=v)
        print(f"hz {hz} n {n}: L* {L:.2f} +- {se:.2f} against n = 20 {l20:.2f} +- {s20:.2f}: {v}")
vs = [v["verdict"] for v in out.values()]
overall = "REACHED in all 6" if all(v == "REACHED" for v in vs) else "SHORTER in all 6" if all(v == "SHORTER" for v in vs) else "mixed"
print("overall:", overall)
json.dump(dict(verdicts=out, overall=overall), open(os.path.join(d, "judgement.json"), "w"), indent=1)
