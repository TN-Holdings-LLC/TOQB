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
