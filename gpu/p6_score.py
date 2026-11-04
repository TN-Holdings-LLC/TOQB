"""Score P6 on a device (prereg/drafts-2026-11-04/p6_device_note.md): judgements 1-3 per theta_x, the reported items,
the answer card (owner, 2026-11-04: added to reports, no verdict changes) and the sub-analysis rule R.

usage: PYTHONPATH=<psf-os 61e9edd>:<TOQB> python gpu/p6_score.py OUT_DIR   (writes OUT_DIR/scores.json)
"""
import json
import sys

import numpy as np

from psf_os import ising2d as I
from psf_os import sentinel

TUTORIAL = {5: (0.704, 0.79537), 7: (0.648, 0.78653), 9: (0.617, 0.79699)}  # unmitigated, BP-PEPS (marrakesh)
SHOTS = 4000


def answers(tx):
    if abs(tx - 0.53) < 1e-9:
        cpu = json.load(open("results/p6-answers-2026-11-04/answers_cpu.json"))["answers"]
        gpu = json.load(open("results/p6-answers-2026-11-04/gpu/answers_gpu.json"))
    else:
        cpu = json.load(open(f"results/bank-2026-11-04/p6_tx{tx:g}_answers_cpu.json"))["answers"]
        gpu = json.load(open(f"results/bank-2026-11-04/pod/p6_tx{tx:g}/answers_gpu.json"))
    out = {t: list(cpu[str(t)]) for t in range(1, 6)}
    out.update({t: gpu[str(t)]["z"] for t in range(6, 10)})
    return out


def judge(meas, ans, keep=None):
    rows, se2, sa2 = {}, [], []
    for t in range(1, 10):
        idx = [i for i, a in enumerate(ans[t]) if a is not None and (keep is None or keep[i])]
        m = np.array(meas[t])[idx]
        a = np.array([ans[t][i] for i in idx])
        se2.append((m - a) ** 2)
        sa2.append(a ** 2)
        two_se = 2 * np.sqrt(np.sum(1 - m ** 2) / SHOTS) / len(m)
        rows[t] = dict(n=len(idx), M=float(m.mean()), M_exact=float(a.mean()), diff=float(m.mean() - a.mean()),
                       two_se=float(two_se), diff_over_se=float((m.mean() - a.mean()) / (two_se / 2)))
    mse, msq = float(np.mean(np.concatenate(se2))), float(np.mean(np.concatenate(sa2)))
    first_miss = next((t for t in range(1, 10) if abs(rows[t]["diff"]) > 0.05), None)
    return dict(rows=rows, mse=mse, mean_square_answer=msq, reads="READS" if mse <= msq / 2 else "DOES NOT READ",
                agrees="AGREES" if first_miss is None else "DIFFERS", first_miss=first_miss,
                first_miss_by=None if first_miss is None else rows[first_miss]["diff"])


def score(out):
    jd, runs = f"{out}/V/job", f"{out}/V/runs"
    sc = I.score(jd, runs)  # {theta_x: {t: [<Z> per label]}}
    floor = sc["0"]
    z0 = np.mean([floor[t] for t in (1, 5, 9)], axis=0)
    med = float(np.median(z0))
    mad = float(np.median(np.abs(z0 - med)))
    line = med - max(5 * 1.4826 * mad, 0.05)
    keep = z0 >= line
    res = dict(sentinel=sentinel.verdict(jd, runs)["status"],
               floor={t: float(np.mean(floor[t])) for t in (1, 5, 9)},
               rule_R=dict(median=med, mad=mad, line=line,
                           dropped=[dict(label=I.QUBITS[i], z0=float(z0[i])) for i in range(len(z0)) if not keep[i]]))
    for tx in ("0.53", "0.3", "0.8"):
        if tx not in sc:
            continue
        ans = answers(float(tx))
        full = judge(sc[tx], ans)
        out_tx = dict(full=full)
        if tx == "0.53":
            out_tx["tutorial"] = {t: dict(ours_abs_diff=abs(full["rows"][t]["diff"]), tutorial_abs_gap=abs(u - p),
                                         ours_M_all35=float(np.mean(sc[tx][t])), tutorial_noisy=u, tutorial_peps=p)
                                  for t, (u, p) in TUTORIAL.items()}
            if keep.all():
                out_tx["rule_R"] = "NOT TESTED (nothing dropped)"
            else:
                kept = judge(sc[tx], ans, keep)
                ratio = kept["mse"] / full["mse"]
                out_tx["rule_R"] = dict(kept=kept, ratio=ratio,
                                        verdict="HELPS" if ratio <= 0.8 else ("HURTS" if ratio >= 1.25 else "NO EFFECT"))
        t9 = sc[tx][9]
        err = np.array([abs(sc[tx][5][i] - ans[5][i]) for i in range(len(I.QUBITS))])
        out_tx["worst_t5"] = [dict(label=I.QUBITS[i], measured=float(sc[tx][5][i]), answer=float(ans[5][i]))
                              for i in np.argsort(-err)[:5]]
        out_tx["M_all35_t9"] = float(np.mean(t9))
        res[tx] = out_tx
    json.dump(res, open(f"{out}/scores.json", "w"), indent=1, default=str)
    return res


if __name__ == "__main__":
    r = score(sys.argv[1])
    print("sentinel", r["sentinel"], "| floor", {t: round(v, 4) for t, v in r["floor"].items()},
          "| rule R line", round(r["rule_R"]["line"], 4), "dropped", r["rule_R"]["dropped"])
    for tx in ("0.53", "0.3", "0.8"):
        if tx not in r:
            continue
        f = r[tx]["full"]
        print(f"theta_x {tx}: MSE {f['mse']:.4f} (half {f['mean_square_answer'] / 2:.4f}) {f['reads']}, {f['agrees']}"
              + (f" (first miss t {f['first_miss']}: {f['first_miss_by']:+.4f})" if f["first_miss"] else ""))
        for t, row in f["rows"].items():
            print(f"   t {t}: M {row['M']:.4f} exact {row['M_exact']:.4f} ({row['n']}) diff {row['diff']:+.4f} "
                  f"+- {row['two_se']:.4f} (2 SE), {row['diff_over_se']:+.1f} SE")
        if tx == "0.53":
            for t, x in r[tx]["tutorial"].items():
                print(f"   tutorial t {t}: ours |diff| {x['ours_abs_diff']:.3f} vs tutorial unmitigated gap "
                      f"{x['tutorial_abs_gap']:.3f}; ours M over all 35 {x['ours_M_all35']:.4f}")
            print("   rule R:", r[tx]["rule_R"] if isinstance(r[tx]["rule_R"], str) else
                  f"ratio {r[tx]['rule_R']['ratio']:.3f} {r[tx]['rule_R']['verdict']}")
        print("   worst t5:", [(w["label"], round(w["measured"], 3), round(w["answer"], 3)) for w in r[tx]["worst_t5"][:3]])
