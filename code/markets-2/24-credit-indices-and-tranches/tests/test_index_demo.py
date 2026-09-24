"""Tests of the Chapter 24 demo: the stylised index, the skew curve and the chart data."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from index_demo import NAMES, SPREADS, loss_histograms, skew_pnl_curve, tranche_table


def test_constituents():
    assert len(SPREADS) == NAMES == 125 and SPREADS == sorted(SPREADS)


def test_skew_pnl_rises_with_exit_skew_and_is_zero_at_entry():
    curve = dict(skew_pnl_curve())
    assert abs(curve[-8]) < 1e-9 and all(curve[x] < curve[x + 1] for x in range(-24, 8))


def test_tranche_table_directions():
    rows = tranche_table()
    assert all(a[1] > b[1] and a[4] < b[4] for a, b in zip(rows, rows[1:], strict=False))
    senior = [r[3] for r in rows]
    peak = senior.index(max(senior))
    assert rows[peak][0] == 0.65 and senior[-1] < senior[peak]            # 7-15% peaks at high correlation


def test_loss_distributions_are_probabilities():
    for _, h in loss_histograms():
        assert abs(sum(p for _, _, p in h) - 1.0) < 1e-9
