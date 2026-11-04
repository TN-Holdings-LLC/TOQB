# DRAFT (not declared; skeleton before tonight's P6/OS2D results): crosstalk, measured before anything is corrected (workplace, 2026-11-04)

Status: a skeleton for home and the owner. The tools exist (psf-os 3259af3 `psf_os/crosstalk2d.py` with 7 tests; TOQB
`gpu/xtalk_device.py`, `notes/xtalk_2026-11-04/xtalk_answers.py`, `xtalk_score.py`), dry-run on three fake snapshots.
Fields marked **[after tonight]** are filled once the P6 and OS2D results are in, as home's instruction asks; nothing
in this draft depends on them except those fields.

## 0. Which crosstalk this test measures (stated first)

| kind | splitting a layer | what this test can say |
|---|---|---|
| between CZs driven at the same time on neighbouring couplers | **removes it** (no two CZs of a split layer are on the same or neighbouring couplers) | **measured**: the standard arm against the split arm, same job, interleaved |
| static (always-on) ZZ between neighbouring qubits | does not remove it; it acts while a qubit waits, and the split schedule is longer (3 -> 6 CZ layers per step), so it can act more | **not separated**: it enters the split arm's cost together with the other idle-time losses (T1, T2) |
| readout crosstalk (a correlation added at measurement) | not affected | **measured by the pattern controls** (section 3) |

Two consequences, written here so that no result is read past them:
- The difference between the arms is a **net** number: (crosstalk between simultaneous CZs removed) minus (longer idle
  time: static ZZ plus decoherence). A split arm that does not help does not show that there is no simultaneous-CZ
  crosstalk.
- A mirror (U, barrier, U^dagger) can cancel a static ZZ (as the frame flip showed on mirror circuits). **A mirror drop
  is not a measurement of static ZZ**, and a small mirror drop does not show that the static ZZ is small.

## 1. Layers, barriers and acceptance

The compiler and the device run gates on different qubits as early as they can. Two layers written one after the
other without a barrier run together (the same pitfall as the ring echo and the mirror join). So:

- **Standard arm (S):** P5's circuit (RZZ(-pi/2) as one CZ, RZ(-pi/2) on both ends, then RX(theta) on every qubit), CZs
  in P5's colour classes (`kim.colour`, greedy, sorted order), **a barrier after every class**. P5 as run on 3 November
  had no barriers; S has them so that which CZs run together is known and checked (3 classes per step; on the fake
  snapshots 50 / 46 / 41 CZs on kingston).
- **Split arm (D):** each colour class split greedily in sorted order (no search): an edge joins the first sublayer in
  which it shares no qubit with, and has no device coupler (working or failed: the geometry) to, any edge already
  there; **a barrier after every sublayer**. On the fake snapshots: 6 sublayers per step on kingston, fez and
  marrakesh (kingston 28 / 22 / 27 / 19 / 20 / 21).
- The RZZs commute, so S and D prepare the same state (tested by statevector, and both equal P5 without barriers).
- **Acceptance (refused before sending if it fails):** in every compiled circuit, the CZs between consecutive
  barriers are exactly the designed groups, in order, each edge once, no two sharing a qubit; for D, the groups are
  also mutually non-adjacent (`crosstalk2d.accept`, `is_split`). A missing barrier merges two groups and is refused
  (tested). Mirrors are checked the same way (groups, then the groups reversed).
- **Assumption, not checkable from counts:** the device honours barriers when it schedules (Qiskit's documented
  behaviour). The compiled circuit is checked; the pulse schedule is not.

## 2. The job (one job; P6's device rule)

- Device by queue (P6's rules: fewest pending jobs among fez, marrakesh, kingston; ties marrakesh, fez, kingston).
  **[after tonight]:** if tonight's P6/OS2D job shows a reason to fix the device instead (for example the combined
  day-to-day design N), the owner decides.
- Lattice: P5's suspect-qubit lattice (`kim.region(suspect=True)` after the registry's mask); the registry file in
  force at the fetch is hashed and committed before the build.
- Cells (each record interleaves the arms: S t1, D t1, S t2, D t2, ..., so a slow drift falls on both alike):
  - theta 0.4, t = 1..5, S and D (where the correlations were amplified 1.08-1.17x);
  - theta 0.8, t = 1..5, S and D (where the magnetisation error is larger);
  - theta 0, t = 1, 5, S and D (floor; every gate diagonal, ideal <Z> = 1);
  - mirror of theta 0.4 at t = 3, 5, S and D (ideal <Z> = 1);
  - readout patterns (section 3), 7 circuits;
  - ring sentinel.
- 39 circuits, 4000 shots, 46.5 s by the time model (dry run on FakeKingston, FakeFez, FakeMarrakesh; all accepted).
  No mitigation; "stay".
- Answers sealed before sending (`xtalk_answers.py`): per qubit <Z_q> by P5's causal cone, and for every lattice edge
  (<Z_a>, <Z_b>, <Z_a Z_b>) from a statevector of the union of the two cones. On FakeKingston's lattice at t = 5 the
  largest union is 23 qubits (all 137 edges answered with maxq 24; t = 5 took 224 s per theta in the workplace container).

