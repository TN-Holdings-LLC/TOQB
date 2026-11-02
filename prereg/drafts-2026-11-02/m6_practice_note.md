# OS plan M6 (sentinels, part 1) and practice problems P2, P3 on ibm_kingston (home, 2026-11-02)

**Why.** psf-os (TN-Holdings-LLC/psf-os eb20501) now builds user jobs with a sentinel and has practice problems with
exact answers. Both have been run on fake devices only. The workplace's draft for M6 (`m6_sentinel_note_DRAFT.md`) is
taken as part 1 below; part 2 (a later submission time) is not in this note.

**Built by** `gpu/m6_practice.py` (psf-os's own functions; no new rule or threshold) from one new fetch of
ibm_kingston and the registry `results/coverage-days-2026-11-02-day3/list_after.json` (LISTED [28, 29, 38, 49],
[11, 10, 9], [87, 86, 85]; masked couplers (9, 10), (29, 38), (85, 86)). Submitted with TOQB's `s2rc_device submit`;
every manifest says "stay". 1000 shots, options off. Three jobs, 26.1 s by the time model (dry run on the 11:19 CET
fetch of 2 November: all records accepted; S and V on TOQB's standard and avoiding n = 40 rings, P on the standard
n = 20 ring; local noiseless run with the sentinel at the Clifford point: sh6 1.000, parity 1.000, CLEAN).

| job | ring | records | circuits |
|---|---|---|---|
| S | standard n = 40 (holds [28, 29, 38, 49]) | sh6 (D = 12), cluster parity, sentinel (echo D = 24, h 0.6) | 20 |
| V | n = 40 placed around the registry | the same three | 20 |
| P | standard n = 20 | kicked Ising forward, hz 0, h 0.3, L = 4 and 8 | 16 |

**Change from the workplace's practice set.** P3 uses h = 0.3, not 0.6: at h = 0.6 the exact <Z_j> are near 0 after
4 steps (mean square 0.009 at L = 4, 0.0001 at L = 8), so a fully mixed output would score as well as the right one.
At h = 0.3 the mean square is 0.60 (L = 4) and 0.42 (L = 8), and the circuit is still not Clifford.

## Judged

1. **M6, sentinel on job S (the sure case):** DEAD expected (the known run on qubits 3-59).
   - DEAD: *the sentinel sees the known dead run in the user's job.*
   - CLEAN or WEAK: *the sentinel missed a known dead run* (part 2 is not run).
2. **M6, sentinel on job V:** CLEAN expected.
   - CLEAN: *the ring placed around the registry was clean at the job's time.*
   - WEAK or DEAD: *a defect not in the morning's registry was present at the job's time*; its positions are reported
     and enter the registry as gray. A run within 0.05 of the weak line is reported as borderline, not a catch.
3. **sh6 on kingston n = 40 (M3, third form):** ring mean V - S, 2 SE: HELPS / NO EFFECT / HURTS; usable sites V - S:
   WIDER (>= +3) / SAME / NARROWER. Readable only if V's mean is 0.05 or more (else INCONCLUSIVE).
   - HELPS and WIDER: *on a ring with a dead run, avoiding it makes a forward computation right on more of the ring.*
   - Otherwise the verdicts are reported as they come.
4. **P2, cluster parity n = 40:** fraction of right parities, V - S, 2 SE (each from 4000 shots): HELPS / NO EFFECT /
   HURTS. If both are within 2 SE of 0.5: UNREADABLE (a weight-40 parity is near the readout floor).
   - HELPS: *avoiding the dead path helps even a one-layer computation.*
   - NO EFFECT: *the defect does not touch a one-layer computation; avoiding pays with depth.*
5. **P3, kicked Ising n = 20:** per L, the mean squared error of <Z_j> against the exact answer, against the error of
   a fully mixed output (the mean square of the answer): READS if the error is at most half of it, else DOES NOT READ.
   Reported: the error per site and input, and how much of the answer is recovered.

## Reported, not judged

Every sentinel's per-site signal, dead and weak runs; sh6 per-bit right fraction; billed time. Part 2 of M6 (a later
submission time) needs its own note.

**Stop.** One run of the three jobs.
