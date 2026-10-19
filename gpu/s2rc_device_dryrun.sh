#!/bin/bash
# GPU pod: design C's device path, once end to end with NO IBM connection (procedure check (a), C r4 section 6).
# fetch takes FakeFez's Target from qiskit_ibm_runtime's fake provider; plans, training with QPY export and assemble
# run exactly as on the device day (option A's sizes: P_8 150, P_16 500, N 250, M 1; 20 loops only, so the models are
# not trained: this checks the procedure, not the learning); submit --local --noiseless samples the circuits with a
# noiseless Qiskit Aer (fast; the plumbing is what is checked); score writes score.json / score.md. Not scored;
# seed 299 is outside every scored range.
# Needs the environment that gpu/s2rg_pilot.sh built (venv, psf next to TOQB). Run from the folder that holds TOQB:
#   DAY=... OUT=... setsid nohup bash TOQB/gpu/s2rc_device_dryrun.sh > dryrun.txt 2>&1 &
# Elsewhere (for example the home PC's GPU) set TOQB_DIR, PSF_DIR and VENV_ACT (the venv's activate script).
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
DAY=${DAY:?set DAY to the folder that receives the zip}
OUT=${OUT:?set OUT to a new folder for the results}
LOOPS=${LOOPS:-20}
P8=${P8:-150}
P16=${P16:-500}
TRAJ=${TRAJ:-1024}
REPS=${REPS:-20000}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, the venv and psf (see the header)"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/runs" "$OUT/logs"
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$TQ" || exit 1
step() { echo "== $1 $(TZ=Europe/Zurich date '+%H:%M:%S %Z')"; }
{ echo "toqb $(git log --oneline -1)"; echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "LOOPS=$LOOPS P8=$P8 P16=$P16 TRAJ=$TRAJ REPS=$REPS"; } | tee "$OUT/times.txt"
step fetch
python -m toqb.s2rc_device fetch --fake FakeFez --out "$OUT/fetch" || { echo "STOP: fetch failed"; exit 1; }
step plans
python -m toqb.s2rc_device plans --target "$OUT/fetch/target.pkl" --out "$OUT/plans" --seeds 299 --p8 "$P8" --p16 "$P16" \
  --shots 250 --lr 0.4 --loops "$LOOPS" --traj "$TRAJ" --reps "$REPS" || { echo "STOP: plans failed"; exit 1; }
step train
export OUT
for f in "$OUT"/plans/*.json; do for arm in qiskit:2:target:template psfai:template; do echo "$f $arm"; done; done |
  xargs -P 4 -L 1 sh -c 'b=$(basename "$0" .json); a=$(echo "$1" | tr : _); \
    python -m toqb.s2rc "$0" "$OUT/runs/$b-$a.json" "$1" --qpy "$OUT/runs/$b-$a.qpy" > "$OUT/logs/$b-$a.log" 2>&1; \
    echo "$b $1 done $(tail -n 1 "$OUT/logs/$b-$a.log" | cut -c1-200)"'
step assemble
python -m toqb.s2rc_device assemble --fetch "$OUT/fetch" --runs "$OUT/runs" --out "$OUT/job" --max-seconds 150 \
  || { echo "STOP: assemble failed"; exit 1; }
ls -l "$OUT/job"
step "submit (LOCAL: noiseless Qiskit Aer; no IBM connection)"
python -m toqb.s2rc_device submit --job "$OUT/job" --local --noiseless || { echo "STOP: local submit failed"; exit 1; }
step score
python -m toqb.s2rc_device score --job "$OUT/job" || { echo "STOP: score failed"; exit 1; }
step end
python -m zipfile -c "$DAY/s2rc_device_dryrun.zip" "$OUT/times.txt" "$OUT/fetch/fetch.json" "$OUT/plans" "$OUT/logs" \
  "$OUT/job/manifest.json" "$OUT/job/submission.json" "$OUT/job/score.json" "$OUT/job/score.md" \
  && echo "== DONE: $DAY/s2rc_device_dryrun.zip"
