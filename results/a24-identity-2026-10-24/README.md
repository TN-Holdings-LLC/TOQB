# PSF-Zero a24 builds TOQB's two PSF arms instruction for instruction (analysis for the a24 switch; 2026-10-24)

`python -m toqb.zip_a24_check zipper.json` and `... item31.json --item31` (toqb `c6655d1` plus
`toqb/zip_a24_check.py`; psf-zero `1294780`, psfbind built from it; Qiskit 2.5.2). Per (n, L) for n 10, 12, 14, 16 and
L 8, 16, 24, 32, one random model compiled for `snapshot:marrakesh`; the two compiled circuits compared instruction by
instruction (name, physical qubits, parameters to 1e-9).

- **The zipper:** TOQB's report-only `psfai:template_zip` (a22 / c61 with `toqb.ring_zip`, Python) against a24 with
  `PSF_RING_ZIP=1` (Rust ring r2): identical in 16 of 16.
- **Item 31:** TOQB's `psfai:template` on a22 / c61 (Python) against a24's default (Rust ring r2): identical in 16 of 16.

So the zipper of TOQB's runs (far teachers, zip_long, data_grad, zip_depth) is, circuit for circuit, PSF-Zero a24's
zipper, and switching TOQB's baseline from a22 / c61 to a24 changes no circuit at these sizes. Not checked: other
devices, odd n, other model structures.
