#!/bin/bash
# heartbeat: one line a minute (time, finished rows, running case) into STEM_progress.log, until the run ends
ST=$1
while ps -eo args | grep -q "^bash run_pod.sh" > /dev/null; do
  p=$(ps -eo etimes,pcpu,rss,args --sort=-pcpu | grep "[h]ub_cost.py" | head -1)
  echo "$(TZ=CET-1 date +%H:%M:%S) rows_with_seconds $(grep -c '"seconds"' ${ST}_report.jsonl 2>/dev/null) running: $p" >> ${ST}_progress.log
  sleep 60
done
echo "$(TZ=CET-1 date +%H:%M:%S) run_pod.sh ended" >> ${ST}_progress.log
