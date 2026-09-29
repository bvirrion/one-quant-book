"""Numbers gate: every numerical answer printed in Book 18, chapter 16 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import sympy as sp

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_stoch import (
    both_positive,
    digital_prices,
    exit_prob_up,
    gbm_mean_median,
    ito_drift,
    max_tail,
    simulate_max_tail,
)

W = sp.Symbol("w")


def test_q1_q2_ito():
    assert ito_drift(W**2, W) == 1
    assert ito_drift(W**3, W) == 3 * W
    t, s = sp.symbols("t sigma", positive=True)
    f = sp.exp(s * W - s**2 * t / 2)
    assert sp.simplify(sp.diff(f, t) + sp.Rational(1, 2) * sp.diff(f, W, 2)) == 0  # driftless


def test_q3_both_positive():
    assert math.isclose(both_positive(), 3 / 8)
    rng = np.random.default_rng(0)
    w1 = rng.standard_normal(400_000)
    w2 = w1 + rng.standard_normal(400_000)
    assert abs(np.mean((w1 > 0) & (w2 > 0)) - 0.375) < 0.003


def test_q4_integral_of_w():
    rng = np.random.default_rng(1)
    n, paths, t = 500, 20_000, 1.0
    dw = rng.standard_normal((paths, n)) * math.sqrt(t / n)
    w = np.cumsum(dw, axis=1)
    integral = w.sum(axis=1) * (t / n)
    assert abs(integral.var() - 1 / 3) < 0.015


def test_q5_exit():
    assert math.isclose(exit_prob_up(1, 2), 2 / 3) and 1 * 2 == 2


def test_q6_exit_with_drift():
    p = exit_prob_up(1, 1, 0.5)
    assert round(p, 3) == 0.731
    assert math.isclose(p, 1 / (1 + math.exp(-1)))


def test_q7_max():
    assert round(max_tail(1), 4) == 0.3173
    # discrete monitoring underestimates; dividing the step by 16 moves the estimate towards the exact value
    coarse = simulate_max_tail(1.0, 50, 20_000, 21)
    fine = simulate_max_tail(1.0, 800, 20_000, 22)
    assert coarse < fine < max_tail(1) + 0.01


def test_q8_gbm():
    mean, median = gbm_mean_median(0.08, 0.4, 10)
    assert round(mean, 2) == 2.23 and round(median, 2) == 1.0


def test_q9_girsanov():
    assert round((0.08 - 0.03) / 0.2, 2) == 0.25


def test_q10_digitals():
    cash, asset = digital_prices(100, 100, 0.2, 1)
    assert round(cash, 4) == 0.4602 and round(asset, 2) == 53.98
    # call = asset-or-nothing - K * cash-or-nothing
    assert round(asset - 100 * cash, 2) == 7.97


def test_q11_feynman_kac():
    x, t, big_t = sp.symbols("x t T")
    u = x**2 + (big_t - t)
    assert sp.simplify(sp.diff(u, t) + sp.Rational(1, 2) * sp.diff(u, x, 2)) == 0 and u.subs(t, big_t) == x**2


def test_q13_optional_stopping():
    for b in (1, 2, 5):
        assert math.isclose(exit_prob_up(1, b), b / (1 + b))


def test_q7_bridge_correction():
    rng = np.random.default_rng(5)
    n, paths, a = 50, 40_000, 1.0
    dt = 1.0 / n
    x = np.zeros(paths)
    hit = np.zeros(paths, dtype=bool)
    for _ in range(n):
        y = x + math.sqrt(dt) * rng.standard_normal(paths)
        p = np.exp(-2 * np.maximum(a - x, 0) * np.maximum(a - y, 0) / dt)
        hit |= (y >= a) | (rng.random(paths) < p)
        x = y
    assert abs(hit.mean() - max_tail(1)) < 0.006


def test_q9_q12_numbers():
    assert 0.25**2 / 2 == 0.03125
    rng = np.random.default_rng(6)
    mu, dt, paths = 1.0, 0.002, 20_000
    x = np.zeros(paths)
    t = np.zeros(paths)
    alive = np.ones(paths, dtype=bool)
    while alive.any():
        k = alive.sum()
        x[alive] += mu * dt + math.sqrt(dt) * rng.standard_normal(k)
        t[alive] += dt
        alive &= x < 1
    assert abs(t.mean() - 1 / mu) < 0.05


def test_worked_answers():
    assert round(math.log(2) / 0.1, 1) == 6.9 and round(1 / (2 * 0.1), 6) == 5 and round(math.sqrt(5), 2) == 2.24
    assert round(2 * math.sqrt(5), 1) == 4.5
    rng = np.random.default_rng(16)
    n, steps, dt = 4000, 3000, 0.1
    x = np.zeros(n)
    for _ in range(steps):
        x += -0.1 * x * dt + math.sqrt(dt) * rng.standard_normal(n)
    assert abs(x.std() - math.sqrt(5)) < 0.1
    p = 2 / math.pi * math.asin(math.sqrt(0.1))
    assert round(p, 2) == 0.20
    w = np.cumsum(rng.standard_normal((20_000, 1000)), axis=1)
    frac = (w > 0).mean(axis=1)
    assert abs((frac <= 0.1).mean() - p) < 0.015 and abs((frac >= 0.9).mean() - p) < 0.015
