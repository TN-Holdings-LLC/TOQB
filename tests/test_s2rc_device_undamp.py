"""toqb.s2rc_device_undamp: fix writes (lam, delta) and the undamped prediction per cell, bound to the manifest's hash
and never overwritten; score reads the device's counts and agrees with the raw CE of toqb.s2rc_device's formula."""
import argparse
import hashlib
import json
import os

import numpy as np
import pytest

from toqb import s2rc_device_undamp as D


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _job(tmp):
    rng = np.random.default_rng(4)
    runs, job = os.path.join(tmp, "runs"), os.path.join(tmp, "job")
    os.makedirs(runs)
    os.makedirs(job)
    cells, pubs = [], []
    for cid, name in enumerate(["L8_s301-psfai_template", "L8_s301-qiskit_2_target_template"]):
        y = [1, -1] * 10
        rec = dict(plan="p", device="file:x", task={"n": 10, "layers": 8}, train={}, standin={}, arm="a",
                   predict={"seed": 50301, "reps": 200, "level": 0.99, "traj": 64}, final_mean=[0.0] * 170)
        rf = os.path.join(runs, name + ".json")
        json.dump(rec, open(rf, "w"))
        p1 = list(np.clip(0.5 - 0.15 * np.array(y) + rng.normal(0, 0.02, 20), 0.01, 0.99))
        cells.append(dict(cell=cid, name=name, arm="a", layers=8, points=20, run_sha256=_sha(rf), labels=y,
                          twin_p1=p1))
        pubs += [dict(cell=cid, point=i) for i in range(20)]
    json.dump(dict(shots=250, cells=cells, pubs=pubs), open(os.path.join(job, "manifest.json"), "w"))
    return runs, job


def test_fix_then_score(tmp_path, monkeypatch):
    runs, job = _job(str(tmp_path))
    from toqb import s2r2 as S2
    monkeypatch.setattr(S2, "Runner", lambda plan, arm: None)
    monkeypatch.setattr(S2, "teacher_data2", lambda task: (np.zeros((64, 10)), None, None, None))
    D.cmd_fix(argparse.Namespace(runs=runs, job=job, traj=8), estimate=lambda *a: (0.4, 0.05, 0.01))
    und = json.load(open(os.path.join(job, "undamp.json")))
    assert und["manifest_sha256"] == _sha(os.path.join(job, "manifest.json")) and len(und["cells"]) == 2
    with pytest.raises(SystemExit):
        D.cmd_fix(argparse.Namespace(runs=runs, job=job, traj=8), estimate=lambda *a: (0.4, 0.05, 0.01))
    man = json.load(open(os.path.join(job, "manifest.json")))
    rows = []
    for i, pub in enumerate(man["pubs"]):
        p = man["cells"][pub["cell"]]["twin_p1"][pub["point"]]
        k = int(round(p * 250))
        rows.append(dict(pub=i, counts={"1": k, "0": 250 - k}))
    json.dump(dict(job_id="local", rows=rows), open(os.path.join(job, "raw_counts.json"), "w"))
    D.cmd_score(argparse.Namespace(job=job))
    sc = json.load(open(os.path.join(job, "undamp_score.json")))
    from toqb.s2rc_device import ce
    c0 = sc["cells"][0]
    ph = np.array([r["counts"]["1"] / 250 for r in rows[:20]])
    assert abs(c0["ce_raw"] - ce(1 - 2 * ph, np.array(man["cells"][0]["labels"]))) < 1e-12
    assert c0["ce_undamped"] < c0["ce_raw"]  # a shrunk but right answer gains


def test_score_refuses_another_manifest(tmp_path, monkeypatch):
    runs, job = _job(str(tmp_path))
    from toqb import s2r2 as S2
    monkeypatch.setattr(S2, "Runner", lambda plan, arm: None)
    monkeypatch.setattr(S2, "teacher_data2", lambda task: (np.zeros((64, 10)), None, None, None))
    D.cmd_fix(argparse.Namespace(runs=runs, job=job, traj=8), estimate=lambda *a: (0.4, 0.05, 0.01))
    with open(os.path.join(job, "manifest.json"), "a") as f:
        f.write(" ")
    with pytest.raises(SystemExit):
        D.cmd_score(argparse.Namespace(job=job))


def test_snapshot_fetch_folder(tmp_path):
    """s2rc_device snapshot (C r9 item 7): a fetch folder from the published calibration, hashed, never overwritten."""
    pytest.importorskip("qiskit")
    from toqb import s2rc_device as SD
    out = str(tmp_path / "snap")
    SD.cmd_snapshot(argparse.Namespace(out=out))
    fj = json.load(open(os.path.join(out, "fetch.json")))
    assert fj["backend"] == "ibm_marrakesh" and fj["source"].startswith("snapshot") and not fj["fake"]
    assert fj["target_sha256"] == _sha(os.path.join(out, "target.pkl"))
    assert fj["calibration_time"].startswith("2026-10-13")
    with pytest.raises(SystemExit):
        SD.cmd_snapshot(argparse.Namespace(out=out))


class _FakeBackend:
    def __init__(self, name, target, operational=True):
        self.name, self.target, self._op = name, target, operational

    def status(self):
        return type("S", (), {"operational": self._op})()


def test_pick_backend_moves_on_in_the_fixed_order(monkeypatch):
    """C r9 item 8 (owner, 2026-10-22): a failed element under the job on the first device sends the same circuits to
    the next device in the fixed order; everything tried is recorded; none eligible gives None."""
    pytest.importorskip("qiskit")
    import copy
    from qiskit import QuantumCircuit
    from qiskit.transpiler import InstructionProperties
    from toqb import s2rc_device as SD
    from toqb.devices import get_device
    good = get_device("snapshot:marrakesh").target
    bad = copy.deepcopy(good)
    p = bad["cz"][(0, 1)] if (0, 1) in bad["cz"] else None
    qa = (0, 1) if p is not None else (1, 0)
    p = bad["cz"][qa]
    bad.update_instruction_properties("cz", qa, InstructionProperties(duration=p.duration, error=0.9))
    qc = QuantumCircuit(good.num_qubits, 1)
    qc.cz(*qa)
    qc.measure(0, 0)
    monkeypatch.setattr(SD, "calibration_time", lambda b: f"cal-{b.name}")
    backs = {"ibm_marrakesh": _FakeBackend("ibm_marrakesh", bad), "ibm_fez": _FakeBackend("ibm_fez", good),
             "ibm_kingston": _FakeBackend("ibm_kingston", good)}
    b, cal, tried = SD.pick_backend([qc], backs.__getitem__, "ibm_marrakesh")
    assert b.name == "ibm_fez" and cal == "cal-ibm_fez"
    assert [t["backend"] for t in tried] == ["ibm_marrakesh", "ibm_fez"] and tried[0]["reasons"]
    backs["ibm_fez"] = _FakeBackend("ibm_fez", good, operational=False)
    b, _, tried = SD.pick_backend([qc], backs.__getitem__, "ibm_marrakesh")
    assert b.name == "ibm_kingston" and len(tried) == 3
    backs["ibm_kingston"] = _FakeBackend("ibm_kingston", bad)
    b, _, tried = SD.pick_backend([qc], backs.__getitem__, "ibm_marrakesh")
    assert b is None and len(tried) == 3
