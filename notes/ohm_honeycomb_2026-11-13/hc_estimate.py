"""Honeycomb strips for the Ohm question: sizes, CZ per cycle, cost of the exact answers, distance from full mixing
(workplace, 2026-11-13; handover 11-12 item 2-1; desk only, not declared, no device).

Strip rule (extends home VS's two-row rule, notes/ohm_sim_2026-11-12/ohm_sim.py, honeycomb_layout): on the Heron r2
coupling graph (rows of 16 qubits starting at 0, 20, 40, ...; bridge qubits 16-19, 36-39, ... join equal columns of
neighbouring rows), take rows 0 .. R-1, columns 0 .. c of each, and every bridge whose two ends are inside; failed
qubits and couplers of the record are left out (none in rows 0-2 on kingston 11-12). Labels: sorted by (column,
level), level = 2 x row for a row qubit and 2 x row + 1 for a bridge; the left half of the labels is the left of the
wall (the wall at the middle column). One cycle = fSim(pi/4, pi/2) once on every bond of the strip, in colours found
greedily in the sorted bond order, colour after colour (as ohm_sim.colour).
Exact answers: quimb CircuitMPS over the label order (cutoff 1e-10, cap 4096), per circuit timed; the 1-minute rule of
the handover stops a strip at the first circuit over 60 s. Strings: gpu/ohm_answers.strings (m 0.5, seed 20261112).
Full mixing as home (ohm_sim.py, results/ohm-2026-11-12): every Z = 0, W_mixed = mean of (m0_R(c) - m0_R(s)) / 2;
beside, the end of the noiseless dynamics (the count of |1> kept, spread evenly): M = n_total N_R / N - m0_R.
usage: python hc_estimate.py DEVICE_JSON OUT.jsonl --strips 2x15 3x9 3x11 3x15 --cycles 3 6 --K 2
"""
import argparse
import json
import os
import signal
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "gpu"))
import ohm_answers as OA  # noqa: E402

THETA, PHI = np.pi / 4, np.pi / 2


def device_edges(path):
    d = json.load(open(path))
    bad_q = set(d.get("failed_qubits", []))
    bad_e = {tuple(sorted(e)) for e in d.get("failed_couplers", [])}
    return {tuple(sorted(e)) for e in d["couplers"] if tuple(sorted(e)) not in bad_e and not (set(e) & bad_q)}, bad_q


def strip(E, R, c, bad_q):
    qs = []
    for r in range(R):
        for col in range(c + 1):
            q = 20 * r + col
            if q not in bad_q:
                qs.append((col, 2 * r, q))
    inside = {q for _, _, q in qs}
    for r in range(R - 1):
        for b in range(20 * r + 16, 20 * r + 20):
            ends = {y for e in E for y in e if b in e and y != b}
            up = [y for y in ends if 20 * r <= y < 20 * r + 16]
            dn = [y for y in ends if 20 * (r + 1) <= y < 20 * (r + 1) + 16]
            if up and dn and up[0] in inside and dn[0] in inside and b not in bad_q:
                qs.append((up[0] - 20 * r, 2 * r + 1, b))
    phys = [q for _, _, q in sorted(qs)]
    idx = {q: k for k, q in enumerate(phys)}
    bonds = sorted(tuple(sorted((idx[a], idx[b]))) for a, b in E if a in idx and b in idx)
    return phys, bonds


def colour(bonds):
    col = {}
    for e in bonds:
        used = {col[f] for f in col if set(f) & set(e)}
        col[e] = min(k for k in range(len(bonds)) if k not in used)
    return [[e for e in bonds if col[e] == k] for k in range(max(col.values()) + 1)]


def cz_per_cycle(phys, layers, n_dev):
    """Compile one cycle on the device's own qubits (no routing) and count CZ and CZ layers."""
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit.library import UnitaryGate
    from qiskit.transpiler import CouplingMap
    G = UnitaryGate(OA.fsim(THETA, PHI))
    qc = QuantumCircuit(len(phys))
    for lay in layers:
        for a, b in lay:
            qc.append(G, [a, b])
    edges = [(phys[a], phys[b]) for lay in layers for a, b in lay]
    cm = CouplingMap([list(e) for e in edges] + [[b, a] for a, b in edges])
    t = transpile(qc, coupling_map=cm, basis_gates=["cz", "rz", "sx", "x"], initial_layout=phys,
                  routing_method="none", optimization_level=1, seed_transpiler=0)
    return t.count_ops().get("cz", 0), t.depth(lambda i: i.operation.name == "cz")


