#!/bin/bash
# Noise wall, stage 1 (prereg/drafts-2026-10-29/noise_wall_1_note.md), the build step: probe P1 (the weight-2 conserved
# charge, toqb.kising_charge) and probe P2 (<X_0>, toqb.lam_device --kind kising --twin none) of the kicked-Ising ring
# (J = pi/4, h = 0.6) at n = 20 and 40; arms fold:rule, fold:zipcyc (where a cycle of n qubits exists) and
# qiskit:2:blind:template; no twin, no quality number read by any arm. CPU is enough (the name follows the other
# scripts). Two jobs (one shot count per job): P1 at SHOTS1 (default 1000), P2 at SHOTS2 (default 250). From
# /workspace, with the fetch folder of the day from home:
#   FETCH=/root/nw1_fetch_2026-10-29 OUT=/workspace/nw1 nohup bash TOQB/gpu/noise_wall_1.sh > nw1.txt 2>&1 &
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; PSF=${PSF_DIR:-$W/psf}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}
NS=${NS:-"20 40"}; LS=${LS:-"24 50 100"}; L2=${L2:-"24 50"}
SHOTS1=${SHOTS1:-1000}; SHOTS2=${SHOTS2:-250}; MAX1=${MAX1:-120}; MAX2=${MAX2:-120}
COEF=${COEF:-"-1.2860758110631627 -1.2860758110631603"}  # the declared charge (b, c), from `kising_charge charges`
NOTE=prereg/drafts-2026-10-29/noise_wall_1_note.md
[ -d "$TQ" ] && [ -f "$VA" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB, venv, fetch"; exit 1; }
[ "${RUST:-1}" = "1" ] && { [ -d "$PSF" ] || { echo "STOP: RUST=1 needs psf (or set RUST=0)"; exit 1; }; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
. "$VA"; mkdir -p "$OUT"
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore OMP_NUM_THREADS=4 TOQB_NOISELESS=numpy
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
python -m pytest -q tests/test_kising_charge.py tests/test_kising.py tests/test_kising_formula.py \
  tests/test_lam_device_blind.py tests/test_fold.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; [ -d "$PSF" ] && echo "psf-zero $(git -C "$PSF" log --oneline -1 | cut -c1-40)"; \
  echo "note $(sha256sum $NOTE)"; echo "tests $(tail -1 "$OUT/check_tests.log")"; \
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")"; \
  echo "charge (b, c) declared: $COEF"; echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
# the declared charge must equal the one computed at each n (noiseless criterion; n-independent)
python - $NS <<PY | tee -a "$OUT/times.txt"
import sys
from toqb import kising_charge as KC
dec = [float(v) for v in "$COEF".split()]
for n in [int(v) for v in sys.argv[1:]]:
    ch = KC.charges(n, 0.6)
    d = max(abs(ch["coef"][0] - dec[0]), abs(ch["coef"][1] - dec[1]))
    print("charge check n", n, "PASS" if d < 1e-9 and ch["dim"] == 2 else "FAIL", f"(max diff {d:.1e}, dim {ch['dim']})")
PY
grep -q "charge check.*FAIL" "$OUT/times.txt" && { echo "STOP: charge check failed"; exit 1; }
B1() { python -m toqb.kising_charge build "$FETCH" "$OUT/runs1" --shots "$SHOTS1" --coef $COEF "$@" 2>&1 | grep -v Warn | tail -1 | tee -a "$OUT/build.txt"; }
B2() { python -m toqb.lam_device build "$FETCH" "$OUT/runs2" --kind kising --twin none --P 64 --shots "$SHOTS2" "$@" 2>&1 | grep -v Warn | tail -1 | tee -a "$OUT/build.txt"; }
for n in $NS; do
  for arm in fold:rule fold:zipcyc qiskit:2:blind:template; do
    for L in $LS; do B1 --arm $arm --n $n --L $L; done
    for L in $L2; do B2 --arm $arm --n $n --L $L --mseed 0; done
  done
done
# a refused placement (e.g. no cycle of n qubits for the zipper) leaves no record; it is in build.txt
python -m toqb.kising_charge rehearse "$OUT/runs1" --p 0.0051 | tee "$OUT/rehearse.txt"
python - "$OUT/runs1" "$OUT/runs2" <<'PY' | tee "$OUT/cells.txt"
import glob, json, sys
from qiskit import qpy
for d in sys.argv[1:]:
    for f in sorted(glob.glob(d + "/*.json")):
        r = json.load(open(f)); c = qpy.load(open(f[:-5] + ".qpy", "rb"))[0]
        qs = sorted({c.find_bit(q).index for i in c.data for q in i.qubits if i.operation.name not in ("barrier", "delay")})
        m0 = [c.find_bit(i.qubits[0]).index for i in c.data if i.operation.name == "measure" and c.find_bit(i.clbits[0]).index == 0]
        print(f.split("/")[-1][:-5], "q2", r["q2"], "us", r["us"], "active", r.get("active"), "measured", m0, "qubits", qs)
PY
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs1" --out "$OUT/job1" --max-seconds "$MAX1" | tee "$OUT/assemble1.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs2" --out "$OUT/job2" --max-seconds "$MAX2" | tee "$OUT/assemble2.txt"
[ -f "$OUT/job1/manifest.json" ] && [ -f "$OUT/job2/manifest.json" ] || { echo "STOP: no job"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/nw1_jobs.zip" "$OUT" && echo "== DONE: $W/nw1_jobs.zip"
# home, after the owner's go: s2rc_device submit/result for job1 and job2; then
#   python -m toqb.lam_device score $OUT/job2 $OUT/runs2
#   python -m toqb.kising_charge score $OUT/job1 $OUT/runs1 --p 0.0051 --p-range 0.00475 0.00548 \
#          --p2-job $OUT/job2 --p2-runs $OUT/runs2                                  (primary, declared p)
#   python -m toqb.kising_charge score $OUT/job1 $OUT/runs1 --p-from-n 20 --p-L 50 \
#          --p2-job $OUT/job2 --p2-runs $OUT/runs2 --out-name charge_score_p1ref.json   (secondary)
