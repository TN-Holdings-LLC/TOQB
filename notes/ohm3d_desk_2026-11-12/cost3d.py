"""Desk estimate (not declared, no device): CZ cost per step of an fSim(pi/4, pi/2) cubic lattice on Heron, built from
psf-os grid3d's fixed fold layout. The kicked-Ising layout is converted gate by gate: each RZZ bond -> fSim on the
same pair; each bridge CX (a, b) (b is |0> between uses) -> SWAP (a, b), so CX RZZ(b, p) CX becomes SWAP fSim SWAP.
Then compiled to the CZ basis (no routing: every pair is a coupler) and counted.
usage: PYTHONPATH=<psf-os> python cost3d.py DEV_DIR"""
import collections
import sys

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import UnitaryGate

from psf_os import device as Dv, grid3d as G


def fsim(theta, phi):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[1, 0, 0, 0], [0, c, -1j * s, 0], [0, -1j * s, c, 0], [0, 0, 0, np.exp(-1j * phi)]])


def convert(qc, theta=np.pi / 4, phi=np.pi / 2):
    out = QuantumCircuit(qc.num_qubits)
    F = UnitaryGate(fsim(theta, phi), label="fsim")
    for ins in qc.data:
        qs = [qc.find_bit(q).index for q in ins.qubits]
        name = ins.operation.name
        if name == "rzz":
            out.append(F, qs)
        elif name == "cx":
            out.swap(*qs)
        elif name in ("rx", "barrier", "measure"):
            continue  # the kicked-Ising field is not part of the fSim circuit
        else:
            out.append(ins.operation, qs)
    return out


def cz_stats(qc):
    c = transpile(qc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=1)
    return c.count_ops().get("cz", 0), c.depth(filter_function=lambda i: i.operation.name == "cz")


if __name__ == "__main__":
    dev = Dv.Device.load(sys.argv[1])
    for (L, M, N) in ((4, 2, 2), (4, 3, 2), (4, 4, 2)):
        rows = []
        for t in (1, 2):
            qc, placed, used, passes, info = G.physical(dev, L, M, N, t, 0.8, info=True)
            ki = cz_stats(qc)
            fs = cz_stats(convert(qc))
            rows.append((t, len(used), ki, fs))
        for t, nu, ki, fs in rows:
            print(f"{L}x{M}x{N} t{t}: qubits {nu}; kicked Ising CZ {ki[0]} depth {ki[1]}; fSim CZ {fs[0]} depth {fs[1]}",
                  flush=True)
