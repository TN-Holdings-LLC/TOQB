"""Design C's device step: the day's Target at home, training and prediction on the pod, one job from home, scoring.

The IBM API key stays at home: only `fetch`, `submit` and `result` connect to IBM, and they use the account saved
beforehand in the home terminal with QiskitRuntimeService.save_account(...); this module never reads or writes the
key. The pod gets the Target as a file and returns the compiled circuits as a file. Nothing here runs git or pip.

    [home, VPN OFF]  python -m toqb.s2rc_device fetch    --backend ibm_fez --out DAY/fetch
    [pod]            python -m toqb.s2rc_device plans    --target <pod>/fetch/target.pkl --out PLANS --seeds 301 \\
                         --p8 150 --p16 500 --shots 250 --lr 0.4 --loops 2000
    [pod]            python -m toqb.s2rc PLANS/L8_s301.json RUNS/L8_s301-psfai_template.json psfai:template \\
                         --qpy RUNS/L8_s301-psfai_template.qpy          (one per plan and compiler)
    [pod]            python -m toqb.s2rc_device assemble --fetch <pod>/fetch --runs RUNS --out JOB --max-seconds 150
    [home, VPN OFF]  python -m toqb.s2rc_device submit   --job JOB
    [home, VPN OFF]  python -m toqb.s2rc_device result   --job JOB
    [anywhere]       python -m toqb.s2rc_device score    --job JOB

`fetch --fake FakeFez` and `submit --local` (Qiskit Aer instead of IBM; the fake device's noise when the Target came
from a fake device, else noiseless) run the whole flow with no IBM connection: the procedure check.

What `assemble` checks before it writes anything (it stops on the first failure):
- every run is valid, predicted without the stand-in ("verify": false), on the fetched Target (same SHA-256), and its
  QPY file is the one its record names (same SHA-256);
- every circuit uses only operations and qubit pairs the Target supports, and no element reported as failed;
- the job's QPU time by the time model below is at most --max-seconds.
Its manifest (circuits, predictions, labels, hashes) is written before any submission; `submit` refuses a job folder
whose files differ from it, a job already submitted, and, on IBM, a backend whose calibration time differs from the
fetched one (design C section 5: retrain on a new calibration).

QPU time model: 0.036 s per circuit + 0.00027 s per shot (+ about 3 s per job). Checked on 2026-10-19 against three
earlier jobs on ibm_marrakesh: 60 circuits x 6,000 shots, 99.4 s predicted, 102 s billed; 81 circuits, 198,000 shots,
56.4 s against 56 s; 4 circuits, 16,000 shots, 4.5 s against 7 s.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import math
import os
import pickle
import sys

import numpy as np

PER_CIRCUIT_S, PER_SHOT_S, PER_JOB_S = 0.036, 0.00027, 3.0
ALPHA = 0.01
CLIP = 1e-4


def stamp():
    now = dt.datetime.now(dt.timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        local = now.astimezone(ZoneInfo("Europe/Zurich")).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:  # noqa: BLE001
        local = "?"
    return f"{now.isoformat(timespec='seconds')} ({local})"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def qpu_seconds(n_circuits, shots):
    return n_circuits * PER_CIRCUIT_S + n_circuits * shots * PER_SHOT_S + PER_JOB_S


def calibration_time(backend):
    try:
        return str(backend.properties().last_update_date)
    except Exception:  # noqa: BLE001
        return None


def _dump_json(path, obj):
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=str)
    os.replace(path + ".tmp", path)


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _service():
    from qiskit_ibm_runtime import QiskitRuntimeService
    try:
        return QiskitRuntimeService()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit("No usable saved IBM account (" + type(exc).__name__ + "). Save it once in the terminal with "
                         "QiskitRuntimeService.save_account(...); never paste the key into a file or chat.")


# ------------------------------------------------------------------------------------------------ scoring rules

def ce(z, y):
    """Cross-entropy of <Z> values z against labels y in {+1, -1} (+1 <-> <Z> > 0 <-> P(1) < 0.5): the same formula as
    toqb.s2r2._ce (p = (1 + z) / 2 clipped to [1e-4, 1 - 1e-4]; -log p for y = +1, -log(1 - p) for y = -1)."""
    p = np.clip((1 + np.asarray(z, float)) / 2, CLIP, 1 - CLIP)
    return float(np.mean(-np.where(np.asarray(y) > 0, np.log(p), np.log(1 - p))))


def acc_half(z, y):
    """Accuracy with a tie (<Z> = 0) counted 0.5, as in the predictions."""
    z, y = np.asarray(z, float), np.asarray(y)
    return float(np.mean(np.where(z == 0, 0.5, (np.sign(z) == y).astype(float))))


def holm(pvals):
    """Holm-adjusted p values (same order as given)."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, run = [0.0] * m, 0.0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (m - k) * pvals[i]))
        adj[i] = run
    return adj


