"""Numbers gate: every numerical answer printed in Book 8, chapter 17 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_news import capture, daily, stream  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_stream_and_capture():
    s = stream()
    assert (s["items"], r(s["per_day"], 1), r(100 * s["halted"], 2), r(s["att_median"]), r(s["att_min"])) == \
        (82351, 40.8, 1.18, 0.42, 0.14)
    got = [(r(100 * capture(L)[0], 1), r(capture(L)[1], 0)) for L in (0.001, 0.01, 0.1, 1.0, 3600.0, None)]
    assert got == [(96.7, 144), (93.7, 139), (70.1, 102), (29.2, 36), (28.7, 36), (28.7, 36)]


def test_daily_trader():
    f = lambda d: (r(d["sr"]), r(100 * d["ret"], 1), r(d["drift_bp"], 1), r(100 * d["right"], 1))  # noqa: E731
    assert f(daily("all")) == (3.24, 7.4, 25.4, 68.9)
    assert f(daily("quiet")) == (1.8, 6.3, 20.8, 68.6)
    assert f(daily("busy")) == (2.74, 8.3, 29.5, 68.5)


def test_exercises():
    assert r(math.exp(-0.1 / 0.2), 3) == 0.607 and r(math.exp(-1 / 0.2), 4) == 0.0067
    assert r(0.5 + 0.5 * 0.42, 2) == 0.71 and r(1 / (1 + 0.03 * 39), 2) == 0.46
    assert r(0.5 + math.asin(1 / math.sqrt(1 + 1.5**2)) / math.pi, 3) == 0.687


def test_perfect_reading():
    import s1_news
    old = s1_news.READ
    try:
        s1_news.READ = 0.0
        s1_news.daily.cache_clear()
        d = s1_news.daily("all")
        assert (r(d["sr"], 1), r(100 * d["ret"], 1), r(d["drift_bp"], 1), d["right"]) == (7.6, 17.4, 45.7, 1.0)
    finally:
        s1_news.READ = old
        s1_news.daily.cache_clear()


def test_solution_arithmetic():
    assert r(0.5 + 0.5 * (1 / (1 + 0.03 * 39)), 2) == 0.73 and r(1 / math.sqrt(1 + 1.5**2), 3) == 0.555
    assert r(2 * 0.689 - 1, 2) == 0.38 and r(25.4 / 45.7, 2) == 0.56 and r(1 - 25.4 / 45.7, 2) == 0.44 and r(0.2 * math.log(2), 2) == 0.14
