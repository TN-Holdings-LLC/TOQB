"""L* measurement job (2026-11-10, for the classifier's depth; not declared): the 10-29 noise-wall probe P1 as built
then (prereg/drafts-2026-10-29/noise_wall_1_note.md, gpu/noise_wall_1.sh, toqb.kising_charge build), narrowed:

  n = 20 only; arms fold:rule and qiskit:2:blind:template; L = 24, 50, 100; per record the 12 circuits (inputs
  |0..0>, |1..1>, Neel, anti-Neel x settings Z, YZ, ZY) and the 4 per-record readout references; 1000 shots; the
  declared charge (b, c) of 10-29; the kicked-Ising ring J = pi/4, h = 0.6. 2 x 3 x 16 = 96 circuits.

The device is read from a psf-os device record (`psfos:FOLDER`, toqb.devices: geometry and failed marks only; no map,
no number). Each record is built exactly as `kising_charge build` builds it (the same circuits, references, record
fields), only with the plan's device "psfos:FOLDER" instead of "file:target.pkl". The job is then assembled by
`toqb.s2rc_device assemble` unchanged, from a fetch folder written here: target.pkl = the failed-mark Target
(toqb.devices.failmark_target, pickled) and fetch.json with its sha256 (the records carry the same sha256).
--spec builds on any toqb.devices spec instead (e.g. fake:FakeKingston, for the noiseless check); the fetch folder
then holds that spec's Target.

QPU time model (toqb.s2rc_device): 0.036 s per circuit + 0.00027 s per shot + 3 s per job.

usage: PYTHONPATH=<TOQB> python gpu/lstar_build.py OUT (--psfos FOLDER | --spec SPEC)
           [--n 20] [--Ls 24,50,100] [--arms fold:rule,qiskit:2:blind:template] [--shots 1000] [--max-seconds 60]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import subprocess
import sys
import time

import numpy as np

COEF = (-1.2860758110631627, -1.2860758110631603)  # the declared charge (b, c) of 10-29 (gpu/noise_wall_1.sh COEF)
H = 0.6
ARMS = ("fold:rule", "qiskit:2:blind:template")
LS = (24, 50, 100)
SHOTS = 1000


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def stamp():
    from toqb import s2r as S
    return S._cest()


def write_fetch(out, spec, dev_json=None):
    """OUT/fetch/target.pkl and fetch.json (the folder toqb.s2rc_device assemble reads)."""
    from toqb.devices import failmark_target, get_device
    d = os.path.join(out, "fetch")
    os.makedirs(d)
    if dev_json is not None:
        target, name, fake = failmark_target(dev_json), dev_json.get("name"), False
    else:
        dev = get_device(spec)
        target, name, fake = dev.target, spec, spec.startswith("fake:")
    if target is None:
        raise SystemExit(f"STOP: {spec} has no Target")
    tf = os.path.join(d, "target.pkl")
    with open(tf, "wb") as f:
        pickle.dump(target, f)
    fj = dict(written=stamp(), backend=name, fake=fake, spec=spec, two_qubit_gate="cz", num_qubits=target.num_qubits,
              target_sha256=sha256_file(tf), source="gpu/lstar_build.py (failed-mark Target from psf-os device.json)"
              if dev_json is not None else f"gpu/lstar_build.py ({spec})")
    if dev_json is not None:
        fj["device_json_failed_couplers"] = dev_json.get("failed_couplers", [])
        fj["device_json_failed_qubits"] = dev_json.get("failed_qubits", [])
    json.dump(fj, open(os.path.join(d, "fetch.json"), "w"), indent=1)
    return d, fj


def build_record(runs, spec, target_sha, arm, n, L, shots, coef=COEF, h=H):
    """One P1 record, as toqb.kising_charge.cmd_build writes it (device spec in place of file:target.pkl)."""
    from qiskit import qpy
    from toqb import kising_charge as KC
    from toqb import s2r2 as S2
    from toqb.fold_lam import active
    from toqb.s2rc import predict_job
    name = f"kcharge_n{n}_L{L}_h{h:g}-{arm.replace(':', '_')}"
    jf, qf = os.path.join(runs, name + ".json"), os.path.join(runs, name + ".qpy")
    for f in (jf, qf):
        if os.path.exists(f):
            raise SystemExit(f"STOP: {f} exists: a run never overwrites another")
    t0 = time.perf_counter()
    task = dict(n=n, layers=L, enc=float(np.pi / 2))
    pr = dict(traj=0, seed=7, shots=shots, reps=200, level=0.99)
    plan = dict(name=f"noise wall P1: {name}", device=spec, verify=False, task=task, predict=pr,
                standin=dict(t12=0.3, over=0.01, zz_hz=1e4, seed=20261017))
    R = S2.Runner(plan, arm)
    points, cs = [], []
    for i in KC.INPUTS:
        for s in KC.SETTINGS:
            bits = KC.input_bits(i, n)
            cs.append(R.arm.compile(KC.circuit(bits, s, n, L, h)))
            points.append(dict(input=i, setting=s, noiseless=None, q_exact_input=KC.q_noiseless(bits, n)))
    meas0 = None
    for i in KC.INPUTS:
        bits = KC.input_bits(i, n)
        rc, meas = KC.reference_circuit(cs[0], bits)
        meas0 = meas
        cs.append(rc)
        points.append(dict(input=i, setting="ref", noiseless=KC.q_noiseless(bits, n), q_exact_input=KC.q_noiseless(bits, n)))
    for c in cs[:len(KC.INPUTS) * len(KC.SETTINGS)]:
        mm = {c.find_bit(x.clbits[0]).index: c.find_bit(x.qubits[0]).index for x in c.data if x.operation.name == "measure"}
        if mm != meas0:
            raise SystemExit("STOP: the compiled circuits of one record measure on different qubits")
    d, q2 = R.arm.duration(cs[0], (n, L))
    labels = np.ones(len(cs), dtype=int)
    p1 = np.full(len(cs), 0.5)
    rec = dict(kind="s2rc", lam_test=True, charge_test=True, arm=arm, seed=0, plan=plan["name"], task=task,
               predict=pr, standin=plan["standin"], verify=False, device=spec, target_sha256=target_sha,
               version=R.arm.version(), final_mean=[], loops=0, started=stamp(),
               charge=dict(h=h, J="pi/4", coef_YZ=coef[0], coef_ZY=coef[1], info=dict(source="declared 2026-10-29"),
                           inputs=list(KC.INPUTS), settings=list(KC.SETTINGS),
                           measured_qubits={str(k): v for k, v in sorted(meas0.items())}),
               points=points, q_exact={i: KC.q_noiseless(KC.input_bits(i, n), n) for i in KC.INPUTS},
               inputs=[KC.input_bits(p_["input"], n) for p_ in points],
               noiseless_z=[float(p_["q_exact_input"]) for p_ in points], twin=None,
               q2=int(q2), us=round(d * 1e6, 3), active=int(active(cs[0])))
    rec["prediction"] = predict_job(p1, labels, shots, pr["reps"], pr["level"], pr["seed"] + 1)
    rec["prediction_shots_only"] = predict_job(p1, labels, shots, pr["reps"], pr["level"], pr["seed"] + 1)
    rec["prediction"]["twin_p1"] = [float(x) for x in p1]
    rec["test_labels"] = [int(v) for v in labels]
    with open(qf, "wb") as f:
        qpy.dump(list(cs), f)
    rec["export"] = dict(qpy=os.path.basename(qf), circuits=len(cs), sha256=sha256_file(qf))
    rec.update(wall_s=time.perf_counter() - t0, structural_fail=R.arm.structural_fail,
               on_failed_ops=R.arm.on_failed_ops, ended=stamp())
    rec["valid"] = not R.arm.structural_fail and not R.arm.on_failed_ops
    json.dump(rec, open(jf, "w", encoding="utf-8"))
    print(f"{name}: {len(cs)} circuits (12 + 4 references), {q2} two-qubit gates, {d * 1e6:.2f} us; measured "
          f"{[meas0[k] for k in sorted(meas0)]}; valid {rec['valid']}", flush=True)
    if not rec["valid"]:
        raise SystemExit(f"STOP: {name} is not valid")
    return rec


def qpu_seconds(circuits, shots):
    from toqb.s2rc_device import PER_CIRCUIT_S, PER_JOB_S, PER_SHOT_S
    return circuits * (PER_CIRCUIT_S + shots * PER_SHOT_S) + PER_JOB_S


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--psfos", help="a psf-os device record folder (device.json)")
    g.add_argument("--spec", help="any toqb.devices spec (e.g. fake:FakeKingston)")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--Ls", default=",".join(map(str, LS)))
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--shots", type=int, default=SHOTS)
    ap.add_argument("--max-seconds", type=float, default=60.0)
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    from toqb import kising_charge as KC
    ch = KC.charges(a.n, H)  # the declared charge must be the one computed at this n (as the 10-29 script checks)
    dmax = max(abs(ch["coef"][0] - COEF[0]), abs(ch["coef"][1] - COEF[1]))
    print(f"charge check n {a.n}: {'PASS' if dmax < 1e-9 and ch['dim'] == 2 else 'FAIL'} (max diff {dmax:.1e}, dim "
          f"{ch['dim']})")
    if dmax >= 1e-9 or ch["dim"] != 2:
        raise SystemExit("STOP: charge check failed")
    os.makedirs(a.out)
    if a.psfos:
        dj = json.load(open(os.path.join(a.psfos, "device.json")))
        spec = "psfos:" + a.psfos  # as given (pass a path relative to the working folder: no local path in the records)
        fdir, fj = write_fetch(a.out, spec, dj)
    else:
        spec = a.spec
        fdir, fj = write_fetch(a.out, spec)
    print(f"device {fj['backend']} ({'psfos' if a.psfos else spec}); target sha256 {fj['target_sha256']}")
    runs = os.path.join(a.out, "runs1")
    os.makedirs(runs)
    Ls = [int(x) for x in a.Ls.split(",")]
    for arm in a.arms.split(","):
        for L in Ls:
            build_record(runs, spec, fj["target_sha256"], arm, a.n, L, a.shots)
    ncirc = 16 * len(Ls) * len(a.arms.split(","))
    print(f"time model: {ncirc} circuits x {a.shots} shots -> {qpu_seconds(ncirc, a.shots):.1f} s "
          f"(0.036 s/circuit + 0.00027 s/shot + 3 s)")
    p = subprocess.run([sys.executable, "-m", "toqb.s2rc_device", "assemble", "--fetch", fdir, "--runs", runs,
                        "--out", os.path.join(a.out, "job1"), "--max-seconds", str(a.max_seconds)],
                       capture_output=True, text=True)
    print((p.stdout + p.stderr).strip())
    if p.returncode:
        raise SystemExit("STOP: assemble failed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
