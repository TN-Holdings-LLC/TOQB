# Three mirrors: a prototype in the simulator (workplace, 2026-11-09; owner's idea "三面鏡"; not declared, no device)

Code: `three_mirrors.py` (criteria C1-C3 fixed in its header at 01:39 CET, before any run), `pod_three_mirrors.py`
(the same readings split over many cores), kit for VS Claude's POD run (`指示書_三面鏡_2026-11-09.md`, `run_pod.sh`).

## The idea

Front mirror F = today's mirror (compiled U, barrier, U^dagger). U is compiled once (rzz_exact, RuleCompiler) and split
by instruction: left L = everything that touches no bridge qubit (x- and z-bonds, swaps, RX), right Rt = everything that
touches a bridge (the y-bonds); each mirrored without optimisation, so CZ(F) = CZ(L) + CZ(Rt). R reads the sites with
no gate. If the two parts' errors act independently, F * R ~ L * Rt; delta = F - L * Rt / R shows how much they act on
each other. (Splitting before compiling was tried first and dropped: the compiler merged bridge gates that the row
gates keep apart in U, 24 CZ instead of 48.)

## Results (fez 11-08 record; 4x2x2 Ising, theta 0.6; uniform depolarizing p2 0.005, p1 0.0002, readout 0.015;
300 trajectories; zeta = an always-on ZZ on every coupler among the touched qubits after each CZ layer, a fixed
assumption, noise-free; `line_fez1108.log`, `fold_fez1108.log`)

| layout, t | CZ F / L / Rt | zeta 0: delta | zeta 0.005 | zeta 0.02 |
|---|---|---|---|---|
| line, t 1 | 120 / 72 / 48 | +0.006 +- 0.008 (+0.7 SE) | -0.002 +- 0.008 | **-0.022 +- 0.008 (-2.9 SE)** |
| line, t 2 | 240 / 144 / 96 | -0.012 +- 0.012 (-1.0 SE) | -0.031 +- 0.012 (-2.6 SE) | **-0.106 +- 0.011 (-9.7 SE)** |
| fold, t 1 | 216 / 168 / 48 | +0.011 +- 0.011 (+1.0 SE) | -0.017 +- 0.011 | **-0.061 +- 0.011 (-5.7 SE)** |

- **C1 (gate-local noise only, |delta| <= 2 SE): met** in all three (within 1.0 SE) at 300 trajectories. **Superseded
  by the POD run below: at 2000 trajectories C1 holds at t 1 only.** But the trajectory SE (0.008-0.012)
  is not small enough to show that the gate-local delta is zero rather than about +-0.01; the POD run (2000
  trajectories) is for that.
- **C2 (zeta 0.02 gives delta < 0 beyond 2 SE): met** in all three, growing with depth (line: -0.022 at t 1, -0.106 at
  t 2) and with the circuit's length (fold t 1: -0.061). zeta 0.005 shows at line t 2 (-2.6 SE) only.
- **C3 (device time at most 1.5 x): met by the shot-noise estimate** (sites independent, v = (1 - m^2)/16 per shot,
  F at today's 4000 shots, L, Rt, R added): resolving zeta 0.02's delta needs about 160 shots per added circuit at line
  t 1 and fewer at t 2 (time x 1.04). Caveat: the same estimate would also "resolve" the gate-local delta of line t 2
  (-0.012) with about 700 shots, so a device delta must be read against the gate-local value, which the POD run pins.

## What delta can and cannot say

- Static ZZ shows in delta because the row qubits sit in superpositions (after RX) while the bridge part runs; run
  apart, the parts never see each other's layers. Idle errors (relaxation and dephasing while other qubits work)
  act the same way: three mirrors tell "the parts act on each other", not which of the two it is.
- The right mirror alone barely moves with zeta (0.951 -> 0.953): the bridge part is diagonal apart from the bridges'
  H, so a ZZ does not change its Z readings. The bridges' own losses show in Rt; the interaction shows in delta.
- Report only. Nothing here corrects an answer or fits a noise model (owner's rules). Uses as our own check (like the
  floor and the mirror) would be: report beside the verdict, and the place choice (rule "top" style), if the owner
  decides.

## Open

- The POD run (VS Claude): line and fold, t 1-4, zeta 0 / 0.005 / 0.01 / 0.02, 2000 trajectories.
- Heisenberg (TOQB `gpu/heis3d.py`) is not in psf-os; the simulator's Heisenberg gap (15-28 %) is where delta would
  matter most. A three-mirror run of the Heisenberg circuits needs their compiled form split the same way.
- A device test needs a declaration (owner).

## POD run (VS Claude, 2026-11-09 02:40-05:32 CET; `pod/`; 4 CPU pods x 16 cores, $4.56; scripts unchanged, a venv
because the image refused pip; split by layout and t, seeds by chunk index, so the rows equal one run; merged file
checked against the four parts here: 32 rows, 0 differences)

Line and fold, 4x2x2, theta 0.6, t 1-4, zeta 0 / 0.005 / 0.01 / 0.02, 2000 trajectories. delta (SE units):

| layout | zeta 0 (gate-local only) t 1 / 2 / 3 / 4 | excess over zeta 0 at zeta 0.02, t 1 / 2 / 3 / 4 |
|---|---|---|
| line | -0.001 (-0.3) / -0.020 (-4.3) / -0.069 (-11.5) / -0.131 (-19.2) | -0.020 (-4.8) / -0.087 / -0.121 / -0.106 |
| fold | +0.004 (+1.0) / -0.025 (-4.1) / -0.077 (-11.1) / -0.116 (-16.9) | -0.053 (-9.1) / -0.133 / -0.082 / +0.079 |

At zeta 0.01, the excess is -0.003 (-0.8 SE) for line t 1 and -0.017 (-2.9 SE) for fold t 1.

### Verdict by the criteria fixed at 01:39 CET

- **C1: met at t 1 only** (line -0.3 SE, fold +1.0 SE); **not met at t 2-4** (-4.1 to -19.2 SE). With gate-local noise
  alone the product rule fails more and more with depth: an error in one part is spread by the other part's
  entangling gates in the front mirror, which the side mirrors, run apart, never do. So at t >= 2 a negative delta
  does not by itself mean crosstalk or idle errors; reading it would need a baseline from a noise model, and fitting
  that model to the device is not allowed (owner's rules). The 300-trajectory prototype could not see this
  (SE 0.012).
- **C2: met** (zeta 0.02 below 2 SE everywhere; also as an excess over zeta 0 except fold t 4, where F and L have
  fallen to 0.17 / 0.22 and delta saturates).
- **C3: met at t 1 only**, for a large ZZ: the zeta 0.02 excess (line 0.020, fold 0.053) needs about 200 / 35 shots per
  added circuit (time x 1.05 / x 1.01); a zeta 0.01 excess is out of reach for line t 1 (the front mirror's own 4000
  shots are too noisy) and needs about 320 shots for fold t 1.

### What remains usable

The three mirrors work as an interaction check **at t = 1 only**, where gate-local noise leaves delta at zero
(|delta| <= 0.004). That is the depth at which rule "top" already runs its own probes, so the three mirrors would sit
there as one more own check (report beside, or the place choice, if the owner decides), sensitive to a static ZZ of
about 0.02 rad per CZ layer (fold: about 0.01). The device's real ZZ is not known here (no calibration number is read).
For t >= 2 the design as fixed does not separate "interaction" from "error spreading"; a different split (e.g. by time
segments rather than by part) would be a new design, not tried.

Time note for later estimates: circuits with zeta > 0 took 8-12 times longer than zeta 0 (the ZZ unitaries per layer).
