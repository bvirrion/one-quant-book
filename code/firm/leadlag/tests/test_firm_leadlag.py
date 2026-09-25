import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_leadlag import (
    directional_corr,
    hy_ccf,
    lagged_corr_matrix,
    lead_estimate,
    lead_lag_ratio,
    lead_symmetric,
    linked_feature,
    peer_relative,
    top_pairs,
)


def _pair(lead: float, seed: int = 0):
    """A Brownian path observed at independent Poisson times by two series, series 2 delayed by `lead` seconds."""
    rng = np.random.default_rng(seed)
    grid = np.arange(0.0, 3600.0, 0.01)
    w = np.cumsum(rng.standard_normal(len(grid))) * 0.01
    t1 = np.sort(rng.uniform(0.0, 3600.0, 7200))
    t2 = np.sort(rng.uniform(lead, 3600.0, 7200))
    x1 = np.interp(t1, grid, w)
    x2 = np.interp(t2 - lead, grid, w)
    return t1, x1, t2, x2


def test_hy_lead_recovered():
    lags = np.round(np.arange(-3.0, 3.01, 0.1), 2)
    for lead in (0.0, 0.7, 2.0):
        t1, x1, t2, x2 = _pair(lead)
        c = hy_ccf(t1, x1, t2, x2, lags, norm_step=10.0)
        assert abs(lead_estimate(lags, c) - lead) <= 0.21
        assert abs(lead_symmetric(lags, c, 10) - lead) <= 0.21
        assert 0.8 < c.max() < 1.1
    t1, x1, t2, x2 = _pair(1.0)
    c = hy_ccf(t1, x1, t2, x2, lags, norm_step=10.0)
    assert lead_lag_ratio(lags, c) > 2.0
    ab, ba = directional_corr(t1, x1, t2, x2, 1.0)
    assert ab > 0.5 and abs(ba) < 0.1


def test_symmetric_centre():
    lags = np.round(np.arange(-2.0, 2.001, 0.1), 2)
    flat = np.clip(1.0 - np.abs(lags - 0.6) / 1.5, 0.0, None)
    flat[(lags > 0.1) & (lags < 1.1)] = 0.9 + 0.01 * np.cos(40 * lags[(lags > 0.1) & (lags < 1.1)])   # noisy flat top
    assert lead_symmetric(lags, flat, 10) == 0.6


def test_peer_relative_leave_one_out():
    ret = np.array([[0.01, 0.03, 0.05, 0.02], [0.02, np.nan, 0.04, -0.01]])
    g = np.array([0, 0, 0, 1])
    out = peer_relative(ret, g)
    assert np.allclose(out[0, :3], [0.01 - 0.04, 0.03 - 0.03, 0.05 - 0.02])
    assert np.allclose(out[1, [0, 2]], [0.02 - 0.04, 0.04 - 0.02])
    assert np.isnan(out[1, 1]) and np.isnan(out[0, 3])            # missing, and alone in its group


def test_linked_feature_and_mining():
    v = np.array([[1.0, 2.0, 3.0]])
    assert np.allclose(linked_feature(v, np.array([2, -1, 0]))[0, [0, 2]], [3.0, 1.0])
    assert np.isnan(linked_feature(v, np.array([2, -1, 0]))[0, 1])
    rng = np.random.default_rng(3)
    R = rng.standard_normal((5000, 6))
    R[1:, 4] += 0.5 * R[:-1, 1]                                    # name 4 follows name 1 by a day
    C = lagged_corr_matrix(R, 1)
    assert np.isnan(C[2, 2]) and top_pairs(C, 1) == [(4, 1)]
    assert abs(C[4, 1] - 0.5 / np.sqrt(1.25)) < 0.03
