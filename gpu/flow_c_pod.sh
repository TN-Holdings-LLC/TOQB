#!/bin/bash
# Flow C, the pod step (prereg/drafts-2026-10-24/flow_c_note.md): the far-teacher models of the zipper and Qiskit
# (teachers 17-19), compiled for the day's Target and predicted with the day's twin and the snapshot's twin
# (toqb.device_reuse, 90 points each), then assembled into one job of at most 60 s (toqb.s2rc_device assemble).
# Run from the folder that holds TOQB, psf and venv, with the fetch folder from home:
#   FETCH=/workspace/fetch OUT=/workspace/fc_2026-10-24 bash TOQB/gpu/flow_c_pod.sh 2>&1 | tee fc.txt
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH to the fetch folder from home}
OUT=${OUT:?set OUT}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] && [ -f "$FETCH/target.pkl" ] || { echo "STOP: needs TOQB, venv, psf, fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/logs"
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-8} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f.get('backend'), f.get('calibration_time'), f.get('target_sha256'))" "$FETCH/fetch.json")"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
for t in 17 18 19; do
  for rec in "results/far-teacher-2026-10-23/runs/L16_t${t}_a10_s301-psfai_template_zip.json" \
             "results/far-qiskit-2026-10-23/runs/L16_t${t}_a10_s301-qiskit_2_target_template.json"; do
    b=$(basename "$rec" .json)
    python -m toqb.device_reuse "$FETCH" "$rec" "$OUT/runs" --points 90 > "$OUT/logs/$b.log" 2>&1 &
  done
done
wait
cat "$OUT"/logs/*.log | tee "$OUT/reuse.txt"
[ "$(ls "$OUT"/runs/*.qpy 2>/dev/null | wc -l)" = 6 ] || { echo "STOP: not all 6 runs were built"; exit 1; }
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds 60 \
  | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: assemble wrote no job"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$W/flow_c_job.zip" "$OUT" && echo "== DONE: $W/flow_c_job.zip"
