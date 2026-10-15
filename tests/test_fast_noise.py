"""Tests of the fast engine (toqb.fast_noise) on Qiskit's arms, which need no PSF-Zero checkout."""
import numpy as np
import pytest

pytest.importorskip("qiskit_aer")

from toqb.check_fast_noise import _engine_rho, _reference_rho  # noqa: E402
from toqb.devices import get_device  # noqa: E402
from toqb.fast_noise import FastNoisyDevice, check_against_aer  # noqa: E402
from toqb.task_loop import Executor, angle_list, make_loop_arm, model_circuit, n_params, z_of_counts  # noqa: E402


def _setup(spec="qiskit:2:target:template", n=4, L=2, count=3, seed=0):
    dev = get_device("fake:FakeFez")
    arm = make_loop_arm(spec)
    arm.setup(dev.target)
    rng = np.random.default_rng(seed)
    qcs = [model_circuit(angle_list(rng.uniform(-3, 3, n_params(n, L)), rng.uniform(-1, 1, n), n, L, np.pi / 2), n, L)
           for _ in range(count)]
    return dev, arm, qcs


def test_exact_against_quantum_info_and_aer():
    dev, arm, qcs = _setup()
    fast = FastNoisyDevice(dev.target)
    outs = [arm.compile_circuit(q) for q in qcs]
    for c in outs:
        assert np.max(np.abs(_engine_rho(fast, c) - _reference_rho(fast, c))) < 1e-12
    _, p1 = check_against_aer(fast, outs)
    assert p1 < 1e-6
    assert np.max(np.abs(fast.p1_fast(outs) - fast.p1_of(outs))) < 1e-12


def test_structure_reused_and_counts():
    dev, arm, qcs = _setup(count=5)
    fast = FastNoisyDevice(dev.target)
    outs = [arm.compile_circuit(q) for q in qcs]
    counts = fast.counts(outs, 400, [1, 2, 3, 4, 5])
    assert all(sum(c.values()) == 400 for c in counts)
    assert len(getattr(fast, "_plans", {})) == 1  # one template structure, planned once
    p1 = fast.p1_fast(outs)
    z = np.array([z_of_counts(c) for c in counts])
    assert np.all(np.abs(z - (1 - 2 * p1)) < 0.3)  # 400 shots: within six standard deviations


def test_executor_fast_matches_slow_structure_checks():
    dev, arm, qcs = _setup(count=6)
    ex_f, ex_a = Executor(arm, dev, engine="fast"), Executor(arm, dev, engine="aer")
    ex_f.run(qcs, 100, list(range(6)), check_first=True)
    ex_a.run(qcs, 100, list(range(6)), check_first=True)
    assert ex_f.q2 == ex_a.q2 and ex_f.durations == ex_a.durations
    assert (ex_f.structural_fail, ex_f.on_failed_ops) == (ex_a.structural_fail, ex_a.on_failed_ops)
    assert ex_f.equivalence[0]["equivalent"] and ex_a.equivalence[0]["equivalent"]
