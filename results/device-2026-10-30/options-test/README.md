# Options test on ibm_kingston, 2026-10-30 15:24 CET: dynamical decoupling and gate twirling against the dead sites at n = 40

- **Declaration:** `prereg/drafts-2026-10-30/options_test_note.md` (SHA-256 2ebd84e2...a924d), fixed 15:20 CET
  before the fetch (15:21:29 CET; calibration 14:56:41 CET). TOQB f06e173 (`s2rc_device submit --dd / --twirl`,
  default off). `fold:rule` only; mirror echo n = 20 and 40, D = 24, hz = 0, 1000 shots; 16 circuits, built once.
- **Jobs** (the same `circuits.qpy`, c19345ec...): off dbiah1ghoj4c73b5qkrg (6 s billed); dd XY4
  dbiah38hoj4c73b5qku0 (6 s); gate twirling dbiah581h92s73832mh0 (7 s). Submitted 15:24:09-15:24:23 CET.
- The n = 40 circuit is byte for byte this morning's (QPY SHA-256 42376e3f..., the same as test 3E's record): the
  same ring, the same gates, for the third time.
- **Files:** `fetch.json`, build logs, `runs/`, `job_off|dd|twirl/` (manifest, submission, `raw_counts.json.gz`,
  `echo_score.json`), `sites_n40.json`, `sites_n20.json` (`toqb.echo_sites compare`), `qpy_sha256.txt`.

## Judged (n = 40; G = the 18 dead sites, R = the other 22; mean raw per-site signal, 1 perfect, 0 random)

| job | G | R | all | rho_E |
|---|---|---|---|---|
| off | -0.133 +- 0.004 | 0.430 +- 0.003 | 0.176 | 0.181 +- 0.004 |
| dd XY4 | -0.115 +- 0.004 | 0.417 +- 0.003 | 0.178 | 0.182 +- 0.004 |
| twirl | 0.010 +- 0.004 | 0.366 +- 0.003 | 0.206 | 0.211 +- 0.004 |

- **dd against off:** G **HELPS** (+0.018 +- 0.005), not recovered; R **HURTS** (-0.013 +- 0.004).
- **twirl against off:** G **HELPS** (+0.143 +- 0.005), not recovered (0.010 against 0.8 x 0.366); R **HURTS**
  (-0.064 +- 0.004).

## Reported

- The dead sites came back with the options off, for the third time today (G -0.133).
- Sub-blocks, off / dd / twirl: 3-29: -0.052 / -0.037 / +0.004; 38-59: -0.214 / -0.192 / +0.015. Twirling turns the
  inverted block (the echo returns the wrong bit more often than the right one) into a random one: the error there
  is coherent. It does not bring the information back.
- n = 20 control (no dead sites): rho_E off 0.374, dd 0.369, twirl 0.272. Twirling costs the healthy ring about a
  quarter of its signal; DD costs nothing visible.
- Reading at home (not tested): DD, which cancels static ZZ coupling on idle qubits, does almost nothing, so the
  damage is unlikely to be idle crosstalk; a coherent error during the gates themselves (e.g. between gates run at
  the same time) remains the candidate. Neither option is a fix: the standard stays off / off.
