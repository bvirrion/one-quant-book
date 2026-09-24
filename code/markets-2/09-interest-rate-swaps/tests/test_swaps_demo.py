"""Tutorial of Book 2, Chapter 9: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from swaps_demo import curve_table, forward_5y5y, ten_year


def test_ten_year():
    t = ten_year()
    assert round(t["par"] * 100, 2) == 4.05 and round(t["annuity"], 3) == 8.228
    assert round(t["dv01_analytic"]) == 82_278 and round(t["dv01"]) == 82_262
    assert all(abs(x) < 1e-3 for x in t["buckets"][:-1])


def test_forward_and_curve():
    f = forward_5y5y()
    assert round(f["par"] * 100, 3) == 4.295
    assert round(f["buckets"][3]) == -45_394 and round(f["buckets"][5]) == 82_651
    rows = curve_table()
    fwd = [r[2] for r in rows]
    assert len(set(round(x, 3) for x in fwd)) < len(fwd)                   # piecewise-flat forwards
