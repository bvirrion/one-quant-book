"""Tutorial of Book 2, Chapter 5: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from repo_demo import financed_note, sept_2019, special_value, specialness_curve, sponsored


def test_financed_note():
    f = financed_note()
    assert round(f["cash"]) == 98_853_492 and round(f["interest"]) == 321_274
    assert round(f["carry"]) == 18_637 and round(f["breakeven_bp"], 2) == 0.23
    assert round(f["margin_after_fall"]) == 1_500_000


def test_special_value():
    v = special_value()
    assert (round(v["points"], 4), round(v["thirty_seconds"], 2), round(v["yield_bp"], 2)) == (0.0672, 2.15, 0.84)
    assert len(specialness_curve()) == 90


def test_data_files():
    s = {r["date"]: r for r in sept_2019()}
    assert s["2019-09-17"]["sofr"] == 5.25 and s["2019-09-17"]["effr"] == 2.30
    assert s["2019-09-17"]["range_upper"] == 2.25 and s["2019-09-19"]["range_upper"] == 2.00
    sp = sponsored()
    peak = max(sp, key=lambda r: r[1] + r[2])
    assert peak[0] == "2025-12-31" and round((peak[1] + peak[2]) / 1000, 2) == 2.96
    assert sp[-1][0] == "2026-08-21" and round((sp[-1][1] + sp[-1][2]) / 1000, 2) == 2.33
