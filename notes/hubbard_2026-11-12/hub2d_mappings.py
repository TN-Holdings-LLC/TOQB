"""2D Fermi-Hubbard, R x W grid (4 x 4 = 32 modes), one first-order Trotter step: CZ count and CZ layers per
fermion-to-qubit mapping, by formula (workplace VS Claude, 2026-11-12; desk study, not declared, no device).

Gate costs (CZ), taken from the circuits counted on 11-11 (hub_count.py, hub2d_count.py; transpiled to cz/rz/sx/x):
  onsite U (RZZ on u_i, d_i)                 2 CZ
  hop exp(-i th (XX+YY)/2) on adjacent modes 2 CZ
  FSWAP (SWAP . CZ, one KAK class of iSWAP)  2 CZ
  site swap (u_a d_a u_b d_b -> u_b d_b u_a d_a) = 4 FSWAP in 3 layers   8 CZ, 6 CZ layers
  bond between snake neighbours (FSWAP, two hops, FSWAP)                 8 CZ
  1D step on a line of n sites: 10 n - 8 CZ, 12 CZ layers (measured on 11-11, every n)
  Pauli rotation exp(-i th P) of weight w on a connected path            2 (w - 1) CZ, 2 (w - 1) CZ layers

Mapping 1 (JW, one line, vertical bonds by a fermionic swap network): the snake-neighbour bonds as the 1D step; the
other vertical bonds in each two-row block: the block's order is a0 .. a(W-1) b(W-1) .. b0 (row r+1 runs backwards),
so the vertical pairs are nested; an odd-even transposition of sites toward the interleaved order a0 b0 a1 b1 ...
brings every pair together. That needs W (W - 1) site swaps (each b passes the a's after its partner, W (W - 1) / 2,
and the b's reverse among themselves, W (W - 1) / 2); each pair is hopped as a site-level bond when it meets (8 CZ),
then the swaps are undone (W (W - 1) more). Blocks (0,1), (2,3), ... run together, then (1,2), ...
`network_circuit` builds this circuit and counts it (a check of the formula, and the 2 x 4 statevector check).

usage: python hub2d_mappings.py     (prints the table and the checks)
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "hubbard_2026-11-11"))

J, U, DT = 1.0, 4.0, 0.25
ONSITE, HOP, FSWAP, SITE_SWAP, SITE_SWAP_LAYERS, BOND = 2, 2, 2, 8, 6, 8


def one_d(n):
    return 10 * n - 8, 12


def jw_network_formula(R, W):
    """mapping 1 by formula: (qubits, CZ, CZ layers)."""
    n = R * W
    cz1, ly1 = one_d(n)
    blocks = R - 1                                   # two-row blocks, each with W - 1 vertical pairs off the snake
    swaps = 2 * W * (W - 1)                          # W (W - 1) to interleave, the same to undo
    cz = cz1 + blocks * (swaps * SITE_SWAP + (W - 1) * BOND)
    # CZ layers: not by formula (the odd-even layers overlap); taken from the built circuit (network_circuit)
    return 2 * n, cz, None


def compact_formula(R, W):
    """mapping 3a, compact encoding (Derby-Klassen type): per spin, one qubit per site plus about one auxiliary qubit
    per two faces; hopping terms of Pauli weight at most 3 (two rotations each). Upper estimate with every hop at
    weight 3 and all-to-all neighbour gates on the encoding's own graph (not heavy-hex)."""
    faces = (R - 1) * (W - 1)
    aux = math.ceil(faces / 2)
    q = 2 * (R * W + aux)
    bonds = R * (W - 1) + (R - 1) * W
    rot = 2 * (3 - 1)                                # CZ per weight-3 rotation
    cz = 2 * bonds * 2 * rot + R * W * ONSITE        # 2 spins, 2 rotations per hop
    rounds = 4                                       # bonds of a square grid in 4 colour classes (lower estimate)
    layers = rounds * 2 * rot + 2
    return q, cz, layers


def vc_formula(R, W):
    """mapping 3b, Verstraete-Cirac: one auxiliary qubit per mode; horizontal hops weight 2, vertical hops weight 4
    (through the auxiliaries); plus the preparation of the auxiliary stabiliser state (not counted here)."""
    n = R * W
    q = 2 * 2 * n
    h, v = R * (W - 1), (R - 1) * W
    cz = 2 * (h * 2 * 2 * (2 - 1) + v * 2 * 2 * (4 - 1)) + n * ONSITE
    layers = 2 * 2 * 2 * (2 - 1) + 2 * 2 * 2 * (4 - 1) + 2      # 2 colour classes per direction
    return q, cz, layers


# ---- check of mapping 1 by building the circuit -----------------------------------------------------------------

