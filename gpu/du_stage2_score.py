"""Score P4 stage 2b (prereg/drafts-2026-11-03/du_stage2_note.md): judgements 1-4 and the reported items, from the job
folder, its run records and the sealed answers (answers.json of gpu/du_answers_pod.sh).

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/du_stage2_score.py OUT_DIR ANSWERS.json   (writes OUT_DIR/scores.json)
"""
import json
import sys

import numpy as np

from psf_os import dual as DU
from psf_os import sentinel

P4 = np.pi / 4


def key(h, b):
    return f"h{h:g}_b{b:.6f}"


def rate(a, b, T):
    """k of R(t) = a_t / b_t = k^t, weighted least squares on ln R through the origin, t = 1..T."""
    ts = np.arange(1, T + 1)
    y = np.array([np.log(a[t]["on"] / b[t]["on"]) for t in ts])
    w = 1 / np.array([(a[t]["on_se"] / a[t]["on"]) ** 2 + (b[t]["on_se"] / b[t]["on"]) ** 2 for t in ts])
    lk = float(np.sum(w * ts * y) / np.sum(w * ts ** 2))
    return float(np.exp(lk)), float(np.exp(lk) / np.sqrt(np.sum(w * ts ** 2)))


def score(out, answers_file):
    jd, runs = f"{out}/V/job", f"{out}/V/runs"
    ans = json.load(open(answers_file))
    sc = DU.score(jd, runs)
    by = {key(s_rec["h"], b): s_rec for s_rec, b in
          ((s, json.load(open(f"{runs}/{name}.json"))["psfos_job"].get("kick", P4)) for name, s in sc.items())}
    N, T = 33, 16
    rows = {k: {r["t"]: r for r in s["rows"]} for k, s in by.items()}
    res = dict(sentinel=sentinel.verdict(jd, runs)["status"], answers_file=answers_file)
    cl, du = rows[key(0.0, P4)], rows[key(0.15, P4)]
    k, se = rate(du, cl, T)
    c = float(np.cos(0.3))
    res["control_rate"] = dict(k=k, se=se, cos2h=c, verdict="AGREES" if abs(k - c) <= max(2 * se, 0.005) else "DIFFERS")
    for name, b in (("off1", P4 - 0.1), ("off2", P4 - 0.2)):
        kk = key(0.15, b)
        r, a = rows[kk], np.array(ans[kk]["x"])
        m = np.array([r[t]["all"] for t in range(1, T + 1)])
        A = a[1:T + 1]
        mse, msq = float(np.mean((m - A) ** 2)), float(np.mean(A ** 2))
        Rn = np.array([r[t]["on"] / cl[t]["on"] for t in range(1, T + 1)])
        on_ans = np.array([a[t][t] for t in range(1, T + 1)])
        rms = float(np.sqrt(np.mean((Rn - on_ans) ** 2)))
        off_mask = np.ones_like(A, dtype=bool)
        for t in range(T):
            off_mask[t, t + 1] = False
        below = [t for t in range(1, T + 1) if abs(r[t]["on"]) < 3 * r[t]["on_se"]]
        res[name] = dict(b=b, mse=mse, mean_square_answer=msq, reads="READS" if mse <= msq / 2 else "DOES NOT READ",
                         on_cone_raw=[r[t]["on"] for t in range(1, T + 1)], on_cone_normalised=Rn.tolist(),
                         on_cone_answer=on_ans.tolist(), rms_normalised=rms,
                         agrees="AGREES" if rms <= 0.05 else "DIFFERS",
                         off_cone_mse=float(np.mean(((m - A) ** 2)[off_mask])),
                         first_t_below_3se=below[0] if below else None)
    for kk in (key(0.0, P4), key(0.15, P4)):
        a = np.array(ans[kk]["x"])
        res.setdefault("answer_check", {})[kk] = float(max(np.max(np.abs(a[t] - DU.exact(N, t, float(kk[1:].split("_")[0]))))
                                                         for t in range(T + 1)))
    json.dump(res, open(f"{out}/scores.json", "w"), indent=1)
    return res


if __name__ == "__main__":
    r = score(sys.argv[1], sys.argv[2])
    print("sentinel", r["sentinel"], "| control rate k", round(r["control_rate"]["k"], 4), "+-",
          round(r["control_rate"]["se"], 4), "cos 0.3", round(r["control_rate"]["cos2h"], 4), r["control_rate"]["verdict"])
    for n in ("off1", "off2"):
        x = r[n]
        print(n, f"b {x['b']:.4f} MSE {x['mse']:.4f} (half {x['mean_square_answer'] / 2:.4f}) {x['reads']} | on-cone "
              f"normalised RMS {x['rms_normalised']:.4f} {x['agrees']} | off-cone MSE {x['off_cone_mse']:.4f} | "
              f"raw below 3 SE from t {x['first_t_below_3se']}")
        print("   raw   ", [round(v, 3) for v in x["on_cone_raw"]])
        print("   norm  ", [round(v, 3) for v in x["on_cone_normalised"]])
        print("   answer", [round(v, 3) for v in x["on_cone_answer"]])
