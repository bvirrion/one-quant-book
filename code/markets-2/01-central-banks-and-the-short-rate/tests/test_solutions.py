"""Numbers gate: every numerical answer printed in Book 2, Chapter 1 (text and solutions)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from short_rate_demo import (
    FED_MBS,
    FED_RESERVES,
    FED_RRP,
    FED_TGA,
    FED_TOTAL_ASSETS,
    FED_TREASURIES,
    fed_balance_sheet,
    fixings,
    month_summary,
    problem_numbers,
)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/rfr"))
from firm_rfr import Calendar, Convention, compound_in_arrears

S = month_summary()


def bp(x):
    return x * 1e4


def test_text():
    # Figure 1 caption, USD billion
    assert (round(FED_TOTAL_ASSETS), round(FED_RESERVES), round(FED_TGA), round(FED_RRP)) == (6747, 3014, 877, 324)
    assert round(fed_balance_sheet()["liabilities"]["currency and other"]) == 2532
    assert abs(FED_TREASURIES / FED_TOTAL_ASSETS - 2 / 3) < 0.01 and FED_MBS > 0
    # Example: the ECB corridor
    assert round(bp(0.0290 - 0.0250)) == 40 and round(bp(0.0265 - 0.0250)) == 15
    assert round(bp(0.0250 - 0.02440)) == 6
    # Example: September 2026
    assert round(bp(S["compounded"] - S["simple"]), 2) == 0.54
    assert round(bp(0.0374**2 * 29 / 720), 2) == 0.56
    assert round(bp(S["compounded"] - S["lookback5"]), 2) == 6.12
    assert round((S["compounded"] - S["lookback5"]) * 100e6 * 30 / 360) == 5098


def test_exercises():
    cal = Calendar()
    thu, tue = dt.date(2026, 10, 1), dt.date(2026, 10, 6)
    fx = {dt.date(2026, 10, 1): 0.0390, dt.date(2026, 10, 2): 0.0388, dt.date(2026, 10, 5): 0.0392}
    assert round(compound_in_arrears(fx, cal, thu, tue) * 100, 4) == 3.8926
    assert round((0.0390 + 3 * 0.0388 + 0.0392) / 5 * 100, 4) == 3.8920
    assert round(bp(0.04**2 * 90 / 720), 2) == 2.00
    assert round(bp(((1 + 0.04 / 360) ** 91 - 1) * 360 / 91 - 0.04), 2) == 2.01
    allin = 0.0380 + 0.0026161 + 0.0150
    assert round(allin * 100, 5) == 5.56161 and round(50e6 * allin * 91 / 360) == 702_926
    assert round(S["lockout2"] * 100, 4) == 3.7421 and round(bp(S["compounded"] - S["lockout2"]), 2) == 0.27
    assert S["shift5"] == S["lookback5"] and round(bp(S["compounded"] - S["shift5"]), 2) == 6.12


def test_shift_and_lookback_differ_when_the_hike_is_inside_the_long_weekend():
    from short_rate_demo import CAL, END, START
    fx = fixings()
    for d in fx:
        if d >= dt.date(2026, 9, 4):
            fx[d] = 0.0387
    a = compound_in_arrears(fx, CAL, START, END, Convention(lookback=5))
    b = compound_in_arrears(fx, CAL, START, END, Convention(lookback=5, shift=True))
    assert abs(a - b) > 1e-6


def test_problem():
    p = problem_numbers()
    assert round(p["a_deposit"]) == 3_958_333 and round(p["b_lending"]) == 4_625_000
    assert round(p["gap"]) == 666_667 and round(p["interbank"]) == 4_291_667
    assert round(p["a_gain"]) == 333_333 and round(p["b_saving"]) == 333_333
    extra = 2e9 * 0.0005 * 30 / 360
    assert round(extra) == 83_333 and round(p["a_gain"] + extra) == 416_667 and round(p["b_saving"] - extra) == 250_000
    assert round(1e9 * 0.0006 * 30 / 360) == 50_000
    assert round(2e9 * 0.0040 * 30 / 360) == 666_667
