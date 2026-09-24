"""Chapter 22 of Book 2: the RFQ model behaves as the text says."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rfq_demo import cost_table, histograms


def test_best_n_falls_with_leakage():
    rows = cost_table()
    best = [min(rows, key=lambda r: r[k])[0] for k in (2, 3, 4)]
    assert best == [6, 3, 2]


def test_histograms_integrate_to_one():
    for _, h in histograms():
        width = h[1][0] - h[0][0]
        assert abs(sum(d for _, d in h) * width - 1) < 0.02
