# Device test D5, amendment 2 (owner, 2026-10-28: "Quiskitはじっきだけだよ"): Qiskit's circuits go to the device only; no twin simulation of them. Fixed by SHA-256 and CET time; D5's pod step was stopped before the Qiskit cell was built

- **Changed:** part A's Qiskit cell is built with `--twin none` (amendment 1 had `--twin auto`, which would simulate
  it on the pod). Only the device comparison rule - Qiskit (WIN / LOSS / TIE within 2 SE) is made for Qiskit; no
  Qiskit-against-twin verdict.
- **The pod step:** D5's first run (TOQB 7148f53, started 13:04:06 CET) was stopped after the cells already built.
  `gpu/device_d5b.sh` continues in the same folder: a cell whose record exists is not rebuilt (`lam_device build`
  refuses to overwrite and the script goes on), the others are built as declared, the Qiskit cell without a twin.
- Everything else as device_d5_note.md (4d737d05…) and amendment 1 (3b83d226…).
