# Two more devices (OS plan M4), 2026-11-01: scan-then-avoid HELPS on ibm_fez and on ibm_marrakesh

- **Declaration:** `prereg/drafts-2026-11-01/two_devices_note.md` (SHA-256 91f2dbb8...9d68), fixed 11:30 CET, TOQB
  541d0b5. Morning list: `results/defect-list-replay-2026-10-31/observations.json` (CANDIDATE only on both devices).
  `dryrun/`: the chain on the 31 October fez fetch with made-up counts.

| device | fetch (calibration) | scan job (billed) | avoid job (billed) |
|---|---|---|---|
| ibm_fez | 11:32:29 CET (11:10:52) | dbjhcahffo6c73b9lldg, 11:36:26 CET (9 s) | dbjhvd9kdqps7390knsg, 12:17:09 CET (6 s) |
| ibm_marrakesh | 12:20:26 CET (11:58:38) | dbji2qpffo6c73b9n4cg, 12:24:27 CET (9 s) | dbji4t1kdqps7390l4pg, 12:28:52 CET (7 s) |

## Registered after the scan

- **fez:** all three candidates of 31 October came back: [6, 7, 17, 27], [26, 27, 28, 29], [63, 56] LISTED; masked
  couplers (7, 17), (27, 28), (56, 63).
- **marrakesh:** the candidate [27, 28] of 30 October came back as part of [17, 27, 28, 29] (LISTED; one old
  contradiction); [96, 103, 104] not seen again (CANDIDATE); masked coupler (27, 28).

## Judged (usable sites, avoid ring against the scan's standard ring)

| device | n = 40 | n = 72 | verdict |
|---|---|---|---|
| fez | 29 -> 40 **WIDER** | 36 -> 63 **WIDER** | **HELPS** |
| marrakesh | 40 -> 40 SAME | 67 -> 72 **WIDER** | **HELPS** |

**Outcome by the note:** HELPS on both devices: scan-then-avoid widens the usable part of the device on three chips;
it is a property of the method, not of kingston.

## Reported

- Signal over the whole ring, standard / avoid: fez n = 40 0.141 / 0.205, n = 72 0.149 / 0.201; marrakesh n = 40
  0.270 / 0.241, n = 72 0.224 / 0.257.
- fez's avoid n = 72 ring still had a 9-site dead run (66-61, 76, 81, 82), next to the listed [63, 56]; it enters the
  list (`fez/avoid/list_after.json`).
- n = 20 standard rings: fez 7 / 20 usable (a 13-site dead run 16, 3-7, 17, 27, 26, 25, 37, 45, 44), marrakesh
  17 / 20 (3 sites, 26, 25, 37). The n = 20, 72 standard circuits are byte-identical across the three devices (the
  rule's ring is the same where the chips' failed elements allow); fez's n = 40 differs.
- fez reads at about half of kingston's level overall; marrakesh is the healthiest of the three today.
