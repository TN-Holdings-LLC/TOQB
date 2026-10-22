"""Prototype check of the zipper (ring_zip.py) against a22's ring template: exactness (logical circuit and the bound
device circuit, statevector up to global phase, read in clbit order) and cost (CZ, duration, CZ depth), on fake
Heron devices. Analysis script; nothing here chooses anything at compile time."""
import collections
import importlib.util
import json
import sys
import time

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

import psf_compile as pc

spec = importlib.util.spec_from_file_location("ai", sys.argv[1])
ai = importlib.util.module_from_spec(spec)
sys.modules["ai"] = ai
spec.loader.exec_module(ai)
sys.path.insert(0, sys.argv[2])
import ring_zip as Z  # noqa: E402
from toqb import task_loop as TL  # noqa: E402
from qiskit_ibm_runtime import fake_provider as fp  # noqa: E402


def state_by_clbit(circ, meas):
    """Statevector of `circ` (measures removed), qubits reordered so that qubit k is the one measured into clbit k."""
    c = QuantumCircuit(circ.num_qubits)
    for ins in circ.data:
        if ins.operation.name in ("measure", "barrier"):
            continue
        c.append(ins.operation, [circ.find_bit(q).index for q in ins.qubits])
    sv = Statevector.from_instruction(c)
    perm = [None] * len(meas)
    for q, cb in meas:
        perm[cb] = q
    return sv.data.reshape([2] * circ.num_qubits)[...].transpose(
        [circ.num_qubits - 1 - perm[circ.num_qubits - 1 - k] for k in range(circ.num_qubits)]).reshape(-1)


def phase_dist(a, b):
    k = int(np.argmax(abs(a)))
    ph = a[k] / b[k]
    return float(np.max(abs(a - ph * b)))


def device_part(c, layout):
    """The bound device circuit restricted to its layout qubits, renumbered 0..n-1, and its (qubit, clbit) map."""
    idx = {p: i for i, p in enumerate(layout)}
    out = QuantumCircuit(len(layout))
    meas = []
    for ins in c.data:
        qs = [c.find_bit(q).index for q in ins.qubits]
        if ins.operation.name == "measure":
            meas.append((idx[qs[0]], c.find_bit(ins.clbits[0]).index))
            continue
        if any(q not in idx for q in qs):
            raise RuntimeError("an operation off the layout")
        out.append(ins.operation, [idx[q] for q in qs])
    return out, meas


def cz_depth(c):
    d = collections.defaultdict(int)
    for ins in c.data:
        if ins.operation.name == "cz":
            a, b = (c.find_bit(q).index for q in ins.qubits)
            m = max(d[a], d[b]) + 1
            d[a] = d[b] = m
    return max(d.values()) if d else 0


rows = []
worst_logical = worst_device = 0.0
for dname in ("FakeMarrakesh", "FakeFez", "FakeKingston", "FakeTorino", "FakeAachen"):
    t = getattr(fp, dname)().target
    for L in (1, 2, 3, 8, 16):
        for seed in (1, 2):
            n = 10
            rng = np.random.default_rng(1000 * L + seed)
            th = rng.uniform(-np.pi, np.pi, TL.n_params(n, L))
            x = rng.uniform(-1, 1, n)
            qc = TL.model_circuit(TL.angle_list(th, x, n, L, 1.5707963267948966), n, L)
            meas_qc = [(qc.find_bit(i.qubits[0]).index, qc.find_bit(i.clbits[0]).index) for i in qc.data
                       if i.operation.name == "measure"]
            ref = state_by_clbit(qc, meas_qc)
            read = ai._ring_read(qc)
            logical, _ = ai._ring_logical(qc, read, Z.ring_rounds_zip)
            meas_lg = [(logical.find_bit(i.qubits[0]).index, logical.find_bit(i.clbits[0]).index)
                       for i in logical.data if i.operation.name == "measure"]
            dl = phase_dist(ref, state_by_clbit(logical, meas_lg))
            worst_logical = max(worst_logical, dl)
            row = dict(device=dname, L=L, seed=seed)
            for name, fn in (("q4", ai.ring_rounds_q4), ("zip", Z.ring_rounds_zip)):
                t0 = time.perf_counter()
                tp = ai._ring_template_one(qc, t, rounds_fn=fn)
                build = time.perf_counter() - t0
                c = tp.bind(qc)
                part, meas = device_part(c, tp.layout)
                dd = phase_dist(ref, state_by_clbit(part, meas))
                if name == "zip":
                    worst_device = max(worst_device, dd)
                row[name] = dict(cz=sum(1 for i in c.data if i.operation.name == "cz"), cz_depth=cz_depth(c),
                                 duration_us=round(pc._duration_s(c, t) * 1e6, 4), exact=dd, build_s=round(build, 3),
                                 layout=list(tp.layout))
            best, lab = Z.ring_template_z(ai, pc, qc, t)
            row["chosen"] = lab
            rows.append(row)
    print(dname, "done", flush=True)

summ = collections.defaultdict(list)
for r in rows:
    summ[r["L"]].append((r["q4"]["cz"], r["zip"]["cz"], r["q4"]["cz_depth"], r["zip"]["cz_depth"],
                         r["q4"]["duration_us"], r["zip"]["duration_us"]))
print("worst logical", worst_logical, "worst device (zip)", worst_device)
print("chosen", collections.Counter(r["chosen"] for r in rows))
for L in sorted(summ):
    a = np.array(summ[L])
    print(f"L {L:2d}: CZ q4 {a[:,0].min():.0f}-{a[:,0].max():.0f} zip {a[:,1].min():.0f}-{a[:,1].max():.0f}; "
          f"CZ depth q4 {a[:,2].min():.0f}-{a[:,2].max():.0f} zip {a[:,3].min():.0f}-{a[:,3].max():.0f}; "
          f"duration us q4 {a[:,4].min():.3f}-{a[:,4].max():.3f} zip {a[:,5].min():.3f}-{a[:,5].max():.3f}")
json.dump(rows, open(sys.argv[3], "w"), indent=1)
