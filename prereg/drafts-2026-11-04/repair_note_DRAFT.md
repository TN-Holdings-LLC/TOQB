# DRAFT (not declared): the self-repair chain on a device, two jobs in a row, the problem on the copy chosen without the chain against the copy chosen with it (workplace, 2026-11-04)

Status: a draft for home and the owner (task R). The owner's decision of 2026-11-04 07:57 CET: the chain (find,
confirm, avoid, re-place, verify) is not counted as search, provided its rules are fixed here and applied mechanically;
build it and test its effect. The owner's decisions of 2026-11-04 08:24 CET (`owner_decisions_2026-11-04.md`): confirm
rule **(b)**, release by **expiry (7 days)**, **tonight's OS2D job is job 1** and job 2 is sent right after it. **Only
the thresholds wait for tonight's results** (field marked **[after tonight]**). Home's procedure for tonight:
`notes/repair_2026-11-04/指示書_ジョブ2_2026-11-04.md`.

Tools: psf-os 1250c90 `psf_os/repair2d.py` and `psf-os repair2d` (3 tests); TOQB `gpu/repair_job2.py`,
`notes/repair_2026-11-04/` (`ledger_from_job.py`, `repair_score.py`, `repair_posthoc.py`, `dry_counts.py` for dry runs
only). Job 1 is built by the existing `gpu/os2d_device.py`.

## 1. Honest expectation (stated first; the workplace's five points)

1. **Readout faults move within hours.** A flag from job 1 may be stale by job 2. After the fact (section 6), of 5
   qubits read DEAD at 06:08 on 3 November none was DEAD at 12:09; of 11 excluded by rule b before the 17:04 job, one
   was DEAD again.
2. **A device's first job cannot be helped.** The chain needs an earlier job. Inside one job only rule R acts, and it
   is a scoring drop (the qubit is left out of the score), not a repair. fez's misses on 3 November came on its first
   job.
3. **A static ZZ is not seen by the mirror.** A mirror can cancel it, so the mirror kind cannot flag it; the floor kind
   does not see it either (it acts on superpositions only).
4. **The patch avoids; it does not correct.** The chain moves the problem to another copy. It does not compensate an
   error, and the copy it moves to has its own faults.
5. **A repair chosen after seeing the same job would be a choice after the fact.** The chain acts only on later jobs;
   job 2's comparison is fixed before job 2 is built (the chain's log is hashed and committed first).

And from the geometry: the P6 patch has **6 copies** on a Heron r2 lattice, and the chain can only flag qubits of the
copy job 1 used. On the fake snapshots (no registry) 3 copies qualify on kingston and none on fez or marrakesh. So B
often has no other copy to go to: then the test is NO COPY and is reported so.

## 2. The chain (rules fixed by this declaration)

