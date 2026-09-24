"""Acceptance tests of firm.hfvol."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_hfvol import (
    bipower,
    hayashi_yoshida,
    noise_variance,
    optimal_n,
    preaveraged,
    previous_tick,
    realised_kernel,
    refresh_times,
    roll_spread,
    rv,
    rv_subsampled,
    tsrv,
)

N = 23_400
SD = 0.01 / math.sqrt(N)          # integrated variance 1e-4


def _paths(n_days, noise, seed):
    rng = np.random.default_rng(seed)
    for _ in range(n_days):
        p = np.cumsum(SD * rng.standard_normal(N))
        yield p, p + noise * rng.standard_normal(N)


def test_noise_free_and_noise_bias():
    for p, x in _paths(1, 1e-4, 1):
        assert abs(rv(p) / 1e-4 - 1) < 0.03 and abs(rv_subsampled(p, 300) / 1e-4 - 1) < 0.15
        assert abs(rv(x) - (1e-4 + 2 * (N - 1) * 1e-8)) / rv(x) < 0.03       # E[RV] = IV + 2 n omega^2
        assert abs(noise_variance(x) / (1e-8 + 1e-4 / (2 * (N - 1))) - 1) < 0.05     # it also counts IV / 2n


def test_noise_robust_estimators_are_unbiased():
    t, k, pa = [], [], []
    for _, x in _paths(20, 1e-4, 2):
        t.append(tsrv(x, 300))
        k.append(realised_kernel(x, 60))
        pa.append(preaveraged(x, 150))
    for v in (t, k, pa):
        assert abs(np.mean(v) / 1e-4 - 1) < 0.05


def test_bipower_ignores_a_jump():
    rng = np.random.default_rng(3)
    p = np.cumsum(SD * rng.standard_normal(N))
    p[N // 2:] += 0.01
    assert abs(rv(p) - (1e-4 + 1e-4)) / 2e-4 < 0.05 and abs(bipower(p) / 1e-4 - 1) < 0.05


def test_asynchronous_covariance():
    rng = np.random.default_rng(4)
    rho, hy = 0.6, []
    for _ in range(40):
        z1, z2 = rng.standard_normal(N), rng.standard_normal(N)
        p1, p2 = np.cumsum(SD * z1), np.cumsum(SD * (rho * z1 + math.sqrt(1 - rho**2) * z2))
        t1 = np.flatnonzero(rng.random(N) < 0.2).astype(float)
        t2 = np.flatnonzero(rng.random(N) < 0.07).astype(float)
        hy.append(hayashi_yoshida(t1, p1[t1.astype(int)], t2, p2[t2.astype(int)]))
    assert abs(np.mean(hy) / (rho * 1e-4) - 1) < 0.05
    t1, x1 = np.array([0.0, 2.0, 5.0]), np.array([0.0, 1.0, 3.0])
    t2, x2 = np.array([0.0, 3.0, 5.0]), np.array([0.0, 2.0, 2.5])
    assert abs(hayashi_yoshida(t1, x1, t2, x2) - (1 * 2 + 2 * 2 + 2 * 0.5)) < 1e-12   # all return pairs overlap
    r = refresh_times([0, 1, 4, 6], [0, 3, 5, 9])
    assert list(r) == [0, 3, 5, 9]
    assert list(previous_tick([0, 2, 5], [1, 2, 3], [0, 1, 2, 4, 6])) == [1, 1, 2, 2, 3]


def test_roll_and_optimal_n():
    rng = np.random.default_rng(5)
    mid = 100 + np.cumsum(0.001 * rng.standard_normal(200_000))
    price = mid + 0.05 * rng.choice([-1, 1], 200_000)
    assert abs(roll_spread(price) - 0.1) < 0.003
    iq, om2 = 1e-8, 1e-9
    n = optimal_n(iq, om2)
    f = [2 * iq / m + (2 * m * om2) ** 2 for m in (0.9 * n, n, 1.1 * n)]
    assert f[1] < f[0] and f[1] < f[2]
