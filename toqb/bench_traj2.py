"""Times the second trajectory engine (`toqb.traj2`) on S2R's classifier, both compilers, at a loop's sizes.

    TOQB_XP=cupy python -m toqb.bench_traj2 [n] [L ...]     (from the TOQB root; default n = 10, L = 8 16 24)

An arm whose compiled circuit is wider than TOQB_BENCH_MAXQ active qubits (default 16) is reported and skipped
(Qiskit's L = 24 circuit is about 21 qubits wide: hours per batch).

Per compiler and depth: active qubits, duration, two-qubit gates; the time of one simulator batch as an S2R loop
sends it (68 circuits of one structure x 32 trajectories) and of the stand-in's two circuits x 100 shots; and the
compile time of the 68 circuits.
"""
import os
import sys
import time

import numpy as np

from toqb import s2r as S
from toqb import task_loop as TL
from toqb import traj2 as T2


def _sync(xp):
    if hasattr(xp, "cuda"):
        xp.cuda.Stream.null.synchronize()


def main(argv):
    n = int(argv[0]) if argv else 10
    Ls = [int(a) for a in argv[1:]] or [8, 16, 24]
    from toqb.devices import get_device
    from toqb.fast_noise import FastNoisyDevice
    dev = get_device("fake:FakeFez")
    sim = FastNoisyDevice(dev.target)
    st = S.StandIn()
    eng = T2.Engine()
    print("backend", eng.xp.__name__, eng.dtype, flush=True)
    rng = np.random.default_rng(1)
    for L in Ls:
        for spec in ("psfai:template", "qiskit:2:target:template"):
            arm = S.Arm(spec, dev)
            th = rng.uniform(-1.0, 1.0, TL.n_params(n, L))
            X = rng.uniform(-1, 1, (68, n))
            t0 = time.perf_counter()
            cs = [arm.compile(TL.model_circuit(TL.angle_list(th + 0.01 * k, X[k], n, L, 1.0), n, L)) for k in range(68)]
            tc = time.perf_counter() - t0
            dur, q2 = arm.duration(cs[0], sim._scan(cs[0])[0])
            r, _a, _nm, _rp = sim.noisy_circuit(cs[0])
            pl = T2.plan(cs[0], r, dev.target)
            if pl.n > int(os.environ.get("TOQB_BENCH_MAXQ", "16")):
                print(f"n={n} L={L} {spec:26s} act {pl.n} dur {dur * 1e6:.1f} us q2 {q2} steps {len(pl.steps)}: "
                      f"skipped (wider than TOQB_BENCH_MAXQ), compile 68 {tc:.2f} s", flush=True)
                continue
            A = np.stack([pl.angles(c) for c in cs])
            eng.z_mean(pl, A[:2], 4, seed=1)  # warm-up
            _sync(eng.xp)
            t0 = time.perf_counter()
            eng.z_mean(pl, A, 32, seed=2)
            _sync(eng.xp)
            ts = time.perf_counter() - t0
            rs, _ = st.prepared(cs[0])
            spl = T2.plan(cs[0], rs, st.target, over=st.params["over"])
            t0 = time.perf_counter()
            eng.z_shots(spl, np.stack([spl.angles(c) for c in cs[:2]]), 100, seed=3)
            _sync(eng.xp)
            td = time.perf_counter() - t0
            print(f"n={n} L={L} {spec:26s} act {pl.n} dur {dur * 1e6:.1f} us q2 {q2} steps {len(pl.steps)}: "
                  f"sim 68x32 {ts:.2f} s, stand-in 2x100 {td:.2f} s, compile 68 {tc:.2f} s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
