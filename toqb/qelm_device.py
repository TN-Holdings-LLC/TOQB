"""QELM task A on a device (2026-10-30; owner: ibm_kingston only): build one job per arm from the declared teacher task,
and score the device counts against the declaration (prereg/drafts-2026-10-30/qelm_A_note.md and its addendum 1).

    python -m toqb.qelm_device build FETCH TASK_DIR RUNS --arm fold:rule [--shots 250] [--points K]
    python -m toqb.qelm_device score TASK_DIR OUT --job ARM=JOB:RUNS [--job ...] --predict PREDICT.json

TASK_DIR holds the declared noiseless.json (results/qelm-A-2026-10-30; its SHA-256 is checked against
--task-sha256 when given). `build` compiles the 984 circuits of one arm (point-major, basis-minor, as toqb.qelm) with
toqb.qelm's own compile path (canonical diagonal order), checks rule G (one measured-qubit map, no failed element) and
writes a record that `toqb.s2rc_device assemble` reads (the prediction and labels are placeholders, as lam_device).
`--points K` keeps the first K training and K test points: for tests only, never for a declared run.

`score` turns each job's full bit strings into per-qubit counts of ones (k1, rows point-major, basis-minor), then
applies the declared rules: G; Q1 (affine model, chi2/dof median <= 2); Q2 (test accuracy at S = 250 inside the
declared band of the device's row, from PREDICT.json); Q3a (rule more accurate than zipcyc, one-sided McNemar at
S = 64 and 250, Holm over the two); Q3b (rule against blind Qiskit, reported); R (baselines). Subsamples S < 250 are
drawn from the 250-shot counts without replacement, as toqb.qelm. Nothing here connects to IBM.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from toqb import qelm as Q
from toqb import kising_charge as KC


def _task(task_dir, points=None):
    r0 = json.load(open(os.path.join(task_dir, "noiseless.json")))
    X = np.array(r0["X"])
    F0 = np.array(r0["features"])
    ytr, yte = np.array(r0["y_train"]), np.array(r0["y_test"])
    ntr = len(ytr)
    if points:
        idx = list(range(points)) + list(range(ntr, ntr + points))
        X, F0 = X[idx], F0[idx]
        ytr, yte = ytr[:points], yte[:points]
    return r0, X, F0, ytr, yte


def cmd_build(argv):
    import argparse
    p = argparse.ArgumentParser(prog="qelm_device build")
    p.add_argument("fetch")
    p.add_argument("task_dir")
    p.add_argument("out")
    p.add_argument("--arm", required=True)
    p.add_argument("--shots", type=int, default=Q.SHOTS)
    p.add_argument("--points", type=int, default=None, help="tests only: the first K training and K test points")
    a = p.parse_args(argv)
    from toqb import s2r as S
    from toqb.fold_lam import active
    from toqb.s2rc import predict_job
    tfile = os.path.abspath(os.path.join(a.fetch, "target.pkl"))
    fj = json.load(open(os.path.join(a.fetch, "fetch.json"), encoding="utf-8"))
    if KC.sha256_file(tfile) != fj["target_sha256"]:
        print("STOP: target.pkl differs from fetch.json's hash", file=sys.stderr)
        return 2
    r0, X, F0, ytr, yte = _task(a.task_dir, a.points)
    n, L, enc = int(r0["n"]), int(r0["L"]), float(r0["enc"])
    name = f"qelmA_n{n}_L{L}-{a.arm.replace(':', '_')}"
    os.makedirs(a.out, exist_ok=True)
    jf, qf = os.path.join(a.out, name + ".json"), os.path.join(a.out, name + ".qpy")
    for f in (jf, qf):
        if os.path.exists(f):
            print(f"STOP: {f} exists: a run never overwrites another", file=sys.stderr)
            return 2
    t0 = time.perf_counter()
    cs, maps, A = Q.build_features(a.arm, "file:" + tfile, X, n, L, enc)
    ok_g = len(maps) == 1 and not A.structural_fail and not A.on_failed_ops
    ops = cs[0].count_ops()
    d, q2 = A.duration(cs[0], (n, L)) if hasattr(A, "duration") else (float("nan"), int(ops.get("cz", 0)))
    P = len(cs)
    labels = np.ones(P, dtype=int)
    p1 = np.full(P, 0.5)
    pr = dict(traj=0, seed=7, shots=a.shots, reps=50, level=0.99)
    task = dict(n=n, layers=L, enc=enc)
    rec = dict(kind="s2rc", lam_test=True, qelm_test=True, arm=a.arm, seed=0, plan=f"QELM A: {name}", task=task,
               predict=pr, standin=dict(t12=0.3, over=0.01, zz_hz=1e4, seed=20261017), verify=False,
               device="file:" + tfile, target_sha256=fj["target_sha256"], version=A.version(), final_mean=[], loops=0,
               started=S._cest(), task_sha256=KC.sha256_file(os.path.join(a.task_dir, "noiseless.json")),
               points_override=a.points, measured_maps=len(maps),
               measured_qubits={str(k): v for k, v in sorted(Q.measured_map(cs[0]).items())},
               points=[dict(point=i // 3, basis=Q.BASES[i % 3]) for i in range(P)],
               inputs=[[0] * n for _ in range(P)], noiseless_z=[0.0] * P, twin=None,
               q2=int(q2), us=round(d * 1e6, 3) if d == d else None, active=int(active(cs[0])),
               cz_per_circuit=int(ops.get("cz", 0)))
    rec["prediction"] = predict_job(p1, labels, a.shots, pr["reps"], pr["level"], pr["seed"] + 1)
    rec["prediction_shots_only"] = rec["prediction"]
    rec["prediction"]["twin_p1"] = [float(x) for x in p1]
    rec["test_labels"] = [int(v) for v in labels]  # placeholders: only so that assemble can read the record
    from qiskit import qpy
    with open(qf, "wb") as f:
        qpy.dump(list(cs), f)
    rec["export"] = dict(qpy=os.path.basename(qf), circuits=P, sha256=KC.sha256_file(qf))
    rec.update(wall_s=time.perf_counter() - t0, structural_fail=A.structural_fail, on_failed_ops=A.on_failed_ops,
               ended=S._cest(), valid=bool(ok_g), rule_G="PASS" if ok_g else "FAIL")
    json.dump(rec, open(jf, "w", encoding="utf-8"))
    print(f"{name}: {P} circuits, {rec['cz_per_circuit']} CZ per circuit, measured maps {len(maps)}: rule G "
          f"{rec['rule_G']}")
    return 0 if ok_g else 2


def k1_from_job(job, runs):
    """Per-qubit counts of ones, rows in the record's point order (point-major, basis-minor), and the shots."""
    man = json.load(open(os.path.join(job, "manifest.json")))
    raw = json.load(open(os.path.join(job, "raw_counts.json")))
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    recs = []
    for cid, c in enumerate(man["cells"]):
        rf = os.path.join(runs, c["name"] + ".json")
        if KC.sha256_file(rf) != c["run_sha256"]:
            raise SystemExit(f"STOP: {rf} differs from the manifest")
        rec = json.load(open(rf))
        if rec.get("qelm_test"):
            recs.append((cid, rec))
    if len(recs) != 1:
        raise SystemExit("STOP: one QELM record per job expected")
    cid, rec = recs[0]
    n = rec["task"]["n"]
    P = len(rec["points"])
    k1 = np.zeros((P, n), dtype=int)
    S = None
    for k, pub in enumerate(man["pubs"]):
        if pub["cell"] != cid:
            continue
        counts = rows[k]
        S = sum(counts.values())
        for key, v in counts.items():
            b = key.replace(" ", "")[::-1]
            for q in range(n):
                if b[q] == "1":
                    k1[pub["point"], q] += v
    return rec, k1, S


