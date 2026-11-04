# DRAFT (not declared): how much the device moves from run to run and day to day, before any phenomenon is claimed (workplace, 2026-11-04)

Status: a draft for home and the owner. It uses only builders that exist (`gpu/p6_device.py` cells, `psf-os submit`).

**Why.** Every verdict so far compares one run with an exact answer, and the answer card separates chance (shot noise)
from bias. A third part is missing: how much the bias itself moves between runs. Two back-to-back runs of the same
circuit already differed by 2.4 SE (home's count, 11/04). Before a 2D phenomenon (correlations, spreading, area) is
claimed from a difference of a few hundredths, the size of this movement has to be known.

## Design

- **The job:** P6 at t = 1..5 (theta_x 0.53) with its theta_x = 0 floor at t = 1 and 5 and the ring sentinel: 11
  circuits, 4000 shots, about 15 s by the time model. Answers sealed (P6's CPU answers).
- **Runs:** the same job, rebuilt from that day's fetch, on the **same device** (the first day's device, chosen by
  queue as P6's rules; kept fixed for days 2 and 3 so that the device does not vary), on three different days, and on
  day 1 twice in a row (back to back), to separate within-day from between-day movement.
- **Placement:** P6's rules each day (the copy may change if the failed marks change; then that is recorded and the
  comparison is reported per copy).

## Quantities

- Per t and per qubit: <Z_q> and its SE in each run.
- **Run-to-run excess:** for two runs r, s: chi2 = sum over qubits and t of (z_r - z_s)^2 / (SE_r^2 + SE_s^2), divided
  by the number of terms. About 1 means the runs differ only by shot noise; larger means the device moved.
- For the magnetisation: |M_r - M_s| in units of its combined SE, per t.
- The floor's movement the same way (readout drift is a likely part).

## Judged (proposed)

1. **Back to back (day 1):** STABLE if the per-term chi2 is at most 2; MOVES otherwise.
2. **Day to day:** the same statistic for days 1-2, 2-3, 1-3.
3. The outcome sets the **minimum difference** a later 2D claim may rest on: a difference smaller than twice the
   observed run-to-run spread of M is not reported as a phenomenon (proposal for the owner).

## Reported, not judged

Per-qubit maps of the run-to-run differences in SE units (where the device moves); whether the moving qubits are those
the mirror sentinel or rule R flag; the queue and the billed time.
