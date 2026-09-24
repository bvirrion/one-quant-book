"""Tutorial of Book 6, chapter 14: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_structural as m


def test_barrier_fit_reprices_the_quote():
    f = m.firm()
    assert abs(m.fp_spread(f["V"], f["sigma"], 5.0, m.implied_barrier()) - m.MARKET_SPREAD) < 1e-8


def test_model_spread_falls_as_equity_rises_and_hedge_is_short():
    c = m.equity_spread_curve()
    assert all(b[1] < a[1] for a, b in zip(c, c[1:], strict=False))
    assert m.hedge()["short_equity"] > 0
