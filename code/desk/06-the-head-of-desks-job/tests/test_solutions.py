"""Numbers gate: every numerical answer printed in Book 16, chapter 6 (text and solutions)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_head as m  # noqa: E402

dp = m.dp


def r(x, d=1):
    return round(float(x), d)


def test_headline():
    h = m.headline()
    assert (r(h["mu"]), r(h["sigma"]), r(h["sharpe"], 2)) == (55.0, 42.2, 1.30)
    assert r(100 * h["p_meet"]) == 44.8 and r(h["lam75"], 2) == 2.28 and r(100 * h["p_loss_year"], 0) == 26
    assert r(m.PLAN.budget, 1) == 60.5 and r(2.28 * 42.2, 0) == 96


@pytest.mark.reference
def test_simulated():
    s = m.simulated()
    assert (r(100 * s["p_meet"]), r(s["mdd_median"]), r(s["mdd_p90"])) == (45.0, 30.0, 50.4)
    assert r(m.expected_pnl_after_costs()) == 20.5


def test_small_runs():
    s = m.simulated(n=2_000)
    assert abs(s["p_meet"] - m.headline()["p_meet"]) < 0.05 and s["mdd_p90"] > s["mdd_median"] > 0
    f = m.fan(n=500)
    assert all(f[k][0] < f[k][2] < f[k][4] for k in f)


def test_cascade():
    c = m.cascade()
    assert (r(c["vol_budget"]), r(c["daily_var"]), r(c["scale"], 2)) == (45.6, 6.7, 1.08)
    assert [r(v) for v in c["stops"].values()] == [8.8, 7.0, 4.2]


def test_exercises():
    assert r(100 * m.p_meet_closed(1.0, 1.1)) == 46.0
    assert dp._inv_phi(0.95) > 1.3 and dp.risk_multiple(m.PLAN, 0.95) == math.inf
    target = m.p_meet_closed(0.5, 1.5)
    assert r(100 * target) == 40.1 and r(1 - dp._inv_phi(target) / 2.0, 3) == 1.125
    assert r(60.5 * 3 / 12 - 55 * 3 / 12, 1) == 1.4 and r((60.5 - 55) * 0.25 / (42.2 * math.sqrt(0.25)), 3) == 0.065
    lam = dp.risk_multiple(m.plan(1.2), 0.75)
    assert r(lam, 2) == 2.49 and r(dp._inv_phi(0.99) * lam * dp.plan_stats(m.PLAN)["sigma"] / math.sqrt(252), 1) == 15.4
    assert r(100 * (1 - m.headline()["p_meet"]) ** 2, 1) == 30.5
    assert r(100 * dp._phi(-1.0), 1) == 15.9 and r(100 * m.p_meet_closed(1.3, 1.2), 1) == 39.7
