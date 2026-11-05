"""Checks before the pool goes home (task T, section 6), on the CPU, no device:

  agree    the circuits against the sealed answers by an independent method at shallow t (as gpu/practice_circuits.py
           --check): P32/B42/B72 problems with t <= 4 from the ball of radius t - 1 around each qubit (psf_os.ising2d.ball,
           the circuit rebuilt on the ball by daily/pool.py, Aer statevector); C33 at t 8 (D01) by Aer's
           matrix-product-state method on the whole chain (no truncation set).
  run2d    every circuit (D01-D32, FX-A, FX-B, S01-S06) through `psf-os run2d`, one job each, on fake devices (FakeFez,
           FakeMarrakesh, FakeKingston; their graphs and failed marks only) and on the device records of the 11-04 practice runs (marrakesh, fez); the CZ
           count, the copy placed, the time model, or the refusal as given. Also how many copies of each patch the
           lattice has and how many qualify.
  noiseless  the compiled user circuit (of the first device above that accepted it) against the sealed answers, without noise: P32 and C33
           at shallow t on the whole circuit (Aer matrix-product state), B42/B72 from the light cone of each qubit
           in the compiled circuit (Aer statevector), as home's end-to-end check.

usage: python daily/handoff_check.py ANSWERS.json OUT_DIR SCRATCH_DIR
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gpu"))
sys.path.insert(0, os.path.join(HERE, ".."))
import daily_answers as A  # noqa: E402

from daily import pool as P  # noqa: E402

IDS = [e[0] for e in P.POOL] + ["FX-A", "FX-B"] + [e[0] for e in P.SCALE]
DEVICES = {"fake_FakeFez": None, "fake_FakeMarrakesh": None, "fake_FakeKingston": None, "marrakesh_11-04": "results/practice-2026-11-04/dev",
           "fez_11-04": "results/practice-fez-2026-11-04/dev"}
SHOTS = 4000


def _z_sv(qc, q):
    from qiskit.quantum_info import Pauli, Statevector
    n = qc.num_qubits
    return float(Statevector(qc).expectation_value(Pauli("I" * (n - 1 - q) + "Z" + "I" * q)).real)


def _z_mps(qc, qubits):
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    c = qc.copy()
    for q in qubits:
        c.save_expectation_value(Pauli("Z"), [q], label=f"z{q}")
    r = AerSimulator(method="matrix_product_state").run(c).result().data()
    return {q: float(r[f"z{q}"]) for q in qubits}


def agree(ans):
    from psf_os import ising2d as I
    out = {}
    for pid in IDS:
        if pid not in ans:
            continue
        _, fam, pa, par, t, _, _ = P.entry(pid)
        sealed = {int(k): v for k, v in ans[pid]["values"].items()}
        if pa != "C33" and t <= 4:
            qs, es = P.patch(pa)
            dev = 0.0
            for q in qs:
                ball = I.ball(q, t - 1, es)
                idx = {x: k for k, x in enumerate(ball)}
                be = [(idx[a], idx[b]) for a, b in es if a in idx and b in idx]
                small = P.f1(t, par["theta_x"], par["theta_zz"], list(idx.values()), be) if fam == "F1" else \
                    P.f2(t, par["theta"], list(idx.values()), be)
                dev = max(dev, abs(_z_sv(small.remove_final_measurements(inplace=False), idx[q]) - sealed[q]))
            out[pid] = dict(method="ball statevector", max_diff=dev)
        elif pa == "C33" and t <= 8:  # t 10 (D05) took over an hour on the laptop
            chain = list(range(33))
            qc = P.circuit(fam, pa, par, t, chain=chain).remove_final_measurements(inplace=False)
            z = _z_mps(qc, chain)
            out[pid] = dict(method="chain MPS", max_diff=max(abs(z[k] - sealed[P.PC.CHAIN[k]]) for k in chain))
        if pid in out:
            print(f"agree {pid}: {out[pid]['method']} max |. - sealed| {out[pid]['max_diff']:.2e}", flush=True)
    return out


def copies(dev):
    from psf_os import lattice2d as L
    out = {}
    for pa in ("P32", "B42", "B72", "B102", "C33"):
        qs, es = P.patch(pa)
        cs = L.copies(dev, es, qs)
        out[pa] = dict(copies=len(cs), qualify=sum(not L.check(dev, es, m) for _, _, m in cs))
    return out


def run2d(scratch, devdirs, ids=IDS, done=None):
    from qiskit import qpy
    from psf_os import device as Dv
    from psf_os import job as J
    cdir = os.path.join(scratch, "circuits")
    os.makedirs(cdir, exist_ok=True)
    for pid in ids:
        with open(os.path.join(cdir, pid + ".qpy"), "wb") as f:
            qpy.dump(P.problem_circuit(pid), f)
    out = done or {}
    for dname, ddir in devdirs.items():
        dev = Dv.Device.load(ddir)
        res = out.get(dname) or dict(device=dev.name, problems={})
        res["copies"] = copies(dev)
        for pid in ids:
            if pid in res["problems"]:
                continue
            o = os.path.join(scratch, "run2d", dname, pid)
            t0 = time.time()
            p = subprocess.run([sys.executable, "-m", "psf_os", "run2d", "--device", ddir, "--circuit",
                                os.path.join(cdir, pid + ".qpy"), "--out", o, "--shots", str(SHOTS)],
                               capture_output=True, text=True)
            r = dict(returncode=p.returncode, seconds_wall=round(time.time() - t0, 1))
            if p.returncode == 0:
                rep = json.load(open(os.path.join(o, "report.json")))
                r.update(cz=rep["cz"], copy=rep["copy"], passed_over=len(rep["passed_over"]),
                         circuits=rep["circuits"], qpu_seconds_model_job=rep["qpu_seconds_model"],
                         qpu_seconds_model_three=round(J.qpu_seconds(3, SHOTS), 2), checks=rep["checks"])
            else:
                r.update(refused=(p.stderr.strip().splitlines() or [""])[-1])
            res["problems"][pid] = r
            print(f"run2d {dname} {pid}: " + (f"cz {r['cz']} copy {r['copy']} job {r['qpu_seconds_model_job']} s"
                                              if p.returncode == 0 else f"REFUSED {r['refused']}"), flush=True)
        out[dname] = res
    return out


def _compiled(scratch, dname, pid):
    from qiskit import qpy
    o = os.path.join(scratch, "run2d", dname, pid)
    rep = json.load(open(os.path.join(o, "report.json")))
    with open(os.path.join(o, "runs", "p2d_user.qpy"), "rb") as f:
        return qpy.load(f)[0], {int(k): v for k, v in rep["mapping"].items()}


def _compact(qc):
    """The compiled circuit on its active qubits only, without measurements: (circuit, physical -> index)."""
    from qiskit import QuantumCircuit
    used = sorted({qc.find_bit(q).index for ins in qc.data for q in ins.qubits})
    idx = {p: k for k, p in enumerate(used)}
    out = QuantumCircuit(len(used))
    for ins in qc.data:
        if ins.operation.name in ("measure", "barrier", "delay"):
            continue
        out.append(ins.operation, [out.qubits[idx[qc.find_bit(q).index]] for q in ins.qubits])
    return out, idx


def noiseless(ans, scratch, whole=("D13", "D21", "D01"), by_cone=("D17", "D03", "D07", "FX-B")):
    from qiskit import QuantumCircuit
    out = {}
    for pid in whole + by_cone:
        ok = [d for d in DEVICES if os.path.exists(os.path.join(scratch, "run2d", d, pid, "report.json"))]
        if not ok:
            out[pid] = dict(skipped="refused on every device")
            continue
        dname = ok[0]
        qc, m = _compiled(scratch, dname, pid)
        sealed = {int(k): v for k, v in ans[pid]["values"].items()}
        if pid in whole:
            c, idx = _compact(qc)
            z = _z_mps(c, [idx[m[q]] for q in sealed])
            got = {q: z[idx[m[q]]] for q in sealed}
            how = "compiled circuit, whole, MPS"
        else:
            ops, readout, _ = A.program(qc)
            got = {}
            inv = {p: q for q, p in m.items()}
            for p in readout:
                cq, co = A.cone_ops(ops, p)
                idx = {x: k for k, x in enumerate(cq)}
                small = QuantumCircuit(len(cq))
                for name, qs, par in co:
                    if name == "cz":
                        small.cz(idx[qs[0]], idx[qs[1]])
                    elif name == "rzz":
                        small.rzz(par, idx[qs[0]], idx[qs[1]])
                    else:
                        small.unitary(par, [idx[qs[0]]])
                got[inv[p]] = _z_sv(small, idx[p])
            how = "compiled circuit, light cones, statevector"
        out[pid] = dict(method=how, device=dname, max_diff=max(abs(got[q] - sealed[q]) for q in sealed))
        print(f"noiseless {pid}: {how} max |. - sealed| {out[pid]['max_diff']:.2e}", flush=True)
    return out


def devices(scratch):
    from psf_os import device as Dv
    devdirs = {}
    for dname, ddir in DEVICES.items():
        if ddir is None:
            ddir = os.path.join(scratch, "dev_" + dname)
            if not os.path.exists(os.path.join(ddir, "device.json")):
                Dv.fetch_fake(dname.split("_", 1)[1]).save(ddir)
        devdirs[dname] = ddir
    return devdirs


def main(answers, out, scratch):
    """run2d does not need the answers: its result is kept in SCRATCH/run2d.json and reused."""
    ans = json.load(open(answers)) if answers != "-" else None
    os.makedirs(out, exist_ok=True)
    cache = os.path.join(scratch, "run2d.json")
    done = json.load(open(cache)) if os.path.exists(cache) else None
    if done is None or any(p not in r["problems"] for r in done.values() for p in IDS):
        json.dump(run2d(scratch, devices(scratch), done=done), open(cache, "w"), indent=1)
    if ans is None:
        return None
    rep = dict(agree=agree(ans), run2d=json.load(open(cache)), noiseless=noiseless(ans, scratch))
    json.dump(rep, open(os.path.join(out, "handoff_check.json"), "w"), indent=1)
    return rep


if __name__ == "__main__":
    main(*sys.argv[1:4])
