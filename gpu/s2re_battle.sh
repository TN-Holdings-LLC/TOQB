#!/bin/bash
# GPU pod: design C against design E on the twin and the stand-in (exploratory, not scored; simulation only, no IBM).
# The rehearsal's task, sizes and stand-in (P 500, N 1,000, T_pred 1,024, R 20,000, device snapshot:marrakesh):
#   E: training by formula (toqb.s2re_run; the twin's exact tangent at theta = 0, feat_traj trajectories), 2 depths x 2 arms;
#   C0: design C's training (toqb.s2rc, lr 0.4, 2,000 loops) started at theta = 0 instead of uniform(-1, 1), seeds SEEDS.
# Design C's own runs from uniform(-1, 1) are the rehearsal of 2026-10-20 (results/s2rc-rehearsal-2026-10-20/).
# Run from the folder that holds TOQB:
#   DAY=... OUT=... setsid nohup bash TOQB/gpu/s2re_battle.sh > battle.txt 2>&1 < /dev/null &
set -u
W=$(pwd)
DAY=${DAY:?set DAY}
OUT=${OUT:?set OUT}
SEEDS=${SEEDS:-201}
FEAT=${FEAT:-1024}
PAR=${PAR:-6}
TA=${TA:-0.3}
[ -d "$W/TOQB" ] && [ -d "$W/venv" ] && [ -d "$W/psf" ] || { echo "STOP: needs TOQB, venv and psf here"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$W/venv/bin/activate"
mkdir -p "$OUT/logs" "$OUT/plans" "$OUT/runs" "$DAY"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git -C "$W/TOQB" log --oneline -1)"; \
  echo "SEEDS=$SEEDS FEAT=$FEAT PAR=$PAR teacher_angle=$TA"; echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
export PYTHONPATH="$W/TOQB" PSF_ZERO_REPO="$W/psf" PYTHONWARNINGS=ignore TOQB_XP=cupy TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$W/psf/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$W/psf/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$W/TOQB" || exit 1
python - "$OUT/plans" "$FEAT" "$TA" $SEEDS <<'PY'
import json, sys
out, feat, ta, seeds = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), [int(s) for s in sys.argv[4:]]
def plan(L, s, kind):
    train = ({"seed": s, "feat_traj": feat} if kind == "E" else
             {"seed": s, "init": 0.0, "pairs": 8, "sim_batch": 4, "sim_traj": 32, "h": 0.1, "lr": 0.4, "loops": 2000,
              "curve_every": 200, "curve_points": 100, "curve_traj": 64})
    return {"name": f"S2RE battle {kind} L{L} s{s}", "device": "snapshot:marrakesh",
            "task": {"n": 10, "layers": L, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_angle": ta,
                     "teacher_gap": 0.2, "n_train": 64, "n_test": 500},
            "train": train, "predict": {"traj": 1024, "shots": 1000, "reps": 20000, "level": 0.99, "seed": 50000 + s},
            "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}
for L in (16, 8):
    json.dump(plan(L, seeds[0], "E"), open(f"{out}/E_L{L}.json", "w"), indent=1)
    for s in seeds:
        json.dump(plan(L, s, "C0"), open(f"{out}/C0_L{L}_s{s}.json", "w"), indent=1)
PY
JOBS="$OUT/jobs.txt"
for f in "$OUT"/plans/*.json; do for arm in qiskit:2:target:template psfai:template; do echo "$f $arm"; done; done > "$JOBS"
echo "$(wc -l < "$JOBS") runs" | tee -a "$OUT/times.txt"
export OUT
xargs -P "$PAR" -L 1 sh -c 'b=$(basename "$0" .json); a=$(echo "$1" | tr : _); \
  case "$b" in E_*) mod=toqb.s2re_run;; *) mod=toqb.s2rc;; esac; \
  python -m $mod "$0" "$OUT/runs/$b-$a.json" "$1" > "$OUT/logs/$b-$a.log" 2>&1; \
  echo "$b $1 done $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/$b-$a.log" | cut -c1-260)"' < "$JOBS" \
  | tee "$OUT/progress.txt"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$DAY/s2re_battle.zip" "$OUT" && echo "== DONE: $DAY/s2re_battle.zip"
