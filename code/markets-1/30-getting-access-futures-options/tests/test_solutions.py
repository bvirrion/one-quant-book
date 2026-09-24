"""Numbers gate: every numerical answer printed in the Chapter 30 text and solutions."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from futures_access import ES, LESSEE, MICRO, OUTSIDE, breakevens, exchange_round_trip_in_ticks

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/futfees"))
from firm_futfees import Access, breakeven_sides, monthly_cost, per_side


def test_text():
    assert [round(per_side(ES, a), 2) for a in (OUTSIDE, LESSEE, Access("owner", 0.10))] == [1.45, 0.57, 0.45]
    lease, own = breakevens()
    assert (round(lease), round(own)) == (1705, 20_833) and round(lease / 21 / 2) == 41 and round(own / 21) == 992
    e, m = exchange_round_trip_in_ticks(ES, 12.5), exchange_round_trip_in_ticks(MICRO, 1.25)
    assert [round(e[k] * 100) for k in ("non_member", "lessee", "owner")] == [19, 8, 6]
    assert [round(m[k] * 100) for k in ("non_member", "lessee", "owner")] == [35, 11, 6]
    assert round(1.18 / 0.35, 1) == 3.4


def test_exercises():
    assert monthly_cost(ES, OUTSIDE, 10_000) == pytest.approx(14_500) and monthly_cost(ES, LESSEE, 10_000) == pytest.approx(7_200)
    rt = 400 * 21
    gross = rt * 0.3 * 12.5
    assert gross == pytest.approx(31_500) and gross - rt * 2 * 1.45 == pytest.approx(7_140)
    assert gross - rt * 2 * 0.57 - 1_500 == pytest.approx(20_424)
    assert 46_000 + 2 * 1_500 == 49_000 and 50_000 * 0.05 == 2_500
    non_member_with_data = Access("non_member", 0.25, 1_200.0)
    assert breakeven_sides(ES, LESSEE, non_member_with_data) == pytest.approx(300 / 0.88)
    assert round(300 / 0.88) == 341
    assert breakeven_sides(ES, Access("lessee", 0.10, 1_100.0), non_member_with_data) == 0.0


def test_problem():
    sides = 600 * 21
    gross = sides * 0.25 * 12.5
    fees_out, fees_lease = sides * 1.45, sides * 0.57 + 1_500
    assert (sides, gross, fees_out) == (12_600, 39_375.0, pytest.approx(18_270))
    assert gross - fees_out == pytest.approx(21_105) and round(fees_out / gross * 100) == 46
    assert round(2 * 1.45 / 12.5, 2) == 0.23
    assert round(1_500 / 0.88) == 1_705 and round(1_500 / 0.88 / 21) == 81
    assert fees_lease == pytest.approx(8_682) and gross - fees_lease == pytest.approx(30_693)
    assert (gross - fees_lease) - (gross - fees_out) == pytest.approx(9_588)
    assert round(2_000 / (9_588 / 21), 1) == 4.4
    ms = 2_000 * 21
    mg = ms * 0.25 * 1.25
    assert mg == pytest.approx(13_125) and mg - ms * (0.22 + 0.10) == pytest.approx(-315)
    assert mg - ms * (0.07 + 0.05) == pytest.approx(8_085)
    assert sides < 20_000 and round(20_000 / 21) == 952
