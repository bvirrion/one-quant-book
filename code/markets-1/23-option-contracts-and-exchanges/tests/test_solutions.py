"""Numbers gate: every numerical answer printed in the Chapter 23 text and solutions."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from option_basics import count_series, example_book, shares_by_close

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/chain"))
from firm_chain import Series, expiry_shares, parse_osi


def test_text():
    assert count_series(5, 6, 5, 70, 30) == 2 * (11 * 70 + 5 * 30) == 1840
    s = parse_osi("XYZ   261218C00052500")
    assert (s.expiry, s.right, s.strike) == (dt.date(2026, 12, 18), "C", 52.5)


def test_exercises():
    p = parse_osi("XYZ   270115P00047500")
    assert (p.expiry, p.right, p.strike) == (dt.date(2027, 1, 15), "P", 47.5)
    assert Series("XYZ", dt.date(2027, 3, 19), "C", 112_500).osi == "XYZ   270319C00112500"
    call = Series("XYZ", dt.date(2026, 12, 18), "C", 50_000)
    assert call.payoff(56.0, 2.40, 10) == pytest.approx(3_600) and call.payoff(48.0, 2.40, 10) == pytest.approx(-2_400)
    assert 1840 * 16 == 29_440
    assert shares_by_close(example_book(), [47.00, 49.00, 50.00, 50.01, 52.50, 52.51]) == [5000, 1000, 0, 2500, 2500, -3500]
    assert 0.60 > 0.15
    c50 = next(s for s in example_book() if s.right == "C" and s.strike_milli == 50_000)
    assert expiry_shares(example_book(), 50.01) == 2500 and expiry_shares(example_book(), 50.01, {c50: False}) == 0


def test_problem():
    book = example_book()
    assert expiry_shares(book, 52.48) == 2_500 and round(52.48 - 50.0, 2) == 2.48 and round(52.50 - 52.48, 2) == 0.02
    assert -1_900 + 2_500 == 600
    assert 45 * 100 == 4_500 and -1_900 + 2_500 - 4_500 == -3_900
    assert 4_500 * (54.10 - 52.50) == pytest.approx(7_200)
    assert 60 * 100 * 0.04 == pytest.approx(240) and 7_200 / 240 == pytest.approx(30)
    assert 3_000 * (54.10 - 52.48) == pytest.approx(4_860)