| step | input | rule |
|---|---|---|
| find | job 1's floor (theta_x 0 at t = 1, 5) and mirror (t = 3, 5); the ring sentinel | per qubit, the ledger's three-valued reading with the job's own line (rule R's form: median - max(5 x 1.4826 MAD, 0.05) for the floor; median + the same for the mirror's d = floor - mirror): DEAD if beyond the line by 3 SE, HEALTHY if inside by 3 SE, UNCERTAIN otherwise. The ring sentinel goes to the registry under its existing rules (unchanged) |
| confirm | the test's ledger (section 3: job 1's readings only) | **rule (b)** (owner, 08:24 CET): DEAD in one job in one kind (value + 3 SE < line for the floor; value - 3 SE > line for the mirror's d). Rule (a), two different jobs, is not used here |
| avoid | the confirmed qubits | marked failed in a copy of the device record (after the registry's mask) |
| re-place | `lattice2d.place`, P6's six copies in P6's order | the first copy with no failed, masked or suspect element; none qualifying -> NO COPY |
| verify | job 2 | section 3 |
| release | | **expiry** (owner, 08:24 CET): an exclusion lapses 7 days after its last DEAD (the ledger's rule). The early release (a later HEALTHY reading) is not used |

- Each run of the chain writes a log: the readings, each confirmation with its reason (kind and jobs), each release
  with its reason, the excluded qubits, the copy chosen for A and for B, the copies passed over with their reasons, and
  the price. Ledger, registry and log are hashed and committed before job 2 is built.
- Two copies in one job are recorded under one job name in the ledger.
- Readings dated after the chain's "now" are never used (no look-ahead); `gpu/repair_job2.py` stops if the ledger has
  any (a clock or time mistake), and stops if the ledger has no reading for the fetched device (job 2 on another device).
- **What the past data said before the choice (reference only; section 6):** rule a would have
  excluded nothing on 3 November. Rule b with expiry would have excluded 11 qubits before the 17:04 job, among them
  qubit 72 (DEAD at 06:08, HEALTHY at 12:09, DEAD at 17:04 with 0.51). The scoring-only gain came entirely from 72.
  Rule b with early release would have released 72 at 12:09 and gained nothing. Three jobs on one device and day.
  The choice was made after seeing this; it is a choice on these three jobs, not on the test, which runs later.

## 3. The test

- **Device:** P6's rule (fewest pending jobs among fez, marrakesh, kingston; ties marrakesh, fez, kingston). Job 2 runs
  on job 1's device ("stay"). A and B must share one job, so if B has no copy on that device the result is NO COPY.
  The production chain would move to the next device; this test does not.
- **Job 1:** tonight's OS2D job (owner, 08:24 CET), as declared and run for OS2D (81ba8d4): P6 problem (theta_x 0.53)
  t = 1..5, floor theta_x 0 at t = 1, 5, mirror at t = 3, 5, ring sentinel; 13 circuits. Its OS2D verdicts are judged
  under OS2D's own declaration and are not changed by this test.
- **The test's ledger:** job 1's readings only (`ledger_from_job.py` with no input ledger, WHEN read from job 1's
  submission.json). No earlier reading is in a declared ledger file; the 3 November readings are after-the-fact only
  and are not used.
- **The chain:** `gpu/repair_job2.py` with rule b and expiry, on a fresh fetch of job 1's device and the registry file
  OS2D used; "now" is the build time (CET).
- **Job 2 (sent right after job 1's results are in; the gap between the two submissions is recorded):** the P6 problem t = 1..5 on A's copy and on B's copy, interleaved
  (A t1, B t1, A t2, ...), each copy's floor at t = 1, 5, ring sentinel. 18 circuits, 23.1 s by the time model.
  A and B on the same copy (nothing excluded on A's copy): **NOT TESTED**.
- Answers: P6's sealed CPU answers (both copies run the same circuit on different qubits; the answers are the same).
- 4000 shots, no mitigation, "stay". Acceptance as P6 (2 x 38 x t CZs, every patch qubit measured) per point.

## 4. Judged

1. Sentinel; acceptance.
2. **The chain (B against A):** MSE of <Z_q> against the answers, all 35 qubits, t = 1..5, ratio B / A:
   **HELPS** if <= 0.8 **and** MSE_A - MSE_B > 2 U; **HURTS** if >= 1.25 **and** MSE_B - MSE_A > 2 U; **NO EFFECT**
   otherwise. U = the larger of the shot SE of the difference (bootstrap over shots, 200 resamples, seed 0) and the
   between-run spread (owner's decision of 2026-11-04): |MSE_A(job 1) - MSE_A(job 2)| / sqrt(2), the same circuits on
   the same copy in the two jobs. If A's copy differs between the jobs, U is the shot SE alone and that is stated.
   **[after tonight]:** whether 0.8 / 1.25 stay (the owner, after OS2D's Q2).
3. Reported with it, **the price:** qubits excluded, how many of them were on A's copy, how far the copy moved
   (drow, dcol) and how many qubits A and B share.

## 5. Reported, not judged

- **The flag's lifetime:** job 2's floor on A's copy read at the excluded qubits (DEAD / UNCERTAIN / HEALTHY with the
  job's own line). This is the direct check of point 1 (do readout faults move within hours).
- The chain's log; MSE per t for both copies; the answer card for both copies.
- After the test, job 2's floors are appended to the ledger (a new file; the old one kept).

## 6. After the fact (reference only)

`notes/repair_2026-11-04/repair_posthoc.py` -> `out/repair_posthoc.json`, `out/run.txt` (floor kind only; P5 on
kingston, 3 November).

| before | rule, release | excluded | still DEAD in that job |
|---|---|---|---|
| C/D (12:09) | a, either | none | |
| C/D (12:09) | b, either | 72, 87, 125, 127, 131 | 0 of 5 (all HEALTHY, 6 h later) |
| K (17:04) | a, either | none | |
| K (17:04) | b, expiry | 35, 43, 69, 72, 78, 87, 119, 125, 127, 131, 138 | 1 of 11 (72, 0.51); 3 not in K's lattice; 35 UNCERTAIN |
| K (17:04) | b, early | 35, 43, 69, 78, 119, 138 | 0 of 6 |

Scoring-only change on K (the circuits ran as they did; a declared test places the problem elsewhere), MSE ratio
kept / all at theta 0.4, 0.8, 1.0:

| exclusions | qubits left out of K | ratios | mean |
|---|---|---|---|
| rule b, expiry | 8 | 0.55, 0.86, 0.93 | 0.78 |
| qubit 72 alone | 1 | 0.62, 0.84, 0.90 | 0.79 |
| rule b, expiry, without 72 | 7 | 0.95, 1.03, 1.03 | 1.00 |
| rule b, early | 4 | 0.95, 1.01, 1.01 | 0.99 |

The headline would be "the chain would have cut the error by 22 %". The essential numbers: all of it came from one
qubit that came back; the other seven exclusions cost seven qubits for nothing; rule a, the current rule, did nothing.

M6 (2 November, the ring kind, which is the chain's registry path already in use): the morning scan's listed run was
DEAD in the same 18 qubits 32 minutes later (part 2), and the ring placed around it helped (sh6 +0.045, parity right
+0.121). Coupler faults seen by the ring lasted at least an hour; readout faults seen by the floor mostly did not last
6 hours.

## 7. Dry run (fake, synthetic counts; plumbing only)

`notes/repair_2026-11-04/out/dryflow_synthetic.txt`: FakeKingston, a readout fault planted on physical qubit 26 (0.4
low in every cell). Job 1 (OS2D cells) -> floor DEAD [26], mirror DEAD [] (a readout fault cancels in d = floor -
mirror, as it should) -> chain rule b: excluded [26], A copy (0, 0), B copy (2, 4) ((0, 4) holds 26 too) -> job 2
built, 18 circuits, 23.1 s -> HELPS on synthetic counts. Rule a on the same ledger: NOT TESTED. The counts are made
up; nothing here is a result.

## 8. Decided and open

Decided (owner, 2026-11-04 08:24 CET): rule (b); expiry (7 days); tonight's OS2D job is job 1, job 2 right after.
Open: the thresholds 0.8 / 1.25 **[after tonight]**.
