"""Acceptance tests of firm.resample."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_resample import (
    block_indices,
    bootstrap,
    circular_shift_test,
    iid_indices,
    jackknife,
    optimal_block_length,
    percentile_interval,
    permutation_test,
    stationary_indices,
)


def test_index_generators():
    rng = np.random.default_rng(1)
    n = 50
    b = block_indices(n, 200, 7, rng)
    assert b.shape == (200, n) and b.min() >= 0 and b.max() < n
    steps = np.diff(b, axis=1) % n
    assert np.all(steps[:, :6] == 1)                            # the first block is 7 consecutive days
    s = stationary_indices(n, 20_000, 10.0, rng)
    new = (np.diff(s, axis=1) % n) != 1
    assert abs(1 / new.mean() - 10.0) < 0.5                    # geometric blocks of mean 10
    for t in (0, n - 1):                                         # the resampled series is stationary:
        freq = np.bincount(s[:, t], minlength=n) / s.shape[0]    # every day equally likely at every position
        assert np.max(np.abs(freq - 1 / n)) < 0.006
    assert iid_indices(n, 3, rng).shape == (3, n)


def test_bootstrap_se_of_mean():
    rng = np.random.default_rng(2)
    x = rng.standard_normal(500)
    d = bootstrap(np.mean, x, iid_indices(500, 4000, rng))
    assert abs(d.std() - x.std() / math.sqrt(500)) < 0.003
    lo, hi = percentile_interval(d)
    assert lo < x.mean() < hi and abs((hi - lo) - 2 * 1.96 * x.std() / math.sqrt(500)) < 0.015


def test_block_length_rule():
    rng = np.random.default_rng(3)
    e = rng.standard_normal(10_000)
    assert optimal_block_length(e)[0] < 4                        # no dependence: short blocks
    x = np.empty(10_000)
    x[0] = e[0]
    for t in range(1, x.size):
        x[t] = 0.5 * x[t - 1] + e[t]
    b_sb, b_cb = optimal_block_length(x)
    target = (4 / 3) ** (2 / 3) * 10_000 ** (1 / 3)               # AR(1) 0.5: (G / g(0))^(2/3) n^(1/3) = 26.1
    assert abs(b_sb / target - 1) < 0.3 and b_cb > b_sb


def test_permutation_exact_size_and_power():
    rng = np.random.default_rng(4)
    rej = 0
    for _ in range(400):
        x, y = rng.standard_normal(40), rng.standard_normal(40)
        rej += permutation_test(lambda a, b: float(np.corrcoef(a, b)[0, 1]), x, y, 99, rng) <= 0.05
    assert abs(rej / 400 - 0.05) < 0.03
    x = rng.standard_normal(100)
    y = 0.5 * x + rng.standard_normal(100)
    assert permutation_test(lambda a, b: float(np.corrcoef(a, b)[0, 1]), x, y, 199, rng) == 1 / 200
    assert circular_shift_test(lambda a, b: float(np.corrcoef(a, b)[0, 1]), x, y, rng) == 1 / 100


def test_jackknife():
    rng = np.random.default_rng(5)
    x = rng.standard_normal(30)
    j = jackknife(lambda v: float(np.mean((v - v.mean()) ** 2)), x)
    assert abs(j["bias_corrected"] - x.var(ddof=1)) < 1e-12      # removes the O(1/n) bias exactly
    m = jackknife(np.mean, x)
    assert abs(m["se"] - x.std(ddof=1) / math.sqrt(30)) < 1e-12 and abs(m["bias"]) < 1e-12
