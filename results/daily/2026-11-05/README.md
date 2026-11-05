# Daily record, day 1: 2026-11-05

- Rules: `prereg/daily/standing_rules.md` (SHA-256 64846a60...8aef4f3, f54f3d9). Problems: FX-A (fixed), D02 (new).
- Queue 11:19 CET: marrakesh 1, fez 0, kingston 138 -> marrakesh and fez. psf-os fetch 11:19 CET; built 376d0ee
  (marrakesh: D02 moved by the entrance to (4, 0) around the day's new failed qubits 46, 73).
- Jobs: marrakesh dbm5hgd8mdtc73d7bang (sent 11:21:52 CET), fez dbm5hid8ft8s738u88g0 (11:22:00 CET); both DONE.
- Scored by `gpu/daily_score.py` (unchanged); lines in `results/daily/RECORD.md`.

## Reported

- FX-A repeats the 2026-11-04 result within 0.002 on both devices (marrakesh -0.024 against -0.022; fez -0.043
  against -0.041): the first day-to-day point.
- D02 (P6 form, 32 qubits, RZZ(1.0) as 2 CZ, 256 CZ) DIFFERS on both (-0.111, -0.147) but BEATS the trivial guess;
  P6 on 2026-11-04 had missed at t 4 by a similar amount. Share within 2 SE: 3 % and 6 % (FX-A 55 % and 45 %).
