"""Tutorial of Book 2, Chapter 4: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/tsyauction"))
from firm_tsyauction import coupon_from_high_yield
from tsy_auction_demo import OFFERING, demand_curve, summary


def test_summary_as_printed():
    s = summary()
    assert round(s["stop"] * 100, 3) == 4.198 and round(s["tail_bp"], 1) == 1.8
    assert round(s["btc"], 2) == 1.82 and round(s["allot"] * 100, 2) == 95.02
    assert (round(s["indirect"] * 100, 1), round(s["direct"] * 100, 1), round(s["dealers"] * 100, 1)) == (51.1, 10.6, 38.3)
    assert round(s["tendered"] / 1000, 1) == 76.1
    assert coupon_from_high_yield(s["stop"]) == 4.125


def test_demand_curve_crosses_capacity_at_the_stop():
    curve = demand_curve()
    first = next(y for y, c in curve if c >= OFFERING - 300)
    assert round(first * 100, 3) == 4.198
    assert all(a[1] < b[1] for a, b in zip(curve, curve[1:], strict=False))
