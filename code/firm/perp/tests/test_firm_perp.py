"""Acceptance tests of the Book 3, Chapter 17 build (perpetual contract engine)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_perp import (
    Source,
    average_premium,
    funding_payment,
    funding_rate,
    impact_price,
    index_price,
    mark_price,
    pnl_inverse,
    pnl_linear,
    pnl_quanto,
    premium_index,
)


def test_index_caps_outliers_and_drops_stale():
    s = [Source(100, 1, 1), Source(101, 1, 1), Source(150, 1, 1), Source(50, 5, 400)]
    # median of fresh = 101; 150 capped at 104.03; stale source dropped
    assert round(index_price(s), 4) == round((100 + 101 + 104.03) / 3, 4)


def test_impact_and_premium():
    asks = [(100.0, 1.0), (101.0, 10.0)]
    assert round(impact_price(asks, 302.0), 4) == round(302 / (1 + 202 / 101), 4)
    assert premium_index(100.5, 100.8, 100.0) == 0.005
    assert premium_index(99.0, 99.5, 100.0) == -0.005
    assert premium_index(99.9, 100.1, 100.0) == 0.0


def test_average_and_funding():
    assert round(average_premium([0.0, 0.0, 0.003]), 12) == 0.0015
    assert round(funding_rate(0.0003), 12) == 0.0001                 # within the clamp: pinned to interest
    assert round(funding_rate(0.002), 6) == 0.0015          # above: premium less the clamp
    assert round(funding_rate(-0.001), 6) == -0.0005
    assert funding_rate(0.05) == 0.02


def test_mark_and_pnl():
    assert mark_price(100.0, 0.001, 0.5, 0.2, 110.0) == 100.2
    assert funding_payment(-2.0, 50_000, 0.0001) == -10.0   # a short receives
    assert pnl_linear(0.5, 60_000, 66_000) == 3_000
    assert round(pnl_inverse(60_000, 60_000, 66_000), 6) == round(1 - 60_000 / 66_000, 6)
    assert round(pnl_quanto(100, 1e-6, 3_000, 3_300), 6) == 0.03
