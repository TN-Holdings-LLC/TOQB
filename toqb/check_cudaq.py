"""X22's noise-model gate: does CUDA-Q (`toqb.cudaq_engine`) simulate exactly traj2's model, and how fast?

    TOQB_XP=cupy python -m toqb.check_cudaq [T] [L ...]    (from the TOQB root, on a GPU pod with cudaq installed)

1. CUDA-Q's u3 against the matrix this module assumes (largest deviation up to a global phase; must be < 1e-5).
2. For n = 10, each L (default 8 16) and both compilers, two circuits of one structure, in the simulator's model
   (FakeFez) and on the stand-in (its Marrakesh-based Target, over-rotation and ZZ crosstalk): <Z> of clbit 0 from T
   trajectories (default 8192) by traj2 and by CUDA-Q. |d| / se with se from both estimates' binomial bounds
   (sqrt((1 - z^2) / T) each). The gate passes when every |d| / se < 4 (traj2 passed the same test against the density
   matrix at 1.36 se).
3. Times (after one warm-up call each): one simulator batch as an S2R loop sends it (68 circuits x 32 trajectories)
   and one circuit x 4096 trajectories, by traj2 and by CUDA-Q, with the number of inline noise operations.
"""
import sys
import time

import numpy as np

from toqb import s2r as S
from toqb import task_loop as TL
from toqb import traj2 as T2
from toqb.cudaq_engine import CudaqEngine


def _sync(xp):
    if hasattr(xp, "cuda"):
        xp.cuda.Stream.null.synchronize()


def _timed(f):
    t0 = time.perf_counter()
    out = f()
    return out, time.perf_counter() - t0


def main(argv):
    T = int(argv[0]) if argv else 8192
    Ls = [int(a) for a in argv[1:]] or [8, 16]
    from toqb.devices import get_device
    from toqb.fast_noise import FastNoisyDevice
    dev = get_device("fake:FakeFez")
    sim = FastNoisyDevice(dev.target)
    st = S.StandIn()
    eng = T2.Engine()
    cq = CudaqEngine()
    import cudaq
    print("cudaq", cudaq.__version__, "target", cq.target, "| traj2", eng.xp.__name__, eng.dtype, flush=True)
    u3dev = cq.u3_selftest()
    print(f"u3 self-test: largest deviation {u3dev:.2e}", flush=True)
    worst = 0.0 if u3dev < 1e-5 else 99.0
    rng = np.random.default_rng(11)
    n = 10
    for L in Ls:
        for spec in ("psfai:template", "qiskit:2:target:template"):
            arm = S.Arm(spec, dev)
            th = rng.uniform(-1.0, 1.0, TL.n_params(n, L))
            X = rng.uniform(-1, 1, (68, n))
            cs = [arm.compile(TL.model_circuit(TL.angle_list(th + 0.01 * k, X[k], n, L, 1.0), n, L)) for k in range(68)]
            r, _a, _nm, _rp = sim.noisy_circuit(cs[0])
            rs, _ = st.prepared(cs[0])
            for model, pl in (("sim", T2.plan(cs[0], r, dev.target)),
                              ("stand-in", T2.plan(cs[0], rs, st.target, over=st.params["over"]))):
                A = np.stack([pl.angles(c) for c in cs])
                z2 = eng.z_mean(pl, A[:2], T, seed=5)
                zc, tb = _timed(lambda: cq.z_mean(pl, A[:2], T, seed=6))
                se = np.sqrt((1 - z2 ** 2) / T + (1 - zc ** 2) / T)
                d = float((np.abs(zc - z2) / se).max())
                worst = max(worst, d)
                _, _, _, n_noise = cq.kernel(pl)
                line = (f"n={n} L={L} {spec:26s} {model:8s} act {pl.n} steps {len(pl.steps)} noise ops {n_noise}: "
                        f"traj2 z {np.round(z2, 4)} cudaq z {np.round(zc, 4)} ({d:.1f} se; first call {tb:.1f} s)")
                if model == "sim":
                    eng.z_mean(pl, A[:2], 4, seed=1)
                    _sync(eng.xp)
                    _, t_a = _timed(lambda: (eng.z_mean(pl, A, 32, seed=2), _sync(eng.xp)))
                    _, t_b = _timed(lambda: cq.z_mean(pl, A, 32, seed=3))
                    _, t_c = _timed(lambda: (eng.z_mean(pl, A[:1], 4096, seed=4), _sync(eng.xp)))
                    _, t_d = _timed(lambda: cq.z_mean(pl, A[:1], 4096, seed=7))
                    line += (f" | 68x32: traj2 {t_a:.2f} s, cudaq {t_b:.2f} s; 1x4096: traj2 {t_c:.2f} s, "
                             f"cudaq {t_d:.2f} s")
                print(line, flush=True)
    print("PASS" if worst < 4 else "FAIL", f"largest {worst:.2f} se")
    return 0 if worst < 4 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
