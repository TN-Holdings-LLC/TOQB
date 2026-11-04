"""After the fact (reference only, not declared): the self-repair chain (psf_os.repair2d) applied to the floor cells
of past P5 jobs on kingston, in time order: stage B (06:08 CET, 3 Nov), stage C/D (12:09), stage E job K (17:04
submitted). For each rule (a: two jobs, b: one job) and release (expiry, early): what the chain would have excluded
before each next job, and whether those qubits were still bad in that job (the flag's lifetime, read with the next
job's own line). For K, also the scoring-only change of the MSE (ledger_posthoc's proxy: the circuits ran as they
did; a declared test would place the problem elsewhere). fez had one job: nothing to confirm from (first day).

usage: PYTHONPATH=<psf-os>:<TOQB> python repair_posthoc.py OUT_JSON
"""
import datetime as dt
import importlib.util
import json
import os
import sys

import numpy as np

from psf_os import ledger as Lg
from psf_os import repair2d as Rp

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("lp", os.path.join(HERE, "..", "ledger_2026-11-04", "ledger_posthoc.py"))
LP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LP)
DEV = "ibm_kingston"


def main(outp):
    jobs = []
    for name, d, tag in LP.KJOBS:
        q, z0, se, sc = LP.floor(d, tag)
        rd = Rp.readings(q, z0, se)
        jobs.append(dict(name=name, d=d, tag=tag, when=LP.when(d), qubits=q, z0=z0, se=se, rd=rd))
    res = dict(jobs=[dict(job=j["name"], when=j["when"], line=j["rd"]["floor"][1],
                          dead=[x[0] for x in j["rd"]["floor"][0] if x[1] == "DEAD"]) for j in jobs], steps=[])
    for k in (1, 2):
        nxt = jobs[k]
        now = dt.datetime.fromisoformat(nxt["when"])
        led = Lg.empty()
        for j in jobs[:k]:
            led = Rp.record(led, DEV, j["name"], j["when"], j["rd"])
        verdict_next = {x[0]: (x[1], round(x[2], 3)) for x in nxt["rd"]["floor"][0]}
        for rule in Rp.RULES:
            for rel in Rp.RELEASES:
                exc, released = Rp.confirmed(led, DEV, now, rule, rel)
                seen = {q: verdict_next.get(q, ("not in lattice", None)) for q in sorted(exc)}
                still = sum(1 for v in seen.values() if v[0] == "DEAD")
                step = dict(before=nxt["name"], from_jobs=[j["name"] for j in jobs[:k]], rule=rule, release=rel,
                            excluded=sorted(exc), in_next_job=seen, still_dead=still,
                            hours=round((now - dt.datetime.fromisoformat(jobs[k - 1]["when"])).total_seconds() / 3600,
                                        1))
                res["steps"].append(step)
                print(f"before {nxt['name']} rule {rule} {rel}: excluded {sorted(exc)}; next job: {seen}; "
                      f"still DEAD {still}/{len(exc)}")
    # K, scoring-only proxy for rule b (the exclusions from C/D, the job before K)
    nameK, dK, tagK = LP.KJOBS[2]
    led = Rp.record(Rp.record(Lg.empty(), DEV, jobs[0]["name"], jobs[0]["when"], jobs[0]["rd"]),
                    DEV, jobs[1]["name"], jobs[1]["when"], jobs[1]["rd"])
    nowK = dt.datetime.fromisoformat(jobs[2]["when"])
    excK = sorted(Rp.confirmed(led, DEV, nowK, "b", "expiry")[0])
    _, _, _, scK = LP.floor(dK, tagK)
    pod = json.load(open(os.path.join(LP.ROOT, dK, "answers_pod", "answers_C.json")))
    qK = jobs[2]["qubits"]

    def proxy(excl):
        keep = {i for i, q in enumerate(qK) if q not in set(excl)}
        rows = {}
        for th in (0.4, 0.8, 1.0):
            cell = [s for s in scK.values() if abs(s["theta"] - th) < 1e-9 and s["tag"] == tagK][0]
            a_all, a_keep = [], []
            for r in cell["rows"]:
                ex = pod[f"{th:.6f}"][str(r["t"])]["z"]
                ia = [i for i, v in enumerate(ex) if v is not None]
                for idx, acc in ((ia, a_all), ([i for i in ia if i in keep], a_keep)):
                    acc.extend(((np.array([r["z"][i] for i in idx]) - np.array([ex[i] for i in idx], float)) ** 2
                                ).tolist())
            rows[f"{th:g}"] = dict(mse_all=float(np.mean(a_all)), mse_kept=float(np.mean(a_keep)),
                                   ratio=float(np.mean(a_keep) / np.mean(a_all)))
        return dict(excluded=sorted(excl), dropped_in_K=len(qK) - len(keep), rows=rows,
                    mean_ratio=float(np.mean([v["ratio"] for v in rows.values()])))
    excE = sorted(Rp.confirmed(led, DEV, nowK, "b", "early")[0])
    res["K_proxy"] = {"rule b, expiry": proxy(excK), "rule b, early": proxy(excE), "qubit 72 only": proxy([72]),
                      "rule b, expiry, without 72": proxy([q for q in excK if q != 72])}
    for k, v in res["K_proxy"].items():
        print(f"K proxy {k}: dropped {v['dropped_in_K']}; ratios " +
              ", ".join(f"theta {th} {r['ratio']:.2f}" for th, r in v["rows"].items()) + f"; mean {v['mean_ratio']:.2f}")
    json.dump(res, open(outp, "w"), indent=1, default=str)


if __name__ == "__main__":
    main(sys.argv[1])
