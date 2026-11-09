#!/bin/bash
# On the POD (64 cores), from this folder. psf-os from the bundle at 0fb4512 (grid3d layout "line").
set -e
git clone -q psfos_full_0fb4512.bundle psf-os && git -C psf-os checkout -q -b main origin/main
git -C psf-os log --oneline -1
pip install -q "qiskit==2.6.1" "qiskit-aer==0.18.2" numpy scipy
python -c "import qiskit, qiskit_aer; print('qiskit', qiskit.__version__, 'aer', qiskit_aer.__version__)"
nproc
PYTHONPATH=psf-os:. python pod_three_mirrors.py dev three_mirrors_pod.json \
    --layouts line,fold --ts 1,2,3,4 --zetas 0,0.005,0.01,0.02 --traj 2000 --chunk 100 --procs $(nproc) \
    2>&1 | grep -v -i deprec | tee three_mirrors_pod.txt
