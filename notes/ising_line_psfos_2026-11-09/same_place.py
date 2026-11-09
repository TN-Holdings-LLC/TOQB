"""Confirmation without noise (workplace, 2026-11-09; handover 11-08 item 2): the line layout (psf-os grid3d
layout="line") next to the fold v3.1 on the same records, at the fold's place (r0, c0 forced with at=) and at the
line's own first place. Not declared; no device.

usage: PYTHONPATH=<psf-os> python same_place.py [--m3-ts 1,2] RECORD_DIR [RECORD_DIR ...] > same_place.txt
4 x 2 x 2: t 1-4, statevector (18 qubits). 4 x 3 x 2 (28 qubits): t 1 by MPS, later t (--m3-ts) by a single-precision
statevector (the MPS did not finish t 2 in 7 minutes on 2 CPUs).
"""
import sys

import numpy as np


def mps_check(qc, placed, used, L, M, N, t, theta):
    """max |<Z> placed - exact| by Aer MPS on the touched qubits (for 28 qubits, too big for a statevector here)."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    from psf_os import grid3d as G
    m = {u: i for i, u in enumerate(used)}
    small = QuantumCircuit(len(used))
    for ins in qc.data:
        small.append(ins.operation, [m[qc.find_bit(q).index] for q in ins.qubits])
    for s in placed:
        small.save_expectation_value(Pauli("Z"), [m[placed[s]]], label=f"z{s}")
    d = AerSimulator(method="matrix_product_state").run(small, shots=1).result().data()
    ex = G.exact(L, M, N, t, theta)
    return max(abs(float(np.real(d[f"z{s}"])) - ex[str(s)]) for s in placed)


def sv32_check(qc, placed, used, L, M, N, t, theta):
    """max |<Z> placed - exact| by Aer statevector in single precision (28 qubits: 2 GB; precision about 1e-6)."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    from psf_os import grid3d as G
    m = {u: i for i, u in enumerate(used)}
    small = QuantumCircuit(len(used))
    for ins in qc.data:
        small.append(ins.operation, [m[qc.find_bit(q).index] for q in ins.qubits])
    for s in placed:
        small.save_expectation_value(Pauli("Z"), [m[placed[s]]], label=f"z{s}")
    d = AerSimulator(method="statevector", precision="single").run(small, shots=1).result().data()
    ex = G.exact(L, M, N, t, theta)
    return max(abs(float(np.real(d[f"z{s}"])) - ex[str(s)]) for s in placed)


def main(records, m3_ts=(1,)):
    from psf_os import device as Dv
    from psf_os import grid3d as G
    theta = 0.6
    for rec in records:
        dev = Dv.Device.load(rec)
        for (M, ts) in ((2, (1, 2, 3, 4)), (3, m3_ts)):
            for t in ts:
                f = G.prepare(dev, 4, M, 2, t, theta, layout="fold")
                at = [(f["where"]["r0"], f["where"]["c0"])]
                rows = [("fold v3.1", f, dict(layout="fold")), ("line at fold's place", None, dict(layout="line", at=at)),
                        ("line own place", None, dict(layout="line"))]
                for name, p, kw in rows:
                    try:
                        p = p or G.prepare(dev, 4, M, 2, t, theta, **kw)
                    except G.Refused as e:
                        print(f"{dev.name} 4x{M}x2 t{t} {name:21} REFUSED {e}")
                        continue
                    qc, placed, used, _ = G.physical(dev, 4, M, 2, t, theta, layout=kw["layout"],
                                                     at=[(p["where"]["r0"], p["where"]["c0"])])
                    err = (G.exact_placed_check(qc, placed, used, 4, M, 2, t, theta) if len(used) <= 20
                           else mps_check(qc, placed, used, 4, M, 2, t, theta) if t == 1
                           else sv32_check(qc, placed, used, 4, M, 2, t, theta))
                    common = sorted(set(used) & set(f["used"]))
                    print(f"{dev.name} 4x{M}x2 t{t} {name:21} r0 {p['where']['r0']} c0 {p['where']['c0']}  CZ {p['cz']:4} "
                          f"layers {p['cz_layers']:4} qubits {len(used):2} shared with fold {len(common):2}  "
                          f"accept {all(p['checks'].values())}  max|placed - exact| {err:.1e}", flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    ts = (1,)
    if args and args[0] == "--m3-ts":
        ts, args = tuple(int(v) for v in args[1].split(",")), args[2:]
    main(args, ts)
