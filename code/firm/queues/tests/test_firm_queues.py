"""Acceptance tests of firm.queues."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_queues import (
    bd_expected_exit_time,
    bd_hitting_probability,
    depletion_cdf,
    fill_time_cdf,
    generator,
    race,
    stationary,
    thomas,
)


def test_gamblers_ruin_and_exit_times():
    h = bd_hitting_probability(1.0, 1.0, 10)
    assert np.allclose(h, np.arange(11) / 10)
    m = bd_expected_exit_time(1.0, 1.0, 10)
    assert np.allclose(m, np.arange(11) * (10 - np.arange(11)) / 2.0)
    r = 1 / 0.9
    assert abs(bd_hitting_probability(0.9, 1.0, 40)[20] - (1 - r**20) / (1 - r**40)) < 1e-12


def test_mm1_stationary_law():
    n, lam, mu = 60, 0.6, 1.0
    rates = np.zeros((n, n))
    for i in range(n - 1):
        rates[i, i + 1], rates[i + 1, i] = lam, mu
    pi = stationary(generator(rates))
    assert np.allclose(pi[:10], 0.4 * 0.6 ** np.arange(10), atol=1e-9)


def test_depletion_law_against_simulation():
    t = np.linspace(0, 200, 401)
    F = depletion_cdf(0.9, 1.0, 5, t)
    rng = np.random.default_rng(1)
    hits = []
    for _ in range(20_000):
        q, s = 5, 0.0
        while q > 0 and s < 200:
            s += rng.exponential(1 / 1.9)
            q += 1 if rng.random() < 0.9 / 1.9 else -1
        hits.append(s if q == 0 else np.inf)
    hits = np.array(hits)
    for tt in (10.0, 50.0, 150.0):
        assert abs(np.mean(hits <= tt) - np.interp(tt, t, F)) < 0.012


def test_race_symmetry_and_fill_mean():
    t = np.linspace(0, 1200, 2401)
    F = depletion_cdf(0.9, 1.0, 20, t)
    assert abs(race(F, F, t) - 0.5) < 1e-3
    G = fill_time_cdf(10, 1.0, 0.5, t)
    mean = np.sum((1 - 0.5 * (G[1:] + G[:-1])) * np.diff(t))
    assert abs(mean - (10 + 2)) < 0.01


def test_thomas():
    a, b, c = np.array([0.0, 1, 1]), np.array([4.0, 4, 4]), np.array([1.0, 1, 0])
    x = thomas(a, b, c, np.array([5.0, 6, 5]))
    assert np.allclose(x, [1, 1, 1])
