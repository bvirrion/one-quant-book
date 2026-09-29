"""Acceptance tests of firm.riskgrid (One Quant Book 15, chapter 20)."""
import datetime as dt
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "riskengine"))
import firm_riskengine as RE  # noqa: E402
import firm_riskgrid as G  # noqa: E402


def trades(n=10, est=1.0):
    return [G.GridTrade(f"t{i}", "x", est) for i in range(n)]


def test_plan_batches_and_isolation():
    ts = trades(10) + [G.GridTrade("slow", "x", 50.0)]
    p = G.plan(ts, 100, 3.0, 20, 1.0)
    assert G.cells(p) == 11 * 100 and all(t.scenarios == 20 for t in p)
    q = G.plan(ts, 100, 3.0, 20, 1.0, isolate_above=200.0)
    heavy = [t for t in q if t.trades[0].trade_id == "slow"]
    assert len(heavy) == 25 and all(t.scenarios == 4 for t in heavy) and G.cells(q) == 1100
    assert max(t.estimate for t in q) <= 201.0 < max(t.estimate for t in p)


def test_failure_policies_and_bound():
    ts = trades(8) + [G.GridTrade("bad", "x", 1.0, fails=True)]
    p = G.plan(ts, 10, 3.0, 5, 1.0)
    a, b = G.run(p, 1, 2, failures="task"), G.run(p, 1, 2, failures="trade")
    assert a.wasted == 2 * 2 * 16.0 and a.lost_cells == 3 * 10 and a.makespan > b.makespan
    assert b.wasted == 0 and b.quarantined == ["bad"] and b.lost_cells == 10
    assert G.lower_bound(p, 2) <= b.makespan


def test_adjoint_deltas_match_bumped_sensitivities():
    asof = dt.date(2026, 9, 28)
    curve = RE.PillarCurve(asof, (0.030, 0.031, 0.032, 0.033, 0.034, 0.035, 0.036, 0.036))
    md = RE.fp.MarketData(asof, {"R": 0.0}, {"USD": curve}, vols={"R": RE.fp.FlatVol(0.01)})
    sw = RE.IRSwap(id="S", underlying="R", currency="USD", years=12, fixed=0.034)
    pv, grad, stats = G.swap_pv_adjoint(curve.zeros, RE.TENORS, 12, 0.034)
    assert pv == pytest.approx(RE.fp.price(sw, md, RE.model_for(sw)).pv, abs=1e-12)
    bump = RE.fp.sensitivities(sw, md, [f"CURVE:USD:{p}" for p in RE.PILLARS], RE.model_for(sw))
    for g, p in zip(grad, RE.PILLARS, strict=True):
        assert g * 1e-4 == pytest.approx(bump[f"CURVE:USD:{p}"], abs=1e-9)
    assert stats["ops"] > 0


def test_result_cache():
    c = G.ResultCache()
    c.store("a", 1, "m1", 0.0)
    c.store("b", 1, "m1", 0.0)
    assert c.needed({"a": 1, "b": 2, "c": 1}, "m1") == ["b", "c"] and c.needed({"a": 1}, "m2") == ["a"]
    assert G.hours(3 * 3600 + 125) == "3:02"
