"""Phase floor, synthetic noise (post hoc tool check, nothing judged): the floor circuit of s1_sim's 10-qubit P6 piece
(every non-diagonal one-qubit gate removed: CZ and RZ only; two CZ per edge per step, so every edge has an even CZ
count) between H layers: |+> in, X and Y read. Ideal values from the same circuit without noise. Per qubit:
contrast = |<X> + i<Y>| / |ideal|, phase error = arg(<X> + i<Y>) - arg(ideal). Variants: plain; echo-all (X on every
qubit at the middle step boundary: cancels Z detuning, keeps ZZ); echo-A (X on one side of the bipartition: cancels
ZZ on every edge and Z on side A). Same noise models and strengths as s1_sim (P2 0.004, readout 2 %, static ZZ and
detuning 0.02 rad per CZ slot, over-rotation 5 %, a stuck partner on label 23).
usage: python notes/phase_floor_2026-11-05/pf_sim.py OUT.json"""
import json, os, sys
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "s1_2026-11-05"))
import s1_sim as M  # noqa: E402

N = M.N
# bipartition of the piece by BFS colouring
adj = {q: set() for q in range(N)}
for a, b in M.EDGES:
    adj[a].add(b); adj[b].add(a)
col = {0: 0}
fr = [0]
while fr:
    x = fr.pop()
    for y in adj[x]:
        if y not in col:
            col[y] = 1 - col[x]; fr.append(y)
SIDE_A = [q for q in range(N) if col[q] == 0]
assert all(col[a] != col[b] for a, b in M.EDGES)


def circuit(m, t, echo, basis):
    qc = QuantumCircuit(N)
    qc.h(range(N))
    for s in range(1, t + 1):
        M.emit(qc, M.step_ops(0.0, m, floor=True), m)
        if s == t // 2 and echo:
            qc.x(range(N) if echo == "all" else SIDE_A)
    if basis == "y":
        qc.sdg(range(N))
    qc.h(range(N))
    M.save_z(qc, "r")
    return qc


def measure(m, t, echo):
    out = {}
    for b in ("x", "y"):
        d = M.run(circuit(m, t, echo, b), m)
        out[b] = np.array([d[f"r_{q}"] for q in range(N)]) * M.readout(m)
    return out["x"] + 1j * out["y"]


def main(path):
    models = ["dep", "static", "detune", "partner_dead", "over", "zzangle"]
    R = dict(side_A=[M.S[q] for q in SIDE_A], runs={})
    for echo in ("", "all", "A"):
        for t in (2, 4, 6):
            ideal = measure("none", t, echo)
            for m in models:
                z = measure(m, t, echo)
                contrast = np.abs(z) / np.abs(ideal)
                phase = np.angle(z / ideal)
                nb = [M.IDX[q] for q in (16, 22, 24)]
                rest = [q for q in range(N) if q not in nb and q != M.BAD]
                key = f"{echo or 'plain'} t{t} {m}"
                R["runs"][key] = dict(ideal_abs=np.abs(ideal).tolist(), contrast=contrast.tolist(), phase=phase.tolist())
                print(f"{key:24s} |ideal| {np.abs(ideal).min():.3f}-{np.abs(ideal).max():.3f}  contrast nb23 {contrast[nb].mean():.3f} "
                      f"rest {contrast[rest].mean():.3f}  |phase| nb23 {np.abs(phase[nb]).mean():.3f} rest {np.abs(phase[rest]).mean():.3f} rad", flush=True)
    json.dump(R, open(path, "w"))


if __name__ == "__main__":
    main(sys.argv[1])
