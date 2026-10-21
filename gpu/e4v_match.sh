#!/bin/bash
# GPU pod: the E4v match (W13, fixed 2026-10-21; owner: both additions) and W12's twin part (T2). Simulation only.
#   main (scored, headline): fresh teachers 10, 11, 12 x angles 0.3, 1.0, 2.0 x L 8: Z (theta = 0), C0
#     (toqb.s2rc_ckpt, seed 201, init 0, 2,000 loops, checkpoints 510 / 1,020 / 1,530) and E4v (toqb.s2re4_run,
#     "variant": "e4v", traj 32, sweeps budget = 3, checkpoints, twin seed = teacher seed);
#   F3 (reported, in main): (1.0, L 8, teacher 10): C0 seeds 202, 203 and E4v twin seeds 1010, 2010;
#   plain (reported, never a headline, its own directory): plain E4 on the same 9 tasks, for attribution;
#   W12 T2: the twin's training Brier (1,024 trajectories) at every recorded point of the runs in W12_DIRS (the fruit
#     match and the test match, if present on this pod), after the matches.
# Everything else as the fruit match's plans. Order: Z, then C0 and E4v, then F3, then plain, then W12.
#   DAY=... OUT=... setsid nohup bash TOQB/gpu/e4v_match.sh > e4v.txt 2>&1 < /dev/null &
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
ARMS=${ARMS:-psfai:template}
DAY=${DAY:?set DAY}
OUT=${OUT:?set OUT}
PAR=${PAR:-6}
W12_DIRS=${W12_DIRS:-"$W/fruit_match_1/runs $W/s2re4_match_1/runs"}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, the venv and psf (see the header)"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/main/logs" "$OUT/main/runs" "$OUT/plain/logs" "$OUT/plain/runs" "$OUT/plans" "$DAY"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git -C "$TQ" log --oneline -1)"; \
  echo "PAR=$PAR ARMS=$ARMS"; echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=cupy TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$TQ" || exit 1
python - "$OUT/plans" <<'PY'
import json, sys
out = sys.argv[1]
def plan(a, ts, kind, seed):
    if kind == "C0":
        train = {"seed": seed, "init": 0.0, "pairs": 8, "sim_batch": 4, "sim_traj": 32, "h": 0.1, "lr": 0.4,
                 "loops": 2000, "curve_every": 200, "curve_points": 100, "curve_traj": 64,
                 "checkpoints": [510, 1020, 1530]}
    elif kind == "E4v":
        train = {"seed": seed, "traj": 32, "sweeps": "budget", "budget_traj_circuits": 4096000, "checkpoints": True,
                 "variant": "e4v"}
    elif kind == "E4":
        train = {"seed": seed, "traj": 32, "sweeps": "budget", "budget_traj_circuits": 4096000, "checkpoints": True}
    else:
        train = {"seed": seed, "sweeps": 0}
    return {"name": f"E4v match {kind} L8 angle{a} teacher{ts} seed{seed}", "device": "snapshot:marrakesh",
            "task": {"n": 10, "layers": 8, "enc": 1.5707963267948966, "teacher_seed": ts, "teacher_angle": a,
                     "teacher_gap": 0.2, "n_train": 64, "n_test": 500},
            "train": train, "predict": {"traj": 1024, "shots": 1000, "reps": 20000, "level": 0.99, "seed": 50000 + ts},
            "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}
for a in (0.3, 1.0, 2.0):
    for ts in (10, 11, 12):
        tag = f"L8_a{a}_t{ts}"
        json.dump(plan(a, ts, "Z", ts), open(f"{out}/0Z_{tag}.json", "w"), indent=1)
        json.dump(plan(a, ts, "C0", 201), open(f"{out}/1C0_{tag}_s201.json", "w"), indent=1)
        json.dump(plan(a, ts, "E4v", ts), open(f"{out}/1E4v_{tag}_s{ts}.json", "w"), indent=1)
        json.dump(plan(a, ts, "E4", ts), open(f"{out}/3E4plain_{tag}_s{ts}.json", "w"), indent=1)
for s in (202, 203):
    json.dump(plan(1.0, 10, "C0", s), open(f"{out}/2C0_L8_a1.0_t10_s{s}.json", "w"), indent=1)
for s in (1010, 2010):
    json.dump(plan(1.0, 10, "E4v", s), open(f"{out}/2E4v_L8_a1.0_t10_s{s}.json", "w"), indent=1)
PY
JOBS="$OUT/jobs.txt"
for f in "$OUT"/plans/*.json; do for arm in $ARMS; do echo "$f $arm"; done; done > "$JOBS"
echo "$(wc -l < "$JOBS") runs" | tee -a "$OUT/times.txt"
export OUT
xargs -P "$PAR" -L 1 sh -c 'b=$(basename "$0" .json); a=$(echo "$1" | tr : _); \
  case "$b" in *C0_*) mod=toqb.s2rc_ckpt;; *) mod=toqb.s2re4_run;; esac; \
  case "$b" in 3E4plain_*) d=plain;; *) d=main;; esac; \
  python -m $mod "$0" "$OUT/$d/runs/$b-$a.json" "$1" > "$OUT/$d/logs/$b-$a.log" 2>&1; \
  echo "$b $1 done $(TZ=Europe/Zurich date +%H:%M:%S)"' < "$JOBS" | tee "$OUT/progress.txt"
echo "matches end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
DIRS=""; for d in $W12_DIRS; do [ -d "$d" ] && DIRS="$DIRS $d"; done
if [ -n "$DIRS" ]; then
  python -m toqb.w12_check twin "$OUT/w12_twin.jsonl" $DIRS "$OUT/main/runs" > "$OUT/w12_twin.log" 2>&1
  echo "W12 twin part: $(wc -l < "$OUT/w12_twin.jsonl") points" | tee -a "$OUT/times.txt"
fi
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$DAY/e4v_match.zip" "$OUT" && echo "== DONE: $DAY/e4v_match.zip"
