"""The undamped readout on the device day (C r9 draft, 2026-10-21): fixed before submission, scored after the results.

    python -m toqb.s2rc_device_undamp fix --runs RUNS_DIR --job JOB_DIR [--traj 1024]      (pod, after assemble)
    python -m toqb.s2rc_device_undamp score --job JOB_DIR                                   (home, after result)

fix: for every cell of the job's manifest, the cell's run record (its plan, arm and the day's Target) gives the twin;
(lam, delta) come from that twin on the run's 64 training inputs (traj trajectories, seed predict.seed + 5) against
the exact noiseless model (toqb.undamp; no labels, no device data). The undamped prediction is the record's twin P(1)
through the same simulated jobs as the raw prediction (same seed), at the job's shots. Written to JOB/undamp.json with
the manifest's SHA-256; its own SHA-256 is fixed with the manifest's before submission. It never changes the job.

score: the device's counts (raw_counts.json) per point give p_hat; the raw CE and accuracy are toqb.s2rc_device's
(score.md); the undamped ones use z_u = clip((1 - 2 p_hat - delta) / lam, -1, 1). Per cell: raw and undamped CE and
accuracy, the undamped prediction and whether the device's undamped CE falls inside its 99 % interval. Written to
JOB/undamp_score.json and .md. Reported beside C's hypotheses, which it does not change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

from toqb import undamp as U


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _load(path):
    return json.load(open(path, encoding="utf-8"))


def _p1(counts, clbit=0):
    total = sum(counts.values())
    return sum(v for k, v in counts.items() if k.replace(" ", "")[-1 - clbit] == "1") / total


def _ce(z, y):
    p = np.clip((1 + np.asarray(z)) / 2, 1e-4, 1 - 1e-4)
    return float(np.mean(-np.where(np.asarray(y) > 0, np.log(p), np.log(1 - p))))


def _acc(z, y):
    z, y = np.asarray(z), np.asarray(y)
    return float(np.mean(np.where(z == 0, 0.5, (np.sign(z) == y).astype(float))))


def cmd_fix(a, estimate=None):
    from toqb import s2r2 as S2
    estimate = estimate or U.estimate
    man_f = os.path.join(a.job, "manifest.json")
    out_f = os.path.join(a.job, "undamp.json")
    if os.path.exists(out_f):
        raise SystemExit(f"STOP: {out_f} exists; it is never overwritten")
    man = _load(man_f)
    cells = []
    for c in man["cells"]:
        rf = os.path.join(a.runs, c["name"] + ".json")
        if _sha(rf) != c["run_sha256"]:
            raise SystemExit(f"STOP: {rf} differs from the run the manifest was built from")
        r = _load(rf)
        plan = dict(name=r["plan"], device=r["device"], task=r["task"], train=r["train"], predict=r["predict"],
                    standin=r["standin"], verify=False)
        R = S2.Runner(plan, r["arm"])
        Xtr = S2.teacher_data2(r["task"])[0]
        lam, delta, rms = estimate(R, np.array(r["final_mean"]), Xtr, r["task"], a.traj, int(r["predict"]["seed"]) + 5)
        pr = r["predict"]
        Pu = U.predict_job_undamped(c["twin_p1"], np.array(c["labels"]), man["shots"], pr["reps"], pr["level"],
                                    pr["seed"] + 1, lam, delta, traj=pr["traj"])
        cells.append(dict(cell=c["cell"], name=c["name"], arm=c["arm"], layers=c["layers"], lam=lam, delta=delta,
                          fit_rms=rms, traj=a.traj, seed=int(pr["seed"]) + 5, prediction_undamped=Pu))
        print(f"cell {c['cell']} {c['name']}: lam {lam:.4f} delta {delta:+.4f} (fit rms {rms:.4f}); undamped "
              f"prediction CE {Pu['ce_mean']:.4f} [{Pu['ce_interval'][0]:.4f}, {Pu['ce_interval'][1]:.4f}]", flush=True)
    doc = dict(written=__import__("toqb.s2rc_device", fromlist=["stamp"]).stamp(), manifest_sha256=_sha(man_f),
               readout="z_u = clip((z - delta) / lam, -1, 1); p = (1 + z_u) / 2", cells=cells,
               script_sha256=_sha(os.path.abspath(__file__)), undamp_sha256=_sha(os.path.abspath(U.__file__)))
    with open(out_f, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    print(f"undamp.json written before any submission, sha256 {_sha(out_f)}")


def cmd_score(a):
    man_f = os.path.join(a.job, "manifest.json")
    man, und = _load(man_f), _load(os.path.join(a.job, "undamp.json"))
    if und["manifest_sha256"] != _sha(man_f):
        raise SystemExit("STOP: undamp.json was fixed for another manifest")
    raw = _load(os.path.join(a.job, "raw_counts.json"))
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    if len(rows) != len(man["pubs"]):
        raise SystemExit("STOP: the results do not cover every circuit")
    ph = {}
    for i, pub in enumerate(man["pubs"]):
        ph.setdefault(pub["cell"], {})[pub["point"]] = _p1(rows[i])
    ucell = {c["cell"]: c for c in und["cells"]}
    out = dict(job_id=raw.get("job_id"), shots=man["shots"], cells=[])
    for c in man["cells"]:
        u = ucell[c["cell"]]
        y = np.array(c["labels"])
        z = 1 - 2 * np.array([ph[c["cell"]][i] for i in range(c["points"])])
        zu = U.apply(z, u["lam"], u["delta"])
        Pu = u["prediction_undamped"]
        ce_u = _ce(zu, y)
        out["cells"].append(dict(cell=c["cell"], name=c["name"], arm=c["arm"], layers=c["layers"], lam=u["lam"],
                                 delta=u["delta"], ce_raw=_ce(z, y), acc_raw=_acc(z, y), ce_undamped=ce_u,
                                 acc_undamped=_acc(zu, y), pred_ce_undamped=Pu["ce_mean"],
                                 pred_ce_interval_undamped=Pu["ce_interval"],
                                 inside_undamped=bool(Pu["ce_interval"][0] <= ce_u <= Pu["ce_interval"][1])))
    with open(os.path.join(a.job, "undamp_score.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    L = [f"# Device job {out['job_id']}: the undamped readout (fixed before submission)", "",
         "| cell | lam / delta | CE raw -> undamped | accuracy raw -> undamped | undamped prediction [99 %] | inside |",
         "|---|---|---|---|---|---|"]
    for c in out["cells"]:
        L.append(f"| {c['name']} | {c['lam']:.3f} / {c['delta']:+.3f} | {c['ce_raw']:.4f} -> {c['ce_undamped']:.4f} | "
                 f"{c['acc_raw']:.3f} -> {c['acc_undamped']:.3f} | {c['pred_ce_undamped']:.4f} "
                 f"[{c['pred_ce_interval_undamped'][0]:.4f}, {c['pred_ce_interval_undamped'][1]:.4f}] | "
                 f"{'yes' if c['inside_undamped'] else 'no'} |")
    with open(os.path.join(a.job, "undamp_score.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="toqb.s2rc_device_undamp")
    sp = ap.add_subparsers(dest="cmd", required=True)
    f = sp.add_parser("fix")
    f.add_argument("--runs", required=True)
    f.add_argument("--job", required=True)
    f.add_argument("--traj", type=int, default=1024)
    s = sp.add_parser("score")
    s.add_argument("--job", required=True)
    a = ap.parse_args(argv)
    try:
        (cmd_fix if a.cmd == "fix" else cmd_score)(a)
    except U.Stop as exc:
        raise SystemExit(f"STOP: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
