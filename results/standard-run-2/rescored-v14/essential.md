# Display and essential results (exploratory re-scoring after the run, TOQB v14; not a scored result)

Display: as scored. Essential: an output with an operation on a failed element (FakeTorino) is unusable, and time is the first compile in the process. **These records have no first-compile time: essential time = display time.**

| compiler | within 1x (display / essential) | within 3x | within 10x | two-qubit / reference (display / essential) | FakeTorino outputs usable on the device | failed (display / essential) |
|---|---|---|---|---|---|---|
| qiskit:2:target | 1.000 / 0.960 | 1.000 / 0.960 | 1.000 / 0.960 | 1.000 / 1.000 | 13 of 18 (5 unusable) | 0 / 5 |
| qiskit:1:target | 1.000 / 0.960 | 1.000 / 0.960 | 1.000 / 0.960 | 1.265 / 1.266 | 13 of 18 (5 unusable) | 0 / 5 |
| qiskit:3:target | 0.556 / 0.548 | 0.960 / 0.929 | 0.984 / 0.952 | 0.973 / 0.974 | 14 of 18 (4 unusable) | 2 / 6 |
| tket:2 | 0.071 / 0.071 | 0.143 / 0.143 | 0.254 / 0.246 | 1.145 / 1.147 | 4 of 18 (2 unusable) | 52 / 54 |
| psf:default | 0.714 / 0.675 | 0.952 / 0.873 | 1.000 / 0.921 | 1.012 / 1.010 | 8 of 18 (10 unusable) | 0 / 10 |
| psf:recommended | 0.667 / 0.667 | 0.905 / 0.905 | 0.984 / 0.984 | 1.012 / 1.010 | 17 of 18 (0 unusable) | 1 / 1 |
