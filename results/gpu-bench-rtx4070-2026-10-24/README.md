# GPU benchmark on the owner's PC: RTX 4070 (12 GB), WSL (2026-10-24, before the a24 switch)

`toqb.check_traj 4000` and `toqb.bench_traj 10 16` (complex64) at toqb `c6655d1`, psf-zero `1294780`, a22 / c61, run by
the VS Code Claude. The check passed (largest 2.00 se). Against the H100 pod of 2026-10-23 (same commands):

| n = 10, L 16, item 31 | H100 | RTX 4070 | ratio |
|---|---|---|---|
| sim 50 x 256 | 16.8 s | 42.8 s | 2.5 |
| stand-in 2 x 200 | 7.2 s | 21.9 s | 3.0 |
| skeleton sim 50 x 256 | 11.7 s | 34.2 s | 2.9 |
| check, n = 6, Qiskit #1 | 2.7 s | 8.3 s | 3.1 |

The Qiskit line of the L 16 benchmark (14 active qubits) had not finished after about 60 minutes with the GPU memory
nearly full (11.9 of 12.3 GB) and was stopped (`Terminated` in the file): Qiskit's L 16 arm does not fit this GPU
for the benchmark's batch.
