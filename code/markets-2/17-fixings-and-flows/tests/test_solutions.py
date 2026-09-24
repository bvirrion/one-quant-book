"""Numbers gate: every numerical answer printed in Book 2, Chapter 17 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/fixflow"))
from firm_fixflow import dealer_pnl, fix_and_cost, hedge_rebalance, weight_rebalance
from fixflow_demo import LAM, PIP_USD, Q, fixing_order, month_end


def test_text():
    assert round(1_114_918_000 / 1e9, 2) == 1.11
    assert round(LAM * Q, 6) == 3.0
    r0, r5, r1 = fixing_order(0.0), fixing_order(0.5), fixing_order(1.0)
    assert (r0["fix"], r0["cost"], r5["fix"], r1["fix"]) == (1.5, 1.5, 2.25, 3.0)
    assert (round(r5["pnl"]), round(r1["pnl"])) == (75_000, 150_000) and round(r5["client_extra"]) == 75_000
    m = month_end()
    assert round(m["hedge_sale"] / 1e9) == 40 and round(m["fund_us"] / 1e9, 2) == -1.44


def test_exercises():
    assert round(hedge_rebalance(50e9, 0.03, 0.7) / 1e9, 2) == 1.05
    fix, cost = fix_and_cost(Q, LAM, 0.3)
    assert (round(fix, 2), cost, round(dealer_pnl(Q, LAM, 0.3) * PIP_USD)) == (1.95, 1.5, 45_000)
    w = weight_rebalance({"US": 60e9 * 0.97, "EU": 40e9 * 1.02}, {"US": 0.6, "EU": 0.4})
    assert round(w["US"] / 1e9, 2) == 1.2
    assert (round(fixing_order(0.5)["sim_mean"]), round(fixing_order(0.5)["sim_sd"])) == (74_346, 100_276)
    assert (round(fixing_order(1.0)["sim_mean"]), round(fixing_order(1.0)["sim_sd"])) == (148_692, 200_552)


def test_problem():
    assert round(fixing_order(0.5)["sim_sd"], -3) == 100_000 and round(fixing_order(1.0)["sim_sd"], -3) == 201_000
    assert round(Q - 6e8) == 400_000_000
