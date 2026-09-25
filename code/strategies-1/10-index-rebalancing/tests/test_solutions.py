"""Numbers gate: every numerical answer printed in Book 8, chapter 10 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_index import accuracy, counts, path_for_figure, trades  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_counts_and_accuracy():
    assert counts() == {"events": 17, "adds": 331, "drops": 270}
    a0, a20, a60 = accuracy(0), accuracy(20), accuracy(60)
    assert all(v == 1.0 for v in a0.values())
    f = lambda a: tuple(r(100 * a[k], 0) for k in ("add_precision", "add_recall", "drop_precision", "drop_recall"))  # noqa: E731
    assert f(a20) == (86, 72, 86, 74) and f(a60) == (76, 45, 76, 46)


def test_trades():
    t = trades(0.15, 0.5)
    assert (r(100 * t["push"], 2), r(100 * t["predict"], 2), r(100 * t["announce"], 2), r(100 * t["provide"], 2),
            t["n"], r(100 * t["se_announce"], 1)) == (5.3, 3.75, 2.4, 2.65, 601, 0.4)
    grid = {(s, e): r(100 * trades(s, e)["announce"], 1) for s in (0.05, 0.15, 0.30) for e in (0.2, 0.5, 0.8)}
    assert grid == {(0.05, 0.2): 2.2, (0.05, 0.5): 1.3, (0.05, 0.8): 0.4, (0.15, 0.2): 4.0, (0.15, 0.5): 2.4,
                    (0.15, 0.8): 0.8, (0.3, 0.2): 5.7, (0.3, 0.5): 3.5, (0.3, 0.8): 1.3}
    assert [r(100 * trades(s, 0.5)["push"], 1) for s in (0.05, 0.30)] == [3.1, 7.5]
    assert [r(100 * trades(0.15, e)["predict"], 1) for e in (0.2, 0.8)] == [2.2, 5.3]
    p = path_for_figure(0.15, 0.5)
    assert (r(100 * p[20], 1), r(100 * p[44], 1), r(100 * p[-1], 1)) == (3.1, 5.9, 2.8)


def test_exercises():
    assert (300 - 15, 300 + 15) == (285, 315)
    assert r(100 * 0.7 * 0.02 * (0.15 / 0.006) ** 0.5, 1) == 7.0 and r(100 * 0.5 * 0.07, 1) == 3.5