class Over(Exception):
    pass


def _alarm(signum, frame):
    raise Over()


def answer(N, layers, cycles, bits, limit):
    import quimb.tensor as qtn
    c = qtn.CircuitMPS(N, max_bond=4096, cutoff=1e-10)
    X = np.array([[0, 1], [1, 0]])
    for k, b in enumerate(bits):
        if b:
            c.apply_gate_raw(X, (k,))
    G = OA.fsim(THETA, PHI)
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(limit)
    t0 = time.time()
    try:
        for _ in range(cycles):
            for lay in layers:
                for a, b in lay:
                    c.apply_gate_raw(G, (a, b))
        Z = np.diag([1.0, -1.0])
        z = np.array([float(np.real(c.psi.local_expectation(Z, k))) for k in range(N)])
    finally:
        signal.alarm(0)
    return z, c.psi.max_bond(), time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("device")
    ap.add_argument("out")
    ap.add_argument("--strips", nargs="+", default=["2x15", "3x9", "3x11", "3x15"])
    ap.add_argument("--cycles", type=int, nargs="+", default=[3, 6])
    ap.add_argument("--K", type=int, default=2)
    ap.add_argument("--limit", type=int, default=60)
    a = ap.parse_args()
    E, bad_q = device_edges(a.device)
    n_dev = json.load(open(a.device))["num_qubits"]
    for s in a.strips:
        R, c = map(int, s.split("x"))
        phys, bonds = strip(E, R, c, bad_q)
        N = len(phys)
        layers = colour(bonds)
        cz, czl = cz_per_cycle(phys, layers, n_dev)
        row = dict(strip=s, N=N, bonds=len(bonds), colours=len(layers), cz_per_cycle=cz, cz_layers_per_cycle=czl,
                   phys=phys, cycles={})
        print(f"strip {s}: N {N}, bonds {len(bonds)}, colours {len(layers)}, CZ per cycle {cz}, CZ layers per cycle "
              f"{czl}", flush=True)
        strs = OA.strings(N, a.K, 0.5, 20261112)
        over = False
        for t in a.cycles:
            if over:
                break
            Ms, info = {}, []
            for name, bits in strs:
                try:
                    z, bond, sec = answer(N, layers, t, bits, a.limit)
                except (Over, SystemError):   # the alarm may land inside numba and come back as SystemError
                    print(f"  t {t} {name}: over {a.limit} s: stopped (1-minute rule)", flush=True)
                    row["cycles"][str(t)] = dict(stopped=f"over {a.limit} s at {name}")
                    over = True
                    break
                m0 = sum(bits[N // 2:])
                Ms[name] = float(((1 - z[N // 2:]) / 2).sum() - m0)
                info.append((bond, round(sec, 1)))
                print(f"  t {t} {name}: bond {bond}, {sec:.1f} s, |total Z - initial| "
                      f"{abs(z.sum() - sum(1 - 2 * x for x in bits)):.1e}", flush=True)
            if over:
                continue
            ks = sorted({n[1:] for n in Ms})
            W = float(np.mean([(Ms['s' + k] - Ms['c' + k]) / 2 for k in ks]))
            m0 = {name: sum(bits[N // 2:]) for name, bits in strs}
            Wm = float(np.mean([(m0['c' + k] - m0['s' + k]) / 2 for k in ks]))     # every Z = 0 (as ohm_sim / ohm-2026-11-12)
            cons = {name: sum(bits) * (N - N // 2) / N - sum(bits[N // 2:]) for name, bits in strs}
            Wc = float(np.mean([(cons['s' + k] - cons['c' + k]) / 2 for k in ks]))   # evenly spread, count kept
            row["cycles"][str(t)] = dict(W=W, W_mixed=Wm, ratio=W / Wm, W_spread_kept=Wc, ratio_kept=W / Wc,
                                         bond_seconds=info, cz=cz * t, cz_layers=czl * t)
            print(f"  t {t}: W {W:.3f}; W_mixed (every Z 0) {Wm:.3f}, ratio {W / Wm:.2f}; evenly spread with the count "
                  f"kept {Wc:.3f}, ratio {W / Wc:.2f}; CZ {cz * t}, CZ layers {czl * t}", flush=True)
        with open(a.out, "a") as f:
            f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
