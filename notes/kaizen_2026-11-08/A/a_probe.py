"""Probe: CZ of the line layout by psf-os's RuleCompiler pass manager (level 1) and by a level-3 pass manager on
the same map-free target; the abstract operation list around the step boundaries."""
import json, sys
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from psf_os import device as Dv
from psf_os.compile import RuleCompiler
from psf_os import mirror2d as Mi
import heis3d as H

dev = Dv.Device.load(sys.argv[1])
rc = RuleCompiler(dev)
pm3 = generate_preset_pass_manager(3, target=rc.target, initial_layout=list(range(dev.num_qubits)),
                                   routing_method="none", seed_transpiler=0)
for t in range(1, 5):
    qc, placed, used, log, where = H.physical_line(dev, t, 0.05)
    full = QuantumCircuit(dev.num_qubits); full.compose(qc, qubits=list(range(qc.num_qubits)), inplace=True)
    c1 = Mi.cz_count(rc.pm.run(full)); c3 = Mi.cz_count(pm3.run(full))
    print(f"t {t}: RuleCompiler {c1}  level3 {c3}  where {where}")
# abstract ops for t = 2 with the merge
br = tuple(where["bridges"])
A = list(range(8)); B = list(range(8, 16)); bl = {p: 16 + i for i, p in enumerate(br)}
out, start, end, log = H._line_build(A, B, bl, br, 2, 0.05, 1.0)
print("ops t=2:", out)

# CZ per qubit pair, level 1 vs level 3, t = 2
from collections import Counter
qc, placed, used, log, where = H.physical_line(dev, 2, 0.05)
full = QuantumCircuit(dev.num_qubits); full.compose(qc, qubits=list(range(qc.num_qubits)), inplace=True)
def pairs(c):
    return Counter(tuple(sorted(c.find_bit(q).index for q in i.qubits)) for i in c.data if i.operation.name == "cz")
p1, p3 = pairs(rc.pm.run(full)), pairs(pm3.run(full))
lines = {q: f"A{q - 20 * where['r0'] - where['c0']}" for q in range(20 * where['r0'] + where['c0'], 20 * where['r0'] + where['c0'] + 8)}
lines.update({q: f"B{q - 20 * (where['r0'] + 1) - where['c0']}" for q in range(20 * (where['r0'] + 1) + where['c0'], 20 * (where['r0'] + 1) + where['c0'] + 8)})
for k in sorted(set(p1) | set(p3)):
    if p1[k] != p3[k]:
        print("pair", [lines.get(q, f"q{q}") for q in k], "level1", p1[k], "level3", p3[k])
