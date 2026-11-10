"""L* measurement job (2026-11-10, for the classifier's depth): the readable depth L* of each arm from P1 records, by the
10-29 noise-wall formulas unchanged (prereg/drafts-2026-10-29/noise_wall_1_note.md, "Readable depth"):

  per cell (arm, n, L): the four-input ratio rho(L) = [Q(0..0) + Q(1..1) - Q(Neel) - Q(anti-Neel)]_L / [same]_reference,
      SE by the delta method from the shot variances               (toqb.kising_charge.estimate)
  per (arm, n): L* from the one-parameter fit rho(L) = exp(-L / L*) over the arm's L, weighted least squares on the rho
      scale (weights 1 / SE^2), SE from the curvature              (toqb.kising_charge.decay_length)
  per other arm X at the same n: kappa_X = L*_rule / L*_X, Delta L_X = L*_rule - L*_X, gate and duration ratios
                                                                    (toqb.kising_charge.wall)

Nothing is re-implemented: the cells and fits are the functions the 10-29 score used. Reads JOB/manifest.json,
JOB/raw_counts.json (or raw_counts.json.gz) and RUNS/<cell>.json; checks each record's sha256 against the manifest.

usage: PYTHONPATH=<TOQB> python gpu/lstar_score.py JOB RUNS [--out FILE.json]
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys

from toqb import kising_charge as KC


def load_raw(job):
    p = os.path.join(job, "raw_counts.json")
    if os.path.exists(p):
        return json.load(open(p))
    return json.load(gzip.open(p + ".gz", "rt"))


def cells_of(job, runs):
    man = json.load(open(os.path.join(job, "manifest.json")))
    raw = load_raw(job)
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    cells = []
    for cid, c in enumerate(man["cells"]):
        rf = os.path.join(runs, c["name"] + ".json")
        if KC.sha256_file(rf) != c["run_sha256"]:
            raise SystemExit(f"STOP: {rf} differs from the manifest")
        rec = json.load(open(rf))
        if not rec.get("charge_test"):
            continue
        n, L = rec["task"]["n"], rec["task"]["layers"]
        coef = (rec["charge"]["coef_YZ"], rec["charge"]["coef_ZY"])
        cc = {}
        for k, pub in enumerate(man["pubs"]):
            if pub["cell"] == cid:
                pt = rec["points"][pub["point"]]
                cc[(pt["input"], pt["setting"])] = rows[k]
        est = KC.estimate(cc, n, L, coef)
        # a record built on a failed-mark Target (psfos:) has no durations (us 0): the duration ratio is then n/a
        us = rec.get("us") or None
        cells.append(dict(name=c["name"], arm=rec["arm"], n=n, L=L, q2=rec.get("q2"), us=us,
                          measured_qubits=rec["charge"]["measured_qubits"], **est))
    return man, cells


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("runs")
    ap.add_argument("--out", default=None, help="write the result here (never overwritten)")
    a = ap.parse_args(argv)
    man, cells = cells_of(a.job, a.runs)
    for c in sorted(cells, key=lambda c: (c["n"], c["arm"], c["L"])):
        print(f"{c['name']:44s} rho4 {c['rho4']:.4f} +- {c['se4']:.4f} | {c['q2']} two-qubit gates, {c['us']} us")
    wl = KC.wall(cells)
    for f in wl["fits"]:
        ls = "n/a" if f["L_star"] is None else f"{f['L_star']:.1f} +- {f['se']:.1f}"
        print(f"L* {f['arm']} n {f['n']}: {ls} (fit over L = {f['Ls']})")
    for x in wl["relative"]:
        if "kappa" not in x:
            print(f"Delta L {x['arm']} n {x['n']}: n/a")
            continue
        s = (f"Delta L {x['arm']} n {x['n']}: L* {x['L_star']:.1f}, Delta L {x['delta_L']:+.1f} +- {x['se_delta_L']:.1f},"
             f" kappa {x['kappa']:.2f} +- {x['se_kappa']:.2f}")
        if x.get("g") is not None and x.get("t") is not None:
            s += f" | gates {x['g']:.2f}, duration {x['t']:.2f}"
        print(s)
    if a.out:
        if os.path.exists(a.out):
            print(f"{a.out} exists; not written")
        else:
            json.dump(dict(cells=cells, wall=wl, job_written=man.get("written"), backend=man["fetch"].get("backend")),
                      open(a.out, "w"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    return wl


if __name__ == "__main__":
    main(sys.argv[1:])
