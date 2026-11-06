"""The combined 3D device-test job: arms and depths kept apart by record name, acceptance passed, answers only in
the answers file, and a noiseless local run reads floor = mirror = 1 for every arm (Clifford point, dry run)."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEV = os.path.join(ROOT, "results/daily/2026-11-05/ibm_fez/dev")


@pytest.mark.skipif(not os.path.isdir(DEV), reason="needs the 11-05 fez record")
def test_combined_job_dry_run(tmp_path):
    out, ans = tmp_path / "job", tmp_path / "answers.json"
    subprocess.run([sys.executable, os.path.join(ROOT, "gpu/os3d_compare_build.py"), DEV, str(out), str(ans),
                    "--ts", "1", "--theta", "1.5707963267948966", "--dry-clifford-sentinel"], check=True,
                   cwd=ROOT, env=dict(os.environ))
    rep = json.load(open(out / "report.json"))
    assert rep["circuits"] == 10 and set(rep["arms"]) == {"g3d_t1", "sabre_t1"}
    assert rep["arms"]["g3d_t1"]["cz"] == 116 and all(all(a["checks"].values()) for a in rep["arms"].values())
    names = sorted(f[:-5] for f in os.listdir(out / "runs") if f.endswith(".json"))
    assert [n for n in names if n.startswith("p2d_")] == ["p2d_g3d_t1", "p2d_g3d_t1_floor", "p2d_g3d_t1_mirror",
                                                          "p2d_sabre_t1", "p2d_sabre_t1_floor", "p2d_sabre_t1_mirror"]
    assert "exact" not in open(out / "report.json").read()
    from psf_os import sim
    from psf_os import user2d as U
    sim.submit(rep["job"], "noiseless", seed=3)
    answers = json.load(open(ans))
    for tag in rep["arms"]:
        c = U.card(rep["job"], rep["runs"], answers[tag], tag=tag)
        assert abs(c["floor_mean"] - 1) < 1e-9 and abs(c["mirror_mean"] - 1) < 1e-9
