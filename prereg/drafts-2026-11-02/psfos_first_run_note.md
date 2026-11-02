# psf-os's first device run: a byte-identical resend of job S through psf-os's own submit (home, 2026-11-02)

**Why.** Until now psf-os built jobs and TOQB's `s2rc_device` sent them. psf-os now has its own device layer
(`psf_os/ibm.py`: fetch, submit, collect; SamplerV2 with dynamical decoupling and twirling off; a job is tried only on
its own device and refused if a circuit touches an element the device marks as failed now; no quality number read).
Its first run is chosen to be the sure case: a job whose answer is already known on the device.

**What is run.** Job S of `results/m6-practice-2026-11-02` (standard n = 40 ring of ibm_kingston: sh6 at D = 12,
cluster parity, sentinel; 20 circuits, 1000 shots), copied unchanged (`circuits.qpy` SHA-256 checked against its
manifest), sent with `psf-os submit`, collected with `psf-os collect`, scored with `psf-os result`. No fetch is used
to build it; the submission check reads the device's failed marks at the time of sending. 9.1 s by the time model.

**Reference (the two earlier runs of the same circuits, 12:03 and 12:35 CET):** sentinel DEAD on qubits 3-7, 17,
27-29, 38, 49-55, 59; sh6 ring mean 0.780 and 0.770; parity right 0.482 and 0.472.

## Judged

1. **The chain:** psf-os submits, the job ends DONE, psf-os collects the counts and scores them. PASS or FAIL (with
   the step that failed).
2. **The same answer:** the sentinel reads DEAD with a dead run on the same 18 qubits; the sh6 ring mean lies within
   0.03 of 0.775; the parity's right fraction within 0.03 of 0.477. AGREES if all three hold, else DIFFERS (each
   reported).
- Both PASS and AGREES: *psf-os runs a job on the device by itself, with the same result as through TOQB.*
- PASS and DIFFERS: *the chain works; the device or the day differed* (reported, not a failure of the chain).
- A refusal at submission (a failed element under the job) is reported as such: *the check worked; the job was not
  sent*; nothing is judged on the answer.

**Stop.** One run.
