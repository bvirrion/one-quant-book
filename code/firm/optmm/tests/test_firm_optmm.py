"""Acceptance tests of the Book 5, Chapter 26 build (options quoting engine)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_optmm import (
    Bucket,
    Option,
    SkewSurface,
    best_play,
    dividend_play,
    hedge_paths,
    optimal_width,
    quote,
    should_exercise,
    theo,
    vega_by_bucket,
    width_profit,
)

FLAT = SkewSurface(lambda tau: 0.2)


def test_width_model():
    assert abs(optimal_width(0.5, 20.0, 0.3, 0.0) - 0.3) < 1e-7          # w exp(-w / w_s) peaks at w_s
    w = [optimal_width(0.5, 20.0, 0.3, li) for li in (2.0, 10.0)]
    assert 0.3 < w[0] < w[1]
    assert width_profit(0.0, 0.5, 20.0, 0.3, 0.0) == 0.0 and width_profit(0.3, 0.5, 20.0, 0.3, 5.0) < width_profit(0.3, 0.5, 20.0, 0.3, 0.0)


def test_dividend_play():
    r = dividend_play(10_000, 0.3, 1e12, 48.0, 0.0, 0.0)
    assert abs(r["unassigned"] - 3000) < 1e-3                             # an infinite trade captures every failure
    assert dividend_play(10_000, 0.0, 5_000, 48.0, 0.1, 0.05)["net"] < 0  # nothing to capture: only fees
    q, best = best_play(10_000, 0.3, 48.0, 0.10, 0.05)
    for dq in (-100, 100):
        assert dividend_play(10_000, 0.3, q + dq, 48.0, 0.10, 0.05)["net"] < best["net"]
    assert should_exercise(0.50, 0.02) and not should_exercise(0.02, 0.50)


def test_quotes_and_limits():
    o = Option(100.0, 0.25, "C")
    value, vega = theo(o, 100.0, 0.0, FLAT)
    bid, ask = quote(o, 100.0, 0.0, FLAT, 0.4, 0.0, 1000.0)
    assert math.isclose(ask - value, value - bid) and math.isclose(ask - bid, 0.8 * vega)
    b2, a2 = quote(o, 100.0, 0.0, FLAT, 0.4, 500.0, 1000.0)               # long vega: both quotes lower
    assert b2 < bid and a2 < ask
    b3, a3 = quote(o, 100.0, 0.0, FLAT, 0.4, 1000.0, 1000.0)
    assert math.isnan(b3) and not math.isnan(a3)
    buckets = (Bucket("1m", 0.0, 0.125, 1.0), Bucket("3m", 0.125, 0.375, 1.0))
    book = [Option(100.0, 1 / 12, "C", 2.0), Option(100.0, 0.25, "P", -1.0)]
    v = vega_by_bucket(book, 100.0, 0.0, FLAT, buckets)
    assert math.isclose(v["1m"], 2 * theo(book[0], 100.0, 0.0, FLAT)[1]) and v["3m"] < 0


def test_hedging_policies():
    rng = np.random.default_rng(2)
    n, steps, dt = 500, 21 * 13, 1 / 252 / 13
    z = rng.standard_normal((n, steps))
    paths = np.column_stack([np.full(n, 100.0), 100 * np.exp(np.cumsum(-0.02 * dt + 0.2 * math.sqrt(dt) * z, axis=1))])
    book = [Option(100.0, 21 / 252, "C", -1.0), Option(100.0, 21 / 252, "P", -1.0)]
    fine = hedge_paths(paths, book, 0.2, dt, 0.0, every=1)
    none = hedge_paths(paths, book, 0.2, dt, 0.0005, band=1e6)
    assert fine["pnl"].std() < 0.35 and abs(fine["pnl"].mean()) < 0.1 and none["trades"].mean() < 10 < fine["trades"].mean()
    tight, wide = (hedge_paths(paths, book, 0.2, dt, 0.0005, band=c) for c in (0.25, 4.0))
    assert tight["costs"].mean() > wide["costs"].mean() and tight["pnl"].std() < wide["pnl"].std()
