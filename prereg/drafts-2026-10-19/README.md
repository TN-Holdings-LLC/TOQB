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
