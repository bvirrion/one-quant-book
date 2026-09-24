"""Acceptance tests of the Book 5, Chapter 25 build (volatility-book P&L)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_volpnl import DT, Option, SkewSurface, book_greeks, explain, gamma_scalp, roll_down, value

BOOK = [Option(100.0, 0.25, "C"), Option(100.0, 0.25, "P"), Option(90.0, 0.25, "P", -2.0)]


def test_explain_is_exact_to_third_order():
    for ref in (100.0, None):
        s0 = SkewSurface(lambda tau: 0.2, -0.1, ref)
        s1 = s0.shifted(0.002)
        for ds in (0.1, 0.2, 0.4):
            e = explain(BOOK, 100.0, 100.0 + ds, 0.0, DT, s0, s1)
            explained = abs(e["gamma"]) + abs(e["theta"]) + abs(e["vega"]) + abs(e["delta"])
            assert abs(e["unexplained"]) < 0.02 * explained
        small, big = (abs(explain(BOOK, 100.0, 100.0 + d, 0.0, 0.0, s0, s0)["unexplained"]) for d in (0.5, 1.0))
        assert 5 < big / small < 11                                  # third order: doubling the move x8


def test_hedge_and_marking_rules():
    ss, sd = SkewSurface(lambda tau: 0.2, -0.1, 100.0), SkewSurface(lambda tau: 0.2, -0.1, None)
    assert ss.vol(90.0, 0.25, 95.0) == ss.vol(90.0, 0.25, 100.0)
    assert math.isclose(sd.vol(90.0, 0.25, 95.0) - sd.vol(90.0, 0.25, 100.0), -0.1 * math.log(100 / 95) / 0.5)
    hedge = -book_greeks(BOOK, 100.0, 0.0, ss)["delta"]
    e = explain(BOOK, 100.0, 100.1, 0.0, 0.0, ss, ss, hedge)
    assert abs(e["delta"]) < 1e-12
    assert value([Option(100.0, 0.1, "C")], 104.0, 0.1, ss) == 4.0


def test_gamma_scalp_identity():
    r = 0.18 * math.sqrt(DT) * np.array([(-1.0) ** i for i in range(21)])
    g = gamma_scalp(r, vol=0.18)
    assert abs(g["realised"] - 0.18) < 1e-12
    assert abs(g["daily"].sum()) < 0.1 * g["premium"]
    r2 = 0.30 * math.sqrt(DT) * np.array([(-1.0) ** i for i in range(21)])
    g2 = gamma_scalp(r2, vol=0.18)
    assert g2["daily"].sum() > 0 and abs(g2["daily"].sum() - g2["approx"].sum()) < 0.15 * g2["daily"].sum()


def test_roll_down():
    def atm(tau):
        return 0.24 - 0.06 * math.exp(-tau / 0.25)
    assert roll_down(atm, 0.25, 1 / 12) < 0 and roll_down(lambda tau: 0.2, 0.5, 0.1) == 0.0
