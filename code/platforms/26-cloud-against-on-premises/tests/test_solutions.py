"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 26 (text and solutions)."""
import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_cloudcost as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/26-cloud-against-on-premises"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    r = P.burst(0.05, P.PRICES["spot"].value, n=300, n_long=3, nodes=2)
    assert r["cost"] > 0 and r["busy_core_h"] > 0
    assert P.burst(0.05, 1.0, 900.0, n=300, n_long=3, nodes=2)["makespan_h"] > 0


def test_prices_and_break_even():
    p = P.per_thread()
    assert (round(p["on_demand"], 6), round(p["spot"], 6), round(p["reserved_3y"], 6)) == (0.044625, 0.018096, 0.019647)
    assert round(P.SERVER.monthly) == 1508 and round(p["owned"], 5) == 0.00404
    b = P.break_evens()
    assert (round(b["vs_on_demand"], 3), round(b["vs_spot"], 3), round(b["reserved_3y_vs_on_demand"], 3)) == (0.09, 0.223, 0.44)
    assert [r["vs_on_demand"] for r in _csv("break_even.csv")] == ["0.090", "0.145", "0.200"]
    assert round(P.monthly_to_hourly_rate(0.2), 6) == 0.000306


def test_plans_and_data():
    plans = {r["plan"]: r for r in _csv("plans.csv")}
    assert [plans[k]["total"] for k in plans] == ["1315233", "940460", "361215", "281883"]
    assert plans["owned + on demand"]["owned_threads"] == "5500" and plans["reserved + on demand"]["reserved_threads"] == "2500"
    assert _csv("demand.csv")[0] == {"mean": "3364", "peak": "13500", "hours_above_5500": "496"}
    assert _csv("data.csv")[0]["transfer_out_usd"] == "29491" and _csv("data.csv")[0]["storage_usd_month"] == "11776"
    assert P.C.transfer_out(500 * 1024, P.TRANSFER_TIERS) == pytest.approx(29491.2)
    spread = P.plans(P.demand(spread_sweep=True))["owned + on demand"]                 # exercise 7
    assert (spread.owned, round(spread.total)) == (7900, 291003)


def test_burst_csv():
    b = {r["rate_per_hour"]: r for r in _csv("burst.csv")}
    assert (b["0"]["on_demand_cost"], b["0"]["cost_none"], b["0.000306"]["cost_none"], b["0.000306"]["makespan_none"]) == (
        "202.79", "82.23", "94.20", "14.39")
    assert (b["0.2"]["cost_none"], b["0.2"]["makespan_none"], b["0.2"]["cost_ckpt"], b["0.2"]["makespan_ckpt"]) == (
        "184.68", "58.96", "81.81", "8.78")


@pytest.mark.reference
def test_full_burst():
    r = P.burst(0.000306, P.PRICES["spot"].value)
    assert (round(r["cost"], 2), round(r["makespan_h"], 2)) == (94.20, 14.39)
