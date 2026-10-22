"""Design C's device step: the day's Target at home, training and prediction on the pod, one job from home, scoring.

The IBM API key stays at home: only `fetch`, `submit` and `result` connect to IBM, and they use the account saved
beforehand in the home terminal with QiskitRuntimeService.save_account(...); this module never reads or writes the
key. The pod gets the Target as a file and returns the compiled circuits as a file. Nothing here runs git or pip.

    [home, VPN OFF]  python -m toqb.s2rc_device fetch    --backend ibm_fez --out DAY/fetch
    [pod]            python -m toqb.s2rc_device precheck --fetch <pod>/fetch            (before training: both compilers'
                         circuits on the fetched Target, ISA and failed elements; minutes instead of hours to a STOP)
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
whose files differ from it, a job already submitted, and, on IBM, a job that uses an element failed in the calibration
in effect at submission (owner decision of 2026-10-20: a new calibration timestamp alone no longer stops it; P1
showed one about every 2 h).

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
    try:
        operational = bool(backend.status().operational)  # device rule E3 (C section 5), read with the Target
    except Exception:  # noqa: BLE001
        operational = None
    info = dict(written=stamp(), backend=backend.name, fake=bool(a.fake), calibration_time=calibration_time(backend),
                operational=operational, two_qubit_gate=("cz" if "cz" in target.operation_names else
                                                         "ecr" if "ecr" in target.operation_names else None),
                num_qubits=target.num_qubits, target_sha256=sha256_file(os.path.join(out, "target.pkl")),
                script_sha256=sha256_file(os.path.abspath(__file__)))
    _dump_json(os.path.join(out, "fetch.json"), info)
    print(f"{info['written']} saved the Target of {info['backend']} (calibration {info['calibration_time']}; "
          f"{info['num_qubits']} qubits; two-qubit gate {info['two_qubit_gate']}; operational {operational}) to "
          f"{out}/target.pkl, sha256 {info['target_sha256'][:16]}...")


def cmd_snapshot(a):
    """Owner, 2026-10-22 (C r9 item 7): the day trains on ibm_marrakesh's published calibration of 2026-10-13 (the
    stand-in's snapshot, `snapshot:marrakesh`), not on a Target fetched that day. Writes a fetch folder (target.pkl,
    fetch.json) from the snapshot so that plans, precheck, assemble and submit run unchanged; no IBM connection. The
    calibration in effect at submission is still read, and a failed element still stops the submission (r8)."""
    from toqb.devices import get_device
    from toqb.s2r import SNAPSHOT
    out = a.out
    if os.path.exists(os.path.join(out, "fetch.json")):
        raise SystemExit(f"{out}/fetch.json exists: a fetch is never overwritten (use a new folder)")
    target = get_device("snapshot:marrakesh").target
    snap = _load_json(SNAPSHOT)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "target.pkl"), "wb") as f:
        pickle.dump(target, f)
    info = dict(written=stamp(), backend=snap["device"], fake=False,
                source="snapshot: the published calibration (toqb/data), not fetched on the day (owner, 2026-10-22)",
                snapshot_sha256=sha256_file(SNAPSHOT), calibration_time=snap["calibration_time"], operational=None,
                two_qubit_gate=("cz" if "cz" in target.operation_names else None), num_qubits=target.num_qubits,
                target_sha256=sha256_file(os.path.join(out, "target.pkl")),
                script_sha256=sha256_file(os.path.abspath(__file__)))
    _dump_json(os.path.join(out, "fetch.json"), info)
    print(f"{info['written']} wrote the snapshot Target of {info['backend']} (calibration {info['calibration_time']}; "
          f"not fetched) to {out}/target.pkl, sha256 {info['target_sha256'][:16]}...")


# ------------------------------------------------------------------------------------------------ history (home)

def update_summary(stamps):
    """Distinct calibration timestamps (ISO strings, any order, duplicates allowed) -> sorted list, gaps in hours,
    and each update's time of day in UTC (hours). Pure; used by `history` (C r6, P1)."""
    from datetime import datetime, timezone
    ts = sorted({datetime.fromisoformat(str(x)).astimezone(timezone.utc) for x in stamps if x})
    gaps = [(b - a).total_seconds() / 3600 for a, b in zip(ts, ts[1:])]
    return dict(updates=[t.isoformat() for t in ts], gaps_h=[round(g, 2) for g in gaps],
                utc_hour=[round(t.hour + t.minute / 60, 2) for t in ts],
                min_gap_h=round(min(gaps), 2) if gaps else None, median_gap_h=round(float(np.median(gaps)), 2) if gaps else None)


