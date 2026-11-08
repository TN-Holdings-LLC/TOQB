# Three layouts side by side on a device (prereg/os3d_heisE_2026-11-08.md)

- Declared at TOQB f67aa5b, pushed before the fetch. Queue read 12:23 CET 2026-11-08: marrakesh 0, fez 0,
  kingston 1 -> ibm_marrakesh (fewest pending, tie broken by the declared order; a translation fits).
  Record: failed qubits 46, 73, 82, 113, 119, 130; coupler 113-119.
- Job `marrakesh/`: candidates (1, 8), (3, 4), (5, 0), (0, 0) (fold order); each in old / carry / line at t = 1-4;
  148 circuits, 168.2 s by the model; answers 21c88673...; every answer equals the sealed tables' entry.
- CZ at t = 1 / 4: odd rows (candidates 0-2) old 176 / 692, carry 152 / 596, line 116 / 404; even row (candidate 3,
  bridges at line positions 3, 7) old 212 / 836, carry 200 / 788, line 128 / 452.

## Run

Job dbo4smlt7fqc73akilo0, submitted 12:26 CET, DONE at the first collect. Sentinel CLEAN. Scored with the declared
rule: `marrakesh/scores.json`. Answers released in `answers/` (the run's answers, the carry and line tables), as
sealed.

## Judged candidate 1 (r0 3, c0 4; mean t1 mirror 0.653, the highest)

| t | old: retention (CZ) | carry | line | carry - old | line - old | shot bound |
|---|---|---|---|---|---|---|
| 1 | 0.802 (176) | 0.820 (152) | 0.841 (116) | +0.018 | +0.039 | 0.048 |
| 2 | 0.689 (348) | 0.732 (300) | 0.768 (212) | +0.043 | +0.079 resolved | 0.059 |
| 3 | 0.616 (520) | 0.681 (448) | 0.712 (308) | +0.065 | +0.096 resolved | 0.084 |
| 4 | 0.610 (692) | 0.711 (596) | 0.687 (404) | +0.101 | +0.077 | 0.145 |

Every judged arm READS and DIFFERS (|m_s - exact| > 0.05). The recorded predictions (carry - old >= 0, line - old
>= 0 at every t on the judged place) held at every t; line - old is resolved at t = 2 and 3, carry - old at none.
The simulator's estimate recorded in heisD (line - old +0.065 / +0.088 / +0.093 / +0.107, made on the 422-CZ line
layout) and the device (+0.039 / +0.079 / +0.096 / +0.077) are within 0.03 of each other at every t.

Beside: candidates 0 and 2 (odd rows) line - old +0.038 / +0.062 / -0.016 / +0.009 and +0.037 / +0.057 / +0.094 /
+0.111; candidate 3 (row 0, even, floor 0.87-0.89) +0.012 / +0.070 / -0.053 / -0.037, and its line arm at t = 4 does not
READ. Mean over the four places: line - old +0.031 / +0.067 / +0.030 / +0.040, carry - old +0.017 / +0.028 / +0.034 /
+0.053 (carry - old positive at all 16 place-depths).
