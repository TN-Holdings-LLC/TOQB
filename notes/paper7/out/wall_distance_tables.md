# Distance to the wall: generated tables (ESTIMATE, not a measurement; notes/paper7/wall_distance.py)

gamma per CZ layer from 36 record rows (daily and practice, |M_exact| >= 0.1): smallest 0.0001, median 0.0013, largest 0.0182.

## Table 1: L_max = -ln(1 - eps) / gamma (CZ layers without correction)

| gamma | value | eps 0.1 | eps 0.01 | eps 0.001 |
|---|---|---|---|---|
| smallest | 0.0001 | 751.0 | 71.64 | 7.132 |
| median | 0.0013 | 80.1 | 7.64 | 0.761 |
| largest | 0.0182 | 5.8 | 0.55 | 0.055 |

## Table 2: chemical accuracy as a relative error (one example)

1 kcal/mol = 1.594 mHa; water's total correlation energy 0.3706 Ha (total correlation energy of H2O, CBS extrapolation: 'Complete basis set correlation energies. IV. The total correlation energy of the water molecule', J. Chem. Phys. 83, 5129 (1985)): eps = 4.30e-03. Larger molecules have larger correlation energies, so eps is smaller for them; FeMoco's correlation energy is not stated in the sources read.

## Table 3: FeMoco estimates and the gamma they would need without correction (eps as in table 2)

| estimate | depth taken as | layers | gamma needed | orders below the median gamma | below the smallest |
|---|---|---|---|---|---|
| femoco_reiher_thc_toffoli | serial (every non-Clifford gate one layer) | 5.30e+09 | 8.1e-13 | 9.2 | 8.2 |
| femoco_reiher_thc_toffoli | fully parallel over the logical qubits (count / qubits) | 2.47e+06 | 1.7e-09 | 5.9 | 4.9 |
| femoco_li_thc_toffoli | serial (every non-Clifford gate one layer) | 3.20e+10 | 1.3e-13 | 10.0 | 9.0 |
| femoco_li_thc_toffoli | fully parallel over the logical qubits (count / qubits) | 1.46e+07 | 3.0e-10 | 6.6 | 5.7 |
| femoco_reiher2017_T_1mHa_serial | serial (every non-Clifford gate one layer) | 1.00e+14 | 4.3e-17 | 13.5 | 12.5 |
| femoco_reiher2017_T_1mHa_serial | fully parallel over the logical qubits (count / qubits) | 9.01e+11 | 4.8e-15 | 11.4 | 10.5 |

Sources: water_correlation_ha: total correlation energy of H2O, CBS extrapolation: 'Complete basis set correlation energies. IV. The total correlation energy of the water molecule', J. Chem. Phys. 83, 5129 (1985); femoco_reiher_thc_toffoli: Lee et al., PRX Quantum 2, 030305 (2021), THC, Reiher et al. FeMoco Hamiltonian; 2,142 logical qubits; chemical accuracy taken there as 1.6 mHa; femoco_li_thc_toffoli: Lee et al., PRX Quantum 2, 030305 (2021), THC, Li et al. FeMoco Hamiltonian (CAS(113e,76o), J. Chem. Phys. 150, 024302 (2019)); 2,196 logical qubits; femoco_reiher2017_T_1mHa_serial: Reiher et al., PNAS 114, 7555 (2017), Table 1, structure 1, 1 mHa, serial: 1.0e14 T gates, 111 logical qubits
