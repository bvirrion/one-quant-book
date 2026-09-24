"""Numbers gate: every numerical answer printed in Book 3, Chapter 2 (text and solutions)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/crude"))
from firm_crude import api_gravity, cl_last_trading_day, quality_adjusted, storage_floor
from m3_crude import april_20, quality_examples, spread_stats

A = april_20()
S = spread_stats()


def test_text():
    q = quality_examples()
    assert round(q["api"], 1) == 39.6 and round(q["adjusted"] - 80.0, 2) == 0.34
    assert q["grade"] == "Forties" and q["benchmark"] == 81.05
    assert (A["near"], A["far"], round(A["prev_spread"], 2), round(A["spread"], 2)) == (-37.63, 20.43, 6.76, 58.06)
    assert A["expiry"] == 10.01 and S["widest"][0] == dt.date(2020, 4, 20)
    assert round(S["second"], 2) == 8.49 and S["over5"] == 25 and S["negative_c1"] == [dt.date(2020, 4, 20)]
    assert S["last"].year - S["first"].year == 39
    assert cl_last_trading_day(2020, 5) == dt.date(2020, 4, 21)


def test_exercises():
    assert round(api_gravity(0.87), 1) == 31.1
    assert cl_last_trading_day(2026, 12) == dt.date(2026, 11, 20)
    assert round(quality_adjusted(80, 36, 0.60, 38, 0.40, 0.04, 0.12), 2) == 79.68
    assert round(storage_floor(25.0, 0.40, 1.0), 2) == 24.60 and round(25 - 18 - 0, 0) == 7
    assert round((71.35 + 2.20) * 2e6 / 1e6, 1) == 147.1


def test_problem():
    assert round(18.27 * 1e6 / 1e6, 2) == 18.27 and round(25.03 - 18.27, 2) == 6.76
    assert round(6.76 / 0.40) == 17
    assert round((-37.63 - 18.27) * 1e6 / 1e6, 2) == -55.90
    assert round(58.06 / 0.40) == 145
    assert round((58.06 - 0.40) * 1e6 / 1e6, 2) == 57.66
    assert round(6.76 / 25.03 * 100) == 27
