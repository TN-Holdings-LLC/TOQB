"""Noise comparison of the zipper against item 31 on Aer's device noise model (NoiseModel.from_backend: per-gate
depolarizing plus thermal relaxation, and relaxation on the idle delays after ALAP scheduling with the Target's
durations). Report only: nothing is chosen from it. Readout error is left out (no measurement in the simulation),
the same for both. Per case: the state fidelity of the 10 active qubits before measurement, and the readout qubit's
<Z> (noisy / ideal = the damping the classifier sees)."""
import importlib.util
import json
import sys
import time

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix, Statevector, partial_trace
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDelay
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

spec = importlib.util.spec_from_file_location("ai", sys.argv[1])
ai = importlib.util.module_from_spec(spec)
sys.modules["ai"] = ai
spec.loader.exec_module(ai)
sys.path.insert(0, sys.argv[2])
import ring_zip as Z  # noqa: E402
from toqb import task_loop as TL  # noqa: E402
from qiskit_ibm_runtime import fake_provider as fp  # noqa: E402

DEV = sys.argv[4] if len(sys.argv) > 4 else "FakeMarrakesh"
backend = getattr(fp, DEV)()
t = backend.target
nm = NoiseModel.from_backend(backend)
sim = AerSimulator(method="density_matrix", noise_model=nm)
sched = PassManager([ALAPScheduleAnalysis(target=t), PadDelay(target=t)])


def ideal_part(c, layout):
    idx = {p: i for i, p in enumerate(layout)}
    out = QuantumCircuit(len(layout))
    ro = None
    for ins in c.data:
        qs = [c.find_bit(q).index for q in ins.qubits]
        if ins.operation.name == "measure":
            if c.find_bit(ins.clbits[0]).index == 0:
                ro = idx[qs[0]]
            continue
        out.append(ins.operation, [idx[q] for q in qs])
    return Statevector.from_instruction(out), ro


def zexp(rho, k, n):
    keep = [k]
    r = partial_trace(rho, [q for q in range(n) if q not in keep])
    return float(np.real(r.data[0, 0] - r.data[1, 1]))


rows = []
t0 = time.time()
for L in (8, 16):
    for seed in range(int(sys.argv[5]) if len(sys.argv) > 5 else 6):
        n = 10
        rng = np.random.default_rng(5000 + 100 * L + seed)
        th = rng.uniform(-np.pi, np.pi, TL.n_params(n, L))
        x = rng.uniform(-1, 1, n)
        qc = TL.model_circuit(TL.angle_list(th, x, n, L, 1.5707963267948966), n, L)
        row = dict(L=L, seed=seed)
        for name, fn in (("q4", ai.ring_rounds_q4), ("zip", Z.ring_rounds_zip)):
            tp = ai._ring_template_one(qc, t, rounds_fn=fn)
            c = tp.bind(qc)
            psi, ro = ideal_part(c, tp.layout)
            s = sched.run(c)
            s.remove_final_measurements()
            s.save_density_matrix(qubits=list(tp.layout))
            rho = DensityMatrix(sim.run(s, shots=1).result().data(0)["density_matrix"])
            fid = float(np.real(psi.data.conj() @ rho.data @ psi.data))
            zi = zexp(DensityMatrix(psi), ro, n)
            zn = zexp(rho, ro, n)
            row[name] = dict(fidelity=fid, z_ideal=zi, z_noisy=zn,
                             cz=sum(1 for i in c.data if i.operation.name == "cz"))
        rows.append(row)
        print(L, seed, {k: (round(row[k]["fidelity"], 4), round(row[k]["z_ideal"], 3), round(row[k]["z_noisy"], 3))
                        for k in ("q4", "zip")}, round(time.time() - t0), "s", flush=True)
json.dump(dict(device=DEV, rows=rows), open(sys.argv[3], "w"), indent=1)
for L in (8, 16):
    r = [x for x in rows if x["L"] == L]
    fq = np.array([x["q4"]["fidelity"] for x in r]); fz = np.array([x["zip"]["fidelity"] for x in r])
    # damping: regression of noisy <Z> on ideal <Z> through 0 (lam), per schedule
    zi = np.array([x["q4"]["z_ideal"] for x in r])
    lq = np.dot(zi, [x["q4"]["z_noisy"] for x in r]) / np.dot(zi, zi)
    lz = np.dot(zi, [x["zip"]["z_noisy"] for x in r]) / np.dot(zi, zi)
    print(f"{DEV} L {L}: fidelity q4 {fq.mean():.4f} (range {fq.min():.4f}-{fq.max():.4f}) zip {fz.mean():.4f} "
          f"({fz.min():.4f}-{fz.max():.4f}); zip better in {int((fz > fq).sum())}/{len(r)}; "
          f"readout damping lam q4 {lq:.3f} zip {lz:.3f}")
