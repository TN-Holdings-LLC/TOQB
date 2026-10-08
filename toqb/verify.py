"""An independent re-scoring of a standard run: recomputes the numbers that the predictions use straight from
records.jsonl, without toqb.runner or toqb.score, and compares them with score.json.

    python -m toqb.verify --out DIR
"""
import argparse
import json
import math
import os

KEYS = ("qiskit:2:target", "qiskit:1:target", "qiskit:3:target", "tket:2", "psf:default", "psf:recommended")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = ap.parse_args().out
    lines = [json.loads(x) for x in open(os.path.join(out, "records.jsonl"), encoding="utf-8")]
    meta = next(x["meta"] for x in lines if "meta" in x)
    recs = [x for x in lines if "adapter" in x]
    S = json.load(open(os.path.join(out, "score.json"), encoding="utf-8"))
    ref_name, floor, tiers = meta["reference"], meta["floor_s"], meta["tiers"]
    ref = {}
    for r in recs:
        if r["adapter"] == ref_name:
            ref[r["case"]] = r

    def bad_eq(r):
        e = r.get("equivalence") or {}
        return e.get("checked") is True and e.get("equivalent") is False

    def good(r):
        return "error" not in r and r.get("valid") is True and not bad_eq(r)

    mine = {}
    for a in KEYS:
        rs = [r for r in recs if r["adapter"] == a]
        base = [r for r in rs if "t_s" in ref.get(r["case"], {})]
        share = {}
        for t in tiers:
            hit = [good(r) and r["t_s"] <= t * max(floor, ref[r["case"]]["t_s"]) for r in base]
            share[t] = sum(hit) / len(hit) if hit else float("nan")
        logs = [math.log((r["q2"] + 1) / (ref[r["case"]]["q2"] + 1)) for r in rs
                if r["case"] in ref and good(r) and good(ref[r["case"]])]
        torino = [r for r in rs if ("FakeTorino" in r["case"] or "hamlib_hamiltonians" in r["case"]
                                    or "feynman" in r["case"]) and "error" not in r]
        mine[a] = dict(within=share, q_all=math.exp(sum(logs) / len(logs)) if logs else float("nan"),
                       n=len(logs), invalid=sum(r.get("valid") is False for r in rs),
                       not_equivalent=sum(bad_eq(r) for r in rs),
                       on_failed=sum((r.get("on_failed") or 0) > 0 for r in torino),
                       failed_share=(sum("error" in r for r in base) / len(base)) if base else float("nan"))

    def same(x, y):
        if isinstance(x, float) and math.isnan(x):
            return isinstance(y, float) and math.isnan(y) or y in ("NaN", None)
        return abs(x - y) < 1e-9

    problems = []
    for a in KEYS:
        s = S["adapters"][a]
        for t in tiers:
            if not same(mine[a]["within"][t], s["within"][str(t)]):
                problems.append(f"{a} within {t}: {mine[a]['within'][t]} vs {s['within'][str(t)]}")
        for k, sk in (("q_all", "q_all"), ("n", "q_all_n"), ("invalid", "invalid"),
                      ("not_equivalent", "not_equivalent"), ("on_failed", "torino_tests_on_failed")):
            v, w = mine[a][k], s[sk]
            if not (same(float(v), float(w)) if not isinstance(w, str) else False):
                problems.append(f"{a} {k}: {v} vs {w}")
    p = S["predictions"]
    if not same(mine["psf:default"]["failed_share"], p["T6"]["value"]):
        problems.append(f"T6: {mine['psf:default']['failed_share']} vs {p['T6']['value']}")
    print(f"verify: {len(recs)} records; {len(problems)} differences")
    for x in problems:
        print("  " + x)
    print("VERIFY " + ("PASS" if not problems else "FAIL"))


if __name__ == "__main__":
    main()
