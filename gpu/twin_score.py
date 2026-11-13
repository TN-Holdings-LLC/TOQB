"""Score a job built with --twin (home, 2026-11-13; prereg/twin_2026-11-13.md). Per user tag over its chain qubits:
the user circuit against its answers and its Clifford twin against the twin answers, each with MSE / mean square,
READS (MSE <= mean square / 2), AGREES (|z - e| <= 0.05) and the kept share r = sum z e / sum e^2; per pair the
difference r_twin - r and whether r_twin >= 1 - 1/sqrt(2) matches the user circuit's READS. Never used to correct.
usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/twin_score.py OUT USER_ANSWERS.json TWIN_ANSWERS.json  (writes OUT/twin_scores.json)"""
import json
import os
import sys

import numpy as np

LINE = 1 - 1 / np.sqrt(2)


def verdict(z, e):
    mse, msq = float(np.mean((z - e) ** 2)), float(np.mean(e ** 2))
    return dict(mse=mse, mean_square=msq, reads="READS" if mse <= msq / 2 else "DOES NOT READ",
                agrees=int(np.sum(np.abs(z - e) <= 0.05)), r=float(z @ e / (e @ e)))


def main(out, user_ans, twin_ans):
    from psf_os import job as J, user2d as U
    from psf_os.kim import z_values
    ua, ta = json.load(open(user_ans)), json.load(open(twin_ans))
    read = J.read(os.path.join(out, "job"), os.path.join(out, "runs"))
    cards = U.cards(os.path.join(out, "job"), os.path.join(out, "runs"), ua)
    res = dict(pairs={})
    for tag in sorted(ta):
        card = cards[tag]
        labels = None
        zt = None
        for name, (rec, cc) in read.items():
            if rec.get("psfos_job", {}).get("kind") == "user2d_twin" and U._tag_of(name, rec) == tag:
                labels = rec["labels"]
                zt, _ = z_values(cc[(rec["points"][0]["input"], "z")], len(labels))
        q = {x["q"]: x for x in card["qubits"]}
        zu = np.array([q[lab]["z"] for lab in labels])
        eu = np.array([q[lab]["exact"] for lab in labels])
        et = np.array([ta[tag][str(lab)] for lab in labels])
        u, t = verdict(zu, eu), verdict(np.asarray(zt), et)
        p = dict(user=u, twin=t, r_diff=t["r"] - u["r"], twin_line=bool(t["r"] >= LINE),
                 line_matches=bool((t["r"] >= LINE) == (u["reads"] == "READS")),
                 floor=card["floor_mean"], mirror=card["mirror_mean"])
        res["pairs"][tag] = p
        print(f"{tag}: user {u['reads']} (MSE/msq {u['mse'] / u['mean_square']:.3f}, r {u['r']:.3f}) | twin {t['reads']} "
              f"(MSE/msq {t['mse'] / t['mean_square']:.3f}, r {t['r']:.3f}) | r_twin - r {p['r_diff']:+.3f} | "
              f"r_twin >= 0.293 {p['twin_line']} matches user verdict {p['line_matches']} | mirror {p['mirror']:+.3f}")
    json.dump(res, open(os.path.join(out, "twin_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:4])
