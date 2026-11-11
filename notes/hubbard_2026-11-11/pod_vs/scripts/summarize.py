"""Table of the hub_cost reports with the fixed verdict (instructions 02:13 CET), no values. Reads *_report.jsonl.
Verdict per (L, steps):
  1. Aer exact finished (within 2 h) and |Aer - quimb at the largest chi that finished| <= 1e-3
  2. two neighbouring chis differ <= 1e-3, the larger chi's error estimate <= 1e-4, |checks| <= 1e-3
Rows run before the thread change (note line) are marked "16 thr"."""
import json
import sys
from collections import defaultdict

CHIS = [256, 512, 1024, 2048]


def load(paths):
    rows = []
    for p in paths:
        thr = "16 thr"
        for line in open(p):
            r = json.loads(line)
            if "note" in r:
                thr = "1/8 thr"
                continue
            r["_thr"] = thr
            r["_file"] = p.replace("\\", "/").split("/")[-1]
            rows.append(r)
    return rows


def main():
    rows = load(sys.argv[1:])
    by = defaultdict(list)
    for r in rows:
        by[(r["L"], r["steps"])].append(r)
    print("| L | steps | method | chi | seconds | threads | max bond | error est. | max diff to others | |sum Z| | |Sz| | note |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    verdicts = {}
    for key in sorted(by):
        done = {}
        for r in by[key]:
            if "seconds" not in r:
                print(f"| {key[0]} | {key[1]} | {r['method']} | {r.get('chi') or '-'} | - | - | - | - | - | - | - | {r.get('stopped')} |")
                continue
            tag = "aer" if r["method"] == "aer" else f"quimb{r['chi']}"
            done[tag] = r
            md = max(r.get("max_diff_to", {}).values(), default=None)
            ee = r.get("error_estimate")
            print(f"| {key[0]} | {key[1]} | {r['method']} | {r.get('chi') or '-'} | {r['seconds']} | {r['_thr']} | "
                  f"{r.get('max_bond')} | {'-' if ee is None else f'{ee:.1e}'} | {'-' if md is None else f'{md:.1e}'} | "
                  f"{abs(r['check_sum_z']):.1e} | {abs(r['check_sz']):.1e} | |")
        # differences between cases come from the later row's max_diff_to (keys like L20_s4_quimb512)
        def diff(a, b):
            ra, rb = done.get(a), done.get(b)
            pre = f"L{key[0]}_s{key[1]}_"
            for x, y in ((ra, b), (rb, a)):
                if x and (pre + y) in x.get("max_diff_to", {}):
                    return x["max_diff_to"][pre + y]
            return None
        qs = [c for c in CHIS if f"quimb{c}" in done]
        why = []
        ok1 = False
        if "aer" in done and qs:
            d = diff("aer", f"quimb{qs[-1]}")
            ok1 = d is not None and d <= 1e-3
            why.append(f"1: Aer vs chi {qs[-1]} {d:.1e}" if d is not None else "1: no diff")
        ok2 = False
        for lo, hi in zip(qs, qs[1:]):
            if CHIS.index(hi) - CHIS.index(lo) != 1:
                continue
            d = diff(f"quimb{lo}", f"quimb{hi}")
            r = done[f"quimb{hi}"]
            ee = r.get("error_estimate")
            c = max(abs(r["check_sum_z"]), abs(r["check_sz"]))
            if d is not None and d <= 1e-3 and ee is not None and ee <= 1e-4 and c <= 1e-3:
                ok2 = True
                why.append(f"2: chi {lo}/{hi} diff {d:.1e}, err {ee:.1e}, checks {c:.1e}")
                break
        verdicts[key] = ("検算できた" if (ok1 or ok2) else "検算できなかった", "; ".join(why) or "no finished pair")
    print()
    print("| L | steps | verdict | basis |")
    print("|---|---|---|---|")
    for key, (v, w) in sorted(verdicts.items()):
        print(f"| {key[0]} | {key[1]} | {v} | {w} |")


if __name__ == "__main__":
    main()
