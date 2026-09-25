"""Numbers gate: every numerical answer printed in Book 9, chapter 9 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_capstruct import cumulative, curve, stats, through_shifts  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_curve():
    c = curve()
    assert (r(c["at50"][40.0][0], 1), r(c["at50"][80.0][0], 1), r(c["lbo"], 1)) == (55.8, 115.4, 98.8)
    assert (r(c["at50"][40.0][1] * 1e7, -2), r(c["at50"][40.0][1] * 1e7 * 50 / 1e6, 2)) == (6700.0, 0.34)
    assert (r(c[40.0][0], 1), r(c[80.0][0], 1)) == (189.8, 226.2)


def test_book():
    got = {k: stats(k) for k in (0.05, 0.2, 0.0)}
    assert {k: (v["trades"], r(v["mean_bp"], 1), round(100 * v["lose"]), r(v["worst_bp"], 0), r(v["days"], 0),
                round(100 * v["timeouts"]), r(v["sr"]), r(v["open"], 0), v["shifts"]) for k, v in got.items()} == {
        0.05: (440, 26.1, 48, -347.0, 140.0, 56, 1.4, 27.0, 34), 0.2: (433, 9.3, 52, -378.0, 141.0, 57, 0.39, 27.0, 123),
        0.0: (413, 25.3, 44, -179.0, 140.0, 55, 1.66, 25.0, 0)}
    assert (r(got[0.05]["cds_bp"], 1), r(got[0.05]["equity_bp"], 1)) == (20.4, 5.6)


def test_shifts():
    t, t4 = through_shifts(), through_shifts(0.2)
    assert {k: (v["n"], r(v["mean_bp"], 0), r(v["worst_bp"], 0)) for k, v in t.items()} == {
        "sold protection": (5, -98.0, -316.0), "bought protection": (7, 220.0, 86.0)}
    assert {k: (v["n"], r(v["mean_bp"], 0)) for k, v in t4.items()} == {"sold protection": (23, -174.0),
                                                                        "bought protection": (31, 104.0)}
    c = cumulative()
    assert (r(100 * c[0.05][-1], 1), r(100 * c[0.2][-1], 1)) == (4.2, 1.5)


def test_exercises():
    import math
    assert r(0.6 * -math.log(0.954) / 5 * 1e4, 1) == 56.5
    assert r(4.5 * (99 - 56) / 1e4 * 1e4, 1) == 193.5
