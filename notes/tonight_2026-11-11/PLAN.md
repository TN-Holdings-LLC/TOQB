# Tonight's device runs, prepared in advance (home, 2026-11-11 09:40 CET; written before any record of tonight)

Owner 17:03 / 17:05 JST: prepare the home device tests; build ahead whatever takes time.

## Jobs

1. Depth scan, `prereg/utility_depth_2026-11-11.md`: device by `gpu/utility_depth_pick.py FETCH_DIR`; build
   `gpu/utility_build.py ... --max-seconds 160` (32 s here); pre-run check `gpu/utility_check.py` (about 5 min).
2. Classifier series, job 3, `prereg/qclf_2026-11-10.md`: build `gpu/qclf_build.py` (about 200 s here); noiseless
   check `gpu/qclf_check.py` (25-34 min on 2 CPUs) unless carried over (below).

## Determinism (checked today)

- Classifier: rebuilt from the 11-10 records, fez and kingston give the committed gate hashes exactly
  (7d98a8c2..., a2f3f3b3...).
- Depth scan: rebuilt from the same 11-10 fez record, the same gate hash as the try-build. The answers file's sha256
  differs between builds (81f46f24... and 0394716a...) by the Z_106 4-step value's float noise from the contraction
  order (as on 11-10); the night's answers are compared with the sealed files by value (1e-12), not by hash.

## Carry-over of a check (fixed now, before tonight)

- A build whose gate hash equals that of a build whose check PASSED carries that PASS (the circuits are the same bytes).
- Classifier only: `gpu/qclf_canon.py` hashes the user, floor and mirror circuits relabelled from physical qubits to
  the measured map's bit order. The two 11-10 builds (fez and kingston, different placements, both full checks PASS)
  have the same canonical hash 0b7032ec5657ba35b0fc6dc4e7ef677d4d46278c286161e01701058a06644d4c. Tonight's build with
  this canonical hash carries the PASS (qclf_check reads each circuit on its active qubits by the measured map, so the
  noiseless result is the same); any other hash, or a refusal, runs the full check.
