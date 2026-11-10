eval "$(tr '\0' '\n' < /proc/1/environ | grep -E '^RUNPOD_(POD_ID|API_KEY)=' | sed 's/^/export /')"
S=$(( $(date -u -d '2026-11-10 15:40:00' +%s) - $(date -u +%s) ))
if [ -n "${RUNPOD_POD_ID:-}" ] && [ -n "${RUNPOD_API_KEY:-}" ] && [ "$S" -gt 0 ]; then
  setsid nohup bash -c "sleep $S; runpodctl stop pod \"\$RUNPOD_POD_ID\"" > /workspace/backstop2.log 2>&1 < /dev/null &
  echo "new backstop armed: $S s (15:40 UTC)"
  OLD=$(pgrep -f 'sleep 9000'); echo "old sleep pid: $OLD"; [ -n "$OLD" ] && kill $OLD && echo "old backstop removed"
else echo "NOT armed"; fi
unset RUNPOD_API_KEY
ps -eo pid,args | grep -E 'sleep [0-9]+' | grep -v grep
