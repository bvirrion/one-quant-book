"""Tutorial of Book 2, Chapter 3: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from bond_demo import SETTLE, TEN, Y10, from_32nds, price_yield_curve, to_32nds, year_of_prices, zero_curve


def test_ten_year_end_state():
    r = TEN.risk(Y10, SETTLE)
    assert round(TEN.accrued(SETTLE), 6) == 0.473505
    assert round(TEN.clean_price(Y10, SETTLE), 6) == 100.397405 and to_32nds(100.397405) == "100-12+"
    assert (round(r["macaulay"], 3), round(r["modified"], 3), round(r["dv01"] * 1e4), round(r["convexity"], 1)) == (
        8.142, 7.975, 804, 75.8)


def test_price_yield_curve_is_convex_and_tangent_below():
    rows = price_yield_curve(TEN, Y10)
    assert all(p >= lin - 1e-9 for _, p, lin, _ in rows)
    prices = [p for _, p, _, _ in rows]
    assert all(a > b for a, b in zip(prices, prices[1:], strict=False))


def test_clean_price_has_no_coupon_jump():
    rows = year_of_prices(TEN, Y10)
    dirty = [d for _, _, d in rows]
    clean = [c for _, c, _ in rows]
    assert max(abs(a - b) for a, b in zip(clean, clean[1:], strict=False)) < 0.01
    assert min(b - a for a, b in zip(dirty, dirty[1:], strict=False)) < -2.0


def test_zero_curve_shape_as_captioned():
    z = {t: (p, zz) for t, p, zz in zero_curve()}
    assert z[10.0][1] > z[10.0][0] and z[1.0][1] < z[1.0][0] and z[2.0][1] < z[2.0][0]


def test_32nds_round_trip():
    assert from_32nds("99-16+") == 99.515625 and to_32nds(101.296875) == "101-09+"


def test_figure_3_2_caption_gaps():
    rows = price_yield_curve(TEN, Y10)
    lo, hi = rows[0], rows[-1]
    assert (round(lo[0], 1), round(hi[0], 1)) == (1.7, 6.7)
    assert (round(hi[1] - hi[2], 1), round(lo[1] - lo[2], 1)) == (2.2, 2.6)
