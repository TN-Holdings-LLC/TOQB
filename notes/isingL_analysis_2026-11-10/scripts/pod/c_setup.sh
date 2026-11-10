nproc; free -g | sed -n 2p; python3 --version
sha256sum /workspace/ckit.zip
pip install "qiskit==2.5.2" "qiskit-aer==0.17.2" "qiskit-ibm-runtime==0.49.0" numpy 2>&1 | tail -n 1
python3 -c "import qiskit, qiskit_aer, qiskit_ibm_runtime; print('qiskit', qiskit.__version__, 'aer', qiskit_aer.__version__, 'runtime', qiskit_ibm_runtime.__version__)"
cd /workspace && python3 -m zipfile -e ckit.zip . && ls ckit ckit/inputs
cat /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.max 2>/dev/null
