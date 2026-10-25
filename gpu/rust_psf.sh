# Sourced by the GPU scripts after the venv and the exports (2026-10-21). RUST=1 (the default): the PSF template arm's
# template is built in Rust and checked identical to the Python's when built (toqb.ringport, TOQB_RUST_TEMPLATE=check),
# and bound in Rust (toqb.rustbind, TOQB_FAST_PSF=1). PSF-Zero's rust/psfbind is (re)built here with cargo; without
# cargo the script stops (install: curl --proto '=https' -sSf https://sh.rustup.rs | sh -s -- -y; then
# . "$HOME/.cargo/env"). RUST=0: the Python path, as before.
if [ "${RUST:-1}" = "1" ]; then
  [ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"  # rustup's cargo (gpu/setup_and_bench.sh installs it there)
  # always rebuilt from the checked-out psf-zero, so an older library never runs; no cargo, no run
  command -v cargo > /dev/null 2>&1 || { echo "STOP: RUST=1 needs cargo (see the header of gpu/rust_psf.sh)"; exit 1; }
  cargo build --release --quiet --manifest-path "$PSF/rust/psfbind/Cargo.toml" || { echo "STOP: rust/psfbind did not build"; exit 1; }
  python - <<'PY' || { echo "STOP: RUST=1 needs PSF-Zero's rust/psfbind built with the ring builder (install cargo, see gpu/rust_psf.sh)"; exit 1; }
from toqb import rustbind as RB
lib = RB.cdll()
lib.psfbind_ring_template, lib.psfbind_angles
PY
  # a24 (the default front end from 2026-10-24) builds the template in Rust itself and checks it against its Python
  # with PSF_RUST_TEMPLATE=check; a22 ignores both variables and is checked by TOQB_RUST_TEMPLATE=check as before
  export TOQB_FAST_PSF=1 TOQB_RUST_TEMPLATE=check PSF_RUST_TEMPLATE=check \
    PSF_BIND_LIB="$PSF/rust/psfbind/target/release/libpsfbind.so"
  echo "RUST=1: TOQB_FAST_PSF=1 TOQB_RUST_TEMPLATE=check PSF_RUST_TEMPLATE=check, front end ${PSF_AI_FILE:-a25 (default)} (psf-zero $(git -C "$PSF" log --oneline -1 | cut -c1-7))" | tee "$OUT/rust.txt"
else
  echo "RUST=0: the Python path" | tee "$OUT/rust.txt"
fi
