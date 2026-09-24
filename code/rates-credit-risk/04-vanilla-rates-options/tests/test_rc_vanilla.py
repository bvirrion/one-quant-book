"""Tutorial of Book 6, chapter 4: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_vanilla as m
from firm_capfloor import Cap, cap_price, piecewise


def test_strip_reprices_every_cap():
    f = piecewise(m.stripped())
    for n, v in zip(m.CAP_YEARS, m.CAP_VOLS, strict=True):
        c = Cap(m.SPOT, n, m.CAP_STRIKE)
        assert abs(cap_price(c, m.PROJ, m.DISC, f) - cap_price(c, m.PROJ, m.DISC, v)) < 1e-10


def test_smile_is_a_negative_skew():
    v = [b for _, b in m.smile_from_flat_normal()]
    assert all(b < a for a, b in zip(v, v[1:], strict=False))
