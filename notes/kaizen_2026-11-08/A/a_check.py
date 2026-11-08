import sys
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from psf_os import device as Dv
from psf_os.compile import RuleCompiler
from psf_os import mirror2d as Mi
import heis3d as H
import line_merge as LM

dev = Dv.Device.load(sys.argv[1])
rc = RuleCompiler(dev)
pm3 = generate_preset_pass_manager(3, target=rc.target, initial_layout=list(range(dev.num_qubits)),
                                   routing_method="none", seed_transpiler=0)
print(f"device {dev.name}")
for t in range(1, 7):
    qc0, placed, used, log, where = H.physical_line(dev, t, 0.05)
    qc, placed2, used2, log2, where2, ops = LM.physical_line_merged(dev, t, 0.05)
    assert placed == placed2
    def full(c):
        f = QuantumCircuit(dev.num_qubits); f.compose(c, qubits=list(range(c.num_qubits)), inplace=True); return f
    n0 = Mi.cz_count(rc.pm.run(full(qc0))); n1 = Mi.cz_count(rc.pm.run(full(qc))); n3 = Mi.cz_count(pm3.run(full(qc0)))
    n13 = Mi.cz_count(pm3.run(full(qc)))
    used_now = sorted({qc.find_bit(q).index for ins in qc.data for q in ins.qubits})
    se, be = H.placed_check(qc, placed, used_now, 4, 2, 2, log, 0.05)
    merged = sum(1 for o in ops if o[0] == "L" and o[2] > 1)
    print(f"t {t}: line (bc38d2c) {n0}  + rule A {n1}  | level3 on bc38d2c {n3}, level3 on rule A {n13} |"
          f" merged blocks {merged}  placed-exact {se:.1e}  bridge {be:.1e}")
