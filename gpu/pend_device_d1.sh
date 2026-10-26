#!/bin/bash
# Device test D1 (prereg/drafts-2026-10-26/pend_device_note.md), the pod step: fold:rule at n = 13, L = 16, model 0,
# 64 inputs, compiled for the fetched Target and predicted by its twin; the zipper's twin slope for scale (not sent);
# then the job (at most 12 s). Run from the folder that holds TOQB, psf and venv, with the fetch folder from home:
#   FETCH=/workspace/fetch_d1 OUT=/workspace/d1 bash TOQB/gpu/pend_device_d1.sh 2>&1 | tee d1.txt
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; PSF=${PSF_DIR:-$W/psf}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB, venv, psf, fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
. "$VA"; mkdir -p "$OUT"
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-16} OMP_NUM_THREADS=4
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "psf-zero $(git -C "$PSF" log --oneline -1 | cut -c1-40)"; \
  echo "note $(sha256sum prereg/drafts-2026-10-26/pend_device_note.md)"; \
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python -m toqb.lam_device build "$FETCH" "$OUT/runs" --arm fold:rule --n 13 --L 16 --mseed 0 --P 64 --shots 250 --traj 256 \
  2>&1 | grep -v Warn | tail -1 | tee "$OUT/build.txt"
python -m toqb.lam_device build "$FETCH" "$OUT/scale" --arm psfai:template_zip --n 13 --L 16 --mseed 0 --P 64 --shots 250 \
  --traj 256 2>&1 | grep -v Warn | tail -1 | tee -a "$OUT/build.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds 12 | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/d1_job.zip" "$OUT" && echo "== DONE: $W/d1_job.zip"
