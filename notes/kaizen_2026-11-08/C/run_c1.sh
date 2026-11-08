cd /mnt/c/Users/ADMINI~1/AppData/Local/Temp/claude/8a1ace7179dfc39a/59fede2c-03ff-41cb-a49f-2b1e696cbad7/scratchpad/kaizen/C
gcc -O2 -o /tmp/line_dfs line_dfs.c || exit 1
echo "== sanity 4x2x2 bridges 1,5, E=0"; timeout 300 /tmp/line_dfs 2 0 2000 1 200000 1,5
echo "== 4x2x2 bridges 3,7, E=0"; timeout 300 /tmp/line_dfs 2 0 3000 1 200000 3,7
echo "== 4x2x2 bridges 3,7, E=2"; timeout 300 /tmp/line_dfs 2 2 2000 1 400000 3,7
