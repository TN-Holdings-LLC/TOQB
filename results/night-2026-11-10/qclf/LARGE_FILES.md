# Large circuit files stored gzipped (2026-11-10)

GitHub refuses files over 100 MB. The classifier jobs' circuit files (about 170 MB each) are committed as
`.qpy.gz` (gzip -9 -n); `gunzip -k FILE.qpy.gz` gives the original byte for byte. The scorers do not read them
(`gpu/qclf_score.py` reads the manifest, the run records and the counts). Original sha256:

- `results/night-2026-11-10/qclf/ibm_fez/job/circuits.qpy`: e265620f58fc7785eefa5757352990aee90dfcd632b01586248b99ef2a76ef3a
- `results/night-2026-11-10/qclf/ibm_fez/runs/q_a_rule.qpy`: 021b2ff015aeac3a22db4e27dc64e550abc83b1d70d98fe311f2545321fbf8e3
- `results/night-2026-11-10/qclf/ibm_kingston/job/circuits.qpy`: bc81a24f3a453f2dbce20a1fc450f92c32672f09c5a39b6f6dc63a34a0825978
- `results/night-2026-11-10/qclf/ibm_kingston/runs/q_a_rule.qpy`: 021b2ff015aeac3a22db4e27dc64e550abc83b1d70d98fe311f2545321fbf8e3
