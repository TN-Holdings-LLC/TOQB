"""Answers for the Ohm's-law device job (workplace, 2026-11-12; home's instruction of 02:05 CET; not declared).

Circuits (notes/ohm_2026-11-11, samples6.py): N qubits on a chain, a random product state (bits), then CYCLES cycles of
the fSim(pi/4, phi) brickwork (even bonds, then odd bonds); arms
    A0: phi 0 (free fermions)          A1: phi pi/2 (isotropic, integrable)
    A2: phi pi/2 and, after each cycle, RZ(H p_k) on qubit k with p = (1, -1, 0) repeating, H 1 (interacting and not
        integrable: diffusive, the Ohmic t^(1/2), home 11-12).
RZ is virtual on IBM devices, so A1 and A2 carry the same CZ count and layers (checked by the builder).
Bit strings: K strings, each qubit of the left half |1> with probability (1 + m) / 2, of the right half (1 - m) / 2
(a weakly polarised wall), and each string's complement (the mirrored wall: the left leans to |0>), which reverses the
sign of the transfer and of the drift that decay towards |0> adds to it. The same strings in every arm and time.

Answers: per-qubit <Z> of every circuit, A1 / A2 by quimb's CircuitMPS (cutoff 1e-10 by default, bond cap CHI), A0 by free
fermions (exact at any size: <n_x> = sum over occupied y of |W_xy|^2). Values go only to OUT.json (sealed until the
verdicts); printed are checks only: largest bond (below the cap), quimb's error estimate, total Z (conserved exactly:
the initial value), for A0 also quimb against free fermions on the first strings (--pipeline-check).
usage: python gpu/ohm_answers.py OUT.json --N 40 --K 14 --m 0.5 --cycles 3 6 --seed SEED [--chi 2048]
       [--pipeline-check 2]
"""
import argparse
import hashlib
import json
import os
import time

import numpy as np

THETA = np.pi / 4
ARMS = {"A0": (0.0, 0.0), "A1": (np.pi / 2, 0.0), "A2": (np.pi / 2, 1.0)}
PATTERN = (1, -1, 0)


def fsim(theta, phi):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[1, 0, 0, 0], [0, c, -1j * s, 0], [0, -1j * s, c, 0], [0, 0, 0, np.exp(-1j * phi)]])


def strings(N, K, m, seed):
    """[(name, bits)]: K strings s00.. and their complements c00.. (bits[k] = 1: qubit k starts in |1>)."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(K):
        b = [int(rng.random() < ((1 + m) / 2 if k < N // 2 else (1 - m) / 2)) for k in range(N)]
        out.append((f"s{i:02d}", b))
        out.append((f"c{i:02d}", [1 - x for x in b]))
    return out


def circuit(N, cycles, arm, bits):
    """The logical circuit on N qubits (qubit k = chain label k), no measurement. fSim as a two-qubit unitary on
    (k, k + 1) (symmetric under exchanging the two qubits), RZ(0) on the field's zero sites left out."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate
    phi, H = ARMS[arm]
    G = UnitaryGate(fsim(THETA, phi), label=f"fsim_{arm[:2]}")
    qc = QuantumCircuit(N)
    for k, b in enumerate(bits):
        if b:
            qc.x(k)
    for _ in range(cycles):
        for par in (0, 1):
            for q in range(par, N - 1, 2):
                qc.append(G, [q, q + 1])
        if H:
            for k in range(N):
                if PATTERN[k % 3]:
                    qc.rz(H * PATTERN[k % 3], k)
    return qc


