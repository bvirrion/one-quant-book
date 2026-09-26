import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "feesched"))
from firm_feesched import Tier  # noqa: E402
from firm_venuefees import (  # noqa: E402
    Schedule,
    effective_tick,
    fee_adjusted,
    indifference_make,
    neutral_ask,
    passive_value,
    route_take,
    tier_make_fee,
)


def test_fee_adjusted_and_routing():
    assert math.isclose(fee_adjusted(10.00, 1, 0.003), 10.003)
    assert math.isclose(fee_adjusted(10.00, -1, -0.0002), 10.0002)
    # a buy of 500: the inverted venue's ask at 10.00 is cheaper all-in than the maker-taker ask at 10.00
    quotes = [("MT", 10.00, 300, 0.003), ("INV", 10.00, 200, -0.0002), ("MT", 10.01, 1000, 0.003)]
    assert route_take(quotes, 1, 500) == [("INV", 10.00, 200), ("MT", 10.00, 300)]
    # a sell takes the bid with the highest fee-adjusted price
    bids = [("MT", 9.99, 100, 0.003), ("INV", 9.99, 100, -0.0002)]
    assert route_take(bids, -1, 150) == [("INV", 9.99, 100), ("MT", 9.99, 50)]


def test_effective_tick():
    assert math.isclose(effective_tick(0.01, [0.003, -0.0002]), 0.0032)
    assert math.isclose(effective_tick(0.01, [0.003, 0.003]), 0.01)
    assert math.isclose(effective_tick(0.01, [0.003, -0.0002, 0.0010]), 0.0012)


def test_values_and_neutrality():
    assert math.isclose(passive_value(0.5, 0.005, 0.002, -0.0016), 0.0023)
    m = indifference_make(0.2, 0.004, 0.4, 0.003, 0.002)
    assert math.isclose(0.2 * (0.004 - m), 0.4 * (0.003 - 0.002))
    assert math.isclose(neutral_ask(10.01, 0.003, 0.001), 10.012)
    assert math.isclose(neutral_ask(10.01, 0.003, 0.001, 0.01), 10.02)
    s = Schedule("X", 0.0010, 0.0030, (Tier("t1", 0.002, -0.0020),))
    assert (tier_make_fee(s, 1e6, 1e9), tier_make_fee(s, 3e6, 1e9)) == (0.0010, -0.0020)
