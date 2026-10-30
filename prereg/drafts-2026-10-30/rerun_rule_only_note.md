# Rule-only rerun on ibm_kingston (home, FIXED 2026-10-30 14:02 CET on the owner's go, before any fetch): today's echo again, the rule as the only arm

**Why.** Today's echo on ibm_kingston (`results/device-2026-10-30/test2/kingston`, job dbi7r45ep8hs73anb5q0;
`results/device-2026-10-30/test3E/kingston`, job dbi7rtene4hc73be2p8g) is run again, the same day, with the rule
alone, to see whether the rule's numbers reproduce. Read after the run (post hoc) and not used for anything here:
at n = 40 and 72 some runs of ring sites came out near random at D = 24, at n = 20 and 36 none did.

**Design (owner's go 2026-10-30 21:49 and 22:00 JST).**
- ibm_kingston, a new fetch after this note. The rule (`fold:rule`) is the only arm (owner: the other arms add
  nothing here and do not change the rule's circuits, which run one at a time).
- The mirror echo exactly as declared for test 2 and part E of test 3 (`echo_hz_note.md`, 1308cf9b...;
  `test3_note.md`, 8b13773f...; `test3_addendum2.md`, 78986cf3...): n = 20, 36, 40, 72; hz = 0, 0.1, 0.3; one-way
  L = 12, 25, 50 (D = 24, 50, 100); h = 0.6; 4 inputs and 4 references; 500 shots. 36 cells, 288 circuits, one
  job; time model 3 + 0.036 x 288 + 0.00027 x 144,000 = 52.2 s.
- Placement map-free as always: from the coupling graph and the failed elements only; nothing read from the
  calibration's quality numbers, nothing chosen from today's results. A placement refused or an acceptance failed
  is recorded, never replaced. Code `gpu/rerun_rule_only.sh` at the commit of this note.

**Judged.** "Today" is the rule's cell in today's `echo_score.json` of the same (n, hz, D) (test 2 for n = 20, 36;
test 3E for n = 40, 72).
- **J1 (cells):** per cell, judged if today's or the rerun's rho_E exceeds 2 SE (else NOT JUDGED); AGREE if
  |rho_E(rerun) - rho_E(today)| <= 2 sqrt(SE_rerun^2 + SE_today^2), else DIFFER. **REPRODUCED** if at least 80 % of
  the judged cells AGREE, else **NOT REPRODUCED**.
- **J2 (readable depth):** per (hz, n), the rule's L* (`kising_charge.decay_length` over D = 24, 50, 100, as in
  test 2): AGREE if within 2 combined SE of today's, else DIFFER; NOT JUDGED where either fit has no value.

**Reported, not judged.** The counts of J1 and J2 by n; the per-site minority rate min(p1, 1 - p1) of every
D = 24 cell (all n, all hz) beside today's; the new fetch's time and calibration time. No rule A or B (no other
arm). Nothing read from these numbers changes this note.
