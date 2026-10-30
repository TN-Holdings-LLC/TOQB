"""toqb.qelm_device (2026-10-30): the device path of QELM task A builds one assemble-ready job per arm from a teacher
task, passes rule G, and scores local (fake-device) counts by the declared rules."""
import json
import os
import subprocess
import sys

import pytest

pytest.importorskip("qiskit")


def test_end_to_end_on_a_fake_device(tmp_path):
    pytest.importorskip("qiskit_aer")
    pytest.importorskip("qiskit_ibm_runtime")
    from toqb import qelm as Q
    env = dict(os.environ, PYTHONWARNINGS="ignore")
    py = sys.executable
    T = str(tmp_path / "task")
    Q.write_teacher(T, n=8, L=3)
    Q.predict(T, {"fold:rule": 56.5, "fold:zipcyc": 15.1}, reps=20)
    F = str(tmp_path / "fetch")

    def run(*args):
        r = subprocess.run([py, "-m", *args], capture_output=True, text=True, env=env, cwd=os.getcwd())
        assert r.returncode == 0, r.stdout + r.stderr
        return r.stdout
    run("toqb.s2rc_device", "fetch", "--fake", "FakeFez", "--out", F)
    jobs = []
    for arm in ("fold:rule", "fold:zipcyc"):
        R, J = str(tmp_path / f"runs_{arm[5:]}"), str(tmp_path / f"job_{arm[5:]}")
        out = run("toqb.qelm_device", "build", F, T, R, "--arm", arm, "--points", "4")
        assert "rule G PASS" in out
        run("toqb.s2rc_device", "assemble", "--fetch", F, "--runs", R, "--out", J, "--max-seconds", "60")
        run("toqb.s2rc_device", "submit", "--job", J, "--local")
        jobs += ["--job", f"{arm}={J}:{R}"]
    out = run("toqb.qelm_device", "score", T, str(tmp_path / "score"), *jobs, "--predict", os.path.join(T, "predict.json"),
              "--points", "4")
    res = json.load(open(tmp_path / "score" / "qelm_device_score.json"))
    assert set(res["arms"]) == {"fold:rule", "fold:zipcyc"} and "Q3a" in res
    for ar in res["arms"].values():
        assert ar["Q1"] in ("HOLDS", "FAILS") and ar["Q2"]["verdict"] in ("INSIDE", "OUTSIDE")
