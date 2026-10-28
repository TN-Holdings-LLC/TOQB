"""The signal-on-the-device test (2026-10-26, draft for a later device day): how much of a random ring classifier's
noiseless output each compiler's circuits keep on the device, against the twin of the day's calibration. No labels and
no training: z_device ~ lam z_noiseless + delta over P random inputs of one random model, per arm.

    [home]  python -m toqb.s2rc_device fetch --backend ibm_kingston --out DAY/fetch
    [pod]   python -m toqb.lam_device build DAY/fetch RUNS --arm fold:rule --n 13 --L 16 --mseed 0 --P 48 \\
                --shots 250 --traj 256                     (one per arm; the same model and inputs for every arm)
    [pod]   python -m toqb.s2rc_device assemble --fetch DAY/fetch --runs RUNS --out JOB --max-seconds 20
    [home]  python -m toqb.s2rc_device submit --job JOB ; python -m toqb.s2rc_device result --job JOB
    [any]   python -m toqb.lam_device score JOB RUNS
    [pod]   python -m toqb.lam_device rehearse RUNS [--shots 250 --points P --reps 2000]   (before any device: the job's outcome
                if the device were the day's twin -- each arm's slope and the difference of every two arms, with the
                shot noise drawn `reps` times; how often the proposed rule (difference > 2 standard errors) would
                decide)

`build` writes RUNS/<name>.json and .qpy in the form `toqb.s2rc_device assemble` reads. The model and inputs are
fold_lam's (seed 1000 n + L + 100000 mseed; inputs uniform in [-1, 1], P of them). `assemble` needs labels: they are
the sign of the noiseless z (+1 at 0), written as "test_labels" only so that the job can be assembled; nothing is
scored against them. The twin's lam and delta (fixed before submission) and the noiseless z are in the record.

`score` fits each cell's device z on the noiseless z (least squares; the slope's standard error from the residuals),
and reports it beside the twin's; for two cells of the same (n, L, mseed) the difference of slopes and its standard
error. Nothing here connects to IBM.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

import numpy as np


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def model_inputs(n, L, mseed, P):
    from toqb import task_loop as TL
    rng = np.random.default_rng(1000 * n + L + 100000 * mseed)
    theta = rng.uniform(-1, 1, TL.n_params(n, L))
    X = rng.uniform(-1, 1, (P, n))
    return theta, X


def noiseless_z(theta, X, n, L):
    from qiskit.quantum_info import Statevector
    from toqb import task_loop as TL
    out = []
    for x in X:
        q = TL.model_circuit(TL.angle_list(theta, x, n, L, np.pi / 2), n, L).remove_final_measurements(inplace=False)
        out.append(1 - 2 * Statevector(q).probabilities([0])[1])
    return np.array(out)


def fit(zd, zl):
    A = np.vstack([zl, np.ones_like(zl)]).T
    (lam, delta), res, _, _ = np.linalg.lstsq(A, zd, rcond=None)
    r = zd - lam * zl - delta
    dof = max(len(zl) - 2, 1)
    s2 = float(r @ r) / dof
    se = float(np.sqrt(s2 / np.sum((zl - zl.mean()) ** 2)))
    return float(lam), float(delta), se, float(np.corrcoef(zl, zd)[0, 1])


def cmd_build(argv):
    import argparse
    p = argparse.ArgumentParser(prog="lam_device build")
    p.add_argument("fetch")
    p.add_argument("out")
    p.add_argument("--arm", required=True)
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--L", type=int, required=True)
    p.add_argument("--mseed", type=int, default=0)
    p.add_argument("--P", type=int, default=48)
    p.add_argument("--shots", type=int, default=250)
    p.add_argument("--traj", type=int, default=256)
    p.add_argument("--kind", default="classifier", choices=["classifier", "kising"])
    p.add_argument("--h", type=float, default=0.6)
    p.add_argument("--twin", default="sim", choices=["sim", "none"],
                   help="none: no twin (rings too large to simulate); the job's p1 stand-in is the noiseless value")
    a = p.parse_args(argv)
    from toqb import s2r as S
    from toqb import s2r2 as S2
    from toqb.s2rc import predict_job
    tfile = os.path.abspath(os.path.join(a.fetch, "target.pkl"))
    fj = json.load(open(os.path.join(a.fetch, "fetch.json"), encoding="utf-8"))
    if sha256_file(tfile) != fj["target_sha256"]:
        print("STOP: target.pkl differs from fetch.json's hash", file=sys.stderr)
        return 2
    if a.kind == "kising":  # toqb.kising: X-basis inputs drawn as in its main (seed number = mseed), exact reference
        name = f"kising_n{a.n}_L{a.L}_s{a.mseed}_h{a.h:g}-{a.arm.replace(':', '_')}"
    else:
        name = f"lam_n{a.n}_L{a.L}_m{a.mseed}-{a.arm.replace(':', '_')}"
    os.makedirs(a.out, exist_ok=True)
    jf, qf = os.path.join(a.out, name + ".json"), os.path.join(a.out, name + ".qpy")
    for f in (jf, qf):
        if os.path.exists(f):
            print(f"STOP: {f} exists: a run never overwrites another", file=sys.stderr)
            return 2
    t0 = time.perf_counter()
    if a.kind == "kising":
        from toqb import kising as K
        rng = np.random.default_rng(8_000_000 + 1000 * a.n + a.L + 100000 * a.mseed)
        X = [rng.choice([1, -1], a.n) for _ in range(a.P)]
        theta = np.zeros(0)
        zl = np.array([K.z_noiseless(s, a.n, a.L, a.h) for s in X])
    else:
        theta, X = model_inputs(a.n, a.L, a.mseed, a.P)
        zl = noiseless_z(theta, X, a.n, a.L)
    labels = np.where(zl >= 0, 1, -1)
    task = dict(n=a.n, layers=a.L, enc=float(np.pi / 2))
    pr = dict(traj=a.traj, seed=7, shots=a.shots, reps=2000, level=0.99)
    plan = dict(name=f"lam device test: {name}", device="file:" + tfile, verify=False, task=task, predict=pr,
                standin=dict(t12=0.3, over=0.01, zz_hz=1e4, seed=20261017))
    R = S2.Runner(plan, a.arm)
    if a.kind == "kising":
        cs = [R.arm.compile(K.circuit(s, a.n, a.L, a.h)) for s in X]
    else:
        cs = [R.compile(theta, x) for x in X]
    if a.twin == "none":
        zt = np.asarray(zl, dtype=float)  # stand-in for assemble's bookkeeping only; no twin prediction exists
        twin = None
    else:
        zt = R.z("sim", cs, a.traj, pr["seed"])
        lam, delta, se, corr = fit(zt, zl)
        twin = dict(lam=lam, delta=delta, se=se, corr=corr, z=[float(v) for v in zt])
    p1 = np.clip((1 - np.asarray(zt, dtype=float)) / 2, 0, 1)
    d, q2 = R.arm.duration(cs[0], (a.n, a.L))
    rec = dict(kind="s2rc", lam_test=True, arm=a.arm, seed=a.mseed, plan=plan["name"], task=task, predict=pr,
               standin=plan["standin"], verify=False, device=plan["device"], target_sha256=fj["target_sha256"],
               version=R.arm.version(), final_mean=[float(v) for v in theta], loops=0, started=S._cest(),
               inputs=[[float(v) for v in x] for x in X], noiseless_z=[float(v) for v in zl],
               twin=twin,
               q2=int(q2), us=round(d * 1e6, 3))
    if a.kind == "kising":
        rec.update(kising=dict(h=a.h, J="pi/4", readout_sign=K.SIGN_OF_READOUT))
    rec["prediction"] = predict_job(p1, labels, a.shots, pr["reps"], pr["level"], pr["seed"] + 1, traj=a.traj)
    rec["prediction_shots_only"] = predict_job(p1, labels, a.shots, pr["reps"], pr["level"], pr["seed"] + 1)
    rec["prediction"]["twin_p1"] = [float(x) for x in p1]
    rec["test_labels"] = [int(v) for v in labels]  # the noiseless sign: only so that assemble can read the record
    from qiskit import qpy
    with open(qf, "wb") as f:
        qpy.dump(list(cs), f)
    rec["export"] = dict(qpy=os.path.basename(qf), circuits=len(cs), sha256=sha256_file(qf))
    rec.update(wall_s=time.perf_counter() - t0, structural_fail=R.arm.structural_fail,
               on_failed_ops=R.arm.on_failed_ops, ended=S._cest())
    rec["valid"] = not R.arm.structural_fail and not R.arm.on_failed_ops
    json.dump(rec, open(jf, "w", encoding="utf-8"))
    tw = (f"twin lam {twin['lam']:.3f} +- {twin['se']:.3f} (delta {twin['delta']:+.3f}, corr {twin['corr']:.3f})"
          if twin else "no twin")
    print(f"{name}: {len(cs)} circuits, {q2} two-qubit gates, {d * 1e6:.2f} us; {tw}; noiseless z spread "
          f"{zl.std():.3f}; valid {rec['valid']}")
    return 0 if rec["valid"] else 2


def cmd_score(argv):
    from toqb.s2rc_device import p1_of_counts
    job, runs = argv[0], argv[1]
    man = json.load(open(os.path.join(job, "manifest.json")))
    raw = json.load(open(os.path.join(job, "raw_counts.json")))
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    cells = []
    for cid, c in enumerate(man["cells"]):
        rf = os.path.join(runs, c["name"] + ".json")
        rec = json.load(open(rf))
        if sha256_file(rf) != c["run_sha256"]:
            raise SystemExit(f"STOP: {rf} differs from the manifest")
        zl = np.array(rec["noiseless_z"])
        zd = np.zeros(len(zl))
        for i, pub in enumerate(man["pubs"]):
            if pub["cell"] == cid:
                zd[pub["point"]] = 1 - 2 * p1_of_counts(rows[i])
        lam, delta, se, corr = fit(zd, zl)
        cells.append(dict(name=c["name"], arm=rec["arm"], n=rec["task"]["n"], L=rec["task"]["layers"],
                          mseed=rec["seed"], device=dict(lam=lam, delta=delta, se=se, corr=corr),
                          twin=(rec["twin"] | {"z": None}) if rec["twin"] else None, q2=rec.get("q2"), us=rec.get("us"),
                          device_z=[float(v) for v in zd]))
        tw = f"twin {rec['twin']['lam']:.3f} +- {rec['twin']['se']:.3f}" if rec["twin"] else "no twin"
        print(f"{c['name']:40s} device lam {lam:.3f} +- {se:.3f} (corr {corr:.3f}) | {tw} | {rec.get('q2')} "
              f"two-qubit gates, {rec.get('us')} us")
    groups = {}
    for c in cells:
        groups.setdefault((c["n"], c["L"], c["mseed"]), []).append(c)
    for k, g in sorted(groups.items()):
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a, b = g[i], g[j]
                dlam = a["device"]["lam"] - b["device"]["lam"]
                se = float(np.hypot(a["device"]["se"], b["device"]["se"]))
                tw = (f"twin {a['twin']['lam'] - b['twin']['lam']:+.3f}" if a["twin"] and b["twin"] else "no twin")
                print(f"n {k[0]} L {k[1]} model {k[2]}: {a['arm']} - {b['arm']}: device {dlam:+.3f} +- {se:.3f}; {tw}")
    out = os.path.join(job, "lam_score.json")
    if os.path.exists(out):
        print(f"{out} exists; not written")
    else:
        json.dump(dict(cells=cells), open(out, "w"))
    return 0


def cmd_rehearse(argv):
    import glob
    runs = argv[0]
    shots = int(argv[argv.index("--shots") + 1]) if "--shots" in argv else None
    reps = int(argv[argv.index("--reps") + 1]) if "--reps" in argv else 2000
    npts = int(argv[argv.index("--points") + 1]) if "--points" in argv else None  # the first P points (a build's
    # inputs are drawn row by row, so its first P equal a build with P)
    recs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(runs, "*.json")))]
    recs = [r for r in recs if r.get("lam_test") and r.get("twin")]  # no rehearsal without a twin
    rng = np.random.default_rng(12345)
    draws = {}
    for r in recs:
        zl, zt = np.array(r["noiseless_z"])[:npts], np.array(r["twin"]["z"])[:npts]
        N = shots or r["predict"]["shots"]
        p1 = np.clip((1 - zt) / 2, 0, 1)
        lam_se = []
        for _ in range(reps):
            zd = 1 - 2 * rng.binomial(N, p1) / N
            lam, _, se, _ = fit(zd, zl)
            lam_se.append((lam, se))
        a = np.array(lam_se)
        draws[(r["task"]["n"], r["task"]["layers"], r["seed"], r["arm"])] = a
        print(f"n {r['task']['n']} L {r['task']['layers']} model {r['seed']} {r['arm']:22s} twin lam {r['twin']['lam']:.3f};"
              f" with {N} shots x {len(zl)} points: slope {a[:, 0].mean():.3f} +- {a[:, 0].std():.3f} (fit's own SE "
              f"{a[:, 1].mean():.3f}); noiseless z sd {zl.std():.3f}")
    keys = sorted(draws)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            if keys[i][:3] != keys[j][:3]:
                continue
            A, B = draws[keys[i]], draws[keys[j]]
            d = A[:, 0] - B[:, 0]
            se = np.hypot(A[:, 1], B[:, 1])
            print(f"n {keys[i][0]} model {keys[i][2]}: {keys[i][3]} - {keys[j][3]}: difference {d.mean():+.3f} +- "
                  f"{d.std():.3f}; the rule (> 2 SE) decides for the first in {np.mean(d > 2 * se):.0%}, for the "
                  f"second in {np.mean(d < -2 * se):.0%}, TIE in {np.mean(abs(d) <= 2 * se):.0%}")
    return 0


def main(argv):
    if not argv or argv[0] not in ("build", "score", "rehearse"):
        print(__doc__)
        return 1
    return {"build": cmd_build, "score": cmd_score, "rehearse": cmd_rehearse}[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
