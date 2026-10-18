"""First contact with CUDA-Q (a probe, not a measurement for any claim): can CUDA-Q run S2R's compiled classifier
circuits with noise on the GPU, and how fast, next to `toqb.traj2` on the same circuits?

    python -m toqb.cudaq_probe [L ...]        (from the TOQB root, on a GPU pod; needs `pip install cudaq`)

For n = 10 and each depth L, one circuit of each compiler (PSF-Zero's template, Qiskit level 2) on FakeFez is turned
into a CUDA-Q kernel on its active qubits (rz -> rz, sx -> rx(pi/2), x -> x, cz -> cz; delays and barriers dropped).
Noise, the same simple model for both engines here: a depolarizing channel of probability p1 after every one-qubit
gate and p2 on each qubit after every cz (CUDA-Q's DepolarizationChannel; in traj2 the plan's own FakeFez noise is
used instead, so the times compare engines, not noise models). Prints CUDA-Q's version and targets, then per circuit:
active qubits, gates, and the time of <Z0> from T trajectories (sample with T shots under the noise model) on the
"nvidia" target, against traj2's z_mean of 1 circuit x T trajectories. Every CUDA-Q call is guarded: an API this
probe does not know prints its error and the probe goes on.
"""
import math
import sys
import time

import numpy as np

from toqb import s2r as S
from toqb import task_loop as TL
from toqb import traj2 as T2


def _active(c):
    idx = {q: k for k, q in enumerate(c.qubits)}
    act = sorted({idx[q] for i in c.data if i.operation.name not in ("delay", "barrier", "measure") for q in i.qubits})
    return act, idx


def to_cudaq(cudaq, c):
    """A CUDA-Q builder kernel of compiled circuit c on its active qubits, and the kernel qubit of clbit 0."""
    act, idx = _active(c)
    pos = {q: k for k, q in enumerate(act)}
    kernel = cudaq.make_kernel()
    q = kernel.qalloc(len(act))
    m0 = None
    n_g = 0
    for ins in c.data:
        nm = ins.operation.name
        qs = [pos[idx[x]] for x in ins.qubits if idx[x] in pos]
        if nm == "rz":
            kernel.rz(float(ins.operation.params[0]), q[qs[0]])
        elif nm == "sx":
            kernel.rx(math.pi / 2, q[qs[0]])
        elif nm == "x":
            kernel.x(q[qs[0]])
        elif nm == "cz":
            kernel.cz(q[qs[0]], q[qs[1]])
        elif nm == "measure":
            if c.find_bit(ins.clbits[0]).index == 0:
                m0 = qs[0]
            continue
        elif nm in ("delay", "barrier"):
            continue
        else:
            raise ValueError(f"cudaq_probe: unsupported gate {nm}")
        n_g += 1
    kernel.mz(q[m0])
    return kernel, len(act), n_g, m0


def noise_model(cudaq, nq, p1=1e-3, p2=5e-3):
    nm = cudaq.NoiseModel()
    for g in ("rz", "rx", "x"):
        for k in range(nq):
            nm.add_channel(g, [k], cudaq.DepolarizationChannel(p1))
    for a in range(nq):
        for b in range(nq):
            if a != b:
                try:
                    nm.add_channel("z", [a, b], cudaq.DepolarizationChannel(p2))
                except Exception:  # noqa: BLE001 - controlled-gate channels differ between versions
                    pass
    return nm


def main(argv):
    Ls = [int(a) for a in argv] or [8, 16]
    try:
        import cudaq
    except ImportError as exc:
        print("STOP: no cudaq:", exc)
        return 1
    print("cudaq", getattr(cudaq, "__version__", "?"), flush=True)
    try:
        print("targets", [t.name for t in cudaq.get_targets()], flush=True)
        cudaq.set_target("nvidia")
        print("target nvidia set", flush=True)
    except Exception as exc:  # noqa: BLE001
        print("target:", type(exc).__name__, exc, flush=True)
    from toqb.devices import get_device
    from toqb.fast_noise import FastNoisyDevice
    dev = get_device("fake:FakeFez")
    sim = FastNoisyDevice(dev.target)
    eng = T2.Engine()
    rng = np.random.default_rng(3)
    n = 10
    for L in Ls:
        th = rng.uniform(-1, 1, TL.n_params(n, L))
        x = rng.uniform(-1, 1, n)
        for spec in ("psfai:template", "qiskit:2:target:template"):
            c = S.Arm(spec, dev).compile(TL.model_circuit(TL.angle_list(th, x, n, L, 1.0), n, L))
            try:
                kernel, nq, n_g, m0 = to_cudaq(cudaq, c)
            except Exception as exc:  # noqa: BLE001
                print(f"L={L} {spec}: kernel: {type(exc).__name__}: {exc}", flush=True)
                continue
            line = f"L={L} {spec:26s} active {nq} gates {n_g}:"
            for T in (256, 4096):
                try:
                    nmod = noise_model(cudaq, nq)
                    t0 = time.perf_counter()
                    res = cudaq.sample(kernel, shots_count=T, noise_model=nmod)
                    tc = time.perf_counter() - t0
                    p1 = res.probability("1") if hasattr(res, "probability") else float("nan")
                    line += f" cudaq T={T} {tc:.2f} s (p1 {p1:.3f});"
                except Exception as exc:  # noqa: BLE001
                    line += f" cudaq T={T}: {type(exc).__name__}: {exc};"
            r, _a, _nm, _rp = sim.noisy_circuit(c)
            pl = T2.plan(c, r, dev.target)
            A = pl.angles(c)[None, :]
            for T in (256, 4096):
                t0 = time.perf_counter()
                z = eng.z_mean(pl, A, T, seed=1)[0]
                line += f" traj2 T={T} {time.perf_counter() - t0:.2f} s (p1 {(1 - z) / 2:.3f});"
            print(line, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
