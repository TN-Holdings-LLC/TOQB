"""Desk probe (home, 2026-11-13): the Clifford twin of a compiled circuit = the same circuit with every RZ angle rounded
to the nearest multiple of pi/2 (CZ, SX, X unchanged). Its per-qubit <Z> is exact by stabilizer simulation at any size.
For each compiled user circuit given: CZ count equal (by construction), op set, and the twin's signal on the chain:
fraction of chain qubits with |<Z>| = 1, mean square of <Z>.
usage: python twin_probe.py RUNS_DIR TAG [TAG ...]   (reads p2d_TAG.qpy and p2d_TAG.json for the chain mapping)"""
import ast
import gzip
import json
import os
import sys

import numpy as np
from qiskit import QuantumCircuit, qpy


def load(path):
    if os.path.exists(path):
        return qpy.load(open(path, "rb"))[0]
    return qpy.load(gzip.open(path + ".gz", "rb"))[0]


def twin(c):
    out = QuantumCircuit(c.num_qubits, c.num_clbits)
    for ins in c.data:
        op = ins.operation
        if op.name == "rz":
            k = int(np.round(float(op.params[0]) / (np.pi / 2)))
            new = QuantumCircuit(1)
            new.rz(k * np.pi / 2, 0)
            out.append(new.data[0].operation, ins.qubits, ins.clbits)
        else:
            out.append(op, ins.qubits, ins.clbits)
    return out


def z_stab(c, phys):
    from qiskit.quantum_info import Clifford, StabilizerState, Pauli
    keep = sorted(set(phys))
    pos = {p: k for k, p in enumerate(keep)}
    r = QuantumCircuit(len(keep))
    for ins in c.data:
        if ins.operation.name in ("measure", "barrier", "delay"):
            continue
        qs = [c.find_bit(q).index for q in ins.qubits]
        if any(q not in pos for q in qs):
            raise SystemExit("gate outside the chain")
        r.append(ins.operation, [pos[q] for q in qs])
    st = StabilizerState(r)
    n = len(keep)
    zs = []
    for p in phys:
        lab = ["I"] * n
        lab[n - 1 - pos[p]] = "Z"
        zs.append(float(np.real(st.expectation_value(Pauli("".join(lab))))))
    return np.array(zs)


if __name__ == "__main__":
    runs = sys.argv[1]
    for tag in sys.argv[2:]:
        rec = json.load(open(os.path.join(runs, f"p2d_{tag}.json")))
        m = rec["mapping"] if isinstance(rec["mapping"], dict) else ast.literal_eval(rec["mapping"])
        c = load(os.path.join(runs, f"p2d_{tag}.qpy"))
        used = sorted({c.find_bit(q).index for ins in c.data if ins.operation.name == "cz" for q in ins.qubits})
        phys = [int(v) for v in m.values()] if len(m) else used
        phys = [p for p in phys if p in set(used)] or used
        t = twin(c)
        z = z_stab(t, phys)
        ops = dict(t.count_ops())
        print(f"{tag}: qubits {len(phys)} CZ {ops.get('cz')} | twin |Z|=1 on {np.mean(np.abs(z) > 0.999):.2f}, "
              f"mean square {np.mean(z ** 2):.3f}, Z=0 on {np.mean(np.abs(z) < 1e-9):.2f}", flush=True)
