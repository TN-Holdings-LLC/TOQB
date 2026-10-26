"""How much signal each arm keeps on TOQB's noise models (report only; 2026-10-25, results/fold-holes-2026-10-25):

    python -m toqb.fold_lam OUT.jsonl [--n 9 10 ...] [--L 8 16] [--P 24] [--T 256] [--models sim dev]
                                      [--arms fold:template psfai:template_zip qiskit:2:target:template]
                                      [--max-active 22] [--models-seed 0 1 2 3]

For each (n, L): one random model of TOQB's ring classifier and P random inputs (seeded by n and L, the same for every
arm); each arm compiles them for `snapshot:marrakesh`; <Z> of clbit 0 on the twin ("sim") and the stand-in ("dev")
with T trajectories; least-squares z ~ lam z_noiseless + delta against the noiseless model (statevector), the
correlation, the two-qubit count, the scheduled duration and the active qubits. An arm whose circuit has more than
--max-active active qubits is recorded as skipped (the trajectory state would not fit). One JSON line per (n, L, arm,
model), appended as it is done; the output file must not exist.

--models-seed (2026-10-26): the random models per (n, L); model 0 is seeded by 1000 n + L as before (flow D and E),
model s > 0 by 1000 n + L + 100000 s. Rows carry "mseed".
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np


def active(c):
    return len({c.find_bit(q).index for i in c.data for q in i.qubits if i.operation.name not in ("barrier", "delay")})


def main(argv):
    argv = list(argv)
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 1
    out = argv.pop(0)
    if os.path.exists(out):
        print(f"STOP: {out} exists: an output is never overwritten", file=sys.stderr)
        return 2
    opts = {"--n": ["9", "10", "11"], "--L": ["8"], "--P": ["12"], "--T": ["128"], "--models": ["sim", "dev"],
            "--arms": ["fold:template", "psfai:template_zip", "qiskit:2:target:template"], "--max-active": ["22"], "--models-seed": ["0"]}
    key = None
    for a in argv:
        if a in opts:
            key, opts[a] = a, []
        else:
            opts[key].append(a)
    from qiskit.quantum_info import Statevector
    from toqb import s2r2 as S2
    from toqb import task_loop as TL
    ns, Ls = [int(v) for v in opts["--n"]], [int(v) for v in opts["--L"]]
    P, T, maxa = int(opts["--P"][0]), int(opts["--T"][0]), int(opts["--max-active"][0])
    for n, L, ms in [(n, L, ms) for n in ns for L in Ls for ms in [int(v) for v in opts["--models-seed"]]]:
        if True:
            rng = np.random.default_rng(1000 * n + L + 100000 * ms)
            theta = rng.uniform(-1, 1, TL.n_params(n, L))
            X = rng.uniform(-1, 1, (P, n))
            zl = []
            for x in X:
                q = TL.model_circuit(TL.angle_list(theta, x, n, L, np.pi / 2), n, L).remove_final_measurements(
                    inplace=False)
                zl.append(1 - 2 * Statevector(q).probabilities([0])[1])
            zl = np.array(zl)
            task = dict(n=n, layers=L, enc=float(np.pi / 2))
            for arm in opts["--arms"]:
                plan = dict(name="fold-lam", device="snapshot:marrakesh", verify=False, task=task,
                            predict=dict(traj=T, seed=1), standin=dict(t12=0.3, over=0.01, zz_hz=1e4, seed=20261017))
                base = dict(n=n, L=L, arm=arm, P=P, T=T)
                if ms:
                    base["mseed"] = ms
                try:
                    t0 = time.time()
                    R = S2.Runner(plan, arm)
                    cs = [R.compile(theta, x) for x in X]
                    d, q2 = R.arm.duration(cs[0], (n, L))
                    base.update(q2=int(q2), us=round(d * 1e6, 3), active=active(cs[0]), version=R.arm.version())
                    if base["active"] > maxa:
                        rows = [dict(base, model=m, skipped=f"{base['active']} active qubits > {maxa}")
                                for m in opts["--models"]]
                    else:
                        rows = []
                        for m in opts["--models"]:
                            t1 = time.time()
                            z = R.z(m, cs, T, 7)
                            lam, delta = np.polyfit(zl, z, 1)
                            rows.append(dict(base, model=m, lam=round(float(lam), 5), delta=round(float(delta), 5),
                                             corr=round(float(np.corrcoef(zl, z)[0, 1]), 5),
                                             rms=round(float(np.sqrt(np.mean((z - lam * zl - delta) ** 2))), 5),
                                             s=round(time.time() - t1, 1)))
                except Exception as exc:  # recorded, not hidden
                    rows = [dict(base, error=f"{type(exc).__name__}: {exc}"[:300])]
                with open(out, "a", encoding="utf-8") as f:
                    for r in rows:
                        f.write(json.dumps(r) + "\n")
                        print(json.dumps(r), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
