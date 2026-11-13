# The Clifford twin: a ruler that needs no answer (home, 2026-11-13; desk only, no device)

Owner 10:53 JST: "OS として不足しているもの" item 1 (the OS cannot say how far to trust a circuit whose answer is not
computable). Module: psf-os `psf_os/twin.py` (+ `tests/test_twin.py`, 4 tests).

## What it is

The compiled circuit with every RZ angle rounded to the nearest multiple of pi/2; CZ, SX, X and their order kept.
RZ is virtual on Heron, so the twin runs the same physical pulses as the user circuit. All its gates are Clifford, so
its per-qubit <Z> is exact at any size (stabilizer simulation). The device's kept share on the twin, r_twin, is meant
to estimate the kept share r on the user circuit; with a mainly multiplicative error READS is r >= 0.293
(`notes/paper9/r_thread_2026-11-13`).

## Desk checks on compiled circuits from the records

| record | circuit | CZ | same non-RZ schedule | twin's exact Z |
|---|---|---|---|---|
| hubbard-2026-11-11 (fez) | L20, 6 steps, U 4 | 1152 | yes | all +-1 (20 of 40 are -1) |
| xx91-2026-11-12 (fez) | 91 qubits, pi/4, 20 steps | 3600 | yes | all +-1 (45 of 91) |
| ohm-kingston-2026-11-12 | A1, 6 cycles, string 0 | 702 | yes | all +-1 (19 of 40) |

Also: L20 2 / 4 steps (U 4 and the U 0 ruler) and XX91 pi/4 4 / 12 steps: all +-1 (`twin_probe.py`).
So each twin is a full-signal ruler (mean square 1) with about half the qubits ending in 1.

## Why the existing rulers are not twins

- XX91's theta pi/2 ruler tracked the pi/4 circuit's r (0.81 / 0.82, 0.68 / 0.69, 0.50 / 0.47, 0.33 / 0.31), but its
  pulses differ: 2342 against 3104 non-RZ instructions at 4 steps (fewer SX).
- Hubbard's U 0 ruler did not track U 4 (r falls with an e-fold of 30 against 71 layers): 1456 against 1686 SX and 132
  against 152 X, with barriers. The twin removes both differences.

## Not shown yet

Whether r_twin follows r on a device: needs a declared run (`prereg/drafts-2026-11-13/twin_DRAFT.md`). The twin sees
the shrink only; shape errors (Hubbard U 4, 6 steps: residual as large as the shrink) are outside it.
