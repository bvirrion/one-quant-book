"""Acceptance tests of firm.tradeflow."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_tradeflow import (
    aggregate_orders,
    bvc,
    hurst_aggvar,
    kyle_lambda,
    lee_ready,
    markout_toxicity,
    quote_rule,
    sign_acf,
    tick_rule,
    vpin,
)


def test_signing_rules():
    p = np.array([10.00, 10.01, 10.01, 10.00, 10.005])
    assert list(tick_rule(p)) == [0, 1, 1, -1, 1]
    bid, ask = np.full(5, 10.00), np.full(5, 10.01)
    assert list(quote_rule(p, bid, ask)) == [-1, 1, 1, -1, 0]
    assert list(lee_ready(p, bid, ask)) == [-1, 1, 1, -1, 1]
    f = bvc([0.0, 1.0, -1.0], [100, 100, 100], 1.0)
    assert np.isclose(f[0], 0.5) and np.isclose(f[1], 0.8413, atol=1e-4) and np.isclose(f[1] + f[2], 1.0)


def test_vpin_and_buckets():
    v = np.full(10, 50.0)
    buys = np.where(np.arange(10) < 5, 50.0, 0.0)          # five buys then five sells
    x = vpin(buys, v, 100.0, 1)
    assert list(x) == [1.0, 1.0, 1.0, 1.0, 1.0] or np.allclose(x, [1.0, 1.0, 0.0, 1.0, 1.0])
    y = vpin(np.full(10, 25.0), v, 100.0, 2)                # every trade half buy: balanced
    assert np.isnan(y[0]) and np.allclose(y[1:], 0.0)


def test_memory_and_hurst():
    rng = np.random.default_rng(0)
    assert abs(hurst_aggvar(rng.normal(size=100_000)) - 0.5) < 0.03
    s = np.repeat(rng.choice([-1, 1], 10_000), 5)           # runs of five equal signs
    acf = sign_acf(s, [1, 4, 5, 10])
    assert acf[0] > 0.7 and acf[1] > 0.15 and abs(acf[3]) < 0.03


def test_lambda_markout_orders():
    rng = np.random.default_rng(1)
    x = rng.normal(size=2000)
    k = kyle_lambda(0.3 * x + rng.normal(0, 0.1, 2000), x)
    assert abs(k["lambda"] - 0.3) < 0.01 and k["r2"] > 0.8
    assert np.isclose(markout_toxicity([1, -1], [10.0, 10.0], [10.2, 9.9]), 0.15)
    t, q, s = aggregate_orders([1, 1, 2, 3, 3, 3], [0.1, 0.1, 0.5, 0.9, 0.9, 0.9], [100, 50, 200, 10, 20, 30], [1, 1, -1, 1, 1, 1])
    assert list(t) == [0.1, 0.5, 0.9] and list(q) == [150, 200, 60] and list(s) == [1, -1, 1]
