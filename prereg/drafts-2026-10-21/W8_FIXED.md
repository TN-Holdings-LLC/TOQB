# W8 fixed (owner, 2026-10-21 02:03 CEST, before any record of the E4-against-C match was read)

Owner's answer: "fix as is" (all four points of W8 section 5 accepted: teacher 4 out of the headline as a
development task; alpha 0.01 two-sided, Holm per comparison, Stouffer overall; per-point CE from the exact P(1) as
the primary quantity, accuracy secondary; the headline needs E4 > C0 and E4 > Z on fresh tasks).

| file | SHA-256 |
|---|---|
| prereg/drafts-2026-10-21/W8_match_rules_2026-10-21.md | f9e5057f1a1d04f9c2c31f258a4386b181561478e7ae31d5c1075eba9e86584c |
| toqb/match_score.py | aa40de4363ab69840047060b8169e9010476b38a7690911feb0f27cfd896e122 |
| tests/test_match_score.py | 25f4e5a952feca87509eb34bd28a41b9c206457db7e39059422cfb1c43fbb0a0 |

Home check before fixing: tests/test_match_score.py 9 passed; a smoke run on real s2re4 records (E4 and Z, L 1,
8 test points) read the record format without change.

Home note (not a change of the rules): the unit is the test point, and each task has one C0 run (seed 201) and one
E4 run, so a task's test compares two trained models; the method-level evidence is the replication over tasks
(the Stouffer combination over teachers and depths).

W9 (owner, the same time): option C, the fixed ladder of teacher angles 0.3, 1.0 and 2.0, every method at every
angle, every result reported; from the match after today's (today's match stays at angle 1.0).
