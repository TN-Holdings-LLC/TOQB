#!/bin/bash
# Device test D3 (prereg/drafts-2026-10-28/kising_device_d3_note.md), the pod step: the kicked Ising ring, n = 20, L = 24 (amendment 1),
# h = 0.6, fold:rule, 64 inputs, compiled for the fetched Target and predicted by its twin; the rehearsal; the job (at
# most 10 s). Run from the folder that holds TOQB, psf and venv, with the fetch folder from home:
#   FETCH=/workspace/fetch_d3 OUT=/workspace/d3 bash TOQB/gpu/kising_device_d3.sh 2>&1 | tee d3.txt
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
  echo "note $(sha256sum prereg/drafts-2026-10-28/kising_device_d3_note.md)"; echo "amend1 $(sha256sum prereg/drafts-2026-10-28/kising_device_d3_amend1.md)"; \
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python -m toqb.lam_device build "$FETCH" "$OUT/runs" --arm fold:rule --kind kising --h 0.6 --n 20 --L 24 --mseed 0 \
  --P 64 --shots 250 --traj 256 2>&1 | grep -v Warn | tail -1 | tee "$OUT/build.txt"
python -m toqb.lam_device rehearse "$OUT/runs" --shots 250 --reps 2000 2>&1 | grep -v Warn | tee "$OUT/rehearse.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds 10 | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/d3_job.zip" "$OUT" && echo "== DONE: $W/d3_job.zip"
