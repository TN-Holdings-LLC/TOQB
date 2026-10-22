#!/bin/bash
# GPU pod, design C's device day, C r9 draft (2026-10-21): C r8's day (below) plus four items, nothing else changed:
#   - INIT: the training's start, uniform(-INIT, INIT); C r8 had 1.0; the owner chose 0.0 (C0) on 2026-10-21;
#   - after assemble, the undamped readout is fixed before submission (toqb.s2rc_device_undamp fix: (lam, delta)
#     from the day's twin on the training inputs, no labels, no device data) into job/undamp.json, hashed with the job.
#   - RUST (default 1, gpu/rust_psf.sh): the PSF template is built in Rust (toqb.ringport) and checked identical to
#     the Python's when built (TOQB_RUST_TEMPLATE=check; a difference stops the run); the circuits, their QPY and
#     the binding stay Qiskit's (a device run never takes the fast path: verify false). Needs cargo on the pod.
#     A placement that would need VF2's search is outside the scope (owner, 2026-10-21): E5 below;
#   - FETCHES (the fetched folders in the fixed order marrakesh, fez, kingston): `s2rc_device choose` applies E2-E5
#     and the first eligible device is used (FETCH alone: that device, checked by precheck as before).
# C r8's text:
# GPU pod, design C's device day (C r8 section 5, steps 2-4; no IBM connection here): from the Target fetched at
# home, precheck, plans (seed 301, P_8 150, P_16 500, N 250, M 1, lr 0.4, 2,000 loops, T_pred 1,024, R 20,000),
# training with QPY export (4 runs in parallel), assemble (all checks, QPU time at most 150 s), and a zip for home with
# the job folder and the run records. Run from the folder that holds TOQB:
#   FETCH=<folder with target.pkl and fetch.json> DAY=... OUT=... setsid nohup bash TOQB/gpu/s2rc_device_day.sh > day.txt 2>&1 < /dev/null &
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:-}
FETCHES=${FETCHES:-}
[ -n "$FETCH$FETCHES" ] || { echo "STOP: set FETCHES (the fetched folders in the fixed order) or FETCH (one folder)"; exit 1; }
DAY=${DAY:?set DAY to the folder that receives the zip}
OUT=${OUT:?set OUT to a new folder for the results}
SEED=${SEED:-301}
LOOPS=${LOOPS:-2000}
P8=${P8:-150}
P16=${P16:-500}
SHOTS=${SHOTS:-250}
LR=${LR:-0.4}
PAR=${PAR:-4}
INIT=${INIT:-0.0}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, the venv and psf"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/runs" "$OUT/logs" "$DAY"
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
ZEXTRA=""
if [ -n "$FETCHES" ]; then  # r9's device rule: E2-E5 in the fixed order, the first eligible is used
  echo "== choose $(TZ=Europe/Zurich date '+%H:%M:%S %Z')"
  python -m toqb.s2rc_device choose --fetches $FETCHES --out "$OUT/choice.json" | tee "$OUT/choose.txt"
  FETCH=$(grep '^CHOSEN ' "$OUT/choose.txt" | tail -n 1 | cut -d' ' -f2-)
  [ -n "$FETCH" ] || { echo "STOP: no device is eligible (see $OUT/choose.txt)"; exit 1; }
  ZEXTRA="$OUT/choice.json $OUT/choose.txt $FETCHES"
fi
[ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: $FETCH has no target.pkl and fetch.json"; exit 1; }
[ -n "$ZEXTRA" ] || ZEXTRA="$FETCH"
step() { echo "== $1 $(TZ=Europe/Zurich date '+%H:%M:%S %Z')"; }
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; cat "$FETCH/fetch.json"; echo; \
  echo "SEED=$SEED LOOPS=$LOOPS P8=$P8 P16=$P16 SHOTS=$SHOTS LR=$LR PAR=$PAR INIT=$INIT"; } | tee "$OUT/times.txt"
step precheck
python -m toqb.s2rc_device precheck --fetch "$FETCH" | tee "$OUT/precheck.txt"
grep -q "all OK" "$OUT/precheck.txt" || { echo "STOP: precheck found problems"; exit 1; }
step plans
python -m toqb.s2rc_device plans --target "$FETCH/target.pkl" --out "$OUT/plans" --seeds "$SEED" --p8 "$P8" --p16 "$P16" \
  --shots "$SHOTS" --lr "$LR" --loops "$LOOPS" || { echo "STOP: plans failed"; exit 1; }
python - "$OUT/plans" "$INIT" <<'PY' || { echo "STOP: setting INIT failed"; exit 1; }
import glob, json, sys
for f in sorted(glob.glob(sys.argv[1] + "/*.json")):
    p = json.load(open(f))
    p["train"]["init"] = float(sys.argv[2])
    json.dump(p, open(f, "w"), indent=1)
    print(f, "init", p["train"]["init"])
PY
step train
export OUT
for f in "$OUT"/plans/L16_*.json "$OUT"/plans/L8_*.json; do for arm in qiskit:2:target:template psfai:template; do echo "$f $arm"; done; done |
  xargs -P "$PAR" -L 1 sh -c 'b=$(basename "$0" .json); a=$(echo "$1" | tr : _); \
    python -m toqb.s2rc "$0" "$OUT/runs/$b-$a.json" "$1" --qpy "$OUT/runs/$b-$a.qpy" > "$OUT/logs/$b-$a.log" 2>&1; \
    echo "$b $1 done $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/$b-$a.log" | cut -c1-200)"' | tee "$OUT/progress.txt"
step assemble
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds 150 \
  || { echo "STOP: assemble failed"; exit 1; }
step undamp
python -m toqb.s2rc_device_undamp fix --runs "$OUT/runs" --job "$OUT/job" --traj 1024 || { echo "STOP: undamp fix failed"; exit 1; }
sha256sum "$OUT/job/manifest.json" "$OUT/job/circuits.qpy" "$OUT/job/undamp.json" | tee "$OUT/job_sha256.txt"
step zip
python -m zipfile -c "$DAY/s2rc_device_day.zip" "$OUT/times.txt" "$OUT/rust.txt" "$OUT/precheck.txt" "$OUT/progress.txt" "$OUT/plans" \
  "$OUT/logs" "$OUT/runs" "$OUT/job" "$OUT/job_sha256.txt" $ZEXTRA \
  && echo "== DONE: $DAY/s2rc_device_day.zip ($(du -h "$DAY/s2rc_device_day.zip" | cut -f1))"
