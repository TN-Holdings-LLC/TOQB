#!/bin/bash
# Device test D5 (prereg/drafts-2026-10-28/device_d5_note.md), the pod step: parts A (classifier n = 20, L = 16,
# fold:rule and fold:zipcyc), B (classifier n = 22, L = 16, fold:rule), C (kicked Ising L = 24, n = 20 with twin,
# n = 32 and 40 without); one job of at most 200 s; amendment 1 adds Qiskit to part A. Waits for D4's pod step to finish (the same GPU). From /workspace:
#   FETCH=/root/d3_fetch_2026-10-28 OUT=/workspace/d5 nohup bash TOQB/gpu/device_d5.sh > d5.txt 2>&1 &
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; PSF=${PSF_DIR:-$W/psf}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB, venv, psf, fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
while [ -e "$W/d4" ] && ! grep -q "== DONE\|STOP" "$W/d4.txt" 2>/dev/null; do sleep 60; done
. "$VA"; mkdir -p "$OUT"
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-16} OMP_NUM_THREADS=4
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
python -m pytest -q tests/test_kising.py tests/test_kising_formula.py > "$OUT/check.log" 2>&1
tail -1 "$OUT/check.log" | grep -q "11 passed" || { echo "STOP: tests (see check.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "psf-zero $(git -C "$PSF" log --oneline -1 | cut -c1-40)"; \
  echo "note $(sha256sum prereg/drafts-2026-10-28/device_d5_note.md)"; echo "amend1 $(sha256sum prereg/drafts-2026-10-28/device_d5_amend1.md)"; echo "tests $(tail -1 "$OUT/check.log")"; \
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
B() { python -m toqb.lam_device build "$FETCH" "$OUT/runs" --P 64 --traj 256 "$@" 2>&1 | grep -v Warn | tail -1 | tee -a "$OUT/build.txt"; }
B --arm fold:rule --n 20 --L 16 --mseed 0 --shots 1000
B --arm fold:zipcyc --n 20 --L 16 --mseed 0 --shots 1000
B --arm qiskit:2:target:template --n 20 --L 16 --mseed 0 --shots 1000 --twin auto
B --arm fold:rule --kind kising --h 0.6 --n 20 --L 24 --mseed 0 --shots 1000
B --arm fold:rule --kind kising --h 0.6 --n 32 --L 24 --mseed 0 --shots 1000 --twin none
B --arm fold:rule --kind kising --h 0.6 --n 40 --L 24 --mseed 0 --shots 1000 --twin none
B --arm fold:rule --n 22 --L 16 --mseed 0 --shots 1000
python -m toqb.lam_device rehearse "$OUT/runs" --reps 2000 2>&1 | grep -v Warn | tee "$OUT/rehearse.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds 200 | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/d5_job.zip" "$OUT" && echo "== DONE: $W/d5_job.zip"
