# Design C device job: score (2026-10-22T10:33:26+00:00 (2026-10-22 12:33:26 CEST))

Job dbcubfoc77vs73872leg on ibm_marrakesh (DONE); calibration fetched 2026-10-13 11:37:12+02:00, at result 2026-10-22 12:01:03+02:00; usage {'qpu_charge_time_seconds': 100, 'value': 1.661696, 'unit': 'resource_units', 'status': 'complete', 'details': [{'value': 1.661696, 'unit': 'resource_units', 'metric': {'id': 'caffe3ca-729c-5750-8777-df63bbf8bfd9', 'value': 100}}]}; 250 shots per point.

| cell | P | correct (strict) | H1 p (Holm) | H1 | CE (pred) | in 99 % (twin+shots / shots) | acc (pred) | mean dev (shot floor) |
|---|---|---|---|---|---|---|---|---|
| L16_s301-psfai_template | 500 | 277 | 1.77e-02 | not confirmed | 0.5716 (0.6291) | no / no | 0.563 (0.624) | 0.0949 (0.0249) |
| L16_s301-qiskit_2_target_template | 500 | 305 | 1.49e-06 | confirmed | 0.5867 (0.5852) | yes / yes | 0.625 (0.648) | 0.0271 (0.0240) |
| L8_s301-psfai_template | 150 | 109 | 5.23e-08 | confirmed | 0.5087 (0.5618) | no / no | 0.733 (0.771) | 0.0790 (0.0244) |
| L8_s301-qiskit_2_target_template | 150 | 79 | 2.84e-01 | not confirmed | 0.6613 (0.5205) | no / no | 0.527 (0.739) | 0.0985 (0.0232) |

| depth | seeds | mean d (Qiskit dev - PSF dev) | Wilcoxon p (Holm) | paired t p | H2 |
|---|---|---|---|---|---|
| L 8 | [301] | +0.0194 | 5.67e-01 | 3.90e-02 | not confirmed |
| L 16 | [301] | -0.0678 | 1.00e+00 | 1.00e+00 | not confirmed |
