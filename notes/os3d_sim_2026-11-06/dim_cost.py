"""The price of the third dimension in a simulator (owner 2026-11-06 13:52 CET; not declared, not a device result):
16 sites, the same step (RZZ(-pi/2) on every lattice edge, then RX(0.8)), t = 1, 2, 3, placed by psf-os and compiled
for the marrakesh record of 11-06, under the uniform model of sim3d.py (p2 0.005, p1 0.0002, readout 0.015).

  3D: 4 x 2 x 2 cubic lattice (28 edges), grid3d v3 fold.
  2D: a 16-site patch of the device's own heavy-hex lattice (one hexagon of 12 plus two tails of 2; 16 edges), written
      as a user circuit on labels and placed by psf-os run2d (translation only).

usage: python dim_cost.py PSF_OS DEVICE_RECORD OUT.json
"""
import json
import os
import sys
import tempfile

import numpy as np

HEX = [3, 4, 5, 6, 7, 17, 27, 26, 25, 24, 23, 16]      # hexagon: row 0 cols 3-7, bridge 17, row 1 cols 7-3, bridge 16
TAILS = [(7, 8), (8, 9), (27, 28), (28, 29)]


def patch():
    sites = HEX + [8, 9, 28, 29]
    edges = [(HEX[i], HEX[(i + 1) % 12]) for i in range(12)] + TAILS
    return sites, edges


def circuit2d(t, theta):
    from qiskit import QuantumCircuit
    sites, edges = patch()
    qc = QuantumCircuit(max(sites) + 1)
    for _ in range(t):
        for a, b in edges:
            qc.rzz(-np.pi / 2, a, b)
        for q in sites:
            qc.rx(theta, q)
    return qc, sites


def exact2d(t, theta):
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    sites, edges = patch()
    idx = {q: i for i, q in enumerate(sites)}
    qc = QuantumCircuit(16)
    for _ in range(t):
        for a, b in edges:
            qc.rzz(-np.pi / 2, idx[a], idx[b])
        for q in sites:
            qc.rx(theta, idx[q])
    p = Statevector(qc).probabilities()
    k = np.arange(len(p))
    z = {q: float(np.sum(p * (1 - 2 * ((k >> idx[q]) & 1)))) for q in sites}
    return np.array([z[q] for q in sorted(sites)])   # run2d measures the labels in sorted order (clbit k = k-th label)


def main():
    psf, devdir, out = sys.argv[1:4]
    sys.path.insert(0, psf)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import sim3d as S
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    from psf_os import device as Dv
    from psf_os import grid3d as G
    from psf_os import mirror2d as Mi
    from psf_os import user2d as U
    from psf_os.compile import RuleCompiler
    dev = Dv.Device.load(devdir)
    rc = RuleCompiler(dev)
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(0.005, 2), ["cz"])
    nm.add_all_qubit_quantum_error(depolarizing_error(0.0002, 1), ["sx", "x"])
    sim = AerSimulator(noise_model=nm, method="statevector", seed_simulator=11)
    rows = []
    for t in (1, 2, 3):
        pr = G.prepare(dev, 4, 2, 2, t, 0.8, layout="fold", rc=rc)
        ex3 = G.exact(4, 2, 2, t, 0.8)
        z3, _ = S.z_per_site(sim, pr["cu"], 16, 400, 0.015)
        r3 = S.score(z3, [ex3[str(s)] for s in range(16)])
        qc2, sites = circuit2d(t, 0.8)
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "P2D.qpy")
            with open(f, "wb") as fh:
                qpy.dump(qc2, fh)
            U.build_batch(dev, [("P2D", U.load(f))], os.path.join(d, "run"), shots=4000, max_seconds=10 ** 6)
            cu2 = qpy.load(open(os.path.join(d, "run", "runs", "p2d_P2D.qpy"), "rb"))[0]
            rep2 = json.load(open(os.path.join(d, "run", "report.json")))
        # the record's labels are the patch's sites in order; clbit k measures sites[k] (translated)
        z2, _ = S.z_per_site(sim, cu2, 16, 400, 0.015)
        r2 = S.score(z2, exact2d(t, 0.8))
        for name, c, r in (("3D 4x2x2 v3", pr["cu"], r3), ("2D hex patch", cu2, r2)):
            r.update(dim=name, t=t, cz=Mi.cz_count(c), cz_layers=c.depth(lambda i: len(i.qubits) == 2))
            r["decay_per_layer"] = (-np.log(r["retention"]) / r["cz_layers"]) if r["retention"] and r["retention"] > 0 else None
            rows.append(r)
            print(f"t{t} {name:13} CZ {r['cz']:4} layers {r['cz_layers']:3}  M {r['M']:+.3f}/{r['M_exact']:+.3f}  "
                  f"retention {r['retention'] if r['retention'] is None else round(r['retention'], 3)}  MSE {r['mse']:.4f}"
                  f"  msq {r['msq']:.3f}", flush=True)
    json.dump(rows, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
