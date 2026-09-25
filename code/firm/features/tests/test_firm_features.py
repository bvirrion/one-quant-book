"""Acceptance tests of firm.features."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_features import (
    amihud,
    crossover_weights,
    ewma_vol,
    garman_klass,
    leakage_test,
    ma_crossover,
    parkinson,
    past_return,
    rogers_satchell,
    rolling_vol,
    turnover,
    volume_surprise,
    yang_zhang,
)

RNG = np.random.default_rng(3)
RET = RNG.normal(0, 0.01, (300, 5))
PRICE = 100 * np.exp(np.cumsum(np.log1p(RET), axis=0))
VOL = RNG.lognormal(10, 0.3, (300, 5))


def test_past_return_with_skip():
    r = np.array([[0.1], [0.2], [0.3], [0.4]])
    assert np.isclose(past_return(r, 2)[3, 0], 1.3 * 1.4 - 1)
    assert np.isclose(past_return(r, 2, skip=1)[3, 0], 1.2 * 1.3 - 1) and np.isnan(past_return(r, 2, skip=1)[1, 0])


def test_no_feature_looks_ahead():
    feats = [
        (lambda r: past_return(r, 20, 1), (RET,)), (lambda r: rolling_vol(r, 20), (RET,)),
        (lambda r: ewma_vol(r, 10), (RET,)), (lambda v: volume_surprise(v, 20), (VOL,)),
        (lambda r, d: amihud(r, d, 20), (RET, VOL * PRICE)), (lambda v, s: turnover(v, s, 20), (VOL, VOL * 50)),
        (lambda p: ma_crossover(p, 5, 20), (PRICE,)),
    ]
    for f, inp in feats:
        assert leakage_test(f, inp, 150)


def test_leakage_test_catches_a_leak():
    def peek(r):
        return np.roll(r, -1, axis=0)
    assert not leakage_test(peek, (RET,), 150)


def test_range_estimators_are_unbiased_for_brownian_motion():
    rng = np.random.default_rng(0)
    days, steps, sigma = 4000, 390, 0.01
    paths = np.cumsum(rng.normal(0, sigma / math.sqrt(steps), (days, steps)), axis=1)
    lo, hi, c = np.minimum(paths.min(axis=1), 0), np.maximum(paths.max(axis=1), 0), paths[:, -1]
    e = np.exp
    for est in (parkinson(e(hi), e(lo)), garman_klass(np.ones(days), e(hi), e(lo), e(c)),
                rogers_satchell(np.ones(days), e(hi), e(lo), e(c))):
        assert abs(est.mean() / sigma**2 - 1) < 0.10          # a range seen at 390 points is 7-9% too narrow
    yz = yang_zhang(np.ones(days), e(hi), e(lo), e(c), 20)
    assert np.nanmean(yz) > 0


def test_crossover_is_a_filter_of_past_returns():
    w = crossover_weights(5, 20)
    lp = np.log(PRICE[:, 0])
    r = np.diff(lp)
    t = 250
    approx = sum(w[j] * r[t - 1 - j] for j in range(len(w)))
    exact = math.log(np.mean(np.exp(lp[t - 4: t + 1])) / np.mean(np.exp(lp[t - 19: t + 1])))
    assert abs(approx - exact) < 1e-3 and w[0] > 0 and np.isclose(w.sum(), (20 - 1) / 2 - (5 - 1) / 2)
