#!/bin/bash
# TOQB S2R stage 0, after an interruption (prereg/2026-10-17-s2r-stage0.md, section 2: "a run that stops is started
# again into a new folder; the first complete run is scored"; a run is one of the 80). Runs only the runs that have no
# record in the first folder (OLD), each into a new folder (NEW), with the same code, plans and checks as run.sh; then
# builds a third folder (MERGED) with the first complete record of every run, scores it and zips it. Nothing existing
# is overwritten. Gentler on the machine than run.sh: fewer processes (PAR, default 5), lowest CPU priority, and a
# memory guard that stops the runs (they leave no record and can be resumed again) when free memory falls below
# MINMB megabytes. Start it detached so that closing the terminal does not stop it:
#   DAY=... setsid nohup bash prereg/s2r-stage0-2026-10-17/resume.sh > ~/s2r_resume.out 2>&1 &
set -u
TOQB=${TOQB:-~/toqb_push_2026-10-15}
PSF=${PSF:-~/psf_zero_fresh_test}
DAY=${DAY:?set DAY to the folder that receives the zip}
PAR=${PAR:-5}
MINMB=${MINMB:-2000}
OLD=${OLD:-$HOME/toqb_runs_kept/s2r-stage0-2026-10-17}
NEW=${NEW:-$HOME/toqb_runs_kept/s2r-stage0-2026-10-17-resume1}
MERGED=${MERGED:-$HOME/toqb_runs_kept/s2r-stage0-2026-10-17-merged}
P=prereg/s2r-stage0-2026-10-17
cd "$TOQB" || { echo "STOP: no $TOQB"; exit 1; }
echo "9fa868b7f1d4e2738d82720e06090fb384177bafe5c2a33d2356abde058c4857  prereg/2026-10-17-s2r-stage0.md" | sha256sum -c --quiet || { echo "STOP: pre-registration changed"; exit 1; }
echo "ee1cf452a67124f7bbbccb8baacc056899fb61c24b5de54dc40e27717c38ca1e  $P/SHA256SUMS" | sha256sum -c --quiet || { echo "STOP: plan list changed"; exit 1; }
echo "510baa0d78565503cb68b4cd6a46ffac225476febb3bc96dfb83d91c5a68ebac  $P/CODE_SHA256SUMS" | sha256sum -c --quiet || { echo "STOP: code list changed"; exit 1; }
( cd "$P" && sha256sum -c --quiet SHA256SUMS ) || { echo "STOP: a plan changed"; exit 1; }
sha256sum -c --quiet "$P/CODE_SHA256SUMS" || { echo "STOP: TOQB code differs from the pre-registered"; exit 1; }
( cd "$PSF" && printf '%s\n' \
  "254cfabc5924118a5c54e159fa2284202d21b87894202f447333de07f06b3728  patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  "625f9431344cd0fad6715ea44dc347044b0c64507c008f69202145d03b14a8ce  patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py" \
  | sha256sum -c --quiet ) || { echo "STOP: PSF-Zero files differ from the pre-registered ones"; exit 1; }
python -c "import qiskit, qiskit_aer; assert (qiskit.__version__, qiskit_aer.__version__) == ('2.5.2', '0.17.2')" \
  || { echo "STOP: needs Qiskit 2.5.2 and Aer 0.17.2"; exit 1; }
[ -d "$OLD" ] || { echo "STOP: no first folder $OLD"; exit 1; }
[ -e "$NEW" ] && { echo "STOP: $NEW exists; a run never overwrites another"; exit 1; }
[ -e "$MERGED" ] && { echo "STOP: $MERGED exists"; exit 1; }
for s in $(seq 9001 9020); do cmp -s "$P/plan_s$s.json" "$OLD/seed$s/plan.json" || { echo "STOP: $OLD/seed$s/plan.json differs"; exit 1; }; done
mkdir -p "$NEW/logs"
for s in $(seq 9001 9020); do mkdir -p "$NEW/seed$s" && cp "$P/plan_s$s.json" "$NEW/seed$s/plan.json"; done
JOBS="$NEW/jobs.txt"
for k in s2r spsa; do for s in $(seq 9001 9020); do for a in psfai:template qiskit:2:target:template; do
  f=$(echo $a | tr : _); [ -e "$OLD/seed$s/$k-$f.json" ] || echo "$k $s $a"; done; done; done > "$JOBS"
{ echo "toqb $(git log --oneline -1)"; echo "psf-zero $(git -C "$PSF" log --oneline -1)"; \
  python -c "import qiskit, qiskit_aer; print('qiskit', qiskit.__version__, 'aer', qiskit_aer.__version__)"; \
  echo "resume of $OLD: $(wc -l < "$JOBS") of 80 runs have no record there; PAR=$PAR, nice 19, MINMB=$MINMB"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$NEW/times.txt"
export PSF_ZERO_REPO="$PSF" PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py" PYTHONWARNINGS=ignore OUT=$NEW P
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 QISKIT_NUM_PROCS=1 \
  NUMEXPR_NUM_THREADS=1 QISKIT_PARALLEL=FALSE
xargs -P "$PAR" -L 1 sh -c 'f=$(echo $2 | tr : _); nice -n 19 python -m toqb.s2r "$0" "$OUT/seed$1/plan.json" \
    "$OUT/seed$1/$0-$f.json" "$2" > "$OUT/logs/seed$1-$0-$f.log" 2>&1; \
    echo "$0 seed $1 $2 done $(TZ=Europe/Zurich date +%H:%M:%S)"' < "$JOBS" &
XP=$!
# Memory record every minute, and the guard: below MINMB MB available, stop launching and stop every run (by pid)
# rather than let the machine freeze.
( while sleep ${MEMEVERY:-60}; do
    av=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)
    pids=$(pgrep -f "^python -m toqb.s2r")
    rss=0; [ -n "$pids" ] && rss=$(ps -o rss= -p $(echo $pids | tr ' ' ',') | awk '{s+=$1} END{print int(s/1024)}')
    echo "$(TZ=Europe/Zurich date +%H:%M:%S) available ${av} MB; runs $(echo $pids | wc -w), together ${rss} MB" >> "$NEW/logs/mem.txt"
    if [ "$av" -lt "$MINMB" ] && [ -n "$pids" ]; then
      echo "$(TZ=Europe/Zurich date +%H:%M:%S) STOP: available ${av} MB < $MINMB MB; stopping pids $pids" | tee -a "$NEW/logs/mem.txt"
      kill $XP; kill $pids
    fi
  done ) &
MON=$!
wait $XP
kill $MON 2>/dev/null
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$NEW/times.txt"
# The merged folder: for every run, its record from the first folder if there is one, otherwise from the new one.
mkdir -p "$MERGED"
missing=0
for s in $(seq 9001 9020); do mkdir -p "$MERGED/seed$s" && cp "$P/plan_s$s.json" "$MERGED/seed$s/plan.json"
  for k in s2r spsa; do for a in psfai:template qiskit:2:target:template; do f=$(echo $a | tr : _)
    if [ -e "$OLD/seed$s/$k-$f.json" ]; then cp "$OLD/seed$s/$k-$f.json" "$MERGED/seed$s/"; echo "$s $k $a first" >> "$MERGED/sources.txt"
    elif [ -e "$NEW/seed$s/$k-$f.json" ]; then cp "$NEW/seed$s/$k-$f.json" "$MERGED/seed$s/"; echo "$s $k $a resume1" >> "$MERGED/sources.txt"
    else echo "$s $k $a MISSING" >> "$MERGED/sources.txt"; missing=$((missing+1)); fi
  done; done; done
mkdir -p "$MERGED/first" "$MERGED/resume1"
cp -r "$OLD/logs" "$OLD/times.txt" "$MERGED/first/"; cp -r "$NEW/logs" "$NEW/times.txt" "$NEW/jobs.txt" "$MERGED/resume1/"
[ "$missing" -gt 0 ] && { echo "STOP: $missing runs still have no record (see $MERGED/sources.txt); resume again into new folders"; exit 1; }
python -m toqb.score_s2r "$MERGED" > "$MERGED/score.log" 2>&1
sed -n '1,/^## Reported/p' "$MERGED/score.md"
python -m zipfile -c "$DAY/s2r_stage0_results.zip" "$MERGED" && echo "== DONE: $DAY/s2r_stage0_results.zip"
