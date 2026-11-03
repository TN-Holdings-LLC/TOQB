# P4: reproduction of the dual-unitary kicked Ising experiment (arXiv 2411.00765) on psf-os, no error mitigation (home, 2026-11-03)

**Why.** A hard problem with a known answer first; a problem of the same size without a known answer comes after,
in its own note. IBM ran this circuit on a 1D chain of ibm_strasbourg (51-91 qubits) and matched the exact answer
only with heavy error mitigation (noise learning, twirling, tensor-network mitigation); unmitigated, the signal
decayed faster than the exact one. Here: the same circuit, no mitigation, placed by psf-os.

**The problem** (`psf_os/dual.py`, psf-os 0fc96e5; SI Eq. S5). Open chain of N = 21 sites; |+> on site 0, Bell pairs on (1, 2),
(3, 4), ..., (19, 20); t brickwork layers (even pairs first) of U = e^{-ihZ_a} e^{-iJ ZZ} e^{-ib(X_a + X_b)} e^{-iJ ZZ}
e^{-ihZ_a} with J = b = pi/4; X readout of every site. Exact answer for t <= 10: <X_t> = cos(2h)^t on the light cone
(site t), 0 elsewhere. Checked: the circuit as compiled (CZ form, every gate 2 CZ) against the statevector, N = 11
(t <= 5, h 0 to 0.3) and N = 21 (t = 9, 10), all within 1e-6. CZs per circuit: 10 + 20 t (210 at t = 10).

**Built by** `gpu/du_repro.py` from one new fetch of ibm_kingston and the registry
`results/coverage-days-2026-11-02-day3/list_after.json` (its LISTED entries are valid 7 days; no new scan: the
sentinel in each job reads the ring at the job's time). Two jobs, 48 circuits each (h = 0, 0.05, 0.1, 0.15 x t = 0..10,
then the sentinel), 4000 shots, options off, "stay", sent with `psf-os submit`; 113 s by the time model.

| job | chain (positions 0..20 of the n = 40 ring) | in the dry run (fetch 2 Nov) |
|---|---|---|
| S | the rule's ring as fetched | 3 ... 29, 38, 49 ... 73: holds the listed path [28, 29, 38, 49] (chain positions 7-10) |
| V | the ring placed around the registry | 3 ... 29, 30 ... 33, 39, 53 ... 73: no listed path |

Dry run (fetch of 2 Nov, sentinel at the Clifford point, noiseless): both jobs accepted (every circuit's CZ count as
expected), on-cone values equal the exact ones within shot noise, sentinels CLEAN.

## Judged

1. **Sentinels:** S DEAD and V CLEAN expected (as in M6, 2 Nov). Reported as they come; a V that is not CLEAN is
   reported with its sites.
2. **The answer, raw (V):** over the 40 on-cone points (t = 1..10, four h), the mean squared error of <X_t> against
   the exact value, against the mean square of the exact values (the error of an output with no signal):
   READS if at most half of it, else DOES NOT READ (P3's rule). Reported: measured / exact per point.
3. **The decay rate (the paper's claim), V:** per h > 0, the ratio R(t) = <X_t>(h) / <X_t>(h = 0) (the same gates,
   Clifford at h = 0), fitted as R = k^t over t = 1..10 (weighted least squares on ln R). AGREES if
   |k - cos 2h| <= max(2 SE, 0.005), else DIFFERS (k, SE and cos 2h reported).
   - READS and AGREES at all three h: *psf-os reproduces the exact answer of the dual-unitary experiment without
     error mitigation on a 21-site chain.*
4. **OS against standard:** mean of measured / exact over the 40 on-cone points, V - S, 2 SE: HELPS / NO EFFECT /
   HURTS. Reported per t as well (S's listed path sits at chain positions 7-10, so a difference is expected from t = 7).

## Reported, not judged

Off-cone values (mean and largest |<X_n>|, n != t); t = 0 (readout of |+>); the sentinels' per-site signals; billed time.

**Stop.** One run of the two jobs. The second stage (b away from pi/4, no closed form, answer from a GPU computation)
needs its own note.
