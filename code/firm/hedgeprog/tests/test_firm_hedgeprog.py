"""Acceptance tests of the Book 3, Chapter 12 build (hedging programmes)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_hedgeprog import Leg, black76, cash_flow_at_risk, collar, hedged_revenue, simulate_averages, three_way, value


def test_black_put_call_parity():
    f, k, t, s, r = 60.0, 55.0, 1.0, 0.35, 0.04
    c, p = black76(f, k, t, s, r, True), black76(f, k, t, s, r, False)
    assert math.isclose(c - p, math.exp(-r * t) * (f - k), rel_tol=1e-12)


def test_average_is_cheaper_than_vanilla():
    avg = simulate_averages(60.0, 0.35, 1.0, 12, 100_000)
    apo = value([Leg("put", 55.0)], avg, 0.04, 1.0)
    assert apo < black76(60.0, 55.0, 1.0, 0.35, 0.04, False)
    assert abs(np.mean(avg) - 60.0) < 0.2                 # the future is a martingale


def test_structures_bound_revenue():
    x = np.linspace(20, 120, 101)
    rev = hedged_revenue(x, collar(50.0, 75.0), 0.0)
    assert rev.min() == 50.0 and rev.max() == 75.0
    rev3 = hedged_revenue(x, three_way(55.0, 40.0, 75.0), 0.0)
    assert rev3[x == 30.0][0] == 30.0 + 15.0            # below the lower put the protection is capped at 15
    assert cash_flow_at_risk(np.array([40.0, 50.0, 60.0, 70.0]), 55.0, 0.25) > 0
