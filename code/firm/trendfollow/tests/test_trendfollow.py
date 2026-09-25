import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_trendfollow import breakout, ewma_vol, ma_cross, positions, run, tsmom, vol_target  # noqa: E402


def test_signals_by_hand():
    r = np.array([[0.01], [0.01], [-0.05], [0.02], [0.02], [0.02]])
    assert tsmom(r, 2)[:, 0].tolist() == [0, 0, -1, -1, 1, 1]
    b = breakout(r, 2)[:, 0].tolist()
    assert b == [0, 0, -1, -1, 1, 1]
    m = ma_cross(r, 1, 3)[:, 0].tolist()
    assert m[:2] == [0, 0] and m[2] == -1 and m[5] == 1


def test_positions_run_and_costs():
    r = np.array([[0.0, 0.0], [0.01, -0.02], [0.02, 0.01]])
    pos = positions(np.array([[1, -1], [1, 1], [1, 1]]), np.full((3, 2), 0.2), 0.4)
    assert np.allclose(pos[0], [1.0, -1.0])
    pnl = run(r, pos, 0.001)
    assert math.isclose(pnl[0], -0.002) and math.isclose(pnl[1], 0.01 + 0.02 - 0.002) and math.isclose(pnl[2], 0.03)


def test_ewma_vol_and_targeting():
    rng = np.random.default_rng(3)
    r = 0.01 * rng.standard_normal((5000, 1))
    assert abs(ewma_vol(r)[-2000:].mean() / (0.01 * math.sqrt(252)) - 1) < 0.05
    x = np.concatenate([0.005 * rng.standard_normal(3000), 0.02 * rng.standard_normal(3000)])
    v = vol_target(x, 0.10)
    assert abs(v[500:3000].std() * math.sqrt(252) - 0.10) < 0.01 and abs(v[3500:].std() * math.sqrt(252) - 0.10) < 0.01
