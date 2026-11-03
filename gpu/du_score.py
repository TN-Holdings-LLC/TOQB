# Score P4 per prereg/drafts-2026-11-03/du_repro_note.md (judgements 1-4 and the reported items).
import json, sys
import numpy as np
from psf_os import dual as DU, sentinel
OUT = sys.argv[1]
res = {}
for tag in "SV":
    jd, runs = f"{OUT}/{tag}/job", f"{OUT}/{tag}/runs"
    sc = DU.score(jd, runs)
    sv = sentinel.verdict(jd, runs)
    raw = json.load(open(f"{jd}/raw_counts.json"))
    by_h = {s["h"]: s for s in sc.values()}
    on = [(r["on"], r["on_se"], r["exact"], h, r["t"]) for h, s in by_h.items() for r in s["rows"] if r["t"] >= 1]
    m = np.array([x[0] for x in on]); se = np.array([x[1] for x in on]); ex = np.array([x[2] for x in on])
    mse, msq = float(np.mean((m - ex) ** 2)), float(np.mean(ex ** 2))
    frac = m / ex
    rate = {}
    for h in (0.05, 0.1, 0.15):
        a = {r["t"]: r for r in by_h[h]["rows"]}; b = {r["t"]: r for r in by_h[0.0]["rows"]}
        ts = np.arange(1, 11)
        y = np.array([np.log(a[t]["on"] / b[t]["on"]) for t in ts])
        var = np.array([(a[t]["on_se"] / a[t]["on"]) ** 2 + (b[t]["on_se"] / b[t]["on"]) ** 2 for t in ts])
        w = 1 / var
        lk = float(np.sum(w * ts * y) / np.sum(w * ts ** 2)); slk = float(1 / np.sqrt(np.sum(w * ts ** 2)))
        k, sk = float(np.exp(lk)), float(np.exp(lk) * slk)
        ck = float(np.cos(2 * h))
        rate[h] = dict(k=k, se=sk, cos2h=ck, diff=k - ck,
                       verdict="AGREES" if abs(k - ck) <= max(2 * sk, 0.005) else "DIFFERS",
                       ratio=[float(np.exp(v)) for v in y])
    res[tag] = dict(sentinel=sv["status"], sentinel_runs={c: v.get("runs") for c, v in sv["cells"].items()},
                    mse=mse, mean_square_exact=msq, reads="READS" if mse <= msq / 2 else "DOES NOT READ",
                    recovered_mean=float(frac.mean()), recovered_se=float(np.sqrt(np.sum((se / ex) ** 2)) / len(ex)),
                    rate=rate, metrics=raw.get("metrics"),
                    per_h={h: dict(t=[r["t"] for r in s["rows"]], on=[round(r["on"], 4) for r in s["rows"]],
                                   exact=[round(r["exact"], 4) for r in s["rows"]],
                                   off_mean=[round(r["off_mean_abs"], 4) for r in s["rows"]],
                                   off_max=[round(r["off_max_abs"], 4) for r in s["rows"]]) for h, s in by_h.items()},
                    chain=next(iter(sc.values()))["chain"])
d = res["V"]["recovered_mean"] - res["S"]["recovered_mean"]
sd = float(np.hypot(res["V"]["recovered_se"], res["S"]["recovered_se"]))
res["V_minus_S"] = dict(diff=d, se=sd, note="S and V are the same chain (byte-identical circuits): not comparable")
json.dump(res, open(f"{OUT}/scores.json", "w"), indent=1, default=str)
for tag in "SV":
    r = res[tag]
    print(tag, "sentinel", r["sentinel"], "| MSE", round(r["mse"], 4), "msq", round(r["mean_square_exact"], 4), r["reads"],
          "| recovered", round(r["recovered_mean"], 3), "+-", round(r["recovered_se"], 3))
    for h, v in r["rate"].items():
        print("   rate h", h, "k", round(v["k"], 4), "+-", round(v["se"], 4), "cos2h", round(v["cos2h"], 4), v["verdict"])
    for h, v in sorted(r["per_h"].items()):
        print("   h", h, "on", v["on"]); print("        exact", v["exact"]); print("        offmax", v["off_max"])
print("V-S", round(d, 4), "+-", round(sd, 4))
print("sentinel runs", res["S"]["sentinel_runs"], res["V"]["sentinel_runs"])
