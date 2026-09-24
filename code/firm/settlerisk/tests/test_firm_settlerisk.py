"""Acceptance tests of the Book 2, Chapter 20 build (settlement exposure)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_settlerisk import Trade, exposure_at, net_by_counterparty, peak, profile, window

TIMES = {"JPY": (-2.0, 7.0), "EUR": (6.0, 16.0), "USD": (13.0, 21.0)}


def test_window_direction():
    assert window(Trade("A", "JPY", "USD", 1.0), TIMES) == (-2.0, 21.0)     # the Herstatt direction
    assert window(Trade("A", "USD", "JPY", 1.0), TIMES) == (13.0, 13.0)     # receipt before the deadline


def test_exposure_and_pvp():
    trades = [Trade("A", "EUR", "USD", 100.0), Trade("B", "JPY", "USD", 50.0)]
    assert exposure_at(14.0, trades, TIMES) == 150.0 and exposure_at(22.0, trades, TIMES) == 0.0
    assert peak(profile(trades, TIMES, pvp={"EUR", "USD", "JPY"})) == 0.0


def test_netting_reduces_payments():
    trades = [Trade("A", "EUR", "USD", 100.0), Trade("A", "USD", "EUR", 60.0)]
    net = net_by_counterparty(trades)
    assert len(net) == 1 and net[0].sell == "EUR" and math.isclose(net[0].value_usd, 40.0)
    assert peak(profile(net, TIMES)) < peak(profile(trades, TIMES))
