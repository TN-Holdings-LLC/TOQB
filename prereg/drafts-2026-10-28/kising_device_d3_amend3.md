# Device test D3, amendment 3 (owner, 2026-10-28: "やはりL＝２４に変える"): the depth is L = 24, as amendment 1. Fixed by SHA-256 and CET time before the fetch; nothing of D3 had run

- **Changed:** amendment 2 (back to L = 50, SHA-256 40484553…) is withdrawn; amendment 1 (SHA-256 2828c7a9…) holds:
  L = 24, inputs the first 64 of flow M's seed-0 draw at L = 24, everything else as kising_device_d3_note.md
  (SHA-256 558aa6cd…).
- **Purpose, stated by the owner's discussion before the run:** n = 20 is simulable on a PC at any L; the device
  point does not compute anything new. It checks whether the day's twin, on which flows I-M and Paper 4's lam rest,
  describes the device at 480 two-qubit gates. L = 24 is chosen because the twin's lam_K there (0.291 on the
  2026-10-24 calibration, correlation 0.93-0.97) is large against the expected device SE (about 0.02), so both SIGNAL
  and the twin comparison should be decidable; at L = 50 they likely were not.
