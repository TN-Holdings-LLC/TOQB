# Draft issue for NVIDIA/cuda-quantum (to be posted by the owner)

**Title:** 0.16.0 regression: general Kraus channels (amplitude damping, phase damping, custom KrausChannel) fail
with "Invalid dense matrix task size." on the nvidia target; 0.15.1 works

**Environment:** CUDA-Q 0.16.0 (Python wheel, commit 62fce8b862302158e0119c65e3ce57538f3af048), target `nvidia`,
NVIDIA H100 80GB HBM3, Python 3.12, Linux. The same script runs without error on 0.15.1 (aca5853) and 0.14.2
(91ab309) in the same environment.

**Reproducer:**

```python
import math
import cudaq

cudaq.set_target("nvidia")
k = cudaq.make_kernel()
q = k.qalloc(2)
k.rx(math.pi / 3, q[0])
k.rx(math.pi / 5, q[1])
k.cz(q[0], q[1])
k.apply_noise(cudaq.AmplitudeDampingChannel, 0.01, q[0])
k.mz(q[0])
print(cudaq.sample(k, shots_count=256, noise_model=cudaq.NoiseModel()))
```

**Result on 0.16.0:** `ValueError: Invalid dense matrix task size.` (from `compactMatrixTask` in
`runtime/nvqir/custatevec/CuStateVecTasks.h`), with or without `CUDAQ_FUSION_MAX_QUBITS=1`.

**Also failing on 0.16.0:** `PhaseDamping` and a `KrausChannel` built from the amplitude-damping operators, applied
inline; `AmplitudeDampingChannel` attached to `u3` per qubit with `NoiseModel.add_channel`; a two-qubit `KrausChannel`
(amplitude damping on both qubits) attached to `cz`. **Working on 0.16.0:** Pauli channels (DepolarizationChannel,
PhaseFlipChannel, Depolarization2) inline or attached, and `AmplitudeDampingChannel` attached to `x` or to an `r1(0)`
gate.

**Expected:** the same results as 0.15.1 (all of the above run).
