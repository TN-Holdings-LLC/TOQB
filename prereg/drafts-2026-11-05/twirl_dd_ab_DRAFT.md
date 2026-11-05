# DRAFT (not declared; the owner decides; written at the workplace 2026-11-05 02:10 CET): P6 with formula-built Pauli twirling and an idle-qubit echo against P6 as run on 11-04, A and B in one job

Status: draft only. Nothing here is fixed until home declares it. The idea comes from a post-hoc analysis
(`notes/s1_2026-11-05/`, synthetic noise of strengths chosen there; no calibration numbers, no fake-device noise).

## Question

Does writing P6 with (i) Pauli twirling of every CZ by a fixed table and (ii) an X-X echo on every qubit that is idle
during a CZ layer change P6's raw forward error? Reported beside it, not judged: does the 11-04 correction (floor and
mirror, `gpu/corr_score.py`) hold on B, in particular at theta_x 0.8 where it over-corrected on ibm_fez?

## What B changes (A = P6 exactly as on 11-04)

- Same logical circuit (RX(theta_x) RZ(0.1), then RZZ(1.0) on the 38 edges in P6's three layers; RZZ = CX RZ CX,
  CX = H CZ H; 2 x 38 x t CZ). Same copy, same shots per arm, same job.
- **Twirl (fixed table, no random numbers):** the CZs of a circuit are numbered g = 0, 1, ... in circuit order. Frame
  k = 0..7: before CZ g put the two-qubit Pauli P with index (g + 3k) mod 16 in the order II, IX, IY, IZ, XI, ..., ZZ
  (control first); after it put CZ P CZ (computed, a Pauli up to sign; the sign is dropped as a global phase).
  Each B circuit is run as 8 frame circuits of 250 shots (A: one circuit of 2000 shots).
- **Echo:** in every CZ layer (two CZ slots per RZZ layer), every patch qubit not in that layer gets an X after each of
  the two slots; barriers delimit the slots so the compiler cannot merge the two Xs.
- Floors and mirrors of B are built from B's circuits the way the 11-04 builder built them from A's.

## Job (one job; budget kept under the 60 s default)

- theta_x 0.53 and 0.8 only (0.3 left out to keep one job: it is the case the correction already handled), t 1-9.
- A: forward 18 + floor 7 (theta_x 0, t 1, 3, 5, 6, 7, 9, 10) + mirror 4 (t 3, 5) = 29 circuits x 2000 shots.
- B: the same 29, each as 8 frame circuits x 250 shots = 232 circuits.
- Ring sentinel as on 11-04.
- Cost: CZ per circuit unchanged (B adds none; mirror CZ exactly doubled as before). 1q gates added by the echo:
  2 x (11 + 11 + 7) = 58 X per step (t 9: 522), in idle windows. Time model: A 1.04 + 15.66 s, B 8.35 + 15.66 s,
  + 3 s per job + the sentinel: about 44 s (11-04's corr job: 44 circuits, 52.1 s).

## Checks before sending (any failure: no job)

1. Every B frame circuit has the same unitary as A's circuit (statevector on light cones, t <= 3; within 1e-9 up to
   global phase).
2. After psf-os compilation: B's CZ count = A's for every circuit; B's X count >= the echo's count (the Xs survived).
3. Mirrors accepted as on 11-04 (CZ exactly doubled).

## Judged (per theta_x)

**HELPS / NO EFFECT / HURTS:** R = MSE_B / MSE_A of the raw forward <Z_q> against the sealed answers, over t 1-9 and
every qubit with an answer (no floor, no mirror, no rule R), at R <= 0.8 / R >= 1.25.

## Reported (not judged)

The 11-04 correction applied unchanged to A and to B (rule R, F, a_theta, z_corr): MSE ratio and AGREES for each arm;
per-qubit residuals by distance to rule-R-dropped qubits; forward and mirror decay per step of each arm.

## Honest expectation (from the synthetic-noise simulation; not evidence about the device)

- Raw error (the judged number): B/A was 1.01-1.49 across every noise model tried (depolarizing 1.08-1.10;
  static ZZ 1.15-1.49; detuning 1.12-1.48; over-rotation 1.05-1.07; a stuck partner qubit 1.01-1.07). It never fell
  below 0.8. **The most likely verdict is NO EFFECT; HURTS is possible at theta_x 0.8.** The echo adds gates; the twirl
  turns coherent errors into stochastic ones, which shows in the raw mean as a loss.
- What B is for shows only in the corrected numbers: when always-on coherent errors (static ZZ, detuning) break the
  mirror model, corrected MSE with B fell to 0.002-0.11 of A's (static ZZ at 0.8: 0.0005 against 0.037; detuning at
  0.8: 0.0003 against 0.18), the over-correction at 0.8 vanished. When the loss is over-rotation or a stuck partner
  (the marrakesh pattern), B changed nothing.
- So a test judged on the raw error alone would most likely not show the fix. Whether the judged item should be the
  corrected ratio instead is the owner's decision; this draft keeps the raw error as the 05b instruction asks.

## Limits

One device, one job; shots per arm 2000 (11-04: 4000). Eight fixed frames (8 of the 16 Paulis per CZ), not the
infinite average the simulation used; the depolarizing+echo case stood in for depolarizing+echo+twirl (the twirl
does nothing to Pauli noise). The simulation's noise strengths were chosen there, not fitted; the device's actual error mix is unknown, which
is why a device test is asked at all.
