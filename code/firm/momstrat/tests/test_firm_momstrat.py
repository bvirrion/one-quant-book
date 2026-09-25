import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_momstrat import bear, decile_book, industry_mom, residual_mom, total_mom, vol_scale  # noqa: E402


def test_total_mom_skips_the_last_month():
    r = np.zeros((40, 1))
    r[5:15] = 0.01
    m = total_mom(r, lookback=30, skip=5)
    assert np.isnan(m[28, 0]) and abs(m[34, 0] - (1.01**10 - 1)) < 1e-12 and abs(m[35, 0] - (1.01**9 - 1)) < 1e-12
    r2 = r.copy()
    r2[36:] = 0.5                                                      # the skipped days do not count
    assert total_mom(r2, 30, 5)[39, 0] == total_mom(r, 30, 5)[39, 0]


def test_residual_and_industry_mom():
    rng = np.random.default_rng(0)
    E = rng.standard_normal((300, 3)) * 0.01
    E[:, 0] += 0.004
    s = residual_mom(E, 252, 21)
    assert s[-1, 0] > 2 and abs(s[-1, 1]) < 3
    ret = np.zeros((300, 4))
    ret[:, :2] = 0.001
    im = industry_mom(ret, np.array([0, 0, 1, 1]), np.ones((300, 4)), 252, 21)
    assert im[-1, 0] == im[-1, 1] > 0 and im[-1, 2] == 0


def test_book_scaling_and_state():
    W = decile_book(np.arange(20.0)[None, :].repeat(2, 0), np.ones((2, 20), bool), 0.1)
    assert W[0, -2:].tolist() == [0.25, 0.25] and W[0, :2].tolist() == [-0.25, -0.25] and abs(W[0]).sum() == 1.0
    r = np.r_[np.full(100, 0.01) * np.tile([1, -1], 50), np.zeros(10)]
    w = vol_scale(r, 0.12, 100)
    assert abs(w[100] - 0.12 / (np.std(r[:100], ddof=1) * math.sqrt(252))) < 1e-12 and np.isnan(w[99])
    assert bear(np.r_[np.full(10, 0.01), np.full(10, -0.03)], 10).tolist()[-1]
