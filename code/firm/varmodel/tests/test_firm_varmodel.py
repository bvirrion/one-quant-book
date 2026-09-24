import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_varmodel as f


def test_historical_var_and_es_on_a_known_sample():
    pnl = -np.arange(1, 201, dtype=float)          # losses 1..200
    assert f.hs_var_es(pnl, 0.99) == (199.0, 199.5)
    assert f.hs_var_es(pnl, 0.975) == (196.0, 198.0)


def test_parametric_matches_monte_carlo_for_a_linear_book_and_euler_adds_up():
    cov = np.array([[1.0, 0.3], [0.3, 2.0]]) * 1e-4
    d = np.array([1e6, -5e5])
    v, es = f.parametric_var_es(d, cov, 0.99)
    mv, _ = f.mc_var_es(lambda x: x @ d, cov, 0.99, n=400_000)
    assert abs(mv / v - 1) < 0.01
    assert abs(f.euler_var(d, cov, 0.99).sum() - v) < 1e-6 * v
    assert abs(f.parametric_var_es(d, cov, 0.975)[1] / v - 1) < 0.01     # ES 97.5% ~ VaR 99% under normality


def test_backtests():
    assert abs(f.kupiec(1000, 10, 0.01)[0]) < 1e-9 and f.kupiec(250, 10, 0.01)[1] < 0.01
    assert f.traffic_light(4) == ("green", 0.0) and f.traffic_light(5) == ("yellow", 0.40)
    assert f.traffic_light(9) == ("yellow", 0.85) and f.traffic_light(12)[0] == "red"
    clustered = np.zeros(500, dtype=int)
    clustered[100:105] = 1
    spread = np.zeros(500, dtype=int)
    spread[::100] = 1
    assert f.christoffersen(clustered)[1] < 0.01 < f.christoffersen(spread)[1]


def test_ewma_and_filtered_scenarios():
    x = np.random.default_rng(1).normal(0, 0.01, (1000, 2))
    c = f.ewma_cov(x, 0.94)
    assert c.shape == (2, 2) and np.all(np.diag(c) > 0)
    s = f.fhs_scenarios(x, 0.94)
    _, now = f.ewma_vol_path(x, 0.94)
    assert np.allclose(s.std(axis=0) / now, 1.0, atol=0.15)
    assert math.isclose(f.sqrt_time(1.0, 10), math.sqrt(10))
