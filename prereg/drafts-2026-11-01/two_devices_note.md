# Two more devices (OS plan M4): scan, list, avoid on ibm_fez and ibm_marrakesh (home, 2026-11-01; declared on the owner's go of 2026-11-01 11:25 CET)

**Why.** On ibm_kingston, placing the rule's rings around a self-measured list of dead paths made every site usable
on two days (coverage days 1, 2: 22 -> 40 at n = 40, 38-39 -> 72 at n = 72). Whether this is a property of the method
or of one chip is decided on other devices.

**The list there now** (`results/defect-list-replay-2026-10-31/observations.json`, SHA-256 b1fe9fe7...6765):
CANDIDATE only. ibm_fez (31 October): [6, 7, 17, 27], [26, 27, 28, 29], [63, 56]. ibm_marrakesh (30 October):
[27, 28] (one contradiction), [96, 103, 104]. Same rules as coverage days: dead run = at least 3 consecutive ring
sites below 0.12 at D = 24; centre 4 qubits; sightings sharing 2 qubits merge; LISTED after 2 jobs; 7-day expiry.

**A session (per device, one fetch, two jobs; fez first, then marrakesh).**
1. **Scan** (`gpu/defect_days.sh` with DEVICE, the list above as the morning list): the rule's echo on the standard
   rings n = 20, 40, 72; D = 24, hz 0, h 0.6, 4 inputs and 4 references, 1000 shots, options off; 24 circuits,
   10.3 s. (Nothing is LISTED, so no avoid rings are built in this step.)
2. **Register** (`gpu/defect_days_score.sh`): the scan is added to the list (`list_after.json`); a candidate seen
   again becomes LISTED.
3. **Avoid** (`gpu/avoid_job.sh`): n = 40 and 72 on the rings placed when the same fetch is masked by the LISTED
   paths of that device; a size whose ring equals the scan's is dropped; up to 16 circuits, 7.9 s. If nothing is
   LISTED, there is no avoid job.
4. **Score** (`gpu/avoid_score.sh`): usable sites of the avoid rings against the scan's standard rings.

Dry run of the whole chain on the 31 October fez fetch with made-up counts: scan accepted (n = 20, 40, 72), a
candidate seen again was LISTED, the masked n = 72 ring was built and the n = 40 ring (unchanged) dropped, scoring ran.

**Judged per device.**
- **C, per size (n = 40, 72):** usable sites, avoid ring minus standard ring: WIDER (>= +3), NARROWER (<= -3), SAME
  otherwise; a dropped size counts as SAME.
- **Device verdict:** HELPS if at least one WIDER and no NARROWER; NO GAIN if all SAME; HURTS if any NARROWER;
  NOTHING LISTED if no path became LISTED (the list could not act that day).

**One sentence per outcome (fixed in advance).**
- HELPS on both devices: scan-then-avoid widens the usable part of the device on three chips; it is a property of the
  method, not of kingston.
- HELPS on one: it works where a dead path repeats; the other device is reported with its verdict.
- Neither HELPS: the gain was kingston's; the method is reported as device-specific.

**Reported.** Which candidates came back; every dead run; signal on usable sites; the n = 20 ring; billed time.
**Stop.** One session per device.
