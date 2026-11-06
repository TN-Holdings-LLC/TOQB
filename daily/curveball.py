"""Task Y (owner 2026-11-06): choosing the "curveball" problems from the grid daily/pool.CURVE by fixed rules, from the
exact answers alone (never from a device result). Committed before any answer of the grid is computed.

Rules (per rule group and per t; one problem each, so at most 8):
  Y-F1, Y-F2  eligible if 0.35 <= M_exact <= 0.65; choose the smallest |M_exact - 0.5|; tie: the smaller angle.
  Y-F4s       choose the largest per-qubit spread (population standard deviation of the exact values); tie: the
              smaller theta0, then the smaller delta.
  Y-F4m       eligible if the share of qubits with a negative exact value is between 0.25 and 0.75; choose the largest
              mean |exact value|; tie: the smaller theta0, then the smaller delta.
A (group, t) with no eligible candidate chooses nothing (recorded as such; no rule is relaxed).
Ties are decided exactly as written; values are compared after rounding to 1e-9.

The guess table for each chosen problem: MSE of all 0, all 1, all M_exact (an oracle guess, for reference), and of the
exact answers scaled by 0.8 (a device that keeps 0.8 of every value) with 4000-shot noise added
(mean((1 - (0.8 a)^2) / 4000)); "beats" compares the last with the better of all 0 and all 1 (the BEATS rule).

usage: python daily/curveball.py select ANSWERS.json [ANSWERS.json ...] OUT.json
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from daily import pool as P  # noqa: E402

SHOTS = 4000
RET = 0.8


def stats(values):
    a = np.array([v for v in values if v is not None], dtype=float)
    return dict(n=int(len(a)), M=float(a.mean()), spread=float(a.std()), neg_share=float((a < 0).mean()),
                mean_abs=float(np.abs(a).mean()))


def guesses(values):
    a = np.array([v for v in values if v is not None], dtype=float)
    g0, g1, gm = float(np.mean(a ** 2)), float(np.mean((1 - a) ** 2)), float(np.var(a))
    dev = float(np.mean((RET * a - a) ** 2) + np.mean((1 - (RET * a) ** 2) / SHOTS))
    best = min(g0, g1)
    return dict(all_0=g0, all_1=g1, all_M_exact=gm, scaled_0_8_with_shots=dev, better_trivial=best,
                beats_expected=dev < best, margin=best - dev)


def r9(x):
    return round(float(x), 9)


def select(answers):
    """answers: {ID: {label: value}} (or the sealed record with "values"). Returns dict(chosen, table)."""
    vals = {}
    for pid, rec in answers.items():
        if pid in P.CURVE_GROUP:
            v = rec["values"] if isinstance(rec, dict) and "values" in rec else rec
            vals[pid] = list(v.values())
    table, chosen = [], []
    for pid in sorted(vals):
        _, fam, pa, par, t, layers, g = P.entry(pid)
        table.append(dict(id=pid, group=P.CURVE_GROUP[pid], family=fam, patch=pa, params=par, t=t, **stats(vals[pid])))
    by = {}
    for row in table:
        by.setdefault((row["group"], row["t"]), []).append(row)
    for (grp, t), rows in sorted(by.items()):
        if grp in ("Y-F1", "Y-F2"):
            ok = [r for r in rows if 0.35 <= r["M"] <= 0.65]
            angle = "theta_x" if grp == "Y-F1" else "theta"
            key = lambda r: (r9(abs(r["M"] - 0.5)), r["params"][angle])
        elif grp == "Y-F4s":
            ok = rows
            key = lambda r: (-r9(r["spread"]), r["params"]["theta0"], r["params"]["delta"])
        else:
            ok = [r for r in rows if 0.25 <= r["neg_share"] <= 0.75]
            key = lambda r: (-r9(r["mean_abs"]), r["params"]["theta0"], r["params"]["delta"])
        if not ok:
            chosen.append(dict(group=grp, t=t, id=None, why="no eligible candidate"))
            continue
        best = sorted(ok, key=key)[0]
        chosen.append(dict(group=grp, t=t, id=best["id"], params=best["params"], M=best["M"], spread=best["spread"],
                           neg_share=best["neg_share"], mean_abs=best["mean_abs"],
                           guesses=guesses(vals[best["id"]]), candidates=len(rows), eligible=len(ok)))
    return dict(chosen=chosen, table=table)


def md(res):
    lines = ["| group | t | chosen | params | M_exact | spread | negative share | all 0 | all 1 | all M_exact | 0.8 x exact + shots | beats expected |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in res["chosen"]:
        if c["id"] is None:
            lines.append(f"| {c['group']} | {c['t']} | none ({c['why']}) |  |  |  |  |  |  |  |  |  |")
            continue
        g = c["guesses"]
        lines.append(f"| {c['group']} | {c['t']} | {c['id']} | {P.params_text(c['params'])} | {c['M']:.3f} | {c['spread']:.3f} | "
                     f"{c['neg_share']:.2f} | {g['all_0']:.4f} | {g['all_1']:.4f} | {g['all_M_exact']:.4f} | "
                     f"{g['scaled_0_8_with_shots']:.4f} | {'yes' if g['beats_expected'] else 'no'} |")
    return "\n".join(lines)


if __name__ == "__main__":
    if sys.argv[1] != "select":
        raise SystemExit(__doc__)
    merged = {}
    for f in sys.argv[2:-1]:
        merged.update(json.load(open(f)))
    res = select(merged)
    json.dump(res, open(sys.argv[-1], "w"), indent=1)
    print(md(res))
