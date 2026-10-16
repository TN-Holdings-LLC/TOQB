# Loop budget run, first start at the workplace: stopped, not scored (2026-10-16)

Pre-registration: [`prereg/2026-10-16-loop-n6-budget.md`](../../prereg/2026-10-16-loop-n6-budget.md) (SHA-256
`0e35edcf...`, printed in `times.txt`). Times in CEST.

- **Started:** 2026-10-16 02:18:03 on the owner's workplace PC (Windows, 14 logical CPUs, 12 processes), with
  `run_budget.py`, which checked every fixed hash before starting.
- **Stopped:** after 240 of 2,000 arm runs (119 seeds with both arms, 2 with one; 248 partial records of arms in
  progress). The PC was slower than the authors' estimate (measured afterwards: 5.6-6.5 hours for the whole run at
  4-8 processes, against the 30-45 minutes estimated), and an editor update ended the process.
- **Not scored.** By the pre-registration's interruption rule, the run is started again into a new folder and the first
  complete run is scored. Nothing here is read by the scorer.
- **Kept here:** `times.txt` and every record written (`arm-*.json`, `arm-*.partial.json`). The 1,000 `plan.json`
  copies are left out of the tree: each was checked identical, byte for byte, to the pre-registered
  `prereg/loop-n6-budget-2026-10-16/plan_s<seed>.json`. The logs, which `.gitignore` keeps out of the tree, are in
  `raw_records.zip`, the folder as zipped at the workplace (added 2026-10-16; the first version of this note said the
  logs were kept here, which they were not).