def p1_of_counts(counts, clbit=0):
    """Fraction of shots with clbit `clbit` = 1 (Qiskit keys: clbit 0 rightmost)."""
    shots = sum(counts.values())
    one = sum(v for k, v in counts.items() if k.replace(" ", "")[-1 - clbit] == "1")
    return one / shots


# ------------------------------------------------------------------------------------------------ fetch (home)

def cmd_fetch(a):
    out = a.out
    if os.path.exists(os.path.join(out, "fetch.json")):
        raise SystemExit(f"{out}/fetch.json exists: a fetch is never overwritten (use a new folder)")
    if a.fake:
        from qiskit_ibm_runtime import fake_provider
        backend = getattr(fake_provider, a.fake)()
    else:
        if not a.backend:
            raise SystemExit("--backend is required (or --fake for the procedure check)")
        backend = _service().backend(a.backend)
    target = backend.target
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "target.pkl"), "wb") as f:
        pickle.dump(target, f)
    info = dict(written=stamp(), backend=backend.name, fake=bool(a.fake), calibration_time=calibration_time(backend),
                num_qubits=target.num_qubits, target_sha256=sha256_file(os.path.join(out, "target.pkl")),
                script_sha256=sha256_file(os.path.abspath(__file__)))
    _dump_json(os.path.join(out, "fetch.json"), info)
    print(f"{info['written']} saved the Target of {info['backend']} (calibration {info['calibration_time']}; "
          f"{info['num_qubits']} qubits) to {out}/target.pkl, sha256 {info['target_sha256'][:16]}...")


# ------------------------------------------------------------------------------------------------ plans (pod)

