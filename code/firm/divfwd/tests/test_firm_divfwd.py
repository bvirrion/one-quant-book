"""Acceptance tests of the Book 5, Chapter 5 build (equity forward curve)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
from firm_bs import black
from firm_divfwd import ForwardCurve, implied_borrow, implied_carry, implied_forward, strip_dividends

C = ForwardCurve(100.0, 0.03, cash=((0.2, 1.0), (0.7, 1.2)), proportional=((0.9, 0.01),), borrow=0.004)


def test_cash_and_carry():
    t = 1.0
    f = C.forward(t)
    pv = 1.0 * math.exp(-0.006) + 1.2 * math.exp(-0.021)
    assert abs(f - (100 - pv) * 0.99 * math.exp(-0.004) * math.exp(0.03)) < 1e-12
    assert C.forward(0.1) == 100 * math.exp(-0.004 * 0.1) * math.exp(0.003)


def test_regression_recovers_forward_and_df_exactly():
    t, f, df = 0.75, C.forward(0.75), C.df(0.75)
    ks = [80.0, 90.0, 100.0, 110.0, 120.0]
    cs = [black(f, k, t, df, 0.25, "C") for k in ks]
    ps = [black(f, k, t, df, 0.25, "P") for k in ks]
    f2, df2 = implied_forward(ks, cs, ps)
    assert abs(f2 - f) < 1e-9 and abs(df2 - df) < 1e-12


def test_implied_borrow_round_trip():
    c = ForwardCurve(50.0, 0.04, borrow=0.35)
    t = 30 / 365
    assert abs(implied_borrow(50.0, c.forward(t), c.df(t), t) - 0.35) < 1e-12


def test_strips_sum_to_carry():
    ts = [0.25, 0.5, 0.75, 1.0]
    fs, ds = [C.forward(t) for t in ts], [C.df(t) for t in ts]
    assert abs(sum(strip_dividends(100.0, ts, fs, ds)) - implied_carry(100.0, fs[-1], ds[-1])) < 1e-12
