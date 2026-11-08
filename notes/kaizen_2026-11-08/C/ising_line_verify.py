"""C: the 4x2x2 line schedule (bridges 1, 5) used for the kicked Ising model (RZZ(-pi/2) bonds, RX(theta) layer per
step), on the fez record at the line translation of heis3d.physical_line. Ops: SWAP.RZZ as psf-os _swap_bond (2 CX),
RZZ in place (rzz_exact: 1 CZ), y-bond CX(a,b) RZZ(b,q) CX(a,b) (the bridge copies a, no move). CZ by RuleCompiler
after rzz_exact; noiseless <Z> against grid3d.exact (the bonds of a step commute, so the order does not matter)."""
import sys
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from psf_os import device as Dv, grid3d as G, mirror2d as Mi
from psf_os.compile import RuleCompiler, rzz_exact
import heis3d as H

dev = Dv.Device.load(sys.argv[1]); rc = RuleCompiler(dev)
theta = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
adj = {}
for a, b in dev.couplers:
    adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
r0, c0 = 1, 0
bl = {c - c0: b for b, c in G.bridges(adj, r0, 2).get(0, []) if 0 <= c - c0 < 8}
br = tuple(sorted(bl)); assert br == (1, 5), br
A = [20 * r0 + c0 + p for p in range(8)]; B = [20 * (r0 + 1) + c0 + p for p in range(8)]
start_names, text = H.LINE_SCHEDULES[br]; ops = H._parse_ops(text)
idx = {s: i for i, s in enumerate(G.sites(4, 2, 2))}
site = lambda name, y: idx[(name % 4, y, name // 4)]

def swap_bond(qc, a, b):
    qc.z(a); qc.z(b); qc.h(b); qc.cx(b, a); qc.cx(a, b); qc.h(a); qc.s(a); qc.s(b)

for t in (1, 2, 3, 4):
    qc = QuantumCircuit(dev.num_qubits)
    arr = [H._NAMES.index(v) for v in start_names]
    for step in range(t):
        seq = ops if step % 2 == 0 else list(reversed(ops))
        ydone = set()
        def yb():
            for p in br:
                if arr[p] not in ydone:
                    qc.cx(A[p], bl[p]); qc.rzz(-np.pi / 2, bl[p], B[p]); qc.cx(A[p], bl[p]); ydone.add(arr[p])
        yb()
        for kind, e in seq:
            for line in (A, B):
                if kind == "SWAP.U":
                    swap_bond(qc, line[e], line[e + 1])
                elif kind == "U":
                    qc.rzz(-np.pi / 2, line[e], line[e + 1])
                else:
                    qc.swap(line[e], line[e + 1])
            if kind != "U":
                arr[e], arr[e + 1] = arr[e + 1], arr[e]
            yb()
        assert len(ydone) == 8
        for line in (A, B):
            for q in line:
                qc.rx(theta, q)
    cz = Mi.cz_count(rc.pm.run(rzz_exact(qc)))
    used = sorted({qc.find_bit(q).index for i in qc.data for q in i.qubits})
    m = {u: i for i, u in enumerate(used)}
    small = QuantumCircuit(len(used))
    for ins in qc.data:
        small.append(ins.operation, [m[qc.find_bit(q).index] for q in ins.qubits])
    p = Statevector(small).probabilities(); ii = np.arange(len(p))
    z = {u: float(np.sum(p * (1 - 2 * ((ii >> m[u]) & 1)))) for u in used}
    ex = G.exact(4, 2, 2, t, theta)
    err = max(abs(z[(A if y == 0 else B)[pp]] - ex[str(site(arr[pp], y))]) for y in (0, 1) for pp in range(8))
    berr = max(1 - z[b] for b in bl.values())
    print(f"Ising line 4x2x2 t {t}: CZ {cz}  max|placed - exact| {err:.1e}  bridges |0>: {berr:.1e}")
