#!/bin/bash
# GPU pod: the fruit match (design: prereg/drafts-2026-10-21/F1_fruit_match_design_2026-10-21.md; owner's scope of
# 2026-10-21: "recommended"). Simulation only, no IBM. E4 against C0 at matched budget points, with the theta = 0
# control, on fresh teachers 7, 8, 9 and the fixed ladder of teacher angles (W9 option C).
#   Z:  theta = 0, no training (toqb.s2re4_run, sweeps 0).
#   E4: toqb.s2re4_run, 3 sweeps at L 8 and 2 at L 16, TRAJ trajectories (two halves), checkpoints after every sweep.
#   C0: toqb.s2rc_ckpt (design C's loop, unchanged, with checkpoints), from theta = 0, 2,000 loops; checkpoints at the
#       loops of the same cost as E4's sweeps (one C0 loop 2,048 trajectory-circuits; one E4 sweep 3 x d x 64 x 32):
#       L 8 (d 170): 510, 1,020, 1,530; L 16 (d 330): 990, 1,980.
# Cells: angles 0.3, 1.0, 2.0 at L 8, teachers 7, 8, 9 (owner, 2026-10-21 05:30 CEST: the short version; L 16 was
# cut after the test match, where no method learned at L 16). F3 (reproducibility): angle 1.0, L 8,
# teacher 7: C0 also with seeds 202 and 203, E4 also with twin seeds 1007 and 2007.
# Order: all Z, then the runs (C0 and E4), then the F3 extra seeds.
#   DAY=... OUT=... setsid nohup bash TOQB/gpu/fruit_match.sh > fruit.txt 2>&1 < /dev/null &
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
ARMS=${ARMS:-psfai:template}
DAY=${DAY:?set DAY}
OUT=${OUT:?set OUT}
TRAJ=${TRAJ:-32}
PAR=${PAR:-6}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, the venv and psf (see the header)"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/logs" "$OUT/plans" "$OUT/runs" "$DAY"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git -C "$TQ" log --oneline -1)"; \
  echo "TRAJ=$TRAJ PAR=$PAR ARMS=$ARMS"; echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=cupy TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$TQ" || exit 1
python - "$OUT/plans" "$TRAJ" <<'PY'
import json, sys
out, traj = sys.argv[1], int(sys.argv[2])
CK = {8: [510, 1020, 1530], 16: [990, 1980]}
SW = {8: 3, 16: 2}
def plan(L, a, ts, kind, seed):
    if kind == "C0":
        train = {"seed": seed, "init": 0.0, "pairs": 8, "sim_batch": 4, "sim_traj": 32, "h": 0.1, "lr": 0.4,
                 "loops": 2000, "curve_every": 200, "curve_points": 100, "curve_traj": 64, "checkpoints": CK[L]}
    elif kind == "E4":
        train = {"seed": seed, "traj": traj, "sweeps": SW[L], "checkpoints": True}
    else:
        train = {"seed": seed, "sweeps": 0}
    return {"name": f"fruit match {kind} L{L} angle{a} teacher{ts} seed{seed}", "device": "snapshot:marrakesh",
            "task": {"n": 10, "layers": L, "enc": 1.5707963267948966, "teacher_seed": ts, "teacher_angle": a,
                     "teacher_gap": 0.2, "n_train": 64, "n_test": 500},
            "train": train, "predict": {"traj": 1024, "shots": 1000, "reps": 20000, "level": 0.99, "seed": 50000 + ts},
            "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}
cells = [(8, a, ts) for a in (0.3, 1.0, 2.0) for ts in (7, 8, 9)]
for L, a, ts in cells:
    pre = "1" if L == 16 else "2"
    tag = f"L{L}_a{a}_t{ts}"
    json.dump(plan(L, a, ts, "Z", ts), open(f"{out}/0Z_{tag}.json", "w"), indent=1)
    json.dump(plan(L, a, ts, "E4", ts), open(f"{out}/{pre}E4_{tag}_s{ts}.json", "w"), indent=1)
    json.dump(plan(L, a, ts, "C0", 201), open(f"{out}/{pre}C0_{tag}_s201.json", "w"), indent=1)
for s in (202, 203):
    json.dump(plan(8, 1.0, 7, "C0", s), open(f"{out}/3C0_L8_a1.0_t7_s{s}.json", "w"), indent=1)
for s in (1007, 2007):
    json.dump(plan(8, 1.0, 7, "E4", s), open(f"{out}/3E4_L8_a1.0_t7_s{s}.json", "w"), indent=1)
PY
JOBS="$OUT/jobs.txt"
for f in "$OUT"/plans/*.json; do for arm in $ARMS; do echo "$f $arm"; done; done > "$JOBS"
echo "$(wc -l < "$JOBS") runs" | tee -a "$OUT/times.txt"
export OUT
xargs -P "$PAR" -L 1 sh -c 'b=$(basename "$0" .json); a=$(echo "$1" | tr : _); \
  case "$b" in *C0_*) mod=toqb.s2rc_ckpt;; *) mod=toqb.s2re4_run;; esac; \
  python -m $mod "$0" "$OUT/runs/$b-$a.json" "$1" > "$OUT/logs/$b-$a.log" 2>&1; \
  echo "$b $1 done $(TZ=Europe/Zurich date +%H:%M:%S)"' < "$JOBS" | tee "$OUT/progress.txt"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$DAY/fruit_match.zip" "$OUT" && echo "== DONE: $DAY/fruit_match.zip"
