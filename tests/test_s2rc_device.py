"""Scoring helpers of toqb.s2rc_device: the same CE as toqb.s2r2, Holm, clbit 0 from counts, the time model."""
import numpy as np

from toqb import s2rc_device as D


def test_ce_matches_s2r2():
    from toqb import s2r2 as S2
    rng = np.random.default_rng(1)
    for _ in range(5):
        z = rng.uniform(-1, 1, 300)
        z[:3] = [1.0, -1.0, 0.0]
        y = rng.choice([-1, 1], 300)
        assert abs(D.ce(z, y) - S2._ce(z, y)) < 1e-12


def test_holm():
    assert D.holm([0.01, 0.04, 0.03, 0.005]) == [0.03, 0.06, 0.06, 0.02]
    assert D.holm([0.9]) == [0.9]


def test_p1_of_counts_reads_clbit_0_rightmost():
    assert D.p1_of_counts({"0001": 30, "0000": 70}) == 0.3
    assert D.p1_of_counts({"1 0": 5, "0 1": 15}) == 0.75


def test_acc_half_counts_ties_half():
    assert D.acc_half([0.2, -0.1, 0.0], [1, 1, 1]) == (1 + 0 + 0.5) / 3


def test_time_model_matches_billed_jobs():
    # 2026-10-13, ibm_marrakesh: 60 circuits x 6,000 shots billed 102 s; 81 circuits, 198,000 shots billed 56 s
    assert abs(60 * D.PER_CIRCUIT_S + 360000 * D.PER_SHOT_S - 102) < 4
    assert abs(81 * D.PER_CIRCUIT_S + 198000 * D.PER_SHOT_S - 56) < 2
    assert abs(D.qpu_seconds(1300, 250) - (1300 * 0.036 + 1300 * 250 * 0.00027 + 3.0)) < 1e-9


def test_update_summary():
    from toqb.s2rc_device import update_summary
    r = update_summary(["2026-10-19T02:00:00+00:00", "2026-10-19T02:00:00+00:00", None,
                        "2026-10-20T04:00:00+02:00", "2026-10-18T03:30:00+00:00"])
    assert r["updates"] == ["2026-10-18T03:30:00+00:00", "2026-10-19T02:00:00+00:00", "2026-10-20T02:00:00+00:00"]
    assert r["gaps_h"] == [22.5, 24.0] and r["min_gap_h"] == 22.5 and r["utc_hour"] == [3.5, 2.0, 2.0]
