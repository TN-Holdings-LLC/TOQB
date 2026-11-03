# P4 stage 2b: the same chain away from the dual-unitary point, N = 33, t <= 16, answers from a GPU computation sealed before the run (home, 2026-11-03)

**Why.** Stage 1 (`results/du-repro-2026-11-03`) read the closed-form answer without error mitigation at N = 21,
t <= 10. Away from b = pi/4 there is no closed form, and at N = 33 the answer needs 2^33 amplitudes (64 GB): a GPU
server. This is the last size whose answer can still be computed exactly; the stage after it (t = 20, N = 41) has no
exact answer and needs its own note. The answers are computed and sealed (SHA-256 in the record) before the device
run.

**The circuit** (`psf_os/dual.py`, psf-os 0fc96e5, unchanged): N = 33, t = 0..16 (CZ: 16 + 32 t, 528 at t = 16), X
readout of every site. Four settings in one job, 17 circuits each:

| setting | h | b | answer |
|---|---|---|---|
| Clifford control | 0 | pi/4 | closed form (1 on the light cone, 0 elsewhere) |
| dual-unitary control | 0.15 | pi/4 | closed form cos(0.3)^t on the light cone, 0 elsewhere |
| off 1 | 0.15 | pi/4 - 0.1 | GPU statevector |
| off 2 | 0.15 | pi/4 - 0.2 | GPU statevector |

Off 2 spreads the signal over the chain (at N = 21, t = 10: on-cone 0.21, root mean square over sites 0.17); off 1
keeps most of it on the light cone (0.48 at t = 10).

**Answers** (`gpu/du_answers.py`, `gpu/du_answers_pod.sh`, one GPU with 80 GB or more): the gates are read from
`dual.chain_circuit` itself; <X_n> of every site after every layer, single precision. Used only if three checks pass
(else STOP, no device run): C1 GPU code = numpy code at N = 21 (single 1e-4, double 1e-10); C2 single = double at
N = 31, t <= 14 (1e-4); C3 both controls at N = 33 equal the closed form (1e-4), norm within 1e-4. The numpy code
equals Qiskit's statevector at N = 9 (tests/test_du_answers.py). `answers.json` and its SHA-256 are committed before
the fetch.

**The job** (`gpu/du_stage2.py`): one job, V only: positions 0..32 of the n = 40 ring placed around the registry
(`results/coverage-days-2026-11-02-day3/list_after.json`; no new scan). S is not built: since IBM's record of
3 November marks (29, 38) and (9, 10) failed, the standard ring is V's ring (stage 1). 68 circuits + the sentinel
(4), 4000 shots, options off, "stay", `psf-os submit`; 83 s by the time model. Dry run (fetch of 3 November 02:17
CET): accepted (CZ counts as expected), chain 3-7, 17, 27-33, 39, 53-55, 59, 75-63, 56, 43; no listed path on it.

## Judged

1. **Sentinel:** CLEAN expected; otherwise reported with its sites.
2. **Dual-unitary control (stage 1 at depth 16):** the rate k from R(t) = <X_t>(h 0.15) / <X_t>(h 0), t = 1..16,
   as in stage 1: AGREES if |k - cos 0.3| <= max(2 SE, 0.005), else DIFFERS.
3. **Off 1 and off 2, raw:** over every site and t = 1..16 (33 x 16 values), the mean squared error of <X_n> against
   the answer, against the mean square of the answer: READS if at most half of it, else DOES NOT READ.
4. **Off 1 and off 2, on the light cone, normalised:** R(t) = <X_t>(off) / <X_t>(Clifford control), t = 1..16;
   the root mean square of R(t) - answer_t: AGREES if at most 0.05, else DIFFERS.
   - READS and AGREES on both: *psf-os gives the right answer, without error mitigation, on circuits whose answer
     needed a GPU server.*
   - READS on off 1 only: *the answer is read where it stays on the light cone, not where it spreads*.

## Reported, not judged

Per site and t: measured, answer, difference; the depth where the raw on-cone signal falls below 3 SE; the off-cone
error alone; the pod's checks and time; billed time.

**Stop.** One pod run (or its STOP), then one device run.
