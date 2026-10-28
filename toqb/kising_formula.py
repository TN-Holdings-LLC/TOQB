"""The formula prediction of device test D7 (2026-10-28): one uniform depolarizing rate p is fitted on the device's
kicked Ising ring at a reference n, and the noisy free-fermion recursion (`kising.x0_noisy`) then predicts the slope
lam at the other n, with no twin and no calibration data.

    python -m toqb.kising_formula JOB RUNS [--ref-n 20]       (after `lam_device score JOB RUNS`)

For a cell with inputs s_i (from its run record) the formula's slope is lam_f(p) = least-squares slope of
SIGN * x0_noisy(s_i, n, L, h, p) on the exact noiseless z_i. At the reference n, p is the root of
lam_f(p) = lam_device (bisection on [0, 0.1]); its range comes from lam_device +- SE. At every other n:
lam_pred = lam_f(p), SE_pred = half the spread of lam_f over that range, and the declared rule
AGREE if |lam_device - lam_pred| <= 2 sqrt(SE_device^2 + SE_pred^2), else BELOW or ABOVE.
Writes JOB/formula_score.json (never overwritten).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from toqb import kising as K


def lam_formula(inputs, zl, n, L, h, p):
    zf = np.array([K.SIGN_OF_READOUT * K.x0_noisy(s, n, [L], h, p)[L] for s in inputs])
    return float(np.polyfit(np.asarray(zl, float), zf, 1)[0])


def fit_p(target, inputs, zl, n, L, h, lo=0.0, hi=0.1, tol=1e-7):
    """p with lam_formula(p) = target; None if target lies outside [lam_f(hi), lam_f(lo)]."""
    flo, fhi = lam_formula(inputs, zl, n, L, h, lo), lam_formula(inputs, zl, n, L, h, hi)
    if not (fhi <= target <= flo):
        return None
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if lam_formula(inputs, zl, n, L, h, mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def predict(cells, ref_n=20):
    """cells: dicts with n, L, h, inputs, noiseless_z, lam, se (device). Returns the reference fit and the verdicts."""
    ref = [c for c in cells if c["n"] == ref_n]
    if len(ref) != 1:
        raise SystemExit(f"STOP: need exactly one cell at the reference n = {ref_n}")
    r = ref[0]
    args = (r["inputs"], r["noiseless_z"], r["n"], r["L"], r["h"])
    p = fit_p(r["lam"], *args)
    p_lo, p_hi = fit_p(r["lam"] + r["se"], *args), fit_p(r["lam"] - r["se"], *args)
    out = dict(ref=dict(n=ref_n, lam=r["lam"], se=r["se"], p=p, p_range=[p_lo, p_hi]), cells=[])
    if p is None:
        out["ref"]["note"] = "the device lam lies outside the formula's range for p in [0, 0.1]; no prediction"
        return out
    for c in cells:
        if c["n"] == ref_n:
            continue
        a = (c["inputs"], c["noiseless_z"], c["n"], c["L"], c["h"])
        lp = lam_formula(*a, p)
        ends = [lam_formula(*a, q) for q in (p_lo, p_hi) if q is not None]
        sp = (max(ends) - min(ends)) / 2 if len(ends) == 2 else float("nan")
        tol = 2 * float(np.hypot(c["se"], sp))
        d = c["lam"] - lp
        verdict = "AGREE" if abs(d) <= tol else ("BELOW" if d < 0 else "ABOVE")
        out["cells"].append(dict(n=c["n"], L=c["L"], lam_device=c["lam"], se_device=c["se"], lam_pred=lp, se_pred=sp,
                                 diff=d, two_se=tol, verdict=verdict))
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    job, runs = argv[0], argv[1]
    ref_n = int(argv[argv.index("--ref-n") + 1]) if "--ref-n" in argv else 20
    sc = json.load(open(os.path.join(job, "lam_score.json")))
    cells = []
    for c in sc["cells"]:
        rec = json.load(open(os.path.join(runs, c["name"] + ".json")))
        if not rec.get("kising"):
            continue
        cells.append(dict(n=c["n"], L=c["L"], h=rec["kising"]["h"], inputs=rec["inputs"],
                          noiseless_z=rec["noiseless_z"], lam=c["device"]["lam"], se=c["device"]["se"]))
    res = predict(cells, ref_n)
    r = res["ref"]
    print(f"reference n {r['n']}: device lam {r['lam']:.3f} +- {r['se']:.3f} -> p {r['p']} (range {r['p_range']})")
    for c in res["cells"]:
        print(f"n {c['n']} L {c['L']}: device {c['lam_device']:.3f} +- {c['se_device']:.3f} | formula "
              f"{c['lam_pred']:.3f} +- {c['se_pred']:.3f} | diff {c['diff']:+.3f}, 2 SE {c['two_se']:.3f}: {c['verdict']}")
    f = os.path.join(job, "formula_score.json")
    if os.path.exists(f):
        print(f"{f} exists; not written")
    else:
        json.dump(res, open(f, "w"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
