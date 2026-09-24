"""Acceptance tests of firm.bayes."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_bayes import (
    beta_binomial,
    eb_normal_means,
    ess,
    gibbs_hierarchical,
    james_stein,
    metropolis,
    nig_update,
    normal_normal,
    rhat,
)


def test_conjugate_updates():
    assert beta_binomial(2, 3, 7, 10) == (9, 6)
    m, v = normal_normal(0.0, 1.0, 2.0, 1.0)
    assert abs(m - 1.0) < 1e-12 and abs(v - 0.5) < 1e-12
    x = np.random.default_rng(1).normal(3.0, 2.0, 400)
    mn, kn, an, bn = nig_update(0.0, 1e-9, 1e-9, 1e-9, x)
    assert abs(mn - x.mean()) < 1e-6 and kn > 399.99 and abs(an - 200) < 1e-6
    assert abs(bn / (an - 1) - np.sum((x - x.mean()) ** 2) / 398) < 1e-6        # E[s2] = SS / (n - 2)


def test_empirical_bayes_equal_and_unequal():
    rng = np.random.default_rng(2)
    th = 0.5 + 0.4 * rng.standard_normal(2000)
    x = th + 0.5 * rng.standard_normal(2000)
    e = eb_normal_means(x, 0.5)
    assert abs(e["m"] - 0.5) < 0.03 and abs(math.sqrt(e["tau2"]) - 0.4) < 0.03
    assert np.mean((e["post_mean"] - th) ** 2) < np.mean((x - th) ** 2)
    se = rng.uniform(0.2, 0.8, 2000)
    x = th + se * rng.standard_normal(2000)
    e = eb_normal_means(x, se)

    def ll(m, t2):
        v = se**2 + t2
        return -0.5 * np.sum((x - m) ** 2 / v + np.log(v))
    grid = [(ll(m, t2), m, t2) for m in np.linspace(0.44, 0.56, 25) for t2 in np.linspace(0.10, 0.22, 25)]
    _, m_best, t2_best = max(grid)
    assert abs(e["m"] - m_best) < 0.006 and abs(e["tau2"] - t2_best) < 0.006   # the fixed point is the marginal MLE


def test_james_stein_dominates():
    rng = np.random.default_rng(3)
    r_mle = r_js = 0.0
    for _ in range(4000):
        th = rng.normal(0.0, 0.5, 10)
        x = th + rng.standard_normal(10)
        r_mle += np.sum((x - th) ** 2)
        r_js += np.sum((james_stein(x, 1.0) - th) ** 2)
    assert r_js < 0.6 * r_mle


def test_samplers_and_diagnostics():
    rng = np.random.default_rng(4)
    ch, acc = metropolis(lambda z: -0.5 * float(z @ z), [3.0], 60_000, 2.4, rng)
    assert abs(ch[5000:, 0].mean()) < 0.05 and abs(ch[5000:, 0].var() - 1) < 0.06 and 0.3 < acc < 0.55
    phi, n = 0.9, 200_000
    e = rng.standard_normal(n)
    y = np.empty(n)
    y[0] = e[0]
    for t in range(1, n):
        y[t] = phi * y[t - 1] + e[t]
    assert abs(ess(y) / (n * (1 - phi) / (1 + phi)) - 1) < 0.1
    assert abs(rhat(rng.standard_normal((4, 5000))) - 1) < 0.01
    assert rhat(rng.standard_normal((4, 5000)) + np.arange(4)[:, None]) > 1.5


def test_gibbs_matches_empirical_bayes_for_many_units():
    rng = np.random.default_rng(5)
    th = 0.5 + 0.4 * rng.standard_normal(400)
    x = th + 0.5 * rng.standard_normal(400)
    g = gibbs_hierarchical(x, 0.5, 4000, rng)
    e = eb_normal_means(x, 0.5)
    assert np.max(np.abs(g["theta"][500:].mean(0) - e["post_mean"])) < 0.04
    assert abs(g["tau"][500:].mean() - math.sqrt(e["tau2"])) < 0.03
