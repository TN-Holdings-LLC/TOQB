#!/bin/bash
# GPU pod, report only (declared in prereg/drafts-2026-10-23/data_grad_note.md before the run): does more training data
# break the 64-point wall, does the zipper's gain survive it, and does the twin's gradient point where the noiseless
# model's does. L 16, teachers 14, 15, 16, seed 301, design C (C0, 2,000 loops), arms item 31 (psfai:template) and the
# zipper (psfai:template_zip), 256 training points and 64 (the first 32 per class of the 256, on the same 500 test
# points: task test_after 128): 12 runs (toqb.s2rc), then toqb.grad_agree on each, then toqb.data_grad_score.
# Run from /workspace (venv, TOQB, psf there):
#   OUT=/workspace/dg_2026-10-23 setsid nohup bash TOQB/gpu/data_grad.sh > dg.txt 2>&1 < /dev/null &
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=${OUT:?set OUT}
PAR=${PAR:-6}
GPAR=${GPAR:-6}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, the venv and psf"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/logs" "$OUT/plans" "$OUT/runs" "$OUT/grad"
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "PAR=$PAR GPAR=$GPAR TOQB_TRAJ_MEM_GB=$TOQB_TRAJ_MEM_GB"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python - "$OUT/plans" <<'PY' || { echo "STOP: plans"; exit 1; }
import json, math, os, sys
from toqb import s2r2 as S2
out = sys.argv[1]
for t in (14, 15, 16):
    for ntr in (256, 64):
        task = dict(n=10, layers=16, enc=math.pi / 2, teacher_seed=t, teacher_angle=0.3, teacher_gap=0.2,
                    n_train=ntr, n_test=500)
        if ntr == 64:
            task["test_after"] = 128
        S2.teacher_data2(task)
        p = dict(name=f"data grad (report only): L16 t{t} n{ntr} s301", device="snapshot:marrakesh", verify=True,
                 task=task,
                 train=dict(seed=301, init=0.0, pairs=8, sim_batch=4, sim_traj=32, h=0.1, lr=0.4, loops=2000,
                            curve_every=200, curve_points=100, curve_traj=64),
                 predict=dict(traj=1024, shots=250, reps=20000, level=0.99, seed=50301),
                 standin=dict(t12=0.3, over=0.01, zz_hz=10000.0, seed=20261017))
        f = f"L16_t{t}_n{ntr:03d}_s301.json"
        json.dump(p, open(os.path.join(out, f), "w"), indent=1)
        print(f, flush=True)
PY
JOBS="$OUT/jobs.txt"
for f in $(ls "$OUT"/plans/*.json); do echo "$f psfai:template_zip"; echo "$f psfai:template"; done > "$JOBS"
export OUT
xargs -P "$PAR" -L 1 sh -c 'b=$(basename "$0" .json); a=$(echo "$1" | tr : _); \
  python -m toqb.s2rc "$0" "$OUT/runs/$b-$a.json" "$1" > "$OUT/logs/$b-$a.log" 2>&1; \
  echo "$b $1 done $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/$b-$a.log" | cut -c1-200)"' < "$JOBS" \
  | tee "$OUT/progress.txt"
echo "trained $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
ls "$OUT"/runs/*.json | xargs -P "$GPAR" -I{} sh -c 'b=$(basename "{}" .json); \
  python -m toqb.grad_agree "{}" "$OUT/grad/$b.json" > "$OUT/logs/grad-$b.log" 2>&1; \
  echo "$b grad $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 2 "$OUT/logs/grad-$b.log" | tr "\n" " " | cut -c1-240)"' \
  | tee -a "$OUT/progress.txt"
python -m toqb.data_grad_score "$OUT/runs" "$OUT/grad" "$OUT/score.md" --json "$OUT/score.json"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$W/data_grad.zip" "$OUT" && echo "== DONE: $W/data_grad.zip"
