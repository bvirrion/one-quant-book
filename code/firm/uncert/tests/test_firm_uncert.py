import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_uncert import (
    MDN,
    GaussNet,
    adaptive_conformal,
    crps_gaussian,
    crps_quantiles,
    fit_nll,
    mdn_quantile,
    pinball,
    predict_gauss,
    predict_mdn,
    split_conformal,
)


def test_pinball_minimised_at_the_quantile():
    y = np.random.default_rng(0).standard_normal(20000)
    grid = np.linspace(1.0, 2.2, 61)
    best = grid[np.argmin([pinball(y, q, 0.95) for q in grid])]
    assert abs(best - np.quantile(y, 0.95)) < 0.03


def test_crps_forms_agree():
    from scipy.stats import norm

    rng = np.random.default_rng(1)
    y = rng.standard_normal(5000)
    alphas = np.linspace(0.005, 0.995, 199)
    Q = np.tile(norm.ppf(alphas), (len(y), 1))
    assert abs(crps_gaussian(y, 0.0, 1.0) - crps_quantiles(y, Q, alphas)) < 0.01


def test_split_conformal_covers_on_exchangeable_data():
    rng = np.random.default_rng(2)
    covered = []
    for _ in range(300):
        s = np.abs(rng.standard_normal(101))
        covered.append(s[100] <= split_conformal(s[:100], 0.1))
    assert np.mean(covered) >= 0.87


def test_adaptive_conformal_recovers_after_a_scale_change():
    rng = np.random.default_rng(3)
    s = np.abs(np.r_[rng.standard_normal(3000), 2.0 * rng.standard_normal(3000)])
    th, err = adaptive_conformal(s, 0.1, gamma=0.01, window=500)
    assert abs(1 - err[4000:].mean() - 0.9) < 0.03


def test_networks_recover_planted_distributions():
    rng = np.random.default_rng(4)
    X = rng.uniform(-1, 1, (6000, 2)).astype(np.float32)
    y = 0.5 * X[:, 0] + (0.2 + 0.8 * (X[:, 1] > 0)) * rng.standard_normal(6000)
    g = fit_nll(GaussNet(2, (16,)), X[:5000], y[:5000], X[5000:], y[5000:], epochs=60, patience=8)
    _, s = predict_gauss(g, np.array([[0.0, -0.5], [0.0, 0.5]], np.float32))
    assert s[0] < 0.4 < 0.7 < s[1]
    z = np.where(rng.random(6000) < 0.5, -2.0, 2.0) + 0.3 * rng.standard_normal(6000)
    mdn = fit_nll(MDN(2, K=2, hidden=(16,)), X[:5000], z[:5000], X[5000:], z[5000:], epochs=60, patience=8)
    w, mu, sd = predict_mdn(mdn, X[:5])
    assert np.all(np.abs(np.sort(mu, axis=1) - [-2.0, 2.0]) < 0.3) and np.all(sd < 0.5)    # two modes found
    q25, q75 = mdn_quantile(w, mu, sd, 0.25), mdn_quantile(w, mu, sd, 0.75)
    assert np.all(q25 < -1.5) and np.all(q75 > 1.5)
