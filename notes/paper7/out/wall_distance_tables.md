# Distance to the wall: generated tables (ESTIMATE, not a measurement; notes/paper7/wall_distance.py)

Row rule (written before computing): |M_exact| >= 0.3 and >= 10 CZ layers. Kept 20 of 38 rows.

## gamma per CZ layer by family (kept rows)

| family | rows | smallest | median | largest |
|---|---|---|---|---|
| chain | 0 | - | - | - |
| P5 | 18 | 0.0005 | 0.0010 | 0.0020 |
| P6 form | 2 | 0.0038 | 0.0045 | 0.0052 |
| all kept | 20 | 0.0005 | 0.0011 | 0.0052 |
| unfiltered (abs(M_exact) >= 0.1, any depth; comparison) | 36 | 0.0001 | 0.0013 | 0.0182 |

## Table 1: L_max = -ln(1 - eps) / gamma (CZ layers without correction)

| gamma | value | eps 0.1 | eps 0.01 | eps 0.001 |
|---|---|---|---|---|
| all kept, smallest | 0.0005 | 203.1 | 19.37 | 1.928 |
| all kept, median | 0.0011 | 92.4 | 8.81 | 0.877 |
| all kept, largest | 0.0052 | 20.1 | 1.92 | 0.191 |
| P5, median | 0.0010 | 101.6 | 9.69 | 0.965 |
| P6 form, median | 0.0045 | 23.4 | 2.23 | 0.222 |
| unfiltered, median (comparison) | 0.0013 | 80.1 | 7.64 | 0.761 |

## Table 2: chemical accuracy as a relative error (one example)

1 kcal/mol = 1.594 mHa; water's total correlation energy 0.3706 Ha (total correlation energy of H2O, CBS extrapolation: 'Complete basis set correlation energies. IV. The total correlation energy of the water molecule', J. Chem. Phys. 83, 5129 (1985)): eps = 4.30e-03. Larger molecules have larger correlation energies, so eps is smaller for them; FeMoco's correlation energy is not stated in the sources read.

## Table 3: FeMoco estimates and the gamma they would need without correction (eps as in table 2)

| estimate | depth taken as | layers | gamma needed | orders below the kept median | below the kept smallest | below the unfiltered median |
|---|---|---|---|---|---|---|
| femoco_reiher_thc_toffoli | serial (every non-Clifford gate one layer) | 5.30e+09 | 8.1e-13 | 9.1 | 8.8 | 9.2 |
| femoco_reiher_thc_toffoli | fully parallel over the logical qubits (count / qubits) | 2.47e+06 | 1.7e-09 | 5.8 | 5.5 | 5.9 |
| femoco_li_thc_toffoli | serial (every non-Clifford gate one layer) | 3.20e+10 | 1.3e-13 | 9.9 | 9.6 | 10.0 |
| femoco_li_thc_toffoli | fully parallel over the logical qubits (count / qubits) | 1.46e+07 | 3.0e-10 | 6.6 | 6.2 | 6.6 |
| femoco_reiher2017_T_1mHa_serial | serial (every non-Clifford gate one layer) | 1.00e+14 | 4.3e-17 | 13.4 | 13.1 | 13.5 |
| femoco_reiher2017_T_1mHa_serial | fully parallel over the logical qubits (count / qubits) | 9.01e+11 | 4.8e-15 | 11.4 | 11.0 | 11.4 |

## Kept rows

| source | device | problem | family | M_exact | CZ layers | gamma |
|---|---|---|---|---|---|---|
| daily 2026-11-05 | ibm_fez | D02 | P6 form | 0.796 | 40 | 0.00525 |
| daily 2026-11-05 | ibm_marrakesh | D02 | P6 form | 0.796 | 40 | 0.00377 |
| practice 2026-11-04 | ibm_marrakesh | p5_tx0.4_t2 | P5 | 0.931 | 41 | 0.00126 |
| practice 2026-11-04 | ibm_marrakesh | p5_tx0.4_t4 | P5 | 0.946 | 50 | 0.00139 |
| practice 2026-11-04 | ibm_marrakesh | p5_tx0.4_t6 | P5 | 0.906 | 56 | 0.00124 |
| practice 2026-11-04 | ibm_marrakesh | p5_tx0.4_t8 | P5 | 0.894 | 62 | 0.00131 |
| practice 2026-11-04 | ibm_marrakesh | p5_tx0.8_t2 | P5 | 0.646 | 41 | 0.00105 |
| practice 2026-11-04 | ibm_marrakesh | p5_tx0.8_t4 | P5 | 0.512 | 50 | 0.00132 |
| practice 2026-11-04 | ibm_marrakesh | p5_tx0.8_t6 | P5 | 0.432 | 56 | 0.00090 |
| practice 2026-11-04 | ibm_marrakesh | p5_tx0.8_t8 | P5 | 0.449 | 62 | 0.00204 |
| practice 2026-11-04 | ibm_marrakesh | p5_tx1.0_t2 | P5 | 0.425 | 41 | 0.00082 |
| practice 2026-11-04 | ibm_fez | p5_tx0.4_t2 | P5 | 0.932 | 45 | 0.00098 |
| practice 2026-11-04 | ibm_fez | p5_tx0.4_t4 | P5 | 0.945 | 51 | 0.00130 |
| practice 2026-11-04 | ibm_fez | p5_tx0.4_t6 | P5 | 0.907 | 57 | 0.00123 |
| practice 2026-11-04 | ibm_fez | p5_tx0.4_t8 | P5 | 0.893 | 63 | 0.00102 |
| practice 2026-11-04 | ibm_fez | p5_tx0.8_t2 | P5 | 0.647 | 45 | 0.00080 |
| practice 2026-11-04 | ibm_fez | p5_tx0.8_t4 | P5 | 0.506 | 51 | 0.00089 |
| practice 2026-11-04 | ibm_fez | p5_tx0.8_t6 | P5 | 0.428 | 57 | 0.00058 |
| practice 2026-11-04 | ibm_fez | p5_tx0.8_t8 | P5 | 0.449 | 63 | 0.00095 |
| practice 2026-11-04 | ibm_fez | p5_tx1.0_t2 | P5 | 0.426 | 45 | 0.00052 |

Sources: water_correlation_ha: total correlation energy of H2O, CBS extrapolation: 'Complete basis set correlation energies. IV. The total correlation energy of the water molecule', J. Chem. Phys. 83, 5129 (1985); femoco_reiher_thc_toffoli: Lee et al., PRX Quantum 2, 030305 (2021), THC, Reiher et al. FeMoco Hamiltonian; 2,142 logical qubits; chemical accuracy taken there as 1.6 mHa; femoco_li_thc_toffoli: Lee et al., PRX Quantum 2, 030305 (2021), THC, Li et al. FeMoco Hamiltonian (CAS(113e,76o), J. Chem. Phys. 150, 024302 (2019)); 2,196 logical qubits; femoco_reiher2017_T_1mHa_serial: Reiher et al., PNAS 114, 7555 (2017), Table 1, structure 1, 1 mHa, serial: 1.0e14 T gates, 111 logical qubits
