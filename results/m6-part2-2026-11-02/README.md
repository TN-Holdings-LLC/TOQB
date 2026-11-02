# OS plan M6, part 2: sentinels 64 minutes after the scan (ibm_kingston, 2026-11-02; reported, not judged)

- **Declaration:** `prereg/drafts-2026-11-02/m6_part2_note.md` (SHA-256 e030951b...f49b), fixed 12:12 CET, TOQB
  482d772. Fetch 12:14:00 CET (calibration 11:54:20 CET, Target 8e2a05a9...). Built by `gpu/m6_practice.py` (psf-os
  eb20501) with the day-3 registry; the circuits of S and V are byte for byte part 1's (`build.json`).
- **Jobs:** S dbk7b1l6p51s73cm3lb0, submitted 12:35:35 CET; V dbk7b4l6p51s73cm3lgg, 12:35:47 CET; 7 s billed each.
  The registry's scan (coverage day 3, job A) was submitted at 11:31:02 CET: 64 minutes earlier, inside the declared
  60-90 minutes. Part 1 ran at 12:03 CET.

## Reported (`part2_compare.json`)

| | part 1 (12:03 CET) | part 2 (12:35 CET) |
|---|---|---|
| S sentinel | DEAD: 3-7, 17, 27-29, 38, 49-55, 59 (mean -0.12) | DEAD: the same 18 qubits (mean -0.10) |
| V sentinel | CLEAN (median 0.44) | CLEAN (median 0.41) |
| sh6 ring mean, S / V | 0.780 / 0.825 | 0.770 / 0.820 |
| parity right, S / V | 0.482 / 0.602 | 0.472 / 0.591 |

- The morning registry still described the device 64 minutes later: the listed run was dead in the same 18 qubits, and
  the ring around it had no weak or dead stretch. Nothing enters the registry as gray.
- **Drift seen on V, above the weak line:** in 32 minutes the sentinel's sites on qubits 29, 30, 31 and 39 fell by
  0.13-0.17 (30: 0.43 -> 0.26; 29: 0.44 -> 0.31; 31: 0.44 -> 0.31; 39: 0.50 -> 0.37). The lowest site, 0.26, stayed
  above the weak line (0.21). These qubits sit next to the listed path [28, 29, 38, 49]. Not a catch by the note; it is
  the kind of change a later sentinel would flag.
- sh6 and the parity moved by 0.005-0.011 on both rings, with the gap between the rings unchanged
  (sh6 +0.045 -> +0.050; parity +0.121 -> +0.119).
