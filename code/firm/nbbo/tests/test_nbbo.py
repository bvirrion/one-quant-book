"""Acceptance tests of the Chapter 9 build (Python reference)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_nbbo import NbboBuilder, Quote


def book():
    b = NbboBuilder()
    b.update(Quote("XNYS", 100_000, 300, 100_200, 500))
    b.update(Quote("XNAS", 100_100, 200, 100_200, 100))
    b.update(Quote("IEXG", 100_100, 400, 100_300, 900))
    return b


def test_best_prices_sizes_and_venues():
    n = book().nbbo()
    assert (n.bid, n.bid_size, n.bid_venues) == (100_100, 600, ("IEXG", "XNAS"))
    assert (n.ask, n.ask_size, n.ask_venues) == (100_200, 600, ("XNAS", "XNYS"))


def test_odd_lots_are_not_protected():
    b = book()
    assert b.update(Quote("ARCX", 100_150, 60, 100_400, 100)) is None       # better bid, odd lot: ignored
    assert b.update(Quote("ARCX", 100_150, 100, 100_400, 100)).bid == 100_150


def test_update_reports_only_changes():
    b = book()
    assert b.update(Quote("XNYS", 100_000, 900, 100_200, 500)) is None      # away from the best bid
    assert b.update(Quote("XNYS", 100_000, 300, 100_200, 700)).ask_size == 800


def test_locked_and_crossed():
    b = book()
    assert b.update(Quote("XNYS", 100_200, 300, 100_300, 500)).locked
    assert b.update(Quote("XNYS", 100_250, 300, 100_300, 500)).crossed


def test_trade_through():
    b = book()
    assert b.trades_through(+1, 100_300) and not b.trades_through(+1, 100_200)
    assert b.trades_through(-1, 100_000) and not b.trades_through(-1, 100_100)


def test_rejects_bad_quotes():
    with pytest.raises(ValueError):
        NbboBuilder().update(Quote("X", 0, 100, 1, 100))
