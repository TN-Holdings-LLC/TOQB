# CUDA-Q on the pod, 2026-10-19 (H100 80 GB, target nvidia): the noise-model gate's first step

**`toqb.check_cudaq` with CUDA-Q 0.16.0 (commit 62fce8b):** the u3 self-test passed (largest deviation 3.11e-07,
limit 1e-5); the first noisy `cudaq.sample` then stopped with `ValueError: Invalid dense matrix task size.` (raised in
`runtime/nvqir/custatevec/CuStateVecTasks.h`, `compactMatrixTask`).

**`toqb.cudaq_diag`** (two-qubit kernels, 256 shots; OK = ran, ERROR = that ValueError):

| construct | 0.16.0 | 0.16.0, CUDAQ_FUSION_MAX_QUBITS=1 | 0.15.1 (aca5853) | 0.14.2 (91ab309) |
|---|---|---|---|---|
| inline DepolarizationChannel | OK | OK | OK | OK |
| inline PhaseFlipChannel | OK | OK | OK | OK |
| inline Depolarization2 (2 qubits) | OK | OK | OK | OK |
| inline AmplitudeDampingChannel | ERROR | ERROR | OK | OK |
| inline AmplitudeDampingChannel, parameters as a list | ERROR | – | OK | OK |
| inline amplitude damping as a KrausChannel instance | ERROR | – | OK | OK |
| inline PhaseDamping | ERROR | – | OK | OK |
| u3, then inline AmplitudeDampingChannel | ERROR | ERROR | OK | OK |
| gate-attached DepolarizationChannel / PhaseFlipChannel (on x) | OK | OK | OK | OK |
| gate-attached AmplitudeDampingChannel (on x) | OK | OK | OK | OK |
| gate-attached AmplitudeDampingChannel on u3, per qubit | ERROR | – | OK | OK |
| gate-attached 2-qubit Kraus (AD x AD) on cz | ERROR | – | OK | OK |
| gate-attached AmplitudeDampingChannel on an r1(0) carrier | OK | – | OK | OK |
| cx-rz-cx (ZZ), no noise | OK | OK | OK | OK |
| list-argument kernel: rz(arg), u3, inline depolarizing | OK | OK | OK | OK |

**Reading:** in 0.16.0 the general (non-unitary) Kraus channels fail in most placements, inline or attached, with or
without gate fusion; unitary mixtures (Pauli channels) work everywhere. 0.15.1 and 0.14.2 run every construct.
`toqb.cudaq_engine` therefore runs on CUDA-Q 0.15.1 (installed on the pod 2026-10-19); the agreement check against
traj2 (`toqb.check_cudaq`) was started on 0.15.1 while 12 learning runs shared the GPU, stopped by hand, and is to be
run on an idle GPU. A report for NVIDIA is drafted in `bug_report_cudaq_0.16.0.md`.

**Upstream status (checked 2026-10-19, 12:25 CEST): already known, fix pending; no issue posted.** Searching the
cuda-quantum issues for "dense matrix task" gives no result, but pull request
[NVIDIA/cuda-quantum#5584](https://github.com/NVIDIA/cuda-quantum/pull/5584), "Fix general Kraus noise channels on
fp32 backends" (open, approved by two reviewers, CI passed, not merged), reports the same error with
`AmplitudeDampingChannel` on the `nvidia` target. Its root cause: `kraus_op::data` was stored in the precision of
whichever library built it, so an fp32 simulator reads a double buffer with the wrong size and builds an invalid
matrix task. The `nvidia` target runs in fp32 by default, which fits every failure here. Consequences: 0.15.1 stays
pinned until a release contains the fix; `option="fp64"` on 0.16.0 would likely avoid the bug (not tried); the draft
issue `bug_report_cudaq_0.16.0.md` is not posted, as it would duplicate #5584.
