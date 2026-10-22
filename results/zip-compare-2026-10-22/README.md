# The zipper against item 31 on the device day's plans (report only; 2026-10-22, 04:04-04:25 CEST, H100)

Declared before the run in `prereg/drafts-2026-10-22/zip_compare_note.md`. The device day's two plans (seed 301, C0,
2,000 loops), run as a rehearsal on snapshot:marrakesh, then verified on the stand-in. One seed and one task per depth:
reported as seen, no test, nothing chosen. Pod paths written `<pod>/`; the zip's SHA-256 is
97fabcc435ef12f055295f58a615d177729334c0c7b087406d9a6ebf9ae56f0e.

| L | schedule | CZ | duration (us) | twin's predicted CE [99 %] | stand-in CE | inside | stand-in accuracy |
|---|---|---|---|---|---|---|---|
| 8 | item 31 (the day's) | 224 | 10.39 | 0.5618 [0.5488, 0.5747] | 0.5629 | yes | 0.783 |
| 8 | zipper | 168 | 7.20 | 0.5678 [0.5547, 0.5808] | 0.5662 | yes | 0.823 |
| 16 | item 31 (the day's) | 448 | 18.02 | 0.6291 [0.6213, 0.6369] | 0.6323 | yes | 0.618 |
| 16 | zipper | 336 | 11.65 | 0.6456 [0.6377, 0.6534] | 0.6446 | yes | 0.710 |

- The item 31 runs reproduce the device day's PSF predictions exactly (L 8: 0.5618, L 16: 0.6291): a rehearsal of the
  day's own PSF models, and both fell inside their intervals on the stand-in.
- The zipper: 25 % fewer CZ and 31-35 % shorter; on the stand-in, accuracy higher (+4.0 and +9.2 points), CE slightly
  higher (worse: +0.003 and +0.012). Its twin predicted the same direction for the CE. One seed: no claim.
- 4 of 4 stand-in CEs inside the twin's 99 % intervals.
