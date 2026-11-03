"""Score P5 stage E (prereg/drafts-2026-11-03/kim_e_note.md), one job folder at a time.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/kim_e_score.py OUT_DIR   (OUT_DIR holds V/, answers_cpu.json and
       answers_pod/answers_C.json; writes OUT_DIR/scores.json)
"""
import json
import sys

import numpy as np

from psf_os import kim as K
from psf_os import sentinel

TH = (0.4, 0.8, 1.0)


def k(th):
    return f"{th:.6f}"


def verdicts(m, a, ts):
    """m, a: {t: arrays}; a may hold None (unanswered). READS over the pooled values, AGREES per-t magnetisation."""
    se, sa, rows = [], [], {}
    for t in ts:
        ok = [i for i, v in enumerate(a[t]) if v is not None]
        mm, aa = np.asarray(m[t])[ok], np.array([a[t][i] for i in ok], dtype=float)
        se.append((mm - aa) ** 2)
        sa.append(aa ** 2)
        rows[str(t)] = dict(answered=len(ok), M_measured=float(mm.mean()), M_exact=float(aa.mean()),
                            dev=float(abs(mm.mean() - aa.mean())))
    mse, msq = float(np.mean(np.concatenate(se))), float(np.mean(np.concatenate(sa)))
    dev = max(r["dev"] for r in rows.values())
    return dict(rows=rows, mse=mse, mean_square_answer=msq, reads="READS" if mse <= msq / 2 else "DOES NOT READ",
                max_dev=dev, agrees="AGREES" if dev <= 0.05 else "DIFFERS")


def score(out):
    jd, runs = f"{out}/V/job", f"{out}/V/runs"
    cpu = json.load(open(f"{out}/answers_cpu.json"))
    pod = json.load(open(f"{out}/answers_pod/answers_C.json"))
    sc = {k(s["theta"]): s for s in K.score(jd, runs).values()}
    res = dict(sentinel=sentinel.verdict(jd, runs)["status"], qubits=len(cpu["qubits"]))
    for th in TH:
        meas = {r["t"]: np.array(r["z"]) for r in sc[k(th)]["rows"]}
        ts = sorted(meas)
        out_th = {}
        tb = [t for t in ts if t <= 5]
        if tb:
            out_th["B"] = verdicts(meas, {t: cpu["answers"][k(th)][str(t)]["z"] for t in tb}, tb)
        tc = [t for t in ts if t >= 6]
        out_th["C"] = verdicts(meas, {t: pod[k(th)][str(t)]["z"] for t in tc}, tc)
        res[k(th)] = out_th
    res["theta0_M"] = {str(r["t"]): float(np.mean(r["z"])) for r in sc[k(0.0)]["rows"]}
    json.dump(res, open(f"{out}/scores.json", "w"), indent=1)
    return res


if __name__ == "__main__":
    r = score(sys.argv[1])
    print("sentinel", r["sentinel"], "| lattice", r["qubits"], "qubits | theta 0 M", {t: round(v, 3) for t, v in r["theta0_M"].items()})
    for th in TH:
        for st, x in r[k(th)].items():
            print(f"theta {th} stage {st}: MSE {x['mse']:.4f} (half {x['mean_square_answer'] / 2:.4f}) {x['reads']}; "
                  f"max |dM| {x['max_dev']:.4f} {x['agrees']}; "
                  + "; ".join(f"t {t}: {v['M_measured']:.3f}/{v['M_exact']:.3f} ({v['answered']})" for t, v in x["rows"].items()))
