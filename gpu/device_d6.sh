#!/bin/bash
# Device test D6 (prereg/drafts-2026-10-28/device_d6_note.md), the pod step: classifier L = 16, n = 13-24, model 0, 64
# inputs x 250 shots, arms fold:rule, fold:zipcyc (even n), qiskit:2:blind:template; no twin; the noiseless reference
# on the GPU after the declared check; one job of at most 300 s. From /workspace, with the fetch folder from home:
#   FETCH=/root/d6_fetch_2026-10-28 OUT=/workspace/d6 nohup bash TOQB/gpu/device_d6.sh > d6.txt 2>&1 &
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; PSF=${PSF_DIR:-$W/psf}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB, venv, psf, fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
. "$VA"; mkdir -p "$OUT"
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-16} OMP_NUM_THREADS=4
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
python -m pytest -q tests/test_lam_device_blind.py tests/test_fold.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "psf-zero $(git -C "$PSF" log --oneline -1 | cut -c1-40)"; \
  echo "note $(sha256sum prereg/drafts-2026-10-28/device_d6_note.md)"; echo "tests $(tail -1 "$OUT/check_tests.log")"; \
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python - <<'PY' | tee -a "$OUT/times.txt"
import os
import numpy as np
from toqb import lam_device as LD
th, X = LD.model_inputs(13, 16, 0, 4)
os.environ["TOQB_NOISELESS"] = "qiskit"; a = LD.noiseless_z(th, X, 13, 16)
os.environ["TOQB_NOISELESS"] = "cupy"; b = LD.noiseless_z(th, X, 13, 16)
d = float(np.abs(a - b).max())
print("check", "PASS" if d < 1e-9 else "FAIL", f"(GPU reference against Qiskit, n = 13, L = 16, 4 inputs: {d:.1e})")
PY
grep -q "check PASS" "$OUT/times.txt" || { echo "STOP: check failed"; exit 1; }
export TOQB_NOISELESS=cupy
B() { python -m toqb.lam_device build "$FETCH" "$OUT/runs" --P 64 --shots 250 --twin none "$@" 2>&1 | grep -v Warn | tail -1 | tee -a "$OUT/build.txt"; }
for n in 13 14 15 16 17 18 19 20 21 22 23 24; do
  B --arm fold:rule --n $n --L 16 --mseed 0
  [ $((n % 2)) -eq 0 ] && B --arm fold:zipcyc --n $n --L 16 --mseed 0
  B --arm qiskit:2:blind:template --n $n --L 16 --mseed 0
done
python - "$OUT/runs" <<'PY' | tee "$OUT/cells.txt"
import glob, json, sys
from qiskit import qpy
for f in sorted(glob.glob(sys.argv[1] + "/*.json")):
    r = json.load(open(f)); c = qpy.load(open(f[:-5] + ".qpy", "rb"))[0]
    qs = sorted({c.find_bit(q).index for i in c.data for q in i.qubits if i.operation.name not in ("barrier", "delay")})
    m0 = [c.find_bit(i.qubits[0]).index for i in c.data if i.operation.name == "measure" and c.find_bit(i.clbits[0]).index == 0]
    print(f.split("/")[-1][:-5], "q2", r["q2"], "us", r["us"], "active", r.get("active"), "measured", m0, "qubits", qs)
PY
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds 300 | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/d6_job.zip" "$OUT" && echo "== DONE: $W/d6_job.zip"
