#!/bin/bash
# Defect days (prereg/drafts-2026-10-31/defect_days_DRAFT.md; a draft until the owner fixes it): per day on ibm_kingston,
# job A = the rule's echo at n 20 40 72 on the standard placement; job B = n 40 72 on the placement masked by the
# frozen defect list (toqb.defect_list mask). D = 24, hz 0, 1000 shots. CPU only.
#   FETCH=DAY/fetch OUT=DAY/defect LIST=results/defect-list-replay-2026-10-31/observations.json bash TOQB/gpu/defect_days.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}; LIST=${LIST:-results/defect-list-replay-2026-10-31/observations.json}
NOTE=${NOTE:-prereg/drafts-2026-10-31/defect_days_DRAFT.md}; DEVICE=${DEVICE:-ibm_kingston}; NOW=${NOW:-2026-10-31T12:00:00}
[ -d "$TQ" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB and a fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -f "$TQ/$NOTE" ] && [ -f "$TQ/$LIST" ] || { echo "STOP: no declaration or no list"; exit 1; }
FB=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['backend'])" "$FETCH/fetch.json")
[ "$FB" = "$DEVICE" ] || { echo "STOP: the fetch is of $FB, not $DEVICE"; exit 1; }
[ -f "$VA" ] && . "$VA"
mkdir -p "$OUT"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
cd "$TQ" || exit 1
python -m pytest -q tests/test_kising_echo.py tests/test_defect_list.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)"; echo "list $(sha256sum $LIST)";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python -m toqb.defect_list mask "$FETCH" "$LIST" "$OUT/fetch_masked" --now "$NOW" | tee "$OUT/mask.txt"
for n in 20 40 72; do
  python -m toqb.kising_echo build "$FETCH" "$OUT/runs_A" --arm fold:rule --n $n --L 12 --hz 0 --h 0.6 --shots 1000 2>&1 \
    | grep -v Warn | tail -1 | sed "s/^/[A] /" | tee -a "$OUT/build.txt"
done
for n in 40 72; do
  python -m toqb.kising_echo build "$OUT/fetch_masked" "$OUT/runs_B" --arm fold:rule --n $n --L 12 --hz 0 --h 0.6 --shots 1000 2>&1 \
    | grep -v Warn | tail -1 | sed "s/^/[B] /" | tee -a "$OUT/build.txt"
done
# a size whose masked ring equals the standard ring is dropped from job B (reported)
python - "$OUT" <<'EOF' | tee -a "$OUT/build.txt"
import json, os, sys, shutil
out = sys.argv[1]
for n in (40, 72):
    name = f"kecho_n{n}_D24_hz0_h0.6-fold_rule"
    a = json.load(open(os.path.join(out, "runs_A", name + ".json")))["echo"]["measured_qubits"]
    pb = os.path.join(out, "runs_B", name + ".json")
    if os.path.exists(pb) and json.load(open(pb))["echo"]["measured_qubits"] == a:
        os.makedirs(os.path.join(out, "dropped_B"), exist_ok=True)
        for ext in (".json", ".qpy"):
            shutil.move(os.path.join(out, "runs_B", name + ext), os.path.join(out, "dropped_B", name + ext))
        print(f"[B] n {n}: the masked ring equals the standard ring; dropped from job B")
EOF
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs_A" --out "$OUT/job_A" --max-seconds 30 | tail -2 | tee -a "$OUT/assemble.txt"
if ls "$OUT"/runs_B/*.json >/dev/null 2>&1; then
  python -m toqb.s2rc_device assemble --fetch "$OUT/fetch_masked" --runs "$OUT/runs_B" --out "$OUT/job_B" --max-seconds 30 | tail -2 | tee -a "$OUT/assemble.txt"
fi
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/job_A $OUT/job_B"
