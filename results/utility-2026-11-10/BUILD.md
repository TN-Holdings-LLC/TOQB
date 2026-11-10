# Utility observables, 2026-11-10 (prereg/utility_2026-11-11.md)

- Declared at 22ecaf0 (pushed as 52a3a87 after the large-file fix, GitHub f67734c..52a3a87, 13:44 CET); queue read
  13:44:25 CET: marrakesh 1, fez 1, kingston 12 -> order marrakesh, fez (ties in the declared order).
- ibm_marrakesh: no observable's cone avoids the failed elements (failed qubits 30, 32, 34, 41, 46, 47, 48, 56, 73, 82,
  113, 119, 130, 136; coupler 113-119): not buildable -> ibm_fez.
- ibm_fez (failed qubits 72, 148, 149; coupler 32-33): z106_t4 and w10_t5 on embedding 0, w17_t5 and w17b_t5x on
  embedding 1; 80 circuits, 92.3 s by the model; CZ per circuit 564 / 705 / 690 / 690. Answers file sha256 92a989df...
  (it differs from the try-build's f19ae7ac... only in Z_106's last digits, at most 1.2e-15: the contraction order
  varies; the sealed weight-10 / weight-17 values are identical).
- Pre-run check (gpu/utility_check.py): ALL PASS (Clifford points of all four on the whole device; Z_106 all 17 k by
  its cone, 1.2e-13).
