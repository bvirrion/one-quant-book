import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_structrv import discount_trade, simulate_discount, spac_payoff, spac_return  # noqa: E402


def test_discount_mean_reverts_and_catalysts_close_it():
    D, cat = simulate_discount(-0.3, -0.1, 126, 0.0, 1000, 0.0, paths=10, rng=np.random.default_rng(0))
    assert np.allclose(D[:, 126], -0.1 - 0.2 * 0.5, atol=1e-12) and (cat == -1).all()
    D2, cat2 = simulate_discount(-0.15, -0.1, 504, 0.05, 504, 2.0, -0.02, 2000, np.random.default_rng(1))
    assert (cat2 > 0).mean() > 0.9 and np.allclose(D2[cat2 > 0, -1], -0.02)


def test_trade_exit_and_return_by_hand():
    D = np.array([[-0.15, -0.10, -0.04, -0.03], [-0.15, -0.16, -0.14, -0.13]])
    ret, day = discount_trade(D, np.array([-1, 2]), -0.05, 0.0252, 3)
    assert day.tolist() == [2, 2]
    assert np.allclose(ret, [-0.04 + 0.15 - 0.0252 * 2 / 252, -0.14 + 0.15 - 0.0252 * 2 / 252])


def test_spac():
    assert spac_payoff(10.4, np.array([8.0, 12.0])).tolist() == [10.4, 12.0]
    r = spac_return(9.8, 10.0, 0.04, 252, np.array([5.0]))
    assert abs(r[0] - (10 * math.exp(0.04) / 9.8 - 1)) < 1e-12
