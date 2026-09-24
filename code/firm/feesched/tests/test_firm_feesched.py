"""Acceptance tests of the Chapter 29 build."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_feesched import Schedule, Tier, all_in_per_share, breakeven_natural_volume, extra_volume_worth_adding

MT = Schedule("maker-taker", -0.0016, 0.0030, (
    Tier("1", 0.0006, -0.0020), Tier("2", 0.0020, -0.0023), Tier("3", 0.0025, -0.0028), Tier("7", 0.0100, -0.0031)))
TCV = 12e9


def test_tier_lookup():
    assert MT.add_rate(5e6, TCV) == -0.0016                      # 0.042% of TCV: base rate
    assert MT.add_rate(7.2e6, TCV) == -0.0020                    # exactly 0.06%
    assert MT.add_rate(30e6, TCV) == -0.0028 and MT.add_rate(200e6, TCV) == -0.0031
    assert MT.next_tier(9e6, TCV).name == "2" and MT.next_tier(200e6, TCV) is None


def test_the_cliff():
    below, above = MT.daily_bill(23.9e6, 0, TCV), MT.daily_bill(24.0e6, 0, TCV)
    assert below == pytest.approx(-47_800) and above == pytest.approx(-55_200)
    assert above - below == pytest.approx(-7_400)                # 100,000 more shares, $7,400 more rebate


def test_padding_volume():
    extra, gain = extra_volume_worth_adding(MT, 9e6, TCV, 0.0027)
    assert extra == pytest.approx(15e6) and gain == pytest.approx(24e6 * 0.0023 - 15e6 * 0.0027 - 9e6 * 0.0020)
    assert gain < 0
    extra, gain = extra_volume_worth_adding(MT, 20e6, TCV, 0.0027)
    assert extra == pytest.approx(4e6) and gain == pytest.approx(4_400)
    be = breakeven_natural_volume(0.0020, 0.0023, 24e6, 0.0027)
    assert be == pytest.approx(24e6 * 4 / 7)
    assert extra_volume_worth_adding(MT, be * 1.001, TCV, 0.0027)[1] > 0 > extra_volume_worth_adding(MT, be * 0.999, TCV, 0.0027)[1]
    assert breakeven_natural_volume(0.0020, 0.0023, 24e6, 0.0010) == 0.0


def test_all_in():
    a = all_in_per_share(MT, 30e6, TCV, True, 0.0002, 0.0001)
    assert a.total == pytest.approx(-0.0025)
    assert all_in_per_share(MT, 30e6, TCV, False, 0.0002, 0.0001).total == pytest.approx(0.0033)
