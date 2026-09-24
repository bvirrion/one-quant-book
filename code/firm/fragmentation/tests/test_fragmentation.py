"""Acceptance tests of the Chapter 11 build."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_fragmentation import Monitor, VenueTrade


def test_shares_and_the_example_herfindahl():
    m = Monitor()
    for venue, v in (("XPAR", 60), ("CEUX", 20), ("AQEU", 10), ("TQEX", 10)):
        m.add(VenueTrade("FR1", venue, "lit", v, 1))
    assert sum(m.shares("FR1", "venue").values()) == pytest.approx(1.0)
    assert m.effective_venues("FR1") == pytest.approx(1 / 0.42)


def filled(dark=8, lis=5):
    m = Monitor()
    for month in range(1, 13):
        m.add(VenueTrade("FR1", "XPAR", "lit", 100 - dark - lis, month))
        m.add(VenueTrade("FR1", "CEUX", "dark_rpw", dark, month))
        m.add(VenueTrade("FR1", "CEUX", "dark_lis", lis, month))
    return m


def test_cap_usage_on_a_constant_series_and_lis_exclusion():
    m = filled()
    assert m.cap_usage("FR1", 12) == pytest.approx(0.08)          # the 5 % of blocks does not count
    assert m.cap_usage("FR1", 11) is None                          # eleven months: no figure


def test_headroom_brings_usage_exactly_to_the_cap():
    m = filled(dark=6)
    h = m.headroom("FR1", 12, next_total=100)
    assert h == pytest.approx(0.07 * 1200 - 66)
    assert (66 + h) / 1200 == pytest.approx(0.07)


def test_rejects_unknown_mechanism():
    with pytest.raises(ValueError):
        Monitor().add(VenueTrade("X", "V", "whisper", 1, 1))
