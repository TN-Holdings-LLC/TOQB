# Flow C's procedure check (no IBM connection; 2026-10-24)

The whole flow C chain on a fake device, in the cloud container (CPU): `s2rc_device fetch --fake FakeMarrakesh`;
`toqb.device_reuse` for the zipper's and Qiskit's far-teacher models of teacher 17 (4 test points, `--traj 8`: the
procedure-check option; the device run uses the records' 1,024); `assemble --max-seconds 60` (3.8 s predicted);
`submit --local` (Aer with the fake device's noise); `result`; `toqb.flowc_score`. Every step ran; output as written
(`flowc_local.md`, `log.txt`, cloud paths written `<cloud>/`).

Sanity only, no reading: with the fake device as the "device", the twin rebuilt from the same fake Target matches its
scale (0.95 for the zipper, 1.02 for Qiskit), the 2026-10-13 snapshot's twin less so for the zipper (1.31). Four
points per arm.
