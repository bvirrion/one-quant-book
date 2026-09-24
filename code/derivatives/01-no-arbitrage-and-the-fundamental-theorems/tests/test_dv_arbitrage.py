"""Unit tests of the Chapter 1 teaching module."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_arbitrage import (
    BINOMIAL,
    PRICES,
    TRINOMIAL,
    call_payoff,
    find_arbitrage,
    price_bounds,
    state_price_vertices,
    state_prices,
    superreplication,
)

S = TRINOMIAL[:, 1]


def test_complete_market_reprices_assets():
    q = state_prices(BINOMIAL, PRICES)
    assert np.allclose(BINOMIAL.T @ q, PRICES) and np.all(q > 0)


def test_vertices_satisfy_constraints():
    for q in state_price_vertices(TRINOMIAL, PRICES):
        assert np.allclose(TRINOMIAL.T @ q, PRICES) and np.all(q >= 0)


def test_lp_duality_upper_bound_equals_superreplication():
    for k in (85.0, 95.0, 100.0, 110.0):
        g = call_payoff(S, k)
        assert abs(superreplication(TRINOMIAL, PRICES, g)[0] - price_bounds(TRINOMIAL, PRICES, g)[1]) < 1e-9


def test_replicable_claim_has_a_point_interval():
    g = call_payoff(S, 90) - call_payoff(S, 110)
    lo, hi = price_bounds(TRINOMIAL, PRICES, g)
    assert abs(hi - lo) < 1e-12


def test_arbitrage_found_outside_interval_only():
    d3 = np.column_stack([TRINOMIAL, call_payoff(S, 100)])
    assert find_arbitrage(d3, np.array([0.98, 100, 11.0]), [1e4, 10, 1])[0] > 0.19
    assert find_arbitrage(d3, np.array([0.98, 100, 6.0]), [1e4, 10, 1])[0] < 1e-12