## 3. Readout controls (known answers, same job)

- X on a fixed set of lattice qubits, then measure. Patterns (fixed, no seed): all0, all1, A and B (the two sides of
  the lattice's bipartition, BFS from its smallest label: every edge sees 00, 01, 10, 11), M0, M1, M2 (q mod 3 = 0, 1,
  2). Ideal: <Z_q> = -1 on the set, +1 elsewhere, every connected correlation 0. These states include the X gate's
  error: "readout" here means preparation plus measurement.
- Coverage of all four input states (fake snapshots): every distance-1 and distance-3 pair; distance 2 about 83 %
  (kingston 155 / 186; pairs with a = b mod 3 are not covered). The six-pattern set without M2 covered 54 / 186 at
  distance 2; M2 was added for that reason (geometry only; no device number was read).
- From the device's own counts: per pattern, C_ij = <Z_i Z_j> - <Z_i><Z_j> on the lattice edges (the readout-induced
  correlation; ideal 0), and per edge the 4 x 4 pair readout matrix M (output given input, averaged over the patterns
  that prepare each input).
- **What the amplification could owe to readout.** Independent readout errors only scale a connected correlation
  down (<Z_q>_meas = a_q + b_q <Z_q> gives C_meas = b_i b_j C), so an amplification needs a correlated part. The
  exact (<Z_a>, <Z_b>, <Z_a Z_b>) fix the pair's diagonal distribution; M applied to it gives the correlation readout
  alone would produce, and its ratio to the exact one, R_readout.
- **The model's assumption, measured in the same job:** M does not depend on the neighbours' states. The spread of a
  pair's outputs over patterns that prepare the same input (largest total-variation distance) is reported; in the
  tests a planted spectator-free pair error is recovered (predicted and measured ratio within 0.04), and a planted
  error that leaks to neighbouring pairs shows up as a spread above 0.02.
- What we already know (after the fact, 3 November): the theta = 0 floor gives a connected correlation of about 0.0004
  at distance 1, against an excess of about 0.008 at theta 0.4, t = 4. That floor is the all-|0> state only; states
  with |1> have not been measured, which is why the patterns are needed.

## 4. Judged (proposed thresholds; the declaration fixes them)

1. Sentinel; acceptance (at build).
2. **Q1, does splitting bring the amplification toward 1?** R = mean over (t = 1..5, edges with |exact C| >= 0.01) of
   measured C / exact C at theta 0.4 (the correlations note's ratio), per arm. If R_S - 1 <= 2 SE: **NOT TESTED** (no
   amplification in this job). Otherwise, with closer = |R_S - 1| - |R_D - 1|: **CLOSER** if closer > 2 SE, **FARTHER**
   if closer < -2 SE, **NO CHANGE** otherwise.
3. **Q2, magnetisation error, net of the idle cost:** mean squared error of <Z_q> against exact, theta 0.4 and 0.8
   pooled, t = 1..5: **HELPS** if MSE_D / MSE_S <= 0.8, **HURTS** at 1.25 or more, **NO EFFECT** between. Reported with
   it: the magnetisation error per theta and t per arm; the mirror drop (floor mean minus mirror mean) per arm at
   t = 3, 5 and its difference (+- 2 SE), read under section 0 (not a static-ZZ number); the floor per arm.
4. **Q3, how much of the amplification readout explains:** F = (R_readout - 1) / (R_S - 1) at theta 0.4:
   **READOUT** if F >= 0.75, **PARTLY READOUT** between 0.25 and 0.75, **NOT READOUT** below 0.25; not defined when Q1 is
   NOT TESTED. Marked "indicative" if the mean spectator spread exceeds 0.01 (proposal).
- SE: bootstrap over shots, every cell resampled together, 200 resamples, seed 0 (fixed here, never changed). On a
  fake plumbing run the shot SE of R at theta 0.4 was about 0.008, so the observed 0.08-0.17 excess is far above shot
  noise; but two back-to-back runs already differed by 2.4 SE (home's count, 11/04), so the shot SE understates the
  run-to-run spread. **Proposal:** run this job twice back to back (the day-to-day draft N's first pair), and judge Q1
  and Q2 with the larger of the shot SE and the observed run-to-run spread.

## 5. Reported, not judged

The per-pattern readout correlations (mean and largest |C| on the edges); per-edge R_readout and the spectator spread
map; per-qubit maps of S minus D in SE units; whether the qubits where D helps most are those OS2D's mirror flags or
rule R drops **[after tonight: OS2D's flagged qubits on the same device, if any]**; the queue and the billed time.

## 6. [after tonight] fields

- P6's device and copy, and whether the device rule or a fixed device is used here.
- Whether OS2D's mirror located anything (Q1 of OS2D) and on which qubits, for section 5's comparison.
- Whether the P6 result changes the priority (for example, if P6's magnetisation error is already within 2 SE of exact
  at t <= 5, the theta 0.8 cells carry Q2 alone).

## 7. What it will not settle

The static ZZ is not measured; idle-time losses are not separated from it. Readout crosstalk is modelled pairwise;
three-body readout effects appear only as the spectator spread. One device, one day (two runs if the proposal is
taken): no claim about devices in general.
