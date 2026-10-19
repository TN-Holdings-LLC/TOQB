"""Which CUDA-Q noise construct fails on this pod? (diagnostic for `toqb.cudaq_engine`'s "Invalid dense matrix task
size" in cudaq.sample on the nvidia target)

    python -m toqb.cudaq_diag        (on the pod, in the venv with cudaq)

Each case is a two-qubit kernel (rx on both, cz, then the noise under test) sampled with 256 shots under an empty
noise model (inline noise) or a noise model with the channel attached to a gate. Prints OK with P(1) of qubit 0, or
the error. Run once as is and once with CUDAQ_FUSION_MAX_QUBITS=1 if fusion is suspected (the script also reports
that variable).
"""
import math
import os
import sys


def main():
    import cudaq
    print("cudaq", cudaq.__version__, "| CUDAQ_FUSION_MAX_QUBITS =", os.environ.get("CUDAQ_FUSION_MAX_QUBITS"),
          flush=True)
    cudaq.set_target("nvidia")

    def base():
        k = cudaq.make_kernel()
        q = k.qalloc(2)
        k.rx(math.pi / 3, q[0])
        k.rx(math.pi / 5, q[1])
        k.cz(q[0], q[1])
        return k, q

    def inline(ch, p, n=1):
        def build():
            k, q = base()
            k.apply_noise(ch, p, *([q[0]] if n == 1 else [q[0], q[1]]))
            k.mz(q[0])
            return k, cudaq.NoiseModel()
        return build

    def by_gate(ch, p):
        def build():
            k, q = base()
            k.x(q[0])
            k.x(q[0])
            k.mz(q[0])
            nm = cudaq.NoiseModel()
            nm.add_channel("x", [0], ch(p))
            return k, nm
        return build

    def u3_then(ch, p):
        def build():
            k, q = base()
            k.u3(1.0, 0.3, -0.2, q[0])
            k.apply_noise(ch, p, q[0])
            k.mz(q[0])
            return k, cudaq.NoiseModel()
        return build

    def param_rz():
        k, ang = cudaq.make_kernel(list)
        q = k.qalloc(2)
        k.rz(ang[0], q[0])
        k.u3(math.pi / 2, 0.0, 0.0, q[0])
        k.apply_noise(cudaq.DepolarizationChannel, 0.01, q[0])
        k.mz(q[0])
        return k, cudaq.NoiseModel()

    def zz_unitary():
        k, q = base()
        k.cx(q[0], q[1])
        k.rz(0.1, q[1])
        k.cx(q[0], q[1])
        k.mz(q[0])
        return k, cudaq.NoiseModel()

    import numpy as np

    def ad_kraus(g):
        return cudaq.KrausChannel([np.array([[1, 0], [0, math.sqrt(1 - g)]], dtype=np.complex128),
                                   np.array([[0, math.sqrt(g)], [0, 0]], dtype=np.complex128)])

    def inline_instance(g):
        def build():
            k, q = base()
            k.apply_noise(ad_kraus(g), q[0])
            k.mz(q[0])
            return k, cudaq.NoiseModel()
        return build

    def inline_list(ch, p):
        def build():
            k, q = base()
            k.apply_noise(ch, [p], q[0])
            k.mz(q[0])
            return k, cudaq.NoiseModel()
        return build

    def cz_attached_2q(g):
        def build():
            k, q = base()
            k.mz(q[0])
            a = ad_kraus(g).get_ops()
            ops = [np.kron(np.array(x), np.array(y)) for x in a for y in a]
            nm = cudaq.NoiseModel()
            nm.add_channel("z", [0, 1], cudaq.KrausChannel([np.asarray(o, dtype=np.complex128) for o in ops]))
            return k, nm
        return build

    def u3_attached_per_qubit(g0, g1):
        def build():
            k, q = base()
            k.u3(1.0, 0.3, -0.2, q[0])
            k.u3(0.5, 0.1, 0.2, q[1])
            k.mz(q[0])
            nm = cudaq.NoiseModel()
            nm.add_channel("u3", [0], cudaq.AmplitudeDampingChannel(g0))
            nm.add_channel("u3", [1], cudaq.AmplitudeDampingChannel(g1))
            return k, nm
        return build

    def r1_carrier(g):
        def build():
            k, q = base()
            k.r1(0.0, q[0])
            k.r1(0.0, q[0])
            k.mz(q[0])
            nm = cudaq.NoiseModel()
            nm.add_channel("r1", [0], cudaq.AmplitudeDampingChannel(g))
            return k, nm
        return build

    cases = [
        ("inline AmplitudeDamping as a KrausChannel instance", inline_instance(0.01)),
        ("inline AmplitudeDampingChannel, parameters as a list", inline_list(cudaq.AmplitudeDampingChannel, 0.01)),
        ("inline PhaseDamping", inline(cudaq.PhaseDamping, 0.01)),
        ("gate-attached 2-qubit Kraus (AD x AD) on cz", cz_attached_2q(0.01)),
        ("gate-attached AD on u3, per qubit", u3_attached_per_qubit(0.01, 0.02)),
        ("gate-attached AD on an r1(0) carrier, twice", r1_carrier(0.01)),
        ("inline DepolarizationChannel", inline(cudaq.DepolarizationChannel, 0.01)),
        ("inline PhaseFlipChannel", inline(cudaq.PhaseFlipChannel, 0.01)),
        ("inline AmplitudeDampingChannel", inline(cudaq.AmplitudeDampingChannel, 0.01)),
        ("inline Depolarization2 (2 qubits)", inline(cudaq.Depolarization2, 0.01, 2)),
        ("gate-attached DepolarizationChannel", by_gate(cudaq.DepolarizationChannel, 0.01)),
        ("gate-attached PhaseFlipChannel", by_gate(cudaq.PhaseFlipChannel, 0.01)),
        ("gate-attached AmplitudeDampingChannel", by_gate(cudaq.AmplitudeDampingChannel, 0.01)),
        ("u3 then inline AmplitudeDamping", u3_then(cudaq.AmplitudeDampingChannel, 0.01)),
        ("cx-rz-cx (ZZ), no noise", zz_unitary),
    ]
    for name, build in cases:
        try:
            k, nm = build()
            r = cudaq.sample(k, shots_count=256, noise_model=nm)
            print(f"OK    {name}: P(1) {r.probability('1'):.3f}", flush=True)
        except Exception as exc:  # noqa: BLE001 - the point is to see which fails
            print(f"ERROR {name}: {type(exc).__name__}: {exc}", flush=True)
    try:
        k, nm = param_rz()
        r = cudaq.sample(k, [0.4], shots_count=256, noise_model=nm)
        print(f"OK    list-argument rz + u3 + inline depolarizing: P(1) {r.probability('1'):.3f}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR list-argument rz + u3 + inline depolarizing: {type(exc).__name__}: {exc}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
