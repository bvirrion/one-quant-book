"""Acceptance tests of firm.coint."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_coint import (
    JOHANSEN_CRIT,
    engle_granger,
    f_sf,
    fevd,
    granger_test,
    irf,
    johansen,
    johansen_crit_sim,
    var_fit,
    var_stable,
)


def _var1(A, n, rng):
    Y = np.zeros((n, A.shape[0]))
    for t in range(1, n):
        Y[t] = A @ Y[t - 1] + rng.standard_normal(A.shape[0])
    return Y


def test_var_irf_fevd():
    rng = np.random.default_rng(1)
    A = np.array([[0.5, 0.2], [0.0, 0.3]])
    Y = _var1(A, 20_000, rng)
    v = var_fit(Y, 1)
    assert np.allclose(v["A"][0], A, atol=0.02) and var_stable(v["A"]) and not var_stable(np.array([[[1.01, 0], [0, 0.5]]]))
    R = irf(v["A"], v["Sigma"], 5)
    assert np.allclose(R[0], np.linalg.cholesky(v["Sigma"])) and np.allclose(R[1], v["A"][0] @ R[0])
    F = fevd(v["A"], v["Sigma"], 10)
    assert np.allclose(F.sum(axis=1), 1) and F[1, 0] < 0.02            # variable 2 is not driven by variable 1


def test_granger_and_f():
    assert abs(f_sf(3.841458820694124, 1, 10**7) - 0.05) < 1e-4 and abs(f_sf(1.0, 5, 5) - 0.5) < 1e-12
    rng = np.random.default_rng(2)
    A = np.array([[0.5, 0.2], [0.0, 0.3]])
    Y = _var1(A, 5000, rng)
    assert granger_test(Y, 2, 1, 0)[3] < 1e-6 and granger_test(Y, 2, 0, 1)[3] > 0.001
    pv = [granger_test(_var1(np.diag([0.5, 0.5]), 500, rng), 2, 1, 0)[3] for _ in range(300)]
    assert abs(np.mean(np.array(pv) < 0.05) - 0.05) < 0.03


def test_engle_granger():
    rng = np.random.default_rng(3)
    x = np.cumsum(rng.standard_normal(2000))
    y = 2 + 0.7 * x + rng.standard_normal(2000)
    r = engle_granger(y, x)
    assert r["tau"] < r["crit"][0] and abs(r["beta"][1] - 0.7) < 0.01
    rej = sum(engle_granger(np.cumsum(rng.standard_normal(500)), np.cumsum(rng.standard_normal(500)))["tau"] < -3.34
              for _ in range(400))
    assert rej / 400 < 0.09


def test_johansen_detects_rank_and_direction():
    rng = np.random.default_rng(4)
    n = 3000
    common = np.cumsum(rng.standard_normal(n))
    s = np.zeros(n)
    for t in range(1, n):
        s[t] = 0.9 * s[t - 1] + rng.standard_normal()
    Y = np.column_stack([common + rng.standard_normal(n), common + s, np.cumsum(rng.standard_normal(n))])
    j = johansen(Y, lags=1)
    assert j["trace"][0] > j["crit_trace"][0][2] and j["trace"][1] < j["crit_trace"][1][1]
    b = j["beta"][:3, 0] / j["beta"][0, 0]
    assert abs(b[1] + 1) < 0.05 and abs(b[2]) < 0.05


def test_critical_values_resimulate():
    for m in (1, 2):
        sim = johansen_crit_sim(m, T=1000, reps=3000, seed=99)
        assert abs(sim["trace"][1] - JOHANSEN_CRIT["trace"][m][1]) < 0.6
        assert abs(sim["max"][1] - JOHANSEN_CRIT["max"][m][1]) < 0.6
