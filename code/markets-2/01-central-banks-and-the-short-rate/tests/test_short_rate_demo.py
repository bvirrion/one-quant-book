"""Tutorial of Book 2, Chapter 1: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from short_rate_demo import CAL, END, START, fed_balance_sheet, month_summary, overnight_rate, running_compounded

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/rfr"))
from firm_rfr import weights


def test_tutorial_end_state():
    s = month_summary()
    assert round(s["simple"] * 100, 4) == 3.7393
    assert round(s["compounded"] * 100, 4) == 3.7448
    assert round(s["lookback5"] * 100, 4) == 3.6836
    assert len(CAL.business_days(START, END)) == 21


def test_weights_printed_in_step_1():
    import datetime as dt
    days = CAL.business_days(dt.date(2026, 9, 3), dt.date(2026, 9, 10))
    assert weights(CAL, days, dt.date(2026, 9, 10)) == [1, 4, 1, 1]


def test_running_rate_ends_at_the_period_rate():
    assert running_compounded()[-1][2] == month_summary()["compounded"]


def test_corridor_curve_is_bounded_and_decreasing():
    xs = [i / 10 for i in range(61)]
    ys = [overnight_rate(x, 0.025, 0.029) for x in xs]
    assert all(0.025 <= y <= 0.029 for y in ys)
    assert all(a > b for a, b in zip(ys, ys[1:], strict=False))
    assert ys[-1] - 0.025 < 1e-4 and 0.029 - ys[0] < 1e-4


def test_balance_sheet_adds_up():
    bs = fed_balance_sheet()
    assert abs(sum(bs["assets"].values()) - sum(bs["liabilities"].values())) < 1e-9
