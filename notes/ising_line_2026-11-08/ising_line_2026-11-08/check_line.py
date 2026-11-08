"""Checks of ising_line.py: CZ by psf-os's RuleCompiler (after rzz_exact) against the fold v3.1 / v3.2 (grid3d.prepare)
on the device records, and the noiseless <Z> against grid3d.exact (statevector; 4 x 3 x 2 uses Aer's statevector on the
28 touched qubits with saved <Z> only, to keep memory at about 4 GB).
usage: python check_line.py DEV_DIR [DEV_DIR ...] [--exact-dev DEV_DIR] [--theta 0.6]"""
import argparse
import numpy as np
from qiskit import QuantumCircuit
from psf_os import device as Dv, grid3d as G
from psf_os.compile import RuleCompiler
import ising_line as IL

ap = argparse.ArgumentParser()
ap.add_argument("devs", nargs="+")
ap.add_argument("--exact-dev", default=None)
ap.add_argument("--theta", type=float, default=0.6)
a = ap.parse_args()
th = a.theta


def placed_z(qc, placed, used):
    """<Z> of every placed site and of the other touched qubits (bridges), noiseless."""
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    m = {u: i for i, u in enumerate(used)}
    small = QuantumCircuit(len(used))
    for ins in qc.data:
        small.append(ins.operation, [m[qc.find_bit(q).index] for q in ins.qubits])
    for u in used:
        small.save_expectation_value(Pauli("Z"), [m[u]], label=f"q{u}")
    d = AerSimulator(method="statevector").run(small, shots=1).result().data()
    return {u: float(np.real(d[f"q{u}"])) for u in used}


print("== CZ per arm (RuleCompiler + rzz_exact); per step = difference t2 - t1")
for path in a.devs:
    dev = Dv.Device.load(path)
    rc = RuleCompiler(dev)
    for M in (2, 3):
        line = [IL.prepare_line(dev, 4, M, 2, t, th, rc=rc) for t in (1, 2, 3, 4)]
        w = line[0]["where"]
        fold = {}
        for merge, lab in ((True, "v3.1"), ("carry", "v3.2")):
            try:
                fold[lab] = [G.prepare(dev, 4, M, 2, t, th, layout="fold", rc=rc, merge=merge)["cz"] for t in (1, 2)]
            except Exception as e:
                fold[lab] = f"{type(e).__name__}"
        f = lambda v: f"{v[0]}/{v[1]} (step {v[1] - v[0]})" if isinstance(v, list) else v
        print(f"{dev.name} 4x{M}x2: line t1-4 {[p['cz'] for p in line]} (step {line[1]['cz'] - line[0]['cz']}; "
              f"r0 {w['r0']} c0 {w['c0']} bridges {w['bridges']} empty swaps/line {w['empty_swaps']}) | "
              f"fold v3.1 {f(fold['v3.1'])} | fold v3.2 {f(fold['v3.2'])} | floor/mirror accept: {line[0]['checks']}")
if a.exact_dev:
    dev = Dv.Device.load(a.exact_dev)
    print(f"== noiseless check on {dev.name} (theta {th})")
    for M, ts in ((2, (1, 2, 3, 4)), (3, (1, 2))):
        for t in ts:
            qc, placed, used = IL.physical_line(dev, 4, M, 2, t, th)
            z = placed_z(qc, placed, used)
            ex = G.exact(4, M, 2, t, th)
            err = max(abs(z[placed[s]] - ex[str(s)]) for s in placed)
            others = set(used) - set(placed.values())
            berr = max((1 - z[u] for u in others), default=0.0)
            print(f"4x{M}x2 t {t}: qubits {len(used)}  max|placed - exact| {err:.1e}  bridges back to |0>: {berr:.1e}",
                  flush=True)
