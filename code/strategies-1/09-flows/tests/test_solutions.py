"""Numbers gate: every numerical answer printed in Book 8, chapter 9 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_flows import books, event_path, response  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_response():
    a, z = response(), response(0.0)
    assert (r(a["now"]), r(a["later"]), r(100 * a["reversed"], 0), r(100 * a["fit_sd"], 1)) == (1.05, -0.69, 66, 0.5)
    assert (r(z["now"]), r(z["later"])) == (0.31, 0.32)
    assert r(100 * (1 - 0.5 ** (252 / 126)), 0) == 75


def test_paths():
    t, b = event_path()
    s = t - b
    assert [r(100 * s[i]) for i in (62, 125, 314, 503, 755)] == [1.74, 1.65, -0.71, -2.7, -2.15]
    assert (r(100 * s.max()), int(s.argmax()), int((s < 0).argmax())) == (1.91, 66, 261)
    t0, b0 = event_path(0.0)
    assert [r(100 * (t0[i] - b0[i])) for i in (62, 755)] == [0.15, -1.41]
    tt, tb = event_path(1.5, 756, 2.0)
    assert [r(100 * (tt[i] - tb[i]), 1) for i in (62, 755)] == [4.9, 69.0]


def test_books():
    b, z = books(), books(0.0)
    assert (r(b["expected"]["sr"]), r(b["expected"]["sr_gross"]), r(100 * b["expected"]["ret"], 1),
            r(b["expected"]["turnover"], 1)) == (0.44, 0.7, 1.4, 4.0)
    assert (r(b["reversal"]["sr"]), r(b["reversal"]["sr_gross"]), r(z["expected"]["sr"]), r(z["reversal"]["sr"])) == \
        (-0.35, -0.03, 0.12, -1.06)
    assert (r(z["expected"]["sr_gross"]), r(z["reversal"]["sr_gross"])) == (0.38, -0.73)


def test_exercises():
    assert r(0.2 * 0.05 * 100, 2) == 1.0 and r(0.05 * 0.2 * 1.5 * 100, 1) == 1.5
    assert r(100 * 0.5 ** (126 / 126), 0) == 50
