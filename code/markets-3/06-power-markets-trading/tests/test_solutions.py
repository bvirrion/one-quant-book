"""Numbers gate: every numerical answer printed in Book 3, Chapter 6 (text and solutions)."""
import datetime as dt
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/balancing"))
import m3_trading as m
from firm_balancing import capture_price, settle

C24, C25 = m.capture(2024), m.capture(2025)
DAY = [p for t, p, _, _ in m.load() if t.date() == dt.date(2025, 6, 18)]
Y24, Y25, Y25B = m.battery_year(2024)["eur_per_mw"], m.battery_year(2025)["eur_per_mw"], m.battery_year(2025, 2)["eur_per_mw"]


def test_text():
    assert m.wind_day() == {"revenue": 16280.0, "imbalance": -3580.0, "total": 12700.0}
    assert (round(C24["solar"], 2), round(C24["base"], 2), round(C24["solar_rate"] * 100)) == (46.23, 78.51, 59)
    assert (round(C25["solar"], 2), round(C25["base"], 2), round(C25["solar_rate"] * 100)) == (46.07, 89.32, 52)
    assert round(C24["wind_rate"] * 100) == 82 and round(C25["wind_rate"] * 100) == 87
    assert round(60 - C24["solar"]) == 14
    assert (round(Y24), round(Y25), round(Y25B)) == (65968, 74546, 88688)
    v, acts = m.battery_plan(DAY)
    assert round(v) == 30149 and [h for h, a in enumerate(acts) if a] == [14, 15, 20, 21]


def test_exercises():
    assert math.isclose(capture_price([80, 20, 10, 90], [10, 40, 40, 10]), 29.0)
    assert settle(-20, 300) == -6000 and settle(20, 300) == 6000
    assert 50 * 20 * 10 == 10000
    e = math.sqrt(0.88)
    assert round(200 / e, 1) == 213.2 and round(200 * e, 1) == 187.6
    assert round(20 * 200 / e) == 4264 and round(120 * 200 * e) == 22514 and round(-20 * 200 / e + 120 * 200 * e) == 18250
    assert round((60 - C25["solar"]) * 100_000 / 1e6, 2) == 1.39


def test_problem():
    assert [round(DAY[h], 2) for h in (14, 15, 20, 21)] == [-2.30, -2.17, 140.99, 175.32]
    assert round(m.battery_plan(DAY, 2)[0] - m.battery_plan(DAY)[0]) == 760
    assert round(Y25B - Y25) == 14142
    m.RTE = 1.0
    try:
        loss_free = m.battery_plan(DAY)[0]
    finally:
        m.RTE = 0.88
    assert round(loss_free) == 32078 and round(loss_free - 30149.01) == 1929
