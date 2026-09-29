"""Numbers gate: every numerical answer printed in Book 16, chapter 29 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_cases2 as m  # noqa: E402

cb = m.cb


def r(x, d=2):
    return round(float(x), d)


def test_knight():
    k = m.knight()
    assert (r(k["after_loss"], 0), r(k["after"], 0), r(100 * k["old_fraction"], 1)) == (1057, 1457, 26.9)
    assert (r(k["old_book"], 0), r(k["new_book"], 0), r(k["price"])) == (391, 1066, 1.5)
    assert (r(k["bps_before"]), r(k["bps_after_loss"]), r(k["bps_after"])) == (15.29, 10.8, 4.0)
    assert r(100 * 440 / 1496.966, 1) == 29.4 and r(3.75 / 4.0 * 100, 0) == 94


def test_race():
    x = m.race()
    assert r(x["impact"], 3) == 0.531
    assert [r(v) for v in x[0.094]] == [0.0, 0.34, 1.63, 2.92, 4.21, 5.5, 6.79]
    assert [r(v) for v in x[0.2]] == [0.0, 0.0, 0.0, 1.12, 2.41, 3.7, 4.99]
    assert [r(v) for v in x[0.075]][1:3] == [0.66, 1.95] and r(sum(x[0.094]), 1) == 21.4
    assert [r(100 * m.needed_margin(x["impact"], p), 1) for p in (1, 6, 7)] == [3.8, 41.8, 49.3]
    assert r(100 * x["impact"] / 2, 1) == 26.6


def test_ftx():
    f = m.ftx()
    assert r(100 * f["located_a"] / f["payables_a"], 1) == 6.6 and r(100 * f["assets"] / f["payables"], 1) == 22.6
    assert (r(f["customers"][-1], 0), r(f["related"][-1], 0)) == (-7013, 3242)
    assert r(f["customers"][6] - f["customers"][5], 0) == -3306


def test_nickel():
    n = m.nickel()
    assert (r(n["price_0700_8mar"] / 1e6, 0), r(n["peak_8mar"] / 1e6, 0), r(n["break"], 0)) == (319, 533, 78078)
    assert r(cb.NICKEL["peak_8mar"] / cb.NICKEL["close_7mar"], 2) == 2.11


def test_small_runs():
    assert cb.exit_race([0.5, 0.5], [0.0, 0.0], 1.0) == [0.125, 0.375]
    assert r(cb.race_impact(0.375, 0.5, 0.0, 0.5), 6) == 1.0
    assert cb.rescue(100, 50, 50, 1, 1)["old_fraction"] == 0.5


def test_transfer():
    k = m.knight()
    assert r(k["after_loss"] - k["old_book"], 0) == 666 and r(k["new_book"] - 400, 0) == 666


def test_needed_margins():
    x = m.race()
    assert [r(100 * m.needed_margin(x["impact"], p), 1) for p in range(1, 8)] == [3.8, 11.4, 19.0, 26.6, 34.2, 41.8, 49.3]
