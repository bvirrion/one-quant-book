import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_curvestrat import band, pair_pnl, positions, serials, spread_carry, zscore  # noqa: E402


def test_serials_and_pair_through_expiry():
    # contracts A, B, C, D with prices 10, 11, 12, 13 on day 0; A expires on day 1
    C = np.array([[10.0, 11.0, 12.0, 13.0],
                  [10.5, 11.2, 12.1, 13.0],
                  [11.4, 12.4, 13.3, 14.0],        # B is now contract 1
                  [11.0, 12.0, 13.0, 14.0]])
    exp = np.array([False, True, False, False])
    m = serials(exp)
    assert m.tolist() == [0, 0, 1, 1]
    pnl, spread = pair_pnl(C, m, 0, 2, exp)
    # days 0 and 1 are within 2 days of A's expiry: the pair is B-C; from day 2 it is B-C again (now 1-2)
    assert math.isclose(pnl[1], (11.2 - 11.0) - (12.1 - 12.0))
    assert math.isclose(pnl[2], (11.4 - 11.2) - (12.4 - 12.1))
    assert math.isclose(pnl[3], (11.0 - 11.4) - (12.0 - 12.4))
    assert math.isclose(spread[0], math.log(11 / 12))


def test_zscore_band_positions_carry():
    x = np.concatenate([np.zeros(30), [3.0], np.zeros(5)])
    x[:30] = np.tile([0.1, -0.1], 15)
    z = zscore(x, 20)
    assert z[30] > 3
    p = band(z, np.ones(36), 1.5, 0.5, 0.1)
    assert p[30] == -0.1 and p[31] == 0.0
    assert band(-z, np.ones(36), 1.5, 0.5, 0.1, block=np.ones(36, bool))[30] == 0.0
    assert np.allclose(positions(np.array([1.0, -3.0]), np.array([2.0, 2.0]), 1.0, 2.0), [-0.5, 1.0])
    assert math.isclose(spread_carry(-0.01, 21), -0.12)
