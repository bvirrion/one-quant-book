"""Numbers gate: every numerical answer printed in Book 8, chapter 13 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_intraday import smile, summary  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_summaries():
    a, b = summary(0.0), summary(0.05)
    f = lambda s: (r(100 * s["on_share"], 0), r(100 * s["on_ann"], 1), r(100 * s["day_ann"], 1), r(s["slope"], 3),  # noqa: E731
                   r(s["t"], 1), r(s["mom_sr"]), r(100 * s["mom_ann"], 1), r(s["fade_sr"]), r(100 * s["fade_ann"], 1),
                   r(100 * s["hit"], 1), r(s["next_day"], 3))
    assert f(a) == (54, 4.4, 3.7, -0.006, -1.2, -0.77, -4.0, 1.09, 8.8, 48.8, -0.048)
    assert f(b) == (51, 4.3, 4.1, 0.044, 9.2, 1.05, 5.5, 1.08, 8.7, 54.1, -0.053)
    w = smile()
    assert (r(100 * w[0], 1), r(100 * w[6], 1), r(100 * (w[0] + w[-1]), 1)) == (12.1, 4.9, 24.3)


def test_exercises():
    assert r(100 * 0.16 / math.sqrt(20), 1) == 3.6 and r(100 * 0.16 * math.sqrt(0.25) / math.sqrt(20), 1) == 1.8
    assert r(100 * 0.25 * 0.07, 2) == 1.75
    assert r(0.6 * 10, 1) == 6.0 and r(6 * 252 / 100, 1) == 15.1
    assert r(0.05 * 2.0, 2) == 0.1
