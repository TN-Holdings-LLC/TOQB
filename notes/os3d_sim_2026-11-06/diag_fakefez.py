"""Why does an arm do badly under the FakeFez model? Lists, per arm, the touched qubits and pairs whose FakeFez
snapshot errors are large (workplace, 2026-11-06; not declared). The FakeFez snapshot is a public, older calibration;
its bad qubits are not the failed marks of the 11-05 record that both placements read.

usage: python diag_fakefez.py PSF_OS_CHECKOUT DEVICE_RECORD T
"""
import sys

import sim3d

sys.path.insert(0, sys.argv[1])
from psf_os import device as Dv  # noqa: E402
from psf_os import grid3d as G  # noqa: E402
from psf_os.compile import RuleCompiler  # noqa: E402
from qiskit_ibm_runtime.fake_provider import FakeFez  # noqa: E402

dev = Dv.Device.load(sys.argv[2])
t = int(sys.argv[3])
be = FakeFez()
props = be.target
ro = {q: props["measure"][(q,)].error for q in range(be.num_qubits) if props["measure"].get((q,)) is not None}
cz = {frozenset(k): v.error for k, v in props["cz"].items() if v is not None and v.error is not None}
qc, placed, used, _ = G.physical(dev, 4, 2, 2, t, 0.8, layout="fold")
arms = {"v3 fold": sim3d.compile_grid(dev, RuleCompiler(dev), qc, placed, 16, True),
        "SABRE": sim3d.compile_sabre(dev, G.logical(4, 2, 2, t, 0.8))}
for name, c in arms.items():
    touched = sim3d.touched_of(c)
    pairs = {}
    for ins in c.data:
        if ins.operation.name == "cz":
            p = frozenset(c.find_bit(q).index for q in ins.qubits)
            pairs[p] = pairs.get(p, 0) + 1
    meas = {c.find_bit(ins.clbits[0]).index: c.find_bit(ins.qubits[0]).index for ins in c.data
            if ins.operation.name == "measure"}
    exp_loss = sum(n * cz.get(p, 0) for p, n in pairs.items())
    print(f"{name} t{t}: {len(touched)} qubits, {sum(pairs.values())} CZ on {len(pairs)} pairs, "
          f"sum of FakeFez CZ errors {exp_loss:.3f}, mean readout error of read qubits "
          f"{sum(ro.get(q, 0) for q in meas.values()) / len(meas):.4f}")
    for p, n in sorted(pairs.items(), key=lambda kv: -cz.get(kv[0], 0))[:4]:
        print(f"   pair {sorted(p)} x{n}: FakeFez CZ error {cz.get(p, float('nan')):.4f}")
    for s, q in sorted(meas.items(), key=lambda kv: -ro.get(kv[1], 0))[:3]:
        print(f"   site {s} on qubit {q}: FakeFez readout error {ro.get(q, float('nan')):.4f}")
