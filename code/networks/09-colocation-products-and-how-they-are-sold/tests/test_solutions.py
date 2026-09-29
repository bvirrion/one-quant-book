"""Numbers gate: every number printed in Book 14, chapter 9 (text and solutions)."""
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_colo as c  # noqa: E402

cb = c.cb


def test_bills():
    b = c.bills()
    assert round(b["one cabinet"]["annual"] / 1000) == 90 and b["two 10Gb ULL"]["annual"] == 360_000
    assert abs(b["four cabinets"]["annual"] / b["two 10Gb ULL"]["annual"] - 1) < 0.03
    f = c.firm_bill()
    assert f["monthly"] == 44_460 and f["one_time"] == 21_000 and round(f["total_monthly"]) == 45_043
    assert round(f["annual"]) == 540_520 and round(21_000 / 36) == 583
    assert round(cb.break_even(f["total_monthly"], 1_000_000), 3) == 0.045
    assert round(cb.break_even(f["total_monthly"], 500_000), 2) == 0.09
    assert round(100 * 21_000 / (f["total_monthly"] * 36), 1) == 1.3


def test_coil_and_fees():
    assert round(cb.equalisation_ns(5, 150)) == 707 and round(cb.equalisation_ns(30, 120)) == 439
    assert round(cb.equalisation_ns(10, 150)) == 683
    assert (7230 / 10, 7230 / 15) == (723, 482) and 2 * 12 * 1500 == 36_000 and 2 * 12 * 13_500 == 324_000
    assert 15_000 / 1_500 == 10
    fp = c.FOOTPRINTS["four cabinets"][1]
    a, b = cb.bill(cb.SCHEDULES["nasdaq-ny11-4"], fp, 36), cb.bill(cb.SCHEDULES["nasdaq-ny11-4"], fp, 60)
    assert (round(a["annual"]), round(b["annual"]), round(a["annual"] - b["annual"])) == (368_053, 359_648, 8_405)
    assert a["one_time"] == 63_040
    assert c.coil()[0] == (5, pytest.approx(707.12, abs=0.01))
