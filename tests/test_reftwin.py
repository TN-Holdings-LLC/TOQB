"""toqb.reftwin, the reference twin: the Target-only noise model equals Aer's own from_backend path, outputs are
prediction artifacts that toqb.predscore accepts, and a hash mismatch stops it. Needs qiskit, qiskit-aer and
qiskit-ibm-runtime (skipped without them)."""
import hashlib
import json
import os
import pickle
import tempfile

import pytest

pytest.importorskip("qiskit_aer")
pytest.importorskip("qiskit_ibm_runtime")

from toqb import reftwin as RT  # noqa: E402


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _job(d, backend):
    """A small job folder in the s2rc_device layout: 2 cells x 3 points on a fake backend."""
    from qiskit import QuantumCircuit, qpy, transpile
    target = backend.target
    fetch = os.path.join(d, "fetch")
    os.makedirs(fetch)
    with open(os.path.join(fetch, "target.pkl"), "wb") as f:
        pickle.dump(target, f)
    circs, pubs, cells = [], [], []
    for cell in range(2):
        labels = [1, -1, 1]
        for i in range(3):
            qc = QuantumCircuit(2, 2)
            qc.ry(0.4 + 0.9 * i + 0.3 * cell, 0)
            qc.cx(0, 1)
            qc.measure([0, 1], [0, 1])
            circs.append(transpile(qc, target=target, optimization_level=1, seed_transpiler=1))
            pubs.append(dict(cell=cell, point=i))
        cells.append(dict(cell=cell, name=f"c{cell}", arm="qiskit:1", seed=1, layers=1, points=3,
                          run_sha256=str(cell) * 64, labels=labels, twin_p1=[0.3, 0.6, 0.4]))
    job = os.path.join(d, "job")
    os.makedirs(job)
    with open(os.path.join(job, "circuits.qpy"), "wb") as f:
        qpy.dump(circs, f)
    man = dict(written="2026-10-20T08:00:00+00:00 (x)", shots=100, qpy_sha256=_sha(os.path.join(job, "circuits.qpy")),
               fetch=dict(backend=backend.name, target_sha256=_sha(os.path.join(fetch, "target.pkl"))),
               cells=cells, pubs=pubs)
    with open(os.path.join(job, "manifest.json"), "w") as f:
        json.dump(man, f)
    return job, fetch, circs


def test_target_only_noise_model_equals_aer_from_backend():
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2
    be = FakeManilaV2()
    with tempfile.TemporaryDirectory() as d:
        job, fetch, circs = _job(d, be)
        out = os.path.join(d, "ref")
        s = RT.run(job, fetch, out, shots=400, threads=1)
        ref = AerSimulator.from_backend(be, max_parallel_threads=1)
        assert RT.noise_model(be.target) == ref.options.noise_model
        # the same model; Aer's from_backend simulator also sets other options, so its random stream differs: the
        # estimates agree within shot noise (5 standard errors of the difference)
        for i, c in enumerate(circs):
            want = RT.p1_clbit0(ref.run(c, shots=400, seed_simulator=RT.SEED0 + i).result().get_counts(0))
            cell, point = divmod(i, 3)
            got = json.load(open(os.path.join(out, f"ref_cell{cell}.json")))["points"][point]["p1"]
            p = (got + want) / 2
            assert abs(got - want) <= 5 * (2 * max(p * (1 - p), 1e-3) / 400) ** 0.5
        assert s["points"] == 6 and set(s["cells"]) == {"0", "1"}
        for k, v in s["cells"].items():
            assert _sha(os.path.join(out, v["file"])) == v["sha256"]


def test_outputs_score_as_a_reference():
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2
    from toqb import predscore as PS
    with tempfile.TemporaryDirectory() as d:
        job, fetch, _ = _job(d, FakeManilaV2())
        out = os.path.join(d, "ref")
        RT.run(job, fetch, out, shots=200, threads=1)
        pred = json.load(open(os.path.join(out, "ref_cell0.json")))
        PS._check_pred(pred)  # a valid toqb-pred/0 with both classes
        assert pred["twin"]["traj"] == 200 and len(pred["points"]) == 3


def test_hash_mismatch_and_existing_output_stop():
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2
    with tempfile.TemporaryDirectory() as d:
        job, fetch, _ = _job(d, FakeManilaV2())
        out = os.path.join(d, "ref")
        os.makedirs(out)
        with pytest.raises(RT.Stop):
            RT.run(job, fetch, out, shots=10)
        with open(os.path.join(fetch, "target.pkl"), "ab") as f:
            f.write(b"x")
        with pytest.raises(RT.Stop):
            RT.run(job, fetch, os.path.join(d, "ref2"), shots=10)


def test_first_k_takes_both_classes():
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2
    with tempfile.TemporaryDirectory() as d:
        job, fetch, _ = _job(d, FakeManilaV2())
        out = os.path.join(d, "ref")
        RT.run(job, fetch, out, shots=50, threads=1, first=2)
        pred = json.load(open(os.path.join(out, "ref_cell0.json")))
        assert sorted(p["label"] for p in pred["points"]) == [-1, 1]
