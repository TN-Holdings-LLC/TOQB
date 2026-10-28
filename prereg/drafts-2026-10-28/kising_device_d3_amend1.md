# Device test D3, amendment 1 (owner, 2026-10-28: "L = 24"): the depth is L = 24, not 50. Fixed by SHA-256 and CET time before the fetch; nothing of D3 had run

**Why.** Flow M on the 2026-10-24 twin gave lam_K 0.084 +- 0.013 at L = 50 (correlation with the exact values
0.22-0.56) and 0.291 +- 0.007 at L = 24 (correlation 0.93-0.97). With 64 inputs x 250 shots the device slope's SE was
estimated at about 0.05 at L = 50 (no SIGNAL expected to be decidable) and about 0.02 at L = 24 (estimates, not
measured; the rehearsal on the pod gives the expected SE before submission).

- **Changed:** L = 50 to L = 24 (480 two-qubit gates on the 2026-10-24 Target). The inputs are the first 64 of flow
  M's seed-0 draw at L = 24 (seed 8,000,000 + 1000 n + L; its first 24 are flow M's own).
- **Unchanged:** everything else of kising_device_d3_note.md (SHA-256 558aa6cd…): ibm_kingston, the day's Target and
  twin, fold:rule, n = 20, h = 0.6, 64 x 250 shots, at most 10 s, the rule (AGREE / BELOW / ABOVE within 2 SE; SIGNAL
  if lam_device > 2 SE), the prediction (AGREE, and SIGNAL if the twin's lam is above 3 rehearsal SE).
- **For scale:** flow M's twin lam_K at L = 24, seed 0: 0.299 (2026-10-24 calibration).
