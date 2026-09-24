"""Acceptance tests of the Book 5, Chapter 12 build (forward variance and rough Bergomi)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_fwdvar import (
    ForwardVarianceCurve,
    _g_ratio,
    fbm,
    joint_cov,
    log_strip_variance,
    mixing_calls,
    power_law_fit,
    rbergomi_integrals,
    rbergomi_smile,
    rbergomi_vix,
    roughness,
)


def test_log_strip_of_a_flat_smile_is_its_variance():
    for vol, t in ((0.2, 1.0), (0.35, 0.1), (0.15, 3.0)):
        assert abs(log_strip_variance(lambda k, v=vol: v, t) - vol * vol) < 1e-6


def test_forward_variance_curve():
    c = ForwardVarianceCurve.from_vs_vols([0.5, 1.0, 2.0], [0.2, 0.22, 0.21])
    assert abs(c.xi(0.25) - 0.04) < 1e-12
    assert abs(c.xi(0.75) - (0.22 ** 2 - 0.5 * 0.04) / 0.5) < 1e-12
    assert abs(c.vs_vol(1.0) - 0.22) < 1e-12 and abs(c.total_variance(3.0) - (0.0882 + c.xi(2.0))) < 1e-12
    assert abs(c.forward_vol(1.0, 2.0) - math.sqrt(2 * 0.21 ** 2 - 0.22 ** 2)) < 1e-12
    assert c.negative_intervals() == []
    assert ForwardVarianceCurve((1.0, 2.0), (0.05, 0.04)).negative_intervals() == [(1.0, 2.0)]


def test_volterra_covariance():
    h = 0.1
    assert abs(_g_ratio(np.array([1.0]), h)[0] - 1.0) < 1e-10
    s = (np.arange(400_000) + 0.5) / 400_000
    a = h - 0.5          # reference: the singular part (1 - s)^a (x - 1)^a integrated exactly
    ref = 2 * h * (np.mean((1 - s) ** a * ((3 - s) ** a - 2 ** a)) + 2 ** a / (a + 1))
    assert abs(_g_ratio(np.array([3.0]), h)[0] - ref) < 1e-7
    t = np.array([0.25, 0.5, 1.0])
    c = joint_cov(t, h)
    assert np.allclose(np.diag(c)[:3], t ** (2 * h)) and np.allclose(np.diag(c)[3:], t)
    assert abs(c[2, 5] - math.sqrt(2 * h) / (h + 0.5)) < 1e-12
    assert np.linalg.eigvalsh(c).min() > 0
    # H = 1/2: Y is the Brownian motion itself
    assert np.allclose(joint_cov(t, 0.5), np.block([[np.minimum.outer(t, t)] * 2] * 2))


def test_rbergomi_limits_and_martingale():
    vols = rbergomi_smile(0.04, 0.1, 0.0, 0.0, 0.5, np.array([-0.2, 0.0, 0.2]), steps=20, n_paths=2000)
    assert np.allclose(vols, 0.2, atol=1e-9)
    i_sum, q = rbergomi_integrals(0.04, 0.1, 1.9, 1.0, 50, 40_000, 3)
    s1 = np.exp(-0.9 * i_sum - 0.5 * 0.81 * q)
    assert abs(s1.mean() - 1) < 4 * s1.std() / math.sqrt(len(s1))
    assert abs(mixing_calls(i_sum, q, -0.9, [1e-9])[0] - s1.mean()) < 1e-6
    assert abs(q.mean() - 0.04) < 4 * q.std() / math.sqrt(len(q))


def test_negative_correlation_gives_negative_skew():
    v = rbergomi_smile(0.04, 0.1, 1.5, -0.7, 0.25, np.array([-0.05, 0.05]), steps=50, n_paths=20_000)
    assert v[0] > v[1]


def test_vix_squared_is_the_forward_variance():
    vix = rbergomi_vix(0.04, 0.1, 1.9, 1 / 12, n_paths=100_000)
    v2 = vix ** 2
    assert abs(v2.mean() - 0.04) < 4 * v2.std() / math.sqrt(len(v2))
    assert vix.mean() < 0.2


def test_roughness_estimator():
    assert abs(roughness(fbm(1500, 0.3, 1)) - 0.3) < 0.05
    assert abs(roughness(fbm(1500, 0.1, 2)) - 0.1) < 0.05
    a, alpha = power_law_fit([0.1, 1.0, 2.0], [-0.5 * 0.1 ** -0.4, -0.5, -0.5 * 2 ** -0.4])
    assert abs(a - 0.5) < 1e-12 and abs(alpha + 0.4) < 1e-12
