"""Numbers gate: every numerical answer printed in Book 9, chapter 12 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_swapspread import quarter_ends, real, regimes, spread_stats  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_regimes():
    got = {k: (r(v["bp"]), r(v["sr"], 2), r(v["carry"]), r(v["marks"]), r(v["float_repo"]), r(v["charge"]))
           for k, v in regimes().items()}
    assert got == {("before", False): (-24.3, -0.15, -11.5, -17.8, 5.0, 0.0),
                   ("before", True): (-74.3, -0.44, -11.5, -17.8, 5.0, -50.0),
                   ("after", False): (32.4, 0.13, 38.8, -11.4, 5.0, 0.0),
                   ("after", True): (-17.6, -0.07, 38.8, -11.4, 5.0, -50.0)}
    s = spread_stats()
    assert (r(s["before"]), r(s["after"]), r(s["min"]), s["neg_share_after"]) == (11.5, -38.8, -70.6, 1.0)


def test_quarter_ends():
    q = quarter_ends()
    assert {k: (v["n"], r(v["mean_bp"]), r(v["min_bp"])) for k, v in q.items()} == {
        "year_end": (5, 103.3, 90.6), "other": (18, 43.9, -4.3)}


def test_real():
    x = real()
    got = {m: (r(float(v["mean_pre"])), r(float(v["mean_post"])), r(100 * float(v["neg_share_post"])), r(float(v["min"]), 0),
               v["min_at"], r(float(v["last_value"]), 0)) for m, v in x.items()}
    assert got == {"2y": (47.4, 25.7, 0.0, 2.0, "2015-11-20", 24.0), "5y": (56.9, 21.7, 8.5, -14.0, "2015-11-20", 3.0),
                   "10y": (58.6, 8.3, 17.6, -23.0, "2016-02-24", -15.0),
                   "30y": (48.3, -21.4, 93.9, -62.0, "2016-09-13", -55.0)}
    assert (x["30y"]["first"], x["30y"]["last"]) == ("2000-07-03", "2016-10-28")


def test_exercises():
    assert (round(0.05 * 0.10 * 1e4), round(8.5 * 12), round(40 + 5 - 50)) == (50, 102, -5)


def test_whole_sample():
    from s2_swapspread import whole_sample
    w = whole_sample()
    assert (r(w["total"]), r(w["carry"]), r(w["marks"])) == (-36.8, 21.7, -63.4)
