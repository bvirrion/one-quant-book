import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_riskmodel import (
    bias_band,
    bias_stat,
    cs_regression,
    ewma_cov,
    factor_returns,
    pca_model,
    portfolio_risk,
    specific_var,
    vra,
)


def test_constrained_regression_recovers_factors():
    rng = np.random.default_rng(0)
    M, n_ind = 600, 4
    ind = rng.integers(0, n_ind, M)
    cap = rng.lognormal(0, 1, M)
    X = np.column_stack([np.ones(M), np.eye(n_ind)[ind], rng.standard_normal(M)])
    cw = np.array([cap[ind == k].sum() for k in range(n_ind)])
    f_ind = rng.standard_normal(n_ind)
    f_ind -= cw @ f_ind / cw.sum()                                        # truth satisfies the constraint
    f = np.r_[0.01, f_ind * 0.01, 0.004]
    r = X @ f + 0.001 * rng.standard_normal(M)
    C = np.r_[0.0, cw, 0.0][None, :]
    est, e = cs_regression(r, X, np.sqrt(cap), C)
    assert np.allclose(est, f, atol=3e-4) and abs(C @ est).max() < 1e-12
    r2 = r.copy()
    r2[:5] = np.nan
    _, e2 = cs_regression(r2, X, np.sqrt(cap), C)
    assert np.isnan(e2[:5]).all() and np.isfinite(e2[5:]).all()


def test_factor_returns_ewma_vra_and_risk():
    rng = np.random.default_rng(1)
    T, M, K = 400, 300, 3
    X = rng.standard_normal((M, K))
    vol = np.r_[np.full(200, 0.01), np.full(200, 0.03)]                  # a volatility regime shift
    Ftrue = vol[:, None] * rng.standard_normal((T, K))
    R = Ftrue @ X.T + 0.02 * rng.standard_normal((T, M))
    F, E = factor_returns(R, lambda t: X, np.ones((T, M)))
    assert np.corrcoef(F[:, 0], Ftrue[:, 0])[0, 1] > 0.99
    covs = ewma_cov(F, half_life=60)
    lam2 = vra(F, covs, half_life=10)
    assert lam2[205:215].mean() > 2.0 and abs(lam2[150:200].mean() - 1) < 0.3   # the shift is caught early
    assert ewma_cov(F, 60, nw_lags=2).shape == (T, K, K)
    spec = specific_var(E, half_life=60)
    assert abs(np.sqrt(np.nanmean(spec[-1])) - 0.02) < 0.002
    w = rng.standard_normal(M) / M
    risk = portfolio_risk(w, X, covs[-1], spec[-1])
    assert abs(risk["contrib"].sum() - risk["factor"]) < 1e-15 and risk["total"] > risk["factor"]


def test_shrinkage_pca_and_bias():
    rng = np.random.default_rng(2)
    E = rng.standard_normal((300, 50)) * np.linspace(0.01, 0.03, 50)
    raw = specific_var(E, 30)
    sh = specific_var(E, 30, groups=np.zeros(50, int), shrink=0.5)
    assert np.nanstd(np.sqrt(sh[-1])) < np.nanstd(np.sqrt(raw[-1]))
    B = rng.standard_normal((80, 2))
    R = rng.standard_normal((500, 2)) @ B.T * 0.02 + 0.005 * rng.standard_normal((500, 80))
    Bh, Fc, sp = pca_model(R, 2)
    assert Bh.shape == (80, 2) and np.allclose(Bh.T @ Bh, np.eye(2)) and np.median(np.sqrt(sp)) < 0.007
    z = rng.standard_normal(2000)
    assert abs(bias_stat(z, 1.0) - 1) < 0.05 and abs(bias_stat(z, 0.5) - 2) < 0.1
    lo, hi = bias_band(200)
    assert abs(hi - 1.1) < 1e-12 and abs(lo - 0.9) < 1e-12
