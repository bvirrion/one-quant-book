import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_rebatemm as rm  # noqa: E402

fs = rm.fs


def test_queue_edge_limits():
    # no sweeps, no abandonment: always filled by flow, edge = half-spread - adverse - fee
    r = rm.queue_edge(1000, 500.0, 1e-9, 1e-9, -0.3, n=2000)
    assert r["fill_prob"] > 0.999 and math.isclose(r["edge_per_fill"], 0.5 - 0.2 + 0.3, abs_tol=1e-9)
    # a longer queue fills less often and more of its fills are sweeps
    a, b = rm.queue_edge(1000, 500.0, 1 / 30, 1 / 20, 0.0), rm.queue_edge(20000, 500.0, 1 / 30, 1 / 20, 0.0)
    assert b["fill_prob"] < a["fill_prob"] and b["sweep_share"] > a["sweep_share"] and b["edge_per_order"] < a["edge_per_order"]


def test_tier_arithmetic():
    s = fs.Schedule("X", -0.20, 0.30, (fs.Tier("T1", 0.0020, -0.29),))
    tcv = 11e9
    assert math.isclose(rm.monthly_bill(s, 18e6, tcv, 21), 21 * 18e6 * -0.20)
    assert math.isclose(rm.marginal_fee(s, 18e6, tcv), -0.20)
    assert rm.marginal_fee(s, 21.9e6, tcv, 100000) < -10.0            # the cliff
    c = rm.chase(s, 18e6, tcv, 21, 21, 0.6)
    assert math.isclose(c["extra_per_day"], 4e6) and math.isclose(c["cost"], 84e6 * 0.6)
    assert math.isclose(c["gain"], (21 * 18e6 + 84e6) * 0.29 - 21 * 18e6 * 0.20)
    assert rm.chase(s, 14e6, tcv, 21, 21, 0.6)["pays"] is False
    assert rm.last_day_to_chase(s, 18e6, tcv, 21, 0.6, 0.001) == 14
