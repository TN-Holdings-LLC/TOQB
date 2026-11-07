# 3D v3.1 with the pre-run gate on a device (2026-11-07 daytime JST; prereg/os3d_gate_2026-11-07.md)

- Declared at TOQB 1ad49e2 (committed 03:19 CET). The first push failed (the bundle carried no `main` ref), so a first
  queue reading and fetch (`fetch_unused/`, 03:21 CET) happened before the declaration was public; it is not used.
  After the push (73cda75..1ad49e2 on GitHub), a second fetch (`fetch2/`, 03:22:57 CET): pending marrakesh 0, fez 5,
  kingston 10 -> ibm_marrakesh (the fewest).
- Built here from `ibm_marrakesh/dev/device.json` (fetched 03:23:02 CET; failed qubits 46, 73, 82, 113, 119, 130,
  coupler 113-119): 61 circuits, 71.1 s by the model, gates e600779e3efc, answers sha256 0bce0dab... (k = 4, as
  sealed). psf-os 55167cf (plus the long-standing local additions in circuits.py and job.py), qiskit 2.5.2.
- Candidates (fixed order): 0 (r0 1, c0 8), 1 (3, 4), 2 (5, 0), 3 (0, 0). Probes at t = 1.
