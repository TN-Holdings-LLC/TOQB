# TOQB weakness report

756 records from 1 run(s). Nothing here is a score.

## Failures (stopped or failed), by where they were stopped

| compiler | kind | where (innermost own frame) | input size | qubits | family | n | first case |
|---|---|---|---|---|---|---|---|
| tket:2 | time | adapters.py:190 compile | 2q <100 | qubits <=16 | HamLib | 7 | test_hamiltonians[ham_ham_parity10-all-to-all] |
| tket:2 | time | adapters.py:190 compile | 2q 100-1k | qubits >100 | QASMBench | 6 | test_QASMBench_large[adder_n118-all-to-all] |
| tket:2 | time | adapters.py:190 compile | 2q 100-1k | qubits 17-100 | QASMBench | 4 | test_QASMBench_medium[square_root_n18-all-to-all] |
| tket:2 | time | adapters.py:190 compile | 2q <100 | qubits 17-100 | HamLib | 4 | test_hamiltonians[ham_bh_graph-1D-grid-nonpbc-qubitnodes_ |
| tket:2 | time | adapters.py:190 compile | 2q <100 | qubits 17-100 | HamLib, FakeTorino | 4 | test_hamlib_hamiltonians_transpile[ham_graph-2D-grid-nonp |
| tket:2 | time | adapters.py:190 compile | 2q <100 | qubits >100 | HamLib | 4 | test_hamiltonians[ham_will199gpia,n-60,rinst-8-all-to-all |
| tket:2 | time | adapters.py:190 compile | 2q 100-1k | qubits 17-100 | Feynman, FakeTorino | 3 | test_feynman_transpile[adder_8.qasm] |
| tket:2 | time | adapters.py:190 compile | 2q 10k-100k | qubits 17-100 | QASMBench | 3 | test_QASMBench_medium[bwt_n21-square] |
| tket:2 | adapter | - | 2q <100 | qubits <=16 | QASMBench | 2 | test_QASMBench_small[ipea_n2-square] |
| tket:2 | time | adapters.py:190 compile | 2q 1k-10k | qubits <=16 | QASMBench | 2 | test_QASMBench_small[vqe_uccsd_n6-all-to-all] |
| tket:2 | time | adapters.py:190 compile | 2q <100 | qubits 17-100 | Feynman, FakeTorino | 2 | test_feynman_transpile[qcla_mod_7.qasm] |
| psf:recommended | other | psf_compile.py:3242 compile_for_hardware | 2q 1k-10k | qubits <=16 | Feynman, FakeTorino | 1 | test_feynman_transpile[hwb8.qasm] |
| qiskit:3:target | time | qiskit/transpiler/passes/layout/vf2_post_layout.py:144 run | 2q 100-1k | qubits >100 | QASMBench | 1 | test_QASMBench_large[bv_n280-square] |
| qiskit:3:target | time | qiskit/transpiler/passes/layout/vf2_post_layout.py:144 run | 2q <100 | qubits >100 | QASMBench | 1 | test_QASMBench_large[bv_n140-square] |
| tket:2 | adapter | - | 2q 100-1k | qubits >100 | QASMBench | 1 | test_QASMBench_large[cc_n151-all-to-all] |
| tket:2 | adapter | - | 2q <100 | qubits 17-100 | QASMBench | 1 | test_QASMBench_large[cc_n64-linear] |
| tket:2 | other | sympy/core/numbers.py:1489 _new | 2q 1k-10k | qubits 17-100 | QASMBench | 1 | test_QASMBench_large[32-all-to-all] |
| tket:2 | time | adapters.py:190 compile | 2q 100-1k | qubits <=16 | QASMBench | 1 | test_QASMBench_medium[gcm_h6-heavy-hex] |
| tket:2 | time | adapters.py:190 compile | 2q 10k-100k | qubits >100 | QASMBench | 1 | test_QASMBench_large[multiplier_n400-square] |
| tket:2 | time | adapters.py:190 compile | 2q 1k-10k | qubits 17-100 | QASMBench | 1 | test_QASMBench_large[multiplier_n75-linear] |
| tket:2 | time | adapters.py:190 compile | 2q 1k-10k | qubits <=16 | Feynman, FakeTorino | 1 | test_feynman_transpile[hwb8.qasm] |
| tket:2 | time | adapters.py:190 compile | 2q <100 | qubits <=16 | HamLib, FakeTorino | 1 | test_hamlib_hamiltonians_transpile[ham_ham_JW-8] |
| tket:2 | time | adapters.py:190 compile | 2q <100 | qubits >100 | HamLib, FakeTorino | 1 | test_hamlib_hamiltonians_transpile[ham_queen13_13,n-28,ri |
| tket:2 | time | adapters.py:190 compile | 2q >=100k | qubits <=16 | QASMBench | 1 | test_QASMBench_medium[factor247_n15-all-to-all] |
| tket:2 | time | adapters.py:205 _to_qiskit | 2q <100 | qubits >100 | HamLib | 1 | test_hamiltonians[ham_graph-2D-triag-pbc-qubitnodes_Lx-19 |

## Slow: returned, but over 3x the reference's time

| compiler | input size | qubits | family | n | median time / reference | first case |
|---|---|---|---|---|---|---|
| tket:2 | 2q <100 | qubits 17-100 | QASMBench | 19 | 17.2 | test_QASMBench_medium[ising_n26-all-to-all] |
| tket:2 | 2q <100 | qubits <=16 | QASMBench | 16 | 14.6 | test_QASMBench_small[qpe_n9-all-to-all] |
| tket:2 | 2q <100 | qubits <=16 | HamLib | 8 | 15.1 | test_hamiltonians[ham_ham_parity-4-square] |
| psf:default | 2q <100 | qubits <=16 | HamLib | 4 | 3.4 | test_hamiltonians[ham_ham_parity10-all-to-all] |
| psf:recommended | 2q <100 | qubits <=16 | HamLib | 4 | 3.5 | test_hamiltonians[ham_ham_parity10-all-to-all] |
| psf:recommended | 2q <100 | qubits 17-100 | HamLib, FakeTorino | 3 | 3.8 | test_hamlib_hamiltonians_transpile[ham_mu_y_prime_enc_una |
| tket:2 | 2q 100-1k | qubits <=16 | QASMBench | 3 | 50.7 | test_QASMBench_small[hhl_n7-heavy-hex] |
| tket:2 | 2q <100 | qubits 17-100 | HamLib | 3 | 24.7 | test_hamiltonians[ham_mu_y_prime_enc_stdbinary_dvalues_4- |
| psf:recommended | 2q <100 | qubits <=16 | Feynman, FakeTorino | 2 | 4.3 | test_feynman_transpile[barenco_tof_4.qasm] |
| psf:recommended | 2q <100 | qubits <=16 | HamLib, FakeTorino | 2 | 42.8 | test_hamlib_hamiltonians_transpile[ham_mu_y_prime_enc_gra |
| tket:2 | 2q <100 | qubits <=16 | Feynman, FakeTorino | 2 | 46.9 | test_feynman_transpile[barenco_tof_4.qasm] |
| tket:2 | 2q <100 | qubits <=16 | HamLib, FakeTorino | 2 | 14.1 | test_hamlib_hamiltonians_transpile[ham_mu_y_prime_enc_gra |
| psf:default | 2q <100 | qubits 17-100 | HamLib, FakeTorino | 1 | 3.4 | test_hamlib_hamiltonians_transpile[ham_bh_graph-2D-triag- |
| psf:default | 2q <100 | qubits >100 | HamLib | 1 | 3.0 | test_hamiltonians[ham_will199gpia,n-60,rinst-8-all-to-all |
| qiskit:3:target | 2q 100-1k | qubits >100 | QASMBench | 1 | 3.4 | test_QASMBench_large[bv_n280-heavy-hex] |
| qiskit:3:target | 2q <100 | qubits 17-100 | HamLib, FakeTorino | 1 | 3.8 | test_hamlib_hamiltonians_transpile[ham_mu_y_prime_enc_una |
| qiskit:3:target | 2q <100 | qubits >100 | HamLib | 1 | 4.6 | test_hamiltonians[ham_graph-2D-triag-nonpbc-qubitnodes_Lx |
| tket:2 | 2q <100 | qubits 17-100 | HamLib, FakeTorino | 1 | 25.5 | test_hamlib_hamiltonians_transpile[ham_mu_y_prime_enc_una |
| tket:2 | 2q <100 | qubits >100 | HamLib | 1 | 6.8 | test_hamiltonians[ham_graph-2D-grid-pbc-qubitnodes_Lx-4_L |
| tket:2 | 2q <100 | qubits >100 | QASMBench | 1 | 49.7 | test_QASMBench_large[bv_n140-square] |

## Worse: more than 10% more two-qubit gates than the reference

| compiler | input size | qubits | family | n | median (q2 + 1) / (reference + 1) | first case |
|---|---|---|---|---|---|---|
| qiskit:1:target | 2q <100 | qubits <=16 | HamLib | 13 | 1.28 | test_hamiltonians[ham_ham_parity-4-square] |
| qiskit:1:target | 2q <100 | qubits <=16 | QASMBench | 13 | 1.19 | test_QASMBench_small[dnn_n2-all-to-all] |
| tket:2 | 2q <100 | qubits <=16 | QASMBench | 13 | 1.32 | test_QASMBench_small[qec_en_n5-all-to-all] |
| qiskit:1:target | 2q <100 | qubits 17-100 | HamLib | 7 | 1.39 | test_hamiltonians[ham_bh_graph-1D-grid-nonpbc-qubitnodes_ |
| tket:2 | 2q <100 | qubits 17-100 | QASMBench | 7 | 1.89 | test_QASMBench_medium[cat_state_n22-heavy-hex] |
| psf:default | 2q <100 | qubits 17-100 | HamLib | 4 | 1.13 | test_hamiltonians[ham_bh_graph-1D-grid-nonpbc-qubitnodes_ |
| psf:recommended | 2q <100 | qubits 17-100 | HamLib | 4 | 1.13 | test_hamiltonians[ham_bh_graph-1D-grid-nonpbc-qubitnodes_ |
| qiskit:1:target | 2q 100-1k | qubits <=16 | QASMBench | 4 | 2.30 | test_QASMBench_small[hhl_n7-heavy-hex] |
| qiskit:1:target | 2q <100 | qubits 17-100 | HamLib, FakeTorino | 4 | 1.27 | test_hamlib_hamiltonians_transpile[ham_mu_y_prime_enc_una |
| qiskit:1:target | 2q <100 | qubits 17-100 | QASMBench | 4 | 1.47 | test_QASMBench_medium[knn_n25-all-to-all] |
| qiskit:1:target | 2q <100 | qubits <=16 | HamLib, FakeTorino | 4 | 1.80 | test_hamlib_hamiltonians_transpile[ham_mu_y_prime_enc_gra |
| qiskit:1:target | 2q <100 | qubits >100 | HamLib | 4 | 1.22 | test_hamiltonians[ham_will199gpia,n-60,rinst-8-all-to-all |
| qiskit:1:target | 2q 100-1k | qubits 17-100 | Feynman, FakeTorino | 3 | 1.19 | test_feynman_transpile[ham15-high.qasm] |
| qiskit:1:target | 2q 100-1k | qubits >100 | QASMBench | 3 | 1.13 | test_QASMBench_large[bv_n280-square] |
| qiskit:1:target | 2q 100-1k | qubits 17-100 | QASMBench | 2 | 1.46 | test_QASMBench_medium[qft_n18-square] |
| qiskit:1:target | 2q 1k-10k | qubits <=16 | QASMBench | 2 | 1.13 | test_QASMBench_small[vqe_uccsd_n6-all-to-all] |
| qiskit:1:target | 2q <100 | qubits 17-100 | Feynman, FakeTorino | 2 | 1.24 | test_feynman_transpile[qcla_mod_7.qasm] |
| qiskit:1:target | 2q <100 | qubits <=16 | Feynman, FakeTorino | 2 | 1.21 | test_feynman_transpile[barenco_tof_4.qasm] |
| psf:default | 2q 100-1k | qubits 17-100 | QASMBench | 1 | 1.14 | test_QASMBench_medium[qft_n18-square] |
| psf:default | 2q 100-1k | qubits <=16 | QASMBench | 1 | 1.23 | test_QASMBench_small[hhl_n7-heavy-hex] |
| psf:default | 2q <100 | qubits <=16 | QASMBench | 1 | 1.15 | test_QASMBench_small[simon_n6-heavy-hex] |
| psf:default | 2q <100 | qubits >100 | HamLib | 1 | 1.13 | test_hamiltonians[ham_fh-graph-1D-grid-pbc-qubitnodes_Lx- |
| psf:recommended | 2q 100-1k | qubits 17-100 | QASMBench | 1 | 1.14 | test_QASMBench_medium[qft_n18-square] |
| psf:recommended | 2q 100-1k | qubits <=16 | QASMBench | 1 | 1.23 | test_QASMBench_small[hhl_n7-heavy-hex] |
| psf:recommended | 2q <100 | qubits 17-100 | HamLib, FakeTorino | 1 | 1.11 | test_hamlib_hamiltonians_transpile[ham_reg-4_n-90_rinst-0 |
| psf:recommended | 2q <100 | qubits <=16 | QASMBench | 1 | 1.15 | test_QASMBench_small[simon_n6-heavy-hex] |
| psf:recommended | 2q <100 | qubits >100 | HamLib | 1 | 1.13 | test_hamiltonians[ham_fh-graph-1D-grid-pbc-qubitnodes_Lx- |
| psf:recommended | 2q <100 | qubits >100 | HamLib, FakeTorino | 1 | 1.16 | test_hamlib_hamiltonians_transpile[ham_queen13_13,n-28,ri |
| qiskit:1:target | 2q 10k-100k | qubits 17-100 | QASMBench | 1 | 1.11 | test_QASMBench_medium[bwt_n21-square] |
| qiskit:1:target | 2q 1k-10k | qubits <=16 | Feynman, FakeTorino | 1 | 1.15 | test_feynman_transpile[hwb8.qasm] |
| qiskit:1:target | 2q >=100k | qubits <=16 | QASMBench | 1 | 1.10 | test_QASMBench_medium[factor247_n15-all-to-all] |
| tket:2 | 2q 100-1k | qubits <=16 | QASMBench | 1 | 1.13 | test_QASMBench_small[hhl_n7-heavy-hex] |
| tket:2 | 2q <100 | qubits 17-100 | HamLib | 1 | 1.16 | test_hamiltonians[ham_tsp_prob-ts225_Ncity-5_enc-unary-li |
| tket:2 | 2q <100 | qubits <=16 | Feynman, FakeTorino | 1 | 1.33 | test_feynman_transpile[gf2^5_mult.qasm] |
| tket:2 | 2q <100 | qubits <=16 | HamLib | 1 | 1.25 | test_hamiltonians[ham_ham_parity-4-square] |
| tket:2 | 2q <100 | qubits <=16 | HamLib, FakeTorino | 1 | 1.13 | test_hamlib_hamiltonians_transpile[ham_mu_y_prime_enc_gra |
| tket:2 | 2q <100 | qubits >100 | QASMBench | 1 | 1.32 | test_QASMBench_large[bv_n140-square] |

## Reproducing a group's first case

Each command runs one measurement with the same limits and writes a cProfile of its warm-up compile, also when the compile is stopped (`python -m pstats repro.prof`). Run from the TOQB clone, with the run's environment ($TOQB_BENCHPRESS, $PSF_ZERO_REPO).

- failures, tket:2 / time / adapters.py:190 compile / 2q <100 / qubits <=16 / HamLib:

  ```bash
  python -m toqb.runner one --adapter tket:2 --case 'bp:test_hamiltonians[ham_ham_parity10-all-to-all]' --device 'bp:test_hamiltonians[ham_ham_parity10-all-to-all]' --b10-s 0.565483 --profile repro.prof
  ```

- failures, tket:2 / time / adapters.py:190 compile / 2q 100-1k / qubits >100 / QASMBench:

  ```bash
  python -m toqb.runner one --adapter tket:2 --case 'bp:test_QASMBench_large[adder_n118-all-to-all]' --device 'bp:test_QASMBench_large[adder_n118-all-to-all]' --b10-s 1.66451 --profile repro.prof
  ```

- failures, tket:2 / time / adapters.py:190 compile / 2q 100-1k / qubits 17-100 / QASMBench:

  ```bash
  python -m toqb.runner one --adapter tket:2 --case 'bp:test_QASMBench_medium[square_root_n18-all-to-all]' --device 'bp:test_QASMBench_medium[square_root_n18-all-to-all]' --b10-s 0.5 --profile repro.prof
  ```

- failures, tket:2 / time / adapters.py:190 compile / 2q <100 / qubits 17-100 / HamLib:

  ```bash
  python -m toqb.runner one --adapter tket:2 --case 'bp:test_hamiltonians[ham_bh_graph-1D-grid-nonpbc-qubitnodes_Lx-12_U-40_enc-unary_d-4-all-to-all]' --device 'bp:test_hamiltonians[ham_bh_graph-1D-grid-nonpbc-qubitnodes_Lx-12_U-40_enc-unary_d-4-all-to-all]' --b10-s 1.212 --profile repro.prof
  ```

- failures, tket:2 / time / adapters.py:190 compile / 2q <100 / qubits 17-100 / HamLib, FakeTorino:

  ```bash
  python -m toqb.runner one --adapter tket:2 --case 'bp:test_hamlib_hamiltonians_transpile[ham_graph-2D-grid-nonpbc-qubitnodes_Lx-5_Ly-15_h-3]' --device 'bp:test_hamlib_hamiltonians_transpile[ham_graph-2D-grid-nonpbc-qubitnodes_Lx-5_Ly-15_h-3]' --b10-s 1.26278 --profile repro.prof
  ```

- slow, tket:2 / 2q <100 / qubits 17-100 / QASMBench:

  ```bash
  python -m toqb.runner one --adapter tket:2 --case 'bp:test_QASMBench_medium[ising_n26-all-to-all]' --device 'bp:test_QASMBench_medium[ising_n26-all-to-all]' --b10-s 0.5 --profile repro.prof
  ```

- slow, tket:2 / 2q <100 / qubits <=16 / QASMBench:

  ```bash
  python -m toqb.runner one --adapter tket:2 --case 'bp:test_QASMBench_small[qpe_n9-all-to-all]' --device 'bp:test_QASMBench_small[qpe_n9-all-to-all]' --b10-s 0.5 --profile repro.prof
  ```

- slow, tket:2 / 2q <100 / qubits <=16 / HamLib:

  ```bash
  python -m toqb.runner one --adapter tket:2 --case 'bp:test_hamiltonians[ham_ham_parity-4-square]' --device 'bp:test_hamiltonians[ham_ham_parity-4-square]' --b10-s 0.5 --profile repro.prof
  ```

- slow, psf:default / 2q <100 / qubits <=16 / HamLib:

  ```bash
  python -m toqb.runner one --adapter psf:default --case 'bp:test_hamiltonians[ham_ham_parity10-all-to-all]' --device 'bp:test_hamiltonians[ham_ham_parity10-all-to-all]' --b10-s 0.565483 --profile repro.prof
  ```

- slow, psf:recommended / 2q <100 / qubits <=16 / HamLib:

  ```bash
  python -m toqb.runner one --adapter psf:recommended --case 'bp:test_hamiltonians[ham_ham_parity10-all-to-all]' --device 'bp:test_hamiltonians[ham_ham_parity10-all-to-all]' --b10-s 0.565483 --profile repro.prof
  ```

- worse, qiskit:1:target / 2q <100 / qubits <=16 / HamLib:

  ```bash
  python -m toqb.runner one --adapter qiskit:1:target --case 'bp:test_hamiltonians[ham_ham_parity-4-square]' --device 'bp:test_hamiltonians[ham_ham_parity-4-square]' --b10-s 0.5 --profile repro.prof
  ```

- worse, qiskit:1:target / 2q <100 / qubits <=16 / QASMBench:

  ```bash
  python -m toqb.runner one --adapter qiskit:1:target --case 'bp:test_QASMBench_small[dnn_n2-all-to-all]' --device 'bp:test_QASMBench_small[dnn_n2-all-to-all]' --b10-s 0.5 --profile repro.prof
  ```

- worse, tket:2 / 2q <100 / qubits <=16 / QASMBench:

  ```bash
  python -m toqb.runner one --adapter tket:2 --case 'bp:test_QASMBench_small[qec_en_n5-all-to-all]' --device 'bp:test_QASMBench_small[qec_en_n5-all-to-all]' --b10-s 0.5 --profile repro.prof
  ```

- worse, qiskit:1:target / 2q <100 / qubits 17-100 / HamLib:

  ```bash
  python -m toqb.runner one --adapter qiskit:1:target --case 'bp:test_hamiltonians[ham_bh_graph-1D-grid-nonpbc-qubitnodes_Lx-12_U-40_enc-unary_d-4-all-to-all]' --device 'bp:test_hamiltonians[ham_bh_graph-1D-grid-nonpbc-qubitnodes_Lx-12_U-40_enc-unary_d-4-all-to-all]' --b10-s 1.212 --profile repro.prof
  ```

- worse, tket:2 / 2q <100 / qubits 17-100 / QASMBench:

  ```bash
  python -m toqb.runner one --adapter tket:2 --case 'bp:test_QASMBench_medium[cat_state_n22-heavy-hex]' --device 'bp:test_QASMBench_medium[cat_state_n22-heavy-hex]' --b10-s 0.5 --profile repro.prof
  ```

