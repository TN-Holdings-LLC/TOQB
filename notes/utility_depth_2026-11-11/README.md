# Depth scan of the 2023 utility observables: try-build (home, 2026-11-11; not a run)

Declaration draft: `prereg/utility_depth_2026-11-11.md` (task A of the owner's list, 14:28 JST).

- Exact values for Z_106 at 5, 6, 7 steps computed with `gpu/reach_tn.py` (Clifford points against Aer stabilizer on
  127 qubits: |diff| <= 2.2e-16); 8 steps and weight-10 at 6 steps from 11-11 morning (`notes/reach_2026-11-11`).
  All sealed (sha256 in the declaration).
- `gpu/utility_tn.py`: OBS gains z106_t5..t8, w10_t6, w10_t7 (existing keys unchanged).
- `gpu/utility_check.py`: exact stabilizer expectation at k = 0, 16 (strict for exact 0); pruned-cone statevector up to
  25 qubits (Aer above 20; qiskit.quantum_info hit the 50 min limit at 25); quimb light-cone contraction of the
  compiled job circuit at k = 5, 11 for deeper cones.
- Try-build on the 11-10 ibm_fez record: `trybuild_report_fez_1110record.json` (all seven on embedding 0, 137 circuits,
  155.9 s by the model); pre-run check `trybuild_check.txt`: ALL PASS.
