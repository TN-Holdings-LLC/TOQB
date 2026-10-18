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
echo "== DONE"
