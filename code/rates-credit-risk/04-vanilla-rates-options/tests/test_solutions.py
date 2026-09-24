"""Numbers gate: every numerical answer printed in Book 6, chapter 4 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_vanilla as m
from firm_capfloor import Cap, cap_price, caplets, piecewise
from firm_normalvol import bachelier, normal_to_black

SM = dict(m.smile_from_flat_normal())
SW = m.swaption_table()
TC = m.treasurer_cap()
VOL = piecewise(m.stripped())
CL = caplets(Cap(m.SPOT, 5, 0.03), m.PROJ, m.DISC)


def test_text():
    assert (round(SM[0.025], 1), round(SM[0.005], 1), round(SM[0.045], 1)) == (32.7, 71.1, 23.8)
    assert 80 / 250 == 0.32
    assert [round(v * 1e4, 1) for _, v in m.stripped()] == [58.0, 66.6, 75.7, 78.9, 78.0, 73.7, 67.9]
    assert (round(SW["fwd"] * 100, 3), round(SW["annuity"], 3), round(SW["lognormal_vol"] * 100, 1)) == (
        3.098, 7.740, 26.2)
    assert (round(SW["physical"]), round(SW["cash"]), round(SW["cash_annuity_x_df"], 3)) == (
        5_525_150, 5_410_452, 7.579)
    assert round((1 - SW["cash"] / SW["physical"]) * 100, 1) == 2.1


def test_exercises():
    assert round(1e7 * (0.034 - 0.03) * 0.5069) == 20_276
    assert round(normal_to_black(0.025, 0.025, 5, 0.008) * 100, 1) == 32.7
    lo, hi = 0.0, 0.03
    for _ in range(60):
        k = (lo + hi) / 2
        f = cap_price(Cap(m.SPOT, 5, k, floor=True), m.PROJ, m.DISC, VOL, notional=200e6)
        lo, hi = (k, hi) if f < TC["premium"] else (lo, k)
    assert round(k * 100, 2) == 1.97
    late = [c for c in CL if c["t"] > 4.0]
    a = 200e6 * sum(bachelier(c["fwd"], 0.03, c["t"], 0.0076, c["delta"] * c["df"]) for c in late)
    b = 200e6 * sum(bachelier(c["fwd"], 0.03, c["t"], VOL(c["t"]), c["delta"] * c["df"]) for c in late)
    assert (len(late), round(a), round(b), round(b - a)) == (2, 886_956, 916_329, 29_373)


def test_problem():
    assert TC["n"] == 9
    assert (round(TC["premium"]), round(TC["premium_pct"], 3), round(TC["running_bp"], 1)) == (2_157_482, 1.079, 25.2)
    assert round(TC["flat_check"]) == round(TC["premium"])
    assert round(TC["fwd_avg"] * 100, 2) == 2.44 and TC["intrinsic"] == 0.0
    assert round(TC["vega_per_bp"]) == 43_093 and round(10 * TC["vega_per_bp"]) == 430_929
    assert round(TC["lognormal"]) == 1_827_377
    assert round(200e6 * 0.005 * sum(c["delta"] for c in CL)) == 4_569_444
    assert round(200e6 * 0.005 * TC["annuity"]) == 4_285_872
    assert round(3 + TC["running_bp"] / 100, 2) == 3.25
def test_cap_strike_caption():
    t = m.cap_strike_table()
    assert (round(t[0][2]), round(t[-1][2])) == (70, 4)
