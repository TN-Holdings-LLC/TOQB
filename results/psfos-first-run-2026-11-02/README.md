# psf-os's first device run, 2026-11-02: the chain PASSES; the answer DIFFERS on one point by the letter of the note

- **Declaration:** `prereg/drafts-2026-11-02/psfos_first_run_note.md` (SHA-256 3953f4e5...2590), fixed 14:06 CET,
  TOQB f124918. psf-os 0868c25 (`psf_os/ibm.py`).
- **The job:** job S of `results/m6-practice-2026-11-02`, unchanged: `circuits.qpy` SHA-256 8cf6aa6e... is that job's
  (`qpy_sha256.txt`), `manifest.json` byte-identical. Sent with `psf-os submit` at 14:07:57 CET to ibm_kingston
  (calibration at submission 13:50:40 CET; the failed-element check passed), options off, "stay"; job
  dbk8mb0nceqs73aldpc0, DONE, collected with `psf-os collect` at 14:08:13 CET; 7 s billed. Scored with psf-os against
  the records in `results/m6-practice-2026-11-02/S/runs` (`score.json`).

## Judged

| | 12:03 CET (TOQB) | 12:35 CET (TOQB) | 14:07 CET (psf-os) | declared range |
|---|---|---|---|---|
| sentinel | DEAD, 18 qubits | DEAD, the same 18 | DEAD, **19 qubits: the same 18 and qubit 16** (mean -0.11) | DEAD on the same 18 |
| sh6 ring mean | 0.780 | 0.770 | **0.782 +- 0.001** | 0.745-0.805 |
| parity right | 0.482 | 0.472 | **0.473** | 0.447-0.507 |

1. **The chain: PASS.** psf-os submitted, the job ended DONE, psf-os collected and scored it.
2. **The answer: DIFFERS** by the letter of the note: the dead run now holds one more qubit (16, the ring's last site,
   next to qubit 3). The sh6 mean and the parity are inside their ranges.

**Sentence fixed in advance (PASS and DIFFERS):** *the chain works; the device or the day differed.*

## Reported

- The difference is one site at the edge of the known run: qubit 16 read 0.103 at 14:07 CET, just under the dead line
  (0.12), after 0.149 at 12:03 and 0.142 at 12:35 CET: a borderline site that crossed the line. Everything the note compares numerically agrees with the two TOQB runs of the same circuits.
- The submission record (`S/submission.json`) carries the options, "stay" and the calibration time at submission;
  `S/raw_counts.json.gz` is in TOQB's format.
