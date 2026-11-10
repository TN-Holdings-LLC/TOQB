eval "$(tr '\0' '\n' < /proc/1/environ | grep -E '^RUNPOD_(POD_ID|API_KEY)=' | sed 's/^/export /')"
S=$(( $(date -u -d '2026-11-10 15:45:00' +%s) - $(date -u +%s) ))
if [ -n "${RUNPOD_POD_ID:-}" ] && [ -n "${RUNPOD_API_KEY:-}" ] && [ "$S" -gt 0 ]; then
  setsid nohup bash -c "sleep $S; runpodctl remove pod \"\$RUNPOD_POD_ID\" || runpodctl stop pod \"\$RUNPOD_POD_ID\"" > /workspace/backstop3.log 2>&1 < /dev/null &
  echo "remove backstop armed: $S s (15:45 UTC = 00:45 JST)"
  OLD=$(pgrep -f 'sleep 5533'); [ -n "$OLD" ] && kill $OLD && echo "old stop backstop removed"
else echo "NOT armed"; fi
unset RUNPOD_API_KEY
runpodctl remove --help 2>&1 | head -3
ps -eo pid,args | grep -E 'sleep [0-9]+' | grep -v grep
