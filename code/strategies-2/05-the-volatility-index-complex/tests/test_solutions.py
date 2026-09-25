"""Numbers gate: every numerical answer printed in Book 9, chapter 5 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_vixetp import curve_stats, short_book, spike  # noqa: E402
from s2_vixetp import real as real_data  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def pct(x, d=1):
    return round(100 * float(x), d)


def test_curve():
    c0, c = curve_stats(0.0), curve_stats()
    assert (r(c["vix_mean"], 1), r(c["vix_median"], 1), r(c["premium_f1"]), pct(c["contango"], 0), pct(c["long_log"], 0),
            pct(c["long_vol"], 0)) == (19.6, 17.7, 0.44, 81, -74, 88)
    assert (r(c0["premium_f1"]), pct(c0["contango"], 0), pct(c0["long_log"], 0), pct(c0["long_mean"])) == (0.01, 65, -26,
                                                                                                          -3.7)


def test_short_books():
    got = {}
    for k in (0.1, 0.25, 0.5, 1.0):
        b = short_book(k)
        got[k] = (b["alive"], pct(b["ann"]), pct(b["max_dd"], 0), r(b["final"]))
    assert got == {0.1: (True, 4.8, -27, 2.57), 0.25: (True, 9.6, -67, 6.26), 0.5: (False, -100.0, -100, 0.0),
                   1.0: (False, -100.0, -100, 0.0)}


def test_spike():
    s = spike()
    assert (s["day"], r(s["vix_before"], 1), r(s["vix_after"], 1), pct(s["cm_return"], 0)) == (1500, 17.3, 63.6, 189)
    i, d = s["inverse"], s["double"]
    assert (r(i["value_before"], 1), i["value_after"], i["ended"], r(i["flow"])) == (16.5, 0.0, True, 3.77)
    assert (d["ended"], r(d["flow"])) == (False, 3.77)
    assert r(2 * s["cm_return"]) == 3.77


def test_real():
    s, y = real_data()
    assert (s["first"], s["last"], s["days"], pct(float(s["contango_share"])), r(float(s["f1_premium_mean"])),
            r(float(s["f2_f1_mean"])), pct(float(s["long_ann_log"])), pct(float(s["long_total"]), 2),
            pct(float(s["inverse_ann_log"]))) == ("2013-01-02", "2026-09-24", "3456", 85.0, 0.63, 0.89, -66.4, -99.99,
                                                   -4.7)
    assert (pct(float(s["long_worst"])), s["long_worst_at"], pct(float(s["long_best"])), s["long_best_at"],
            float(s["vix_2018_02_02"]), float(s["vix_2018_02_05"]), float(s["f1_2018_02_02"]),
            float(s["f1_2018_02_05"]), pct(float(s["inverse_2018_01_to_02_05"]))) == (
        -25.8, "2018-02-06", 95.9, "2018-02-05", 17.31, 37.32, 15.625, 33.225, -96.7)
    yr = {int(x["year"]): (pct(float(x["long"]), 0), pct(float(x["inverse"]), 0), pct(float(x["contango"]), 0),
                           pct(float(x["vix_change"]), 0)) for x in y}
    assert yr[2014] == (-25, -11, 89, 35) and yr[2015] == (-37, -16, 79, 2) and yr[2017] == (-73, 192, 94, -14)
    assert yr[2018] == (66, -97, 64, 160) and yr[2025] == (-45, 1, 81, -17)
    assert yr[2023] == (-75, 189, 99, -46)
    assert sum(1 for v in yr.values() if v[0] < 0) == 12 and len(yr) == 14


def test_small_answers():
    s, _ = real_data()
    assert pct(1 - float(s["contango_share"])) == 15.0 and r(2 * float(s["long_best"])) == 1.92
    assert (100 * -1 * -2 * 0.3, 100 * 2 * 1 * 0.3, r(8 / 28, 3)) == (60.0, 60.0, 0.286)


def test_wipeout_size():
    assert r(1 / spike()["cm_return"]) == 0.53
