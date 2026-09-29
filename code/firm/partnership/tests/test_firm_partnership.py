import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_partnership as fp  # noqa: E402


def test_allocation_by_points_and_departure():
    p = fp.Partnership([fp.Member("a", 3, 10.0), fp.Member("b", 1, 10.0)])
    draws = p.allocate(40.0, 0.5)
    assert draws == {"a": 15.0, "b": 5.0}
    assert [m.capital for m in p.members] == [25.0, 15.0] and math.isclose(p.total_capital, 40.0)
    p.allocate(-8.0, 0.5)
    assert [m.capital for m in p.members] == [19.0, 13.0]
    p.depart("a", 2)
    assert math.isclose(p.total_capital, 32.0)
    assert p.pay_departures() == 9.5 and p.pay_departures() == 9.5 and p.pay_departures() == 0.0


def test_own_funds_requirement_picks_highest():
    req, which = fp.own_funds_requirement(100.0, 10_000.0, 50_000.0, 5.0)
    assert which == "fixed overheads" and req == 25.0
    req, which = fp.own_funds_requirement(10.0, 20_000.0, 100_000.0, 5.0)
    assert which == "K-factors" and math.isclose(req, 20.0 + 10.0 + 5.0)
    assert fp.own_funds_requirement(0.0, 0.0, 0.0, 0.0) == (0.75, "permanent")


def test_treadmill_steady_state_holds_parity():
    p = fp.Params(spend_share=fp.steady_spend_share(0.15, 0.20), years=12)
    sim = fp.simulate(p, 0.5)
    assert np.allclose(sim["rel"], 1.0) and np.allclose(sim["capture"], p.c0)
    low = fp.simulate(fp.Params(spend_share=0.2), 0.5)
    assert np.all(np.diff(low["rel"]) < 0)


def test_capital_limits_volume_and_payout_identity():
    p = fp.Params(market=1e12)
    s = fp.simulate(p, 0.6)
    assert math.isclose(s["volume"][0], p.capital0 / p.margin)
    assert np.allclose(np.diff(np.r_[p.capital0, s["capital"]]), s["profit"] - s["payout"])
    assert fp.discounted_payout(s, 0.0) == s["payout"].sum()


def test_target_capital_policy():
    p = fp.Params(margin=0.02, market=20_000.0)
    s = fp.simulate(p, fp.target_capital(400.0))
    assert s["capital"][0] > p.capital0 and s["payout"][0] == 0.0
    assert np.all(s["capital"][s["payout"] > 0] >= 400.0 - 1e-9)
