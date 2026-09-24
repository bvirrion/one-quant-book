"""Acceptance tests of the Chapter 17 build."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_wrappers import Investor, WrapperTerms, cost, rank

SHARES = WrapperTerms("shares", False, 5, 5, 50, 0, 50, 40, 0, 0, 0.15)
ETF = WrapperTerms("ETF", False, 3, 3, 0, 7, 50, 40, 0, 0, 0.15)
FUTURE = WrapperTerms("future", True, 1, 1, 0, 0, 30, -30, 1.5, 4, 0.15)
SWAP = WrapperTerms("swap", True, 3, 3, 0, 0, 40, 40, 0, 0, 0.05)
NOTE = WrapperTerms("note", True, 10, 10, 0, 30, 0, 0, 0, 0, 0.15, shortable=False)
ALL = [SHARES, ETF, FUTURE, SWAP, NOTE]


def test_cash_investor_one_year():
    q = rank(ALL, Investor(0.0), 1.0, 200.0)
    assert [x.name for x in q] == ["ETF", "swap", "future", "note", "shares"]
    assert q[0].total_bp == pytest.approx(43.0) and q[-1].total_bp == pytest.approx(90.0)


def test_leveraged_investor_prefers_synthetics():
    q = rank(ALL, Investor(1.0), 1.0, 200.0)
    assert [x.name for x in q][:2] == ["swap", "future"] and q[0].total_bp == pytest.approx(56.0)


def test_tax_exempt_holder_of_shares_over_five_years():
    inv = Investor(0.0, {"shares": 0.0, "ETF": 0.0})
    q = {x.name: x.total_bp for x in rank(ALL, inv, 5.0, 200.0)}
    assert q["shares"] == pytest.approx(60.0) and q["ETF"] == pytest.approx(41.0) and q["future"] == pytest.approx(332.0)


def test_short_side():
    q = rank(ALL, Investor(0.0), 1.0, 200.0, side=-1, borrow_fee_bp=25.0)
    assert "note" not in [x.name for x in q]
    fut = cost(FUTURE, Investor(0.0), 1.0, 200.0, side=-1, borrow_fee_bp=0.0)
    assert fut.total_bp == pytest.approx(2 + 6 - 30)          # the short future earns the rich financing
    etf = cost(ETF, Investor(0.0), 1.0, 200.0, side=-1, borrow_fee_bp=25.0)
    assert etf.total_bp == pytest.approx(6 - 7 + 65)
    with pytest.raises(ValueError):
        cost(NOTE, Investor(0.0), 1.0, 200.0, side=-1)