def cmd_history(a):
    """Read-only (no job, no QPU time): when did each backend's calibration timestamp change over the past days?
    Samples backend.properties(datetime=t) every STEP hours; each sample returns the calibration in effect at t, whose
    last_update_date is the update's own time, so updates are found exactly unless two fall within one step."""
    from datetime import datetime, timedelta, timezone
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "history.json")
    if os.path.exists(path):
        raise SystemExit(f"{path} exists: a reading is never overwritten (use a new folder)")
    svc = _service()
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    rec = dict(written=stamp(), days=a.days, step_h=a.step, backends={})
    for name in a.backends:
        b = svc.backend(name)
        stamps, errors = [calibration_time(b)], 0
        for k in range(int(a.days * 24 / a.step) + 1):
            t = now - timedelta(hours=k * a.step)
            try:
                stamps.append(str(b.properties(datetime=t).last_update_date))
            except Exception:  # noqa: BLE001
                errors += 1
        summ = update_summary(stamps)
        summ.update(current=stamps[0], samples=len(stamps) - 1, errors=errors)
        # if every sample equals the current stamp, the server may not serve history at all: say so, do not guess
        summ["history_served"] = any(x != stamps[0] for x in stamps[1:])
        rec["backends"][name] = summ
        print(f"{name}: {len(summ['updates'])} updates, min gap {summ['min_gap_h']} h, median {summ['median_gap_h']} h, "
              f"UTC hours {summ['utc_hour']} ({errors} failed samples; history served: {summ['history_served']})", flush=True)
    _dump_json(path, rec)


def props_values(props):
    """{(kind, element): value} from BackendProperties: cz / sx gate error per element, readout error, T1, T2."""
    out = {}
    for g in props.gates:
        if g.gate in ("cz", "sx"):
            for prm in g.parameters:
                if prm.name == "gate_error":
                    out[(g.gate, tuple(g.qubits))] = prm.value
    for q, plist in enumerate(props.qubits):
        for prm in plist:
            if prm.name in ("readout_error", "T1", "T2"):
                out[(prm.name, (q,))] = prm.value
    return out


def drift_summary(a_vals, b_vals):
    """Per kind: how many elements changed, the median and largest |relative change|, and how many crossed the
    failed-element rule (error >= 0.5) in either direction. Pure; used by `drift`."""
    kinds = sorted({k for k, _ in a_vals})
    res = {}
    for kind in kinds:
        keys = [k for k in a_vals if k[0] == kind and k in b_vals and a_vals[k] is not None and b_vals[k] is not None]
        rel = np.array([abs(b_vals[k] - a_vals[k]) / abs(a_vals[k]) for k in keys if a_vals[k]] or [0.0])
        failed_flip = sum(1 for k in keys if kind not in ("T1", "T2") and (a_vals[k] >= 0.5) != (b_vals[k] >= 0.5))
        res[kind] = dict(elements=len(keys), changed=int(sum(1 for k in keys if a_vals[k] != b_vals[k])),
                         median_rel=round(float(np.median(rel)), 4), max_rel=round(float(np.max(rel)), 4),
                         failed_flips=failed_flip)
    return res


