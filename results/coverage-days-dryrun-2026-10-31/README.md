# Coverage days: dry run (2026-10-31; nothing submitted)

`gpu/defect_days.sh` on the kingston fetch of 30 October 14:02 with the day-1 list (the replay list, SHA-256
b1fe9fe7...6765) and list date 2026-11-01 10:00: `list_status.txt` (3 LISTED paths), `mask.txt` (couplers (9, 10),
(29, 38), (85, 86) marked failed), `build.txt` (A: n 20, 40, 72; B: n 40, 72; all accepted), `assemble.txt`
(A 24 circuits, 10.3 s; B 16 circuits, 7.9 s).

`plumbing_*`: `gpu/defect_days_score.sh` run on made-up counts (every site right 75 % of the time; on job A, qubits
38, 49-52 random; job B clean), to check the scoring and the next day's list end to end. The numbers mean nothing
about the device.
