"""After the fact (not declared): the reliability ledger v0 (psf_os.ledger) built from the floor cells of past P5 jobs,
in time order, and what leaving its EXCLUDED qubits out of scoring would have changed on the next job.

kingston: stage B (morning of 3 Nov), stage C/D (midday), stage E job K (evening). The ledger after B and C/D is
applied to K (the next job): K's answered cells (theta 0.4, 0.8, 1.0; t = 6, 7, 8) are scored with and without the
excluded qubits. fez: one job only (stage E X), so the two-job rule cannot exclude anything there.
Scoring-only drop (the circuits are as they ran); a declared test would build the lattice without them.

usage: PYTHONPATH=<psf-os>:<TOQB> python ledger_posthoc.py OUT_JSON
"""
import datetime as dt
import json
import os
import re
import sys

import numpy as np

from psf_os import kim as K
from psf_os import ledger as Lg

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KJOBS = [("kingston B", "results/kim-lattice-2026-11-03", ""), ("kingston C/D", "results/kim-cd-2026-11-03", "c"),
         ("kingston K", "results/kim-e-2026-11-03/K", "e")]
FEZ = ("fez X", "results/kim-e-2026-11-03/X", "e")


def when(d):
    s = json.load(open(os.path.join(ROOT, d, "V", "job", "submission.json"))).get("submitted", "")
    m = re.search(r"\((\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) CET\)", s)
    return m.group(1) if m else s[:19].replace("T", " ")


def floor(d, tag):
    sc = K.score(os.path.join(ROOT, d, "V", "job"), os.path.join(ROOT, d, "V", "runs"))
    s0 = [s for s in sc.values() if abs(s["theta"]) < 1e-9 and s["tag"] == tag][0]
    rows = [r for r in s0["rows"] if r["t"] > 0]
    z0 = np.mean([r["z"] for r in rows], axis=0)
    se = np.sqrt(np.sum([np.square(r["se"]) for r in rows], axis=0)) / len(rows)
    return s0["qubits"], z0, se, sc


def main(outp):
    led = Lg.empty()
    res = dict(jobs=[])
    for name, d, tag in KJOBS[:2] + [FEZ]:
        q, z0, se, _ = floor(d, tag)
        rd, line = Lg.read_floor(q, z0, se)
        dev = "ibm_fez" if name.startswith("fez") else "ibm_kingston"
        led = Lg.add(led, dev, "floor", name, when(d), rd, line)
        cnt = {v: sum(1 for _, x, *_ in rd if x == v) for v in ("DEAD", "HEALTHY", "UNCERTAIN")}
        res["jobs"].append(dict(job=name, when=when(d), line=line, counts=cnt,
                                dead=[(a, round(v, 3)) for a, x, v, _ in rd if x == "DEAD"]))
        print(name, when(d), f"line {line:.3f}", cnt, "DEAD", [(a, round(v, 3)) for a, x, v, _ in rd if x == "DEAD"])
    nameK, dK, tagK = KJOBS[2]
    now = dt.datetime.fromisoformat(when(dK))
    qx, _, s = Lg.exclusions(led, "ibm_kingston", now)
    qf, _, _ = Lg.exclusions(led, "ibm_fez", now)
    watch = sorted(q for (k, q), e in s.items() if e["status"] == "WATCH")
    print("kingston EXCLUDED before K:", qx, "| WATCH:", watch, "| fez EXCLUDED:", qf)
    res.update(excluded_kingston=qx, watch_kingston=watch, excluded_fez=qf)
    qK, _, _, scK = floor(dK, tagK)
    pod = json.load(open(os.path.join(ROOT, dK, "answers_pod", "answers_C.json")))
    keep = [i for i, q in enumerate(qK) if q not in set(qx)]
    res["dropped_in_K"] = [q for q in qK if q in set(qx)]
    rows = {}
    for th in (0.4, 0.8, 1.0):
        cell = [s_ for s_ in scK.values() if abs(s_["theta"] - th) < 1e-9 and s_["tag"] == tagK][0]
        se_all, se_keep, devs_all, devs_keep = [], [], [], []
        for r in cell["rows"]:
            ex = pod[f"{th:.6f}"][str(r["t"])]["z"]
            ia = [i for i, v in enumerate(ex) if v is not None]
            ik = [i for i in ia if i in set(keep)]
            for idx, sq, dv in ((ia, se_all, devs_all), (ik, se_keep, devs_keep)):
                m = np.array([r["z"][i] for i in idx])
                a = np.array([ex[i] for i in idx], dtype=float)
                sq.extend(((m - a) ** 2).tolist())
                dv.append(abs(m.mean() - a.mean()))
        rows[f"{th:g}"] = dict(mse_all=float(np.mean(se_all)), mse_kept=float(np.mean(se_keep)),
                               ratio=float(np.mean(se_keep) / np.mean(se_all)), max_dev_all=float(max(devs_all)),
                               max_dev_kept=float(max(devs_keep)))
        print(f"K theta {th}: MSE {rows[f'{th:g}']['mse_all']:.4f} -> {rows[f'{th:g}']['mse_kept']:.4f} "
              f"(ratio {rows[f'{th:g}']['ratio']:.2f}); max |dM| {max(devs_all):.3f} -> {max(devs_keep):.3f}")
    rdK, lineK = Lg.read_floor(qK, *floor(dK, tagK)[1:3])
    led_after = Lg.add(led, "ibm_kingston", "floor", nameK, when(dK), rdK, lineK)
    after = Lg.exclusions(led_after, "ibm_kingston", now)[0]
    res.update(K_floor_dead=[(a, round(v, 3)) for a, x, v, _ in rdK if x == "DEAD"], excluded_after_K=after)
    print("K's own floor DEAD:", res["K_floor_dead"], "| EXCLUDED after adding K:", after)
    allr = np.mean([v["ratio"] for v in rows.values()])
    res.update(K=rows, mean_ratio=float(allr), price=len(res["dropped_in_K"]))
    print(f"mean ratio {allr:.2f}; price {len(res['dropped_in_K'])} qubits of {len(qK)}")
    json.dump(res, open(outp, "w"), indent=1, default=str)


if __name__ == "__main__":
    main(sys.argv[1])
