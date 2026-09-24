"""Unit tests of the Chapter 4 teaching module: the claims its figures rest on."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_greeks import hedge_short_straddle, straddle


def test_expected_loss_matches_value_difference_over_seeds():
    target = straddle(100, 100, 1 / 12, 0, 0.25)["price"] - straddle(100, 100, 1 / 12, 0, 0.20)["price"]
    means = [hedge_short_straddle(10_000, 84, seed=s).mean() for s in range(5)]
    assert abs(np.mean(means) + target) < 0.03


def test_error_halves_when_hedges_quadruple():
    sd = {n: hedge_short_straddle(20_000, n, vol_real=0.2, seed=2).std() for n in (21, 84)}
    assert 0.45 < sd[84] / sd[21] < 0.56


def test_time_step_refinement_is_stable():
    a = hedge_short_straddle(20_000, 336, seed=3, hedge_vol=0.25).std()
    b = hedge_short_straddle(20_000, 1344, seed=3, hedge_vol=0.25).std()
    assert b < 0.6 * a            # hedging at the true volatility converges to zero noise