def cmd_drift(a):
    """Read-only (no job, no QPU time): how much do the calibration values change between consecutive updates?
    For each backend, the calibration in effect now and those in effect `--back` hours earlier, compared pairwise."""
    from datetime import datetime, timedelta, timezone
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "drift.json")
    if os.path.exists(path):
        raise SystemExit(f"{path} exists: a reading is never overwritten (use a new folder)")
    svc = _service()
    now = datetime.now(timezone.utc)
    rec = dict(written=stamp(), back_h=a.back, backends={})
    for name in a.backends:
        b = svc.backend(name)
        snaps = []
        for h in [0] + list(a.back):
            pr = b.properties(datetime=now - timedelta(hours=h)) if h else b.properties(refresh=True)
            snaps.append((h, str(pr.last_update_date), props_values(pr)))
        pairs = {}
        for (h0, t0, v0), (h1, t1, v1) in zip(snaps[1:], snaps[:-1]):
            pairs[f"{t0} -> {t1}"] = drift_summary(v0, v1)
        rec["backends"][name] = pairs
        for k, v in pairs.items():
            print(f"{name} {k}: " + "; ".join(f"{kind} {d['changed']}/{d['elements']} changed, median {d['median_rel']:.1%}, "
                                             f"max {d['max_rel']:.0%}, failed flips {d['failed_flips']}" for kind, d in v.items()), flush=True)
    _dump_json(path, rec)


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


# ------------------------------------------------------------------------------------------------ precheck (pod)

def _precheck(fetch_dir, arms, layers, n, enc, seed):
    """Compile the model circuit once per compiler and depth on the fetched Target (random angles; the structure does
    not depend on them) and apply assemble's checks; also r9's E5 (PSF's placement by the formula, never by VF2's
    search). Returns (fetch.json, number of cases with problems)."""
    from toqb import s2r as S
    from toqb import task_loop as TL
    from toqb.devices import _failed, from_target
    fetch = _load_json(os.path.join(fetch_dir, "fetch.json"))
    tfile = os.path.join(fetch_dir, "target.pkl")
    if sha256_file(tfile) != fetch["target_sha256"]:
        raise SystemExit("STOP: target.pkl differs from fetch.json's hash")
    with open(tfile, "rb") as f:
        target = pickle.load(f)
    device = from_target("file:" + os.path.abspath(tfile), target, True)
    fe, fq = _failed(target)
    rng = np.random.default_rng(seed)
    bad = 0
    for spec in arms:
        arm = S.Arm(spec, device)
        for L in layers:
            th = rng.uniform(-1, 1, TL.n_params(n, L))
            x = rng.uniform(-1, 1, n)
            try:
                c = arm.compile(TL.model_circuit(TL.angle_list(th, x, n, L, enc), n, L))
            except Exception as exc:  # noqa: BLE001 - r9 E5: PSF's placement would need a search (ringport.OutOfScope)
                if type(exc).__name__ != "OutOfScope":
                    raise
                print(f"{spec:28s} L {L:2d}: OUT OF SCOPE (E5): {exc}", flush=True)
                bad += 1
                continue
            pr = _isa_problems(c, target, fe, fq)
            q2 = sum(1 for i in c.data if i.operation.num_qubits == 2)
            act = len({c.find_bit(q).index for i in c.data for q in i.qubits})
            print(f"{spec:28s} L {L:2d}: {act} active qubits, {q2} two-qubit gates: "
                  + ("OK" if not pr else "PROBLEM " + "; ".join(pr[:3])), flush=True)
            bad += bool(pr)
    return fetch, bad


def cmd_precheck(a):
    """The checks of `_precheck` on one fetched Target, so a failed element, a non-native gate or a placement outside
    the scope stops the day before training starts rather than after it."""
    fetch, bad = _precheck(a.fetch, a.arms, a.layers, a.n, a.enc, a.seed)
    print(f"{stamp()} precheck on {fetch['backend']} (calibration {fetch['calibration_time']}): "
          + ("all OK" if not bad else f"STOP: {bad} case(s) with problems"))
    if bad:
        raise SystemExit(1)


