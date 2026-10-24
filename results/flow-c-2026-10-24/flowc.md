# Flow C: the device against two twins (report only, no rule)

Job dbec1jfsstms73fbq0lg on ibm_kingston, calibration 2026-10-24 15:26:59+02:00, 250 shots per point.

## Per arm (all points)

| arm | points | scale vs day twin / vs snapshot twin | offset day / snapshot | corr day / snapshot | +1 on device |
|---|---|---|---|---|---|
| psfai:template_zip | 270 | 1.00 / 4.33 | +0.019 / +0.017 | 0.983 / 0.964 | 0.85 |
| qiskit:2:target:template | 270 | -0.16 / -0.17 | +0.041 / +0.043 | -0.533 / -0.529 | 0.39 |

## Per cell

| cell | scale day / snapshot | corr day / snapshot | +1 device / day / snapshot | accuracy (day twin's prediction, inside) |
|---|---|---|---|---|
| L16_t17_a10_s301-psfai_template_zip | 1.00 / 4.45 | 0.984 / 0.971 | 0.84 / 0.84 / 0.82 | 0.850 (0.818, yes) |
| L16_t17_a10_s301-qiskit_2_target_template | -0.17 / -0.18 | -0.573 / -0.565 | 0.33 / 0.92 / 0.96 | 0.372 (0.889, no) |
| L16_t18_a10_s301-psfai_template_zip | 1.02 / 4.30 | 0.984 / 0.960 | 0.84 / 0.83 / 0.81 | 0.850 (0.829, yes) |
| L16_t18_a10_s301-qiskit_2_target_template | -0.15 / -0.16 | -0.478 / -0.472 | 0.47 / 0.86 / 0.88 | 0.472 (0.865, no) |
| L16_t19_a10_s301-psfai_template_zip | 0.95 / 4.18 | 0.974 / 0.946 | 0.87 / 0.80 / 0.80 | 0.872 (0.787, no) |
| L16_t19_a10_s301-qiskit_2_target_template | -0.16 / -0.17 | -0.518 / -0.517 | 0.37 / 0.87 / 0.90 | 0.383 (0.861, no) |
