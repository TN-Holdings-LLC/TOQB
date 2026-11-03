"""Score P5 stage B (prereg/drafts-2026-11-03/kim_lattice_note.md): judgements 1-4 and the reported items.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/kim_score.py OUT_DIR    (reads OUT_DIR/answers.json; writes OUT_DIR/scores.json)
"""
import json
import sys

import numpy as np

from psf_os import kim as K
from psf_os import sentinel

JUDGED = (0.4, 0.8, 1.0)


def score(out):
    jd, runs = f"{out}/V/job", f"{out}/V/runs"
    A = json.load(open(f"{out}/answers.json"))
    sc = {f"{s['theta']:.6f}": s for s in K.score(jd, runs).values()}
    T = len(next(iter(sc.values()))["rows"]) - 1
    z0 = {r["t"]: np.array(r["z"]) for r in sc[f"{0.0:.6f}"]["rows"]}
    res = dict(sentinel=sentinel.verdict(jd, runs)["status"], t_max=T, n=len(A["qubits"]))
    for th in JUDGED:
        k = f"{th:.6f}"
        m = {r["t"]: np.array(r["z"]) for r in sc[k]["rows"]}
        a = {t: np.array(A["answers"][k][t]["z"]) for t in range(T + 1)}
        err = np.concatenate([m[t] - a[t] for t in range(1, T + 1)])
        ms = np.concatenate([a[t] for t in range(1, T + 1)])
        Mm = [float(m[t].mean()) for t in range(T + 1)]
        Ma = [float(a[t].mean()) for t in range(T + 1)]
        Mn = [float((m[t] / z0[t]).mean()) for t in range(T + 1)]
        raw_dev = max(abs(Mm[t] - Ma[t]) for t in range(1, T + 1))
        norm_dev = max(abs(Mn[t] - Ma[t]) for t in range(1, T + 1))
        site_err = np.abs(m[T] - a[T])
        worst = np.argsort(-site_err)[:5]
        res[k] = dict(mse=float(np.mean(err ** 2)), mean_square_answer=float(np.mean(ms ** 2)),
                      reads="READS" if np.mean(err ** 2) <= np.mean(ms ** 2) / 2 else "DOES NOT READ",
                      M_measured=Mm, M_exact=Ma, M_normalised=Mn, raw_max_dev=raw_dev, norm_max_dev=norm_dev,
                      raw="AGREES" if raw_dev <= 0.05 else "DIFFERS", normalised="AGREES" if norm_dev <= 0.05 else "DIFFERS",
                      worst_sites_at_t_max=[dict(qubit=A["qubits"][i], measured=float(m[T][i]), answer=float(a[T][i]))
                                            for i in worst])
    for k in (f"{0.0:.6f}", f"{np.pi / 2:.6f}"):
        res[k] = dict(M_measured=[float(np.mean(r["z"])) for r in sc[k]["rows"]],
                      M_exact=[float(np.mean(A["answers"][k][t]["z"])) for t in range(T + 1)])
    json.dump(res, open(f"{out}/scores.json", "w"), indent=1)
    return res


if __name__ == "__main__":
    r = score(sys.argv[1])
    print("sentinel", r["sentinel"], "| lattice", r["n"], "qubits, t <=", r["t_max"])
    for th in JUDGED:
        x = r[f"{th:.6f}"]
        print(f"theta {th}: MSE {x['mse']:.4f} (half {x['mean_square_answer'] / 2:.4f}) {x['reads']} | raw max |dM| "
              f"{x['raw_max_dev']:.4f} {x['raw']} | normalised {x['norm_max_dev']:.4f} {x['normalised']}")
        print("   M measured  ", [round(v, 3) for v in x["M_measured"]])
        print("   M normalised", [round(v, 3) for v in x["M_normalised"]])
        print("   M exact     ", [round(v, 3) for v in x["M_exact"]])
    for k, nm in ((f"{0.0:.6f}", "theta 0"), (f"{np.pi / 2:.6f}", "theta pi/2")):
        print(nm, "M measured", [round(v, 3) for v in r[k]["M_measured"]], "exact", [round(v, 3) for v in r[k]["M_exact"]])
