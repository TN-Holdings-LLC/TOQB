#!/bin/bash
# Flow K (prereg/drafts-2026-10-27/zipcyc_k_note.md): the count rule against the zipper on the rule's own cycle, same
# classifiers and qubits, on the twin of ibm_kingston's 2026-10-24 calibration. Run from the folder that holds TOQB,
# psf and venv:
#   TARGET=/workspace/target.pkl OUT=/workspace/zipcyc_k_2026-10-27 bash TOQB/gpu/zipcyc_k.sh 2>&1 | tee zk.txt
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=${OUT:?set OUT}
TARGET=${TARGET:?set TARGET}
WANT=3b93913856d2f0b9bf97ac03f89c43457157735413b02d8722c82d31065b218d
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, venv, psf"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
[ "$(sha256sum "$TARGET" | cut -c1-64)" = "$WANT" ] || { echo "STOP: $TARGET is not the 2026-10-24 kingston Target"; exit 1; }
. "$VA"
mkdir -p "$OUT"
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP TOQB_NOISELESS
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-16} OMP_NUM_THREADS=4
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
stamp() { echo "$1 $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"; }
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "note $(sha256sum prereg/drafts-2026-10-27/zipcyc_k_note.md)"; \
  echo "target $(sha256sum "$TARGET" | cut -c1-64)"; } | tee "$OUT/times.txt"
stamp start
COMMON=(--L 16 --P 24 --T 256 --models sim --max-active 24 --device "file:$TARGET")
python -m toqb.fold_lam "$OUT/check.jsonl" --n 18 20 --arms fold:rule --models-seed 0 "${COMMON[@]}" > "$OUT/check.log" 2>&1
python - "$OUT/check.jsonl" results/flow-g-2026-10-26/main.jsonl results/flow-j-2026-10-27/n20.jsonl <<'PY' | tee -a "$OUT/times.txt"
import json, sys
new = [json.loads(l) for l in open(sys.argv[1])]
ref = {}
for f in sys.argv[2:]:
    for r in map(json.loads, open(f)):
        if "mseed" not in r and r["arm"] == "fold:rule":
            ref[r["n"]] = r
bad = [f"n{r['n']}" for r in new if any(r.get(k) != ref[r["n"]].get(k) for k in ("lam", "q2", "us"))]
print("check", "FAIL " + " ".join(bad) if bad or len(new) != 2 else "PASS (fold:rule n = 18, 20 model 0 equal to flows G and J)")
PY
grep -q "check PASS" "$OUT/times.txt" || { stamp "STOP check failed"; exit 1; }
stamp "main start"
python -m toqb.fold_lam "$OUT/main.jsonl" --n 18 20 --arms fold:zipcyc --models-seed 0 1 2 3 "${COMMON[@]}" > "$OUT/main.log" 2>&1
stamp "main done"
python -m zipfile -c "$W/zipcyc_k.zip" "$OUT" && echo "== DONE: $W/zipcyc_k.zip"
