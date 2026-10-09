"""What the circuit breakers of amendment 1 would have changed in earlier runs (for the amendment's disclosure), and
the bound on a run with the same reference times. Reads records.jsonl of each directory; scores nothing.

    python -m toqb.cap_effect DIR [DIR ...] [--par 4]
"""
import argparse
import json
import os

from toqb.runner import REFERENCE, B10_CAP_S, BUDGET_FLOOR_S, bound_s, budgets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--par", type=int, default=4)
    a = ap.parse_args()
    for d in a.dirs:
        recs = []
        for ln in open(os.path.join(d, "records.jsonl"), encoding="utf-8"):
            try:
                x = json.loads(ln)
            except ValueError:
                continue  # a line cut short
            if "adapter" in x:
                recs.append(x)
        ref = {r["case"]: r["t_s"] for r in recs if r["adapter"] == REFERENCE and "t_s" in r and "error" not in r}
        slow = sorted((t, c) for c, t in ref.items() if 10 * max(BUDGET_FLOOR_S, t) > B10_CAP_S)
        print(f"== {d}: {len(recs)} records, {len(ref)} reference times")
        print(f"tests whose reference took over {B10_CAP_S / 10:g} s (the cap is below 10x there): {len(slow)}")
        for t, c in slow:
            print(f"  {t:8.1f} s  {c[3:80]}")
        print("measurements the breakers would have stopped (time over the largest budget), by compiler:")
        by = {}
        for r in recs:
            if r["adapter"] == REFERENCE or r["case"] not in ref or "t_s" not in r:
                continue
            b10 = budgets(ref[r["case"]])[10.0]
            if r["t_s"] > b10:
                by.setdefault(r["adapter"], []).append((r["t_s"], b10, r["case"]))
        for ad, xs in sorted(by.items()):
            worst = "".join(f"\n    {t:8.1f} s > {b:6.1f} s  {c[3:70]}" for t, b, c in sorted(xs)[-5:])
            print(f"  {ad}: {len(xs)}" + worst)
        others = len({r["adapter"] for r in recs if r["adapter"] != REFERENCE}) or 5
        bound = sum(bound_s(budgets(t)[10.0]) for t in ref.values()) * others / a.par
        print(f"bound on the measurements after the references, with these reference times: {bound:.0f} s "
              f"({bound / 3600:.1f} h; {len(ref)} tests x {others} compilers, {a.par} at a time)")


if __name__ == "__main__":
    main()
