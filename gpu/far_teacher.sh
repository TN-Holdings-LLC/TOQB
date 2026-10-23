#!/bin/bash
# GPU pod, report only (declared in prereg/drafts-2026-10-23/far_teacher_note.md before the run): does the zipper learn
# more than item 31 when the answer is far from the start? L 16, teachers at angle 1.0 (TEACHERS, default 17 18 19),
# seed 301, design C (C0) for 2,000 loops with a checkpoint at 500 (toqb.s2rc_ckpt), arms item 31 (psfai:template) and
# the zipper (psfai:template_zip): 6 runs; and the untrained model (theta = 0) through each arm (toqb.theta0_eval). All
# 12 jobs together, then toqb.far_score.
# Run from /workspace (venv, TOQB, psf there):
#   OUT=/workspace/ft_2026-10-23 setsid nohup bash TOQB/gpu/far_teacher.sh > ft.txt 2>&1 < /dev/null &
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=${OUT:?set OUT}
TEACHERS=${TEACHERS:-"17 18 19"}
PAR=${PAR:-12}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, the venv and psf"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/logs" "$OUT/plans" "$OUT/runs" "$OUT/theta0"
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "PAR=$PAR TEACHERS=$TEACHERS TOQB_TRAJ_MEM_GB=$TOQB_TRAJ_MEM_GB"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python - "$OUT/plans" $TEACHERS <<'PY' || { echo "STOP: plans"; exit 1; }
import json, math, os, sys
out = sys.argv[1]
for t in (int(v) for v in sys.argv[2:]):
    task = dict(n=10, layers=16, enc=math.pi / 2, teacher_seed=t, teacher_angle=1.0, teacher_gap=0.2,
                n_train=64, n_test=500)
    p = dict(name=f"far teacher (report only): L16 t{t} angle 1.0 s301", device="snapshot:marrakesh", verify=True,
             task=task,
             train=dict(seed=301, init=0.0, pairs=8, sim_batch=4, sim_traj=32, h=0.1, lr=0.4, loops=2000,
                        curve_every=200, curve_points=100, curve_traj=64, progress_every=250, checkpoints=[500]),
             predict=dict(traj=1024, shots=250, reps=20000, level=0.99, seed=50301),
             standin=dict(t12=0.3, over=0.01, zz_hz=10000.0, seed=20261017))
    f = f"L16_t{t}_a10_s301.json"
    json.dump(p, open(os.path.join(out, f), "w"), indent=1)
    print(f, flush=True)
PY
JOBS="$OUT/jobs.txt"
for f in $(ls "$OUT"/plans/*.json); do for a in psfai:template_zip psfai:template; do echo "$f $a train"; echo "$f $a theta0"; done; done > "$JOBS"
export OUT
xargs -P "$PAR" -L 1 sh -c 'b=$(basename "$0" .json); a=$(echo "$1" | tr : _); \
  if [ "$2" = train ]; then python -m toqb.s2rc_ckpt "$0" "$OUT/runs/$b-$a.json" "$1" > "$OUT/logs/$b-$a.log" 2>&1; \
  else python -m toqb.theta0_eval "$0" "$1" "$OUT/theta0/$b-$a.json" > "$OUT/logs/theta0-$b-$a.log" 2>&1; fi; \
  echo "$b $1 $2 done $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/$( [ "$2" = train ] || echo theta0-)$b-$a.log" | cut -c1-200)"' \
  < "$JOBS" | tee "$OUT/progress.txt"
echo "trained $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m toqb.far_score "$OUT/runs" "$OUT/theta0" "$OUT/score.md" --json "$OUT/score.json"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$W/far_teacher.zip" "$OUT" && echo "== DONE: $W/far_teacher.zip"