def cmd_plans(a):
    os.makedirs(a.out, exist_ok=True)
    target = os.path.abspath(a.target)
    written = []
    for L, P in ((8, a.p8), (16, a.p16)):
        for s in a.seeds:
            plan = {"name": f"S2RC device L{L} s{s}", "device": f"file:{target}", "verify": False,
                    "task": {"n": 10, "layers": L, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_angle": 0.3,
                             "teacher_gap": 0.2, "n_train": 64, "n_test": P},
                    "train": {"seed": s, "init": 1.0, "pairs": 8, "sim_batch": 4, "sim_traj": 32, "h": 0.1, "lr": a.lr,
                              "loops": a.loops, "curve_every": 200, "curve_points": min(100, P), "curve_traj": 64},
                    "predict": {"traj": a.traj, "shots": a.shots, "reps": a.reps, "level": 0.99, "seed": 50000 + s},
                    "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}
            f = os.path.join(a.out, f"L{L}_s{s}.json")
            if os.path.exists(f):
                raise SystemExit(f"{f} exists: plans are never overwritten")
            _dump_json(f, plan)
            written.append(f)
    print("\n".join(written))


# ------------------------------------------------------------------------------------------------ assemble (pod)

def _isa_problems(qc, target, failed_edges, failed_qubits):
    probs = []
    for inst in qc.data:
        name = inst.operation.name
        if name == "barrier":
            continue
        qargs = tuple(qc.find_bit(q).index for q in inst.qubits)
        if not target.instruction_supported(name, qargs):
            probs.append(f"{name}{qargs} not supported")
        elif len(qargs) == 2 and (qargs in failed_edges or qargs[::-1] in failed_edges):
            probs.append(f"{name}{qargs} on a failed coupler")
        elif len(qargs) == 1 and qargs[0] in failed_qubits:
            probs.append(f"{name}{qargs} on a failed qubit")
    if qc.num_qubits != target.num_qubits:
        probs.append(f"circuit has {qc.num_qubits} qubits, the Target {target.num_qubits}")
    return probs


def cmd_assemble(a):
    from qiskit import qpy
    from toqb.devices import _failed
    fetch = _load_json(os.path.join(a.fetch, "fetch.json"))
    tfile = os.path.join(a.fetch, "target.pkl")
    if sha256_file(tfile) != fetch["target_sha256"]:
        raise SystemExit("STOP: target.pkl differs from fetch.json's hash")
    with open(tfile, "rb") as f:
        target = pickle.load(f)
    fe, fq = _failed(target)
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists; a job folder is never overwritten")
    runs = sorted(glob.glob(os.path.join(a.runs, "*.json")))
    if not runs:
        raise SystemExit(f"STOP: no run records in {a.runs}")
    cells, circuits, pubs, shots = [], [], [], None
    for rf in runs:
        r = _load_json(rf)
        name = os.path.basename(rf)[:-5]
        if not r.get("valid") or "prediction" not in r:
            raise SystemExit(f"STOP: {name} is not a valid run with a prediction ({r.get('error')})")
        if r.get("verify", True):
            raise SystemExit(f"STOP: {name} was a rehearsal run (verify true), not a device run")
        if r.get("target_sha256") != fetch["target_sha256"]:
            raise SystemExit(f"STOP: {name} was trained on another Target than the fetched one")
        ex = r.get("export") or {}
        qf = os.path.join(a.runs, ex.get("qpy", name + ".qpy"))
        if not ex or not os.path.exists(qf) or sha256_file(qf) != ex["sha256"]:
            raise SystemExit(f"STOP: {name}'s QPY file is missing or differs from its record")
        with open(qf, "rb") as f:
            cs = qpy.load(f)
        P = len(r["test_labels"])
        if not (len(cs) == P == len(r["prediction"]["twin_p1"])):
            raise SystemExit(f"STOP: {name}: {len(cs)} circuits, {P} labels, {len(r['prediction']['twin_p1'])} predictions")
        n_shots = r["predict"]["shots"]
        if shots is None:
            shots = n_shots
        elif shots != n_shots:
            raise SystemExit(f"STOP: {name} predicts {n_shots} shots per point, an earlier run {shots}")
        for i, c in enumerate(cs):
            pr = _isa_problems(c, target, fe, fq)
            if pr:
                raise SystemExit(f"STOP: {name} point {i}: " + "; ".join(pr[:3]))
        cid = len(cells)
        pp, so = r["prediction"], r["prediction_shots_only"]
        cells.append(dict(cell=cid, name=name, arm=r["arm"], seed=r["seed"], layers=r["task"]["layers"], points=P,
                          run_sha256=sha256_file(rf), qpy_sha256=ex["sha256"], version=r.get("version"),
                          labels=r["test_labels"], twin_p1=pp["twin_p1"],
                          prediction=dict(ce_mean=pp["ce_mean"], ce_interval=pp["ce_interval"],
                                          acc_mean=pp["acc_mean"], acc_interval=pp["acc_interval"],
                                          ce_exact=pp["ce_exact"], level=pp["level"], reps=pp["reps"]),
                          prediction_shots_only=dict(ce_interval=so["ce_interval"], acc_interval=so["acc_interval"])))
        for i, c in enumerate(cs):
            circuits.append(c)
            pubs.append(dict(cell=cid, point=i))
    secs = qpu_seconds(len(circuits), shots)
    print(f"{len(cells)} cells, {len(circuits)} circuits x {shots} shots: predicted QPU time {secs:.1f} s "
          f"(limit {a.max_seconds} s)")
    if secs > a.max_seconds:
        raise SystemExit("STOP: the job would exceed --max-seconds; nothing written")
    os.makedirs(a.out)
    with open(os.path.join(a.out, "circuits.qpy"), "wb") as f:
        qpy.dump(circuits, f)
    man = dict(written=stamp(), fetch=fetch, shots=shots, qpu_seconds_predicted=round(secs, 1),
               qpu_model=dict(per_circuit_s=PER_CIRCUIT_S, per_shot_s=PER_SHOT_S, per_job_s=PER_JOB_S),
               qpy_sha256=sha256_file(os.path.join(a.out, "circuits.qpy")), cells=cells, pubs=pubs,
               script_sha256=sha256_file(os.path.abspath(__file__)), job_id=None)
    _dump_json(os.path.join(a.out, "manifest.json"), man)
    print(f"{man['written']} manifest written before any submission: {a.out}/manifest.json, sha256 "
          f"{sha256_file(os.path.join(a.out, 'manifest.json'))}")


# ------------------------------------------------------------------------------------------------ submit / result (home)

def _read_job(job):
    man = _load_json(os.path.join(job, "manifest.json"))
    if sha256_file(os.path.join(job, "circuits.qpy")) != man["qpy_sha256"]:
        raise SystemExit("STOP: circuits.qpy differs from the manifest's hash")
    return man


def cmd_submit(a):
    from qiskit import qpy
    man = _read_job(a.job)
    sub_file = os.path.join(a.job, "submission.json")
    if os.path.exists(sub_file):
        raise SystemExit(f"STOP: {sub_file} exists: this job was already submitted")
    with open(os.path.join(a.job, "circuits.qpy"), "rb") as f:
        circs = qpy.load(f)
    if len(circs) != len(man["pubs"]):
        raise SystemExit("STOP: the QPY file and the manifest disagree on the number of circuits")
    N = man["shots"]
    if a.local:
        from qiskit_aer import AerSimulator
        if man["fetch"].get("fake") and not a.noiseless:
            from qiskit_ibm_runtime import fake_provider
            sim = AerSimulator.from_backend(getattr(fake_provider, _fake_class(man["fetch"]["backend"]))())
        else:
            sim = AerSimulator()
        t_sub = stamp()
        res = sim.run(circs, shots=N, seed_simulator=a.seed).result()
        rows = [dict(pub=i, counts=dict(res.get_counts(i))) for i in range(len(circs))]
        _dump_json(sub_file, dict(job_id=f"local-{a.seed}", submitted=t_sub, local=True,
                                  simulator=str(sim.name) + ("" if sim.options.noise_model is None else " with noise")))
        _dump_json(os.path.join(a.job, "raw_counts.json"),
                   dict(fetched=stamp(), job_id=f"local-{a.seed}", status="DONE (local)", metrics={}, rows=rows))
        print(f"{stamp()} LOCAL run (no IBM connection): {len(circs)} circuits x {N} shots; raw_counts.json written")
        return
    from qiskit_ibm_runtime import SamplerV2
    backend = _service().backend(man["fetch"]["backend"])
    cal = calibration_time(backend)
    if cal != man["fetch"]["calibration_time"]:
        raise SystemExit(f"STOP: {backend.name}'s calibration is now {cal}, not the fetched "
                         f"{man['fetch']['calibration_time']}. Design C section 5: fetch again and retrain; not submitted.")
    sampler = SamplerV2(mode=backend)
    sampler.options.dynamical_decoupling.enable = False
    sampler.options.twirling.enable_gates = False
    sampler.options.twirling.enable_measure = False
    t_sub = stamp()
    job = sampler.run([(c, None, N) for c in circs])
    _dump_json(sub_file, dict(job_id=job.job_id(), submitted=t_sub, local=False, backend=backend.name,
                              calibration_at_submit=cal, options="dynamical decoupling off, twirling off (gates and "
                              "measure); SamplerV2 applies no other error mitigation"))
    print(f"{stamp()} submitted job {job.job_id()} ({len(circs)} circuits x {N} shots) to {backend.name}. "
          f"Results are not read here.")


def _fake_class(name):
    """'fake_fez' -> 'FakeFez' (the fake backends' names)."""
    return "".join(p.capitalize() for p in name.split("_"))


def cmd_result(a):
    import time
    _read_job(a.job)
    sub = _load_json(os.path.join(a.job, "submission.json"))
    if sub.get("local"):
        print("local run: raw_counts.json was written by submit")
        return
    raw_file = os.path.join(a.job, "raw_counts.json")
    if os.path.exists(raw_file):
        raise SystemExit(f"{raw_file} exists")
    job = _service().job(sub["job_id"])
    t_end = time.time() + 60 * a.wait_min
    while True:
        st = str(job.status())
        print(f"{stamp()} job {sub['job_id']} status {st}", flush=True)
        if any(x in st.upper() for x in ("DONE", "ERROR", "CANCEL")):
            break
        if time.time() > t_end:
            raise SystemExit("not finished within the wait limit; run result again later")
        time.sleep(30)
    if "DONE" not in st.upper():
        raise SystemExit(f"job ended with status {st}")
    res = job.result()
    rows = [dict(pub=i, counts=dict(r.join_data().get_counts())) for i, r in enumerate(res)]
    try:
        metrics = job.metrics()
    except Exception as exc:  # noqa: BLE001
        metrics = dict(error=type(exc).__name__)
    try:
        cal_run = calibration_time(_service().backend(_load_json(os.path.join(a.job, "manifest.json"))["fetch"]["backend"]))
    except Exception:  # noqa: BLE001
        cal_run = None
    _dump_json(raw_file, dict(fetched=stamp(), job_id=sub["job_id"], status=st, metrics=metrics,
                              calibration_at_fetch=cal_run, rows=rows))
    print(f"{stamp()} saved raw_counts.json ({len(rows)} results); usage {metrics.get('usage')}")


# ------------------------------------------------------------------------------------------------ score

def cmd_score(a):
    from scipy.stats import binomtest, ttest_rel, wilcoxon
    man = _read_job(a.job)
    raw = _load_json(os.path.join(a.job, "raw_counts.json"))
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    if len(rows) != len(man["pubs"]):
        raise SystemExit("STOP: the results do not cover every circuit")
    N = man["shots"]
    p_hat = {}
    for i, pub in enumerate(man["pubs"]):
        p_hat.setdefault(pub["cell"], {})[pub["point"]] = p1_of_counts(rows[i])
    out = dict(scored=stamp(), job_id=raw["job_id"], status=raw.get("status"), metrics=raw.get("metrics"),
               backend=man["fetch"]["backend"], calibration_fetched=man["fetch"]["calibration_time"],
               calibration_at_result=raw.get("calibration_at_fetch"), shots=N, alpha=ALPHA, cells=[], h2=[])
    for c in man["cells"]:
        P = c["points"]
        ph = np.array([p_hat[c["cell"]][i] for i in range(P)])
        y = np.array(c["labels"])
        p1 = np.array(c["twin_p1"])
        z = 1 - 2 * ph
        n_correct = int(np.sum(np.sign(z) == y))
        cv, av = ce(z, y), acc_half(z, y)
        pr, so = c["prediction"], c["prediction_shots_only"]
        e = np.abs(ph - p1)
        out["cells"].append(dict(
            cell=c["cell"], name=c["name"], arm=c["arm"], layers=c["layers"], seed=c["seed"], points=P,
            h1_correct_strict=n_correct, h1_p=float(binomtest(n_correct, P, 0.5, alternative="greater").pvalue),
            ce=cv, acc=av, ce_pred=pr["ce_mean"], acc_pred=pr["acc_mean"],
            r1_ce_inside=pr["ce_interval"][0] <= cv <= pr["ce_interval"][1],
            r1_acc_inside=pr["acc_interval"][0] <= av <= pr["acc_interval"][1],
            r1_ce_inside_shots_only=so["ce_interval"][0] <= cv <= so["ce_interval"][1],
            r1_acc_inside_shots_only=so["acc_interval"][0] <= av <= so["acc_interval"][1],
            r2_ce_gap=cv - pr["ce_mean"], r2_acc_gap=av - pr["acc_mean"],
            dev_mean=float(e.mean()), dev_rms=float(np.sqrt(np.mean((ph - p1) ** 2))),
            shot_floor_mean=float(np.mean(np.sqrt(2 / math.pi * p1 * (1 - p1) / N)))))
    adj = holm([c["h1_p"] for c in out["cells"]])
    for c, q in zip(out["cells"], adj):
        c["h1_p_holm"] = q
        c["h1_confirmed"] = q < ALPHA
    # H2, per depth: d_i = mean over seeds of (|p_hat - p1|_Qiskit - |p_hat - p1|_PSF) at the same point
    by = {}
    for c in man["cells"]:
        kind = "psf" if c["arm"].startswith("psf") else "qiskit" if c["arm"].startswith("qiskit") else None
        by.setdefault(c["layers"], {}).setdefault(kind, {})[c["seed"]] = c
    pv = []
    for L in sorted(by):
        g = by[L]
        seeds = sorted(set(g.get("psf", {})) & set(g.get("qiskit", {})))
        if not seeds:
            continue
        P = g["psf"][seeds[0]]["points"]
        d = np.zeros(P)
        for s in seeds:
            cp, cq = g["psf"][s], g["qiskit"][s]
            if cp["points"] != cq["points"] or cp["labels"] != cq["labels"]:
                raise SystemExit(f"STOP: L {L} seed {s}: the two compilers' test points differ")
            eP = np.abs(np.array([p_hat[cp["cell"]][i] for i in range(P)]) - np.array(cp["twin_p1"]))
            eQ = np.abs(np.array([p_hat[cq["cell"]][i] for i in range(P)]) - np.array(cq["twin_p1"]))
            d += (eQ - eP) / len(seeds)
        w = wilcoxon(d, alternative="greater")
        t = ttest_rel(d, np.zeros(P), alternative="greater")
        out["h2"].append(dict(layers=L, seeds=seeds, points=P, mean_d=float(d.mean()), wilcoxon_p=float(w.pvalue),
                              paired_t_p=float(t.pvalue)))
        pv.append(float(w.pvalue))
    for h, q in zip(out["h2"], holm(pv)):
        h["wilcoxon_p_holm"] = q
        h["h2_confirmed"] = q < ALPHA
    _dump_json(os.path.join(a.job, "score.json"), out)
    lines = [f"# Design C device job: score ({out['scored']})", "",
             f"Job {out['job_id']} on {out['backend']} ({out['status']}); calibration fetched "
             f"{out['calibration_fetched']}, at result {out['calibration_at_result']}; usage "
             f"{(out['metrics'] or {}).get('usage')}; {N} shots per point.", "",
             "| cell | P | correct (strict) | H1 p (Holm) | H1 | CE (pred) | in 99 % (twin+shots / shots) | acc (pred) "
             "| mean dev (shot floor) |", "|---|---|---|---|---|---|---|---|---|"]
    for c in out["cells"]:
        lines.append(f"| {c['name']} | {c['points']} | {c['h1_correct_strict']} | {c['h1_p_holm']:.2e} | "
                     f"{'confirmed' if c['h1_confirmed'] else 'not confirmed'} | {c['ce']:.4f} ({c['ce_pred']:.4f}) | "
                     f"{'yes' if c['r1_ce_inside'] else 'no'} / {'yes' if c['r1_ce_inside_shots_only'] else 'no'} | "
                     f"{c['acc']:.3f} ({c['acc_pred']:.3f}) | {c['dev_mean']:.4f} ({c['shot_floor_mean']:.4f}) |")
    lines += ["", "| depth | seeds | mean d (Qiskit dev - PSF dev) | Wilcoxon p (Holm) | paired t p | H2 |",
              "|---|---|---|---|---|---|"]
    for h in out["h2"]:
        lines.append(f"| L {h['layers']} | {h['seeds']} | {h['mean_d']:+.4f} | {h['wilcoxon_p_holm']:.2e} | "
                     f"{h['paired_t_p']:.2e} | {'confirmed' if h['h2_confirmed'] else 'not confirmed'} |")
    with open(os.path.join(a.job, "score.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m toqb.s2rc_device", description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    f = sp.add_parser("fetch")
    f.add_argument("--out", required=True)
    f.add_argument("--backend")
    f.add_argument("--fake")
    p = sp.add_parser("plans")
    p.add_argument("--target", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--seeds", type=int, nargs="+", required=True)
    p.add_argument("--p8", type=int, required=True)
    p.add_argument("--p16", type=int, required=True)
    p.add_argument("--shots", type=int, required=True)
    p.add_argument("--lr", type=float, required=True)
    p.add_argument("--loops", type=int, required=True)
    p.add_argument("--traj", type=int, default=1024)
    p.add_argument("--reps", type=int, default=20000)
    s = sp.add_parser("assemble")
    s.add_argument("--fetch", required=True)
    s.add_argument("--runs", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--max-seconds", type=float, required=True)
    u = sp.add_parser("submit")
    u.add_argument("--job", required=True)
    u.add_argument("--local", action="store_true")
    u.add_argument("--noiseless", action="store_true")
    u.add_argument("--seed", type=int, default=20261019)
    r = sp.add_parser("result")
    r.add_argument("--job", required=True)
    r.add_argument("--wait-min", type=float, default=60)
    c = sp.add_parser("score")
    c.add_argument("--job", required=True)
    a = ap.parse_args(argv)
    dict(fetch=cmd_fetch, plans=cmd_plans, assemble=cmd_assemble, submit=cmd_submit, result=cmd_result,
         score=cmd_score)[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
