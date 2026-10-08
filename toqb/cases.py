"""Circuit sources. v0 has a small built-in set, enough for a smoke run; the standard set (Benchpress-derived
circuits, hardware-fitness circuits, task circuits) is added before the first scored run.

Spec strings:
    ghz:N            GHZ preparation on N qubits
    qft:N            the quantum Fourier transform on N qubits, expanded to one- and two-qubit gates
    brick:N:L:SEED   L layers of Haar-random two-qubit unitaries in a brick pattern
    qasm:PATH        an OpenQASM 2 file
"""
from __future__ import annotations


def get_case(spec: str):
    kind, _, arg = spec.partition(":")
    from qiskit import QuantumCircuit, transpile
    if kind == "ghz":
        n = int(arg)
        qc = QuantumCircuit(n)
        qc.h(0)
        for q in range(n - 1):
            qc.cx(q, q + 1)
        return qc
    if kind == "qft":
        from qiskit.circuit.library import QFTGate
        n = int(arg)
        qc = QuantumCircuit(n)
        qc.append(QFTGate(n), range(n))
        return transpile(qc, basis_gates=["u", "cx"], optimization_level=0)
    if kind == "brick":
        import numpy as np
        from qiskit.quantum_info import random_unitary
        n, layers, seed = (int(x) for x in arg.split(":"))
        rng = np.random.default_rng(seed)
        qc = QuantumCircuit(n)
        for layer in range(layers):
            for a in range(layer % 2, n - 1, 2):
                qc.unitary(random_unitary(4, seed=int(rng.integers(2**31))), [a, a + 1])
        return qc
    if kind == "qasm":
        return QuantumCircuit.from_qasm_file(arg)
    raise ValueError(f"unknown case spec {spec!r}")
