#!/bin/bash
# Flow L, amendment 1 (prereg/drafts-2026-10-28/clifford_lam_amend1.md): the bridge at L = 24 (real-angle lam, models
# 0-3, and Clifford lam_C, seeds 0-3, n = 20, fold:rule, kingston 2026-10-24 twin). Waits for the main run's "all done".
# On the pod, from /workspace:  nohup bash l24.sh > l24.txt 2>&1 &
set -u
W=/workspace; OUT=$W/clifford_l24_2026-10-28; T=$W/target.pkl; PSF=$W/psf
until grep -q "all done" $W/clifford_l_2026-10-28/times.txt; do sleep 60; done
[ -e $OUT ] && { echo "STOP: $OUT exists"; exit 1; }
[ "$(sha256sum $T | cut -c1-64)" = 3b93913856d2f0b9bf97ac03f89c43457157735413b02d8722c82d31065b218d ] || { echo "STOP: target"; exit 1; }
. $W/venv/bin/activate; mkdir -p $OUT
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP TOQB_NOISELESS
export PYTHONPATH=$W/TOQB PSF_ZERO_REPO=$PSF PYTHONWARNINGS=ignore TOQB_XP=cupy TOQB_TRAJ_DTYPE=complex64 TOQB_TRAJ_MEM_GB=16 OMP_NUM_THREADS=4
cd $W/TOQB || exit 1
. gpu/rust_psf.sh
st() { echo "$1 $(TZ=Europe/Zurich date '+%F %T %Z')" | tee -a $OUT/times.txt; }
echo "note clifford_lam_amend1.md dadc1d872a47d892b81cfeb68b46f49de1d789a4d3413ded89fc2e5c7c6d5a73; toqb $(git log --oneline -1 | cut -c1-7)" | tee -a $OUT/times.txt
st start
python -m toqb.fold_lam $OUT/real_L24.jsonl --n 20 --L 24 --P 24 --T 256 --models sim --arms fold:rule --max-active 24 \
  --models-seed 0 1 2 3 --device file:$T > $OUT/real_L24.log 2>&1
st "clifford start"
python -m toqb.clifford_lam $OUT/clifford_L24.jsonl --n 20 --L 24 --P 24 --T 256 --seeds 0 1 2 3 --arms fold:rule \
  --device file:$T > $OUT/clifford_L24.log 2>&1
st "all done"
python -m zipfile -c $W/clifford_l24.zip $OUT && echo "== DONE: $W/clifford_l24.zip"
