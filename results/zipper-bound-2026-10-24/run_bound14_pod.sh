#!/bin/bash
# The zipper bound at n = 14 on a CPU pod (cloud-side Claude, 2026-10-25); the same search as run_bound14_pc.sh
# (TOQB de3640b, results/zipper-bound-2026-10-24/bound_rs; n 14, limit 17, 64 shards), W workers at a time.
# Needs /root/bound_rs_de3640b.tgz. Resumable: a shard whose result file exists is skipped.
#   W=30 setsid nohup bash /root/run_bound14_pod.sh > /workspace/bound14_run.log 2>&1 < /dev/null &
set -u
W=${W:-30}
OUT=/workspace/bound14
mkdir -p "$OUT"; echo $$ > "$OUT/driver.pid"
if ! command -v cargo >/dev/null && [ ! -f "$HOME/.cargo/env" ]; then
  curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal >/dev/null 2>&1 || { echo "STOP: rustup failed"; exit 1; }
fi
[ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"
[ -d "$OUT/bound_rs" ] || tar xzf /root/bound_rs_de3640b.tgz -C "$OUT" || { echo "STOP: no source"; exit 1; }
grep -q nshard "$OUT/bound_rs/src/main.rs" || { echo "STOP: no shard option"; exit 1; }
CARGO_TARGET_DIR="$OUT/target" cargo build -q --release --manifest-path "$OUT/bound_rs/Cargo.toml" || { echo "STOP: build"; exit 1; }
B="$OUT/target/release/zipper_bound"
echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z') W=$W nproc $(nproc) $(grep -m1 'model name' /proc/cpuinfo)"
export B OUT
seq 0 63 | xargs -P "$W" -I{} bash -c '
  f="$OUT/s{}.txt"; [ -e "$f" ] && exit 0
  s=$(date +%s); "$B" 14 17 {}/64 > "$f.part" 2>&1 || exit 1
  echo "wall_s $(( $(date +%s) - s ))" >> "$f.part"; mv "$f.part" "$f"; echo "shard {} done $(date +%T)"'
done=$(ls "$OUT"/s*.txt 2>/dev/null | wc -l)
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z') shards $done of 64"
if [ "$done" = 64 ]; then
  best=$(grep -h "optimal extra" "$OUT"/s*.txt | awk '{print $5}' | sort -n | head -1)
  echo "== DONE least extra ${best:-none up to 17}, layouts $(grep -h '^layout' "$OUT"/s*.txt | wc -l)"
  cd /workspace && tar czf /root/bound14_results.tgz bound14/s*.txt && echo "results: /root/bound14_results.tgz"
fi
