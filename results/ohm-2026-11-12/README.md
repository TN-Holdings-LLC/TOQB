# Where Ohm's law appears, raw, 6 cycles: ibm_fez, 2026-11-12 (prereg/ohm_2026-11-12.md)

- Declaration a618f1f, pushed before the queue read (head 531be78 on GitHub); queue read 11:19:15 CET (marrakesh 1,
  fez 1, kingston 4). marrakesh: the ring sentinel does not build -> ibm_fez.
- Build: 508 circuits, 158.4 s by the model; 40 qubits; CZ 234 / 468 (A0, 3 / 6 cycles) and 351 / 702 (A1, A2).
  circuits_sha256 3323c0fc... equal to the home try-build whose pre-run check passed (`ibm_fez/check_trybuild.txt`,
  168 circuits, worst 7.3e-8) -> the PASS carries over.
- Answers sealed as declared (`ohm_answers.json` sha256 5580b676...), released in `answers/`.
- Job dbqp8vgk09pc73atljf0, submitted 11:26:55 CET (calibration 10:58 CET), DONE; DD and twirling off; 1000 shots.
- Files: `job/circuits.qpy.gz` and `runs/*.qpy.gz` are gzipped (the plain circuits.qpy is 127 MB); `gunzip` restores
  them byte for byte.

## Declared verdicts (`gpu/ohm_score.py`): transferred magnetization M per circuit, 28 circuits per arm and time

| arm | cycles | CZ | MSE of M / mean square | verdict | AGREES (0.2 quanta) | per-qubit Z READS |
|---|---|---|---|---|---|---|
| A0 free | 3 | 234 | 1.80 / 0.77 | DOES NOT READ | 0 | 28 / 28 |
| A0 free | 6 | 468 | 4.10 / 2.61 | DOES NOT READ | 0 | 28 / 28 |
| A1 isotropic | 3 | 351 | 2.16 / 0.52 | DOES NOT READ | 0 | 28 / 28 |
| A1 isotropic | 6 | 702 | 4.91 / 1.19 | DOES NOT READ | 0 | 28 / 28 |
| A2 + field | 3 | 351 | 2.34 / 0.40 | DOES NOT READ | 1 | 28 / 28 |
| A2 + field | 6 | 702 | 4.86 / 0.67 | DOES NOT READ | 0 | 28 / 28 |

## Prediction (written before the data)

- "Every arm READS at 3 and 6 cycles": **failed** (none of the six reads M).
- "The exponents of W keep the exact ordering A0 > A1 > A2 on the device": held (device 0.758 / 0.625 / 0.519; exact
  0.972 / 0.659 / 0.451). See the next section before reading anything into it.

## Beside (not judged, never used to correct)

- W, device against exact: A0 1.94 / 0.71 and 3.28 / 1.39; A1 1.95 / 0.60 and 3.01 / 0.95; A2 1.93 / 0.52 and
  2.77 / 0.71 (3 / 6 cycles). For reference, W of a fully mixed state (every Z = 0) is 5.5 for these strings. The
  device W lies between the exact value and full mixing: noise mixes spins and looks like extra transport, as the
  declaration's limits say. Every per-qubit Z reads, but M sums 20 right-half errors that point the same way while the
  exact M is small.
- A0 has fewer CZ than A1 and A2, so the A0 / A1 ordering mixes physics with different noise. A1 and A2 have the same
  CZ (the field is virtual): their device exponents 0.625 / 0.519 keep the exact order (0.659 / 0.451) with half the
  exact gap. Shot errors of these exponents are not computed here.
- Drift D (exact about 0): device -0.07 to -0.23 (decay towards |0>). Floor 0.965-0.967; mirror 0.67 / 0.44 (A0),
  0.57 / 0.29 (A1), 0.58 / 0.31 (A2) at 3 / 6 cycles.

## Reproduce

`python reproduce.py ohm-fez-2026-11-12`.
