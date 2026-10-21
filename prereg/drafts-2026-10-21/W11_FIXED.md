# W11 fixed (owner, 2026-10-21 05:41 CEST, before any record of the fruit match was read)

Owner's answer: "fix as is" (all four points of W11 section 6: the headline per group (angle, L), every group
reported as "won in k of 3 groups", the pooled verdict reported only; angle 0.3's loss against theta = 0 written as
"not won" and kept to its group; the headline condition E4 > C0 and E4 > Z at f_min; F4's binomial test indicative).

| file | SHA-256 |
|---|---|
| prereg/drafts-2026-10-21/W11_fruit_rules_2026-10-21.md | 03bb0c2d8d5a9d238873a94e16f2a1c2f21834822bf5e96fafbcecacb4ab2572 |
| toqb/match_score_fruit.py | 29a152d1cb522f4d8ce521800332843b7cfd85ee78fbfda2d4f23039cfbea8d1 |
| tests/test_match_score_fruit.py | 0148cbd01bd144036931ee8e616f49d1765f59298a3ca09c865a6fa4d6065601 |
| toqb/match_score.py (W8, imported, unchanged) | aa40de4363ab69840047060b8169e9010476b38a7690911feb0f27cfd896e122 |

Home check before fixing: tests/test_match_score_fruit.py and tests/test_match_score.py 17 passed; an end-to-end
smoke on real records of the same format (Z, E4 with checkpoints, C0 from toqb.s2rc_ckpt with checkpoints; L 1,
8 training and 20 test points, costs matched) was read and scored without change.
