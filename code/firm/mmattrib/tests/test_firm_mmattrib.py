import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_mmattrib as ma  # noqa: E402


def test_year_and_attribution():
    y = ma.Year(seed=5, inv_sd=0.0)
    at = ma.attribution(y)
    assert np.allclose(at["capture"] + at["adverse"] + at["inventory"], at["total"])
    assert np.allclose(at["capture_ratio_obs"], y.kappa)
    assert y.share[180, 1] < y.share[100, 1] and y.treated[:182].sum() == 0 and 0 < y.treated.sum() < 70


def test_cusum_and_experiment():
    x = np.r_[np.full(50, 0.12), np.full(50, 0.084)]
    assert ma.cusum_down(x, 0.12, 0.005, 0.05) == 51
    assert ma.cusum_down(np.full(50, 0.12), 0.12, 0.005, 0.05) == -1
    y = ma.Year(seed=6)
    e = ma.experiment(y, 182, 251)
    assert math.isclose(e["share_mult"], 1.1, rel_tol=1e-9) and math.isclose(e["adverse_add"], 0.1, abs_tol=1e-12)
    assert e["effect"] < 0


def test_month_change_truth_without_noise():
    y = ma.Year(seed=7, inv_sd=0.0, noise_mv=0.0, noise_half=0.0)
    t = ma.month_change(y, 7, 8)
    assert abs(t["residual"]) < 0.05 * abs(t["realised"])          # month averages of products, not noise
    assert t["spread"] < 0 < t["volume"] and t["competition"] < 0
    assert ma.retire_day(np.r_[np.full(100, 10.0), np.full(100, -1.0)], 20, 0.0) > 100
    assert ma.retire_day(np.full(100, 1.0), 20, 0.0) == -1
