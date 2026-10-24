# Flow C: the device against two twins (report only, no rule)

Job local-20261019 on fake_marrakesh, calibration 2025-02-26 14:52:45-05:00, 250 shots per point.

## Per arm (all points)

| arm | points | scale vs day twin / vs snapshot twin | offset day / snapshot | corr day / snapshot | +1 on device |
|---|---|---|---|---|---|
| psfai:template_zip | 4 | 0.95 / 1.31 | +0.042 / +0.073 | 0.966 / 0.954 | 0.75 |
| qiskit:2:target:template | 4 | 1.02 / 0.99 | -0.077 / -0.071 | 0.986 / 0.990 | 0.75 |

## Per cell

| cell | scale day / snapshot | corr day / snapshot | +1 device / day / snapshot | accuracy (day twin's prediction, inside) |
|---|---|---|---|---|
| L16_t17_a10_s301-psfai_template_zip | 0.95 / 1.31 | 0.966 / 0.954 | 0.75 / 0.75 / 0.50 | 0.875 (0.741, yes) |
| L16_t17_a10_s301-qiskit_2_target_template | 1.02 / 0.99 | 0.986 / 0.990 | 0.75 / 1.00 / 1.00 | 0.750 (0.797, yes) |
