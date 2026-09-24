"""Acceptance tests of the Chapter 25 build."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_parity import (
    conversion_edge,
    implied_dividends_pv,
    implied_forward,
    implied_vol,
    price,
    reversal_edge,
    variance_strip,
)

F, T, R = 100.5, 0.25, 0.04


def test_parity_holds_for_the_pricer_itself():
    for k in (90.0, 100.0, 110.0):
        c, p = price(F, k, T, R, 0.22, "C"), price(F, k, T, R, 0.22, "P")
        assert c - p == pytest.approx(math.exp(-R * T) * (F - k))
        assert implied_forward(c, p, k, T, R) == pytest.approx(F)


def test_implied_vol_round_trip_and_bounds():
    for vol in (0.08, 0.2, 0.65):
        for k, right in ((85.0, "P"), (100.0, "C"), (120.0, "C")):
            assert implied_vol(price(F, k, T, R, vol, right), F, k, T, R, right) == pytest.approx(vol, abs=1e-7)
    with pytest.raises(ValueError):
        implied_vol(0.10, F, 90.0, T, R, "C")             # below intrinsic value
    with pytest.raises(ValueError):
        implied_vol(200.0, F, 90.0, T, R, "C")


def test_dividends_from_the_forward():
    spot = 100.0
    fwd = (spot - 0.8 * math.exp(-R * 0.1)) * math.exp(R * T)      # one dividend of 0.80 in 0.1 year
    assert implied_dividends_pv(spot, fwd, T, R) == pytest.approx(0.8 * math.exp(-R * 0.1))


def test_conversion_and_reversal_are_unprofitable_inside_the_quotes():
    spot_bid, spot_ask, k, div = 99.98, 100.02, 100.0, 0.0
    fwd = 100.0 * math.exp(R * T)
    c, p = price(fwd, k, T, R, 0.2, "C"), price(fwd, k, T, R, 0.2, "P")
    assert conversion_edge(c - 0.03, p + 0.03, spot_ask, k, T, R, div) < 0
    assert reversal_edge(c + 0.03, p - 0.03, spot_bid, k, T, R, div) < 0
    assert conversion_edge(c + 0.40, p - 0.03, spot_ask, k, T, R, div) > 0      # a call bid 40 cents too high


def test_variance_strip_recovers_a_flat_volatility():
    vol, t = 0.20, 30 / 365
    strikes = [k / 2 for k in range(120, 281)]                                   # 60 to 140 by 0.5
    k0 = max(k for k in strikes if k <= F)
    quotes = []
    for k in strikes:
        if k < k0:
            q = price(F, k, t, R, vol, "P")
        elif k > k0:
            q = price(F, k, t, R, vol, "C")
        else:
            q = 0.5 * (price(F, k, t, R, vol, "P") + price(F, k, t, R, vol, "C"))
        quotes.append((k, q))
    assert math.sqrt(variance_strip(F, t, R, quotes)) == pytest.approx(vol, abs=2e-4)
