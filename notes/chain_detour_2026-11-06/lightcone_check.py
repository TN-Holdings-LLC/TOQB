"""Noiseless check of a compiled chain circuit by backward light cones (workplace, 2026-11-06; home's 06p item 3).

For each measured site, the gates of the compiled user circuit (as run2d wrote it) that can reach that measurement
are kept (walking the gate list backward from the measured qubit), and the cone alone is simulated by statevector:
exact for that site's <Z> (the circuit's X readout is already in it). Compared with psf_os.dual's closed form at the
dual-unitary point: <X> = cos(2h)^t on chain site t, 0 elsewhere.

usage: PYTHONPATH=<psf-os> python lightcone_check.py RUN_DIR T H
"""
import os
import sys

import numpy as np


def main(run, t, h):
    from qiskit import QuantumCircuit, qpy
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    c = qpy.load(open(os.path.join(run, "runs", "p2d_user.qpy"), "rb"))[0]
    meas = {c.find_bit(i.clbits[0]).index: c.find_bit(i.qubits[0]).index for i in c.data if i.operation.name == "measure"}
    gates = [(i.operation, [c.find_bit(q).index for q in i.qubits]) for i in c.data
             if i.operation.name not in ("measure", "barrier")]
    sim = AerSimulator(method="statevector")
    worst, biggest, z = 0.0, 0, {}
    for s, q in sorted(meas.items()):
        cone, keep = {q}, []
        for op, qs in reversed(gates):
            if cone & set(qs):
                cone |= set(qs)
                keep.append((op, qs))
        order = sorted(cone)
        m = {x: k for k, x in enumerate(order)}
        sub = QuantumCircuit(len(order))
        for op, qs in reversed(keep):
            sub.append(op, [m[x] for x in qs])
        sub.save_expectation_value(Pauli("Z"), [m[q]], label="z")
        v = float(np.real(sim.run(sub, shots=1).result().data()["z"]))
        want = np.cos(2 * h) ** t if s == t else 0.0
        z[s] = v
        worst = max(worst, abs(v - want))
        biggest = max(biggest, len(order))
    print(f"{run}: {len(meas)} sites, largest cone {biggest} qubits, site {t}: {z[t]:.12f} "
          f"(closed form {np.cos(2 * h) ** t:.12f}), worst deviation over all sites {worst:.1e}")
    return worst


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), float(sys.argv[3]))
