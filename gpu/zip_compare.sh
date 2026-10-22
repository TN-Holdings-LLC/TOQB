#!/bin/bash
# GPU pod, report only (owner, 2026-10-22): the workplace's zipper schedule (toqb.ring_zip, arm psfai:template_zip)
# against today's template (psfai:template, item 31) on the device day's own plans (C r9: seed 301, C0, L 8 and 16,
# 2,000 loops, P 150 / 500, N 250), run as a rehearsal: the twin and the compilers on the published calibration
# (snapshot:marrakesh), the prediction, then the stand-in. Reported per arm and depth: the stand-in CE and accuracy,
# whether the stand-in CE falls in the twin's 99 % interval, CZ count and duration. Nothing is chosen from it; the
# day's job is not touched. Declared in prereg/drafts-2026-10-22/zip_compare_note.md before the run.
# Run from /workspace after the device day (venv, TOQB, psf there):
#   PLANS=/workspace/device_2026-10-22/plans DAY=/workspace/day_z OUT=/workspace/zip_2026-10-22 setsid nohup bash TOQB/gpu/zip_compare.sh > zip.txt 2>&1 < /dev/null &
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
PLANS=${PLANS:?set PLANS to the plans folder of the device day}
DAY=${DAY:?set DAY}
OUT=${OUT:?set OUT}
PAR=${PAR:-4}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, the venv and psf"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/logs" "$OUT/plans" "$OUT/runs" "$DAY"
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "PLANS=$PLANS PAR=$PAR"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python - "$PLANS" "$OUT/plans" <<'PY' || { echo "STOP: plans"; exit 1; }
import glob, json, os, sys
src, out = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(os.path.join(src, "L*_s*.json")))
assert len(files) == 2, files
for f in files:
    p = json.load(open(f))
    assert p["verify"] is False and p["train"]["init"] == 0.0, f
    p["device"] = "snapshot:marrakesh"   # the same calibration as the day's snapshot folder, as a rehearsal
    p["verify"] = True                   # then verified on the stand-in
    p["name"] = "zip compare (report only): " + p["name"]
    json.dump(p, open(os.path.join(out, os.path.basename(f)), "w"), indent=1)
    print(os.path.basename(f), "L", p["task"]["layers"], "P", p["task"]["n_test"], "seed", p["train"]["seed"])
PY
JOBS="$OUT/jobs.txt"
{ for f in "$OUT"/plans/*.json; do echo "$f psfai:template_zip"; done; \
  for f in "$OUT"/plans/*.json; do echo "$f psfai:template"; done; } > "$JOBS"
export OUT
xargs -P "$PAR" -L 1 sh -c 'b=$(basename "$0" .json); a=$(echo "$1" | tr : _); \
  python -m toqb.s2rc "$0" "$OUT/runs/$b-$a.json" "$1" > "$OUT/logs/$b-$a.log" 2>&1; \
  echo "$b $1 done $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/$b-$a.log" | cut -c1-240)"' < "$JOBS" \
  | tee "$OUT/progress.txt"
python - "$OUT" <<'PY' | tee "$OUT/summary.txt"
import glob, json, os, sys
import numpy as np
from toqb import task_loop as TL
from toqb.devices import get_device
out = sys.argv[1]
tg = get_device("snapshot:marrakesh").target
print("run | stand-in CE | in twin 99 % interval | stand-in acc | twin pred CE [interval] | CZ | duration us")
for f in sorted(glob.glob(os.path.join(out, "runs", "*.json"))):
    r = json.load(open(f))
    if not r.get("valid"):
        print(os.path.basename(f), "INVALID", r.get("error")); continue
    pr, rh = r["prediction"], r["rehearsal"]
    lo, hi = pr["ce_interval"]
    arm = TL.make_loop_arm(r["arm"]); arm.setup(tg)
    L = r["task"]["layers"]
    qc = TL.model_circuit(TL.angle_list(np.zeros(TL.n_params(10, L)), np.zeros(10), 10, L, r["task"]["enc"]), 10, L)
    c = arm.compile_circuit(qc)
    cz = sum(1 for i in c.data if len(i.qubits) == 2)
    dur = arm.pc._duration_s(c, tg)
    print(f"{os.path.basename(f)} | {rh['ce']:.4f} | {rh['ce_inside']} | {rh['acc']:.3f} | "
          f"{pr['ce_mean']:.4f} [{lo:.4f}, {hi:.4f}] | {cz} | {dur * 1e6:.2f}")
PY
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$DAY/zip_compare.zip" "$OUT" && echo "== DONE: $DAY/zip_compare.zip"
