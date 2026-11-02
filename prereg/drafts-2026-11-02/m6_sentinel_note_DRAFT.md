# OS plan M6: sentinels in the user's job (DRAFT by the workplace, 2026-11-02; NOT DECLARED — the owner decides, and
home fixes it by SHA-256 and CET time before any fetch)

## Question

Does a sentinel (the rule's mirror echo on the user's own ring, in the user's own job) report the state of that ring
at the time the job ran? In particular, does it catch a defect that the morning scan did not list?

## What is run (psf-os M6 prototype, `psf_os/sentinel.py`)

- **User job:** the period-6 forward identity (`sh6`, D = 12, n = 40, four inputs and their readout references).
- **Sentinel:** the echo (D = 24, hz 0, h 0.6, four inputs, no references) on the same ring, compiled on the same device
  record, assembled after the user's circuits in the same submission. The user's circuits are byte-identical with or
  without the sentinel (psf-os test S1).
- **Verdict (the registry's rules, unchanged):** a dead run (a_j < 0.12 on 3 or more consecutive sites) -> DEAD; else a
  weak run (a_j < max(0.12, half the ring median)) -> WEAK; else CLEAN. Reported with the ring positions and qubits.
- **Registry:** the sentinel's runs enter the next registry file as gray entries of that day; they do not count
  towards LISTED.

## Part 1, the sure case first (ibm_kingston)

- **Job S:** the user job on the standard n = 40 ring, which holds the LISTED path [28, 29, 38, 49] (dead on 30, 31
  October and 1 November).
  - Expected: DEAD, with a dead run covering positions of qubits 3-59.
  - *Sentence fixed in advance:* "the sentinel sees the known dead run in the user's job".
  - If it reads CLEAN or WEAK, the sentence is "the sentinel missed a known dead run", and Part 2 is not run.
- **Job V:** the same user job on the ring placed around the day's registry.
  - Expected: CLEAN.
  - If WEAK or DEAD, the sentence is "a defect not in the morning's registry was present at the job's time". Its
    positions are reported, and they enter the registry as gray.

## Part 2 (only if Part 1 holds; a later day)

The same two jobs, submitted about 60-90 minutes after the morning scan. 31 October showed a gray stretch that came and
went within about 90 minutes. Part 2 is reported, not judged: one more data point on how often the morning registry
differs from the job-time state.

## Cost (time model: 0.036 s per circuit + 0.00027 s per shot + 3 s per job)

12 circuits (8 user + 4 sentinel) x 1000 shots: 12 x 0.036 + 12 x 1000 x 0.00027 + 3 = 6.7 s per job. Part 1 is two
jobs, about 13.3 s. Billed time has been 0.72-1.0 of the model.

## Stop rule

- **Stop.** Part 1, job S reading CLEAN.
- **Effect size.** A WEAK verdict is weighed by the run's mean signal against the ring median. A run within 0.05 of
  the weak line is reported as "borderline". It is not counted as a catch.

## Not claimed

The sentinel shows the ring's state at job time; it does not correct the user's result. The cause of a defect is not
chased.
