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


def _cut_target(every=6, at=2):
    """The snapshot device with every coupler (q, q + 1), q % every == at, reported failed (error 0.7): the snake's
    pieces are too short for a 10-ring, so the Python would place it by VF2's search."""
    import copy
    from qiskit.transpiler import InstructionProperties
    from toqb.devices import get_device
    t = copy.deepcopy(get_device("snapshot:marrakesh").target)
    for qa in list(t["cz"]):
        if qa is None:
            continue
        a, b = sorted(qa)
        if b == a + 1 and a % every == at:
            p = t["cz"][qa]
            t.update_instruction_properties("cz", qa, InstructionProperties(duration=p.duration, error=0.7))
    return t


def test_search_placement_is_out_of_scope(monkeypatch):
    """Owner, 2026-10-21 (formula only): where the Python would place the ring by VF2's search, the Rust builder stops
    with OutOfScope and the arm does not fall back to the Python."""
    t = _cut_target()
    qc = _model(10, 2, 0)
    a = TL.make_loop_arm("psfai:template")
    a.setup(t)
    assert type(a.ai.model_template(qc, t)).__name__ == "RingTemplate"  # the Python would search and build
    with pytest.raises(RP.OutOfScope):
        RP.ring_template(qc, t, a.ai)
    for mode in ("1", "check"):
        monkeypatch.setenv("TOQB_RUST_TEMPLATE", mode)
        b = TL.make_loop_arm("psfai:template")
        b.setup(t)
        with pytest.raises(RP.OutOfScope):
            b.compile_circuit(qc)


def test_choose_takes_the_first_eligible(tmp_path, monkeypatch, capsys):
    """s2rc_device choose: the fixed order, E5 applied; a device whose PSF placement would need a search is passed
    over, the next eligible one is chosen, and choice.json records why."""
    import argparse
    import json
    import pickle
    from toqb import s2rc_device as SD
    from toqb.devices import get_device
    monkeypatch.setenv("TOQB_RUST_TEMPLATE", "check")
    folders = []
    for name, tg in (("cut", _cut_target()), ("whole", get_device("snapshot:marrakesh").target)):
        d = tmp_path / name
        d.mkdir()
        with open(d / "target.pkl", "wb") as f:
            pickle.dump(tg, f)
        json.dump(dict(backend=f"test_{name}", calibration_time="2026-10-21T00:00:00+00:00", operational=True,
                       two_qubit_gate="cz", num_qubits=tg.num_qubits,
                       target_sha256=SD.sha256_file(str(d / "target.pkl"))), open(d / "fetch.json", "w"))
        folders.append(str(d))
    out = tmp_path / "choice.json"
    SD.cmd_choose(argparse.Namespace(fetches=folders, out=str(out), arms=["psfai:template"], layers=[2], n=10,
                                     enc=1.5707963267948966, seed=1))
    ch = json.load(open(out))
    assert ch["chosen"]["backend"] == "test_whole"
    assert not ch["devices"][0]["eligible"] and "E4/E5" in ch["devices"][0]["reasons"][0]
    printed = capsys.readouterr().out
    assert "OUT OF SCOPE (E5)" in printed and printed.strip().splitlines()[-1].startswith("CHOSEN ")
    with pytest.raises(SystemExit):  # never overwritten
        SD.cmd_choose(argparse.Namespace(fetches=folders, out=str(out), arms=["psfai:template"], layers=[2], n=10,
                                         enc=1.5707963267948966, seed=1))


def _broken_snake(tg):
    """FakeTorino with failed couplers (seeded) so that no snake piece holds 14 qubits."""
    import copy
    import random
    from qiskit.transpiler import InstructionProperties
    t = copy.deepcopy(tg)
    r = random.Random(0)
    qs = r.sample(range(t.num_qubits), 6)
    for q in qs[:3]:
        p = t["sx"][(q,)]
        t.update_instruction_properties("sx", (q,), InstructionProperties(duration=p.duration, error=0.6))
    cz = [qa for qa in t["cz"] if qa is not None]
    for qa in r.sample(cz, 6):
        p = t["cz"][qa]
        t.update_instruction_properties("cz", qa, InstructionProperties(duration=p.duration,
                                                                        error=1.0 if r.random() < 0.3 else 0.7))
    return t


def test_second_snake_is_used(monkeypatch):
    """Owner, 2026-10-22 (E5's scope): where the snake on the couplers of the most common gate length does not hold the
    ring but the snake on every working coupler does, the Rust builder places it there (formula, no search)."""
    pytest.importorskip("qiskit_ibm_runtime")
    from toqb.devices import get_device
    tg = _broken_snake(get_device("fake:FakeTorino").target)
    qc = _model(14, 6, 1406)
    a = TL.make_loop_arm("psfai:template")
    a.setup(tg)
    pc = a.pc
    K, kadj, fadj, snake = pc._chain_lattice(tg, 0.5)
    assert pc._chain_place(14, K, fadj, snake)[1] != "snake"
    line, how = pc._chain_place(14, K, kadj, snake)
    assert how == "snake"
    t = RP.ring_template(qc, tg, a.ai)
    assert sorted(t.layout) == sorted(line)


def _broken_both(tg):
    """FakeTorino with failed couplers (seeded) so that neither snake holds 14 qubits while VF2 still finds a path."""
    import copy
    import random
    from qiskit.transpiler import InstructionProperties
    from toqb import task_loop as TL_
    a = TL_.make_loop_arm("psfai:template")
    a.setup(tg)
    pc = a.pc
    cz = sorted(qa for qa in tg["cz"] if qa is not None)
    for seed in range(200):
        t = copy.deepcopy(tg)
        r = random.Random(seed)
        for qa in r.sample(cz, 14):
            p = t["cz"][qa]
            t.update_instruction_properties("cz", qa, InstructionProperties(duration=p.duration, error=0.7))
        lat = pc._chain_lattice(t, 0.5)
        if lat is None:
            continue
        K, kadj, fadj, snake = lat
        hf = pc._chain_place(14, K, fadj, snake)[1]
        hk = pc._chain_place(14, K, kadj, snake)[1]
        if hf == "vf2_path" and hk != "snake":
            return t
    raise AssertionError("no seed gives a device where only VF2 places 14 qubits")


def test_vf2_placement_is_out_of_scope(monkeypatch):
    """Owner, 2026-10-21 (formula only; scope 2026-10-22): where neither snake holds the ring and the Python would
    place it by VF2's search, the Rust builder stops with OutOfScope and the arm does not fall back to the Python."""
    pytest.importorskip("qiskit_ibm_runtime")
    from toqb.devices import get_device
    tg = _broken_both(get_device("fake:FakeTorino").target)
    qc = _model(14, 6, 1406)
    a = TL.make_loop_arm("psfai:template")
    a.setup(tg)
    assert type(a.ai.model_template(qc, tg)).__name__ == "RingTemplate"  # the Python finds one by VF2
    with pytest.raises(RP.OutOfScope):
        RP.ring_template(qc, tg, a.ai)
    for mode in ("1", "check"):
        monkeypatch.setenv("TOQB_RUST_TEMPLATE", mode)
        b = TL.make_loop_arm("psfai:template")
        b.setup(tg)
        with pytest.raises(RP.OutOfScope):
            b.compile_circuit(qc)
