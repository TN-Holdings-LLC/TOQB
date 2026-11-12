#!/bin/bash
# heartbeat (VS Claude): one line a minute into STEM_progress.log while run_pod_m.sh runs: CET time, configurations
# written (of 6), busy workers (>50% CPU), load average, largest worker RSS (MB)
ST=$1
while pgrep -f "run_pod_m.sh" > /dev/null; do
  rows=$(wc -l < ${ST}_design.jsonl 2>/dev/null || echo 0)
  busy=$(ps -eo pcpu,args | awk '/design_pod.py/ && !/awk/ && $1 > 50' | wc -l)
  rss=$(ps -eo rss,args | awk '/design_pod.py/ && !/awk/ {if ($1 > m) m = $1} END {print int(m / 1024)}')
  echo "$(TZ=Europe/Zurich date +%H:%M:%S) configs $rows/6 busy_workers $busy load $(cut -d' ' -f1-3 /proc/loadavg) max_rss_mb $rss" >> ${ST}_progress.log
  sleep 60
done
echo "$(TZ=Europe/Zurich date +%H:%M:%S) run_pod_m.sh ended" >> ${ST}_progress.log
