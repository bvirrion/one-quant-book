"""Numbers gate: every numerical answer printed in the Chapter 16 text and solutions."""
import csv
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from short_cost import breakeven_days, days_to_cover, fee_from_utilisation, squeeze_return

CSV = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/16-stock-loan-and-short-selling/carry.csv"


def rows():
    with open(CSV) as f:
        return [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]


def test_text():
    assert breakeven_days(0.25, 0.40) == pytest.approx(225) and round(breakeven_days(0.25, 0.80)) in (112, 113)
    r = rows()
    best = max(r, key=lambda x: x["net_k"])
    assert (best["day"], best["price"], round(best["net_k"])) == (190, 31.20, 789)
    worst = min(r, key=lambda x: x["net_k"])
    assert (worst["day"], worst["price"], round(worst["net_k"] / 1e3, 2)) == (94, 53.52, -1.36)
    last = r[-1]
    assert (last["price"], round(last["cost_k"]), round(last["net_k"])) == (38.36, 399, -235)
    assert round((last["cost_k"] - r[189]["cost_k"]) / last["cost_k"], 2) == 0.77
    assert round(0.80 / 360 * 100, 2) == 0.22                                   # 'two tenths of a percent' a day
    assert 1 / (1 - 0.2 / 0.5) == pytest.approx(5 / 3) and 1 / (1 - 0.4 / 0.5) == pytest.approx(5.0)
    assert squeeze_return(0.20, 0.4, 0.1, 0.6) == pytest.approx(0.60)


def test_exercises():
    assert 0.043 - (-0.117) == pytest.approx(0.16) and round(3e6 * 0.16 / 360) == 1333
    assert 10.2 / 12 == pytest.approx(0.85) and round(fee_from_utilisation(0.85) * 100, 2) == 13.05
    assert 18 / 60 == pytest.approx(0.30) and days_to_cover(18e6, 2.4e6) == pytest.approx(7.5)
    assert round(225 / 720, 2) == 0.31
    assert 100 + 123 == 223
    mon = dt.date(2026, 9, 14)
    assert mon.weekday() == 0 and (mon + dt.timedelta(days=2)).weekday() == 2 and (mon + dt.timedelta(days=4)).weekday() == 4
    r = rows()
    assert round(r[-1]["price_pnl_k"]) == 164 and round(r[-1]["cost_k"] - r[189]["cost_k"]) == 308


def test_problem():
    assert 20 / 50 == 0.4 and days_to_cover(20e6, 4e6) == 5.0 and 2 / 20 == 0.1
    assert round(40e6 * 0.12 / 360) == 13_333 and breakeven_days(0.30, 0.12) == pytest.approx(900)
    assert round(40e6 * 0.60 / 360) == 66_667 and breakeven_days(0.30, 0.60) == pytest.approx(180)
    x = squeeze_return(0.25, 0.2, 0.1, 0.6)
    assert x == pytest.approx(0.35) and (x - 0.1) / 0.5 == pytest.approx(0.5)
    assert squeeze_return(0.25, 0.4, 0.1, 0.6) == pytest.approx(0.65)
    assert squeeze_return(0.199, 0.4, 0.1, 0.6) < 0.60 and squeeze_return(0.20, 0.4, 0.1, 0.6) == pytest.approx(0.60)
    assert 20 * 1.65 == pytest.approx(33.0) and 2e6 * 13 == 26e6 and 2e6 * 33 * 0.7 == pytest.approx(46.2e6)
    assert 500_000 * 13 == 6.5e6 and 40e6 * 0.20 * 90 / 360 == pytest.approx(2e6)
    assert 40e6 * 0.35 == pytest.approx(14e6)
