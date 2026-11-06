# Review of the declared 3D test: builder, score, declaration (workplace, 2026-11-06; home's 06n item 1 and 06o)

TOQB f630bf3, psf-os e5f95b5. The declaration cannot change; this only reports. Builds run offline on the 11-05
records (`gpu/os3d_compare_build.py`, relative output folders); no IBM.

## Builder (`gpu/os3d_compare_build.py`)

1. **Record names: right.** p2d_g3d_t1..3 and p2d_sabre_t1..3, each with _floor and _mirror, plus the ring sentinel
   (ksent_n40_D24-fold_rule): 22 records. `calib_beside.py` reads them as 7 groups (6 arms + the sentinel)
   (`calib_beside_fake/combined_job_fez1105_properties.json`, FakeFez properties).
2. **Acceptance: right, and the same for both arms.** A through `grid3d.prepare` (`accept`), B through `accept` on the
   SABRE circuit: user and mirror measure the sites in order, the floor keeps every CZ and is diagonal, the mirror has
   twice the CZ. Everything is prepared and accepted before anything is written. B routes on the coupling graph
   without failed elements, so it needs no separate coupler check.
   - fez 11-05: A 116 / 232 / 348, B 136 / 269 / 456 CZ (as declared); 27.6 s.
   - marrakesh 11-05: A 116 / 232 / 348, B 142 / 275 / 417; 27.6 s.
3. **Answers: only in the answers file.** SHA-256 6b2d068c... on both records (device-independent, as declared). No
   answer value (4 decimals rounded and cut, and 6 decimals; values below 0.01 left out) appears in job/, runs/ or
   report.json of either build: 0 hits.

## Declaration against `gpu/os3d_score.py`

1. **BEATS, words against code.** The declaration says "the better of all-0 and all-1"; the code it fixes
   (`practice_score.judge`, unchanged) uses "every <Z> = 0, or every <Z> = 1", that is min(mean a^2, mean (1-a)^2).
   Read as bit strings, "all-1" would be <Z> = -1, a different guess. The code is what scores; the night's README should
   state its definition. With it the guesses are 0.092 / 0.184 / 0.124 at t 1 / 2 / 3 (the workplace simulation notes
   used <Z> = +1 / -1: 0.092 / 0.335 / 0.482; every simulated BEATS verdict is the same under both).
2. **Missing or non-operational elements are not printed.** The declaration reports the calibration beside "with any
   missing or non-operational element named"; `os3d_score.py` prints only the worst CZ and readout, but stores the
   whole calib_beside entry (missing_at, non_operational) in scores.json. The night's README should name them from
   there.
3. **The Qiskit version is not recorded.** SABRE's result with seed 0 depends on the Qiskit version (and on the CPU
   count if QISKIT_SABRE_ALL_THREADS or the sabre_all_threads setting is on; otherwise 5 trials). The job's gate hash
   pins the circuits that ran, so the verdicts are not affected; for a rebuild, write the Qiskit version (and that the
   variable is off) into the night's README.
4. Edge case only: R is infinite (HURTS) if B's MSE is exactly 0.
5. Consistent: tags g3d_t / sabre_t in the answers, the report and the score; R thresholds 0.8 / 1.25; retention for
   |M_exact| >= 0.1 (all M_exact are 0.32-0.70); CALIB_BESIDE files read from the run folder, as the procedure writes
   them; `--job` is the workplace version (45db463).

## A note for tonight (FakeFez only, not the device)

On the fez 11-05 build, SABRE's t 2 and t 3 circuits use coupler 68-69, which the FakeFez snapshot has as dead (CZ
error 1.0) and the 11-05 record does not mark failed (t 1 uses 106-107, likewise). Tonight's calibration beside will
show whether the device's coupler is bad today.
