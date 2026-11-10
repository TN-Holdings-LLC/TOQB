nproc; grep -c ^processor /proc/cpuinfo
eval "$(tr '\0' '\n' < /proc/1/environ | grep -E '^RUNPOD_(POD_ID|API_KEY)=' | sed 's/^/export /')"
if [ -n "${RUNPOD_POD_ID:-}" ] && [ -n "${RUNPOD_API_KEY:-}" ] && command -v runpodctl >/dev/null; then
  setsid nohup bash -c 'sleep 9000; runpodctl stop pod "$RUNPOD_POD_ID"' > /workspace/backstop.log 2>&1 < /dev/null &
  echo "backstop armed (2.5 h) for pod $RUNPOD_POD_ID"
else echo "backstop NOT armed"; fi
unset RUNPOD_API_KEY
cd /workspace/ckit && WORKERS=60 setsid nohup bash run_pod_c.sh > run.log 2>&1 < /dev/null &
sleep 40; cat /workspace/ckit/run.log; tail -n 2 /workspace/ckit/out/q32.log; uptime; free -g | sed -n 2p
