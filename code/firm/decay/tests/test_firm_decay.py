import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_decay import (
    block_bootstrap,
    cusum,
    decline_power,
    half_life_ar,
    half_life_fit,
    ic_decay,
    rank_autocorr,
    sup_f,
    sup_f_critical,
    sup_f_pvalue,
    turnover,
)


def test_decay_curve_recovers_planted_half_life():
    rng = np.random.default_rng(0)
    T, N, rho = 600, 300, 0.5 ** (1 / 5)                    # signal half-life 5 days
    s = np.zeros((T, N))
    s[0] = rng.standard_normal(N)
    for t in range(1, T):
        s[t] = rho * s[t - 1] + math.sqrt(1 - rho * rho) * rng.standard_normal(N)
    ret = np.zeros((T, N))
    ret[1:] = 0.1 * s[:-1] + rng.standard_normal((T - 1, N))  # each day's return loads on yesterday's signal
    ic = ic_decay(s, ret, range(1, 16), range(20, T - 20))
    ic0, hl = half_life_fit(list(ic), list(ic.values()))
    assert 3.5 < hl < 7.0 and ic0 > 0.05
    assert half_life_fit([1, 2, 3, 4], [0.04, 0.0, 0.001, -0.001])[1] < 0.5          # one-day signal
    r = rank_autocorr(s, range(1, T))
    assert abs(r - rho) < 0.02 and abs(half_life_ar(rho) - 5.0) < 1e-9
    assert math.isclose(turnover(0.9), 0.1) and half_life_ar(1.0) == float("inf")


def test_bootstrap():
    x = np.arange(100.0)
    b = block_bootstrap(x, np.mean, 10, 200, seed=1)
    assert b.shape == (200,) and 30 < b.mean() < 70


def test_break_tests():
    rng = np.random.default_rng(3)
    calm = rng.standard_normal(240)
    W, b = cusum(calm)
    assert np.all(np.abs(W) < b)
    shifted = np.r_[rng.normal(0.5, 1, 120), rng.normal(-0.3, 1, 120)]
    W, b = cusum(shifted)
    assert np.any(np.abs(W) > b)
    f, k = sup_f(shifted)
    assert 100 <= k <= 140 and f > sup_f_critical(240, reps=300)
    assert 7.0 < sup_f_critical(240, reps=500) < 11.0
    assert sup_f_pvalue(shifted, reps=200) < 0.02 and sup_f_pvalue(calm, reps=200) > 0.05
    heavy = rng.standard_t(2.5, 240)                        # no break, heavy tails
    assert sup_f_pvalue(heavy, reps=200) > 0.01


def test_decline_power():
    p = decline_power(0.03, 0.10, 60, 0.5, reps=50_000)
    assert math.isclose(p["se"], 0.10 / math.sqrt(60))
    assert 0.1 < p["luck"] < 0.3 < p["decay"] < 0.7
