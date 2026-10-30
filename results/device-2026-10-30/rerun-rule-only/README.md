# Rule-only rerun on ibm_kingston, 2026-10-30 14:12 CET: J1 NOT REPRODUCED (12 / 21), J2 7 / 12 AGREE; the pattern over n and over sites repeats

- **Declaration:** `prereg/drafts-2026-10-30/rerun_rule_only_note.md` (SHA-256 1f883a77...7952d0), fixed 14:02 CET
  before the fetch (14:02:07 CET; calibration 13:37:20 CET). TOQB 5ceba46. `fold:rule` only; test 2 and 3E's
  echo (n 20, 36, 40, 72; hz 0, 0.1, 0.3; D 24, 50, 100; 500 shots); 288 circuits, all 36 cells accepted.
- **Job** dbi9fhene4hc73be4u50, submitted 14:12:21 CET, done 14:14:56 CET; 52.2 s predicted, **41 s billed**.
  Dynamical decoupling and twirling off. The n = 40 ring is the same physical ring as this morning's.
- **Files:** `fetch.json`, build logs, `runs/` (records), `job/` (manifest, submission, `raw_counts.json.gz`,
  `echo_score.json`, `rerun_judgement.json`), `score.txt`; QPY not committed (`qpy_sha256.txt`).

## Judged (against this morning's rule cells on kingston)

- **J1: NOT REPRODUCED.** 12 of 21 judged cells AGREE within 2 combined SE (80 % needed). The 9 DIFFER cells are
  all small in value: the rerun is higher by 0.02-0.05 at n = 36 (D = 24, 50) and by 0.016-0.019 at n = 72 (D = 24);
  one n = 20 cell is lower by 0.035. The SE are 0.004-0.011, so the 2 SE test sees a few per cent of drift.
- **J2: 7 of 12 AGREE.** Rule L*: n = 20 21.9-22.3 (today 22.8-23.7); n = 36 24.5-26.2 (23.0-23.6, DIFFER);
  n = 40 13.0-16.0 (12.8-16.1, AGREE); n = 72 14.6-16.0 (14.2-15.3; hz 0 AGREE, 0.1 and 0.3 DIFFER).

## Reported

- The two regimes repeat: L* about 22-26 at n = 20, 36 and about 13-16 at n = 40, 72.
- Per-site minority rates at D = 24, hz 0 correlate with this morning's at 0.98 (n = 40) and 0.96 (n = 72): the same
  runs of near-random sites come back in the same places; none at n = 20 or 36 (correlation 0.35, 0.52, no
  structure).
- **Correction to an earlier reading at home:** "the rule's readable depth is about 23 layers whatever n" was wrong;
  it holds for n = 20, 36, and is about 13-16 at n = 40, 72 (this morning's fits say the same).
