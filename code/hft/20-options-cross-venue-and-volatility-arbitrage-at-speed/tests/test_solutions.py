"""Numbers gate: every numerical answer printed in Book 11, chapter 20 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_optarb as h  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_scans():
    s = h.scans()
    assert [r(100 * s[(n, 0.5)]["per_snapshot"], 1) for n in (1, 3, 6)] == [0.7, 6.6, 25.7]
    assert [round(100 * s[(n, 0.5)]["survive"]) for n in (3, 6)] == [8, 6]
    assert [round(100 * s[(n, 0.9)]["survive"]) for n in (3, 6)] == [44, 43]
    assert 1.0 < 100 * s[(6, 0.5)]["mean_edge"] < 2.0 and 1.0 < 100 * s[(1, 0.5)]["mean_edge"] < 2.0


def test_dividend_and_examples():
    d = h.dividend()
    assert d[0.015]["q"] == 0.0 and d[0.02]["q"] > 0
    assert [r(d[f]["per_public"]) for f in (0.05, 0.1, 0.2, 0.5)] == [0.27, 1.05, 3.04, 10.02]
    assert [round(100 * d[f]["captured"]) for f in (0.05, 0.5)] == [42, 82]
    e = h.examples()
    assert r(100 * e["box_rate"]) == 4.02 and r(100 * e["box_edge"][0], 1) == 1.0 and r(100 * e["jelly"], 1) == 4.0
    assert r(e["threshold"]) == 0.13
    assert r(100 * (4.60 - 4.10 - 100.01 + 0.50 + 100 * math.exp(-0.01)), 1) == -0.5
