"""1D Fermi-Hubbard, interleaved Jordan-Wigner order (u0 d0 u1 d1 ...), first-order Trotter step:
onsite U (RZZ + RZ on each u_i,d_i pair), then even bonds and odd bonds: FSWAP(d_i, u_{i+1}) brings same-spin
neighbours together, hopping exp(-i th (XX+YY)/2) on (u_i,u_{i+1}) and (d_i,d_{i+1}), FSWAP back.
Counts CZ and CZ layers after transpiling to cz/rz/sx/x on a line (no routing needed)."""
import sys
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import XXPlusYYGate
from qiskit.transpiler import CouplingMap


def fswap(qc, a, b):
    qc.swap(a, b)
    qc.cz(a, b)


def step(qc, L, J=1.0, U=4.0, dt=0.25):
    for i in range(L):
        qc.rzz(U * dt / 2, 2 * i, 2 * i + 1)
    for par in (0, 1):
        for i in range(par, L - 1, 2):
            u0, d0, u1, d1 = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
            fswap(qc, d0, u1)               # order now u0 u1 d0 d1 on positions 2i..2i+3
            qc.append(XXPlusYYGate(2 * J * dt), [2 * i, 2 * i + 1])
            qc.append(XXPlusYYGate(2 * J * dt), [2 * i + 2, 2 * i + 3])
            fswap(qc, 2 * i + 1, 2 * i + 2)


def count(L, n):
    q = 2 * L
    qc = QuantumCircuit(q)
    for _ in range(n):
        step(qc, L)
    cm = CouplingMap.from_line(q)
    t = transpile(qc, coupling_map=cm, basis_gates=["cz", "rz", "sx", "x"], optimization_level=1,
                  initial_layout=list(range(q)), routing_method="none", seed_transpiler=0)
    cz = t.count_ops().get("cz", 0)
    layers = t.depth(lambda i: i.operation.name == "cz")
    return cz, layers


for L in (8, 16, 20, 24, 30):
    for n in (1, 2, 4, 6):
        cz, ly = count(L, n)
        print(f"L {L:2} qubits {2*L:2} steps {n}: CZ {cz:5} CZ layers {ly:4} CZ per qubit {cz*2/(2*L):5.1f}")
