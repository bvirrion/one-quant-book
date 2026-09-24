"""Tests of the Chapter 27 demo: the plan, its check by search, and the routed day."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from access_demo import brute_force, day_of_orders, limits, plan


def test_plan_respects_limits_and_matches_search():
    p, lim = plan(), limits()
    assert all(p["flow"][pb] <= lim[pb][1] and p["position"][pb] <= lim[pb][2] for pb in lim)
    assert sum(p["flow"].values()) == 1200 and sum(p["position"].values()) == 300
    assert abs(brute_force() - p["total"]) < 1e-9


def test_day_keeps_every_limit():
    r = day_of_orders()
    assert all(max(row[1:]) <= 100 + 1e-9 for row in r["path"])
    assert r["rejected"] == 0
