source ~/psf_zero_fresh_test/psf_zero_wsl_env_fresh/bin/activate
cd /mnt/c/Users/Administrator/AppData/Local/Temp/claude/8a1ace7179dfc39a/59fede2c-03ff-41cb-a49f-2b1e696cbad7/scratchpad/heis
echo "== bridges 1,5: 0 empty swaps"
python -I verify_line.py 1,5 "[\"0'\", '1', '0', \"1'\", \"2'\", '3', '2', \"3'\"]" "SWAP.U(3,2)@5 ; SWAP.U(3,3')@6 ; U(1',2')@3 ; SWAP.U(2',2)@4 ; SWAP.U(2',3')@5 ; SWAP.U(1,0)@1 ; SWAP.U(1,1')@2 ; U(1,2)@3 ; SWAP.U(0',0)@0 ; SWAP.U(0',1')@1" 4 0.05
echo "== bridges 3,7: 2 empty swaps"
python -I verify_line.py 3,7 "[\"0'\", '1', \"2'\", '0', \"1'\", '2', '3', \"3'\"]" "U(2,3)@5 ; SWAP.U(3,3')@6 ; SWAP(2',0)@2 ; SWAP.U(2',1')@3 ; SWAP.U(2',2)@4 ; U(2',3')@5 ; SWAP.U(1,0)@1 ; SWAP.U(1,1')@2 ; SWAP.U(1,2)@3 ; SWAP.U(0',0)@0 ; SWAP.U(0',1')@1 ; SWAP(0',2)@2" 4 0.05
