"""Tutorial of Book 6, chapter 13: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_credit as m
from firm_cdscurve import par_spread


def test_every_quote_reprices_and_forward_hazards_rise():
    c = m.curve()
    for T, s in zip(m.TENORS, m.SPREADS, strict=True):
        assert abs(par_spread(c, m.DISC, T, m.R) - s) < 1e-10
    assert all(b > a for a, b in zip(c.hazards, c.hazards[1:], strict=False))


def test_cs01_sits_on_the_position_maturity():
    cs = m.protection_position()["cs01"]
    assert cs[3] > 100 * max(abs(x) for i, x in enumerate(cs) if i != 3)
