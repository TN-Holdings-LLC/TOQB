#!/bin/bash
# Second resume folder: the PSF-Zero runs of resume1 that stopped at import (psf_zero_core was not built on the pod).
set -u
R1=<pod>/kept/s2r-stage0-2026-10-17-resume1; R2=<pod>/kept/s2r-stage0-2026-10-17-resume2
[ -e "$R2" ] && { echo "STOP: $R2 exists"; exit 1; }
[ "$(pgrep -af '^python -m toqb.s2r' | grep -c psfai)" -eq 0 ] || { echo "STOP: a PSF-Zero run is still running"; exit 1; }
mkdir -p "$R2/logs"
for s in $(seq 9001 9020); do mkdir -p "$R2/seed$s" && cp <pod>/toqb/prereg/s2r-stage0-2026-10-17/plan_s$s.json "$R2/seed$s/plan.json"; done
grep psfai "$R1/jobs.txt" > "$R2/jobs.txt"
echo "start $(TZ=Europe/Zurich date '+%F %T %Z'); $(wc -l < "$R2/jobs.txt") PSF-Zero runs; core $(python -c 'import psf_zero_core as c; print(c.CORE_VERSION)')" | tee "$R2/times.txt"
cd <pod>/toqb
export PSF_ZERO_REPO=<pod>/psf PSF_COMPILE_FILE=<pod>/psf/patches/psf_compile_c61_2026-10-15/psf_compile.py \
  PSF_AI_FILE=<pod>/psf/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py PYTHONWARNINGS=ignore OUT=$R2
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 QISKIT_NUM_PROCS=1 \
  NUMEXPR_NUM_THREADS=1 QISKIT_PARALLEL=FALSE
xargs -P 25 -L 1 sh -c 'f=$(echo $2 | tr : _); nice -n 19 python -m toqb.s2r "$0" "$OUT/seed$1/plan.json" \
    "$OUT/seed$1/$0-$f.json" "$2" > "$OUT/logs/seed$1-$0-$f.log" 2>&1; \
    echo "$0 seed $1 $2 done $(TZ=Europe/Zurich date +%H:%M:%S)"' < "$R2/jobs.txt"
echo "end $(TZ=Europe/Zurich date '+%F %T %Z')" | tee -a "$R2/times.txt"
