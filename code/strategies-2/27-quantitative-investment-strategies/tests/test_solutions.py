"""Numbers gate: every numerical answer printed in Book 9, chapter 27 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_qis import complexity, launched, path, verdicts  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_launched():
    a, b = launched(3), launched(1)
    assert (r(a["backtest"]), r(a["true"]), r(a["live"]), r(a["net"]), r(100 * a["decay"], 1)) == (0.51, 0.22, 0.23,
                                                                                                    0.16, 72.2)
    assert (r(b["backtest"]), r(b["true"]), r(b["live"]), r(b["net"]), r(100 * b["decay"], 1)) == (0.62, 0.26, 0.27,
                                                                                                    0.2, 69.4)
    assert (r(100 * a["negative"], 1), r(a["all_true"])) == (36.6, 0.1)


def test_verdicts():
    v = verdicts()
    assert (r(100 * v["pass"], 1), r(v["bt_pass"]), r(v["live_pass"]), r(v["bt_fail"]), r(v["live_fail"])) == (
        5.9, 1.13, 0.32, 0.59, 0.27)


def test_complexity():
    c = complexity()
    assert (r(c[2]["backtest"]), r(c[100]["backtest"]), r(c[2]["net"]), r(c[100]["net"])) == (0.26, 0.76, 0.07, 0.24)
    assert (r(c[2]["backtest"] - c[2]["net"]), r(c[100]["backtest"] - c[100]["net"])) == (0.18, 0.52)
    assert [r(100 * c[n]["decay"], 0) for n in (2, 5, 10, 20, 50, 100)] == [76, 71, 70, 69, 70, 68]


def test_path():
    p = path()
    assert (r(p["sr_backtest"]), r(p["sr_live"]), r(100 * p["cum"][p["split"] - 1], 0),
            r(100 * (p["cum"][-1] - p["cum"][p["split"] - 1]), 1)) == (0.71, -0.07, 71, -7.1)


def test_exercises():
    assert (r(0.007 / 0.10), r(1 / math.sqrt(10)), r(100 * (1 - 0.16 / 0.51), 1)) == (0.07, 0.32, 68.6)
    assert r(math.sqrt(2 * math.log(20)) / math.sqrt(10)) == 0.77                             # interview question 6
