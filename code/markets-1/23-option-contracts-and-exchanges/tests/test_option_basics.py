import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from option_basics import count_series, example_book, shares_by_close


def test_a_liquid_name_lists_thousands_of_series():
    assert count_series(weekly=5, monthly=6, quarterly_leaps=5, strikes_near=70, strikes_far=30) == 1840


def test_net_shares_jump_at_each_strike():
    got = shares_by_close(example_book(), [47.00, 47.50, 49.00, 50.00, 50.01, 52.50, 52.51, 54.00])
    assert got == [5000, 1000, 1000, 0, 2500, 2500, -3500, -3500]
