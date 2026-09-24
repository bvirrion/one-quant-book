"""Acceptance tests of firm.linreg."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_linreg import elastic_net, fama_macbeth, ols, ridge, time_series_folds, tls, vif


def test_ols_and_standard_errors():
    rng = np.random.default_rng(1)
    n = 4000
    x = rng.standard_normal(n)
    X = np.column_stack([np.ones(n), x])
    y = 1 + 2 * x + rng.standard_normal(n) * (1 + np.abs(x))          # heteroskedastic
    f = ols(X, y)
    assert np.allclose(f["beta"], np.linalg.lstsq(X, y, rcond=None)[0])
    assert abs(f["leverage"].sum() - 2) < 1e-9                         # trace of the hat matrix = k
    hc = ols(X, y, cov="hc")["se"][1]
    sims = []
    for _ in range(300):
        yy = 1 + 2 * x + rng.standard_normal(n) * (1 + np.abs(x))
        sims.append(np.linalg.lstsq(X, yy, rcond=None)[0][1])
    assert abs(hc / np.std(sims) - 1) < 0.12 and f["se"][1] < 0.85 * np.std(sims)


def test_frisch_waugh_lovell():
    rng = np.random.default_rng(2)
    n = 500
    z = rng.standard_normal((n, 3))
    x = z @ [0.5, -0.2, 0.3] + rng.standard_normal(n)
    y = 1.5 * x + z @ [1, 2, 3] + rng.standard_normal(n)
    full = ols(np.column_stack([np.ones(n), z, x]), y)["beta"][-1]
    Z = np.column_stack([np.ones(n), z])
    rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
    ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
    assert abs(full - (rx @ ry) / (rx @ rx)) < 1e-10


def test_vif_ridge_and_lasso():
    rng = np.random.default_rng(3)
    n, rho = 20_000, 0.97
    a = rng.standard_normal(n)
    b = rho * a + math.sqrt(1 - rho**2) * rng.standard_normal(n)
    v = vif(np.column_stack([a, b, rng.standard_normal(n)]))
    assert abs(v[0] - 1 / (1 - rho**2)) < 1.0 and abs(v[2] - 1) < 0.01
    X = rng.standard_normal((200, 5))
    y = X @ [1, 0, 0, 2, 0] + rng.standard_normal(200)
    assert np.allclose(ridge(X, y, 0.0), np.linalg.lstsq(X, y, rcond=None)[0])
    assert np.allclose(ridge(X, y, 3.0), np.linalg.solve(X.T @ X + 3 * np.eye(5), X.T @ y))
    assert np.allclose(elastic_net(X, y, 3.0 / 200, alpha=0.0), ridge(X, y, 3.0), atol=1e-7)
    bl = elastic_net(X, y, 0.3)
    assert bl[1] == 0 and bl[2] == 0 and bl[4] == 0 and bl[3] > 1.5          # lasso zeroes the irrelevant ones
    Xo = np.linalg.qr(rng.standard_normal((200, 5)))[0] * math.sqrt(200)     # orthonormal design: soft thresholding
    yo = Xo @ [1, -0.5, 0.2, 0, 0] + 0.1 * rng.standard_normal(200)
    ls = Xo.T @ yo / 200
    assert np.allclose(elastic_net(Xo, yo, 0.3), np.sign(ls) * np.maximum(np.abs(ls) - 0.3, 0), atol=1e-8)


def test_folds_and_fama_macbeth_and_tls():
    folds = time_series_folds(1200, 5, purge=5)
    assert len(folds) == 5 and all(tr.max() + 5 < te.min() for tr, te in folds)
    rng = np.random.default_rng(4)
    ys, Xs = [], []
    for _ in range(120):
        x = rng.standard_normal(50)
        Xs.append(np.column_stack([np.ones(50), x]))
        ys.append(0.3 * x + rng.standard_normal(50))
    fm = fama_macbeth(ys, Xs, lags=2)
    assert abs(fm["beta"][1] - 0.3) < 4 * fm["se"][1] and abs(fm["se"][1] - 1 / math.sqrt(50 * 120)) < 0.004
    x = rng.standard_normal(100_000)
    x2 = x + 0.5 * rng.standard_normal(100_000)
    y2 = x + 0.5 * rng.standard_normal(100_000)
    assert abs(tls(x2, y2) - 1) < 0.02                                     # equal error variances: TLS unbiased
