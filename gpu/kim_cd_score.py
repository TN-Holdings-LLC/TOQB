"""Score P5 stages C, D and the suspect-qubit rule (prereg/drafts-2026-11-03/kim_cd_note.md).

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/kim_cd_score.py OUT_DIR ANSWERS_C.json   (writes OUT_DIR/scores.json)
"""
import json
import sys

import numpy as np

from psf_os import kim as K
from psf_os import sentinel

P2 = float(np.pi / 2)
TH = (0.4, 0.8, 1.0)


def k(th):
    return f"{th:.6f}"


def score(out, answers_c):
    jd, runs = f"{out}/V/job", f"{out}/V/runs"
    cpu = json.load(open(f"{out}/answers_cpu.json"))
    ac = json.load(open(answers_c))
    meas = {}
    for s in K.score(jd, runs).values():
        meas[(s["tag"], k(s["theta"]))] = {r["t"]: np.array(r["z"]) for r in s["rows"]}
    res = dict(sentinel=sentinel.verdict(jd, runs)["status"])
    # the suspect-qubit rule: b against s, t = 1..5
    sus = {}
    for th in TH:
        mse = {}
        for tag in ("b", "s"):
            e = np.concatenate([meas[(tag, k(th))][t] - np.array(cpu["answers"][tag][k(th)][str(t)]["z"])
                                for t in range(1, 6)])
            mse[tag] = float(np.mean(e ** 2))
        sus[k(th)] = mse
    mb = float(np.mean([v["b"] for v in sus.values()]))
    ms = float(np.mean([v["s"] for v in sus.values()]))
    ratio = ms / mb
    res["suspect_rule"] = dict(per_theta=sus, mse_b=mb, mse_s=ms, ratio=ratio,
                               verdict="HELPS" if ratio <= 0.8 else ("HURTS" if ratio >= 1.25 else "NO EFFECT"),
                               qubits_b=len(cpu["lattices"]["b"]["qubits"]), qubits_s=len(cpu["lattices"]["s"]["qubits"]))
    # stage C: answered qubits, t = 6, 7, 8
    stc = {}
    for th in TH:
        rows, sq_e, sq_a = {}, [], []
        for t in (6, 7, 8):
            a = ac[k(th)][str(t)]["z"]
            ok = [i for i, v in enumerate(a) if v is not None]
            m = meas[("c", k(th))][t][ok]
            av = np.array([a[i] for i in ok])
            sq_e.append((m - av) ** 2)
            sq_a.append(av ** 2)
            rows[str(t)] = dict(answered=len(ok), M_measured=float(m.mean()), M_exact=float(av.mean()),
                                dev=float(abs(m.mean() - av.mean())))
        mse, msq = float(np.mean(np.concatenate(sq_e))), float(np.mean(np.concatenate(sq_a)))
        stc[k(th)] = dict(rows=rows, mse=mse, mean_square_answer=msq,
                          reads="READS" if mse <= msq / 2 else "DOES NOT READ",
                          agrees="AGREES" if max(r["dev"] for r in rows.values()) <= 0.05 else "DIFFERS")
    res["stage_C"] = stc
    # stage D: t = 20
    d = {}
    for th, ex in ((0.0, cpu["answers"]["c"][k(0.0)]["20"]["z"]), (P2, cpu["answers"]["c"][k(P2)]["20"]["z"])):
        m = meas[("c", k(th))][20]
        d[k(th)] = dict(M_measured=float(m.mean()), M_exact=float(np.mean(ex)), dev=float(abs(m.mean() - np.mean(ex))),
                        verdict="AGREES" if abs(m.mean() - np.mean(ex)) <= 0.05 else "DIFFERS")
    for th in TH:
        m = meas[("c", k(th))]
        d[k(th)] = dict(M_measured_t20=float(m[20].mean()), M_measured_t6_8=[float(m[t].mean()) for t in (6, 7, 8)],
                        se_t20=float(np.sqrt(np.mean(1 - m[20] ** 2) / 4000 / len(m[20]))))
    res["stage_D"] = d
    for th in (0.0, P2):
        res.setdefault("controls_t6_8", {})[k(th)] = [float(meas[("c", k(th))][t].mean()) for t in (6, 7, 8)]
    json.dump(res, open(f"{out}/scores.json", "w"), indent=1)
    return res


if __name__ == "__main__":
    r = score(sys.argv[1], sys.argv[2])
    print("sentinel", r["sentinel"])
    s = r["suspect_rule"]
    print(f"suspect rule: MSE b {s['mse_b']:.4f} ({s['qubits_b']} qubits), s {s['mse_s']:.4f} ({s['qubits_s']} qubits), "
          f"ratio {s['ratio']:.3f} {s['verdict']}; per theta {s['per_theta']}")
    for th, x in r["stage_C"].items():
        print(f"stage C theta {th}: MSE {x['mse']:.4f} (half {x['mean_square_answer'] / 2:.4f}) {x['reads']}, {x['agrees']}; "
              + "; ".join(f"t {t}: {v['answered']} q, M {v['M_measured']:.3f} vs {v['M_exact']:.3f}" for t, v in x["rows"].items()))
    for th, x in r["stage_D"].items():
        print("stage D", th, {a: (round(b, 4) if isinstance(b, float) else b) for a, b in x.items()})
    print("controls t 6-8", r["controls_t6_8"])
