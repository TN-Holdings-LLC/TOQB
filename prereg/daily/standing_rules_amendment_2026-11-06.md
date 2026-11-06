# Declared: amendment to the standing rules of the daily record (owner, 2026-11-06 07:38 CET: "FX-A だけで流す")

Adds to `prereg/daily/standing_rules.md`; nothing else in it changes. Applies from day 2 (2026-11-06), declared before
the night's fetch.

## A problem that cannot be placed

- `psf-os run2d` refuses the whole batch when one circuit of it has no qualifying translation. Then the refused
  problem gets its line in `results/daily/RECORD.md` as **REFUSED** (with run2d's reason: the translations passed
  over and why), and the night's other problem(s) are run on that device in one `psf-os run2d` batch without it.
- Example: FX-A alone when the night's new problem is refused. If every problem is refused, the device's night is a
  line "not run" with the reasons.
- A refused new problem counts as used (as the rules already say: used once it is built for a night, run or not);
  the next night takes the next one in pool order.
- Everything else (devices, judging, recording, no correction) is unchanged.
