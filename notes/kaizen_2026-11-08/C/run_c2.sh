cd /mnt/c/Users/ADMINI~1/AppData/Local/Temp/claude/8a1ace7179dfc39a/59fede2c-03ff-41cb-a49f-2b1e696cbad7/scratchpad/kaizen/C
try() { echo "== $1"; shift; timeout 600 /tmp/line_dfs "$@" | tail -4; }
try "4xMx2 (M>=3): line 8, two bridge sets 1,5 and 3,7, E=0" 2 0 3000 1 300000 1,5 3,7
try "4xMx2: E=1" 2 1 3000 2 300000 1,5 3,7
try "4xMx2: E=2" 2 2 3000 3 500000 1,5 3,7
try "4x2x3: line 12, bridges 1,5,9, E=0" 3 0 2000 1 2000000 1,5,9
try "4x2x3: bridges 3,7,11, E=0" 3 0 2000 1 2000000 3,7,11