def cmd_choose(a):
    """C r9's device rule on the pod: the fetched Targets in the fixed order (marrakesh, fez, kingston as given),
    each read for E2 (cz), E3 (operational, as fetched; unknown is recorded, not excluded) and E4 + E5 (`_precheck`:
    no failed element, PSF placed by the formula); the first eligible is used. No error rate is read. Writes
    choice.json (never overwritten) and prints `CHOSEN <folder>` last."""
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists; a choice is never overwritten")
    rows, chosen = [], None
    for fd in a.fetches:
        fj = _load_json(os.path.join(fd, "fetch.json"))
        why = []
        if fj.get("two_qubit_gate") != "cz":
            why.append(f"E2: two-qubit gate {fj.get('two_qubit_gate')}")
        if fj.get("operational") is False:
            why.append("E3: not operational at fetch")
        if not why:
            print(f"== {fj['backend']} (calibration {fj['calibration_time']})", flush=True)
            _, bad = _precheck(fd, a.arms, a.layers, a.n, a.enc, a.seed)
            if bad:
                why.append(f"E4/E5: {bad} case(s) with problems")
        rows.append(dict(folder=os.path.abspath(fd), backend=fj["backend"], calibration_time=fj["calibration_time"],
                         operational=fj.get("operational"), target_sha256=fj["target_sha256"], eligible=not why,
                         reasons=why))
        print(f"{fj['backend']}: " + ("eligible" if not why else "not eligible: " + "; ".join(why)), flush=True)
        if not why:
            chosen = rows[-1]
            break
    _dump_json(a.out, dict(written=stamp(), rule="C r9: E1-E5, then the fixed order as given", devices=rows,
                           chosen=chosen))
    if chosen is None:
        raise SystemExit("STOP: no device is eligible")
    print(f"CHOSEN {chosen['folder']}")


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


def submit_problems(circs, target):
    """Problems of the job against the calibration in effect at submission: any circuit on an unsupported or failed
    element (`_isa_problems` with `devices._failed`, as assemble). Each problem is prefixed with its circuit index."""
    from toqb.devices import _failed
    fe, fq = _failed(target)
    out = []
    for i, c in enumerate(circs):
        out += [f"circuit {i}: {p}" for p in _isa_problems(c, target, fe, fq)]
    return out


ORDER = ("ibm_marrakesh", "ibm_fez", "ibm_kingston")  # r8's fixed order


