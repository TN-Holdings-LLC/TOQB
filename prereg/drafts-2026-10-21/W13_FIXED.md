# W13 fixed (home, 2026-10-21 09:43 CEST, before any E4v record exists)

The owner approved the bounded plan of W12 / W13 at the workplace (one cause check; one improved E4, fixed in advance,
on fresh teachers 10, 11, 12, scored by the frozen W11 scorer; no further version whatever the result) and chose
option A ("select and check"). At home the owner chose both additions of W13 section 3: the F3 seeds (C0 202, 203 and
E4v twin seeds 1010, 2010 on (1.0, L 8, teacher 10)) and plain E4 on the same 9 tasks for attribution (its own
directory, scored separately by the same scorer, never a headline). Pod script: gpu/e4v_match.sh.

| file | SHA-256 |
|---|---|
| prereg/drafts-2026-10-21/W12_cause_check_2026-10-21.md | e8d284ab0c1ef94ecd652212d8ff2fc814f5ad0e226b871268c206cff3921989 |
| prereg/drafts-2026-10-21/W13_E4v_select_and_check_2026-10-21.md | f96f72e48ecb2ea37f8c0ae8b398a34b1f25d9c07fbfcd9238271f256346129c |
| toqb/s2re4v.py | 7d04ccebd93958ee19a3e2b3fb1a2a04c3312c4282e83ee12221c52cd09e3de2 |
| toqb/s2re4_run.py | c5517b252db75b58ad1d0a4d3551383dc2e62f9c3e98707cbcf5382d747d4631 |
| tests/test_s2re4v.py | 4c42ad76129a3349e34471b36350930adeb4dd25091873dbf5cbd6f6d96039e2 |
| tests/test_e4v_runner.py | 1347bb3de9337f142238c6ed8d776c1fee199212c90bcbd2014864c806d37318 |
| toqb/match_score_fruit.py (W11, frozen, the scorer) | 29a152d1cb522f4d8ce521800332843b7cfd85ee78fbfda2d4f23039cfbea8d1 |
| toqb/match_score.py (W8, imported) | aa40de4363ab69840047060b8169e9010476b38a7690911feb0f27cfd896e122 |

The workplace's files arrived with these SHA-256 (SHA256SUMS.txt) and were installed unchanged. Home check: 21 tests
passed (test_s2re4v, test_s2re, test_e4v_runner, test_fruit): E4's default path is unchanged and E4v's cost equals
E4's. W12's computation is toqb/w12_check.py (home code; noiseless part on the CPU, twin part on the pod).
