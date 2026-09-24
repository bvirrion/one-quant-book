"""Numbers gate: every numerical answer printed in Book 2, Chapter 9 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/curve"))
from firm_curve import add_years, annuity, bucket_dv01, par_rate, schedule
from swaps_demo import RATES, SPOT, TENORS, corporate_hedge, curve, first_period_interest, forward_5y5y, steepener

H = corporate_hedge()


def test_text():
    assert round(first_period_interest(200e6, 0.0405, SPOT, add_years(SPOT, 1))) == 8_212_500
    assert round((0.0405 + 0.015) * 100, 2) == 5.55
    assert round(0.79 * 846) == 668


def test_exercises():
    assert round(first_period_interest(100e6, 0.0405, SPOT, add_years(SPOT, 1))) == 4_106_250
    assert round((0.0405 - 0.0420) * 1e4) == -15
    c = curve()
    assert (round(par_rate(c, schedule(SPOT, 4)) * 100, 4), round(par_rate(c, schedule(SPOT, 8)) * 100, 4)) == (
        3.8425, 3.9743)
    assert round(c.df(add_years(SPOT, 10)), 6) == 0.666773
    f = forward_5y5y()["buckets"]
    b5 = bucket_dv01(SPOT, TENORS, RATES, schedule(SPOT, 5), par_rate(c, schedule(SPOT, 5)), 1e8)
    b10 = bucket_dv01(SPOT, TENORS, RATES, schedule(SPOT, 10), par_rate(c, schedule(SPOT, 10)), 1e8)
    assert round(b5[3]) == 45_278 and round(b10[5]) == 82_262
    assert round(-f[3] / b5[3] * 100, 1) == 100.3 and round(f[5] / b10[5] * 100, 1) == 100.5
    assert round(annuity(c, schedule(SPOT, 10)) * 1e4) == 82_278 - 0 * 1


def test_problem():
    assert round(H["fixed"] * 100, 2) == 4.05 and round(H["all_in"] * 100, 2) == 5.55
    assert round(H["dv01"]) == 164_474
    assert (round(H["pnl_up50"] / 1e6, 2), round(H["pnl_dn50"] / 1e6, 2)) == (8.02, -8.44)
    assert [round(steepener(t) * 1e4, 1) for t in TENORS] == [-20.0, -16.1, -12.2, -4.4, 3.3, 15.0]
    assert round(H["pnl_steep"] / 1e6, 2) == 2.46 and round(15 * H["dv01"] / 1e6, 2) == 2.47
    assert round(2 * H["dv01"]) == 328_947
