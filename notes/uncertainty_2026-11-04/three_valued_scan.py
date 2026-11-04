"""After-the-fact look (not declared) at a three-valued scan reading: per ring site, the echo signal a_j and its
shot-noise standard error SE_j, then DEAD if a_j + k SE_j < tau, HEALTHY if a_j - k SE_j >= tau, UNCERTAIN otherwise
(tau = 0.12, k = 3). The declared rule (a_j < tau on 3 or more consecutive sites) is not changed here; this only counts
how its dead runs and its healthy sites split when the shot noise is taken into account.

SE: a_j = (1/4) sum_i (-z_in,i,j) m_i,j over the four inputs i, each m_i,j the mean of N_i outcomes +-1, so
SE_j = (1/4) sqrt(sum_i (1 - m_i,j^2) / N_i).

usage: PYTHONPATH=<psf-os> python three_valued_scan.py OUT_JSON
"""
import json
import os
import sys

import numpy as np

from psf_os import scan as S

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JOBS = [("kingston 31 Oct (day 1)", "results/coverage-days-2026-10-31-day1/job_A", "results/coverage-days-2026-10-31-day1/runs_A"),
        ("kingston 1 Nov (day 2)", "results/coverage-days-2026-11-01-day2/job_A", "results/coverage-days-2026-11-01-day2/runs_A"),
        ("kingston 2 Nov (day 3)", "results/coverage-days-2026-11-02-day3/job_A", "results/coverage-days-2026-11-02-day3/runs_A"),
        ("fez 1 Nov", "results/two-devices-2026-11-01/fez/scan/job_A", "results/two-devices-2026-11-01/fez/scan/runs_A"),
        ("marrakesh 1 Nov", "results/two-devices-2026-11-01/marrakesh/scan/job_A", "results/two-devices-2026-11-01/marrakesh/scan/runs_A")]
TAU, K = 0.12, 3.0


def site_signal_se(counts_by_input, n):
    a = np.zeros(n)
    var = np.zeros(n)
    for i in S.INPUTS:
        zin = 1 - 2 * np.array(S.input_bits(i, n))
        c = counts_by_input[i]
        N = float(sum(c.values()))
        m = np.zeros(n)
        for key, k in c.items():
            b = key.replace(" ", "")
            m += k * np.array([1 - 2 * int(b[n - 1 - j]) for j in range(n)])
        m /= N
        a += -zin * m / 4
        var += (1 - m ** 2) / N / 16
    return a, np.sqrt(var)


def profiles(job, runs):
    man = json.load(open(os.path.join(job, "manifest.json")))
    rows = S.load_counts(job)
    out = {}
    for cid, c in enumerate(man["cells"]):
        mt = S.ECHO_NAME.match(c["name"])
        if not mt or int(mt.group(2)) != 24:
            continue
        rec = json.load(open(os.path.join(runs, c["name"] + ".json")))
        n = rec["task"]["n"]
        cc = {}
        for k, p in enumerate(man["pubs"]):
            if p["cell"] == cid:
                pt = rec["points"][p["point"]]
                if pt["setting"] == "echo":
                    cc[pt["input"]] = rows[k]["counts"]
        mq = rec["echo"]["measured_qubits"]
        out[n] = ([int(mq[str(j)]) for j in range(n)], *site_signal_se(cc, n))
    return out


def main(outp):
    res = {}
    tot = dict(sites=0, dead=0, healthy=0, uncertain=0, run_sites=0, run_sites_uncertain=0, outside_runs_uncertain=0)
    for name, job, runs in JOBS:
        pr = profiles(os.path.join(ROOT, job), os.path.join(ROOT, runs))
        for n, (ring, a, se) in sorted(pr.items()):
            cls = np.where(a + K * se < TAU, "DEAD", np.where(a - K * se >= TAU, "HEALTHY", "UNCERTAIN"))
            runs_ = S.dead_runs(a)
            in_run = {(s0 + t) % n for s0, L0 in runs_ for t in range(L0)}
            unc = [j for j in range(n) if cls[j] == "UNCERTAIN"]
            rec = dict(n=n, se_median=float(np.median(se)), se_max=float(se.max()),
                       counts={c: int((cls == c).sum()) for c in ("DEAD", "HEALTHY", "UNCERTAIN")},
                       dead_runs=[dict(start=s0, length=L0, qubits=[ring[(s0 + t) % n] for t in range(L0)],
                                       uncertain=[ring[(s0 + t) % n] for t in range(L0) if cls[(s0 + t) % n] == "UNCERTAIN"])
                                  for s0, L0 in runs_],
                       uncertain_outside_runs=[dict(q=ring[j], a=round(float(a[j]), 4), se=round(float(se[j]), 4))
                                               for j in unc if j not in in_run],
                       uncertain_in_runs=[dict(q=ring[j], a=round(float(a[j]), 4), se=round(float(se[j]), 4))
                                          for j in unc if j in in_run])
            res[f"{name} n{n}"] = rec
            tot["sites"] += n
            for c in ("DEAD", "HEALTHY", "UNCERTAIN"):
                tot[c.lower()] += rec["counts"][c]
            tot["run_sites"] += len(in_run)
            tot["run_sites_uncertain"] += len(rec["uncertain_in_runs"])
            tot["outside_runs_uncertain"] += len(rec["uncertain_outside_runs"])
            print(f"{name} n{n}: SE median {rec['se_median']:.4f}; DEAD {rec['counts']['DEAD']}, HEALTHY {rec['counts']['HEALTHY']}, "
                  f"UNCERTAIN {rec['counts']['UNCERTAIN']} (in dead runs {len(rec['uncertain_in_runs'])} of {len(in_run)}; "
                  f"outside {rec['uncertain_outside_runs']})")
    res["total"] = tot
    print("total", tot)
    json.dump(res, open(outp, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
