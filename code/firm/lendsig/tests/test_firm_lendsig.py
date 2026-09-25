import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_lendsig import LendingConfig, crowding, days_to_cover, fee_of, simulate_lending, squeeze_loss  # noqa: E402


def test_fee_schedule():
    cfg = LendingConfig()
    assert fee_of(0.3, cfg) == cfg.gc_fee and abs(fee_of(1.0, cfg) - cfg.fee_max) < 1e-12
    assert abs(fee_of(0.8, cfg) - (0.0025 + (0.4 - 0.0025) * 0.5**3)) < 1e-12


def test_informed_shorts_follow_negative_alpha():
    T, N = 300, 200
    alpha = np.zeros((T, N))
    alpha[:, :50] = -0.001                                             # a quarter of the names will fall
    out = simulate_lending(alpha, np.ones((T, N), bool), np.ones(N), LendingConfig())
    assert np.nanmean(out["si"][-1, :50]) > 2 * np.nanmean(out["si"][-1, 50:])
    assert np.all(out["si"] <= out["supply"][None, :] + 1e-12) and np.nanmax(out["util"]) <= 1.0


def test_signals_and_squeeze():
    assert days_to_cover(0.1, 1e6, 5e3) == 20.0
    c = crowding(np.array([[0.1, 0.2, 0.3]]), np.array([[0.2, 0.1, 0.9]]), np.array([[1.0, 3.0, 2.0]]))
    assert np.allclose(c, [[1 / 6, 0.5, 5 / 6]])
    loss = squeeze_loss(np.array([-0.01, 0.02]), np.array([0.2, 0.2]), np.array([1e6, 1e6]), np.array([1e4, 1e4]),
                        np.array([0.03, 0.03]), cover=0.5, days=5)
    move = math.expm1(5 * 0.7 * 0.03 * math.sqrt(0.5 * 0.2 * 1e6 / (5 * 1e4)))
    assert abs(loss + 0.01 * move) < 1e-12
