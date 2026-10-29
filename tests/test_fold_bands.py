"""Tests of the ring extension (2026-10-30): bands over three or more row pairs in toqb.fold."""
import pytest

from toqb import fold
from toqb.devices import get_device

MAPS = ("fake:FakeMarrakesh", "fake:FakeFez", "snapshot:marrakesh", "file:data/targets/ibm_kingston_2026-10-24.pkl")


def _target(spec):
    return get_device(spec).target


def test_every_band_is_one_cycle_on_real_couplers():
    t = _target("fake:FakeMarrakesh")
    geo = {tuple(sorted(qa)) for qa in t["cz"] if qa is not None}
    bands = fold.band_shapes(fold._all_pairs(t))
    assert len(bands) > 1000
    for length, name, cyc in bands:
        assert name[0] == "band" and name[2] >= 3
        assert len(cyc) == length == len(set(cyc))
        assert all(tuple(sorted((cyc[i], cyc[(i + 1) % length]))) in geo for i in range(length))


def test_band_order_is_fixed_and_top_down():
    t = _target("fake:FakeMarrakesh")
    a = fold.band_shapes(fold._all_pairs(t))
    b = fold.band_shapes(fold._all_pairs(t))
    assert [x[1] for x in a] == [x[1] for x in b]
    firsts = [x[1][1] for x in a]
    assert firsts == sorted(firsts)


@pytest.mark.parametrize("spec", MAPS)
def test_placements_up_to_36_are_unchanged(spec, monkeypatch):
    """fold_place and pend_place for n <= 36 equal what they were with `shapes` alone (refusals included)."""
    t = _target(spec)
    new = {n: (fold.fold_place(t, n), fold.pend_place(t, n)) for n in range(4, 37)}
    monkeypatch.setattr(fold, "shapes_for", lambda pairs, n, pairs_all=None: fold.shapes(pairs))
    old = {n: (fold.fold_place(t, n), fold.pend_place(t, n)) for n in range(4, 37)}
    assert new == old


@pytest.mark.parametrize("spec", ("snapshot:marrakesh", "file:data/targets/ibm_kingston_2026-10-24.pkl"))
def test_n40_and_n60_place_on_working_elements(spec):
    t = _target(spec)
    def bad(nm, qa):
        p = t[nm].get(qa) if nm in t.operation_names else None
        return p is None or (p.error is not None and p.error >= 1)
    work = {tuple(sorted(qa)) for qa in t["cz"] if qa is not None and not bad("cz", qa)}
    for n in (40, 60):
        m, name, cyc = fold.fold_place(t, n)
        assert m == n and name[0] == "band"
        assert all(tuple(sorted((cyc[i], cyc[(i + 1) % m]))) in work for i in range(m))
        assert not any(bad("sx", (q,)) or bad("measure", (q,)) for q in cyc)
