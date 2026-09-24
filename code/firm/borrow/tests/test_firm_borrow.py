"""Acceptance tests of the Chapter 16 build."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "financing"))
from firm_borrow import BorrowBook, FeeCurve, Line
from firm_financing import FinancingTerms, accrue


def book():
    return BorrowBook(FeeCurve(), {"EASY": Line(1_000_000, 200_000), "HARD": Line(1_000_000, 850_000)})


def test_locate_and_fee_levels():
    b = book()
    assert b.locate("EASY", 50_000) == 50_000 and b.locate("HARD", 200_000) == 150_000 and b.locate("NONE", 1) == 0
    assert b.borrow_fees()["EASY"] == 0.003
    assert b.borrow_fees()["HARD"] == pytest.approx(0.003 + 0.797 * 0.16)       # u = 0.85


def test_our_own_borrow_moves_the_fee():
    b = book()
    assert b.borrow("HARD", 100_000) == 100_000
    assert b.utilisation("HARD") == pytest.approx(0.95)
    assert b.borrow_fees()["HARD"] == pytest.approx(0.003 + 0.797 * 0.64)


def test_recall_forces_a_pro_rata_buy_in():
    b = book()
    b.borrow("HARD", 100_000)
    assert b.recall("HARD", 40_000) == 0                                         # still 10,000 spare
    assert b.recall("HARD", 105_000) == 10_000                                   # 95,000 short of supply
    ln = b.lines["HARD"]
    assert ln.ours == 90_000 and ln.ours + ln.on_loan_others == ln.lendable == 855_000


def test_feeds_the_financing_accrual():
    b = book()
    b.borrow("HARD", 100_000)
    acc = accrue(dt.date(2026, 9, 16), {"HARD": -100_000}, {"HARD": 20.0}, 5e6, 0.04,
                 FinancingTerms(0.005, 0.005), b.borrow_fees())
    assert acc.borrow_fees == pytest.approx(-2e6 * (0.003 + 0.797 * 0.64) / 360)