def holm_two(pa, pb):
    """Holm's step-down for two p values at alpha = 0.05: (reject a, reject b)."""
    ps = sorted([(pa, 0), (pb, 1)])
    rej = [False, False]
    if ps[0][0] <= 0.025:
        rej[ps[0][1]] = True
        if ps[1][0] <= 0.05:
            rej[ps[1][1]] = True
    return rej


def cmd_score(argv):
    import argparse
    from scipy.stats import binomtest
    p = argparse.ArgumentParser(prog="qelm_device score")
    p.add_argument("task_dir")
    p.add_argument("out")
    p.add_argument("--job", action="append", required=True, help="ARM=JOB_DIR:RUNS_DIR")
    p.add_argument("--predict", required=True, help="the declared predictions of the device's row (predict_*.json)")
    p.add_argument("--points", type=int, default=None)
    a = p.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    r0, X, F0, ytr, yte = _task(a.task_dir, a.points)
    n = int(r0["n"])
    ntr = len(ytr)
    F0tr, F0te = F0[:ntr], F0[ntr:]
    pred = json.load(open(a.predict))
    res = dict(task_sha256=KC.sha256_file(os.path.join(a.task_dir, "noiseless.json")), arms={},
               R=dict(raw=Q.accuracy(Q.ols_predict(Q.ols_fit(X[:ntr], ytr), X[ntr:]), yte),
                      ceiling=Q.accuracy(Q.ols_predict(Q.ols_fit(F0tr, ytr), F0te), yte),
                      majority=float(max(np.mean(yte == 1), np.mean(yte == -1)))))
    corr = {}
    for spec in a.job:
        arm, rest = spec.split("=", 1)
        job, runs = rest.split(":", 1)
        rec, k1, S0 = k1_from_job(job, runs)
        Fd = Q.device_features(k1, S0, n)
        aa, lam = Q.affine_fit(Fd[:ntr], F0tr)
        m = np.clip(aa + lam * F0tr, -1, 1)
        chi = np.mean((Fd[:ntr] - m) ** 2 / (np.maximum(1 - m ** 2, 1e-6) / S0), axis=0)
        ar = dict(rule_G=rec.get("rule_G"), cz_per_circuit=rec.get("cz_per_circuit"),
                  lambda_median=[float(np.median(lam[i * n:(i + 1) * n])) for i in range(3)],
                  chi2_median=float(np.median(chi)), chi2_share_gt2=float(np.mean(chi > 2)), acc={})
        ar["Q1"] = "HOLDS" if ar["chi2_median"] <= 2 else "FAILS"
        for S in Q.SUBSAMPLE:
            kS = Q.subsample(k1, S0, S, Q.SHOT_SEED + 7 * S)
            FdS = Q.device_features(kS, S, n)
            z = Q.ols_predict(Q.ols_fit(FdS[:ntr], ytr), FdS[ntr:])
            ar["acc"][S] = Q.accuracy(z, yte)
            corr.setdefault(S, {})[arm] = Q.correct(z, yte)
        band = pred["arms"].get(arm, {}).get("bands", {}).get("250")
        if band:
            ar["Q2"] = dict(band=band, verdict="INSIDE" if band[1] <= ar["acc"][250] <= band[2] else "OUTSIDE")
        res["arms"][arm] = ar
        json.dump(dict(kind="qelm_device", arm=arm, shots=S0, k1=k1.tolist()), open(os.path.join(a.out, f"device_{arm.replace(':', '_')}.json"), "w"))

    def one_sided(x, y):
        b, c = int(np.sum((x == 1) & (y == 0))), int(np.sum((x == 0) & (y == 1)))
        return b, c, (1.0 if b + c == 0 else float(binomtest(b, b + c, 0.5, alternative="greater").pvalue))
    for other, key in (("fold:zipcyc", "Q3a"), ("qiskit:2:blind:template", "Q3b")):
        if "fold:rule" in res["arms"] and other in res["arms"]:
            t = {S: one_sided(corr[S]["fold:rule"], corr[S][other]) for S in (64, 250)}
            rej = holm_two(t[64][2], t[250][2])
            res[key] = dict(S64=t[64], S250=t[250], holm=rej, verdict="WIN" if any(rej) else "not")
    json.dump(res, open(os.path.join(a.out, "qelm_device_score.json"), "w"), indent=1, default=str)
    print(f"R: raw {res['R']['raw']:.3f}, ceiling {res['R']['ceiling']:.3f}, majority {res['R']['majority']:.3f}")
    for arm, ar in res["arms"].items():
        q2 = ar.get("Q2", {})
        print(f"{arm}: G {ar['rule_G']}; lambda (X, Y, Z) {', '.join(f'{v:.3f}' for v in ar['lambda_median'])}; "
              f"Q1 chi2 {ar['chi2_median']:.2f} ({ar['Q1']}); acc " +
              ", ".join(f"S {S} {v:.3f}" for S, v in ar["acc"].items()) +
              (f"; Q2 band {q2['band'][1]:.3f}-{q2['band'][2]:.3f}: {q2['verdict']}" if q2 else ""))
    for key in ("Q3a", "Q3b"):
        if key in res:
            x = res[key]
            print(f"{key}: S 64 {x['S64'][0]} / {x['S64'][1]} p {x['S64'][2]:.3g}; S 250 {x['S250'][0]} / "
                  f"{x['S250'][1]} p {x['S250'][2]:.3g}; Holm {x['holm']}: {x['verdict']}"
                  + (" (reported, not judged)" if key == "Q3b" else ""))
    return 0


def main(argv):
    cmds = dict(build=cmd_build, score=cmd_score)
    if not argv or argv[0] not in cmds:
        print(__doc__)
        return 2
    return cmds[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
