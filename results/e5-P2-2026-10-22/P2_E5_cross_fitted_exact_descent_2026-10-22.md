# P2. Prototype E5: E4's exact step, taken only when it helps points it was not chosen on (workplace, 2026-10-22, 06:15 CEST)

**Status.** This is a prototype, made at the owner's request ("build a prototype E5"). It was run in a toy simulator
only, as a report. Nothing here touches the device run, the W13 match or any pre-registration.

## What E4's defeat taught, and E5's answer

E4 takes, for each parameter, the exact minimum of the estimated training Brier. That step overshoots in two ways:

- it follows the twin's noise (the winner's curse; W12, F5 of the fruit match);
- it follows the 64 training points' quirks (170-330 parameters).

As a result, the test CE stalls or rises after the first sweep, and C0 at its full budget beat E4's last sweep on 8 of
9 tasks. A brake with a constant (a learning rate, a penalty, stopping at k sweeps) would be a tuned constant.

**E5's brake has no constant.** The training points are split by a fixed rule into fold A (even index) and fold B (odd
index), each with its own independent trajectory halves.

| step | formula |
|---|---|
| coefficients | C_A, C_B: E4's unbiased split-half Brier coefficients on each fold |
| fold minima | u_A = argmin C_A, u_B = argmin C_B (the exact quartic) |
| cross-fitted gain | v = dL_B(u_A) + dL_A(u_B), each term out of fold |
| step | if v < 0: u* = argmin (C_A + C_B), E4's step on all points; else 0 |

- **Cost:** the same as E4's per sweep, so W11's budget points are unchanged.
- **Stops by itself:** a parameter whose gain does not carry across folds stops moving, so training stops when it
  stops generalising.

## Toy run (report only; `toy_e5.py`)

**The simulator.** A numpy statevector of TOQB's model: data re-uploading on a CZ ring, read from qubit 0. It matches
Qiskit to 5.6e-16 (`simcheck.py`).

**The task.** n = 8 and L = 10 (168 parameters, close to S2R's 170 at L 8). 64 training and 500 test points. Teachers
7, 8 and 9 at angle 1.0, gap 0.2. Four sweeps.

**The toy twin.**

- z = 0.33 · z_ideal + 0.05: the global shrink, read off the device day's PSF L 8 twin.
- Gaussian trajectory noise, (1 − z²) / 16 per half.
- E4 and E5 receive the same total trajectories.

**This is not TOQB's noise and not a device.**

Test CE (raw) / noiseless accuracy / parameters moved, at sweeps 0 to 4:

| teacher | method | sweep 0 (θ = 0) | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|---|
| 8 | E4 | 0.572 / 0.74 | 0.563 / 0.78 / 168 | 0.616 / 0.72 / 168 | 0.665 / 0.54 / 168 | **0.671 / 0.51** / 168 |
| 8 | E5 | 0.572 / 0.74 | 0.566 / 0.75 / 66 | 0.565 / 0.75 / 65 | 0.573 / 0.73 / 67 | **0.570 / 0.70** / 61 |
| 9 | E4 | 0.549 / 0.76 | 0.537 / 0.81 / 168 | 0.551 / 0.77 | 0.561 / 0.79 | **0.568 / 0.78** |
| 9 | E5 | 0.549 / 0.76 | 0.536 / 0.81 / 69 | 0.541 / 0.81 | 0.547 / 0.82 | **0.541 / 0.81** |
| 7 | both | 0.756 / 0.41 | the task is not learnt by either (noiseless accuracy about 0.5); not informative | | | |

**Reading.**

- **E4 degrades with every sweep**, as on the stand-in. On teacher 8 it ends well below doing nothing (CE 0.671
  against θ = 0's 0.572).
- **E5 holds.** It moves about 40 % of the parameters per sweep, and its CE stays within 0.01 of its first sweep.
- At sweep 1 the two are equal. E5 does not learn more than E4's first sweep; it keeps E4 from destroying it.
- **Vanity:** "E5 does not degrade: teacher 8 CE 0.570 against E4's 0.671 after 4 sweeps".
- **Essential:**
  - Neither method gets much beyond θ = 0 in this toy: the gain is at most 0.013 in CE.
  - E5 fixes E4's late collapse (the peel), not its early loss to C0 (the fruit zone).
  - It rests on two informative teachers and toy noise.

## Next, if wanted (each declared before it runs)

1. **E5 as a variant of TOQB's E4 runner** (`"variant": "e5"`, as E4v in W13), on the real twin and the stand-in.
   W11's frozen scorer works unchanged.
2. **E5 against C0 at C0's full budget (the peel).** That is where E4 lost 8 of 9 tasks and where E5's stability
   should show. The fruit zone is unlikely to change.
3. **The undamped readout** (C r9 item 3) on top, as a report. It is label-free and touches neither method.

## Files

| file | content |
|---|---|
| `e5.py` | `e5_step`, `e4_step`, `folds`, and E4's formulas, standalone |
| `toy_e5.py` | the toy run, with its output `toy_n8L10.json` |
| `simcheck.py` | the simulator checked against Qiskit |
