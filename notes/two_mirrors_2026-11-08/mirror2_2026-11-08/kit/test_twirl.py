"""Without noise, a twirled circuit must give exactly the untwirled <Z> (the frames cancel): checked on the
Heisenberg t1 mirror and forward, a few frames, noiseless statevector."""
import json, sys
import numpy as np
from qiskit import QuantumCircuit, qpy
from qiskit_aer import AerSimulator
import expsim3 as X
import io

def unitary_only(ce):
    """drop the relaxation channels (they would sample one trajectory each run): the frames are checked on gates"""
    out = ce.copy_empty_like()
    for ins in ce.data:
        if ins.operation.name in ("cz", "sx", "x", "rz", "unitary", "rzz", "rx", "save_expval"):
            out.append(ins)
    return out


def zs(ce):
    ce = unitary_only(ce)
    sim = AerSimulator(method="statevector")
    d = sim.run(ce, shots=1).result().data()
    return np.array([np.real(d[k][0]) for k in sorted(d, key=lambda s: int(s[1:]))])

for key, name in (("heisB_mf", "p2d_h3d0_t1_mirror"), ("heisB", "p2d_h3d0_t1")):
    circs = qpy.load(open(f"inputs/{key}.qpy", "rb")); names = json.load(open(f"inputs/{key}_names.json"))
    b = io.BytesIO(); qpy.dump(circs[names.index(name)], b)
    X._STAGE1.clear()
    _, ce0, *_ = X._prepare(0, b.getvalue(), None)
    ref = zs(ce0)
    for seed in (1, 2, 3):
        X._STAGE1.clear()
        _, ce, *_ = X._prepare(0, b.getvalue(), None, twirl_seed=seed)
        print(f"{name}: frame {seed}: max |twirled - plain| = {np.abs(zs(ce) - ref).max():.1e}  (plain mean {ref.mean():.4f})")
