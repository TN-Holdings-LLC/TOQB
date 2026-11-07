# 3D v3.1 at 4 x 6 x 3 (72 sites, 87 qubits) on a device with the pre-run gate (2026-11-07 daytime JST;
prereg/os3d_big_2026-11-07.md)

- Declared at TOQB 5de612d, pushed before the fetch (6f83d5e..5de612d). Queue read 03:44:14 CET: pending marrakesh 1,
  fez 1, kingston 6. 4 x 6 x 3 translations avoiding every failed element: marrakesh none, fez (0, 0) and (1, 0),
  kingston (0, 0) -> ibm_fez (fewest pending among those that qualify; tie with marrakesh, which does not qualify).
- Built here from `ibm_fez/dev/device.json` (failed qubits 72, 148; coupler 32-33): 37 circuits, 44.3 s by the model,
  gates 6d4a92075415, answers sha256 bd39df03... (k = 2, as sealed). Candidates 0 (r0 0, c0 0), 1 (r0 1, c0 0).
  CZ per arm 750 / 1500 / 2250 (layers 35 / 70 / 104). psf-os 55167cf (plus the long-standing local additions).
