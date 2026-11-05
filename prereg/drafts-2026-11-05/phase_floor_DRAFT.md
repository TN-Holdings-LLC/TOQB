# DRAFT (not declared; workplace, 2026-11-05): the phase floor, the errors that neither the floor nor the mirror sees

Status: draft for home and the owner (task U1, home's instruction 05d). Nothing is fixed. Tool check on synthetic noise:
`notes/phase_floor_2026-11-05/pf_sim.py` (strengths chosen there, as in s1_sim; no calibration numbers).

## 0. Why

- The floor (theta_x = 0: the compiled circuit without its non-diagonal one-qubit gates) is a diagonal circuit on
  |0...0>: every Z-type phase (static ZZ, detuning, a CZ's phase error, Stark shifts from neighbouring drives) leaves
  it unchanged. It sees readout and bit flips only.
- The mirror (U, barrier, U^dagger) cancels what U^dagger undoes (over-rotation; a stuck partner) and doubles what it
  does not (always-on phases), so it can under- or over-read the forward loss (05b, S1).
- The phase floor puts the same diagonal circuit between H layers: |+> in, X (and Y) read. Every Z-type phase now
  turns the qubit's Bloch vector; every dephasing shrinks it. Over-rotation of RX stays invisible here too (the floor
  has no RX): **no instrument in this note measures it**.

## 1. The circuit

1. Take the compiled user circuit as psf-os compiles it (`compile`), remove its non-diagonal one-qubit gates exactly
   as `user2d.floor_of` does (CZ, RZ, barriers stay; no recompilation, so no CZ is cancelled or merged).
2. Put H (as RZ(pi/2) SX RZ(pi/2)) on every patch qubit before the first gate and after the last; for the Y read,
   RZ(-pi/2) before the final H. Nothing is optimised afterwards (an ISA circuit is sent as built).
3. Measure every patch qubit in Z (= X or Y of the state before the last H).
- Per qubit: z = <X> + i<Y>, ideal z0 from the same circuit without noise; contrast c = |z| / |z0|, phase error
  phi = arg(z / z0).

## 2. Acceptance (refused with the reason if it fails)

1. **Even CZ count on every edge.** The ideal is a pure phase per qubit (|z0| = 1) only if every edge carries an even
   number of CZs; one unpaired CZ on an edge (q, r) makes <X_q> = <X_q Z_r> = 0 on |+>: no signal.
   - P6 form (RZZ of a general angle = two CZs): even at every t. Accepted.
   - P5 form after psf-os ac84182 (RZZ(+-pi/2) = one CZ): even only at even t. Odd t is **refused** with the reason
     "odd CZ count on edge (q, r)"; for the daily sentinel (section 6) the same circuit's depth t - 1 is used and
     labelled so.
   - Echo variants (section 3): the count must also be even on every edge on each side of the echo.
2. The phase floor's CZ count equals the forward circuit's (no CZ lost in building).
3. Answers: from the assembled circuit by noiseless computation. The circuit is diagonal between the H layers, so
   <X_q>, <Y_q> depend only on q's own RZs and the CZs on q's edges: each is computed exactly on q's star (q and its
   neighbours, at most 4 qubits) for any patch size; checked against a whole-patch statevector on patches of up to
   20 qubits (CPU) before use (agreement within 1e-12).

## 3. Variants and controls (one job)

