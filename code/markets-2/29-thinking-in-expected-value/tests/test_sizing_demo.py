"""Tests of the Chapter 29 demo: chart data shapes and orderings."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from sizing_demo import coin_table, growth_curve


def test_growth_curve_peaks_at_kelly():
    rows = growth_curve()
    assert max(rows, key=lambda r: r[1])[0] == 0.2


def test_coin_table_medians():
    rows = coin_table(paths=1000)
    med = [r["median"] for r in rows]
    assert med[2] == max(med) and med[3] < 25
