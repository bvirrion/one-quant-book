"""Acceptance tests of the Chapter 14 build."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_etfmonitor import Basket, Costs, Quote, indicative_nav, premium_bp, read, signal

BASKET = Basket("TRI", 1000, (("AAA", 300), ("BBB", 500), ("CCC", 200)), cash=1_000)
QUOTES = {"AAA": Quote(9_998, 10_002, 100), "BBB": Quote(3_995, 4_005, 100), "CCC": Quote(19_990, 20_010, 100)}
COSTS = Costs(4.0, 1.5, 1.0, 0.5)


def test_indicative_value_by_hand():
    # (300*10000 + 500*4000 + 200*20000 + 1000) / 1000 = 9001
    assert indicative_nav(BASKET, QUOTES) == pytest.approx(9_001.0)


def test_signals_at_and_beyond_the_band():
    inav = 10_000.0
    assert COSTS.band_bp == 7.0
    assert signal(10_007.0, inav, COSTS) == "none"           # exactly on the band: no trade
    assert signal(10_008.0, inav, COSTS) == "create"
    assert signal(9_992.0, inav, COSTS) == "redeem"
    assert premium_bp(10_008.0, inav) == pytest.approx(8.0)


def test_stale_component_rule():
    q = dict(QUOTES)
    q["BBB"] = Quote(3_995, 4_005, 90)                       # 22% of the basket, ten ticks old
    r = read(BASKET, q, 9_010.0, COSTS, now=100)
    assert r.signal == "unreliable" and r.premium_bp is None and r.stale == ("BBB",)
    r = read(BASKET, q, 9_010.0, COSTS, now=100, max_stale_weight=0.25)
    assert r.signal == "create" and r.premium_bp == pytest.approx(9 / 9_001 * 1e4)
    fresh = read(BASKET, QUOTES, 9_001.0, COSTS, now=100)
    assert fresh.signal == "none" and fresh.stale == ()
