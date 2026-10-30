# Rule-only rerun on ibm_kingston, 2026-10-30 14:12 CET: J1 NOT REPRODUCED (12 / 21), J2 6 / 12 AGREE; the pattern over n and over sites repeats

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
- **J2: 6 of 12 AGREE.** Rule L*: n = 20 21.9-22.3 (today 22.8-23.7); n = 36 24.5-26.2 (23.0-23.6, DIFFER);
  n = 40 13.0-16.0 (12.8-16.1, AGREE); n = 72 14.6-16.0 (14.2-15.3; hz 0 AGREE, 0.1 and 0.3 DIFFER).

## Reported

- The two regimes repeat: L* about 22-26 at n = 20, 36 and about 13-16 at n = 40, 72.
- Per-site minority rates at D = 24, hz 0 correlate with this morning's at 0.98 (n = 40) and 0.96 (n = 72): the same
  runs of near-random sites come back in the same places; none at n = 20 or 36 (correlation 0.35, 0.52, no
  structure).
- **Correction to an earlier reading at home:** "the rule's readable depth is about 23 layers whatever n" was wrong;
  it holds for n = 20, 36, and is about 13-16 at n = 40, 72 (this morning's fits say the same).

## Post hoc (owner's question, 23:08 JST): the near-random sites masked out, the rest read

`posthoc_live_sites/` (`live_sites.py`, output `live_sites.txt`, `live_sites.json`). Not declared; read after both
runs. A site is dead if its echo signal at D = 24, averaged over the 4 inputs and the 3 hz, is below 0.12 (the same
line as a minority rate of 0.44). **Crossed:** the mask is taken from one run and applied to the other (morning ->
rerun and rerun -> morning), so no run is read on sites chosen from itself.

- Dead sites: n = 40, the same 18 qubits in both runs (3-7, 17, 27-29, 38, 49-55, 59); n = 72, 31 in both (33 and
  31); n = 20 and 36, none.
- On the live sites (D = 24, the range over hz and both directions):

| n | live | per-bit accuracy, all -> live | rho_E, all -> live | L*, all -> live |
|---|---|---|---|---|
| 20 | 20 / 20 | 0.67-0.70 (no change) | 0.34-0.40 | 21.9-23.7 |
| 36 | 36 / 36 | 0.71-0.74 (no change) | 0.43-0.49 | 23.0-26.2 |
| 40 | 22 / 40 | 0.58-0.63 -> 0.70-0.72 | 0.17-0.26 -> 0.41-0.45 | 12.8-16.1 -> 19.7-21.3 |
| 72 | 39-41 / 72 | 0.60-0.62 -> 0.67-0.71 | 0.20-0.25 -> 0.35-0.42 | 14.2-16.0 -> 18.6-21.2 |

- Reading: most of the drop of L* at n = 40, 72 sits in the dead runs; the live sites come close to n = 20, 36 but not
  all the way (L* about 20 against 22-26; neighbours of the dead runs are partly hit).
- Limits: this recovers a local, per-site quantity only. A quantity that needs every bit (the parity, a classifier
  that reads the whole ring) is lost once a dead site is in it and is not recovered by masking. To use a mask in a
  test it must be fixed in a declaration before that test's run.
