"""Acceptance tests of the Chapter 31 build."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_replay import Luld, Tick, depth_within, replay


def calm(t0, t1, price, step=1.0):
    t = t0
    while t < t1:
        yield Tick(t, price - 0.01, price + 0.01, price)
        t += step


def test_bands_double_near_the_open_and_the_close():
    luld = Luld(0.05)
    assert luld.pct(100.0) == 0.10 and luld.pct(1_000.0) == 0.05 and luld.pct(23_400.0 - 1_000.0) == 0.10


def test_reference_moves_only_by_one_percent_and_after_thirty_seconds():
    luld = Luld(0.05)
    for k in calm(1_000, 1_100, 100.0):
        luld.on_tick(k)
    assert luld.reference == pytest.approx(100.0)
    for k in calm(1_100, 1_200, 100.5):                 # the five-minute mean drifts by less than 1%
        luld.on_tick(k)
    assert luld.reference == pytest.approx(100.0)
    for k in calm(1_200, 1_700, 103.0):
        luld.on_tick(k)
    assert luld.reference > 101.0


def test_limit_state_then_pause_then_reopening():
    luld = Luld(0.05)
    ticks = list(calm(1_000, 1_300, 100.0))
    ticks += [Tick(1_300 + i, 94.0, 94.9, None) for i in range(20)]      # the offer sits below the lower band of 95
    ticks += [Tick(1_330.0, 94.0, 94.9, None), Tick(1_330.0 + 300.0, 96.0, 96.1, 96.05)]
    states = [s for _, s, _, _ in replay(ticks, luld)]
    assert states[299] == "normal" and states[300] == "limit" and "paused" in states
    assert [e for _, e in luld.events] == ["limit state", "pause"]
    assert luld.events[1][0] - luld.events[0][0] == pytest.approx(15.0)
    assert states[-1] == "normal" and luld.reference == pytest.approx(96.05)


def test_a_limit_state_that_clears_in_time_causes_no_pause():
    luld = Luld(0.05)
    ticks = list(calm(1_000, 1_300, 100.0)) + [Tick(1_300 + i, 94.0, 94.9, None) for i in range(10)]
    ticks += list(calm(1_310, 1_330, 99.0))
    replay(ticks, luld)
    assert [e for _, e in luld.events] == ["limit state"]


def test_depth_near_the_mid():
    levels = [(99.9, 500), (99.5, 800), (98.0, 5_000), (100.1, 400), (103.0, 9_000)]
    assert depth_within(levels, 100.0, 50) == 1_700 and depth_within(levels, 100.0, 500) == 15_700
