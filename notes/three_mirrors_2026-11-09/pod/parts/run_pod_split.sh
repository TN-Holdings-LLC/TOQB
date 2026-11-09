#!/bin/bash
# run_pod.sh split over several pods: the same setup and the same command, with --layouts and --ts given (seeds depend
# only on the chunk index, so the rows are the same as in one run over the whole range).
# usage: bash run_pod_split.sh LAYOUTS TS OUT_STEM
set -e
git clone -q psfos_full_0fb4512.bundle psf-os && git -C psf-os checkout -q -b main origin/main
git -C psf-os log --oneline -1
pip install -q "qiskit==2.6.1" "qiskit-aer==0.18.2" numpy scipy
python -c "import qiskit, qiskit_aer; print('qiskit', qiskit.__version__, 'aer', qiskit_aer.__version__)"
nproc
PYTHONPATH=psf-os:. python pod_three_mirrors.py dev $3.json \
    --layouts $1 --ts $2 --zetas 0,0.005,0.01,0.02 --traj 2000 --chunk 100 --procs $(nproc) \
    2>&1 | grep -v -i deprec | tee $3.txt
