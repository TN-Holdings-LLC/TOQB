# Flow K (owner's go of 2026-10-27, "テスト１"): the same classifier on the same qubits, placed two ways — the count rule against the zipper on the rule's own cycle. Fixed by SHA-256 and CET time before the run

**Why.** Flow J compared three placements on one 20-qubit cycle (holes at n = 18, the bare ring at n = 20, pendants at
n = 22), but each n had its own random classifiers. Here the classifier, the inputs and the qubits stay the same and
only the schedule changes: the rule's schedule against the zipper laid along the same cycle's qubits.

- **Device.** `file:<target.pkl>`, the ibm_kingston Target of 2026-10-24 (SHA-256 3b939138…; the run stops if it
  differs); twin ("sim") only; noiseless reference by Qiskit's Statevector on the CPU (as flows G and J).
- **Arms.** `fold:rule` and `fold:zipcyc` (new, toqb this commit: the zipper schedule of toqb.ring_zip on the first n
  qubits, in cycle order, of the cycle `fold_place` gives; tests/test_fold.py checks it exact with 5n/2 - 4 two-qubit
  gates per layer on that cycle's qubits only, n = 8, 10). On this Target (compile, 2026-10-27):
  n = 18: rule = two holes on the 20-cycle (352 two-qubit gates, 6.7 us, 20 qubits); zipcyc = the zipper on 18 of the
  same qubits (656, 10.6 us; qubits 3-7, 17, 27, 26, 25, 37, 45-41, 36, 21, 22).
  n = 20: rule = the ring itself on the 20-cycle (320, 5.6 us); zipcyc = the zipper on the same 20 qubits (736,
  10.6 us).
- **Run.** L = 16, P = 24, T = 256, models 0-3 (seeds as in flows G and J), `--max-active 24`. The rule's rows are
  flow G's (n = 18) and flow J's (n = 20); **check (declared):** the run first repeats `fold:rule` at n = 18 and 20,
  model 0; if lam, q2 or us differs from those rows the run stops and nothing is reused. Then `fold:zipcyc` at n = 18
  and 20, models 0-3.
- **Rule, per n** (as flows G and I). A model is a win for the rule if its lam is larger than zipcyc's on the twin, a
  loss if smaller. **WIN**: 3 or 4 wins of 4; **LOSS**: 3 or 4 losses; else **TIE**.
- **Prediction (not a rule).** n = 20: WIN (the bare ring has 0.43 of the zipper's two-qubit gates and about half its
  duration on the same qubits). n = 18: no direction predicted (on this twin flow G's zipper, placed elsewhere, kept
  0.63-0.66 against the holes' 0.61-0.68).
- **Reported only.** Per n the four models' lam with standard errors for both arms; counts, duration; the ratio and
  shots as 1/lam^2; beside them flow G's psfai zipper at n = 18 (placed by PSF-Zero elsewhere on the device).
- **Expected time on one H100:** about 1 h alone (the GPU may be shared with flow J's n = 24, which only slows both).
- **Not claimed.** No device; one day's calibration of one device; random models; one cycle.
