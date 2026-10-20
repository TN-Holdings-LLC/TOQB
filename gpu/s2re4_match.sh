#!/bin/bash
# GPU pod: test match, design E4 against design C (C0), from the same start and at the same cost, with the theta = 0
# control (exploratory, not scored; simulation only, no IBM). Owner principle of 2026-10-21: no lanes, formula only,
# same start, same cost, theta = 0 control, raw results.
#   Z:  theta = 0, no training (toqb.s2re4_run, sweeps 0): prediction and stand-in only.
#   E4: toqb.s2re4_run from theta = 0, the twin's exact per-parameter sinusoids in two halves of TRAJ trajectories,
#       unbiased Brier coefficients, the exact quartic minimum; the whole sweeps that fit in C's training budget.
#   C0: design C's training (toqb.s2rc, lr 0.4, 2,000 loops, 8 pairs, batch 4, 32 trajectories) from theta = 0.
# Budget (training only; C's learning-curve evaluations are monitoring and excluded):
#   2,000 loops x 16 candidates x 4 points x 32 trajectories = 4,096,000 trajectory-circuits.
# Tasks: teacher_seed in TASKS (default 4 5 6), teacher_angle TA (default 1.0, fixed before training), L 8 and 16;
# the rehearsal's sizes and stand-in (P 500 test points, T_pred 1,024, N 1,000 shots, R 20,000, snapshot:marrakesh).
# Order: all Z first (minutes), then L 8, then L 16. ARMS default psfai:template (the opponent is ourselves).
#   DAY=... OUT=... setsid nohup bash TOQB/gpu/s2re4_match.sh > match.txt 2>&1 < /dev/null &
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
ARMS=${ARMS:-psfai:template}
DAY=${DAY:?set DAY}
OUT=${OUT:?set OUT}
TASKS=${TASKS:-4 5 6}
TA=${TA:-1.0}
CSEED=${CSEED:-201}
TRAJ=${TRAJ:-32}
PAR=${PAR:-6}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, the venv and psf (see the header)"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/logs" "$OUT/plans" "$OUT/runs" "$DAY"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git -C "$TQ" log --oneline -1)"; \
  echo "TASKS=$TASKS TA=$TA CSEED=$CSEED TRAJ=$TRAJ PAR=$PAR ARMS=$ARMS"; echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=cupy TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$TQ" || exit 1
python - "$OUT/plans" "$TA" "$CSEED" "$TRAJ" $TASKS <<'PY'
import json, sys
out, ta, cseed, traj, tasks = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), [int(s) for s in sys.argv[5:]]
BUDGET = 2000 * 16 * 4 * 32
def plan(L, ts, kind):
    if kind == "C0":
        train = {"seed": cseed, "init": 0.0, "pairs": 8, "sim_batch": 4, "sim_traj": 32, "h": 0.1, "lr": 0.4,
                 "loops": 2000, "curve_every": 200, "curve_points": 100, "curve_traj": 64}
    elif kind == "E4":
        train = {"seed": ts, "traj": traj, "sweeps": "budget", "budget_traj_circuits": BUDGET}
    else:
        train = {"seed": ts, "sweeps": 0}
    return {"name": f"S2RE4 match {kind} L{L} teacher{ts}", "device": "snapshot:marrakesh",
            "task": {"n": 10, "layers": L, "enc": 1.5707963267948966, "teacher_seed": ts, "teacher_angle": ta,
                     "teacher_gap": 0.2, "n_train": 64, "n_test": 500},
            "train": train, "predict": {"traj": 1024, "shots": 1000, "reps": 20000, "level": 0.99, "seed": 50000 + ts},
            "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}
for L, pre in ((8, "1"), (16, "2")):
    for ts in tasks:
        json.dump(plan(L, ts, "Z"), open(f"{out}/0Z_L{L}_t{ts}.json", "w"), indent=1)
        json.dump(plan(L, ts, "E4"), open(f"{out}/{pre}E4_L{L}_t{ts}.json", "w"), indent=1)
        json.dump(plan(L, ts, "C0"), open(f"{out}/{pre}C0_L{L}_t{ts}.json", "w"), indent=1)
PY
JOBS="$OUT/jobs.txt"
for f in "$OUT"/plans/*.json; do for arm in $ARMS; do echo "$f $arm"; done; done > "$JOBS"
echo "$(wc -l < "$JOBS") runs" | tee -a "$OUT/times.txt"
export OUT
xargs -P "$PAR" -L 1 sh -c 'b=$(basename "$0" .json); a=$(echo "$1" | tr : _); \
  case "$b" in *C0_*) mod=toqb.s2rc;; *) mod=toqb.s2re4_run;; esac; \
  python -m $mod "$0" "$OUT/runs/$b-$a.json" "$1" > "$OUT/logs/$b-$a.log" 2>&1; \
  echo "$b $1 done $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/$b-$a.log" | cut -c1-300)"' < "$JOBS" \
  | tee "$OUT/progress.txt"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$DAY/s2re4_match.zip" "$OUT" && echo "== DONE: $DAY/s2re4_match.zip"
