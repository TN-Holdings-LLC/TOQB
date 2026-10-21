"""toqb.ringport, the PSF ring template built in Rust: the same template as psf_ai_compile a22's `model_template` (gate
list, fixed angles, runs, layout, values' order, chosen schedule) for the S2R model at several depths on the snapshot
device, each schedule alone too; a ring that embeds is refused (the Python's compile template, not ported), and so is
a circuit that is not a ring. Needs PSF-Zero and its built rust/psfbind (skipped without)."""
import os

import numpy as np
import pytest

pytest.importorskip("qiskit")
if not os.environ.get("PSF_ZERO_REPO"):
    pytest.skip("needs PSF_ZERO_REPO", allow_module_level=True)

from toqb import ringport as RP  # noqa: E402
from toqb import rustbind as RB  # noqa: E402
from toqb import task_loop as TL  # noqa: E402

try:
    RB.cdll().psfbind_ring_template
except (RB.Unsupported, AttributeError) as exc:  # noqa: BLE001
    pytest.skip(f"psfbind without the ring builder: {exc}", allow_module_level=True)


@pytest.fixture(scope="module")
def arm():
    from toqb.devices import get_device
    a = TL.make_loop_arm("psfai:template")
    a.setup(get_device("snapshot:marrakesh").target)
    return a


def _model(n, L, seed):
    rng = np.random.default_rng(seed)
    th = rng.uniform(-np.pi, np.pi, TL.n_params(n, L))
    x = rng.uniform(-1, 1, n)
    return TL.model_circuit(TL.angle_list(th, x, n, L, 1.5707963267948966), n, L)


@pytest.mark.parametrize("L", [2, 8, 16])
def test_same_template_as_python(arm, L):
    qc = _model(10, L, L)
    py = arm.ai.model_template(qc, arm.target)
    rs = RP.ring_template(qc, arm.target, arm.ai)
    assert type(py).__name__ == "RingTemplate"
    assert RP.compare(py, rs) == []
    # the bound circuits agree too (the same closed form on the same runs)
    a, b = py.bind(qc), rs.bind(qc)
    assert [i.operation.name for i in a.data] == [i.operation.name for i in b.data]
    pa = [float(p) for i in a.data for p in i.operation.params]
    pb = [float(p) for i in b.data for p in i.operation.params]
    assert max(abs(u - v) for u, v in zip(pa, pb)) < 1e-12


@pytest.mark.parametrize("sched", ["n2", "q4"])
def test_each_schedule_alone(arm, sched):
    qc = _model(10, 8, 3)
    fn = arm.ai.ring_rounds_q4 if sched == "q4" else arm.ai.ring_rounds
    py = arm.ai._ring_template_one(qc, arm.target, rounds_fn=fn)
    rs = RP.ring_template(qc, arm.target, arm.ai, schedule=sched)
    assert RP.compare(py, rs) == []


def test_embedding_ring_is_refused(arm):
    qc = _model(12, 2, 1)  # heavy-hex has 12-cycles: a22 hands this to the compile template
    assert arm.ai._ring_embeds(qc, arm.target)
    with pytest.raises(RP.Refused):
        RP.ring_template(qc, arm.target, arm.ai)


def test_not_a_ring_is_refused(arm):
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(5, 5)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure(range(5), range(5))
    with pytest.raises(RP.Refused):
        RP.ring_template(qc, arm.target, arm.ai)


def test_arm_uses_rust_when_asked(monkeypatch):
    from toqb.devices import get_device
    qc = _model(10, 8, 9)
    tg = get_device("snapshot:marrakesh").target
    outs = {}
    for mode in ("", "1", "check"):
        monkeypatch.setenv("TOQB_RUST_TEMPLATE", mode)
        a = TL.make_loop_arm("psfai:template")
        a.setup(tg)
        outs[mode] = a.compile_circuit(qc)
        if mode:
            assert a.stats.get("rust_built") == 1 and "Rust" in a.version()
        if mode == "check":
            assert a.stats.get("rust_checked") == 1
    names = {m: [(i.operation.name, [o.find_bit(q).index for q in i.qubits]) for i in o.data]
             for m, o in outs.items()}
    assert names[""] == names["1"] == names["check"]
    pa = [float(p) for i in outs[""].data for p in i.operation.params]
    pb = [float(p) for i in outs["1"].data for p in i.operation.params]
    assert max(abs(u - v) for u, v in zip(pa, pb)) < 1e-12


def _strip_times(rec):
    if isinstance(rec, dict):
        return {k: _strip_times(v) for k, v in rec.items()
                if not (k.endswith("_s") or k in ("t", "times", "version", "wall", "started", "ended"))}
    if isinstance(rec, list):
        return [_strip_times(v) for v in rec]
    return rec


def test_device_style_run_and_qpy_unchanged(monkeypatch):
    """A device-style run (verify false, test circuits exported as QPY) with the template built in Rust (checked)
    equals the Python path's: the same record (times aside) and byte-identical QPY once Qiskit's automatic circuit names
    are set aside (assign_parameters appends a process-wide counter, which counts the circuits made before)."""
    import copy
    import io
    from qiskit import qpy
    from toqb import s2rc
    plan = {"name": "ringport device-style", "device": "snapshot:marrakesh", "verify": False,
            "task": {"n": 10, "layers": 2, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_angle": 1.0,
                     "teacher_gap": 0.2, "n_train": 8, "n_test": 12},
            "train": {"seed": 201, "init": 0.0, "pairs": 2, "sim_batch": 2, "sim_traj": 4, "h": 0.1, "lr": 0.4,
                      "loops": 4, "curve_every": 2, "curve_points": 6, "curve_traj": 4},
            "predict": {"traj": 16, "shots": 50, "reps": 50, "level": 0.99, "seed": 50001},
            "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}
    out = {}
    for mode in ("", "check"):
        monkeypatch.setenv("TOQB_RUST_TEMPLATE", mode)
        keep = {}
        rec = s2rc.run_s2rc(copy.deepcopy(plan), "psfai:template", keep)
        cs = [c.copy() for c in keep["circuits"]]
        for c in cs:
            c.name = "c"
        buf = io.BytesIO()
        qpy.dump(cs, buf)
        out[mode] = (rec, buf.getvalue())
    assert out[""][0]["valid"] and out["check"][0]["valid"]
    assert _strip_times(out[""][0]) == _strip_times(out["check"][0])
    assert out[""][1] == out["check"][1]
