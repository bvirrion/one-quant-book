"""Tests of the Chapter 23 demo: chart data shapes and the auction replay."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from cds_demo import BIDS, OFFERS, order_book, problem, survival_curves, upfront_curve


def test_upfront_curve_crosses_zero_at_the_coupons():
    rows = dict((s, (a, b)) for s, a, b in upfront_curve())
    assert abs(rows[100][0]) < 1e-9 and abs(rows[500][1]) < 1e-9
    assert all(x[0] < y[0] for x, y in zip(list(rows.values()), list(rows.values())[1:], strict=False))


def test_survival_decreasing_and_ordered():
    rows = survival_curves()
    assert rows[0][1:] == (1.0, 1.0, 1.0)
    assert all(a > b > c for _, a, b, c in rows[1:])


def test_lehman_submissions_are_valid_quotes():
    assert len(BIDS) == len(OFFERS) == 14
    assert all(0 < o - b <= 2 for b, o in zip(BIDS, OFFERS, strict=True))


def test_book_meets_the_open_interest_at_the_final_price():
    p = problem()
    book = order_book()
    first = next(price for price, _, cum in book if cum >= p["oi"])
    assert first == p["final"] == 8.625
