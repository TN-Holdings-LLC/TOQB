"""The kept signal at depth by Clifford eigenstate circuits (2026-10-28; the workplace's option 1 of
deep_lambda_design_and_relatedwork_review_2026-10-28):

    python -m toqb.clifford_lam OUT.jsonl --n 20 --L 8 16 50 100 [--P 24] [--T 256] [--seeds 0 1 2 3]
                                          [--arms fold:rule] [--device file:<target.pkl>] [--max-active 24]

Random classifiers lose their noiseless spread with depth (sd of the noiseless <Z> 0.17, 0.07, 0.005, 0.001 at
L = 10, 20, 50, 100 for n = 20), so the slope lam of `fold_lam` cannot be fitted at L >= 50. Here every rotation of
TOQB's ring classifier is a random multiple of pi/2, so the circuit U is a Clifford. The read-out Pauli Z_0 is carried
back through U by stabilizer algebra, P_in = U^dagger Z_0 U = s Q (s = +1 or -1, Q a Pauli string), and the input is the
+1 eigenstate of Q, prepared by a fixed layer of RY(a_q) RZ(b_q) on every qubit (X: RY(pi/2); Y: RY(pi/2), RZ(pi/2);
Z or I: no rotation). The noiseless <Z_0> is then exactly s at every depth, and

    lam_C = mean over circuits of s * (noisy <Z_0>),     its standard error = sd / sqrt(P).

The prep layer has the same gates (RY, RZ on every qubit) in every circuit, so one compiled template serves all
circuits of an (n, L). Each row: one (n, L, arm, seed) with P circuits and T trajectories on the twin ("sim").
The output file must not exist.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np


def clifford_case(n, L, rng):
    """(angles of the prep layer and the model in circuit order, s): a random Clifford classifier and its sign."""
    from qiskit.quantum_info import Clifford, Pauli
    from toqb import task_loop as TL
    na = 3 * n * L + n
    ang = list(rng.integers(0, 4, na) * (np.pi / 2))
    u = TL.model_circuit(ang, n, L).remove_final_measurements(inplace=False)
    p = Pauli("I" * (n - 1) + "Z").evolve(Clifford(u))  # U^dagger Z_0 U
    lab = p.to_label()
    if lab.startswith("i") or lab.startswith("-i"):
        raise RuntimeError("clifford_lam: a non-Hermitian Pauli (should not happen)")
    s = -1 if lab.startswith("-") else 1
    prep = []
    for q in range(n):
        x, z = bool(p.x[q]), bool(p.z[q])
        if x and z:      # Y
            prep += [np.pi / 2, np.pi / 2]
        elif x:          # X
            prep += [np.pi / 2, 0.0]
        else:            # Z or I
            prep += [0.0, 0.0]
    return prep, ang, s


def circuit(prep, ang, n, L):
    """The prep layer (RY, RZ on every qubit) followed by TOQB's ring classifier with angles `ang`, measured."""
    from qiskit import QuantumCircuit
    from toqb import task_loop as TL
    body = TL.model_circuit(ang, n, L)
    qc = QuantumCircuit(n, body.num_clbits)
    for q in range(n):
        qc.ry(prep[2 * q], q)
        qc.rz(prep[2 * q + 1], q)
    qc.compose(body, inplace=True)
    return qc


def main(argv):
    argv = list(argv)
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 1
    out = argv.pop(0)
    if os.path.exists(out):
        print(f"STOP: {out} exists: an output is never overwritten", file=sys.stderr)
        return 2
    opts = {"--n": ["20"], "--L": ["8"], "--P": ["24"], "--T": ["256"], "--seeds": ["0"], "--arms": ["fold:rule"],
            "--device": ["snapshot:marrakesh"], "--max-active": ["24"]}
    key = None
    for a in argv:
        if a in opts:
            key, opts[a] = a, []
        else:
            opts[key].append(a)
    from toqb import s2r2 as S2
    from toqb.fold_lam import active
    P, T, maxa = int(opts["--P"][0]), int(opts["--T"][0]), int(opts["--max-active"][0])
    for n in [int(v) for v in opts["--n"]]:
        for L in [int(v) for v in opts["--L"]]:
            for sd in [int(v) for v in opts["--seeds"]]:
                rng = np.random.default_rng(7_000_000 + 1000 * n + L + 100000 * sd)
                cases = [clifford_case(n, L, rng) for _ in range(P)]
                for arm in opts["--arms"]:
                    base = dict(n=n, L=L, arm=arm, P=P, T=T, seed=sd, kind="clifford")
                    if opts["--device"][0] != "snapshot:marrakesh":
                        base["device"] = opts["--device"][0].split("/")[-1]
                    plan = dict(name="clifford-lam", device=opts["--device"][0], verify=False,
                                task=dict(n=n, layers=L, enc=float(np.pi / 2)),
                                predict=dict(traj=T, seed=1), standin=dict(t12=0.3, over=0.01, zz_hz=1e4,
                                                                           seed=20261017))
                    try:
                        R = S2.Runner(plan, arm)
                        cs = [R.arm.compile(circuit(pr, an, n, L)) for pr, an, _ in cases]
                        d, q2 = R.arm.duration(cs[0], (n, L))
                        base.update(q2=int(q2), us=round(d * 1e6, 3), active=active(cs[0]), version=R.arm.version())
                        if base["active"] > maxa:
                            row = dict(base, skipped=f"{base['active']} active qubits > {maxa}")
                        else:
                            t1 = time.time()
                            z = np.asarray(R.z("sim", cs, T, 7), dtype=float)
                            v = z * np.array([s for _, _, s in cases], dtype=float)
                            row = dict(base, lam_c=round(float(v.mean()), 5),
                                       se=round(float(v.std(ddof=1) / np.sqrt(P)), 5),
                                       lo=round(float(v.min()), 4), hi=round(float(v.max()), 4),
                                       s=round(time.time() - t1, 1))
                    except Exception as exc:  # recorded, not hidden
                        row = dict(base, error=f"{type(exc).__name__}: {exc}"[:300])
                    with open(out, "a", encoding="utf-8") as f:
                        f.write(json.dumps(row) + "\n")
                    print(json.dumps(row), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
