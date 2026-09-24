"""Acceptance tests of firm.estim."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_estim import delta_method, long_run_variance, mean_se, mle, sharpe


def test_normal_mle_and_standard_errors():
    x = np.random.default_rng(1).normal(2.0, 3.0, 5000)
    f = mle(lambda t: -0.5 * math.log(2 * math.pi) - t[1] - 0.5 * ((x - t[0]) / math.exp(t[1])) ** 2, [0.0, 0.0])
    assert abs(f["theta"][0] - x.mean()) < 1e-3 and abs(math.exp(f["theta"][1]) - x.std()) < 1e-3
    assert abs(f["se_hessian"][0] - 3 / math.sqrt(5000)) < 3e-3
    assert abs(f["se_sandwich"][0] - f["se_hessian"][0]) < 3e-3          # correct model: sandwich = Hessian


def test_exponential_mle():
    t = np.random.default_rng(2).exponential(0.5, 4000)
    f = mle(lambda th: np.log(th[0]) - th[0] * t if th[0] > 0 else -np.inf * t, [1.0])
    assert abs(f["theta"][0] - 1 / t.mean()) < 1e-3 and abs(f["se_hessian"][0] - f["theta"][0] / math.sqrt(4000)) < 1e-3


def test_newey_west_moving_average():
    rng = np.random.default_rng(3)
    e = rng.standard_normal(200_004)
    x = np.convolve(e, np.ones(5) / 5, mode="valid")
    bartlett10 = 1 + 2 * sum((1 - k / 11) * (1 - k / 5) for k in range(1, 5))    # 4.27: weights shrink the lags
    assert abs(long_run_variance(x, lags=10) / x.var() - bartlett10) < 0.15
    assert abs(long_run_variance(x, lags=100) / x.var() - 5) < 0.35       # noise from 96 empty lags
    assert mean_se(x, "hac", lags=10) > 2 * mean_se(x, "iid")


def test_sharpe_se_matches_simulation():
    rng = np.random.default_rng(4)
    srs = [sharpe(rng.normal(0.0005, 0.01, 1260))["sr"] for _ in range(2000)]
    s = sharpe(rng.normal(0.0005, 0.01, 1260))
    assert abs(np.std(srs) - s["se_iid"]) < 0.03 and abs(s["se_hac"] - s["se_iid"]) < 0.08


def test_delta_method():
    se = delta_method(lambda t: t[0] ** 2, np.array([3.0]), np.array([[0.01]]))
    assert abs(se - 0.6) < 1e-6
