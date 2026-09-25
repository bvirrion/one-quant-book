import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_allocation import (
    black_litterman,
    erc,
    gp_aim,
    gp_trade_rate,
    hrp,
    implied_returns,
    mean_variance,
    risk_budget,
    risk_contributions,
    robust_mv,
)


def _cov(n=12, seed=0):
    rng = np.random.default_rng(seed)
    B = rng.standard_normal((n, 3)) * 0.1
    return B @ B.T + np.diag(rng.uniform(0.01, 0.05, n))


def test_mean_variance_and_robust():
    S = _cov()
    alpha = np.random.default_rng(1).normal(0.05, 0.03, 12)
    w = mean_variance(alpha, S, 5.0, lo=-10, hi=10, budget=1.0)
    ones = np.ones(12)
    Si = np.linalg.inv(S)
    lam = (ones @ Si @ alpha - 5.0) / (ones @ Si @ ones)                   # closed form with the budget only
    assert np.allclose(w, Si @ (alpha - lam) / 5.0, atol=1e-7)
    Om = np.diag(np.full(12, 0.03**2))
    wl = mean_variance(alpha, S, 5.0)
    wr = robust_mv(alpha, S, Om, kappa=1.0, gamma=5.0)
    obj = lambda x: alpha @ x - np.sqrt(x @ Om @ x) - 2.5 * x @ S @ x  # noqa: E731
    assert obj(wr) >= obj(wl) - 1e-10 and (wr**2).sum() < (wl**2).sum()   # more diversified
    assert np.allclose(robust_mv(alpha, S, Om, kappa=0.0, gamma=5.0), wl, atol=1e-7)


def test_black_litterman():
    S = _cov()
    w_mkt = np.full(12, 1 / 12)
    pi = implied_returns(S, w_mkt, 3.0)
    assert np.allclose(mean_variance(pi, S, 3.0, lo=-10, hi=10, budget=None), w_mkt, atol=1e-7)
    P = np.zeros((1, 12))
    P[0, 0], P[0, 1] = 1.0, -1.0
    mu, post = black_litterman(pi, S, P, [0.05], np.array([[1e-10]]))
    assert abs((P @ mu)[0] - 0.05) < 1e-6                                # a certain view is met
    mu2, _ = black_litterman(pi, S, P, [0.05], np.array([[1e6]]))
    assert np.allclose(mu2, pi, atol=1e-6) and post.shape == (12, 12)    # a worthless view changes nothing


def test_risk_budgets_and_hrp():
    S = _cov()
    w = erc(S)
    assert np.allclose(risk_contributions(w, S), 1 / 12, atol=1e-9) and abs(w.sum() - 1) < 1e-12
    b = np.linspace(1, 2, 12)
    b /= b.sum()
    assert np.allclose(risk_contributions(risk_budget(S, b), S), b, atol=1e-9)
    D = np.diag([0.01, 0.04, 0.02, 0.09])
    ivp = (1 / np.diag(D)) / (1 / np.diag(D)).sum()
    assert np.allclose(hrp(D), ivp) and np.allclose(erc(D), (1 / np.sqrt(np.diag(D))) / (1 / np.sqrt(np.diag(D))).sum())
    blocks = np.kron(np.eye(2), np.full((3, 3), 0.8)) + 0.2 * np.eye(6)
    h = hrp(blocks * 0.04)
    assert np.allclose([h[:3].sum(), h[3:].sum()], 0.5)                   # the two clusters split the book evenly
    assert abs(h[0] - 0.5 * (1 - 0.04 / (0.04 + 0.036))) < 1e-12          # then bisection by position: {0} | {1, 2}
    assert np.all(hrp(S) > 0) and abs(hrp(S).sum() - 1) < 1e-12


def test_garleanu_pedersen():
    assert 0 < gp_trade_rate(1e-2, 1.0, 1e-3) < 1
    assert gp_trade_rate(1e-2, 1e-8, 1e-3) > 0.999                      # free trading: jump to the aim
    assert gp_trade_rate(1e-2, 10.0, 1e-3) < gp_trade_rate(1e-2, 1.0, 1e-3)
    S = _cov(4)
    f = np.array([0.01, -0.02, 0.0, 0.03])
    assert np.allclose(gp_aim(S, [f], [0.0], 2.0, 0.5), np.linalg.solve(2.0 * S, f))
    fast = gp_aim(S, [f], [1.0], 2.0, 0.5)
    assert np.allclose(fast, np.linalg.solve(2.0 * S, f) / 1.25)          # a fast signal is down-weighted
