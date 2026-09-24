"""Acceptance tests of firm.kalman."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_kalman import HedgeTracker, em, fit_mle, kalman_filter, local_level_gain, particle_filter, rts_smoother


def _local_level(n, q, rng):
    mu = np.cumsum(math.sqrt(q) * rng.standard_normal(n))
    return mu, mu + rng.standard_normal(n)


def test_filter_is_gaussian_conditioning():
    """Likelihood and smoothed means equal the direct multivariate-normal answers for a short local level."""
    rng = np.random.default_rng(1)
    n, q, p0 = 12, 0.3, 2.0
    _, y = _local_level(n, q, rng)
    kf = kalman_filter(y, [1.0], [[1.0]], 1.0, [[q]], [0.0], [[p0]])
    i = np.arange(n)
    cov_mu = p0 + q * np.minimum(i[:, None], i[None, :])          # mu_t = mu_1 + sum of t - 1 increments
    cov_y = cov_mu + np.eye(n)
    sign, logdet = np.linalg.slogdet(cov_y)
    ll = -0.5 * (n * math.log(2 * math.pi) + logdet + y @ np.linalg.solve(cov_y, y))
    assert abs(kf["loglik"] - ll) < 1e-9
    sm = rts_smoother(kf, [[1.0]])
    assert np.allclose(sm["a_smooth"][:, 0], cov_mu @ np.linalg.solve(cov_y, y), atol=1e-9)
    assert np.allclose(kf["a_filt"][-1, 0], (cov_mu @ np.linalg.solve(cov_y, y))[-1], atol=1e-9)


def test_missing_and_steady_gain():
    rng = np.random.default_rng(2)
    _, y = _local_level(300, 0.01, rng)
    y[100] = np.nan
    kf = kalman_filter(y, [1.0], [[1.0]], 1.0, [[0.01]], [0.0], [[10.0]])
    assert kf["a_filt"][100, 0] == kf["a_pred"][100, 0] and np.isnan(kf["v"][100])
    assert abs(kf["K"][-1, 0] - local_level_gain(0.01)) < 1e-6
    assert abs(local_level_gain(1.0) - (1 + math.sqrt(5)) / 2 / (1 + (1 + math.sqrt(5)) / 2)) < 1e-12


def test_mle_and_em():
    rng = np.random.default_rng(3)
    _, y = _local_level(3000, 0.05, rng)
    h, Q, ll = fit_mle(y, [1.0], [[1.0]], [0.0], [[10.0]], 1.0, [0.01])
    assert abs(h - 1) < 0.1 and abs(Q[0, 0] - 0.05) < 0.02
    H, Q2, lls = em(y, [1.0], [[1.0]], 3.0, [[0.5]], [0.0], [[10.0]], 30)
    assert all(b >= a - 1e-8 for a, b in zip(lls, lls[1:], strict=False)) and lls[-1] <= ll + 1e-6


def test_particle_filter_matches_kalman():
    rng = np.random.default_rng(4)
    _, y = _local_level(300, 0.05, rng)
    kf = kalman_filter(y, [1.0], [[1.0]], 1.0, [[0.05]], [0.0], [[1.0]])
    pf = particle_filter(y, 4000, lambda m, g: g.standard_normal(m),
                         lambda x, g: x + math.sqrt(0.05) * g.standard_normal(x.size),
                         lambda yt, x: -0.5 * (yt - x) ** 2 - 0.5 * math.log(2 * math.pi), np.random.default_rng(5))
    assert abs(pf["loglik"] - kf["loglik"]) < 1.5
    assert np.max(np.abs(pf["mean"] - kf["a_filt"][:, 0])) < 0.1


def test_hedge_tracker_is_the_filter():
    rng = np.random.default_rng(6)
    x = rng.standard_normal(200)
    y = 0.8 * x + 0.3 * rng.standard_normal(200)
    kf = kalman_filter(y, x[:, None], [[1.0]], 0.09, [[1e-4]], [0.5], [[1.0]])
    tr = HedgeTracker(1e-4, 0.09, 0.5, 1.0)
    used = np.array([tr.update(a, b)[0] for a, b in zip(x, y, strict=True)])
    assert np.allclose(used, kf["a_pred"][:, 0])