def network_circuit(R, W):
    from qiskit import QuantumCircuit
    from hub2d_count import Line, snake
    sites = snake(R, W)
    qc = QuantumCircuit(2 * R * W)
    log = []
    line = Line(qc, sites, log)
    n = R * W
    for k in range(n):
        qc.rzz(U * DT / 2, 2 * k, 2 * k + 1)
        qc.rz(-U * DT / 2, 2 * k)
        qc.rz(-U * DT / 2, 2 * k + 1)
        log.append(("U", sites[k]))
    for par in (0, 1):
        for k in range(par, n - 1, 2):
            line.hop(k)
    done = {frozenset(p) for kind, *p in log if kind == "hop"}
    for start in (0, 1):
        for r in range(start, R - 1, 2):
            lo, hi = r * W, (r + 2) * W
            row_a = [line.order[k] for k in range(lo, lo + W)]
            rank = {}
            for p, a in enumerate(row_a):                      # target: a0 b0 a1 b1 ... (b = the site below a)
                rank[a] = 2 * p
                rank[(a[0] + 1, a[1])] = 2 * p + 1
            want = {frozenset({a, (a[0] + 1, a[1])}) for a in row_a} - done
            swaps, layer = [], 0
            while True:
                for k in range(lo, hi - 1):
                    p = frozenset({line.order[k], line.order[k + 1]})
                    if p in want:
                        line.hop(k)
                        want.discard(p)
                        done.add(p)
                if not want:
                    break
                moved = False
                for k in range(lo + layer % 2, hi - 1, 2):
                    if rank[line.order[k]] > rank[line.order[k + 1]]:
                        line.swap_sites(k)
                        swaps.append(k)
                        moved = True
                layer += 1
                if layer > 4 * W and not moved:
                    raise RuntimeError("pairs not met")
            for k in reversed(swaps):
                line.swap_sites(k)
    assert line.order == sites
    return qc, log, sites


def count(qc, level):
    from qiskit import transpile
    from qiskit.transpiler import CouplingMap
    t = transpile(qc, coupling_map=CouplingMap.from_line(qc.num_qubits), basis_gates=["cz", "rz", "sx", "x"],
                  optimization_level=level, initial_layout=list(range(qc.num_qubits)), routing_method="none",
                  seed_transpiler=0)
    return t.count_ops().get("cz", 0), t.depth(lambda i: i.operation.name == "cz")


def statevector_check(R, W):
    """the circuit against the product of exp(-i dt h) of the applied terms (sparse, from a Neel start)."""
    from scipy.sparse.linalg import expm_multiply
    from qiskit.quantum_info import SparsePauliOp, Statevector
    qc, log, sites = network_circuit(R, W)
    n = 2 * R * W
    pos = {s: k for k, s in enumerate(sites)}

    def lowering(m):
        lab = ["I"] * n
        for j in range(m):
            lab[j] = "Z"
        a = lab.copy(); a[m] = "X"
        b = lab.copy(); b[m] = "Y"
        return SparsePauliOp(["".join(reversed(a)), "".join(reversed(b))], [0.5, 0.5j])

    c = [lowering(m) for m in range(n)]
    cd = [x.adjoint() for x in c]
    num = [(cd[m] @ c[m]).simplify() for m in range(n)]
    idx = sum(1 << (2 * k + ((sites[k][0] + sites[k][1]) % 2)) for k in range(R * W))
    psi = np.zeros(2 ** n, dtype=complex)
    psi[idx] = 1
    out = Statevector(psi).evolve(qc).data
    for kind, *p in log:
        if kind == "U":
            k = pos[p[0]]
            h = U * (num[2 * k] @ num[2 * k + 1])
        else:
            a, b = pos[p[0]], pos[p[1]]
            h = SparsePauliOp("I" * n, 0)
            for s in (0, 1):
                h = h + (-J) * (cd[2 * a + s] @ c[2 * b + s] + cd[2 * b + s] @ c[2 * a + s])
        psi = expm_multiply(-1j * DT * h.simplify().to_matrix(sparse=True), psi)
    ov = np.vdot(psi, out)
    bonds = sorted(tuple(sorted(p)) for kind, *p in log if kind == "hop")
    grid = sorted(tuple(sorted(((r, c_), (r2, c2)))) for r in range(R) for c_ in range(W)
                  for r2, c2 in ((r + 1, c_), (r, c_ + 1)) if r2 < R and c2 < W)
    return float(np.linalg.norm(out * np.conj(ov) / abs(ov) - psi)), bonds == grid


if __name__ == "__main__":
    R, W = 4, 4
    print(f"1D L {R * W} ({2 * R * W} qubits): CZ {one_d(R * W)[0]}, layers {one_d(R * W)[1]}")
    q, cz, ly = jw_network_formula(R, W)
    print(f"mapping 1 (JW line, swap network), formula: qubits {q}, CZ {cz}, layers {ly}")
    qc, log, _ = network_circuit(R, W)
    for lev in (1, 3):
        print(f"mapping 1, circuit, transpile level {lev}: CZ {count(qc, lev)[0]}, layers {count(qc, lev)[1]}")
    print(f"mapping 3a (compact), formula (own graph, not heavy-hex): qubits / CZ / layers {compact_formula(R, W)}")
    print(f"mapping 3b (Verstraete-Cirac), formula (own graph; stabiliser preparation not counted): {vc_formula(R, W)}")
    err, ok = statevector_check(2, 4)
    print(f"check, mapping 1 circuit 2 x 4 (16 qubits), Neel start: |psi_circuit - psi_product| = {err:.1e} "
          f"(up to global phase); every bond once: {ok}")
