# Drafts of 2026-10-19 (not fixed; nothing here is a pre-registration yet)

Written at the workplace on 2026-10-19 (CEST) from the owner's decisions and the home session's notes; design text
and formula estimates only, nothing was run there. Kept as written; corrections found since are listed below and go
into the next revision, not into these files.

| file | what it is |
|---|---|
| `X22_preregistration_skeleton.md` | engine x compiler (2 x 2) test, CUDA-Q + PSF-Zero: claim form (Pareto within the tested range, not "the only solution"), noise-model gate N1-N4, engine fairness, the Qiskit setting, log-scale interaction |
| `S2RB_preregistration_skeleton.md` | S2R2-B (owner's decision B): GPU simulator learning with stand-in records vs SPSA2 |
| `S2RB_runtime_cost_estimate.md` | GPU hours of the S2R2-B main run, by formula from RTX 4070 timings |
| `*_r2.md` | second revisions (H100 pilot values filled in; the first versions are kept unchanged) |
| `TF_twin_fidelity_proposal.md` | proposal: does PSF-Zero compilation make the GPU twin know the device's gradient better (higher cos)? simulation only, before decision A |
| `C_preregistration_skeleton.md` | design C (owner's decision of 2026-10-19): train on the GPU twin, predict, one device job ("stamp"); H1 accuracy above 0.5, H2 PSF's deviation smaller than Qiskit's |
| `qpu_cost_check_gradcos.md`, `mc_gradcos.py` | check of the hardware cost of decision A (gradient agreement on a real device) and a Monte Carlo of the estimator |

**Corrections and new facts since (2026-10-19, pod pilot on an H100, partial):**

- H100 / RTX 4070 speed of `traj2` (68 circuits x 32 trajectories): PSF L 8 2.3 x, Qiskit L 8 4.8 x, PSF L 16 1.9 x,
  Qiskit L 16 5.0 x. On the H100 the PSF / Qiskit gap at L 16 is 2.8 x (7.4 x on the RTX 4070): ten qubits do not
  fill an H100 (per-step launch and host time dominate), fourteen do.
- The evaluation batches all test points of one structure (template compiles), so the batched rate r_lo applies in
  the runtime estimate.
- Gradient agreement, simulator vs stand-in (`toqb.gradcos`, 24 directions, 8 points, T = 256, student means 5 / 6):
  PSF L 8 1.00 / 1.00, PSF L 16 0.97 / 0.99, Qiskit L 8 0.80 / 0.85, Qiskit L 16 0.87 / 0.97; the stand-in's gradient
  over the simulator's: PSF 0.74-0.79, Qiskit L 8 0.34-0.50, Qiskit L 16 0.81. With K = 24 a true 0.9 reads as
  0.81-0.96, so: PSF about 1, Qiskit about 0.85-0.9.
- CUDA-Q 0.16.0 runs on the pod (target nvidia). Its first contact used a simplified noise model, so its times are not
  yet comparable; `toqb.check_cudaq` (the N1-N4 gate) is the next step.

**Notes on the r2 files (home review, 2026-10-19):**

- Runtime r2: the stand-in's plans have about twice the steps of the simulator's (ZZ crosstalk; PSF L 8: 1558
  against 812), so an evaluation on the stand-in runs slower than the simulator's batched rate r_lo; the
  evaluation share is a lower bound until one evaluation is timed on the pod.
- S2R2-B r2, §3 note on H2: written when both compilers' cos were assumed near 0.99; with Qiskit at about
  0.85-0.9 it needs rewording in r3.
- X22 r2, §2 gate: how CUDA-Q expresses N1-N4 is now implemented (`toqb/cudaq_engine.py`): N1 and N2 as inline
  AmplitudeDampingChannel and PhaseFlipChannel (per gate and per idle interval, from the same Plan), N3 as an exact
  RZZ (cx, rz, cx), N4 inside the u3 of each sx / x; whether the numbers agree is `toqb.check_cudaq`, not yet run.
- TF: besides ZZ, idle relaxation and over-rotation, the compilers also place the circuit on different physical
  qubits, whose stand-in calibration (Marrakesh, T1 / T2 scaled by up to +-30 %) differs from FakeFez's by
  different amounts; the follow-up that switches effects off one at a time should include "same calibration".

**Notes on the C skeleton (home review, 2026-10-19):**

- §2, H1's count: the labels are +1 / -1 on <Z> (`toqb.s2r2.teacher_data2`): label +1 means <Z> > 0, that is
  P(1) < 0.5. The skeleton's "p > 0.5 for label 1" has the sign the other way round. `toqb/s2rc.py` now records the
  strict count (a tie, P(1) = 0.5 exactly, counts as wrong) and the one-sided exact binomial p; its accuracy figure
  still counts a tie as 0.5.
- §6, the rehearsal's twin: in `gpu/s2rc_rehearsal.sh` the twin is the simulator's model of FakeFez (TOQB's noise
  model), and the stand-in is ibm_marrakesh's calibration with T1 / T2 scaled, over-rotation and ZZ. So the
  rehearsal's twin differs from its "device" by the calibration source as well, more than the device day will (the
  twin is then built from that device's own calibration). Whether the rehearsal's twin should instead be built from
  the stand-in's unperturbed Marrakesh calibration (and the circuits compiled against it) is open: an owner decision.
- Decided 2026-10-19 (owner): the rehearsal's twin is built from the stand-in's published calibration (device
  `snapshot:marrakesh`: the Marrakesh snapshot without the stand-in's T1 / T2 scaling, over-rotation and ZZ), and the
  circuits are compiled against it. CPU smoke (n = 6, L = 4, 20 loops): the twin's P(1) against the stand-in's,
  rms 0.014 for PSF (0.026 with the FakeFez twin) and 0.024 for Qiskit.
- S2R2-B r3 (B closed at its pilot) and C r2 (workplace, 06:16 CEST). Home check of C r2 §3: the CE formula matches
  `toqb.s2r2._ce` as `toqb.s2rc` uses it (p = (1 + z) / 2 = 1 - P(1), clipped to [1e-4, 1 - 1e-4]; -log p for y = +1,
  -log(1 - p) for y = -1), so its `[ ]` "to confirm against toqb/s2rc.py" is confirmed.

**X22 r3, C r3, consult A-D and `pn_power2.py` (workplace, 10:00 CEST; home review 2026-10-19 evening):**

- `pn_power2.py` rerun at home (scipy, seed 20261019): every H1 power, critical accuracy, cost and H2 power figure in
  consult §C and C r3 §4 is reproduced.
- consult §A's two code facts are confirmed: `CudaqEngine.kernel` caches one kernel per plan with the slot angles as a
  `list` argument, and `check_cudaq` times after one warm-up call, so the 68 x 32 times are warm. The home note of the
  check (`results/cudaq-check-2026-10-19/README.md`), which blamed the 4-40 s first calls, was wrong and is corrected
  there.
- Home addition to §A: the warm cost per call divided by the plan's inline noise operations is 0.23-0.25 ms for all
  four plans (PSF L 8 0.626 s / 2,693; Qiskit L 8 0.762 / 3,073; PSF L 16 1.272 / 5,313; Qiskit L 16 1.503 / 6,262).
  The fixed cost per call is therefore proportional to the number of inline noise operations (inferred from four
  points; not profiled), which points at C1 (fewer calls) and C3 (gate-attached noise) first. Subtracting it from the
  1 x 4,096 times leaves an estimated simulation share of about 0.12 / 1.07 s (PSF / Qiskit, L 8) and 0.13 / 2.22 s
  (L 16): differences of single measurements, rough. So the home reading "PSF's saving carries over to CUDA-Q
  (2.4-2.7 x)" in instruction 4 measured mostly the per-call cost, not the simulation.
- C r3 §3's `[ ]` on the CE formula: confirmed against `toqb.s2r2._ce` (as for r2).
- consult §B (ii): the owner rules of 2026-10-14 (no effort on calibration data) and 2026-10-15 (placement ignored for
  now) are the rules meant; option 3 needs them lifted explicitly. Home addition: the stand-in's deviations from the
  twin (T1 / T2 scaled, ZZ, over-rotation) act less on better qubits, so Qiskit's calibration-aware placement should
  lower its own twin deviation; if so, the confound works against PSF in H2 as well as in CE (inferred, not checked).
- Open for the owner, not in the drafts: whether the stamp is paid (Pay-As-You-Go, $1.60 / s) or uses the remaining
  open-plan minutes (about 2 minutes as of 2026-10-15). About 120 s of QPU time fits, by the same time model, 800
  points at N = 250 (82.8 s) or about 700 points at N = 500, not P_8 200 / P_16 300 at N = 1,000 (306 s).
