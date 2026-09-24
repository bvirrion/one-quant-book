"""Acceptance tests of the Book 3, Chapter 13 build (nominations and credit)."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_nominate import Nomination, carry_cost, counterparty_mismatches, in_time, uncovered_exposure


def test_balanced_and_unbalanced():
    a = Nomination("GROUP-A")
    a.injections[1] = 50.0
    a.add_trade(1, "GROUP-B", -50.0)
    a.withdrawals[2] = 20.0
    assert a.unbalanced(range(1, 3)) == {2: -20.0}
    with pytest.raises(ValueError):
        a.add_trade(1, "GROUP-A", 1.0)


def test_counterparty_matching():
    a, b = Nomination("A"), Nomination("B")
    a.add_trade(1, "B", -50.0)
    b.add_trade(1, "A", 50.0)
    b.add_trade(2, "A", 10.0)
    assert counterparty_mismatches(a, b, range(1, 3)) == {2: 10.0}


def test_deadline_and_credit():
    assert in_time(dt.datetime(2026, 9, 24, 14, 0), dt.date(2026, 9, 25), dt.time(14, 30))
    assert not in_time(dt.datetime(2026, 9, 24, 14, 31), dt.date(2026, 9, 25), dt.time(14, 30))
    assert uncovered_exposure(3e6, -1e6, 2e6) == 1e6 and uncovered_exposure(1e6, 5e5, 2e6) == 0.0
    assert carry_cost(4e6, 0.05) == 200_000
