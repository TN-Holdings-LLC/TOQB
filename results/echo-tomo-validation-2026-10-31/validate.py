"""Validation of toqb.echo_tomo's reading on a simulator (2026-10-31): a small rule-style echo (n = 8 ring) with an
error injected after every CZ that touches qubits 3 and 4. Three kinds: a coherent single-qubit rotation RX(eps); a
coherent two-qubit RZZ(eps) on the pair (3, 4); a depolarizing channel of probability p. The scorer must call the
single-qubit rotation ROTATED (or at least keep |v|), the depolarizing channel LOST, and see the coherent rotation's
Z component change sign over depth."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from qiskit import QuantumCircuit  # noqa: E402
from qiskit_aer import AerSimulator  # noqa: E402
from qiskit_aer.noise import NoiseModel, depolarizing_error  # noqa: E402

from toqb import echo_tomo as ET  # noqa: E402
from toqb import kising_charge as KC  # noqa: E402
from toqb import kising_echo as KE  # noqa: E402

N, S, SHOTS = 8, (3, 4), 20000
sim = AerSimulator(method="density_matrix", seed_simulator=7)


def inject(qc, kind, eps):
    out = QuantumCircuit(*qc.qregs, *qc.cregs)
    for i in qc.data:
        qs = [qc.find_bit(q).index for q in i.qubits]
        out.append(i.operation, [out.qubits[q] for q in qs], [out.clbits[qc.find_bit(c).index] for c in i.clbits])
        if i.operation.name == "cz":
            for q in qs:
                if q in S:
                    if kind == "rx":
                        out.rx(eps, q)
                    elif kind == "dep":
                        out.id(q)
            if kind == "rzz" and set(qs) & set(S):
                out.rzz(eps, S[0], S[1])
    return out


def components(kind, eps, L, bases="XYZ"):
    noise = None
    if kind == "dep":
        noise = NoiseModel()
        for q in S:
            noise.add_quantum_error(depolarizing_error(eps, 1), ["id"], [q])
    res = {}
    for b in bases:
        cc = {}
        for i in KC.INPUTS:
            qc = inject(KE.circuit(KC.input_bits(i, N), N, L, 0.6, 0.0), kind, eps)
            c = ET.with_basis(qc, b)
            r = sim.run(c, shots=SHOTS, noise_model=noise, basis_gates=None).result()
            cc[i] = r.get_counts()
        res[b] = ET.aligned(cc, N)
    return res


def main():
    print(f"n = {N}, error after every CZ on qubits {S}; values for the segment {S} and the rest")
    for kind, eps in (("rx", 0.08), ("rx", 0.15), ("rzz", 0.15), ("rzz", 0.3), ("dep", 0.01), ("dep", 0.03)):
        c = components(kind, eps, 6)
        vx, vy, vz = (c[b][0] for b in "XYZ")
        r = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
        tf = np.sqrt(vx ** 2 + vy ** 2) / np.maximum(r, 1e-12)
        g, rest = list(S), [j for j in range(N) if j not in S]
        v = verdict_where(float(np.mean(r[g])), float(np.mean(r[rest])), float(np.mean(tf[g])))
        zs, ses = [], []
        for L in (2, 4, 6, 8, 12):
            a, se = components(kind, eps, L, "Z")["Z"]
            zs.append(float(np.mean(a[g])))
            ses.append(float(np.sqrt(np.sum(se[g] ** 2)) / len(g)))
        sc = ET.sign_change([2 * L for L in (2, 4, 6, 8, 12)], zs, ses)
        print(f"{kind:4s} {eps:5.2f} | D 12: vz seg {np.mean(vz[g]):+.3f} rest {np.mean(vz[rest]):+.3f}; |v| seg "
              f"{np.mean(r[g]):.3f} rest {np.mean(r[rest]):.3f}; transverse seg {np.mean(tf[g]):.2f} -> {v} | "
              f"vz seg over D 4..24: " + " ".join(f"{x:+.2f}" for x in zs) + f" -> {sc}")


def verdict_where(r_seg, r_rest, tf_seg, keep=0.8, lost=0.5, tilt=0.5):
    """The first-draft rule that validate.txt was made with (ROTATED / LOST / MIXED); superseded in toqb.echo_tomo by
    verdict_length, verdict_depth and verdict_corr after this check."""
    if r_seg < lost * r_rest:
        return "LOST"
    if r_seg >= keep * r_rest and tf_seg >= tilt:
        return "ROTATED"
    return "MIXED"


def connected(kind, eps, L):
    """Mean |<Z_a Z_b> - <Z_a><Z_b>| over the echo inputs, for the pair (3, 4) and for the pairs outside the segment."""
    noise = None
    if kind == "dep":
        noise = NoiseModel()
        for q in S:
            noise.add_quantum_error(depolarizing_error(eps, 1), ["id"], [q])
    seg, rest = [], []
    for i in KC.INPUTS:
        qc = inject(KE.circuit(KC.input_bits(i, N), N, L, 0.6, 0.0), kind, eps)
        cnt = sim.run(qc, shots=SHOTS, noise_model=noise).result().get_counts()
        Z = []
        w = []
        for key, k in cnt.items():
            b = key.replace(" ", "")
            Z.append([1 - 2 * int(b[N - 1 - j]) for j in range(N)])
            w.append(k)
        Z, w = np.array(Z, float), np.array(w, float) / sum(w)
        m = w @ Z
        for a in range(N):
            b = (a + 1) % N
            c = abs(float(w @ (Z[:, a] * Z[:, b]) - m[a] * m[b]))
            (seg if (a, b) == S else rest).append(c)
    return float(np.mean(seg)), float(np.mean(rest))


def main_corr():
    print("connected ZZ correlation at D = 12, pair (3, 4) against the other neighbour pairs:")
    for kind, eps in (("rx", 0.15), ("rzz", 0.15), ("rzz", 0.3), ("dep", 0.03)):
        s_, r_ = connected(kind, eps, 6)
        print(f"  {kind:4s} {eps:5.2f}: segment pair {s_:.3f}, other pairs {r_:.3f}")


if __name__ == "__main__":
    if "corr" in sys.argv[1:]:
        main_corr()
    else:
        main()
