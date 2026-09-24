"""Tests of the Chapter 17 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_perp as m


def test_month_pins_funding_in_calm():
    rows = m.month_of_funding(m.regimes())
    assert len(rows) == 90
    assert all(round(r, 8) == 0.0001 for _, _, r in rows[:30])
    assert max(r for _, _, r in rows) > 0.0009 and min(r for _, _, r in rows) < -0.0002


def test_inverse_curve_concave():
    rows = m.inverse_curve()
    assert rows[0][1] == -1.0 and rows[-1][1] == 0.5
    assert all(p <= t + 1e-12 for _, p, t in rows)


def test_trade():
    assert round(m.margin_to_survive(), 4) == 0.3065
    assert round(100 * m.funding_trade(0.1192), 2) == 8.89
    assert round(100 * m.funding_trade(0.1192, margin=0.0), 2) == 11.62
    assert m.yearly_funding()[2024] == 0.1192
