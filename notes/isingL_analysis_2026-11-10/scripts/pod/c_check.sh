date -u +%T; uptime | sed 's/.*load/load/'; echo "expsim procs: $(pgrep -fc expsim.py)"
ps -eo pcpu,rss,args | grep [e]xpsim | awk '{c+=$1; r+=$2} END {printf "total CPU %.0f%%, RSS %.0f GB\n", c, r/1e6}'
tail -n 3 /workspace/ckit/out/q32.log; tail -n 2 /workspace/ckit/run.log
grep -i -E "error|traceback|failed" /workspace/ckit/out/q32.log | head -3
