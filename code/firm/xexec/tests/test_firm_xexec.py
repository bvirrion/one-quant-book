import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_xexec import (  # noqa: E402
    LP,
    Market,
    Quote,
    amm_cost_bp,
    cex_amm_split,
    children,
    fx_child,
    orders_allowed,
    rfq,
    roll,
    sqrt_impact_bp,
)


def test_roll_and_children():
    f, b = Quote(499_975, 150, 500_000, 120), Quote(501_000, 80, 501_025, 100)
    r = roll(f, b, Quote(-1025, 60, -1000, 60), 200, 25)
    assert r["mid"] == -1025.0 and r["legs"] == 43.75 and r["spread_book"] == 22.5 and r["implied"] == 22.5
    thin = roll(f, b, Quote(None, 0, None, 0), 50, 25)
    assert thin["implied"] == thin["legs"] == 25.0            # implied-in trades at the legging price, atomically
    import sys as _s
    _s.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "acexec"))
    from firm_acexec import LinearScheduler
    q = children(100.0, LinearScheduler(1.0, 1.0), 4)
    assert np.allclose(q, 25.0)
    assert np.isclose(sqrt_impact_bp(Market("m", 1.0, 100.0, 1e6), 1e4), 7.0)


def test_fx_streams():
    rng = np.random.default_rng(0)
    assert fx_child([LP("firm", 0.2, 0, 0, "none")], 0.01, rng) == (0.2, 0)
    picky = LP("picky", 0.05, 100, -1e9)                      # rejects everything
    c, n = fx_child([picky, LP("firm", 0.2, 0, 0, "none")], 0.01, rng)
    assert n == 1 and c != 0.2
    costs = [fx_child([LP("a", 0.1, 100, 0.0), LP("firm", 0.3, 0, 0, "none")], 0.01, rng)[0] for _ in range(20000)]
    # asymmetric last look with a zero threshold: half rejected, each costing a favourable move of mean s phi(0)/0.5
    s = 0.01 * 10
    assert abs(np.mean(costs) - (0.5 * 0.1 + 0.5 * 0.3 + s / np.sqrt(2 * np.pi))) < 0.005


def test_rfq_amm_split_and_limits():
    r = rfq(3, 40.0, 8.0, 1.5)
    assert np.isclose(r["total"], r["markup"] + r["competition"] + r["leakage"]) and r["leakage"] == 3.0
    assert abs(amm_cost_bp(1_000.0, 1e9, 1e9, 30) - 30.0) < 0.2       # a small trade pays the fee
    m = Market("x", 0.5, 300.0, 5e9)
    s = cex_amm_split(5e7, m, 1e9, 1e9, 5)
    assert 0 < s["x"] < 5e7 and s["saving"] > 0
    import sys as _s
    _s.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "ratelimit"))
    from firm_ratelimit import binance_like
    assert orders_allowed(binance_like(), 10_000, 100) and not orders_allowed(binance_like(), 10_000, 101)
