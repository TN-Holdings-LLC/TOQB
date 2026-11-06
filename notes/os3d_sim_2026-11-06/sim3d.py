"""Noisy simulation of the 3D prototype (psf_os.grid3d) against its first version (521ac5b) and a SABRE reference.

Not declared, not a device result. The noise models are stated here, not read from any device:
  uniform: 2-qubit depolarizing p2 on every CZ, 1-qubit depolarizing p1 on sx/x, symmetric readout error pr.
  fakefez: qiskit_ibm_runtime's FakeFez noise model (a public snapshot), as a second, less tidy model.
The placement still reads only the device record's coupling graph and failed marks.

usage: python sim3d.py PSF_OS_CHECKOUT DEVICE_RECORD OUT.json [--model uniform|fakefez] [--trajectories K]\nEach value is the mean over K noise trajectories of the exact <Z> (no shot noise; trajectory noise ~ 1/sqrt(K)).\nuniform: p2 = 0.005, p1 = 0.0002, pr = 0.015 (readout applied as the factor 1 - 2 pr).
"""
import argparse
import importlib.util
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load_v1():
    spec = importlib.util.spec_from_file_location("grid3d_v1", os.path.join(HERE, "grid3d_v1_521ac5b.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def noise(model, p2=0.005, p1=0.0002, pr=0.015):
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error
    if model == "fakefez":
        from qiskit_ibm_runtime.fake_provider import FakeFez
        return NoiseModel.from_backend(FakeFez())
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cz"])
    nm.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["sx", "x"])
    nm.add_all_qubit_readout_error(ReadoutError([[1 - pr, pr], [pr, 1 - pr]]))
    return nm


def fakefez_dead(limit=0.5):
    """The FakeFez snapshot's dead elements: couplers with CZ error >= limit, qubits with readout error >= limit."""
    from qiskit_ibm_runtime.fake_provider import FakeFez
    tg = FakeFez().target
    dead_c = {tuple(sorted(k)) for k, v in tg["cz"].items() if v is not None and v.error is not None and v.error >= limit}
    dead_q = {k[0] for k, v in tg["measure"].items() if v is not None and v.error is not None and v.error >= limit}
    return dead_c, dead_q


def compile_grid(dev, rc, qc, placed, n, exact_rzz):
    from qiskit import QuantumCircuit
    from psf_os import user2d as U
    from psf_os.compile import rzz_exact
    full = QuantumCircuit(dev.num_qubits)
    full.compose(qc, qubits=list(range(qc.num_qubits)), inplace=True)
    if exact_rzz:
        full = rzz_exact(full)
    return rc.pm.run(U.with_measure(full, [placed[s] for s in range(n)]))


def compile_sabre(dev, logical, seed=0):
    """SABRE layout and routing on the record's coupling graph without failed elements, RZZ(+-pi/2) then as one CZ
    (the same identity grid3d uses), basis cz/rz/sx/x."""
    from qiskit import transpile
    from qiskit.transpiler import CouplingMap
    from psf_os.compile import rzz_exact
    bad = set(dev.failed_qubits)
    badc = {frozenset(c) for c in dev.failed_couplers}
    edges = [(a, b) for a, b in dev.couplers if a not in bad and b not in bad and frozenset((a, b)) not in badc]
    cm = CouplingMap([list(e) for e in edges] + [[b, a] for a, b in edges])
    qc = logical.copy()
    qc.measure_all()
    routed = transpile(qc, coupling_map=cm, basis_gates=["rzz", "swap", "rx", "measure"],
                       optimization_level=1, layout_method="sabre", routing_method="sabre", seed_transpiler=seed)
    routed = rzz_exact(routed)
    return transpile(routed, coupling_map=cm, basis_gates=["cz", "rz", "sx", "x", "measure"],
                     optimization_level=1, routing_method="none", layout_method="trivial", seed_transpiler=seed)


def remap_noise(nm, touched):
    """The backend noise model restricted to the touched physical qubits and renumbered as compact() renumbers them
    (workplace fix, 2026-11-06: compact() renumbers qubits 0..k-1, so a per-qubit backend model must follow, or the
    errors of physical qubits 0..k-1, and no CZ error on pairs that are not couplers there, would be applied)."""
    from qiskit_aer.noise import NoiseModel
    m = {q: i for i, q in enumerate(touched)}
    d = nm.to_dict()
    keep = []
    for e in d["errors"]:
        gq = e.get("gate_qubits")
        if not gq:
            keep.append(e)
            continue
        new = [tuple(m[q] for q in g) for g in gq if all(q in m for q in g)]
        if new:
            e = dict(e, gate_qubits=new)
            keep.append(e)
    d["errors"] = [e for e in keep if e["type"] != "roerror"]
    return NoiseModel.from_dict(d)


def readout_maps(nm, touched):
    """{compact index: (p(1|0), p(0|1))} from the backend model's readout errors."""
    out = {}
    m = {q: i for i, q in enumerate(touched)}
    for e in nm.to_dict()["errors"]:
        if e["type"] == "roerror":
            for g in e["gate_qubits"]:
                if len(g) == 1 and g[0] in m:
                    P = e["probabilities"]
                    out[m[g[0]]] = (float(P[0][1]), float(P[1][0]))
    return out


def touched_of(c):
    return sorted({c.find_bit(q).index for ins in c.data if ins.operation.name not in ("barrier",) for q in ins.qubits})


def compact(c, n):
    """The compiled circuit on its touched qubits only, measurements replaced by saved <Z> of each site
    (clbit s = site s). Returns the circuit; the readout error is applied afterwards as the factor (1 - 2 pr)."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Pauli
    touched = sorted({c.find_bit(q).index for ins in c.data if ins.operation.name not in ("barrier",)
                      for q in ins.qubits})
    m = {q: i for i, q in enumerate(touched)}
    out = QuantumCircuit(len(touched))
    site_q = {}
    for ins in c.data:
        name = ins.operation.name
        qs = [m[c.find_bit(q).index] for q in ins.qubits]
        if name == "measure":
            site_q[c.find_bit(ins.clbits[0]).index] = qs[0]
        elif name != "barrier":
            out.append(ins.operation, qs)
    for s in range(n):
        out.save_expectation_value(Pauli("Z"), [site_q[s]], label=f"z{s}")
    return out


def z_per_site(sim, c, n, trajectories, pr, backend_nm=None, method="statevector"):
    """Mean over noise trajectories of the exact <Z> of each site (Aer statevector, one trajectory per shot).
    backend_nm (fakefez): remapped to the touched qubits; its readout errors applied per site exactly:
    <Z>_read = (1 - p10 - p01) <Z> + (p01 - p10), p10 = p(1|0), p01 = p(0|1)."""
    cc = compact(c, n)
    if backend_nm is None:
        d = sim.run(cc, shots=trajectories).result().data()
        return np.array([float(np.real(d[f"z{s}"])) for s in range(n)]) * (1 - 2 * pr), cc.num_qubits
    from qiskit_aer import AerSimulator
    touched = touched_of(c)
    nm = remap_noise(backend_nm, touched)
    ro = readout_maps(backend_nm, touched)
    d = AerSimulator(noise_model=nm, method=method, seed_simulator=11).run(cc, shots=trajectories).result().data()
    site_q = {}
    for ins in c.data:
        if ins.operation.name == "measure":
            site_q[c.find_bit(ins.clbits[0]).index] = touched.index(c.find_bit(ins.qubits[0]).index)
    z = np.array([float(np.real(d[f"z{s}"])) for s in range(n)])
    for s in range(n):
        p10, p01 = ro.get(site_q[s], (0.0, 0.0))
        z[s] = (1 - p10 - p01) * z[s] + (p01 - p10)
    return z, cc.num_qubits


def score(z, ex):
    ex = np.array(ex)
    M, Mx = float(z.mean()), float(ex.mean())
    mse, msq = float(np.mean((z - ex) ** 2)), float(np.mean(ex ** 2))
    trivial = min(float(np.mean((1 - ex) ** 2)), float(np.mean((-1 - ex) ** 2)))  # all 0 (Z = +1) or all 1
    return dict(M=M, M_exact=Mx, retention=M / Mx if abs(Mx) >= 0.1 else None, mse=mse, msq=msq,
                reads=mse <= msq / 2, agrees=abs(M - Mx) <= 0.05, mse_trivial=trivial, beats=mse < trivial)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("psf_os")
    ap.add_argument("device")
    ap.add_argument("out")
    ap.add_argument("--model", default="uniform")
    ap.add_argument("--trajectories", type=int, default=300)
    ap.add_argument("--sizes", default="4x2x2")
    ap.add_argument("--ts", default="1,2,3")
    ap.add_argument("--method", default="statevector")
    ap.add_argument("--variants", default="v1,v2,v3,sabre", help="which of v1, v2, v3, sabre to run")
    ap.add_argument("--mark-fakefez-dead", action="store_true",
                    help="add the FakeFez snapshot's dead elements (CZ error >= 0.5, readout error >= 0.5) to the "
                         "record's failed marks before placing both arms (rule fixed 2026-11-06 06:06 CET, before "
                         "this run)")
    a = ap.parse_args()
    want = set(a.variants.split(","))
    sys.path.insert(0, a.psf_os)
    from qiskit_aer import AerSimulator
    from psf_os import device as Dv
    from psf_os import grid3d as G2
    from psf_os import mirror2d as Mi
    from psf_os.compile import RuleCompiler
    dev = Dv.Device.load(a.device)
    if a.mark_fakefez_dead:
        dead_c, dead_q = fakefez_dead()
        dev.failed_couplers = [list(e) for e in sorted({tuple(sorted(e)) for e in dev.failed_couplers} | dead_c)]
        dev.failed_qubits = sorted(set(dev.failed_qubits) | dead_q)
        print(f"marked from FakeFez: couplers {sorted(dead_c)}, qubits {sorted(dead_q)}", flush=True)
    rc = RuleCompiler(dev)
    G1 = load_v1()
    nm = noise(a.model)
    pr = 0.015 if a.model == "uniform" else 0.0
    if a.model == "uniform":  # readout as a factor; the gate noise stays in the model
        from qiskit_aer.noise import NoiseModel, depolarizing_error
        nm = NoiseModel()
        nm.add_all_qubit_quantum_error(depolarizing_error(0.005, 2), ["cz"])
        nm.add_all_qubit_quantum_error(depolarizing_error(0.0002, 1), ["sx", "x"])
    sim = AerSimulator(noise_model=nm, method=a.method, seed_simulator=11)
    rows = []
    for size in a.sizes.split(","):
        L, M, N = (int(v) for v in size.split("x"))
        n = L * M * N
        for t in (int(v) for v in a.ts.split(",")):
            ex = G2.exact(L, M, N, t, 0.8)
            ex = [ex[str(s)] for s in range(n)]
            variants = {}
            if "v1" in want:
                qc, placed, used, _ = G1.physical(dev, L, M, N, t, 0.8)
                variants["v1 (521ac5b)"] = compile_grid(dev, rc, qc, placed, n, False)
            if "v2" in want:
                qc, placed, used, _ = G2.physical(dev, L, M, N, t, 0.8, layout="rows")
                variants["v2 rows"] = compile_grid(dev, rc, qc, placed, n, True)
            if L == 4 and "v3" in want:
                qc, placed, used, _ = G2.physical(dev, L, M, N, t, 0.8, layout="fold")
                variants["v3 fold"] = compile_grid(dev, rc, qc, placed, n, True)
            if "sabre" in want:
                variants["SABRE"] = compile_sabre(dev, G2.logical(L, M, N, t, 0.8))
            for name, c in variants.items():
                t0 = time.time()
                z, nq = z_per_site(sim, c, n, a.trajectories, pr,
                                   backend_nm=nm if a.model == "fakefez" else None, method=a.method)
                r = score(z, ex)
                r.update(size=size, t=t, variant=name, model=a.model, cz=Mi.cz_count(c),
                         cz_layers=c.depth(lambda i: len(i.qubits) == 2), qubits=nq, seconds=round(time.time() - t0, 1))
                rows.append(r)
                print(f"{size} t{t} {name:13} q {nq:3} cz {r['cz']:5} layers {r['cz_layers']:4}  M {r['M']:+.3f} / "
                      f"{r['M_exact']:+.3f}  retention {r['retention'] if r['retention'] is None else round(r['retention'], 3)}"
                      f"  mse {r['mse']:.4f} (msq/2 {r['msq'] / 2:.4f})  reads {r['reads']}  agrees {r['agrees']}", flush=True)
    json.dump(rows, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
