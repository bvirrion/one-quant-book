"""Tutorial of Book 2, Chapter 2: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from money_market_demo import bill_curve, one_week_by_start


def test_thirteen_week_row():
    row = next(r for r in bill_curve() if r["weeks"] == 13)
    assert row["price"] == 99.034389
    assert (round(row["mmy"] * 100, 4), round(row["bey"] * 100, 4)) == (3.8572, 3.9108)


def test_money_market_yields_are_not_monotonic_but_discounts_are():
    rows = bill_curve()
    assert all(a["discount"] > b["discount"] for a, b in zip(rows, rows[1:], strict=False))
    assert rows[-1]["mmy"] > rows[-2]["mmy"]
    assert all(r["discount"] < r["mmy"] < r["bey"] for r in rows)


def test_quarter_end_is_priced_for_a_week():
    rates = dict(one_week_by_start())
    spanning = [r for d, r in rates.items() if d.month == 9 and d.day >= 24]
    plain = [r for d, r in rates.items() if d.month == 9 and d.day <= 23]
    assert min(spanning) - max(plain) > 1.0e-4
