#!/usr/bin/env bash
# Sparse Pauli dynamics at small delta on a many-core pod (for home; not run at the workplace).
# Needs: a TOQB checkout at this commit, a Rust toolchain (installed below if missing), python3.
# Writes OUT (default /workspace/spd) with the JSONL records and a log. CPU only; no GPU needed.
set -euo pipefail
OUT=${OUT:-/workspace/spd}
TOQB=${TOQB:-$(cd "$(dirname "$0")/../.." && pwd)}
mkdir -p "$OUT"
command -v cargo >/dev/null || { curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal; . "$HOME/.cargo/env"; }
cd "$TOQB/rust/spd" && cargo test --release 2>&1 | tail -3 && cargo build --release
N=$(nproc)
{
  echo "toqb $(git -C "$TOQB" rev-parse --short HEAD) nproc $N mem $(free -g | awk '/Mem/{print $2}') GB"
  echo "start $(TZ=Europe/Zurich date '+%F %T') CET"
} | tee "$OUT/times.txt"
cd "$TOQB/notes/spd_2026-11-04"
# validation at t = 6-8 against the sealed pod answers, then t = 20 on every qubit
python3 spd_check.py t678 "$OUT/spd_t678_small.jsonl" --deltas 3e-5,1e-5 --threads "$N" | tee -a "$OUT/log.txt"
python3 spd_check.py t20 "$OUT/spd_t20_small.jsonl" --deltas 3e-5,1e-5 --threads "$N" --cap 400000000 | tee -a "$OUT/log.txt"
echo "end $(TZ=Europe/Zurich date '+%F %T') CET" | tee -a "$OUT/times.txt"
