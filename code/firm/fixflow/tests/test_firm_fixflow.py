"""Acceptance tests of the Book 2, Chapter 17 build (month-end flows, fixing orders)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_fixflow import dealer_pnl, fix_and_cost, hedge_rebalance, simulate_pnl, weight_rebalance


def test_hedge_rebalance_sign():
    assert hedge_rebalance(100.0, 0.05, 0.5) == 2.5 and hedge_rebalance(100.0, -0.05, 0.5) == -2.5


def test_weight_rebalance_sells_the_winner():
    flows = weight_rebalance({"US": 66.0, "EU": 34.0}, {"US": 0.6, "EU": 0.4})
    assert math.isclose(flows["US"], -6.0) and math.isclose(flows["EU"], 6.0)


def test_fix_economics():
    fix, cost = fix_and_cost(1.0, 2.0, 0.0)
    assert fix == cost == 1.0                       # no pre-hedge: the dealer buys at the fix
    assert math.isclose(dealer_pnl(1.0, 2.0, 1.0), 1.0) and math.isclose(dealer_pnl(3.0, 2.0, 0.5), 4.5)
    assert fix_and_cost(1.0, 2.0, 1.0)[1] == cost    # the cost does not depend on p


def test_pre_hedging_adds_risk():
    m0, s0 = simulate_pnl(1.0, 2.0, 0.0, 0.5)
    m1, s1 = simulate_pnl(1.0, 2.0, 1.0, 0.5)
    assert abs(m0) < 0.02 and s0 < 1e-9 and math.isclose(m1, 1.0, abs_tol=0.02) and s1 > 0.45
