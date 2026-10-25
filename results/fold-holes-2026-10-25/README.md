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

**Not done.** The cycle is found here by VF2 (a search; prototype only): a formula placement (the outline of a fixed
row or cluster of cells, avoiding failed elements by rule) is still to be written. Not in any compiler; not run on a
device; one random model per n.
