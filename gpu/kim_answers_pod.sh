#!/bin/bash
# P5 stage C answers on a pod (prereg/drafts-2026-11-03/kim_cd_note.md): <Z_q> at theta 0.4, 0.8, 1.0, t = 6, 7, 8 for
# every lattice qubit whose causal cone has at most 33 qubits (single precision, one GPU with 80 GB or more), after
# three checks. Needs TOQB and psf-os side by side, lattice.json (written by gpu/kim_cd.py) in the working folder,
# and Python with qiskit, numpy, cupy. From /workspace:
#   pip install "qiskit==2.5.2" "cupy-cuda12x==14.2.0" pytest
#   OUT=/workspace/kimc nohup bash TOQB/gpu/kim_answers_pod.sh > kimc.txt 2>&1 < /dev/null &
# STOP (no answer is written) if a check fails:
#   K1 GPU single = the CPU answers sealed with the build (theta 0.8, t = 5, every qubit): 1e-4;
#   K2 GPU single = GPU double on the five largest cones at t = 6 (theta 0.8): 1e-4;
#   K3 GPU single at theta pi/2, t = 6 and 7 = the stabilizer answers sealed with the build (answered qubits): 1e-4.
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; PO=${PSFOS_DIR:-$W/psf-os}; OUT=${OUT:?set OUT}; LAT=${LAT:-$W/lattice.json}
[ -d "$TQ" ] && [ -d "$PO" ] && [ -f "$LAT" ] || { echo "STOP: TOQB, psf-os or lattice.json missing"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -n "${VENV_ACT:-}" ] && . "$VENV_ACT"
mkdir -p "$OUT"
export PYTHONPATH="$PO:$TQ" PYTHONWARNINGS=ignore
cd "$TQ" || exit 1
python -m pytest -q tests/test_kim_answers.py tests/test_du_answers.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $( (git log --oneline -1 2>/dev/null || cat COMMIT.txt) | cut -c1-60)"; echo "note $(sha256sum prereg/drafts-2026-11-03/kim_cd_note.md)";
  echo "lattice $(sha256sum "$LAT")"; echo "script $(sha256sum gpu/kim_answers.py)";
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python - "$OUT" "$LAT" <<'EOF' 2>&1 | tee -a "$OUT/progress.txt"
import json, os, sys, hashlib
import numpy as np
sys.path.insert(0, "gpu")
import kim_answers as KA
out, lat = sys.argv[1], json.load(open(sys.argv[2]))
P2 = float(np.pi / 2)
checks = {}
log = lambda s: print(s, flush=True)
def stop(msg):
    json.dump(checks, open(os.path.join(out, "checks.json"), "w"), indent=1)
    print("STOP:", msg); sys.exit(1)
# K1
r = KA.run(lat, [0.8], [5], "cupy", "single")[f"{0.8:.6f}"]["5"]["z"]
d = float(np.max(np.abs(np.array(r) - np.array(lat["check_K1"]["z"]))))
checks["K1"] = dict(max_diff=d, ok=d <= 1e-4); log(f"K1 theta 0.8 t 5: max |GPU - CPU| {d:.2e}")
if not checks["K1"]["ok"]: stop("K1")
# K2
sizes = lat["cone_sizes"]["6"]
big = [lat["qubits"][i] for i in np.argsort(sizes)[-5:]]
s = KA.run(lat, [0.8], [6], "cupy", "single", only=set(big))[f"{0.8:.6f}"]["6"]["z"]
dd = KA.run(lat, [0.8], [6], "cupy", "double", only=set(big))[f"{0.8:.6f}"]["6"]["z"]
d = max(abs(a - b) for a, b in zip(s, dd) if a is not None)
checks["K2"] = dict(qubits=[int(x) for x in big], cone=sorted(sizes)[-5:], max_diff=float(d), ok=d <= 1e-4)
log(f"K2 cones {sorted(sizes)[-5:]}: max |single - double| {d:.2e}")
if not checks["K2"]["ok"]: stop("K2")
# K3
k3 = []
for t in (6, 7):
    g = KA.run(lat, [P2], [t], "cupy", "single", lat["max_qubits"])[f"{P2:.6f}"][str(t)]["z"]
    ref = lat["check_K3"][str(t)]
    d = max(abs(a - b) for a, b in zip(g, ref) if a is not None)
    k3.append(dict(t=t, answered=sum(a is not None for a in g), max_diff=float(d), ok=d <= 1e-4))
    log(f"K3 theta pi/2 t {t}: {k3[-1]['answered']} qubits, max |GPU - stabilizer| {d:.2e}")
checks["K3"] = k3
if not all(x["ok"] for x in k3): stop("K3")
res = KA.run(lat, lat["thetas"], lat["ts"], "cupy", "single", lat["max_qubits"], log=log)
json.dump(checks, open(os.path.join(out, "checks.json"), "w"), indent=1)
json.dump(res, open(os.path.join(out, "answers_C.json"), "w"))
print("answers_C.json sha256", hashlib.sha256(open(os.path.join(out, "answers_C.json"), "rb").read()).hexdigest())
EOF
[ -f "$OUT/answers_C.json" ] || { echo "STOP: no answers (see progress.txt, checks.json)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/kimc_answers.zip" "$OUT" && echo "== DONE: $W/kimc_answers.zip"
