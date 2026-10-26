#!/bin/bash
# The device test's rehearsal (prereg/drafts-2026-10-26/lam_device_draft.md; report only): fold:rule and the zipper at
# n = 13, L = 16, models 0 and 1, 96 inputs, built for ibm_kingston's 2026-10-24 Target and predicted by its twin; then
# the job's outcome if the device were that twin, for 48 / 96 points and 250 / 1000 shots.
#   TARGET=/root/target.pkl OUT=/workspace/lam_rehearse bash TOQB/gpu/lam_rehearse.sh 2>&1 | tee lr.txt
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; PSF=${PSF_DIR:-$W/psf}; VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=${OUT:?set OUT}; TARGET=${TARGET:?set TARGET}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, venv, psf"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ "$(sha256sum "$TARGET" | cut -c1-64)" = "$(python3 -c "import json;print(json.load(open('$TQ/results/flow-c-2026-10-24/fetch.json'))['target_sha256'])")" ] \
  || { echo "STOP: $TARGET is not flow C's kingston Target"; exit 1; }
. "$VA"; mkdir -p "$OUT/fetch"
cp "$TARGET" "$OUT/fetch/target.pkl"; cp "$TQ/results/flow-c-2026-10-24/fetch.json" "$OUT/fetch/fetch.json"
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-16} OMP_NUM_THREADS=4
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
echo "toqb $(git log --oneline -1 | cut -c1-60); start $(TZ=Europe/Zurich date '+%F %T %Z')" | tee "$OUT/times.txt"
for m in 0 1; do for arm in fold:rule psfai:template_zip; do
  python -m toqb.lam_device build "$OUT/fetch" "$OUT/runs" --arm $arm --n 13 --L 16 --mseed $m --P 96 --shots 250 --traj 256 \
    2>&1 | grep -v Warn | tail -1 | tee -a "$OUT/build.txt"
done; done
for P in 48 96; do for N in 250 1000; do
  echo "== $P points, $N shots" | tee -a "$OUT/rehearse.txt"
  python -m toqb.lam_device rehearse "$OUT/runs" --points $P --shots $N --reps 2000 2>&1 | grep -v Warn | tee -a "$OUT/rehearse.txt"
done; done
echo "done $(TZ=Europe/Zurich date '+%F %T %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$W/lam_rehearse.zip" "$OUT/build.txt" "$OUT/rehearse.txt" "$OUT/times.txt" "$OUT/runs" && echo "== DONE: $W/lam_rehearse.zip"
