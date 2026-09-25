"""Numbers gate: every numerical answer printed in Book 8, chapter 8 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_lending import avoidance, book, ic, levels, squeeze  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_levels_and_ics():
    lv = levels()
    assert (r(100 * lv["si_median"], 1), r(100 * lv["si_p90"], 1), r(100 * lv["si_max"], 0), r(100 * lv["util_p90"], 0),
            r(100 * lv["fee_hot"], 1), r(100 * lv["fee_p99"], 0), r(lv["dtc_median"], 1), r(lv["dtc_p90"], 1)) == \
        (3.1, 7.5, 54, 48, 2.9, 40, 2.1, 6.8)
    assert [r(ic(n), 3) for n in ("si", "dtc", "fee", "crowding")] == [0.061, 0.048, 0.006, 0.058]


def test_books():
    got = {n: book(n) for n in ("si", "fee", "crowding")}
    f = lambda b: (r(b["sr_gross"]), r(b["sr_fee"]), r(b["sr_net"]), r(100 * b["ret_gross"], 1),  # noqa: E731
                   r(100 * b["fee"], 1), r(100 * b["cost"], 2), r(100 * b["short_fee"], 1))
    assert f(got["si"]) == (3.33, 2.24, 1.84, 8.3, 2.7, 0.95, 5.4)
    assert f(got["fee"]) == (1.18, -0.66, -0.82, 2.5, 4.0, 0.33, 7.9)
    assert f(got["crowding"]) == (3.3, 2.08, 1.69, 8.2, 3.0, 0.94, 6.1)
    net = got["si"]["ret_gross"] - got["si"]["fee"] - got["si"]["cost"]
    assert r(100 * net, 1) == 4.6
    a = avoidance()
    assert (r(100 * a["all"], 1), r(100 * a["avoid"], 1), r(100 * a["diff"], 2), r(a["t"], 1)) == (9.1, 10.0, 0.94, 7.2)


def test_squeeze():
    s = squeeze(0.5, 5)
    assert (r(100 * s["median"], 1), r(100 * s["worst"], 1), r(100 * s["actual_worst"], 1), s["n"]) == (-4.0, -8.3, -3.0, 96)
    assert (r(100 * squeeze(0.25, 5)["median"], 1), r(100 * squeeze(0.5, 10)["median"], 1),
            r(100 * squeeze(0.5, 10)["worst"], 1)) == (-2.8, -5.7, -12.3)


def test_exercises():
    assert r(0.1 * 80e6 / 0.8e6, 0) == 10
    assert r(100 * (0.0025 + 0.3975 * 0.5**3), 2) == 5.22 and r(100 * 0.05 * 0.052188 * 0.75, 2) == 0.2
    assert r(100 * 0.5 / 20 * 19, 1) == 47.5
