# Folding big: the ring on a device cycle with idle qubits ("holes") (analysis, compile only; 2026-10-25)

**Idea (owner, 2026-10-25: fold the map a few big times instead of many small ones).** The zipper's 5n/2 - 4 CZ per
layer is the least for a ring laid on a *line*; the line is our own restriction. Heron's heavy-hex has cycles of
12, 20, 24, 28, 32, ... qubits (the outlines of rows and clusters of its cells; checked on FakeMarrakesh and
FakeTorino for every length up to 40). A ring of n is laid on the shortest cycle of m >= n qubits; the m - n spare
qubits ("holes") start in |0>. Per layer: CZ on every ring edge already adjacent; for each hole, the ring node before
it moves into it (CX a->hole, CX hole->a: since the hole is |0>, a's state moves and a's old site becomes |0>), then CZ
across. **n + 2(m - n) two-qubit gates per layer**: for n >= 20 at most n + 6, a constant extra, against the zipper's
3n/2 - 4.

**Correct.** `holes_check.txt` (`holes.py`): the hole schedule equals the logical ring circuit (every logical
qubit's distribution, statevector, difference 0) and every hole returns to |0>, for n = 5-11 on cycles of 6-12, L =
1-4. `verify_dev.txt` (`verify_dev.py`): compiled for the `snapshot:marrakesh` Target (TOQB's model circuit, n = 9,
10, 11 on a 12-cycle, L = 2, 4), every clbit's P(1) equals the logical model's to 4e-15.

**Cost** (`device_cmp.py` -> `holes_cost.json`; TOQB `toqb.scale_cost` with the a25 front end -> `sc.json`; one model
circuit per n, L = 16, random angles, `snapshot:marrakesh`, durations from the Target's schedule):

| n | holes: CZ / us (cycle m) | zipper (a25): CZ / us | Qiskit level 2: CZ / us / active qubits | item 31: CZ / us |
|---|---|---|---|---|
| 9 | 240 / 10.0 (12) | 304 / 11.7 | 297 / 29.9 / 12 | 432 / 18.0 |
| 10 | 224 / 8.3 (12) | 336 / 11.7 | 506 / 48.2 / 14 | 448 / 18.0 |
| 11 | 208 / 7.3 (12) | 384 / 11.7 | 493 / 44.0 / 16 | 528 / 18.0 |
| 13 | 434 / 9.7 (20) | 464 / 11.7 | 571 / 57.1 / 20 | 640 / 18.0 |
| 14 | 416 / 9.4 (20) | 496 / 11.7 | 530 / 52.3 / 20 | 656 / 18.0 |
| 15 | 400 / 10.1 (20) | 544 / 11.7 | 699 / 69.3 / 24 | 736 / 18.0 |
| 16 | 384 / 8.8 (20) | 576 / 11.7 | 968 / 99.9 / 16 | 784 / 18.0 |
| 17 | 368 / 7.7 (20) | 624 / 11.7 | 629 / 59.9 / 24 | 848 / 18.0 |
| 18 | 352 / 7.3 (20) | 656 / 11.7 | 639 / 56.0 / 22 | 864 / 18.0 |
| 19 | 336 / 6.9 (20) | 704 / 11.7 | 967 / 95.5 / 32 | 944 / 18.0 |
| 21 | 432 / 7.7 (24) | 784 / 11.7 | 894 / 86.3 / 32 | 1056 / 18.0 |
| 22 | 416 / 7.3 (24) | 816 / 11.7 | 652 / 60.4 / 28 | 1072 / 18.0 |
| 23 | 400 / 6.9 (24) | 864 / 11.7 | 1043 / 96.2 / 33 | 1152 / 18.0 |
| 25 | 496 / 7.3 (28) | 944 / 12.4 | 1571 / 155.3 / 38 | 1264 / 18.0 |
| 26 | 480 / 7.1 (28) | 976 / 12.4 | 1412 / 128.2 / 45 | 1280 / 18.0 |
| 30 | 544 / 7.1 (32) | 1136 / 12.4 | 2102 / 187.6 / 40 | 1488 / 18.0 |

- **Vanity:** at n = 19-30 the hole schedule has 0.46-0.55 of the zipper's CZ and 0.26-0.64 of Qiskit's; its
  duration is 0.57-0.66 of the zipper's and 8-27 times shorter than Qiskit's.
- **What a device user needs, not yet known:** these are gate counts and scheduled durations on a Target, not results
  on hardware. The hole schedule uses m - n more qubits (up to 7 here), whose errors enter through the moves; a
  hole that is not exactly |0> passes its error on.
- Where a cycle of exactly n exists (n = 12, 20, 24, 28, 32), every method needs n CZ per layer and the holes add
  nothing. For n below 9 the zipper is cheaper (n = 6: 11 against 18).

**Placement by formula (2026-10-25, later): `fold_place.py`, `fold_place.txt`.** The heavy-hex is read off the coupling
graph (bridges: two neighbours not consecutive; rows: what is left without them; cells: between consecutive bridges
of a row pair). The cycle is the outline of a fixed shape of cells: k cells side by side (8k + 4 qubits: 12, 20, 28),
or k cells plus k2 cells side by side in the next row pair down (24, 32, 36, ...); the shortest length m >= n, and
among those the first shape in a fixed order (row pairs top to bottom, cells left to right) whose qubits and couplers
all work. No search over mappings and no error value decides. On FakeMarrakesh, FakeKingston, FakeFez (Heron r2) and
FakeTorino (r1): lengths 12, 20, 24, 28, 32, 36, every cycle on the devices' couplers; n up to 36 (larger n needs a
third family, not written). The cost table above used VF2's cycles of the same lengths, so its counts hold.

**As a TOQB arm (2026-10-25, later): `fold:template` (`toqb/fold.py`, `tests/test_fold.py`).** The hole schedule on
the formula-placed cycle, built and transpiled once per structure (level 1, layout fixed, no routing), angles bound
per call, as `qiskit:L:target:template` (single-qubit runs are not merged into closed-form angles as PSF-Zero's
templates do). Tests: exact against the logical model on every clbit (n = 9, 10, 11; L = 2, 4; bound twice), n + 2(m -
n) two-qubit gates per layer, a failed coupler avoided, other circuits refused.

**Signal kept on the twin and the stand-in** (`twin_lam.py`; one random model, 12 random inputs, L = 8, 128
trajectories; z ~ lam z_noiseless + delta; cloud container, CPU):

| n | twin lam: fold / zipper | stand-in lam: fold / zipper | two-qubit gates: fold / zipper | us: fold / zipper |
|---|---|---|---|---|
| 9 | 0.636 / 0.377 | -- | 120 / 152 | 6.4 / 7.2 |
| 10 | 0.699 / 0.357 | 0.652 / 0.427 | 112 / 168 | 5.5 / 7.2 |
| 11 | 0.843 / 0.439 | 0.812 / 0.448 | 104 / 192 | 5.0 / 7.2 |

On both noise models the hole schedule keeps 1.5-2.0 times the zipper's signal at L = 8 (shots for the same
precision scale as 1/lam^2: about 2.3-3.8 times fewer). Correlation with the noiseless model 0.994-0.999 against
0.965-0.982. Qiskit and L = 16 were not run here (14-16 active qubits and 16 layers are slow on this CPU; for the GPU).
The twin and the stand-in are TOQB's models of a 2026-10-13 calibration, not a device.

**Not done.** Not in PSF-Zero's compiler; not run on a
device; one random model per n.
