"""Times the trajectory engine (`toqb.traj`) on S2R's classifier at larger sizes, both compilers, both noise models.

    TOQB_XP=cupy python -m toqb.bench_traj [n] [L ...]      (from the TOQB root; default n = 10, L = 8 16 24)

Per compiler and depth: the compiled circuit's active qubits, duration and two-qubit count; the time of one batch of
P = 50 circuits of one structure (different angles) x T = 256 trajectories in the simulator's model, and of 2 circuits x
200 shots on the stand-in; the program's steps. Prints one line each.
"""
import os
import sys
import time

import numpy as np

from toqb import s2r as S
from toqb import task_loop as TL
from toqb import traj as TJ


def main(argv):
    n = int(argv[0]) if argv else 10
    Ls = [int(a) for a in argv[1:]] or [8, 16, 24]
    from toqb.devices import get_device
    from toqb.fast_noise import FastNoisyDevice
    dev = get_device("fake:FakeFez")
    sim = FastNoisyDevice(dev.target)
    st = S.StandIn()
    eng = TJ.Engine()
    print("backend", eng.xp.__name__, flush=True)
    rng = np.random.default_rng(1)
    for L in Ls:
        for spec in ("psfai:template", "qiskit:2:target:template"):
            arm = S.Arm(spec, dev)
            th = rng.uniform(-1.5, 1.5, TL.n_params(n, L))
            X = rng.uniform(-1, 1, (50, n))
            t0 = time.perf_counter()
            cs = [arm.compile(TL.model_circuit(TL.angle_list(th + 0.01 * k, X[k], n, L, 1.0), n, L)) for k in range(50)]
            tc = time.perf_counter() - t0
            dur, q2 = arm.duration(cs[0], sim._scan(cs[0])[0])
            t0 = time.perf_counter()
            progs = [TJ.program_from_aer(*sim.noisy_circuit(c)[0:3:2]) for c in cs]
            tp = time.perf_counter() - t0
            same = len({p.structure() for p in progs}) == 1
            t0 = time.perf_counter()
            z = eng.z_traj(progs, 256, seed=3) if same else None
            if hasattr(eng.xp, "cuda"):
                eng.xp.cuda.Stream.null.synchronize()
            ts = time.perf_counter() - t0
            sp = [TJ.program_from_aer(*st.prepared(c)) for c in cs[:2]]
            t0 = time.perf_counter()
            cnt = eng.counts(sp[:1], 200, seed=4) + eng.counts(sp[1:2], 200, seed=5)
            td = time.perf_counter() - t0
            # the skeleton path S2R's second design uses: one structure, angles per circuit
            r0, _a, nm0, _rp = sim.noisy_circuit(cs[0])
            sk = TJ.skeleton(cs[0], r0, nm0)
            A = np.stack([sk.angles(c) for c in cs])
            t0 = time.perf_counter()
            eng.z_skeleton(sk, A, 256, seed=6)
            if hasattr(eng.xp, "cuda"):
                eng.xp.cuda.Stream.null.synchronize()
            tk = time.perf_counter() - t0
            rs0, nms0 = st.prepared(cs[0])
            ssk = TJ.skeleton(cs[0], rs0, nms0)
            t0 = time.perf_counter()
            eng.z_shots_skeleton(ssk, np.stack([ssk.angles(c) for c in cs[:2]]), 200, seed=7)
            tks = time.perf_counter() - t0
            print(f"n={n} L={L} {spec:26s} act {progs[0].n} dur {dur * 1e6:.1f} us q2 {q2} steps "
                  f"{len(progs[0].steps)} same-structure {same}: compile {tc:.1f} s, programs {tp:.1f} s, "
                  f"sim 50x256 {ts:.2f} s, stand-in 2x200 {td:.2f} s; skeleton: sim 50x256 {tk:.2f} s, stand-in 2x200 "
                  f"{tks:.2f} s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
