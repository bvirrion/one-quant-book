"""Acceptance tests of the Book 2, Chapter 31 build (calendar and screen)."""
import datetime as dt
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_macrocal import (
    Event,
    blackout,
    calendar,
    classify,
    curve_summary,
    dv01_neutral,
    event_day_moves,
    sensitivity,
    steepener_pnl,
)


def test_blackout_rule_examples():
    # Tuesday-Wednesday meeting: from the Saturday ten days before to the Thursday after
    assert blackout(dt.date(2026, 9, 15), dt.date(2026, 9, 16)) == (dt.date(2026, 9, 5), dt.date(2026, 9, 17))
    s, _ = blackout(dt.date(2026, 1, 27), dt.date(2026, 1, 28))
    assert s == dt.date(2026, 1, 17) and s.weekday() == 5


def test_calendar_flags():
    ev = [Event(dt.date(2026, 9, 11), "08:30 ET", "CPI"), Event(dt.date(2026, 9, 4), "08:30 ET", "payrolls")]
    cal = calendar(ev, [(dt.date(2026, 9, 15), dt.date(2026, 9, 16))])
    assert [(e.name, b) for e, b in cal] == [("payrolls", False), ("CPI", True)]


def test_curve_and_moves():
    c = curve_summary(4.71, 4.83, 4.96, 5.29)
    assert round(c["2s10s"]) == 25 and round(c["5s30s"]) == 46 and round(c["2s5s10s"]) == -1
    assert classify(-28, -19) == "bull steepening" and classify(23, 13) == "bear flattening"
    assert classify(5, 10) == "bear steepening" and classify(-10, -15) == "bull flattening"


def test_event_moves_dv01_and_pnl():
    on, off, n_on, n_off = event_day_moves(["a", "b", "c", "d"], [1.0, 1.1, 1.1, 1.3], {"b", "d"})
    assert (round(on, 6), round(off, 6), n_on, n_off) == (15.0, 0.0, 2, 1)
    assert dv01_neutral(0.08, 0.02, 100e6) == 400e6
    assert steepener_pnl(1000.0, -28, -19) == 9000.0


def test_sensitivity_recovers_beta():
    rng = random.Random(1)
    xs = [rng.gauss(0, 1) for _ in range(2000)]
    ys = [8 * x + rng.gauss(0, 3) for x in xs]
    b, se = sensitivity(xs, ys)
    assert abs(b - 8) < 4 * se
