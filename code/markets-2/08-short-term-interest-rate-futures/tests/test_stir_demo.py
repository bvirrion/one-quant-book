"""Tutorial of Book 2, Chapter 8: the printed end state is reproduced."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from stir_demo import convexity_table, december, imm_date, path, reference_quarters, turn_sensitivity


def test_path_and_december():
    p = dict(path())
    assert (round(p["2026-11"], 4), round(p["2026-12"], 4), round(p["2027-01"], 3)) == (3.8975, 3.9856, 4.175)
    d0, d10 = december(0), december(10)
    assert (round(d0["probability"] * 100, 1), round(d10["probability"] * 100, 1)) == (35.2, 33.4)
    assert round(d10["rate_after"], 4) == 3.9810


def test_imm_dates_and_quarters():
    assert [imm_date(2027, m) for m in (3, 6, 9, 12)] == [dt.date(2027, 3, 17), dt.date(2027, 6, 16),
                                                           dt.date(2027, 9, 15), dt.date(2027, 12, 15)]
    assert imm_date(2026, 9) == dt.date(2026, 9, 16) and imm_date(2026, 12) == dt.date(2026, 12, 16)
    assert reference_quarters(2027)[1] == (dt.date(2027, 3, 17), dt.date(2027, 6, 16))


def test_turn_curve_and_convexity():
    t = dict(turn_sensitivity())
    assert all(a > b for a, b in zip(list(t.values()), list(t.values())[1:], strict=False))
    c = {row[0]: row for row in convexity_table()}
    assert (round(c[5.0][2], 1), round(c[10.0][2], 2)) == (13.1, 51.25)
