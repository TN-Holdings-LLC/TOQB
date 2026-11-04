"""Candidate readout-check rule for P5 (draft, not declared): the theta = 0 circuit of the same job is a readout scan
of every lattice qubit from the device's own counts. A qubit whose theta = 0 <Z> falls far below the lattice's own
floor is left out of scoring. No calibration number is read.

Rule R (fixed in this draft before it is applied below):
  z0_q   = mean over the job's theta = 0 depths of <Z_q> (ideal value 1 at every depth)
  floor  = median of z0 over the lattice qubits
  sigma  = 1.4826 * median absolute deviation of z0 (a robust spread; the bad qubits do not move it)
  drop q if z0_q < floor - max(5 * sigma, 0.05)
  (5 sigma: about 3e-7 one-sided for a Gaussian, so under 1e-4 false drops on 150 qubits; 0.05: no qubit is dropped
  for less than the declared magnetisation line.)

Applied AFTER THE FACT to stage E (fez X, kingston K) and stage C/D (kingston b) as a reference only: the rule was
written after qubits 23, 51 and 83 of fez had been seen. The sensitivity to k = 3, 4, 6 is printed for information.

usage: PYTHONPATH=<psf-os>:<TOQB> python readout_rule.py OUT_JSON
"""
import json
import sys

import numpy as np

from psf_os import kim as K

JOBS = [("fez X (stage E)", "results/kim-e-2026-11-03/X"), ("kingston K (stage E, suspect lattice)", "results/kim-e-2026-11-03/K"),
        ("kingston b (stage C/D)", "results/kim-cd-2026-11-03")]
TH = (0.4, 0.8, 1.0)


def rule(z0, k=5.0, floor_min=0.05):
    z0 = np.asarray(z0)
    med = float(np.median(z0))
    sig = 1.4826 * float(np.median(np.abs(z0 - med)))
    line = med - max(k * sig, floor_min)
    return med, sig, line, [i for i, v in enumerate(z0) if v < line]


def agreement(rows, exact_by_t, keep):
    """Max |M_measured - M_exact| over t and the MSE, on answered qubits in `keep`."""
    devs, se = {}, []
    for r in rows:
        t = r["t"]
        if str(t) not in exact_by_t:
            continue
        ex = exact_by_t[str(t)]
        idx = [i for i in keep if ex[i] is not None]
        if not idx:
            continue
        m = np.array([r["z"][i] for i in idx])
        a = np.array([ex[i] for i in idx], dtype=float)
        devs[t] = float(abs(m.mean() - a.mean()))
        se.extend(((m - a) ** 2).tolist())
    return devs, (float(np.mean(se)) if se else None)


def main(out):
    res = {}
    for name, d in JOBS:
        sc = K.score(f"{d}/V/job", f"{d}/V/runs")
        cells = {round(s["theta"], 6): s for s in sc.values() if s.get("tag") in ("e", "c")}
        s0 = cells[0.0]
        qubits = s0["qubits"]
        z0 = np.mean([r["z"] for r in s0["rows"]], axis=0)
        med, sig, line, drop = rule(z0)
        sens = {k: [qubits[i] for i in rule(z0, k)[3]] for k in (3, 4, 6)}
        rec = dict(qubits=len(qubits), depths_theta0=[r["t"] for r in s0["rows"]], floor=med, sigma=sig, line=line,
                   dropped=[dict(q=qubits[i], z0=float(z0[i])) for i in drop], sensitivity=sens,
                   z0_sorted_lowest=[(qubits[i], round(float(z0[i]), 3)) for i in np.argsort(z0)[:12]])
        cpu = json.load(open(f"{d}/answers_cpu.json"))
        pod = json.load(open(f"{d}/answers_pod/answers_C.json"))
        cpu_ans = cpu["answers"]["b"] if "lattices" in cpu else cpu["answers"]
        keep_all = list(range(len(qubits)))
        keep = [i for i in keep_all if i not in drop]
        for th in TH:
            if th not in cells:
                continue
            rows = cells[th]["rows"]
            if cells[th]["qubits"] != qubits:
                raise RuntimeError("theta cells on different qubit lists")
            key = f"{th:.6f}"
            ex = {}
            ex.update({t: v["z"] for t, v in cpu_ans.get(key, {}).items()})
            ex.update({t: v["z"] for t, v in pod.get(key, {}).items()})
            b_all, mse_all = agreement(rows, ex, keep_all)
            b_keep, mse_keep = agreement(rows, ex, keep)
            rec[key] = dict(max_dev_all=max(b_all.values()), max_dev_kept=max(b_keep.values()), mse_all=mse_all,
                            mse_kept=mse_keep, dev_by_t_all=b_all, dev_by_t_kept=b_keep)
        res[name] = rec
        print(f"{name}: {len(qubits)} qubits, floor {med:.4f}, sigma {sig:.4f}, line {line:.4f}, dropped "
              f"{[(x['q'], round(x['z0'], 3)) for x in rec['dropped']]}; k=3/4/6 drop {sens}")
        for th in TH:
            key = f"{th:.6f}"
            if key in rec:
                r = rec[key]
                print(f"   theta {th}: max |dM| {r['max_dev_all']:.3f} -> {r['max_dev_kept']:.3f}; MSE {r['mse_all']:.4f} -> {r['mse_kept']:.4f}")
    json.dump(res, open(out, "w"), indent=1, default=str)


if __name__ == "__main__":
    main(sys.argv[1])
