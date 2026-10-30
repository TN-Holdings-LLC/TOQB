"""toqb.s2rc_device submit options (2026-10-30 evening): the default stays off/off, and the names set real
SamplerV2 options (checked on the runtime's own options class, no IBM connection)."""
import pytest

from toqb import s2rc_device as SD


def test_default_is_the_standard():
    o = SD.sampler_options()
    assert o == {"dynamical_decoupling.enable": False, "twirling.enable_gates": False, "twirling.enable_measure": False}
    assert SD.options_text().startswith("dynamical decoupling off, twirling off")


@pytest.mark.parametrize("dd,twirl", [("XY4", "off"), ("off", "gates"), ("XpXm", "gates")])
def test_options_reach_the_sampler_options(dd, twirl):
    rt = pytest.importorskip("qiskit_ibm_runtime")
    so = rt.options.SamplerOptions()
    for k, v in SD.sampler_options(dd, twirl).items():
        obj = so
        for part in k.split(".")[:-1]:
            obj = getattr(obj, part)
        setattr(obj, k.split(".")[-1], v)
    assert so.dynamical_decoupling.enable == (dd != "off")
    assert so.twirling.enable_gates == (twirl == "gates") and so.twirling.enable_measure is False
    if dd != "off":
        assert so.dynamical_decoupling.sequence_type == dd


def test_unknown_option_is_refused():
    with pytest.raises(ValueError):
        SD.sampler_options("UR6", "off")
