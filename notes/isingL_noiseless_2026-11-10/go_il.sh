#!/bin/bash
# isingL 4x3x2 noiseless check on the pod: venv (the image's Python refuses pip, PEP 668), then noiseless.py as given.
cd /root/il
TZ=Europe/Zurich date
python3 -m venv /root/venv && export PATH=/root/venv/bin:$PATH
pip install -q qiskit qiskit-aer numpy
python -c "import qiskit, qiskit_aer, numpy; print('qiskit', qiskit.__version__, 'aer', qiskit_aer.__version__, 'numpy', numpy.__version__)"
nproc
cat /sys/fs/cgroup/memory.max 2>/dev/null
sha256sum IL/job/circuits.qpy
python noiseless.py IL/job --max-qubits 30 --workers 32
echo EXIT $?
TZ=Europe/Zurich date
