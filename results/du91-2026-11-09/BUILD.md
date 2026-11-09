# Dual-unitary chain at N = 91 on a device (prereg/du91_2026-11-09.md)

- Declared at TOQB fd88a28 (pushed with 514b98e before the fetch). Queue read 11:59 CET 2026-11-09: marrakesh 0,
  fez 218, kingston 157 -> ibm_marrakesh. Record: failed qubits 46, 73, 82, 113, 119, 130; coupler 113-119.
- No shape qualifies; rule C places the chain: start (+1, row 0, column 0), 1665 steps, first start, suspect on.
- Jobs A (h 0, 0.05) and B (h 0.1, 0.15): 40 circuits each, 47.6 s by the model each, CZ up to 2205; answers
  e90f825e... equal the sealed index table (441c9c1a...) written on the chain's labels.
- Pre-run check on this build: the compiled h = 0 circuits of job A by the stabilizer method at full size: |<X>| = 1.000
  on the light-cone site at t = 4-24, the site the sealed answers name.