def z_quimb(N, cycles, arm, bits, chi, cutoff=1e-10):
    import quimb.tensor as qtn
    phi, H = ARMS[arm]
    c = qtn.CircuitMPS(N, max_bond=chi, cutoff=cutoff)
    X = np.array([[0, 1], [1, 0]])
    for k, b in enumerate(bits):
        if b:
            c.apply_gate_raw(X, (k,))
    G = fsim(THETA, phi)
    for _ in range(cycles):
        for par in (0, 1):
            for q in range(par, N - 1, 2):
                c.apply_gate_raw(G, (q, q + 1))
        if H:
            for k in range(N):
                h = H * PATTERN[k % 3]
                if h:
                    c.apply_gate_raw(np.diag([np.exp(-0.5j * h), np.exp(0.5j * h)]), (k,))
    Z = np.diag([1.0, -1.0])
    z = np.array([float(np.real(c.psi.local_expectation(Z, k))) for k in range(N)])
    return z, c.psi.max_bond(), float(c.error_estimate()) if hasattr(c, "error_estimate") else None


def z_free(N, cycles, bits):
    g = np.array([[np.cos(THETA), -1j * np.sin(THETA)], [-1j * np.sin(THETA), np.cos(THETA)]])
    W = np.eye(N, dtype=complex)
    for _ in range(cycles):
        for par in (0, 1):
            for q in range(par, N - 1, 2):
                W[[q, q + 1], :] = g @ W[[q, q + 1], :]
    occ = [k for k, b in enumerate(bits) if b]
    return 1 - 2 * np.sum(np.abs(W[:, occ]) ** 2, axis=1)


def tag(arm, t, name):
    return f"{arm}_t{t}_{name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--N", type=int, default=40)
    ap.add_argument("--K", type=int, required=True)
    ap.add_argument("--m", type=float, required=True)
    ap.add_argument("--cycles", type=int, nargs="+", default=[3, 6])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--chi", type=int, default=2048)
    ap.add_argument("--cutoff", type=float, default=1e-10, help="quimb's singular-value cutoff (1e-12 took 104 s for one "
                    "6-cycle string here, 2026-11-12; samples6.py and design_pod.py use 1e-10)")
    ap.add_argument("--pipeline-check", type=int, default=0, help="A0 by quimb too on the first this many strings")
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    strs = strings(a.N, a.K, a.m, a.seed)
    vals, worst = {}, dict(bond=0, err=0.0, totz=0.0, pipeline=0.0, seconds=0.0)
    for arm in ARMS:
        for t in a.cycles:
            t0 = time.time()
            for i, (name, bits) in enumerate(strs):
                z0 = float(np.sum(1 - 2 * np.array(bits)))
                if arm == "A0":
                    z = z_free(a.N, t, bits)
                    if i < a.pipeline_check:
                        zq, bond, err = z_quimb(a.N, t, arm, bits, a.chi, a.cutoff)
                        worst["pipeline"] = max(worst["pipeline"], float(np.abs(zq - z).max()))
                else:
                    t1 = time.time()
                    z, bond, err = z_quimb(a.N, t, arm, bits, a.chi, a.cutoff)
                    worst["bond"] = max(worst["bond"], bond)
                    worst["err"] = max(worst["err"], err or 0.0)
                    worst["seconds"] = max(worst["seconds"], time.time() - t1)
                worst["totz"] = max(worst["totz"], abs(float(z.sum()) - z0))
                vals[tag(arm, t, name)] = z.tolist()
            print(f"{arm} t {t}: {len(strs)} circuits, {time.time() - t0:.0f} s; so far: largest bond {worst['bond']} "
                  f"(cap {a.chi}), error estimate {worst['err']:.1e}, |total Z - initial| {worst['totz']:.1e}, "
                  f"slowest {worst['seconds']:.1f} s" + (f", A0 quimb against free fermions {worst['pipeline']:.1e}"
                                                         if arm == "A0" and a.pipeline_check else ""), flush=True)
    meta = dict(N=a.N, K=a.K, m=a.m, cycles=a.cycles, seed=a.seed, chi=a.chi, cutoff=a.cutoff, theta=THETA,
                arms={k: dict(phi=v[0], H=v[1]) for k, v in ARMS.items()}, pattern=PATTERN,
                strings={n: "".join(map(str, b)) for n, b in strs}, checks=worst)
    json.dump(dict(meta=meta, z=vals), open(a.out, "w"), sort_keys=True)
    print("answers", a.out, "sha256", hashlib.sha256(open(a.out, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
