"""Balanced line (ising_line_bal) on the fez record of 2026-11-10 at the judged 4 x 3 x 2 place (r0 0, c0 0):
bridge traffic, CZ (RuleCompiler), duration/idle, and the noiseless check against grid3d.exact (28 qubits, t 1, 2)."""
import sys
from collections import Counter
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli
from qiskit_aer import AerSimulator
from psf_os import device as Dv, grid3d as G
from psf_os.compile import RuleCompiler
import ising_line_bal as IB
sys.path.insert(0, "/mnt/c/Users/Administrator/Desktop/psf_zero_project/ising_line_2026-11-08")
import ising_line as IL
dev = Dv.Device.load(sys.argv[1]); rc = RuleCompiler(dev)
for mod, lab in ((IL, "first-visit"), (IB, "balanced")):
    p = mod.prepare_line(dev, 4, 3, 2, 4, 0.6, rc=rc)
    cz = Counter(tuple(sorted(p["cu"].find_bit(q).index for q in i.qubits)) for i in p["cu"].data if i.operation.name == "cz")
    br = Counter()
    for (a, b), n in cz.items():
        for x in (a, b):
            if 16 <= x <= 19 or 36 <= x <= 39:
                br[x] += n
    print(f"{lab}: where {p['where']['r0'], p['where']['c0']} CZ t4 {p['cz']} layers {p['cz_layers']} bridge CZ {dict(sorted(br.items()))} accept {all(p['checks'].values())}")
for t in (1, 2):
    qc, placed, used = IB.physical_line(dev, 4, 3, 2, t, 0.6)
    m = {u: i for i, u in enumerate(used)}
    small = QuantumCircuit(len(used))
    for ins in qc.data:
        small.append(ins.operation, [m[qc.find_bit(q).index] for q in ins.qubits])
    for u in used:
        small.save_expectation_value(Pauli("Z"), [m[u]], label=f"q{u}")
    d = AerSimulator(method="statevector").run(small, shots=1).result().data()
    ex = G.exact(4, 3, 2, t, 0.6)
    err = max(abs(float(np.real(d[f"q{placed[s]}"])) - ex[str(s)]) for s in placed)
    print(f"balanced 4x3x2 t {t}: max|placed - exact| {err:.1e}", flush=True)
