"""Acceptance tests of the Book 3, Chapter 29 build (market registry and shift planner)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_marketmap import Market, every_day, is_open, open_markets, plan_shifts

CRYPTO = Market("crypto", 20.0, "centralised exchanges", False, every_day(0, 1440))
NYSE = Market("US equities", None, "exchanges", True, every_day(13 * 60 + 30, 20 * 60, range(5)))


def test_open_queries():
    assert is_open(CRYPTO, 6, 0) and not is_open(NYSE, 5, 15 * 60)
    assert open_markets([CRYPTO, NYSE], 2, 14 * 60) == ["crypto", "US equities"]


def test_shifts_cover_the_day():
    s = plan_shifts([CRYPTO, NYSE], 2, 9, 1)
    assert s == [(0, 540, 1), (480, 1020, 2), (960, 60, 2)]            # 0-9, 8-17, 16-1: the whole cycle
    assert plan_shifts([NYSE], 2, 9, 1) == [(810, 1350, 1)]         # one shift covers the equity session
    assert plan_shifts([NYSE], 6, 9, 1) == []
