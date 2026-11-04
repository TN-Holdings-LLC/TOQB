# Sparse Pauli dynamics in Rust for P5 at t = 20 (workplace, 2026-11-04; not declared)

An independent classical value for P5 stage D (t = 20, no exact answer), checked first against the sealed exact
answers at t = 5-8. **Classical simulation only; not a device result, not a declared test.**

| file | content |
|---|---|
| `../../rust/spd/` | the Rust crate (no outside crates): Heisenberg-picture sparse Pauli dynamics with truncation delta, 192 qubits max, threads over qubits. `cargo test --release`: 6 tests (exact against a plain statevector at delta = 0 on a chain of 6 and a ring-with-pendant of 10, theta 0.4-1.3, t 1-5, 1e-10; qubit words beyond 64; truncation sanity; the layered mode against a statevector of a 9-qubit P6-shaped piece at the P6 angles, t 1-4, and against the P5 code at RZZ(-pi/2)) |
| `spd_check.py` | drives the binary on lattice b of `results/kim-cd-2026-11-03` and compares with `answers_cpu.json` (t = 5) and `answers_pod/answers_C.json` (t = 6, 7, 8) |
| `spd_tables.py` | prints the tables below from `out/*.jsonl` |
| `spd_pod.sh` | for home: the same at delta 3e-5 and 1e-5 on a many-core pod (CPU only) |
| `spd_p6_check.py` | P6 (the Qedma patch) through the layered mode (`rust/spd/src/layers.rs`, binary `spd_layers`: RX, RZ, RZZ(theta) layers; RZZ at a generic angle branches), against the sealed answers t = 1..9 |
| `指示書_SPD_POD_2026-11-04.md` | the pod instruction for the VS Code Claude (after the bank pod) |
| `out/` | JSONL records (per qubit: value, peak term count, seconds) and run logs |

Rules (as `gpu/spd_proto.py`, checked equal: qubit 0, theta 0.8, t 8, delta 1e-4 gives 0.7064292438257 and 55,273 peak
terms in both): RX(theta): Z -> cos Z + sin Y, Y -> cos Y - sin Z, branches under delta dropped as made and merged
terms under delta dropped; RZZ(-pi/2) on an edge with X on one side: X -> Y Z, Y -> -X Z, exact; the first RZZ layer
left out. Speed at theta 0.8, t 8, delta 1e-4: up to 1.1 s per qubit (qubit 2, 670,307 peak terms) on a 2-core
machine, where the prototype's note gives 13 s per qubit in Python (not timed on the same qubits here).

Tables: `python spd_tables.py` (numbers quoted in the workplace report of 2026-11-04).
