"""C baseline (Heisenberg): CZ of gpu/heis3d.py physical (old fold and carry), RuleCompiler, fez record, t = 1, 2;
and a combinatorial check of the 4xMx2 line schedule with two bridge sets (each bond once per step, every site on a
{1,5} and on a {3,7} position), with its per-step CZ by the op count (3 per bond block or swap, 7 per y-bond)."""
import sys
from qiskit import QuantumCircuit
from psf_os import device as Dv
from psf_os.compile import RuleCompiler
from psf_os import mirror2d as Mi
import heis3d as H
dev = Dv.Device.load(sys.argv[1]); rc = RuleCompiler(dev)
for (M, N) in ((2, 2), (3, 2), (2, 3)):
    row = []
    for carry in (False, True):
        try:
            c = []
            for t in (1, 2):
                qc, placed, used, log, where = H.physical(dev, M, N, t, 0.05, carry=carry)
                f = QuantumCircuit(dev.num_qubits); f.compose(qc, qubits=list(range(qc.num_qubits)), inplace=True)
                c.append(Mi.cz_count(rc.pm.run(f)))
            row.append(f"{'carry' if carry else 'old'}: t1 {c[0]} t2 {c[1]} (step {c[1] - c[0]})")
        except Exception as e:
            row.append(f"{carry}: {type(e).__name__} {str(e)[:60]}")
    print(f"Heisenberg 4x{M}x{N}: " + " | ".join(row), flush=True)
# combinatorial check of the 4xMx2 schedule
start = "2.0 3.1 1.1 2.1 3.0 0.0 1.0 0.1".split()
ops = "SU@2 SU@1 SU@0 SU@5 SU@6 SW@3 SU@2 SU@1 SU@4 SU@5 SW@2 SU@3".split()
arr = [int(s.split(".")[0]) + 4 * int(s.split(".")[1]) for s in start]
bonds = {frozenset((x + 4 * z, x + 1 + 4 * z)) for z in (0, 1) for x in range(3)} | {frozenset((x, x + 4)) for x in range(4)}
for step in range(2):
    seq = ops if step == 0 else list(reversed(ops))
    done, v15, v37 = [], set(), set()
    def visit():
        v15.update(arr[p] for p in (1, 5)); v37.update(arr[p] for p in (3, 7))
    visit()
    for o in seq:
        k, e = o.split("@"); e = int(e)
        pair = frozenset((arr[e], arr[e + 1]))
        if k in ("SU", "U"):
            assert pair in bonds, (o, pair); done.append(pair)
        if k != "U":
            arr[e], arr[e + 1] = arr[e + 1], arr[e]
        visit()
    assert sorted(map(sorted, done)) == sorted(map(sorted, bonds)) and len(done) == 10, done
    assert len(v15) == 8 and len(v37) == 8
print("4xMx2 line schedule: each of the 10 line bonds once per step, every site on {1,5} and on {3,7}: OK (2 steps)")
for M in (3, 4):
    lines, ypairs = M, M - 1
    heis = lines * (10 * 3 + 2 * 3) + ypairs * 8 * 7
    ising = lines * (10 * 2 + 2 * 3) + ypairs * 8 * 3
    print(f"4x{M}x2 line, per step by op count (no boundary merge): Heisenberg {heis} CZ, Ising {ising} CZ")
