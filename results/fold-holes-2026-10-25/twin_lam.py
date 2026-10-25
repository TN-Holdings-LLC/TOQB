"""Twin scale (lam) and offset of each arm against the noiseless model: z_twin ~ lam z_noiseless + delta, on random
inputs of one random model (analysis, 2026-10-25)."""
import sys, json, time
import numpy as np
from toqb import s2r2 as S2, task_loop as TL
from toqb.devices import get_device
from qiskit.quantum_info import Statevector

ns = [int(v) for v in sys.argv[1].split(',')]; L = int(sys.argv[2]); P = int(sys.argv[3]); T = int(sys.argv[4])
arms = sys.argv[5].split(',')
rows = []
for n in ns:
    rng = np.random.default_rng(1000 + n)
    theta = rng.uniform(-1, 1, TL.n_params(n, L))
    X = rng.uniform(-1, 1, (P, n))
    task = dict(n=n, layers=L, enc=float(np.pi / 2))
    zl = []
    for x in X:
        qc = TL.model_circuit(TL.angle_list(theta, x, n, L, np.pi / 2), n, L)
        q = qc.remove_final_measurements(inplace=False)
        zl.append(1 - 2 * Statevector(q).probabilities([0])[1])
    zl = np.array(zl)
    for arm in arms:
        plan = dict(name="twin-lam", device="snapshot:marrakesh", verify=False, task=task,
                    predict=dict(traj=T, seed=1), standin=dict(t12=0.3, over=0.01, zz_hz=1e4, seed=20261017))
        t0 = time.time()
        try:
            R = S2.Runner(plan, arm)
            cs = [R.compile(theta, x) for x in X]
            z = R.z("sim", cs, T, 7)
            lam, delta = np.polyfit(zl, z, 1)
            d, q2 = R.arm.duration(cs[0], (n, L))
            row = dict(n=n, L=L, arm=arm, lam=round(float(lam), 4), delta=round(float(delta), 4),
                       corr=round(float(np.corrcoef(zl, z)[0, 1]), 4), q2=int(q2), us=round(d * 1e6, 2),
                       s=round(time.time() - t0, 1))
        except Exception as e:
            row = dict(n=n, L=L, arm=arm, error=f"{type(e).__name__}: {e}"[:200])
        rows.append(row); print(json.dumps(row), flush=True)
