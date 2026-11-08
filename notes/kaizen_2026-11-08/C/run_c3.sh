cd /mnt/c/Users/ADMINI~1/AppData/Local/Temp/claude/8a1ace7179dfc39a/59fede2c-03ff-41cb-a49f-2b1e696cbad7/scratchpad/kaizen/C
try() { echo "== $1"; shift; timeout 600 /tmp/line_dfs "$@" > /tmp/ld.out; tail -4 /tmp/ld.out; grep -q FOUND /tmp/ld.out && ! grep -q "NOT FOUND" /tmp/ld.out; }
for E in 2 3 4 5 6; do try "4x2x3 bridges 1,5,9 E=$E" 3 $E 300 $E 2000000 1,5,9 && break; done
for E in 2 4 6 8; do try "4x2x4 bridges 1,5,9,13 E=$E" 4 $E 150 $E 3000000 1,5,9,13 && break; done
for E in 3 4 6 8 10; do try "4xMx3 (M>=3) bridges 1,5,9 and 3,7,11 E=$E" 3 $E 200 $E 3000000 1,5,9 3,7,11 && break; done
