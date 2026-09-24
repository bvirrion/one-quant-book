import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from whoearns import Day, break_even_volume, simulate_day


def test_money_is_conserved_outside_price_moves():
    d = simulate_day(3)
    # what customers pay in spread and commission is what the others receive
    # before position P&L and before fees between professionals
    assert d["customers_cost"] == pytest.approx(-(d["mm_spread_earned"] + d["broker_commission"]))


def test_informed_flow_costs_the_market_maker():
    small = Day(n_orders=4_000)
    toxic = Day(n_orders=4_000, informed=0.30)
    loss = [simulate_day(s, toxic)["mm_position_pnl"] for s in range(40)]
    # theory: -p * J * shares = -0.30 * 0.03 * 400 000 = -3 600 a day
    assert sum(loss) / len(loss) == pytest.approx(-3_600, rel=0.35)
    assert simulate_day(5, small)["mm_spread_earned"] == simulate_day(5, toxic)["mm_spread_earned"]


def test_deterministic():
    assert simulate_day(1) == simulate_day(1)


def test_break_even():
    assert break_even_volume(90_000, 0.0045) == pytest.approx(20e6)
    with pytest.raises(ValueError):
        break_even_volume(1.0, 0.0)
