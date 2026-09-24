import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from short_cost import breakeven_days, carry_short, cascade_path, fee_from_utilisation, squeeze_return


def test_fee_curve_is_flat_then_convex():
    assert fee_from_utilisation(0.3) == fee_from_utilisation(0.75) == 0.003
    assert fee_from_utilisation(1.0) == pytest.approx(0.80)
    mid = fee_from_utilisation(0.875)
    assert mid == pytest.approx(0.003 + 0.797 * 0.25) and mid < (0.003 + 0.80) / 2


def test_carry_charges_the_fee_on_market_value():
    prices = np.array([100.0, 100.0, 200.0])
    pnl, cost = carry_short(prices, np.array([0.36, 0.36, 0.36]), 1000)
    assert list(pnl) == [0.0, 0.0, -100_000.0]
    assert list(cost) == pytest.approx([100.0, 200.0, 400.0])      # the fee doubles with the price
    assert breakeven_days(0.20, 0.36) == pytest.approx(200.0)


def test_squeeze_is_amplified_then_runs_away():
    assert squeeze_return(0.05, 0.3, 0.10, 0.60) == 0.05                        # below every stop
    x = squeeze_return(0.20, 0.3, 0.10, 0.60)
    assert x == pytest.approx((0.20 - 0.06) / 0.4) and x == pytest.approx(cascade_path(0.20, 0.3, 0.10, 0.60)[-1], abs=1e-6)
    assert squeeze_return(0.11, 0.6, 0.10, 0.60) == pytest.approx(0.71)         # k >= b - a: everyone covers
