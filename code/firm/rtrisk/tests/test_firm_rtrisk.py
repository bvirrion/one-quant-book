"""Acceptance tests of firm.rtrisk (One Quant Book 15, chapter 18)."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_rtrisk as RT  # noqa: E402

FP = RT.FP
D = dt.date(2026, 1, 5)
PUT = FP.EuropeanOption(id="P", underlying="U", currency="USD", strike=100.0, expiry=D + dt.timedelta(days=60), right="P")
FUT = RT.Future("F", "U")


def md(s):
    return FP.MarketData(D, {"U": s}, {"USD": FP.FlatCurve(0.03, D)}, vols={"U": FP.FlatVol(0.2)})


def agg(limits=None):
    h = RT.Hierarchy({"firm": None, "a": "firm", "b": "firm", "a1": "a", "b1": "b"})
    return RT.Aggregator(h, RT.SensitivityCache(md(100.0), "U", 0.01), limits or {})


def full_delta_dollars(a, spot):
    total = 0.0
    for _book, inst, qty in a.trades.values():
        g = 1.0 if isinstance(inst, RT.Future) else FP.greeks(inst, md(spot), which=("delta",))["delta"]
        total += g * qty * spot
    return total


def test_hierarchy_and_incremental_sums():
    a = agg()
    assert a.h.ancestors("a1") == ["a1", "a", "firm"]
    a.on_fill(0, "a1", "P", PUT, 100)
    a.on_fill(1, "b1", "F", FUT, -30)
    a.on_fill(2, "a1", "P", PUT, 50)
    assert a.exposure("firm") == pytest.approx(a.exposure("a") + a.exposure("b"))
    assert a.exposure("b") == pytest.approx(-3000.0) and a.trades["P"][2] == 150
    assert a.exposure("firm") == pytest.approx(full_delta_dollars(a, 100.0))


def test_ticks_carry_gamma_and_refresh_past_threshold():
    a = agg()
    a.on_fill(0, "a1", "P", PUT, 100)
    a.on_tick(1, md(100.5))                                     # inside the threshold: cached delta + gamma dS
    assert a.cache.refreshes == 0
    assert a.exposure("firm") == pytest.approx(full_delta_dollars(a, 100.5), rel=2e-3)
    a.on_tick(2, md(102.0))                                     # beyond it: repriced
    assert a.cache.refreshes == 1 and a.cache.asof_spot == 102.0
    assert a.exposure("firm") == pytest.approx(full_delta_dollars(a, 102.0), rel=1e-9)
    snap = a.snapshot(10)
    assert snap.cache_age == 8 and snap.spot == snap.cache_spot == 102.0


def test_limits_and_what_if():
    a = agg({"firm": 5000.0, "a": 4000.0, "b": 4000.0})
    a.on_fill(0, "b1", "F", FUT, -35)
    after, breached = a.what_if("a1", FUT, -30)
    assert breached == ["firm"] and after["a"] == pytest.approx(-3000.0) and a.exposure("a") == 0.0
    a.on_fill(1, "a1", "F2", RT.Future("F2", "U"), -30)
    assert [x[1] for x in a.alerts] == ["firm"] and a.snapshot(2).breaches == ["firm"]


def test_pnl_approximation():
    g = RT.SensitivityCache(md(100.0), "U").greeks(PUT)
    small = RT.delta_gamma_pnl(g, 10, 100.0, 101.0)
    full = RT.full_pnl(PUT, 10, md(100.0), md(101.0))
    assert small == pytest.approx(full, rel=0.01)
    assert RT.full_pnl(FUT, 5, md(100.0), md(103.0)) == 15.0
