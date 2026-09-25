import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_commspread import SpreadConfig, board_crush, crack_321, fade, seasonal, simulate_spreads, spark  # noqa: E402


def test_spread_construction():
    assert crack_321(80.0, 2.5, 3.0) == 32.0 and spark(50.0, 3.0, 7.0) == 29.0
    assert abs(board_crush(10.0, 300.0, 50.0) - 2.1) < 1e-12


def test_fade_by_hand():
    cfg = SpreadConfig(window=3, band=1.0, cost=0.1)
    x = np.array([0.0, 1.0, 0.0, 5.0, 4.0, 1.0, 0.0])
    pnl, pos = fade(x, cfg)
    assert pos.tolist() == [0.0, 0.0, 0.0, -1.0, -1.0, 0.0, 1.0]
    assert np.allclose(pnl, [0, 0, 0, -0.1, 1.0, 3.0 - 0.1, -0.1])


def test_seasonal_holds_february_to_april():
    month = np.array([1, 2, 3, 4, 5])
    p = seasonal(np.array([0.0, 1.0, 3.0, 6.0, 10.0]), month, SpreadConfig(cost=0.0))
    assert p.tolist() == [0.0, 0.0, 2.0, 3.0, 4.0]


def test_simulation_shape_and_bottleneck():
    cfg = SpreadConfig()
    s = simulate_spreads(cfg)
    a = cfg.shock_start
    assert s["level"][a + cfg.shock_days - 1] == cfg.loc_mean + cfg.shock_size and s["level"][a - 1] == cfg.loc_mean
    assert np.corrcoef(np.diff(s["crack"]), np.diff(s["crude"]))[0, 1] < 0
