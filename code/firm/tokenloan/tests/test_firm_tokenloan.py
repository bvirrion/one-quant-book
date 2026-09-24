"""Acceptance tests of the Book 3, Chapter 24 build (token market-making agreement)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "ledger"))
from firm_ledger import Ledger
from firm_tokenloan import (
    Deal,
    call_bs,
    day_one_hedge,
    delta_schedule,
    implied_fee,
    obligations_met,
    package_value,
    package_value_mc,
    post_fee,
)

DEAL = Deal(2_000_000, 0.50, 1.0, 1.2, ((666_667, 0.75), (666_667, 1.00), (666_666, 1.50)))


def test_monte_carlo_matches_closed_form():
    assert abs(package_value_mc(DEAL) / package_value(DEAL) - 1) < 0.01


def test_call_limits():
    v, d = call_bs(1.0, 1e-9, 1.0, 1.0)
    assert abs(v - 1.0) < 1e-6 and abs(d - 1.0) < 1e-6
    assert call_bs(1.0, 1.0, 1.0, 0.8)[1] > 0.5              # driftless ATM delta above one half


def test_fee_and_hedge():
    assert 0 < implied_fee(DEAL) < 1
    h = day_one_hedge(DEAL)
    assert 0 < h < 2_000_000
    sched = dict(delta_schedule(DEAL, [0.25, 0.5, 1.0, 2.0], 0.5))
    assert sched[0.25] < sched[0.5] < sched[1.0] < sched[2.0] <= 2_000_000


def test_obligations_and_ledger():
    assert obligations_met(80, 60_000, 0.97) and not obligations_met(150, 60_000, 0.97)
    led = Ledger()
    n = post_fee(led, DEAL, 1)
    assert led.balance("desk.crypto") == n and led.by_category("desk.crypto") == {"fee": n}
