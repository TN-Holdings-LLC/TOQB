"""B: the even heavy-hex rows. Every translation (r0, c0), c0 = 0 .. 8 (not only multiples of 4): where do the two
bridges between rows r0, r0 + 1 fall on the 8-column line, does it touch a failed element, and for (1, 5) the CZ
(RuleCompiler, rule A) and the noiseless check at t = 4."""
import sys
from qiskit import QuantumCircuit
from psf_os import device as Dv, grid3d as G, mirror2d as Mi
from psf_os.compile import RuleCompiler
import heis3d as H
import line_merge as LM

dev = Dv.Device.load(sys.argv[1]); rc = RuleCompiler(dev)
adj = {}
for a, b in dev.couplers:
    adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
bad, badc = set(dev.failed_qubits), {frozenset(c) for c in dev.failed_couplers}
cpl = {frozenset(c) for c in dev.couplers}
print(f"device {dev.name}: failed qubits {sorted(bad)}, failed couplers {sorted(tuple(sorted(c)) for c in badc)}")
rows = {}
for r0 in range(0, 7):
    for c0 in range(0, 9):
        bl = {c - c0: b for b, c in G.bridges(adj, r0, 2).get(0, []) if 0 <= c - c0 < 8}
        br = tuple(sorted(bl))
        A = [20 * r0 + c0 + p for p in range(8)]; B = [20 * (r0 + 1) + c0 + p for p in range(8)]
        status = ""
        if br not in H.LINE_SCHEDULES:
            status = f"bridges at {br}: no schedule"
        else:
            t = 4
            out, start, end, log = H._line_build(A, B, bl, br, t, 0.05, 1.0)
            ops = LM.merge(LM.to_L(out))
            qc = LM.circuit(ops, start, A, B, bl, dev.num_qubits, 0.05, 1.0)
            used = sorted({qc.find_bit(q).index for ins in qc.data for q in ins.qubits})
            pairs = {frozenset(qc.find_bit(q).index for q in ins.qubits) for ins in qc.data if len(ins.qubits) == 2}
            if pairs - cpl:
                status = f"bridges {br}: non-coupler pairs"
            elif bad & set(used) or badc & pairs:
                status = f"bridges {br}: touches failed {sorted(bad & set(used))}"
            else:
                placed = {}
                idx = {s: i for i, s in enumerate(G.sites(4, 2, 2))}
                for y, line in ((0, A), (1, B)):
                    for p in range(8):
                        placed[idx[(end[p] % 4, y, end[p] // 4)]] = line[p]
                se, be = H.placed_check(qc, placed, used, 4, 2, 2, log, 0.05)
                cz = Mi.cz_count(rc.pm.run(qc))
                status = f"bridges {br}: OK  t4 CZ {cz}  placed-exact {se:.1e}"
        print(f"r0 {r0} ({'even' if r0 % 2 == 0 else 'odd '}) c0 {c0}: {status}")
