"""Acceptance tests of firm.volfcst."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_volfcst import (
    diebold_mariano,
    ewma,
    garch_filter,
    garch_fit,
    garch_forecast,
    har_fit,
    mincer_zarnowitz,
    qlike,
    rolling_var,
)


def _sim_garch(n, omega, alpha, beta, rng, nu=None):
    h, r = omega / (1 - alpha - beta), np.empty(n)
    for t in range(n):
        z = rng.standard_normal() if nu is None else rng.standard_t(nu) / math.sqrt(nu / (nu - 2))
        r[t] = math.sqrt(h) * z
        h = omega + alpha * r[t] ** 2 + beta * h
    return r


def test_garch_recovers_parameters():
    rng = np.random.default_rng(1)
    r = _sim_garch(8000, 0.05, 0.08, 0.9, rng)
    f = garch_fit(r)
    assert abs(f["alpha"] - 0.08) < 3 * f["se"][1] + 0.005 and abs(f["beta"] - 0.9) < 3 * f["se"][2] + 0.005
    assert abs(f["half_life"] - math.log(0.5) / math.log(f["alpha"] + f["beta"])) < 1e-9
    ft = garch_fit(_sim_garch(8000, 0.05, 0.08, 0.9, rng, nu=6), "t")
    assert abs(ft["nu"] - 6) < 3 * ft["se"][-1] + 0.5


def test_filter_forecast_ewma_window():
    r = np.array([1.0, -2.0, 0.5])
    h = garch_filter(r, 0.1, 0.1, 0.8, h0=1.0)
    assert abs(h[1] - (0.1 + 0.1 + 0.8)) < 1e-12 and abs(h[2] - (0.1 + 0.4 + 0.8 * h[1])) < 1e-12
    g = garch_filter(r, 0.1, 0.1, 0.8, gamma=0.2, h0=1.0)
    assert abs(g[2] - (0.1 + 0.3 * 4 + 0.8 * g[1])) < 1e-12                  # GJR: extra weight on the negative return
    fit = {"h": np.array([4.0]), "persistence": 0.9, "uncond_var": 1.0}
    fc = garch_forecast(fit, 3)
    assert np.allclose(fc, [4.0, 1 + 0.9 * 3, 1 + 0.81 * 3])
    e = ewma(r, 0.94, h0=1.0)
    assert abs(e[1] - (0.94 + 0.06)) < 1e-12 and abs(e[2] - (0.94 * e[1] + 0.06 * 4)) < 1e-12
    x = np.random.default_rng(2).standard_normal(300)
    w = rolling_var(x, 250)
    assert np.isnan(w[249]) and abs(w[250] - x[:250].var(ddof=1)) < 1e-12 and abs(w[300] - x[50:300].var(ddof=1)) < 1e-12


def test_losses_and_tests():
    rng = np.random.default_rng(3)
    h = np.exp(rng.normal(0, 0.5, 20_000))
    y = h * rng.standard_normal(20_000) ** 2                                  # unbiased noisy proxy
    assert np.mean(qlike(y, h)) < np.mean(qlike(y, 1.3 * h)) and np.mean(qlike(y, h)) < np.mean(qlike(y, 0.7 * h))
    a, b, _ = mincer_zarnowitz(y, h)
    assert abs(a) < 0.1 and abs(b - 1) < 0.1
    l1, l2 = rng.standard_normal(5000), rng.standard_normal(5000)
    stat, p = diebold_mariano(l1, l2)
    assert abs(stat) < 3 and 0 <= p <= 1
    stat2, p2 = diebold_mariano(l1 - 0.2, l2)
    assert stat2 < -5 and p2 < 1e-6


def test_har():
    rng = np.random.default_rng(4)
    rv = np.empty(6000)
    rv[:22] = 1.0
    for t in range(22, 6000):
        rv[t] = 0.1 + 0.4 * rv[t - 1] + 0.3 * rv[t - 5: t].mean() + 0.2 * rv[t - 22: t].mean() + 0.1 * rng.standard_normal()
    f = har_fit(rv)
    assert np.allclose(f["beta"], [0.1, 0.4, 0.3, 0.2], atol=0.05)
