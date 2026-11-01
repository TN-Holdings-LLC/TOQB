# OS plan M3, second form, on ibm_marrakesh, 2026-11-01: Q1 HELPS, Q2 SAME (the ring as a whole is more right; the dead part was too small to count as a run)

- **Declaration:** `prereg/drafts-2026-11-01/qca_m3b_note.md` (SHA-256 e3337f85...1860), fixed 15:48 CET, TOQB 392a7ba.
  Fetch calibration 15:00:50 CET (Target 74186b1d...). Avoid ring from
  `results/two-devices-2026-11-01/marrakesh/avoid/list_after.json` (LISTED [17, 27, 28, 29]; masked (27, 28)).
  Built 15:50-15:51 CET (`log.txt`, `build.txt`, `assemble.txt`); `dryrun/` on the 11:58 CET fetch.
- **Jobs:** S dbjl4956p51s73cl1030 (standard n = 72 ring, D = 12 and 24), submitted 15:52:20 CET, ran 18:20 CET,
  7 s billed; V dbjl4chffo6c73b9s34g (avoid ring, D = 12 and 24), submitted 15:52:34 CET, ran 18:20 CET, 7 s billed.
  Both jobs ran within one second of each other, so the comparison is not split by drift.

## Results (`score_S.json`, `score_V.json`; signal a_j = mean over inputs of <z_in,j Z_j>)

| ring | D | mean signal | per-bit right | usable sites | whole string | dead runs |
|---|---|---|---|---|---|---|
| standard (holds (27, 28)) | 12 | +0.776 +- 0.001 | 0.888 | 72 / 72 | 0.0008 | none |
| avoid ring | 12 | +0.816 +- 0.001 | 0.908 | 72 / 72 | 0.0040 | none |
| standard | 24 | +0.643 +- 0.001 | 0.821 | 72 / 72 | 0.0000 | none |
| avoid ring | 24 | +0.694 +- 0.001 | 0.847 | 72 / 72 | 0.0000 | none |

## Judged at D = 12 (by the note)

- **Readable:** V's mean 0.816 >= 0.05.
- **Q1:** V - S = +0.040 +- 0.002 (2 SE = 0.004): **HELPS**.
- **Q2:** usable sites 72 -> 72: **SAME**.
- **Sentence fixed in advance:** the ring as a whole is more right; the dead part was too small to count as a run.

## Reported

- **D = 24:** V - S = +0.052 +- 0.002; usable 72 -> 72; per-bit right 0.821 -> 0.847.
- **Where the gain comes from (after the fact, not judged):** the two rings share 62 qubits. On those, S 0.802 and
  V 0.808 at D = 12 (0.670 and 0.682 at D = 24): almost the same. The 10 qubits only in S
  (48, 47, 46, 45, 37, 25, 26, 27, 28, 18) average 0.615 (D = 12) and 0.472 (D = 24); the 10 only in V
  (38, 32, 33, 34, 35, 19, 15, 14, 13, 12) average 0.866 and 0.769. The whole gain is the swapped stretch.
- **The listed path today:** on the standard ring at D = 12, 37 0.54, 25 0.29, 26 0.56, 27 0.72, 28 0.82; at D = 24,
  37 0.35, 25 -0.06, 26 0.38, 27 0.53, 28 0.73. The weakest standard site is 48 (0.04 at D = 12, 0.06 at D = 24),
  alone, so not a run. The 12:24 CET echo dead run 37-25-26-27-28 does not show as a run in this computation; 25 is
  the weak point that remains.
- **Weakest avoid-ring sites (D = 12):** 29 0.50, 43 0.53, 83 0.54, 64 0.57, 41 0.62. At D = 24 site 43 is -0.07.
- **Compared with M3 on kingston (INCONCLUSIVE):** the period-6 computation reads at n = 72 after 12 and 24 layers
  (0.78-0.82 and 0.64-0.69), where kingston's period-n computation at n = 40 after 40 layers read 0.01-0.02.
- **Billed:** 14 s for both jobs.

## Meaning for the OS plan

Avoiding the listed path makes a forward (non-mirror) computation more right on this device and day: +0.04 at
D = 12, +0.05 at D = 24, about 5 % and 8 % of the signal, all from the replaced stretch. Nothing became unusable on the
standard ring, so the gain is in accuracy, not in usable width. The allocator's value is not only for the echo.
