# IBM's dual-unitary chain at N = 71, raw, through the user entrance (2026-11-07 night; prereg/du71_2026-11-07.md)

- Declared at TOQB bf0e37f, pushed before the fetch (f215e49..bf0e37f). Queue read 14:34:17 CET: marrakesh 0, fez 28,
  kingston 19; `gpu/daily_fetch.py` fetched marrakesh only (at most 10 pending). No shape qualifies on marrakesh
  (failed qubits 46, 73, 82, 113, 119, 130 on every copy; `fetch/marrakesh_device.json`), so by the declared rule the
  next by the queue: ibm_kingston, fetched by `psf-os fetch` at 14:35:25 CET.
- Built from that record: S1 at copy (0, 0), chain 0 .. 86 (rows 0-4), jobs A and B, 40 circuits and 47.6 s by the
  model each, CZ up to 1715, answers 07b6d574... (S1, as sealed).
