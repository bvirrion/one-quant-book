import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_pairsel import (  # noqa: E402
    bh,
    copula_fit,
    copula_h,
    eg_null,
    eg_tau,
    normalise,
    pvalue,
    top_pairs,
    trade_pair,
    twin,
)


def test_distance_pairs():
    rng = np.random.default_rng(0)
    base = np.cumprod(1 + 0.01 * rng.standard_normal((250, 3)), axis=0)
    P = np.column_stack([base, base[:, 0] * 1.001, base[:, 1] * (1 + 0.001 * rng.standard_normal(250))])
    pairs = top_pairs(normalise(P), 2)
    assert {(a, b) for a, b, _ in pairs} == {(0, 3), (1, 4)}


def test_eg_null_size_and_power():
    null = eg_null(252, 20000, 4)
    assert -3.5 < np.quantile(null, 0.05) < -3.2                    # MacKinnon's 5% value for N = 2 is about -3.37
    rng = np.random.default_rng(1)
    x = np.cumsum(rng.standard_normal((252, 2000)), axis=0)
    u = np.zeros((252, 2000))
    for t in range(1, 252):
        u[t] = 0.8 * u[t - 1] + rng.standard_normal(2000)
    p = pvalue(eg_tau(x + u, x), null)
    assert (p < 0.05).mean() > 0.95
    y = np.cumsum(rng.standard_normal((252, 2000)), axis=0)
    assert abs((pvalue(eg_tau(y, x), null) < 0.05).mean() - 0.05) < 0.015


def test_bh():
    p = np.array([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216])
    assert bh(p, 0.05).tolist() == [True, True] + [False] * 8


def test_trade_pair_by_hand():
    spread = np.array([0.0, 0.3, 0.1, -0.1, 0.0])
    ra = np.array([0.0, 0.0, -0.02, 0.01, 0.0])
    rb = np.array([0.0, 0.0, 0.01, 0.0, 0.0])
    pnl, trades, opened, end = trade_pair(ra, rb, spread, 0.1, 2.0, cost=0.001)
    # opens at t = 1 short a / long b: day 2 earns 0.02 + 0.01; closes at t = 3 (sign change)
    assert opened == 1 and trades == 2 and end == 0
    assert abs(pnl[1] + 0.002) < 1e-12 and abs(pnl[2] - 0.03) < 1e-12
    assert abs(pnl[3] - (-0.98 * 0.01 - 0.001 * (0.98 * 1.01 + 1.01))) < 1e-12


def test_copula_and_twin():
    rng = np.random.default_rng(2)
    z = rng.standard_normal((2000, 2)) @ np.linalg.cholesky([[1, 0.6], [0.6, 1]]).T
    fit = copula_fit(z[:, 0], z[:, 1])
    assert abs(fit["rho"] - 0.6) < 0.05
    h = copula_h(fit, np.array([2.0, -2.0]), np.array([0.0, 0.0]))
    assert h[0] > 0.9 and h[1] < 0.1
    X = rng.standard_normal((500, 3))
    assert np.allclose(twin(X @ np.array([0.5, 0.3, 0.2]), X, 1e-9), [0.5, 0.3, 0.2])


def test_inverse_normal():
    from firm_pairsel import _ncdf, _ninv
    u = np.array([1e-6, 0.01, 0.2, 0.5, 0.8, 0.99, 1 - 1e-6])
    assert np.allclose(_ncdf(_ninv(u)), u, rtol=1e-6)
