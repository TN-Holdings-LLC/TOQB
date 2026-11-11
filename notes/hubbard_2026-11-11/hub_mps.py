"""Classical check cost: the Trotter circuit (exact gates, as on the device) from a Neel-like product state
(up on even sites, down on odd sites: half filling), <n_{i s}> per mode by Aer MPS (no truncation set: default
threshold), against a statevector where it fits. Times on this 2-CPU sandbox."""
import sys, time
import numpy as np
from math import comb
from qiskit import QuantumCircuit
from qiskit.circuit.library import XXPlusYYGate
from qiskit.quantum_info import Pauli
from qiskit_aer import AerSimulator

J, U, dt = 1.0, 4.0, 0.25


def circuit(L, nsteps):
    n = 2 * L
    qc = QuantumCircuit(n)
    for i in range(L):          # Neel: site i holds up if i even, down if odd
        qc.x(2 * i + (i % 2))
    for _ in range(nsteps):
        for i in range(L):
            qc.rzz(U * dt / 2, 2 * i, 2 * i + 1); qc.rz(-U * dt / 2, 2 * i); qc.rz(-U * dt / 2, 2 * i + 1)
        for par in (0, 1):
            for i in range(par, L - 1, 2):
                qc.swap(2 * i + 1, 2 * i + 2); qc.cz(2 * i + 1, 2 * i + 2)
                qc.append(XXPlusYYGate(-2 * J * dt), [2 * i, 2 * i + 1])
                qc.append(XXPlusYYGate(-2 * J * dt), [2 * i + 2, 2 * i + 3])
                qc.swap(2 * i + 1, 2 * i + 2); qc.cz(2 * i + 1, 2 * i + 2)
    return qc


def run(L, nsteps, method):
    t0 = time.time()
    from qiskit import transpile
    c = transpile(circuit(L, nsteps), basis_gates=["cx", "u", "rz", "x"], optimization_level=1)
    for k in range(2 * L):
        c.save_expectation_value(Pauli("Z"), [k], label=f"z{k}")
    d = AerSimulator(method=method).run(c, shots=1).result().data()
    return np.array([float(np.real(d[f"z{k}"])) for k in range(2 * L)]), time.time() - t0


L0 = 8
for ns in (2, 6):
    a, ta = run(L0, ns, "statevector"); b, tb = run(L0, ns, "matrix_product_state")
    print(f"L {L0} steps {ns}: max |MPS - statevector| over <Z> {np.max(np.abs(a - b)):.1e}  (sv {ta:.1f} s, mps {tb:.1f} s)")
for L in (20, 30):
    for ns in (4, 6, 8):
        z, t = run(L, ns, "matrix_product_state")
        print(f"L {L} ({2*L} qubits) steps {ns} (Jt {ns*dt:.2f}): MPS {t:.1f} s, sum <Z> {z.sum():+.2e} (0 at half filling)")
