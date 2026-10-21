"""toqb.match_score_undamp on synthetic records: a shrunk but right model gains from undamping (A: WIN), equal arms tie,
a missing undamp output or a shot mismatch stops."""
import json
import os

import numpy as np
import pytest

pytest.importorskip("scipy")

from toqb import match_score_undamp as M


def _write(d, name, arm, teacher, angle, z_ideal, lam, delta, y, reproduced=True):
    p1 = (1 - (lam * z_ideal + delta)) / 2
    rec = dict(kind="s2rc", valid=True, arm=arm, train={"init": 0.0}, test_labels=[int(v) for v in y],
               task={"teacher_seed": teacher, "teacher_angle": angle, "layers": 8},
               rehearsal={"standin_p1": [float(v) for v in p1], "ce": 0.6, "ce_inside": True})
    os.makedirs(os.path.join(d, "runs"), exist_ok=True)
    os.makedirs(os.path.join(d, "und"), exist_ok=True)
    json.dump(rec, open(os.path.join(d, "runs", name), "w"))
    und = dict(points=[dict(lam=lam, delta=delta, raw={"reproduced": reproduced, "inside": True},
                            undamped={"inside": True})])
    json.dump(und, open(os.path.join(d, "und", name), "w"))


def _tasks(d, reproduced=True):
    rng = np.random.default_rng(3)
    for teacher in (13, 14, 15):
        y = np.where(rng.uniform(size=500) > 0.5, 1, -1)
        z = y * rng.uniform(0.3, 0.9, 500) * np.where(rng.uniform(size=500) < 0.85, 1, -1)
        _write(d, f"psf_{teacher}.json", "psfai:template", teacher, 1.0, z, 0.4, 0.05, y, reproduced)
        _write(d, f"qk_{teacher}.json", "qiskit:2:target:template", teacher, 1.0, z, 0.6, 0.07, y)


def test_undamping_a_shrunk_right_model_wins(tmp_path):
    _tasks(str(tmp_path))
    res = M.score(M.load(str(tmp_path / "runs"), str(tmp_path / "und")))
    assert res["comparisons"]["A"]["groups"][0]["verdict"] == "WIN"
    assert res["comparisons"]["D"]["groups"][0]["verdict"] == "WIN"
    # the same model undamped on both arms: the same answers, a tie
    assert res["comparisons"]["C"]["groups"][0]["verdict"] == "TIE"
    assert "PSF undamped" in M.markdown(res)
    # the headline needs B and C: C is a tie here, so the group is not won
    assert res["headline"]["won"] == 0 and res["headline"]["groups"][0]["B"] == "WIN"


def test_shot_mismatch_and_missing_output_stop(tmp_path):
    _tasks(str(tmp_path), reproduced=False)
    with pytest.raises(M.Stop):
        M.load(str(tmp_path / "runs"), str(tmp_path / "und"))
    os.remove(str(tmp_path / "und" / "qk_13.json"))
    with pytest.raises(M.Stop):
        M.load(str(tmp_path / "runs"), str(tmp_path / "und"))
