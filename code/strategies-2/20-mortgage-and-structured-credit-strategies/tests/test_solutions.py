"""Numbers gate: every numerical answer printed in Book 9, chapter 20 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_mbsrv import io_summary, mezz, new_mortgage_rate, stack, tranches, vol_case  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_io():
    s = io_summary()
    assert (r(s["price"], 2), r(s["hedge"], 2)) == (26.05, 0.51)
    assert (r(s["market"]), r(s["view"]), r(s["slow"]), r(s["no_burnout"])) == (0.0, 35.8, 16.4, -25.5)
    assert [r(s[n + "_dn100"]) for n in ("market", "view", "slow", "no_burnout")] == [10.1, 63.6, 31.1, -36.0]
    assert (r(100 * new_mortgage_rate()), r(0.06 * 0.6 * 100)) == (5.8, 3.6)
    assert r(s["price"] * s["view"] / 100, 2) == 9.32                                     # exercise 1


def test_stack():
    t = stack()
    assert [r(x["coupon"]) for x in t] == [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5]
    assert [r(x["oas_view"], 0) for x in t] == [59, 65, 73, 86, 102, 120, 135, 148]
    assert [r(x["oas_nob"], 0) for x in t] == [42, 37, 27, 8, -29, -92, -191, -326]
    assert [r(x["price"]) for x in t] == [95.0, 97.9, 100.7, 103.1, 105.3, 107.3, 109.4, 111.9]
    assert (r(t[-1]["oas_view"] - t[0]["oas_view"], 0), r(t[-1]["oas_nob"] - t[0]["oas_nob"], 0)) == (88, -368)


def test_tranches():
    t = tranches()
    assert [[r(x[k], 2) for k in (0.15, 0.30, 0.45)] for x in t] == [
        [74.45, 59.86, 48.11], [25.32, 24.34, 22.11], [7.52, 11.69, 13.0], [2.1, 5.7, 7.92], [0.15, 1.23, 2.77]]
    assert r(30 * t[2][0.30] / 100, 2) == 3.51                                            # exercise 3
    assert r(t[4][0.45] / t[4][0.15], 0) == 18


def test_mezz():
    m = mezz()
    assert [(r(100 * m[k]["pnl_mean"]), r(100 * m[k]["p_loss"]), r(100 * m[k]["wipeout"])) for k in (0.15, 0.30, 0.45)] \
        == [(3.1, 11.3, 5.4), (-0.4, 14.5, 9.4), (-1.4, 15.0, 10.9)]


def test_exercise_7():
    v = vol_case(0.012)
    assert (r(v["price"], 2), r(v["view"]), r(v["no_burnout"])) == (26.85, 33.5, -26.5)
