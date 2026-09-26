import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_basketarb as fb  # noqa: E402


def test_covariance_and_tracking():
    cov = fb.covariance([1.0, 2.0], [0.1, 0.2], 0.5)
    assert np.allclose(cov, [[0.25 + 0.01, 0.5], [0.5, 1.0 + 0.04]])
    assert fb.tracking_var([0.5, 0.5], [0.5, 0.5], cov) == 0.0
    assert math.isclose(fb.tracking_var([0.5, 0.5], [1.0, 0.0], cov), 0.25 * (0.26 - 1.0 + 1.04))


def test_partial_basket_tracks_better_with_more_names():
    ix = fb.Index(n=20, seed=3)
    v = [fb.tracking_var(ix.w, fb.partial_basket(ix.w, ix.cov, k)[1], ix.cov) for k in (1, 3, 10, 20)]
    assert all(a > b for a, b in zip(v, v[1:], strict=False)) and v[-1] < 1e-18
    idx, h = fb.partial_basket(ix.w, ix.cov, 5)
    assert len(set(idx)) == 5 and np.count_nonzero(h) == 5
    # brute force over all pairs agrees with greedy's first two picks' variance or beats it
    best2 = min(fb.tracking_var(ix.w, _ls(ix, [i, j]), ix.cov) for i in range(20) for j in range(i + 1, 20))
    assert best2 <= fb.tracking_var(ix.w, fb.partial_basket(ix.w, ix.cov, 2)[1], ix.cov) + 1e-15


def _ls(ix, S):
    h = np.zeros(ix.n)
    h[S] = np.linalg.solve(ix.cov[np.ix_(S, S)], (ix.cov @ ix.w)[S])
    return h


def test_fair_future_and_band():
    assert math.isclose(fb.fair_future(100.0, 0.05, 0.02, 0.5), 100.0 * math.exp(0.015))
    lo, hi = fb.basis_band(100.0, 0.05, 0.02, 0.5, 2.0)
    f = fb.fair_future(100.0, 0.05, 0.02, 0.5)
    assert math.isclose(lo, f * 0.9998) and math.isclose(hi, f * 1.0002)
    assert fb.cross_listed(38010.0, 38000.0, 5.0) == 5.0
    assert math.isclose(fb.hedge_ratio(1000.0, 5.0, 150.0), 4.0 / 3.0) and fb.hedge_ratio(50.0, 5.0) == 10.0


def test_trade_legging():
    ix = fb.Index(seed=1)
    slow = fb.trade(ix, 30, leg_us=20.0, n_trades=5000)
    fast = fb.trade(ix, 30, leg_us=2.0, n_trades=5000)
    assert fast["capture"] > slow["capture"] and math.isclose(fast["costs"], slow["costs"])
    full = fb.trade(ix, ix.n, leg_us=0.0, lag_us=1e9, n_trades=100)
    assert abs(full["capture"] - 3.0) < 1e-9 and full["te"] < 1e-6       # every leg early: beta one times the jump
