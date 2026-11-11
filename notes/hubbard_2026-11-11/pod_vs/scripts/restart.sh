#!/bin/bash
# restart.sh STEM "Ls" "Ss" BUDGET_H : stop whatever runs, note it, start run_pod.sh (thread-limited c1) and the heartbeat
cd /root/hub
ST=$1
pkill -f "bash run_pod.sh" ; sleep 1; pkill -f "python3 hub_cost.py"; pkill -f "bash hb.sh"; sleep 2
T=$(TZ=CET-1 date +%H:%M:%S)
echo "{\"note\": \"VS: restarted $T CET with quimb threads 1 (chi <= 512) / 8 (chi >= 1024); rows above ran with 16 threads\"}" >> ${ST}_report.jsonl
echo "restart threads $T" >> ${ST}_progress.log
setsid nohup bash run_pod.sh "$2" "$3" "256 512 1024 2048" $ST $4 > ${ST}_screen_c1t.log 2>&1 < /dev/null &
sleep 3
setsid nohup bash hb.sh $ST > /dev/null 2>&1 < /dev/null &
sleep 1
echo "$ST restarted $T; running: $(ps -eo args | grep -c '^bash run_pod.sh')"
