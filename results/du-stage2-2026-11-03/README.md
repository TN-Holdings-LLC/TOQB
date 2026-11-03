# P4 stage 2b, 2026-11-03: away from the dual-unitary point, N = 33, t <= 16 (528 CZ), without error mitigation: both off points READ and AGREE with answers computed on a GPU server and sealed before the run

- **Declaration:** `prereg/drafts-2026-11-03/du_stage2_note.md` (SHA-256 cb97a0c2...1764d65), fixed 02:36 CET, TOQB
  4a2238b; psf-os 0fc96e5 (`psf_os/dual.py`, unchanged since stage 1).
- **Answers:** `answers/` (RunPod H100 80GB, 02:46-03:00 CET, `gpu/du_answers_pod.sh` at fa6b9eb); sealed in 26ed041
  (answers.json SHA-256 b5ba060d...14b4b7) before the fetch. Checks C1 <= 1.03e-5, C2 <= 1.29e-5, C3 <= 3.47e-5
  (tolerance 1e-4). The first pod run stopped before C1 (CUDA C++14 against cupy 14.2.0; fixed in fa6b9eb).
- **Job:** V dbkkbhonceqs73am37qg, built by `gpu/du_stage2.py` from the fetch of 03:22:49 CET (calibration 03:04:31
  CET, target e165e450...; failed marks as at 02:17 CET), sent with `psf-os submit` at 03:24:07 CET, options off,
  "stay"; DONE, 78 s billed. 72 circuits x 4000 shots. Chain (positions 0..32 of the ring around the registry):
  3-7, 17, 27-33, 39, 53-55, 59, 75-63, 56, 43. Scored by `gpu/du_stage2_score.py` (50163a4, written before the
  answers): `scores.json`.

## Judged

| | result | verdict |
|---|---|---|
| 1. sentinel | CLEAN | as expected |
| 2. dual-unitary control, rate over t = 1..16 | k = 0.9559 +- 0.0008 (cos 0.3 = 0.9553) | **AGREES** |
| 3. off 1 (b = pi/4 - 0.1), every site, t = 1..16 | MSE 0.0007 (half the answer's mean square: 0.0090) | **READS** |
| 3. off 2 (b = pi/4 - 0.2) | MSE 0.0008 (0.0151) | **READS** |
| 4. off 1, on-cone normalised by the Clifford control | RMS 0.023 (limit 0.05) | **AGREES** |
| 4. off 2 | RMS 0.037 | **AGREES** |

**Sentence fixed in advance:** *psf-os gives the right answer, without error mitigation, on circuits whose answer
needed a GPU server.*

## Reported

- On the light cone, normalised, against the answer (t = 4, 8, 12, 16): off 1 0.756 / 0.545 / 0.376 / 0.261 against
  0.771 / 0.570 / 0.394 / 0.275; off 2 0.618 / 0.196 / 0.177 / 0.179 against 0.673 / 0.262 / 0.209 / 0.140. Off 2's
  largest misses (0.05-0.07 at t = 3-8) are where its answer turns from the cone into the chain.
- Raw (no division): the Clifford control keeps 0.72 of its exact value 1 at t = 16 (528 CZ); the raw on-cone signal
  never falls below 3 SE (smallest 0.126 for off 2).
- Off-cone error alone (MSE): 0.0005 (off 1), 0.0007 (off 2).
- The READS rule compares with an output with no signal; most of the 528 values per point are small, so it is a lenient
  bar. Judgement 4 (on-cone, 0.05) is the tighter one.
- Scale: 33 qubits and 528 CZ on the device; the answer needed 2^33 amplitudes (64 GB, 124 s per setting on an H100).
  This is the last size with an exact answer by statevector; t = 20 (N = 41) has none.
