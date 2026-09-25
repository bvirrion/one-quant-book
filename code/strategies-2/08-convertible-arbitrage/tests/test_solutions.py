"""Numbers gate: every numerical answer printed in Book 9, chapter 8 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_convarb import profile, summary  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def pct(x, d=1):
    return round(100 * float(x), d)


def test_profile():
    p = profile()
    assert r(p["floor"]) == 87.34
    assert {s: (r(v["value"], 1), r(v["conversion"], 1), r(v["delta"])) for s, v in p["rows"].items()} == {
        15.0: (81.2, 37.5, 1.27), 25.0: (94.0, 62.5, 1.37), 40.0: (117.7, 100.0, 1.8), 60.0: (158.4, 150.0, 2.22),
        80.0: (204.8, 200.0, 2.4)}
    assert r(1.268 * 15 / 81.2) == 0.23


def test_books():
    s, c = summary(), summary(True)
    assert (r(s["price0"]), pct(s["carry"]), pct(s["episode"]["total"]), pct(s["recovery"]), pct(s["total"])) == (
        114.19, 9.8, -11.6, 22.0, 51.9)
    assert {k: pct(v) for k, v in s["episode"].items()} == {"bond": -17.0, "hedge": 20.7, "cheapness": -12.6,
                                                          "credit": -6.9, "credit_hedge": 0.0, "coupon": 5.3,
                                                          "borrow": -1.1, "total": -11.6}
    assert (pct(c["carry"]), pct(c["episode"]["total"]), pct(c["episode"]["credit_hedge"]), pct(c["recovery"]),
            pct(c["total"]), pct(c["buckets"]["credit_hedge"])) == (6.0, -5.8, 5.8, 10.6, 30.1, -21.8)
    assert {k: pct(v) for k, v in s["buckets"].items()} == {"bond": -18.2, "hedge": 44.1, "cheapness": 6.3, "credit": 2.3,
                                                          "credit_hedge": 0.0, "coupon": 21.0, "borrow": -3.7}
    assert pct(s["episode"]["bond"] + s["episode"]["hedge"]) == 3.7


def test_crossing_and_exercises():
    p = profile()
    assert float(p["grid"][p["curve"] < p["floor"]].max()) == 19.0
    assert (100 / 2.5, 2.5 * 60, round(3 * 2.7, 1)) == (40.0, 150.0, 8.1)
