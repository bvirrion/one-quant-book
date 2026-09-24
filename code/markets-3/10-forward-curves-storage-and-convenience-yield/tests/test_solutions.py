"""Numbers gate: every numerical answer printed in Book 3, Chapter 10 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/commcurve"))
from firm_commcurve import full_carry_spread, net_convenience_yield
from m3_curves import convenience_monthly, decomposition, load, roll_cost, samuelson

D = decomposition()
V = samuelson()


def test_text():
    assert (D["start"], D["end"]) == (25.92, 86.91)
    assert round(D["spot"] * 100, 2) == 3.08 and round(D["roll"] * 100, 2) == -0.71
    assert round(D["collateral"] * 100, 2) == 3.18 and round(D["total"] * 100, 2) == 5.55
    back = sum(1 for _, p in load() if p[0] > p[1]) / len(load())
    assert round(back * 100) == 45
    assert round(net_convenience_yield(80.0, 79.40, 1 / 12, 0.04) * 100, 1) == 13.0
    assert round(net_convenience_yield(80.0, 80.60, 1 / 12, 0.04) * 100, 1) == -5.0
    assert [round(v * 100, 1) for v in V] == [40.9, 38.3, 35.3, 33.6]
    rc = roll_cost()
    assert (rc["step"], rc["cost_per_bbl"], rc["cost_usd"]) == (0.04, 0.12, 6_000_000)
    med = sorted(y for _, _, y in convenience_monthly())[len(convenience_monthly()) // 2]
    assert abs(med) < 0.02


def test_exercises():
    assert round(80 * math.exp(0.02), 2) == 81.62 and round(full_carry_spread(80, 1 / 12, 0.04, 0.03), 2) == 0.47
    assert round(net_convenience_yield(70.0, 71.20, 1 / 12, 0.05) * 100, 1) == -15.4
    assert round(5.55 - 3.08 - 3.18, 2) == -0.71
    assert round(roll_cost(days=1)["cost_per_bbl"], 2) == 0.20 and round(roll_cost(days=10)["cost_per_bbl"], 2) == 0.11
    ratio = V[3] / V[0]
    assert round(ratio, 2) == 0.82 and round(-math.log(ratio) / 0.25, 2) == 0.79
    assert round(math.log(2) / (-math.log(ratio) / 0.25), 2) == 0.88


def test_problem():
    rc = roll_cost()
    assert rc["per_day_mbbl"] == 10 and rc["cost_year"] == 72_000_000
    assert round(0.004 * 50, 2) == 0.20
