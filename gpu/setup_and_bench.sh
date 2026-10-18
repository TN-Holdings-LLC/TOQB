#!/bin/bash
# GPU pod: install TOQB's environment, build PSF-Zero's Rust core, check the trajectory engine on the GPU against the
# density-matrix engines (n = 6), and time it on S2R's classifier (n = 10, L = 8, 16, 24). Run from the folder that
# holds the TOQB clone:  bash TOQB/gpu/setup_and_bench.sh 2>&1 | tee bench.txt
set -u
W=$(pwd)
[ -d "$W/TOQB" ] || { echo "STOP: no TOQB clone here"; exit 1; }
[ -d "$W/psf" ] || git clone -q https://github.com/TN-Holdings-LLC/psf-zero.git "$W/psf" || { echo "STOP: psf-zero clone"; exit 1; }
python3 -m venv "$W/venv" && . "$W/venv/bin/activate"
pip install -q qiskit==2.5.2 qiskit-aer==0.17.2 qiskit-ibm-runtime==0.49.0 numpy scipy maturin cupy-cuda12x \
  || { echo "STOP: pip"; exit 1; }
command -v cargo >/dev/null || { curl -sSf https://sh.rustup.rs | sh -s -- -y -q && . "$HOME/.cargo/env"; }
( cd "$W/psf" && pip install -q -e . && maturin develop --release -q ) || { echo "STOP: PSF-Zero core"; exit 1; }
python -c "import psf_zero_core as c; print('CORE_VERSION', c.CORE_VERSION)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
nproc
export PYTHONPATH="$W/TOQB" PSF_ZERO_REPO="$W/psf" PYTHONWARNINGS=ignore \
  PSF_COMPILE_FILE="$W/psf/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$W/psf/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$W/TOQB" && git log --oneline -1
echo "== check on the GPU, complex128"; TOQB_XP=cupy python -m toqb.check_traj 4000
echo "== check on the GPU, complex64"; TOQB_XP=cupy TOQB_TRAJ_DTYPE=complex64 python -m toqb.check_traj 4000
echo "== bench, complex64"; TOQB_XP=cupy TOQB_TRAJ_DTYPE=complex64 python -m toqb.bench_traj 10 8 16 24
echo "== bench, complex128, L = 16"; TOQB_XP=cupy python -m toqb.bench_traj 10 16
echo "== S2R2 smoke on the GPU"; mkdir -p /tmp/s2r2smoke && python - <<'PY'
import json
json.dump({"name": "S2R2 smoke", "device": "fake:FakeFez", "task": {"n": 10, "layers": 16, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_angle": 0.3, "teacher_gap": 0.2, "n_train": 64, "n_test": 100}, "s2r2": {"seed": 1, "init": 1.0, "sigma0": 0.3, "sigma_min": 0.01, "sigma_max": 1.0, "candidates": 16, "sim_batch": 4, "sim_traj": 32, "shots": 100, "budget_usd": 20.0, "max_loops": 100000}, "spsa2": {"seed": 1, "init": 1.0, "a": 0.5, "c": 0.2, "A": 10, "max_iterations": 100000}, "evaluation": {"test_traj": 64, "seed": 777, "every": 25}, "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}, "qpu_cost": {"per_shot_s": 0.00027, "per_circuit_s": 0.036, "usd_per_s": 1.6}}, open("/tmp/s2r2smoke/plan.json", "w"))
PY
for a in psfai:template qiskit:2:target:template; do TOQB_XP=cupy TOQB_TRAJ_DTYPE=complex64 python -m toqb.s2r2 s2r2 /tmp/s2r2smoke/plan.json /tmp/s2r2smoke/s2r2-$a.json $a; python -c "import json,sys; r=json.load(open(sys.argv[1])); print(r[\"times\"], r[\"loops\"], r[\"wall_s\"])" /tmp/s2r2smoke/s2r2-$a.json; done
echo "== DONE"
