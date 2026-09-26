"""Numbers gate: every numerical answer printed in Book 11, chapter 18 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_news as h  # noqa: E402

nr = h.nr


def r(x, d=1):
    return round(float(x), d)


def test_race():
    b = h.base()
    assert [r(100 * s) for s in b["share"]] == [88.1, 11.6, 0.3, 0.0]
    assert round(b["captured_per_release"]) == 223 and r(b["mm_loss_per_release"]) == 57.5
    assert round(b["mm_loss_per_release"] * h.TICK_USD) == 719
    f = h.base(0.5)
    assert list(f["share"]) == [1.0, 0.0, 0.0, 0.0] and round(f["captured_per_release"]) == 197 and r(f["mm_loss_per_release"]) == 52.7


def test_protocol():
    c = h.reentry_curve()
    assert [round(c[t]) for t in (0.0, 0.5, 5, 30)] == [872, 911, 1052, 599]
    p = h.protocol()
    assert p["best_reentry"] == 5 and round(p["stay_total"]) == 814 and round(p["protocol_total"]) == 1052
    assert round(100 * (p["protocol_total"] / p["stay_total"] - 1)) == 29
    assert round(p["protocol_total"] - p["stay_total"]) == 238 and round(238 * 12.5 * 12) == 35700


def test_exercises():
    assert nr.race(4, [10, 10, 10, 10], [(0.05, 30)], 20.0)[0][0] == 60
    assert r(h.headline(), 2) == 1.76 and h.headline(0.2) < 0
    assert r(100 * 2 / 12, 1) == 16.7
    assert r(5 * math.log(3), 1) == 5.5
