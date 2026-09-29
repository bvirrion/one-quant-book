"""Acceptance tests of firm.cloudcost (One Quant Book 15, chapter 26)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_cloudcost as C  # noqa: E402

J = C.J


def test_owned_server_and_per_hour_costs():
    s = C.OwnedServer(price=48_000, life_months=48, kw=1.0, pue=1.5, power_price=0.10, space=100, staff=50)
    assert s.monthly == pytest.approx(1000 + 1.5 * 730 * 0.10 + 150)
    assert s.per_thread_hour(100) == pytest.approx(s.monthly / 73_000)
    assert C.cost_per_used_hour("fixed", 1.0, 0.25) == 4.0 and C.cost_per_used_hour("metered", 1.0, 0.25, 0.1) == 1.1
    assert C.break_even(1.0, 4.0) == 0.25
    assert C.PriceItem("x", 1.0, "USD/h", "list", "2026-09").date == "2026-09"


def test_plan_capacity_by_duration_curve():
    demand = [10] * 90 + [20] * 10                      # 10 units always, 10 more a tenth of the time
    p = C.plan_capacity(demand, owned=0.2, reserved=0.5, on_demand=1.0)
    assert (p.owned, p.reserved, p.metered_hours) == (10, 0, 100.0)
    assert p.total == pytest.approx(10 * 0.2 * 100 + 100 * 1.0)
    q = C.plan_capacity(demand, owned=math.inf, reserved=0.05, on_demand=1.0)
    assert (q.owned, q.reserved, q.metered_hours) == (0, 20, 0.0)          # 0.05 < 0.1: reserve the peak too
    r = C.plan_capacity(demand, owned=math.inf, reserved=0.5, on_demand=1.0, spot=0.4, spot_share=0.5)
    assert r.cost["metered"] == pytest.approx(100 * 0.7)


def test_checkpoints_and_billing():
    tasks = [J.Task(0, 3600.0, 3600.0), J.Task(1, 100.0, 100.0)]
    ck = C.checkpointed(tasks, chunk=900.0, overhead=10.0)
    assert len(ck) == 5 and ck[1].deps == (0,) and ck[0].duration == pytest.approx(910.0)
    s = J.simulate(ck, J.Cluster(2, 1, seed=0), J.LPT())
    assert s.makespan == pytest.approx(4 * 910.0) and C.billed_node_hours(s, 1) == pytest.approx((3640 + 100) / 3600)


def test_transfer_tiers():
    tiers = [(10.0, 1.0), (20.0, 0.5), (math.inf, 0.1)]
    assert C.transfer_out(5, tiers) == 5.0 and C.transfer_out(15, tiers) == 12.5 and C.transfer_out(30, tiers) == 16.0