def pick_backend(circs, get_backend, first):
    """C r9 item 8 (owner, 2026-10-22): at submission, the job's own circuits go to the first device, in the fixed
    order starting at the job's (`first`), whose calibration in effect now has the same number of qubits, reports it
    operational (unknown is not excluded) and has no failed or unsupported element under the job (r8's rule); no
    retraining. Returns (backend, calibration time, tried) with tried = [{backend, calibration, reasons}], or
    (None, None, tried) when no device takes the job."""
    names = [first] + [b for b in ORDER if b != first]
    tried = []
    for name in names:
        try:
            backend = get_backend(name)
        except Exception as exc:  # noqa: BLE001 - recorded; the next device in the order is tried
            tried.append(dict(backend=name, calibration=None, reasons=[f"not reachable: {type(exc).__name__}"]))
            continue
        cal = calibration_time(backend)
        why = []
        if backend.target.num_qubits != circs[0].num_qubits:
            why.append(f"{backend.target.num_qubits} qubits, the job {circs[0].num_qubits}")
        else:
            try:
                if backend.status().operational is False:
                    why.append("not operational")
            except Exception:  # noqa: BLE001
                pass
            probs = submit_problems(circs, backend.target)
            if probs:
                why.append("failed or unsupported elements: " + "; ".join(probs[:5]))
        tried.append(dict(backend=backend.name, calibration=cal, reasons=why))
        if not why:
            return backend, cal, tried
    return None, None, tried


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
    # owner decision of 2026-10-20: a new calibration timestamp does not stop the submission; a failed element under
    # the job does. Owner decision of 2026-10-22 (C r9 item 8): then the same circuits go to the next device in the
    # fixed order (pick_backend), no retraining; every device tried and why is recorded.
    service = _service()
    backend, cal, tried = pick_backend(circs, service.backend, man["fetch"]["backend"])
    for t in tried:
        print(f"{t['backend']} (calibration {t['calibration']}): "
              + ("takes the job" if not t["reasons"] else "passed over: " + "; ".join(t["reasons"])), flush=True)
    if backend is None:
        _dump_json(os.path.join(a.job, "submission_refused.json"), dict(written=stamp(), tried=tried))
        raise SystemExit("STOP: no device in the fixed order takes the job; not submitted (submission_refused.json)")
    sampler = SamplerV2(mode=backend)
    sampler.options.dynamical_decoupling.enable = False
    sampler.options.twirling.enable_gates = False
    sampler.options.twirling.enable_measure = False
    t_sub = stamp()
    job = sampler.run([(c, None, N) for c in circs])
    _dump_json(sub_file, dict(job_id=job.job_id(), submitted=t_sub, local=False, backend=backend.name,
                              trained_for=man["fetch"]["backend"], tried=tried, calibration_at_submit=cal, options="dynamical decoupling off, twirling off (gates and "
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
        cal_run = calibration_time(_service().backend(sub.get("backend")
                                                      or _load_json(os.path.join(a.job, "manifest.json"))["fetch"]["backend"]))
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
    k = sp.add_parser("precheck")
    k.add_argument("--fetch", required=True)
    k.add_argument("--arms", nargs="+", default=["qiskit:2:target:template", "psfai:template"])
    k.add_argument("--layers", type=int, nargs="+", default=[8, 16])
    k.add_argument("--n", type=int, default=10)
    k.add_argument("--enc", type=float, default=1.5707963267948966)
    k.add_argument("--seed", type=int, default=20261020)
    sn = sp.add_parser("snapshot")
    sn.add_argument("--out", required=True)
    ch = sp.add_parser("choose")
    ch.add_argument("--fetches", nargs="+", required=True)
    ch.add_argument("--out", required=True)
    ch.add_argument("--arms", nargs="+", default=["qiskit:2:target:template", "psfai:template"])
    ch.add_argument("--layers", type=int, nargs="+", default=[8, 16])
    ch.add_argument("--n", type=int, default=10)
    ch.add_argument("--enc", type=float, default=1.5707963267948966)
    ch.add_argument("--seed", type=int, default=20261020)
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
    h = sp.add_parser("history")
    h.add_argument("--out", required=True)
    h.add_argument("--backends", nargs="+", default=["ibm_marrakesh", "ibm_fez", "ibm_kingston"])
    h.add_argument("--days", type=float, default=7)
    h.add_argument("--step", type=float, default=2)
    dr = sp.add_parser("drift")
    dr.add_argument("--out", required=True)
    dr.add_argument("--backends", nargs="+", default=["ibm_marrakesh", "ibm_fez", "ibm_kingston"])
    dr.add_argument("--back", type=float, nargs="+", default=[2.5, 5.0])
    c = sp.add_parser("score")
    c.add_argument("--job", required=True)
    a = ap.parse_args(argv)
    dict(fetch=cmd_fetch, snapshot=cmd_snapshot, precheck=cmd_precheck, choose=cmd_choose, plans=cmd_plans, assemble=cmd_assemble, submit=cmd_submit, result=cmd_result,
         score=cmd_score, history=cmd_history, drift=cmd_drift)[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
