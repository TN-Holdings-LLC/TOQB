"""Noiseless check of an L* job (gpu/lstar_build.py). P1 measures a conserved charge, so every four-input ratio rho
should be 1.

  sample   every circuit of JOB/circuits.qpy on the qubits it touches, Aer statevector without noise, at the job's
           shots (seed 11 + circuit index); writes OUT/raw_counts.json and the manifest, so gpu/lstar_score.py reads it
           like a device run (rho = 1 within the shot noise).
  exact    no sampling: per record, each setting's part of Q as an exact expectation value (Aer save_expectation_value
           of the setting's weighted Z Z sum on the measured qubits, the weights of toqb.kising_charge.setting_value);
           Q per input = the sum over the three settings; rho = [sum_inputs sign Q] / [sum_inputs sign Q_reference],
           the reference being the exact Q of the input product state (toqb.kising_charge.q_noiseless). rho = 1 to
           rounding if the circuits keep the charge.

usage: PYTHONPATH=<TOQB> python gpu/lstar_noiseless.py sample JOB OUT
       PYTHONPATH=<TOQB> python gpu/lstar_noiseless.py exact JOB RUNS
"""
from __future__ import annotations

import json
import os
import shutil
import sys

import numpy as np


def compact(c, keep_measure=True):
    """The circuit on its touched qubits; returns (circuit, {clbit: compact qubit})."""
    from qiskit import QuantumCircuit
    used = sorted({c.find_bit(q).index for i in c.data if i.operation.name not in ("barrier", "delay") for q in i.qubits})
    m = {q: i for i, q in enumerate(used)}
    cc = QuantumCircuit(len(used), c.num_clbits)
    meas = {}
    for i in c.data:
        name = i.operation.name
        if name in ("barrier", "delay"):
            continue
        qs = [m[c.find_bit(q).index] for q in i.qubits]
        if name == "measure":
            meas[c.find_bit(i.clbits[0]).index] = qs[0]
            if not keep_measure:
                continue
        cc.append(i.operation, qs, [c.find_bit(x).index for x in i.clbits])
    return cc, meas


def sample(job, out):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    man = json.load(open(os.path.join(job, "manifest.json")))
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    os.makedirs(out)
    shutil.copy(os.path.join(job, "manifest.json"), os.path.join(out, "manifest.json"))
    sim = AerSimulator(method="statevector")
    rows = []
    for k, c in enumerate(circs):
        cc, _ = compact(c)
        rows.append(dict(pub=k, counts=sim.run(cc, shots=man["shots"], seed_simulator=11 + k).result().get_counts()))
    json.dump(dict(fetched="-", job_id="noiseless-sample", status="DONE", rows=rows),
              open(os.path.join(out, "raw_counts.json"), "w"))
    print(f"== NOISELESS SAMPLE FINISHED ({len(circs)} circuits, {man['shots']} shots)")


def exact(job, runs):
    from qiskit import qpy
    from qiskit.quantum_info import SparsePauliOp
    from qiskit_aer import AerSimulator
    from toqb import kising_charge as KC
    man = json.load(open(os.path.join(job, "manifest.json")))
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    sim = AerSimulator(method="statevector")
    worst = 0.0
    for cid, cell in enumerate(man["cells"]):
        rec = json.load(open(os.path.join(runs, cell["name"] + ".json")))
        n = rec["task"]["n"]
        b, cc_ = rec["charge"]["coef_YZ"], rec["charge"]["coef_ZY"]
        Q, ref = {}, {}
        for k, pub in enumerate(man["pubs"]):
            if pub["cell"] != cid:
                continue
            pt = rec["points"][pub["point"]]
            if pt["setting"] == "ref":
                ref[pt["input"]] = KC.q_noiseless(KC.input_bits(pt["input"], n), n)
                continue
            body, meas = compact(circs[k], keep_measure=False)
            terms = []
            for j in range(n):  # the setting's weights, as kising_charge.setting_value
                w = 1.0 if pt["setting"] == "Z" else (b if KC.bases(pt["setting"], n)[j] == "Y" else cc_)
                terms.append(("ZZ", [meas[j], meas[(j + 1) % n]], w))
            op = SparsePauliOp.from_sparse_list(terms, num_qubits=body.num_qubits)
            body.save_expectation_value(op, list(range(body.num_qubits)), label="e")
            Q[pt["input"]] = Q.get(pt["input"], 0.0) + float(np.real(sim.run(body).result().data()["e"]))
        num = sum(KC.SIGN[i] * Q[i] for i in KC.INPUTS)
        den = sum(KC.SIGN[i] * ref[i] for i in KC.INPUTS)
        rho = num / den
        dq = max(abs(Q[i] - KC.q_noiseless(KC.input_bits(i, n), n)) for i in KC.INPUTS)
        worst = max(worst, abs(rho - 1), dq)
        print(f"{cell['name']:46s} exact rho4 {rho:.12f}  |rho - 1| {abs(rho - 1):.1e}  max |Q - Q_exact| over inputs "
              f"{dq:.1e}", flush=True)
    print(f"== NOISELESS EXACT: largest |rho - 1| or |Q - Q_exact| {worst:.1e}")


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("sample", "exact"):
        raise SystemExit(__doc__)
    (sample if sys.argv[1] == "sample" else exact)(sys.argv[2], sys.argv[3])
