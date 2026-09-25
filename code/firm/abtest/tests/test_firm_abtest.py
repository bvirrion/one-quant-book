import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_abtest import (
    always_valid_p,
    assign,
    bucket,
    cluster_diff,
    cuped,
    demean_by,
    diff_means,
    mde,
    msprt,
    power,
    sample_size,
    srm_pvalue,
    stratified,
)


def test_assignment_is_deterministic_and_balanced():
    ids = range(20000)
    a = assign(ids, "algo-v2", 0.1)
    assert np.array_equal(a, assign(ids, "algo-v2", 0.1))                # the same unit, the same arm
    assert abs(a.mean() - 0.1) < 0.006 and srm_pvalue(int(a.sum()), int((~a).sum()), 0.1) > 0.01
    b = assign(ids, "algo-v3", 0.1)
    assert abs((a & b).mean() - 0.01) < 0.003                           # experiments are independent
    assert 0 <= bucket(7, "x") < 1 and bucket(7, "x") != bucket(7, "x", salt="s")


def test_estimators_on_a_known_effect():
    rng = np.random.default_rng(1)
    n = 40000
    x = rng.standard_normal(n)
    t = rng.random(n) < 0.5
    y = 2.0 * x + rng.standard_normal(n) - 0.1 * t
    d, se = diff_means(y, t)
    dc, sec, theta = cuped(y, x, t)
    assert abs(theta[0] - 2.0) < 0.02 and abs(sec / se - 1 / math.sqrt(5)) < 0.01   # R^2 = 0.8: variance / 5
    assert abs(dc + 0.1) < 3 * sec
    ds, ses = stratified(y, t, np.digitize(x, [-1, 0, 1]))
    assert sec < ses < se                                                # coarse strata catch part of x
    assert abs(d + 0.1) < 3 * se


def test_cluster_diff_needs_constant_arms():
    y = np.arange(8.0)
    cl = np.repeat([0, 1, 2, 3], 2)
    d, _ = cluster_diff(y, np.repeat([True, False, True, False], 2), cl)
    assert d == -2.0
    try:
        cluster_diff(y, np.array([1, 0] * 4, bool), cl)
        raise AssertionError
    except ValueError:
        pass


def test_demean_by_removes_group_shocks():
    v = np.array([1.0, 3.0, 10.0, 14.0])
    assert list(demean_by(v, [0, 0, 1, 1])) == [-1.0, 1.0, -2.0, 2.0]


def test_power_mde_sample_size_agree():
    se = 0.1
    m = mde(se)
    assert abs(m - 2.8016 * se) < 1e-3 and abs(power(m, se) - 0.8) < 1e-3
    n = sample_size(0.3, 23.0, share=0.5)
    assert abs(mde(23.0 * math.sqrt(4 / n)) - 0.3) < 1e-9
    assert abs(power(0.0, 1.0) - 0.05) < 1e-12


def test_msprt_is_always_valid():
    rng = np.random.default_rng(3)
    looks, reps = 200, 2000
    x = rng.standard_normal((reps, looks)).cumsum(axis=1)                # running sums of a null stream
    n = np.arange(1, looks + 1)
    d, se = x / n, 1 / np.sqrt(n)
    p = always_valid_p(d, se, tau=0.3)
    assert np.all(np.diff(p, axis=1) <= 0)
    assert (p[:, -1] < 0.05).mean() < 0.05                               # Ville: P(sup Lambda >= 20) <= 1/20
    naive = (np.abs(d / se) > 1.96).any(axis=1).mean()
    assert naive > 0.3                                                   # peeking at a fixed-horizon test
    assert msprt(0.0, 1.0, 1.0) == math.sqrt(0.5)
