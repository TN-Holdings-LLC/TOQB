# Rule-only echo on ibm_fez, 2026-10-31 03:44 CET: W = NO n-WALL at all three hz, because the rings of every size carry dead runs

- **Declaration:** `prereg/drafts-2026-10-30/fez_rule_only_note.md` (SHA-256 6011c240...02ebdce), fixed 2026-10-30
  14:30 CET, before this fetch (2026-10-31 03:30:04 CET; calibration 03:16:45 CET). TOQB c16ba80 (the build script
  `gpu/rerun_rule_only.sh` with `NOTE` set to that note). `fold:rule` only; the echo of test 2 / 3E (n 20, 36, 40, 72;
  hz 0, 0.1, 0.3; D 24, 50, 100; 500 shots); 288 circuits, all 36 cells accepted.
- **Job** dbilc0ghoj4c73b6fkq0, submitted 03:44:02 CET (calibration at submission 03:24:44 CET), queued about 5 min,
  done 03:51:38 CET; 52.2 s predicted, **41 s billed**. Dynamical decoupling and twirling off.
- **Files:** `fetch.json`, build logs, `runs/`, `job/` (manifest, submission, `raw_counts.json.gz`, `echo_score.json`,
  `fez_wall_judgement.json`, per-site `sites_n*.json` from `toqb.echo_sites`), `score.txt`; QPY SHA-256 in
  `qpy_sha256.txt`. A first build attempt stopped before anything was written (the fetch had not been copied yet).

## Judged: W (n-wall), per hz

| hz | L*(20) | L*(36) | M | band [0.8 M, 1.2 M] | L*(40) | L*(72) | verdict |
|---|---|---|---|---|---|---|---|
| 0 | 11.2 +- 0.3 | 16.0 +- 0.3 | 13.6 | [10.9, 16.3] | 12.5 | 12.8 | NO n-WALL |
| 0.1 | 11.4 +- 0.3 | 16.5 +- 0.3 | 14.0 | [11.2, 16.8] | 13.2 | 13.2 | NO n-WALL |
| 0.3 | 12.1 +- 0.3 | 16.8 +- 0.3 | 14.5 | [11.6, 17.4] | 13.8 | 13.9 | NO n-WALL |

**Overall: NO n-WALL** (the same at all three hz).

## Reported

- **Why there is no wall:** the rings of every size have dead runs on fez (per-site signal below 0.12 at D = 24,
  hz 0): n = 20: 11 of 20 sites (4-7, 17, 25-27, 37, 43, 45); n = 36: 6; n = 40: 11; n = 72: 36. The decay length is
  short at every n (11-17 steps), not only above 36. The verdict is the declared one; the reason is not "no defect"
  but "defects at every size".
- **Same circuit, two chips.** The n = 20 ring is the same physical ring, with the same compiled gates, on fez and on
  kingston. On kingston (30 October, three runs) it had no dead site and rho_E 0.34-0.40 at D = 24; on fez it has 11
  dead sites and rho_E 0.12-0.14. The n = 72 ring is also the same on both; its dead runs sit mostly in different
  places on the two chips. The dead runs follow the chip, not the circuit.
- rho_E at D = 24 (hz 0 / 0.1 / 0.3): n 20 0.120 / 0.123 / 0.142; n 36 0.251 / 0.266 / 0.288; n 40 0.158 / 0.172 /
  0.192; n 72 0.163 / 0.174 / 0.192.
- The three devices of the Open Plan on this echo: kingston 22-26 steps at n = 20, 36 and 13-16 at n = 40, 72
  (dead runs only at 40, 72); marrakesh 14-16 at every n; fez 11-17 at every n with dead runs at every n.
