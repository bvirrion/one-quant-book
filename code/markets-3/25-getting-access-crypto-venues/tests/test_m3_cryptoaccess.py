"""Tests of the Chapter 25 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_cryptoaccess as m


def test_allocation():
    spread, conc = m.spread_vs_concentrate()
    assert round(sum(spread.values())) == 321_120 and round(sum(conc.values())) == 143_400
    assert round(m.tier_match_value()) == 11_040


def test_uptime():
    u0, r0 = m.programme_value()
    u1, r1 = m.programme_value(thin_at=2.25)
    assert round(u0, 3) == 0.873 and r0 == 0
    assert round(u1, 3) == 0.910 and round(r1) == 10_500
    curve = m.uptime_curve()
    assert curve[0][1] < curve[-1][1]


def test_fee_curve_crossover():
    rows = m.effective_fee_curve()
    assert rows[0][1:] == (10.0, 15.9) or (round(rows[0][1], 1), round(rows[0][2], 1)) == (10.0, 15.9)
    below = [r for r in rows if r[0] < 2.5]
    above = [r for r in rows if r[0] >= 2.5]
    assert all(b <= k for _, b, k in below) and all(k < b for _, b, k in above)
