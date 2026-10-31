# Readable depth on rings placed around the defect list: is the shorter depth at n = 40, 72 the defects or the size? (home, 2026-10-31; declared on the owner's go of 2026-10-31 11:48 CET)

**Why.** On 30 October (rule-only rerun on ibm_kingston, `results/device-2026-10-30/rerun-rule-only`) the rule's
readable depth L* was about 22-26 layers at n = 20, 36 and 13-16 at n = 40, 72. Masking the dead sites after the run
brought n = 40, 72 to about 19-21, not all the way, because the dead runs' neighbours were hit too. On 31 October the
rings placed around the self-measured list had no dead run at n = 40, 72 (coverage days, day 1). Here the same echo
is run on those rings.

**Design (one job, ibm_kingston, after this note is fixed and after a new fetch).**
- The day's fetch masked by the list `results/coverage-days-2026-10-31-day1/list_after.json` (LISTED [11, 10, 9],
  [28, 29, 38, 49], [87, 86, 85]; `defect_list mask`); the rule (`fold:rule`) places n = 20, 40, 72 on it. n = 20 is
  the control: its ring holds no listed path, so it is the standard ring.
- The echo of the 30 October rerun: hz = 0, 0.1, 0.3; one-way L = 12, 25, 50 (D = 24, 50, 100); h = 0.6; 4 inputs and
  4 references; 500 shots. 27 cells, 216 circuits; predicted 39.9 s. Options off. `gpu/clean_depth.sh`.
- Dry run on the 31 October 10:56 fetch: all 27 cells accepted; the n = 20 ring is the standard ring; the n = 40 and
  72 rings are day 1's job B rings and hold no listed path.
- Self-checked category (placement from the user's own list), always labelled. This job is not added to the
  coverage-days list.

**Judged.** L* per (n, hz) from `kising_echo score` (fit over D = 24, 50, 100, as on 30 October).
- **J (per hz, n = 40 and 72):** REACHED if L*(n) >= L*(20) - 2 sqrt(SE_n^2 + SE_20^2), the same day and hz; else
  SHORTER. Six verdicts.

**One sentence per outcome (fixed in advance; nothing else is concluded).**
- REACHED in all 6: the shorter readable depth at n = 40, 72 came from the defects, not from the ring size; around
  them the rule reads as deep at n = 72 as at n = 20.
- SHORTER in all 6: even without dead runs the larger rings read less deep; the size costs depth on this device.
- Otherwise: mixed; reported per n and hz, no general sentence.

**Reported, not judged.** rho_E per cell; dead runs on every ring at D = 24 (the coverage-days rule: at least 3
consecutive sites below 0.12); L* beside 30 October's (standard rings 13-16 at n = 40, 72; live sites 19-21; n = 20
21.9-23.7); billed time.

**Stop.** One job.
