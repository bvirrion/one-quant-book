"""Numbers gate: every numerical answer printed in Book 5, Chapter 1 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_arbitrage import (
    BINOMIAL,
    PRICES,
    TRINOMIAL,
    box_results,
    call_payoff,
    find_arbitrage,
    price_bounds,
    state_price_vertices,
    state_prices,
    superreplication,
)

S = TRINOMIAL[:, 1]
R = box_results()


def test_text():
    q = state_prices(BINOMIAL, PRICES)
    assert (round(q[0], 4), round(q[1], 4), round(q[0] / 0.98, 4), round(20 * q[0], 4)) == (0.3933, 0.5867, 0.4014, 7.8667)
    v = sorted(tuple(np.round(x, 2)) for x in state_price_vertices(TRINOMIAL, PRICES))
    assert v == [(0.1, 0.88, 0.0), (0.54, 0.0, 0.44)]
    lo, hi = price_bounds(TRINOMIAL, PRICES, call_payoff(S, 100))
    assert (round(lo, 2), round(hi, 2)) == (2.00, 10.80)
    cost, theta = superreplication(TRINOMIAL, PRICES, call_payoff(S, 100))
    assert round(cost, 2) == 10.80 and np.allclose(theta, [-40, 0.5])
    d3 = np.column_stack([TRINOMIAL, call_payoff(S, 100)])
    assert np.allclose(state_prices(d3, np.array([0.98, 100, 6.0])), [0.30, 0.48, 0.20])
    edge, th = find_arbitrage(d3, np.array([0.98, 100, 11.0]), [1e4, 10, 1])
    assert round(edge, 2) == 0.20 and np.allclose(th, [-40, 0.5, -1])
    assert round(R["mid"], 2) == 958.90 and round(100 * R["r_mid"], 2) == 4.20 and round(100 * R["mid"]) == 95_890


def test_exercises():
    b = np.array([[1.0, 115.0], [1.0, 95.0]])
    q = state_prices(b, np.array([0.99, 100.0]))
    assert (round(q[0], 4), round(q[1], 4), round(q[0] / 0.99, 4), round(15 * q[0], 4)) == (0.2975, 0.6925, 0.3005, 4.4625)
    lo, hi = price_bounds(TRINOMIAL, PRICES, np.maximum(100 - S, 0))
    assert (round(lo, 2), round(hi, 2)) == (0.0, 8.80) and round(-50 + 60 * 0.98, 2) == 8.80
    qc = np.array([0.30, 0.48, 0.20])
    assert tuple(np.round(qc / 0.98, 4)) == (0.3061, 0.4898, 0.2041)
    assert tuple(np.round(qc / np.array([0.45, 0.45, 0.10]), 4)) == (0.6667, 1.0667, 2.0)
    lo, hi = price_bounds(TRINOMIAL, PRICES, np.array([1.0, 0, 0]))
    assert (round(lo, 2), round(hi, 2)) == (0.10, 0.54) and round(0.025 * 100 - 2 * 0.98, 2) == 0.54
    lo, hi = price_bounds(TRINOMIAL, PRICES, call_payoff(S, 90) - call_payoff(S, 110))
    assert round(lo, 2) == round(hi, 2) == 10.80


def test_problem():
    assert (round(R["buy"], 2), round(R["sell"], 2)) == (962.10, 955.70)
    assert (round(100 * R["r_lend"], 2), round(100 * R["r_borrow"], 2)) == (3.86, 4.53)
    assert round(R["interest_usd_lend"]) == 3790
    assert (round(R["lend_spread_bp"], 1), round(R["borrow_spread_bp"], 1)) == (-13.6, 53.1)
    assert round(1000 * math.exp(-0.04), 2) == 960.79 and R["violations_fair"] == 0
    assert round((R["buy"] - R["sell"]), 2) == 6.40
    n = 10e6 / (100 * R["mid"])
    assert round(n, 1) == 104.3 and round(104 * 100 * R["mid"]) == 9_972_560
    assert round((R["r_mid"] - 0.04) * 1e4, 1) == 19.7


def test_interview():
    q = state_prices(np.array([[1.0, 110.0], [1.0, 95.0]]), np.array([1.0, 100.0]))
    assert round(q[0], 4) == 0.3333
    assert round(12.00 - 13.00 + 0.90, 2) == -0.10 and round(12.05 - 2 * 6.45 + 0.95, 2) == 0.10
