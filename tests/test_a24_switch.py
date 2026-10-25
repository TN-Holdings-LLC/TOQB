"""The a24 switch (2026-10-24): with the default front end (a24; a25 since 2026-10-25, the same output for even n), TOQB's psfai:template and psfai:template_zip arms
compile the S2R model instruction for instruction as they did on a22 / c61 (toqb.zip_a24_check --via-arm). Needs
PSF-Zero with rust/psfbind built (skipped without)."""
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


@pytest.mark.parametrize("item31", [False, True])
def test_a24_arms_build_a22s_circuits(tmp_path, item31):
    out = tmp_path / "check.json"
    cmd = [sys.executable, "-m", "toqb.zip_a24_check", str(out), "--via-arm", "--n", "10", "12", "--L", "2", "8"]
    if item31:
        cmd.append("--item31")
    subprocess.run(cmd, check=True, capture_output=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    rows = json.load(open(out))
    assert len(rows) == 4
    assert all(r["identical"] for r in rows), rows