| variant | what it is | cancels | keeps |
|---|---|---|---|
| plain | section 1 | nothing | every Z-type phase; dephasing |
| echo-all | X on every patch qubit at the middle step boundary | single-qubit Z phases (detuning, RZ angle errors) | ZZ between neighbours (X X commutes with Z Z); dephasing beyond the echo |
| echo-A | X on side A of the patch's bipartition (fixed: BFS from the smallest label) | ZZ on every edge; Z phases on side A | Z phases on side B |
| near / far pair | probe set Pr (qubits at mutual distance >= 3, greedy in sorted order); probes get no gate between the H layers; "near": CZ pairs (two CZs, so the ideal stays known) on the edges touching a probe's neighbours, layer by layer with barriers; "far": the same number of layers with CZ pairs on edges at distance >= 2 from every probe | both arms: the probe's static ZZ with its neighbours alike (the neighbours' Z distribution is the same in both) | the difference near - far: what a neighbour's CZ drive does to an idle qubit (drive crosstalk), apart from ordinary noise |

What the synthetic run shows (10-qubit P6 piece, t 2 / 4 / 6; not evidence about a device):

| noise | plain: contrast, phase | echo-all | echo-A |
|---|---|---|---|
| depolarizing only | 0.93 / 0.91 / 0.89, 0 | same | same |
| static ZZ 0.02 rad/slot | 0.89 / 0.75 / 0.57, 0 | same as plain | 0.93 / 0.91 / 0.88 (ZZ loss removed) |
| detuning 0.02 rad/slot | as depolarizing, **0.24 / 0.48 / 0.72 rad** | phase 0 | phase 0 on side A, 0.12 / 0.24 / 0.36 on B |
| RZZ angle 5 % | phase 0.08 / 0.17 / 0.25 rad | phase 0 | partly |
| stuck partner (label 23) | its neighbours' contrast **0.62 / 0.60 / 0.58** (others 0.93-0.89) | neighbours' phase about 1.0 rad | neighbours' contrast as plain |
| RX over-rotation 5 % | **invisible** (as in the floor) | invisible | invisible |

So: static ZZ = the contrast that echo-A restores; single-qubit phase errors = the phase that echo-all removes; a stuck
partner = a local hole in its neighbours' contrast in the plain variant. The plain Z floor showed none of these.
Drive crosstalk (near / far) was not simulated: no model of it was invented.

## 4. Questions to fix in advance (proposal; thresholds for the owner)

- **Q1, always-on phase:** per qubit phi_plain at t 2, 4, 6 and its slope per step; median |slope| over kept qubits,
  with echo-all's slope beside it. Proposal: PRESENT if median |phi_plain(t 6)| > 0.05 rad and > 3 SE, SMALL otherwise.
- **Q2, static ZZ:** ratio c_plain / c_echo-A at t 6, median over kept qubits. Proposal: PRESENT if < 0.95 and the gap
  > 3 SE.
- **Q3, drive crosstalk:** probes' c and phi, near minus far, median over probes, +- 2 SE.
- **Q4, the neighbours of dropped qubits:** rule R on the same job's Z floor (P6's rule); the qubits at distance 1 of a
  dropped qubit in a separate column for Q1-Q3 (never pooled with the rest).
- SE: shot noise (phase SE about 1 / (c sqrt(shots)) rad per basis, about 0.017 rad at c 0.9 and 4000 shots) and, if
  the owner keeps the two-runs rule of the crosstalk test, the larger of shot SE and the between-run spread.
- What the answers decide (proposal): Q1 or Q2 PRESENT -> the twirl + echo A/B (S3 draft) is worth a job; both SMALL ->
  S3 stays shelved. Q4 large -> the neighbour rule (`neighbour_rule_DRAFT.md`) is the direct fix.

## 5. Job and cost (P6's 35-qubit patch, P6's device and placement rules)

- plain, echo-all, echo-A at t 2, 4, 6, each read in X and Y: 18 circuits; near / far at t 4, X and Y: 4 circuits;
  the Z floor at t 2, 4, 6 (3, for rule R and Q4); ring sentinel. 25 circuits + sentinel, 4000 shots.
- CZ per circuit: 152 / 304 / 456 at t 2 / 4 / 6 (2 x 38 x t; near / far fewer). Time model: 25 x 0.036 +
  25 x 4000 x 0.00027 + 3 = 30.9 s, + the sentinel (about 1 s at 4000 shots): about 32 s.

## 6. As a daily sentinel (one circuit added)

- The day's problem's own phase floor at the problem's t (t - 1 if the CZ count is odd, labelled), plain, read in X
  with a virtual RZ frame per qubit that puts the ideal phase at pi/4 (ideal <X> = 0.707 for every qubit; a phase
  error moves it at first order with its sign, a contrast loss scales it). One circuit, 4000 shots: +1.1 s by the model.
- Reported per qubit beside the answer card, not judged. It says which qubits carried an unseen phase or a hole that
  day; it cannot split phase from contrast (the full job above does).

## 7. Limits

- Over-rotation (and any error inside the RX gates) is not measured by this note.
- The floor's schedule is not the forward circuit's schedule (the SX gates are missing, so idle windows differ); the
  phase floor measures the CZ schedule's phases, not the full circuit's.
- One job, one device; the thresholds are proposals.
