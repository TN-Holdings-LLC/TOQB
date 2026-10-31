# Coherent stage 1: dry build (2026-10-31; nothing submitted)

`gpu/coherent_stage1.sh` on the kingston fetch of 30 October 14:02 (calibration 13:37:20 CET), with the draft note in
place: 16 records accepted, one ring per size, the n = 40 D = 24 Z circuit byte-identical to 30 October (QPY SHA-256
42376e3f...), 128 circuits x 1000 shots, predicted 42.2 s (limit 60 s), manifest written. `build.txt`,
`assemble.txt`, `qpy_sha256.txt` are the logs. `plumbing_check_fake_counts.json`: `echo_tomo score` run on that
manifest with made-up counts (Z perfect except qubit 38 flipped half the time; X/Y random), to check the reading end to
end; the numbers mean nothing about the device.
