#!/bin/bash
# GPU pod, report only (declared in prereg/drafts-2026-10-22/zip_depth_note.md before the run): the depth sweep of the
# zipper (psfai:template_zip) against item 31 (psfai:template). L 8, 12, 16, 20 x teachers 11, 12, 13 x the two arms =
# 24 runs of design C (C0, seed 301, 2,000 loops, P 500), on the published calibration (snapshot:marrakesh) with the
# stand-in verifying; then toqb.undamp_run --final-only on each, and toqb.zip_depth_score.
# Run from /workspace (venv, TOQB, psf there):
#   OUT=/workspace/zd_2026-10-22 setsid nohup bash TOQB/gpu/zip_depth.sh > zd.txt 2>&1 < /dev/null &
# TOQB_TRAJ_MEM_GB defaults to 4 for both steps: the undamp step redraws the stand-in's shots only with the same value.
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=${OUT:?set OUT}
PAR=${PAR:-4}
UPAR=${UPAR:-2}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, the venv and psf"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/logs" "$OUT/plans" "$OUT/runs" "$OUT/undamp"
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "PAR=$PAR UPAR=$UPAR TOQB_TRAJ_MEM_GB=$TOQB_TRAJ_MEM_GB"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python - "$OUT/plans" <<'PY' || { echo "STOP: plans"; exit 1; }
import json, math, os, sys
from toqb import s2r2 as S2
out = sys.argv[1]
for L in (20, 16, 12, 8):          # the longest first, so the parallel slots finish together
    for t in (11, 12, 13):
        task = dict(n=10, layers=L, enc=math.pi / 2, teacher_seed=t, teacher_angle=0.3, teacher_gap=0.2,
                    n_train=64, n_test=500)
        S2.teacher_data2(task)     # stops here if a teacher does not give both classes
        p = dict(name=f"zip depth (report only): L{L} t{t} s301", device="snapshot:marrakesh", verify=True, task=task,
                 train=dict(seed=301, init=0.0, pairs=8, sim_batch=4, sim_traj=32, h=0.1, lr=0.4, loops=2000,
                            curve_every=200, curve_points=100, curve_traj=64),
                 predict=dict(traj=1024, shots=250, reps=20000, level=0.99, seed=50301),
                 standin=dict(t12=0.3, over=0.01, zz_hz=10000.0, seed=20261017))
        f = f"L{L:02d}_t{t}_s301.json"
        json.dump(p, open(os.path.join(out, f), "w"), indent=1)
        print(f, flush=True)
PY
JOBS="$OUT/jobs.txt"
for f in $(ls "$OUT"/plans/*.json | sort -r); do echo "$f psfai:template_zip"; echo "$f psfai:template"; done > "$JOBS"
export OUT
xargs -P "$PAR" -L 1 sh -c 'b=$(basename "$0" .json); a=$(echo "$1" | tr : _); \
  python -m toqb.s2rc "$0" "$OUT/runs/$b-$a.json" "$1" > "$OUT/logs/$b-$a.log" 2>&1; \
  echo "$b $1 done $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/$b-$a.log" | cut -c1-200)"' < "$JOBS" \
  | tee "$OUT/progress.txt"
echo "trained $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
ls "$OUT"/runs/*.json | xargs -P "$UPAR" -I{} sh -c 'b=$(basename "{}" .json); \
  python -m toqb.undamp_run "{}" "$OUT/undamp/$b.json" --final-only > "$OUT/logs/undamp-$b.log" 2>&1; \
  echo "$b undamp $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/undamp-$b.log" | cut -c1-200)"' \
  | tee -a "$OUT/progress.txt"
python -m toqb.zip_depth_score "$OUT/runs" "$OUT/undamp" "$OUT/score.md" --json "$OUT/score.json"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$W/zip_depth.zip" "$OUT" && echo "== DONE: $W/zip_depth.zip"
