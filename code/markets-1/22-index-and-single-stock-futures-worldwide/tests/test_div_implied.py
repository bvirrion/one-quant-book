import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from div_implied import REGIONS_2025, implied_dividends, implied_growth, trf_pnl_from_spread, trf_price


def test_implied_dividends_invert_the_fair_value():
    assert implied_dividends(5400.0, 5395.0, 0.025, 1.0) == pytest.approx(140.0)


def test_growth_of_a_strip():
    assert implied_growth([100.0, 105.0, 99.75]) == pytest.approx([0.05, -0.05])


def test_trf_is_a_financing_instrument():
    assert trf_price(5400.0, 120.0, 95.0, 40.0, 2.0) == pytest.approx(5400 + 25 + 43.2)
    assert trf_pnl_from_spread(5400.0, 10.0, 100, 5.0, 2.0) == pytest.approx(5400.0)


def test_regional_shares_add_up_to_the_published_total():
    assert sum(v for _, v in REGIONS_2025) == pytest.approx(119.29)
