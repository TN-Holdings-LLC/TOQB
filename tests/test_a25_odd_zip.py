"""The a25 switch (2026-10-25): TOQB's psfai:template_zip arm on the default front end (a25) builds the zipper for odd
n: (5n - 7)/2 CZ per layer, and the compiled circuit gives the logical model's P(1) on clbit 0 (statevector). Needs
PSF-Zero with rust/psfbind ring r3 built (skipped without)."""
import json
import os
import subprocess
import sys

import pytest

pytest.importorskip("qiskit")
if not os.environ.get("PSF_ZERO_REPO"):
    pytest.skip("needs PSF_ZERO_REPO", allow_module_level=True)
LIB = os.path.join(os.environ["PSF_ZERO_REPO"], "rust", "psfbind", "target", "release", "libpsfbind.so")
if not os.path.exists(LIB):
    pytest.skip("needs rust/psfbind built", allow_module_level=True)

SCRIPT = r'''
import json, sys
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from toqb import s2r as S
from toqb import task_loop as TL
from toqb.devices import get_device


def p1(c):
    """P(clbit 0 = 1), the circuit compacted to its active qubits, measurements read from the final statevector."""
    act = sorted({c.find_bit(q).index for i in c.data for q in i.qubits if i.operation.name not in ("barrier", "delay")})
    idx = {q: k for k, q in enumerate(act)}
    s, meas = QuantumCircuit(len(act)), None
    for i in c.data:
        nm = i.operation.name
        if nm in ("barrier", "delay"):
            continue
        if nm == "measure":
            if c.find_bit(i.clbits[0]).index == 0:
                meas = idx[c.find_bit(i.qubits[0]).index]
            continue
        s.append(i.operation, [idx[c.find_bit(q).index] for q in i.qubits])
    return float(Statevector(s).probabilities([meas])[1])


arm = S.Arm("psfai:template_zip", get_device("snapshot:marrakesh"))
rng = np.random.default_rng(20261025)
out = []
for n in (5, 7, 9, 11):
    for L in (2, 4):
        qc = TL.model_circuit(TL.angle_list(rng.uniform(-1, 1, TL.n_params(n, L)), rng.uniform(-1, 1, n), n, L,
                                            np.pi / 2), n, L)
        c = arm.compile(qc)
        q2 = sum(1 for i in c.data if len(i.qubits) == 2)
        out.append(dict(n=n, L=L, q2=q2, want=L * (5 * n - 7) // 2, p_c=p1(c), p_l=p1(qc),
                        version=arm.version()))
json.dump(out, open(sys.argv[1], "w"))
'''


def test_odd_zipper_through_the_arm(tmp_path):
    out = tmp_path / "odd.json"
    env = dict(os.environ)
    env.pop("PSF_AI_FILE", None)  # the arm's default front end (a25 since 2026-10-25)
    env.pop("PSF_RING_ZIP", None)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, "-c", SCRIPT, str(out)], check=True, capture_output=True, cwd=root,
                   env=dict(env, PYTHONPATH=root))
    rows = json.load(open(out))
    assert len(rows) == 8
    for r in rows:
        assert r["q2"] == r["want"], r
        assert abs(r["p_c"] - r["p_l"]) < 1e-9, r
